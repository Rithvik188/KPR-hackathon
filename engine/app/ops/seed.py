"""Seed 30 days of synthetic operations data:  python -m app.ops.seed --reset   (run in engine/).

The data stands for officer-review outcomes *before* SevaiCheck: applications whose documents were sent back
for problems a counter check could have caught. Four stories are planted in the data itself; the alert rules
must find them on their own (nothing here writes an alert):

  A  Sulur 2 e-Sevai scanner: BLUR on 35% of applications in the last 7 days, 10% before.
  B  Pollachi taluk backlog: officer decisions 5x slower in the last 6 days, so ready applications breach SLA.
  C  Duplicate: one (fake) Aadhaar, as a keyed HMAC, in 3 applications at 3 centres within 10 days.
  D  User reports: 4 scanner complaints at Sulur 2 in the last 24 h (+ 2 at Podanur, so one live report there
     triggers a new alert in the demo) and 6 scattered reports over the month.

Seeded rows have is_seed = true and no images. No full Aadhaar number is stored anywhere.
"""
import argparse
import json
from datetime import UTC, datetime, time, timedelta, timezone

import numpy as np
from sqlalchemy import delete, insert
from sqlmodel import Session, select

from app.core.config import get_settings
from app.core.db import create_db, engine
from app.core.models import Alert, AppEvent, Application, Document, IssueReport, Notification, Office
from app.core.security import aadhaar_hmac, mask_phone
from app.ops import alerts
from app.ops.clock import now as utc_now
from app.ops.offices import ensure_offices
from app.validation.messages import make_issue
from app.validation.types import ConsistencyResult, doc_status

IST = timezone(timedelta(hours=5, minutes=30))
RNG_SEED = 22  # chosen so only the planted stories fire at any time of day (see tests/ops)
DAYS = 30
VOLUME = {"taluk_office": 10, "esevai_centre": 6}  # Poisson mean applications per day
BASELINE = {"BLUR": 0.09, "GLARE": 0.06, "AADHAAR_BACK_MISSING": 0.05, "CROPPED": 0.04, "TOO_DARK": 0.03,
            "LOW_RESOLUTION": 0.02, "NAME_MISMATCH": 0.02, "DOB_MISMATCH": 0.01, "INVALID_CHECKSUM": 0.01}
QUALITY = ("BLUR", "GLARE", "CROPPED", "TOO_DARK", "LOW_RESOLUTION")
FIX_PROB = 0.7
DECISION_MEDIAN_H, DECISION_SIGMA = 30.0, 0.6
SERVICES = ("community_certificate", "income_certificate", "nativity_certificate", "ration_card_update")

STORY_A = {"office": "off_sulur_es2", "days": 7, "blur_now": 0.35, "blur_before": 0.10}
STORY_B = {"office": "off_pollachi_to", "days": 9, "factor": 5.0}
STORY_C = {"offices": ("off_gandhipuram_es", "off_podanur_es", "off_mtp_es"), "days_ago": (9, 5, 2)}

GIVEN = ("KARTHIK", "MEENA", "ARUN", "PRIYA", "SURESH", "DIVYA", "RAMESH", "LAKSHMI", "VIGNESH", "KAVITHA",
         "SENTHIL", "DEEPA", "MANI", "REVATHI", "GANESH", "ANITHA", "SARAVANAN", "SANGEETHA", "PRAKASH",
         "GAYATHRI", "MURUGAN", "NITHYA", "BALAJI", "SELVI", "DINESH", "JAYANTHI", "KUMAR", "MALATHI", "RAJA", "SUDHA")
FATHER = ("RAJENDRAN", "SUBRAMANIAN", "KRISHNAN", "MURUGESAN", "PALANISAMY", "RAMASAMY", "GOVINDARAJ",
          "CHINNASAMY", "PERUMAL", "ARUMUGAM", "NATARAJAN", "VELUSAMY", "KANDASAMY", "SHANMUGAM", "DURAISAMY")
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


