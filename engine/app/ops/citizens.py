"""CAN citizen profiles (contract v1.5): POST /citizens (create-or-find by phone) and GET /citizens/{can}.

Built by Person 1 as an agreed one-off exception to folder ownership (comms P1→P2 #0013).
A CAN is created once and never edited: its name and DOB are what the certificate prints. The phone number is
only kept as a keyed HMAC (lookup key) plus its masked form.
"""
import re
from datetime import date

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func
from sqlmodel import Session, select

from app.core.db import get_session
from app.core.errors import api_error
from app.core.models import Citizen, iso
from app.core.security import mask_phone, phone_hmac
from app.ops.clock import now as utc_now

router = APIRouter(tags=["ops"])

_PHONE = re.compile(r"^[6-9]\d{9}$")
_PIN = re.compile(r"^[1-9]\d{5}$")


class CitizenIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    dob: str | None = None
    phone: str = Field(min_length=10, max_length=16)
    address_line: str | None = Field(default=None, max_length=200)
    pin_code: str | None = None

    @field_validator("dob")
    @classmethod
    def _iso_dob(cls, v: str | None) -> str | None:
        if not v:
            return None
        try:
            d = date.fromisoformat(v)
        except ValueError as exc:
            raise ValueError("dob must be YYYY-MM-DD") from exc
        if not (1900 <= d.year <= date.today().year):
            raise ValueError("dob is out of range")
        return d.isoformat()

    @field_validator("pin_code")
    @classmethod
    def _pin(cls, v: str | None) -> str | None:
        if v and not _PIN.match(v):
            raise ValueError("pin_code must be 6 digits")
        return v or None


class CitizenOut(BaseModel):
    can: str
    name: str
    dob: str | None = None
    phone_masked: str
    address_line: str | None = None
    pin_code: str | None = None
    created_at: str


def citizen_out(c: Citizen) -> CitizenOut:
    return CitizenOut(can=c.id, name=c.name, dob=c.dob, phone_masked=c.phone_masked, address_line=c.address_line,
                      pin_code=c.pin_code, created_at=iso(c.created_at))


def normalise_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone)[-10:]
    if not _PHONE.match(digits):
        raise api_error(422, "INVALID_PHONE", "Enter a 10-digit mobile number starting with 6, 7, 8 or 9")
    return digits


def _next_can(session: Session) -> str:
    prefix = f"CAN{utc_now().year}"
    last = session.exec(select(func.max(Citizen.id)).where(Citizen.id.startswith(prefix))).one()
    seq = int(last[len(prefix):]) + 1 if last else 1
    return f"{prefix}{seq:06d}"


def get_citizen(session: Session, can: str) -> Citizen:
    c = session.get(Citizen, can.strip().upper())
    if c is None:
        raise api_error(404, "CAN_NOT_FOUND", f"No citizen with CAN {can}")
    return c


@router.post("/citizens", response_model=CitizenOut, status_code=201,
             responses={200: {"model": CitizenOut, "description": "Existing CAN for this phone"}})
def create_or_find_citizen(body: CitizenIn, session: Session = Depends(get_session)):
    digits = normalise_phone(body.phone)
    key = phone_hmac(digits)
    existing = session.exec(select(Citizen).where(Citizen.phone_hmac == key)).first()
    if existing is not None:  # one CAN per phone; profiles are never edited
        return JSONResponse(citizen_out(existing).model_dump(), status_code=200)
    c = Citizen(id=_next_can(session), name=" ".join(body.name.split()).upper(), dob=body.dob, phone_hmac=key,
                phone_masked=mask_phone(digits), address_line=body.address_line, pin_code=body.pin_code,
                created_at=utc_now())
    session.add(c)
    session.commit()
    session.refresh(c)
    return citizen_out(c)


@router.get("/citizens/{can}", response_model=CitizenOut)
def read_citizen(can: str, session: Session = Depends(get_session)) -> CitizenOut:
    return citizen_out(get_citizen(session, can))
