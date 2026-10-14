"""Alert engine: rules over the data (thresholds in alert_rules.json), GET /alerts and POST /alerts/{id}/ack.

Rules never contain hardcoded numbers in their text: every count, rate and ratio is computed from a query.
Alerts are upserted by dedupe_key (rule + office + subject + ISO week), so re-running refreshes the numbers
of an existing alert and keeps its status (an acknowledged alert stays acknowledged).
"""
import json
import logging
import threading
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.core.db import engine, get_session
from app.core.errors import api_error
from app.core.models import Alert, Application, Document, IssueReport, iso, new_id
from app.ops.clock import now as utc_now
from app.ops.facts import AppFacts, load_facts
from app.ops.offices import office_names
from app.ops.schemas import AlertOut

log = logging.getLogger(__name__)
router = APIRouter(tags=["ops"])

RULES_PATH = Path(__file__).with_name("alert_rules.json")

CODE_LABEL = {
    "BLUR": "Blur", "GLARE": "Glare", "CROPPED": "Cropped-card", "TOO_DARK": "Too-dark", "TOO_BRIGHT": "Too-bright",
    "LOW_RESOLUTION": "Low-resolution", "CARD_NOT_FOUND": "Card-not-found", "UNREADABLE": "Unreadable",
    "WRONG_DOC_TYPE": "Wrong-document", "UNKNOWN_DOC_TYPE": "Unknown-document",
    "AADHAAR_BACK_MISSING": "Missing Aadhaar back", "NAME_MISMATCH": "Name-mismatch", "DOB_MISMATCH": "DOB-mismatch",
    "INVALID_CHECKSUM": "Invalid Aadhaar number", "INVALID_FORMAT": "Invalid number format",
}
CODE_ACTION = {
    "BLUR": "Check the scanner or camera focus at this centre; brief operators on holding cards steady.",
    "GLARE": "Use diffuse lighting or a matte surface; avoid overhead tube lights.",
    "CROPPED": "Brief operators to keep all four card edges in frame; mark a capture area on the desk.",
    "TOO_DARK": "Improve the counter lighting; avoid capturing cards in shadow.",
    "TOO_BRIGHT": "Avoid direct sunlight or flash on the card.",
    "LOW_RESOLUTION": "Move the camera closer or use the scanner's higher resolution setting.",
    "AADHAAR_BACK_MISSING": "Add 'Aadhaar back side' to the intake checklist at this centre.",
    "NAME_MISMATCH": "Ask citizens for a supporting document (gazette or affidavit) at intake.",
    "DOB_MISMATCH": "Check the date of birth on every document at intake.",
    "INVALID_CHECKSUM": "Verify the original cards; report suspected tampering to the district office.",
}
CATEGORY_LABEL = {"scanner_problem": "scanner problems", "long_wait": "long waiting times",
                  "wrong_rejection": "wrong rejections", "other": "other problems"}
CATEGORY_ACTION = {
    "scanner_problem": "Send a technician to check the scanner or camera; swap in a spare device meanwhile.",
    "long_wait": "Add a counter operator during peak hours.",
    "wrong_rejection": "Review recent rejections at this centre with the officer.",
    "other": "Follow up with the centre in-charge.",
}


@lru_cache
def rules() -> dict:
    return json.loads(RULES_PATH.read_text(encoding="utf-8"))


@dataclass
class Draft:
    rule: str
    severity: str
    office_id: str | None
    subject: str
    title_en: str
    detail_en: str
    evidence: dict
    suggested_action_en: str


def _week(now: datetime) -> str:
    year, week, _ = now.isocalendar()
    return f"{year}-W{week:02d}"


def _pct(x: float) -> str:
    return f"{x * 100:.1f}%"


# ---- rules ----------------------------------------------------------------------------------------