class Gen:
    """Row builder. Rows are plain dicts for fast bulk inserts."""

    def __init__(self, rng: np.random.Generator, now: datetime, offices: list[Office]):
        self.rng, self.now, self.offices = rng, now, offices
        self.apps: list[dict] = []
        self.docs: list[dict] = []
        self.events: list[dict] = []
        self._seq = 0

    def new_id(self, prefix: str) -> str:
        """Sequential seeded ids ("app_s000042"). Random 8-hex ids would collide across ~30k rows, and the "s"
        keeps them apart from live ids, which are hex only."""
        self._seq += 1
        return f"{prefix}_s{self._seq:06d}"

    # ---- small random helpers ------------------------------------------------------------------
    def pick(self, seq):
        return seq[int(self.rng.integers(len(seq)))]

    def chance(self, p: float) -> bool:
        return bool(self.rng.random() < p)

    def person(self) -> dict:
        given, father = self.pick(GIVEN), self.pick(FATHER)
        dob = (datetime(1955, 1, 1) + timedelta(days=int(self.rng.integers(0, 50 * 365)))).date().isoformat()
        aadhaar_name = f"{father[0]}. {given}" if self.chance(0.6) else f"{given} {father[0]}"
        pan = "".join(self.pick(LETTERS) for _ in range(3)) + "P" + father[0] + \
            "".join(str(int(self.rng.integers(10))) for _ in range(4)) + self.pick(LETTERS)
        epic = "".join(self.pick(LETTERS) for _ in range(3)) + "".join(str(int(self.rng.integers(10))) for _ in range(7))
        return {"aadhaar_name": aadhaar_name, "full_name": f"{given} {father}", "father": father, "dob": dob,
                "gender": self.pick(("M", "F")), "last4": f"{int(self.rng.integers(10000)):04d}",
                "pin": f"64{int(self.rng.integers(1, 3))}{int(self.rng.integers(1000)):03d}", "pan": pan, "epic": epic,
                "phone": f"{int(self.rng.integers(6, 10))}{int(self.rng.integers(10**8, 10**9))}"}

    def evidence(self, code: str) -> dict:
        r = self.rng
        return {
            "BLUR": {"blur_score": round(float(r.uniform(25, 90)), 1), "threshold": 100},
            "GLARE": {"glare_fraction": round(float(r.uniform(0.02, 0.09)), 3), "threshold": 0.015},
            "CROPPED": {"edge_margin_px": int(r.integers(0, 5)), "threshold": 6},
            "TOO_DARK": {"brightness": round(float(r.uniform(30, 58)), 1), "threshold": 60},
            "LOW_RESOLUTION": {"card_width_px": int(r.integers(380, 640)), "threshold": 650},
            "INVALID_CHECKSUM": {"id_number_confidence": round(float(r.uniform(0.9, 0.99)), 2),
                                 "min_confidence_for_rules": 0.85},
            "NAME_MISMATCH": {"name_score": round(float(r.uniform(35, 75)), 1)},
        }.get(code, {})

    def business_time(self, day) -> datetime:
        start = datetime.combine(day, time(9, 30), IST)
        return (start + timedelta(minutes=float(self.rng.uniform(0, 8 * 60)))).astimezone(UTC)

    def decision_delay(self, office_id: str, ready_at: datetime) -> timedelta:
        hours = DECISION_MEDIAN_H * float(np.exp(self.rng.normal(0, DECISION_SIGMA)))
        if office_id == STORY_B["office"] and ready_at >= self.now - timedelta(days=STORY_B["days"]):
            hours *= STORY_B["factor"]
        return timedelta(hours=hours)

    # ---- rows ----------------------------------------------------------------------------------
    def fields(self, p: dict, declared: str) -> dict:
        if declared == "aadhaar_front":
            return {"id_number_display": f"XXXX XXXX {p['last4']}", "name": p["aadhaar_name"], "dob": p["dob"],
                    "gender": p["gender"], "father_name": None}
        if declared == "aadhaar_back":
            return {"id_number_display": f"XXXX XXXX {p['last4']}", "pin_code": p["pin"]}
        number = p["pan"] if declared == "pan" else p["epic"]
        return {"id_number_display": number, "name": p["full_name"], "dob": p["dob"],
                "gender": None if declared == "pan" else p["gender"], "father_name": p["father"]}

    def doc(self, app_id: str, declared: str, codes: list[str], at: datetime, p: dict) -> dict:
        issues = [make_issue(c, self.evidence(c)) for c in codes]
        quality_fail = any(c in QUALITY for c in codes)
        row = {"id": self.new_id("doc"), "application_id": app_id, "declared_type": declared,
               "doc_type": "unknown" if quality_fail else declared, "status": doc_status(issues),
               "issues_json": json.dumps([i.model_dump() for i in issues]),
               "fields_json": None if quality_fail else json.dumps(self.fields(p, declared)),
               "extracted_json": None, "aadhaar_hmac": None, "phash": None, "image_path": None,
               "uploaded_at": at, "is_seed": True}
        self.docs.append(row)
        self.event(app_id, at, "document_uploaded", "operator",
                   f"{declared}: {row['status']}" + (f" ({', '.join(codes)})" if codes else ""))
        return row

    def event(self, app_id: str, at: datetime, event: str, actor: str, note: str | None = None) -> None:
        self.events.append({"id": self.new_id("ev"), "application_id": app_id, "at": at, "event": event,
                            "actor": actor, "note": note})

    def draw_codes(self, office_id: str, created: datetime) -> list[str]:
        codes = []
        for code, p in BASELINE.items():
            if code == "BLUR" and office_id == STORY_A["office"]:
                recent = created >= self.now - timedelta(days=STORY_A["days"])
                p = STORY_A["blur_now"] if recent else STORY_A["blur_before"]
            if self.chance(p):
                codes.append(code)
        return codes

    def consistency(self, p: dict, unfixed_app_codes: list[str], had_app_codes: bool) -> str:
        names = [p["aadhaar_name"], p["full_name"]]
        if unfixed_app_codes:
            issues = [make_issue(c, self.evidence(c)) for c in unfixed_app_codes]
            result = ConsistencyResult(name_tier="mismatch" if "NAME_MISMATCH" in unfixed_app_codes else "match",
                                       name_score=round(float(self.rng.uniform(35, 75)), 1), names_compared=names,
                                       dob_match="DOB_MISMATCH" not in unfixed_app_codes, issues=issues)
        elif not had_app_codes and "." in p["aadhaar_name"] and self.chance(0.8):
            initial = p["aadhaar_name"][0]
            issues = [make_issue("NAME_LIKELY_MATCH", {"name_score": 69.0, "initial_expanded": f"{initial}→{p['father']}",
                                                       "dob_match": True})]
            result = ConsistencyResult(name_tier="likely_match", name_score=69.0, names_compared=names, dob_match=True,
                                       issues=issues)
        else:
            result = ConsistencyResult(name_tier="match", name_score=100.0, names_compared=names, dob_match=True)
        return result.model_dump_json()

    def application(self, office_id: str, created: datetime, codes: list[str] | None = None) -> str:
        p = self.person()
        app_id = self.new_id("app")
        id_type = self.pick(("pan", "voter_id"))
        codes = self.draw_codes(office_id, created) if codes is None else codes
        back_missing = "AADHAAR_BACK_MISSING" in codes
        slots = ["aadhaar_front"] + ([] if back_missing else ["aadhaar_back"]) + [id_type]
        slot_codes: dict[str, list[str]] = {s: [] for s in ("aadhaar_front", "aadhaar_back", id_type)}
        for code in codes:
            if code in QUALITY:
                slot_codes[self.pick(slots)].append(code)
            elif code in ("INVALID_CHECKSUM", "AADHAAR_BACK_MISSING"):
                slot_codes["aadhaar_front"].append(code)  # back-missing is recorded where it was noticed
            else:  # NAME_MISMATCH / DOB_MISMATCH: found when the ID proof was compared with the Aadhaar
                slot_codes[id_type].append(code)

        self.event(app_id, created, "application_created", "operator")
        t = created + timedelta(minutes=float(self.rng.uniform(2, 15)))
        for i, slot in enumerate(slots):
            self.doc(app_id, slot, slot_codes[slot], t + timedelta(minutes=i), p)
        last = t + timedelta(minutes=len(slots))
        status, resubmissions, ready_at, unfixed_app = "submitted", 0, None, []
        decision = {"decision_action": None, "decision_reason": None, "decision_note": None, "decided_at": None}

        if not codes:
            ready_at = last
        else:
            status = "needs_fix"
            self.event(app_id, last, "sms_sent", "system", "needs a correction")
            t1 = last + timedelta(days=float(self.rng.uniform(1, 4)))
            if t1 <= self.now:
                fixed = self.chance(FIX_PROB)
                redo = [s for s in slot_codes if slot_codes[s]] + (["aadhaar_back"] if back_missing else [])
                for i, slot in enumerate(dict.fromkeys(redo)):
                    keep = [] if fixed else [c for c in slot_codes[slot] if c != "AADHAAR_BACK_MISSING"]
                    self.doc(app_id, slot, keep, t1 + timedelta(minutes=i), p)
                    resubmissions += 1
                last = t1 + timedelta(minutes=len(redo))
                if fixed:
                    ready_at = last
                else:
                    unfixed_app = [c for c in codes if c in ("NAME_MISMATCH", "DOB_MISMATCH")]
                    decided = last + self.decision_delay(office_id, last)
                    if decided <= self.now:
                        status = "rejected"
                        decision = {"decision_action": "reject", "decision_reason": codes[0],
                                    "decision_note": "Documents still not acceptable after resubmission",
                                    "decided_at": decided}
                        self.event(app_id, decided, "rejected", "officer", f"rejected ({codes[0]})")
                        last = decided

        if ready_at is not None:
            status = "ready_for_officer"
            self.event(app_id, ready_at, "sent_to_officer", "system")
            last = ready_at
            decided = ready_at + self.decision_delay(office_id, ready_at)
            if decided <= self.now:
                status = "approved"
                decision = {"decision_action": "approve", "decision_reason": None, "decision_note": None,
                            "decided_at": decided}
                self.event(app_id, decided, "approved", "officer", "approved")
                last = decided

        self.apps.append({
            "id": app_id, "citizen_name": p["aadhaar_name"], "phone_masked": mask_phone(p["phone"]),
            "service": self.pick(SERVICES), "office_id": office_id, "status": status, "created_at": created,
            "updated_at": last, "sla_due_at": created + timedelta(hours=72), "resubmissions": resubmissions,
            "consistency_json": self.consistency(p, unfixed_app, any(c in ("NAME_MISMATCH", "DOB_MISMATCH") for c in codes)),
            "is_seed": True, **decision})
        return app_id

    # ---- stories -------------------------------------------------------------------------------
    def history(self, days: int) -> None:
        today = self.now.astimezone(IST).date()
        for back in range(days, -1, -1):
            day = today - timedelta(days=back)
            for office in self.offices:
                for _ in range(int(self.rng.poisson(VOLUME[office.type]))):
                    created = self.business_time(day)
                    if created < self.now:
                        self.application(office.id, created)

    def duplicate_story(self) -> str:
        """Story C: the same Aadhaar (as an HMAC of a fake number) in three clean applications."""
        fake_digits = "".join(("2345", "6789", "0124"))  # fake, assembled at runtime; only its HMAC is stored
        digest = aadhaar_hmac(fake_digits)
        today = self.now.astimezone(IST).date()
        ids = []
        for office_id, days_ago in zip(STORY_C["offices"], STORY_C["days_ago"]):
            ids.append(self.application(office_id, self.business_time(today - timedelta(days=days_ago)), codes=[]))
        for n, app_id in enumerate(ids):
            for doc in self.docs:
                if doc["application_id"] == app_id and doc["declared_type"] in ("aadhaar_front", "aadhaar_back"):
                    doc["aadhaar_hmac"] = digest
                    fields = json.loads(doc["fields_json"])
                    fields["id_number_display"] = f"XXXX XXXX {fake_digits[-4:]}"
                    doc["fields_json"] = json.dumps(fields)
                    if n > 0 and doc["declared_type"] == "aadhaar_front":
                        dup = make_issue("DUPLICATE_SUSPECTED", {"other_applications": ", ".join(ids[:n]), "matches": n})
                        doc["issues_json"] = json.dumps([*json.loads(doc["issues_json"]), dup.model_dump()])
        return digest

    def reports(self) -> list[dict]:
        """Story D plus background noise. No office other than Sulur 2 gets 3 same-category reports in 24 h."""
        n = self.now
        rows = [
            ("off_sulur_es2", "scanner_problem", "operator", "Scanner output is blurry since Monday", 20),
            ("off_sulur_es2", "scanner_problem", "operator", "Card photos keep coming out blurred; many retakes", 14),
            ("off_sulur_es2", "scanner_problem", "citizen", "Asked to retake my Aadhaar photo twice", 6),
            ("off_sulur_es2", "scanner_problem", "operator", "Scanner glass looks scratched, images are fuzzy", 2),
            ("off_podanur_es", "scanner_problem", "operator", "Camera sometimes loses focus on cards", 18),
            ("off_podanur_es", "scanner_problem", "citizen", "Had to retake a PAN card photo", 5),
            ("off_cbe_north_to", "long_wait", "citizen", "Waited over two hours for the officer", 24 * 4),
            ("off_annur_to", "wrong_rejection", "citizen", "Rejected for a blurry photo, but the copy was clear", 24 * 9),
            ("off_saibaba_es", "other", "operator", "Printer out of paper for the acknowledgement slip", 24 * 13),
            ("off_valparai_to", "long_wait", "citizen", "Only one counter open in the morning", 24 * 17),
            ("off_mtp_to", "scanner_problem", "operator", "Scanner cable loose; fixed by re-plugging", 24 * 22),
            ("off_perur_to", "wrong_rejection", "officer", "Application returned for a name mismatch that was an initial", 24 * 27),
        ]
        return [{"id": self.new_id("is"), "office_id": o, "category": c, "reporter_role": r, "description": d,
                 "created_at": n - timedelta(hours=h)} for o, c, r, d, h in rows]


