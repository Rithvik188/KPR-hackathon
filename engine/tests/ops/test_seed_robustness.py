"""The demo is re-seeded shortly before it starts, at whatever time that is. The four stories must fire, and
nothing else, at any time of day (the seed once lost story A when it was run just after midnight)."""
from datetime import timedelta

import pytest
from sqlmodel import Session

from app.core.db import engine
from app.ops import seed as ops_seed
from app.ops.clock import now

STORIES = {("REJECT_SPIKE", "off_sulur_es2"), ("SLA_BREACH", "off_pollachi_to"),
           ("DUPLICATE_CLUSTER", "off_mtp_es"), ("USER_REPORTED", "off_sulur_es2")}


@pytest.mark.parametrize("hours_earlier", [0, 6, 12, 18])
def test_stories_fire_at_any_time_of_day(hours_earlier):
    with Session(engine) as session:
        ops_seed.reset(session)
        summary = ops_seed.seed(session, now=now() - timedelta(hours=hours_earlier))
    fired = {(rule, office) for rule, _, office, _ in summary["alerts"]}
    assert fired == STORIES, summary["alerts"]
    spike = next(title for rule, _, _, title in summary["alerts"] if rule == "REJECT_SPIKE")
    assert spike.startswith("Blur rejections up")
