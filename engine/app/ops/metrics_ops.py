"""GET /metrics/operations: KPIs, daily series, per-office and per-issue counts, and the impact projection.

A "rejection" here is an application that was sent back for a blocking document issue (the officer-review
outcome before SevaiCheck), so reject_rate = 1 - first-time-right.
"""
from collections import Counter, defaultdict
from datetime import UTC, datetime, time, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, func, select

from app.core.db import get_session
from app.core.models import Document, Office
from app.ops.clock import now as utc_now
from app.ops.facts import AppFacts, load_facts
from app.ops.schemas import (OperationsMetricsOut, OpsDaily, OpsIssueCount, OpsOffice, OpsProjection,
                             OpsTotals)
from app.routers.metrics_detection import load_detection_metrics
from app.validation.messages import QUALITY_CODES

router = APIRouter(tags=["ops"])

IST = timezone(timedelta(hours=5, minutes=30))
# Issues the counter check catches before the application reaches an officer.
COUNTER_DETECTABLE = (*QUALITY_CODES, "AADHAAR_BACK_MISSING", "INVALID_CHECKSUM")
RULE_BASED_RECALL = {"AADHAAR_BACK_MISSING": 1.0}  # a deterministic presence check, not a detector


def _recalls() -> tuple[dict[str, float], str]:
    metrics = load_detection_metrics()
    recall = {row["code"]: float(row["recall"]) for row in metrics.get("per_code", [])}
    return recall, str(metrics.get("source", "unknown"))


def _recall_of(code: str, recall: dict[str, float]) -> float:
    if code not in COUNTER_DETECTABLE:
        return 0.0
    return RULE_BASED_RECALL.get(code, recall.get(code, 0.0))


def projection(rejected: list[AppFacts], total: int) -> OpsProjection:
    """Expected rejections avoided if every document had been checked at the counter first.

    Counted per application, so one application with two issues is never counted twice: its rejection is
    avoided only if every issue it had is counter-detectable, with probability = the product of their recalls.
    With one issue per application this is exactly sum(rejections_with_code x recall(code)).
    """
    recall, source = _recalls()
    expected = 0.0
    for f in rejected:
        p = 1.0
        for code in f.codes:
            p *= _recall_of(code, recall)
        expected += p
    prevented = int(round(expected))
    baseline = len(rejected) / total if total else 0.0
    projected = (len(rejected) - prevented) / total if total else 0.0
    where = "the held-out evaluation" if source == "evaluation" else f"detection metrics (source: {source})"
    return OpsProjection(
        baseline_reject_rate=round(baseline, 4), projected_reject_rate=round(projected, 4),
        prevented_rejections=prevented,
        assumptions_en=(
            f"Projection, not a claim. For each application that was sent back, its rejection counts as prevented "
            f"only if every issue it had can be caught at the counter ({', '.join(COUNTER_DETECTABLE)}), weighted by "
            f"the detector's recall for those issues (multiplied when there are several). With one issue per "
            f"application this is rejections × recall, summed over issue codes. Recall comes from {where}; "
            f"AADHAAR_BACK_MISSING is a presence rule, counted at recall 1.0. Name and date-of-birth mismatches are "
            f"not counted as preventable. Operational data is synthetic (seeded) for demonstration."))


@router.get("/metrics/operations", response_model=OperationsMetricsOut)
def operations_metrics(days: int = Query(30, ge=1, le=90), session: Session = Depends(get_session)) -> OperationsMetricsOut:
    now = utc_now()
    start = now - timedelta(days=days)
    all_facts = load_facts(session, since=start - timedelta(days=30))  # older open applications still count in backlog
    window = [f for f in all_facts if f.created_at >= start]
    offices = {o.id: o for o in session.exec(select(Office)).all()}

    rejected = [f for f in window if f.codes]
    total = len(window)
    documents = session.exec(select(func.count()).select_from(Document)
                             .where(Document.uploaded_at >= start)).one()
    open_now = [f for f in all_facts if not f.decided]
    totals = OpsTotals(
        applications=total, documents=documents,
        first_time_right_rate=round(1 - len(rejected) / total, 4) if total else 0.0,
        avg_resubmissions=round(sum(f.resubmissions for f in window) / total, 3) if total else 0.0,
        backlog_now=len(open_now),
        sla_breaches_now=sum(1 for f in open_now if f.status == "ready_for_officer" and f.sla_due_at < now))

    # Daily series on IST calendar days.
    first_day = start.astimezone(IST).date()
    dates = [first_day + timedelta(days=i) for i in range((now.astimezone(IST).date() - first_day).days + 1)]
    submitted, approved, rejected_n = Counter(), Counter(), Counter()
    for f in window:
        submitted[f.created_at.astimezone(IST).date()] += 1
    for f in all_facts:
        if f.decided_at is not None:
            day = f.decided_at.astimezone(IST).date()
            (approved if f.decision_action == "approve" else rejected_n)[day] += 1
    daily = []
    for d in dates:
        end = min(datetime.combine(d + timedelta(days=1), time(), IST).astimezone(UTC), now)
        daily.append(OpsDaily(date=d.isoformat(), submitted=submitted[d], approved=approved[d],
                              rejected=rejected_n[d], backlog=sum(1 for f in all_facts if f.open_at(end))))

    # Per office.
    per_office: dict[str, list[AppFacts]] = defaultdict(list)
    for f in window:
        per_office[f.office_id].append(f)
    backlog_by_office = Counter(f.office_id for f in open_now)
    by_office = []
    for oid, office in offices.items():
        items = per_office.get(oid, [])
        codes = Counter(code for f in items for code in f.codes)
        by_office.append(OpsOffice(
            office_id=oid, office_name=office.name, taluk=office.taluk, lat=office.lat, lng=office.lng,
            submissions=len(items),
            reject_rate=round(sum(1 for f in items if f.codes) / len(items), 4) if items else 0.0,
            backlog=backlog_by_office[oid], top_issue=codes.most_common(1)[0][0] if codes else None))
    by_office.sort(key=lambda o: o.reject_rate, reverse=True)

    by_issue = Counter(code for f in window for code in f.codes)
    return OperationsMetricsOut(
        days=days, source="seed" if any(f.is_seed for f in window) else "live", totals=totals, daily=daily,
        by_office=by_office,
        by_issue=[OpsIssueCount(code=c, count=n) for c, n in by_issue.most_common()],
        projection=projection(rejected, total))