def reset(session: Session) -> None:
    for model in (Notification, AppEvent, Document, Alert, IssueReport, Application):
        session.execute(delete(model))
    session.commit()
    images = get_settings().images_dir
    if images.exists():
        for f in images.iterdir():
            if f.suffix in (".bin", ".tmp"):
                f.unlink(missing_ok=True)


def seed(session: Session, now: datetime | None = None, rng_seed: int = RNG_SEED, days: int = DAYS) -> dict:
    """Insert the synthetic history (call reset() first) and evaluate the alert rules once."""
    now = now or utc_now()
    ensure_offices(session)
    offices = list(session.exec(select(Office).order_by(Office.id)).all())
    gen = Gen(np.random.default_rng(rng_seed), now, offices)
    gen.history(days)
    gen.duplicate_story()
    reports = gen.reports()
    for model, rows in ((Application, gen.apps), (Document, gen.docs), (AppEvent, gen.events), (IssueReport, reports)):
        if rows:
            session.execute(insert(model), rows)
    session.commit()
    drafts = alerts.evaluate_rules(session, now)
    return {"applications": len(gen.apps), "documents": len(gen.docs), "events": len(gen.events),
            "issue_reports": len(reports), "alerts": [(d.rule, d.severity, d.office_id, d.title_en) for d in drafts]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--reset", action="store_true", help="delete all non-office rows and stored images first")
    parser.add_argument("--seed", type=int, default=RNG_SEED, help="random seed (same seed = same data)")
    args = parser.parse_args()
    create_db()
    with Session(engine) as session:
        has_data = session.exec(select(Application.id).limit(1)).first() is not None
        if has_data and not args.reset:
            raise SystemExit("Database already has applications. Re-run with --reset to replace them.")
        if args.reset:
            reset(session)
        summary = seed(session, rng_seed=args.seed)
    print(f"Seeded {summary['applications']} applications, {summary['documents']} documents, "
          f"{summary['events']} events, {summary['issue_reports']} issue reports.")
    print(f"Alerts found by the rules ({len(summary['alerts'])}):")
    for rule, severity, office, title in summary["alerts"]:
        print(f"  [{severity:6s}] {rule:17s} {office}: {title}")


if __name__ == "__main__":
    main()
