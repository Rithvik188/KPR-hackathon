"""The 18 Coimbatore district offices (approximate coordinates, fine for a demo map) and GET /offices."""
from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.core.db import engine, get_session
from app.core.models import Office
from app.ops.schemas import OfficeOut

router = APIRouter(tags=["ops"])

# id, name, type, taluk, lat, lng
OFFICES: list[tuple[str, str, str, str, float, float]] = [
    ("off_cbe_north_to", "Taluk Office – Coimbatore North", "taluk_office", "Coimbatore North", 11.040, 76.950),
    ("off_gandhipuram_es", "e-Sevai Centre – Gandhipuram", "esevai_centre", "Coimbatore North", 11.017, 76.968),
    ("off_saibaba_es", "e-Sevai Centre – Saibaba Colony", "esevai_centre", "Coimbatore North", 11.025, 76.940),
    ("off_cbe_south_to", "Taluk Office – Coimbatore South", "taluk_office", "Coimbatore South", 10.990, 76.962),
    ("off_podanur_es", "e-Sevai Centre – Podanur", "esevai_centre", "Coimbatore South", 10.965, 76.980),
    ("off_perur_to", "Taluk Office – Perur", "taluk_office", "Perur", 10.975, 76.915),
    ("off_madukkarai_to", "Taluk Office – Madukkarai", "taluk_office", "Madukkarai", 10.906, 76.960),
    ("off_sulur_to", "Taluk Office – Sulur", "taluk_office", "Sulur", 11.024, 77.125),
    ("off_sulur_es1", "e-Sevai Centre – Sulur 1", "esevai_centre", "Sulur", 11.030, 77.118),
    ("off_sulur_es2", "e-Sevai Centre – Sulur 2", "esevai_centre", "Sulur", 11.0247, 77.1256),
    ("off_annur_to", "Taluk Office – Annur", "taluk_office", "Annur", 11.232, 77.105),
    ("off_mtp_to", "Taluk Office – Mettupalayam", "taluk_office", "Mettupalayam", 11.299, 76.935),
    ("off_mtp_es", "e-Sevai Centre – Mettupalayam", "esevai_centre", "Mettupalayam", 11.305, 76.942),
    ("off_pollachi_to", "Taluk Office – Pollachi", "taluk_office", "Pollachi", 10.658, 77.008),
    ("off_pollachi_es", "e-Sevai Centre – Pollachi", "esevai_centre", "Pollachi", 10.662, 77.012),
    ("off_kinathu_to", "Taluk Office – Kinathukadavu", "taluk_office", "Kinathukadavu", 10.822, 77.017),
    ("off_anaimalai_to", "Taluk Office – Anaimalai", "taluk_office", "Anaimalai", 10.583, 76.938),
    ("off_valparai_to", "Taluk Office – Valparai", "taluk_office", "Valparai", 10.327, 76.955),
]


def ensure_offices(session: Session) -> None:
    """Insert the office list if the table is empty (runs on startup and before seeding)."""
    if session.exec(select(Office).limit(1)).first() is not None:
        return
    for id_, name, type_, taluk, lat, lng in OFFICES:
        session.add(Office(id=id_, name=name, type=type_, taluk=taluk, lat=lat, lng=lng))
    session.commit()


def startup() -> None:
    with Session(engine) as session:
        ensure_offices(session)


def office_names(session: Session) -> dict[str, str]:
    return {o.id: o.name for o in session.exec(select(Office)).all()}


@router.get("/offices", response_model=list[OfficeOut])
def list_offices(session: Session = Depends(get_session)) -> list[Office]:
    return list(session.exec(select(Office).order_by(Office.taluk, Office.name)).all())