def reject_spike(facts: list[AppFacts], now: datetime, names: dict[str, str]) -> list[Draft]:
    """This week's rate per office and code vs the baseline weeks before it (a longer baseline is less noisy)."""
    cfg = rules()["reject_spike"]
    win, base = timedelta(days=cfg["window_days"]), timedelta(days=cfg["baseline_days"])
    n_now, n_prev = Counter(), Counter()
    k_now, k_prev = Counter(), Counter()
    for f in facts:
        if now - win <= f.created_at < now:
            n_now[f.office_id] += 1
            for code in f.codes:
                k_now[(f.office_id, code)] += 1
        elif now - win - base <= f.created_at < now - win:
            n_prev[f.office_id] += 1
            for code in f.codes:
                k_prev[(f.office_id, code)] += 1
    baseline_text = "the week before" if cfg["baseline_days"] == 7 else f"the {cfg['baseline_days'] // 7} weeks before"
    out = []
    for (office, code), k in k_now.items():
        n, np_, kp = n_now[office], n_prev[office], k_prev[(office, code)]
        if n < cfg["min_n_now"] or k < cfg["min_k_now"] or np_ == 0:
            continue
        rate, rate_prev = k / n, kp / np_
        if rate - rate_prev < cfg["min_abs_increase"]:
            continue
        ratio = rate / rate_prev if rate_prev > 0 else None
        if ratio is not None and ratio < cfg["min_ratio"]:
            continue
        label = CODE_LABEL.get(code, code)
        title = (f"{label} rejections up {ratio:.1f}× this week" if ratio is not None
                 else f"{label} rejections: {k} this week, none in {baseline_text}")
        out.append(Draft(
            rule="REJECT_SPIKE", severity="high" if ratio is None or ratio >= cfg["high_ratio"] else "medium",
            office_id=office, subject=code, title_en=title,
            detail_en=(f"{k} of {n} applications at {names.get(office, office)} were flagged {code} in the last "
                       f"{cfg['window_days']} days ({_pct(rate)}) vs {kp} of {np_} ({_pct(rate_prev)}) in {baseline_text}."),
            evidence={"code": code, "rate_now": round(rate, 3), "rate_prev": round(rate_prev, 3), "n_now": n,
                      "n_prev": np_, "k_now": k, "k_prev": kp, "ratio": round(ratio, 2) if ratio else None},
            suggested_action_en=CODE_ACTION.get(code, "Review recent rejections at this centre.")))
    return out


def sla_breach(facts: list[AppFacts], now: datetime, names: dict[str, str]) -> list[Draft]:
    """Officer-side SLA: applications waiting for the officer (ready_for_officer) past their 72-hour due time."""
    cfg = rules()["sla_breach"]
    breached: dict[str, list[AppFacts]] = defaultdict(list)
    for f in facts:
        if f.status == "ready_for_officer" and f.sla_due_at < now:
            breached[f.office_id].append(f)
    out = []
    for office, items in breached.items():
        n = len(items)
        if n < cfg["min_breached"]:
            continue
        oldest_h = max((now - f.sla_due_at).total_seconds() / 3600 for f in items)
        out.append(Draft(
            rule="SLA_BREACH", severity="high" if n >= cfg["high_breached"] else "medium", office_id=office,
            subject="sla", title_en=f"{n} applications past the 72-hour SLA",
            detail_en=(f"{n} applications ready for officer review at {names.get(office, office)} have exceeded the "
                       f"72-hour SLA; the oldest is {oldest_h / 24:.1f} days overdue."),
            evidence={"breached": n, "oldest_hours_overdue": round(oldest_h, 1)},
            suggested_action_en="Reassign reviewers or schedule a clearance session at this office."))
    return out


def backlog_growth(facts: list[AppFacts], now: datetime, names: dict[str, str]) -> list[Draft]:
    cfg = rules()["backlog_growth"]
    if not cfg.get("enabled", True):
        return []
    days = cfg["days"]
    points = [now - timedelta(days=days - i) for i in range(days + 1)]  # oldest .. now
    series: dict[str, list[int]] = defaultdict(lambda: [0] * len(points))
    for f in facts:
        for i, t in enumerate(points):
            if f.open_at(t):
                series[f.office_id][i] += 1
    out = []
    for office, s in series.items():
        growth = s[-1] - s[0]
        if not all(b > a for a, b in zip(s, s[1:])) or growth < cfg["min_total_growth"]:
            continue
        out.append(Draft(
            rule="BACKLOG_GROWTH", severity="high" if growth >= cfg["high_total_growth"] else "medium",
            office_id=office, subject="backlog", title_en=f"Backlog grew {days} days in a row (+{growth})",
            detail_en=f"Open applications at {names.get(office, office)}: {' → '.join(map(str, s))} over the last {days} days.",
            evidence={"series": s, "growth": growth},
            suggested_action_en="Check officer availability; consider redistributing applications to nearby offices."))
    return out


