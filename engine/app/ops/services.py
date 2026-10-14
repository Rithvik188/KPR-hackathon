"""Loads contract/services.json (v1.4): per-service required slots, supporting documents, and the officer stages.

A service's required documents are the ID-proof slots plus exactly one supporting slot. The officer chain is
VAO → RI → Tahsildar, each with a per-stage SLA in hours.
"""
import json
from functools import lru_cache

from app.core.config import CONTRACT_DIR

SUPPORTING_SLOT = "supporting"


@lru_cache
def services_data() -> dict:
    return json.loads((CONTRACT_DIR / "services.json").read_text(encoding="utf-8"))


def service_def(service: str) -> dict | None:
    return services_data()["services"].get(service)


def supporting_type_for(service: str) -> str | None:
    """The one supporting DocType a service requires (e.g. community → parent_community_certificate)."""
    for slot in (service_def(service) or {}).get("required", []):
        if isinstance(slot, str) and slot in services_data()["supporting_types"]:
            return slot
    return None


def required_slots_for(service: str) -> tuple[str, ...]:
    """Ops slots required for `ready_for_officer`: the ID proofs plus the service's supporting slot (if any)."""
    base = ("aadhaar_front", "aadhaar_back", "id_proof")
    return (*base, SUPPORTING_SLOT) if supporting_type_for(service) else base


def stages_order() -> list[str]:
    return list(services_data()["stages"]["order"])


def stage_sla_hours(stage: str) -> int:
    return int(services_data()["stages"][stage]["sla_hours"])


def next_stage(stage: str | None) -> str | None:
    order = stages_order()
    if stage not in order:
        return None
    i = order.index(stage)
    return order[i + 1] if i + 1 < len(order) else None
