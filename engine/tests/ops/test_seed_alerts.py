"""The seeded stories must be found by the alert rules on their own, and nothing else may fire."""
import re

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlmodel import Session

from app.core.db import engine
from app.main import app
from app.ops import seed as ops_seed

STORIES = {
    ("REJECT_SPIKE", "off_sulur_es2"),     # A: scanner blur
    ("SLA_BREACH", "off_pollachi_to"),     # B: backlog past SLA
    ("DUPLICATE_CLUSTER", "off_mtp_es"),   # C: same Aadhaar at 3 centres (latest one)
    ("USER_REPORTED", "off_sulur_es2"),    # D: operator scanner reports
}


@pytest.fixture(scope="module")
def seeded():
    with Session(engine) as session:
        ops_seed.reset(session)
        summary = ops_seed.seed(session)
    with TestClient(app) as client:
        yield client, summary


def test_exactly_the_four_stories_fire(seeded):
    _, summary = seeded
    fired = {(rule, office) for rule, _, office, _ in summary["alerts"]}
    assert fired == STORIES
    assert all(severity == "high" for _, severity, _, _ in summary["alerts"])


def test_alert_text_carries_computed_numbers(seeded):
    client, _ = seeded
    alerts = client.get("/api/alerts").json()
    spike = next(a for a in alerts if a["rule"] == "REJECT_SPIKE")
    ev = spike["evidence"]
    assert ev["code"] == "BLUR" and ev["k_now"] >= 10 and ev["rate_now"] > 2 * ev["rate_prev"]
    assert f"{ev['k_now']} of {ev['n_now']}" in spike["detail_en"]
    sla = next(a for a in alerts if a["rule"] == "SLA_BREACH")
    assert sla["evidence"]["breached"] >= 20 and str(sla["evidence"]["breached"]) in sla["title_en"]
    dup = next(a for a in alerts if a["rule"] == "DUPLICATE_CLUSTER")
    assert len(dup["evidence"]["applications"]) == 3 and len(dup["evidence"]["offices"]) == 3
    reported = next(a for a in alerts if a["rule"] == "USER_REPORTED")
    assert "BLUR" in reported["evidence"].get("corroborates", [])


def test_new_report_triggers_user_reported_immediately(seeded):
    client, _ = seeded
    res = client.post("/api/issues", json={"office_id": "off_podanur_es", "category": "scanner_problem",
                                           "description": "Scanner images blurry again", "reporter_role": "operator"})
    assert res.status_code == 201
    alerts = client.get("/api/alerts", params={"status": "open"}).json()
    podanur = [a for a in alerts if a["rule"] == "USER_REPORTED" and a["office_id"] == "off_podanur_es"]
    assert podanur and podanur[0]["evidence"]["reports"] == 3
    assert client.get("/api/issues").json()[0]["description"] == "Scanner images blurry again"


def test_acknowledge(seeded):
    client, _ = seeded
    alert = client.get("/api/alerts").json()[0]
    acked = client.post(f"/api/alerts/{alert['id']}/ack").json()
    assert acked["status"] == "acknowledged"
    assert alert["id"] not in [a["id"] for a in client.get("/api/alerts", params={"status": "open"}).json()]
    # Re-evaluating the rules refreshes numbers but keeps the acknowledgement.
    with Session(engine) as session:
        from app.ops.alerts import evaluate_rules
        evaluate_rules(session)
    again = next(a for a in client.get("/api/alerts").json() if a["id"] == alert["id"])
    assert again["status"] == "acknowledged"


def test_operations_metrics(seeded):
    client, _ = seeded
    m = client.get("/api/metrics/operations", params={"days": 30}).json()
    assert m["source"] == "seed" and m["totals"]["applications"] > 1000
    assert 0.6 < m["totals"]["first_time_right_rate"] < 0.8
    assert len(m["daily"]) == 31 and len(m["by_office"]) == 18
    assert m["by_issue"][0]["code"] == "BLUR"
    p = m["projection"]
    assert 0 <= p["projected_reject_rate"] < p["baseline_reject_rate"]
    assert "Projection, not a claim" in p["assumptions_en"]
    week = client.get("/api/metrics/operations", params={"days": 7}).json()
    assert week["by_office"][0]["office_id"] == "off_sulur_es2"  # highest 7-day reject rate


def test_no_twelve_digit_runs_anywhere_in_the_database(seeded):
    twelve = re.compile(r"(?<![0-9a-f])\d{12}(?![0-9a-f])")
    with engine.connect() as conn:
        tables = [r[0] for r in conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))]
        for table in tables:
            for row in conn.execute(text(f'SELECT * FROM "{table}"')):
                for value in row:
                    if isinstance(value, str):
                        assert not twelve.search(value), f"12-digit run in {table}: {value[:80]}"