def duplicate_cluster(session: Session, now: datetime, names: dict[str, str]) -> list[Draft]:
    """The same Aadhaar (matched by keyed HMAC, never the number itself) in several applications."""
    cfg = rules()["duplicate_cluster"]
    rows = session.exec(
        select(Document.aadhaar_hmac, Application.id, Application.office_id, Application.created_at)
        .join(Application, Application.id == Document.application_id)
        .where(Document.aadhaar_hmac.is_not(None), Document.uploaded_at >= now - timedelta(days=cfg["window_days"]))
    ).all()
    clusters: dict[str, dict[str, tuple[str, datetime]]] = defaultdict(dict)
    for hmac_hex, app_id, office, created in rows:
        clusters[hmac_hex][app_id] = (office, created)
    out = []
    for hmac_hex, apps in clusters.items():
        if len(apps) < cfg["min_applications"]:
            continue
        ordered = sorted(apps.items(), key=lambda kv: kv[1][1])
        offices = list(dict.fromkeys(o for _, (o, _) in ordered))
        span_days = (ordered[-1][1][1] - ordered[0][1][1]).total_seconds() / 86400
        latest_office = ordered[-1][1][0]
        listing = "; ".join(f"{a} ({names.get(o, o)})" for a, (o, _) in ordered)
        out.append(Draft(
            rule="DUPLICATE_CLUSTER", severity="high" if len(apps) >= cfg["high_applications"] else "medium",
            office_id=latest_office, subject=hmac_hex[:16],
            title_en=f"Same Aadhaar used in {len(apps)} applications at {len(offices)} "
                     f"{'centre' if len(offices) == 1 else 'centres'}",
            detail_en=(f"One Aadhaar number (matched by a keyed hash, never stored) appears in {len(apps)} applications "
                       f"within {span_days:.0f} days: {listing}."),
            evidence={"applications": [a for a, _ in ordered], "offices": offices, "span_days": round(span_days, 1)},
            suggested_action_en="Hold these applications and verify the citizen in person; check for identity misuse."))
    return out


def user_reported(session: Session, now: datetime, names: dict[str, str]) -> list[Draft]:
    cfg = rules()["user_reported"]
    reports = session.exec(select(IssueReport).where(
        IssueReport.created_at >= now - timedelta(hours=cfg["window_hours"]))).all()
    groups: dict[tuple[str, str], list[IssueReport]] = defaultdict(list)
    for r in reports:
        groups[(r.office_id, r.category)].append(r)
    out = []
    for (office, category), items in groups.items():
        n = len(items)
        if n < cfg["min_reports"]:
            continue
        roles = Counter(r.reporter_role for r in items)
        latest = max(items, key=lambda r: r.created_at)
        role_text = ", ".join(f"{role} ×{c}" for role, c in roles.most_common())
        out.append(Draft(
            rule="USER_REPORTED", severity="high" if n >= cfg["high_reports"] else "medium", office_id=office,
            subject=category,
            title_en=f"{n} reports of {CATEGORY_LABEL.get(category, category)} in {cfg['window_hours']} h",
            detail_en=(f"{n} reports at {names.get(office, office)} in the last {cfg['window_hours']} hours "
                       f"({role_text}); latest: “{latest.description}”."),
            evidence={"category": category, "reports": n, "roles": dict(roles)},
            suggested_action_en=CATEGORY_ACTION.get(category, CATEGORY_ACTION["other"])))
    return out


def _corroborate(drafts: list[Draft]) -> None:
    """A scanner report at an office that also has a quality-code spike points to hardware, so say so."""
    spikes = {(d.office_id, d.subject) for d in drafts if d.rule == "REJECT_SPIKE"}
    for d in drafts:
        if d.rule == "USER_REPORTED" and d.subject == "scanner_problem":
            codes = sorted(code for office, code in spikes if office == d.office_id)
            if codes:
                d.detail_en += f" Corroborates the {', '.join(codes)} rejection spike at this centre."
                d.evidence["corroborates"] = codes


