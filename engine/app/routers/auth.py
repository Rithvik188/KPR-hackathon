"""POST /auth/staff (staff ID + password), POST /auth/otp/request + /auth/otp/verify (citizen), GET /auth/me."""
import re

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.core.auth import (Principal, lookup_staff, check_otp, check_staff_password, issue_token, new_otp, rate_limited,
                           recent_count, record)
from app.core.config import get_settings
from app.core.errors import api_error
from app.core.security import mask_phone, phone_hmac

router = APIRouter(tags=["auth"])
_PHONE = re.compile(r"^[6-9]\d{9}$")
DEMO_CITIZEN_PHONE = "9876543221"  # the portal's "Use a demo account" number


class StaffLoginIn(BaseModel):
    staff_id: str = Field(min_length=4, max_length=40)
    password: str = Field(min_length=1, max_length=200)


class OtpRequestIn(BaseModel):
    phone: str = Field(min_length=10, max_length=16)


class OtpVerifyIn(OtpRequestIn):
    otp: str = Field(min_length=4, max_length=8)


class SessionOut(BaseModel):
    token: str
    role: str
    name: str | None = None
    office_id: str | None = None
    expires_at: int


class OtpSentOut(BaseModel):
    sent_to: str
    expires_in_s: int
    demo_otp: str | None = None  # only when DEMO_OTP_IN_RESPONSE=1 (no SMS gateway in the prototype)


def _client(request: Request) -> str:
    return request.client.host if request.client else "?"


def _phone(raw: str) -> str:
    digits = re.sub(r"\D", "", raw)[-10:]
    if not _PHONE.match(digits):
        raise api_error(422, "INVALID_PHONE", "Enter a 10-digit mobile number starting with 6, 7, 8 or 9")
    return digits


@router.post("/auth/staff", response_model=SessionOut)
def staff_login(body: StaffLoginIn, request: Request) -> SessionOut:
    staff_id = body.staff_id.strip().upper()
    # Lockout counts only FAILED attempts per staff ID (stops password guessing without locking out real users);
    # all attempts are still capped per IP.
    if rate_limited(f"login:{_client(request)}", 20, 60) or recent_count(f"login-fail:{staff_id}", 300) >= 5:
        raise api_error(429, "TOO_MANY_ATTEMPTS", "Too many sign-in attempts. Wait a few minutes and try again.")
    if not check_staff_password(staff_id, body.password):
        record(f"login-fail:{staff_id}")
        raise api_error(401, "BAD_CREDENTIALS", "Staff ID or password is incorrect")  # same message for both
    s = lookup_staff(staff_id)
    token, exp = issue_token(Principal(role=s["role"], sub=staff_id, name=s["name"], office_id=s["office_id"]))
    return SessionOut(token=token, role=s["role"], name=s["name"], office_id=s["office_id"], expires_at=exp)


@router.post("/auth/otp/request", response_model=OtpSentOut)
def otp_request(body: OtpRequestIn, request: Request) -> OtpSentOut:
    digits = _phone(body.phone)
    # Demo mode only (no SMS gateway, documented in SECURITY.md): the shared demo number gets a higher ceiling so
    # rehearsals and judges don't lock it. Real numbers keep 3 OTPs per 10 minutes.
    demo_number = get_settings().demo_otp_in_response and digits == DEMO_CITIZEN_PHONE
    per_phone = 30 if demo_number else 3
    if rate_limited(f"otp:{_client(request)}", 20, 600) or rate_limited(f"otp-phone:{digits}", per_phone, 600):
        raise api_error(429, "TOO_MANY_ATTEMPTS", "Too many OTP requests. Wait a few minutes and try again.")
    code = new_otp(phone_hmac(digits))
    demo = code if get_settings().demo_otp_in_response else None
    return OtpSentOut(sent_to=mask_phone(digits), expires_in_s=300, demo_otp=demo)


@router.post("/auth/otp/verify", response_model=SessionOut)
def otp_verify(body: OtpVerifyIn, request: Request) -> SessionOut:
    digits = _phone(body.phone)
    if rate_limited(f"otp-verify:{_client(request)}", 15, 600):
        raise api_error(429, "TOO_MANY_ATTEMPTS", "Too many attempts. Wait a few minutes and try again.")
    key = phone_hmac(digits)
    if not check_otp(key, body.otp.strip()):
        raise api_error(401, "BAD_OTP", "The OTP is wrong or has expired. Request a new one.")
    token, exp = issue_token(Principal(role="citizen", sub=key, name=mask_phone(digits)))
    return SessionOut(token=token, role="citizen", name=mask_phone(digits), expires_at=exp)


@router.get("/auth/me")
def me(request: Request) -> dict:
    p = getattr(request.state, "principal", None)
    if p is None:
        raise api_error(401, "NOT_SIGNED_IN", "Sign in first")
    return {"role": p.role, "name": p.name, "office_id": p.office_id, "expires_at": p.exp}