# ---- evaluation and upsert ------------------------------------------------------------------------

def _upsert(session: Session, drafts: list[Draft], now: datetime) -> int:
    week = _week(now)
    for d in drafts:
        key = f"{d.rule}:{d.office_id}:{d.subject}:{week}"
        alert = session.exec(select(Alert).where(Alert.dedupe_key == key)).first()
        if alert is None:
            alert = Alert(id=new_id("al"), rule=d.rule, office_id=d.office_id, created_at=now, dedupe_key=key,
                          status="open", severity=d.severity, title_en=d.title_en, detail_en=d.detail_en,
                          evidence_json="{}", suggested_action_en=d.suggested_action_en)
        alert.severity, alert.title_en, alert.detail_en = d.severity, d.title_en, d.detail_en
        alert.evidence_json = json.dumps(d.evidence)
        alert.suggested_action_en = d.suggested_action_en
        session.add(alert)
    session.commit()
    return len(drafts)


def evaluate_rules(session: Session, now: datetime | None = None) -> list[Draft]:
    """Run every rule and upsert the resulting alerts. Returns the drafts (handy for tests and the seed)."""
    now = now or utc_now()
    names = office_names(session)
    facts = load_facts(session, since=now - timedelta(days=35))
    drafts = (reject_spike(facts, now, names) + sla_breach(facts, now, names) + backlog_growth(facts, now, names)
              + duplicate_cluster(session, now, names) + user_reported(session, now, names))
    _corroborate(drafts)
    _upsert(session, drafts, now)
    return drafts


def evaluate_user_reported(session: Session) -> None:
    """Re-run only USER_REPORTED (called right after a new issue report)."""
    now = utc_now()
    _upsert(session, user_reported(session, now, office_names(session)), now)


def run_once() -> None:
    with Session(engine) as session:
        evaluate_rules(session)


# ---- background loop ------------------------------------------------------------------------------

_started = threading.Event()


def start_background() -> None:
    """Evaluate now, then every `interval_seconds` on a daemon thread (DB work never blocks the event loop)."""
    try:
        run_once()
    except Exception:  # noqa: BLE001
        log.exception("alert evaluation failed at startup")
    if _started.is_set():
        return
    _started.set()

    def loop() -> None:
        stop = threading.Event()
        while not stop.wait(rules()["interval_seconds"]):
            try:
                run_once()
            except Exception:  # noqa: BLE001
                log.exception("alert evaluation failed")

    threading.Thread(target=loop, name="alert-rules", daemon=True).start()


# ---- endpoints ------------------------------------------------------------------------------------

def to_out(a: Alert, names: dict[str, str]) -> AlertOut:
    return AlertOut(id=a.id, rule=a.rule, severity=a.severity, office_id=a.office_id,  # type: ignore[arg-type]
                    office_name=names.get(a.office_id or "", None), title_en=a.title_en, detail_en=a.detail_en,
                    evidence=json.loads(a.evidence_json or "{}"), suggested_action_en=a.suggested_action_en,
                    status=a.status, created_at=iso(a.created_at))  # type: ignore[arg-type]


@router.get("/alerts", response_model=list[AlertOut])
def list_alerts(status: str | None = None, session: Session = Depends(get_session)) -> list[AlertOut]:
    q = select(Alert)
    if status:
        q = q.where(Alert.status == status)
    names = office_names(session)
    return [to_out(a, names) for a in session.exec(q.order_by(Alert.created_at.desc(), Alert.id)).all()]


@router.post("/alerts/{alert_id}/ack", response_model=AlertOut)
def ack_alert(alert_id: str, session: Session = Depends(get_session)) -> AlertOut:
    alert = session.get(Alert, alert_id)
    if alert is None:
        raise api_error(404, "ALERT_NOT_FOUND", f"No alert {alert_id}")
    alert.status = "acknowledged"
    session.add(alert)
    session.commit()
    session.refresh(alert)
    return to_out(alert, office_names(session))
