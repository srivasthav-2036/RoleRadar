"""
auth.py

Register and login. Login returns a JWT the frontend stores and
sends as "Authorization: Bearer <token>" on every subsequent request.

Registration is now a 2-step OTP flow:
  1. POST /send-otp   — validate email availability, send verification code
  2. POST /verify-otp — verify code, create account, return JWT

The old POST /register endpoint is kept for backward compatibility but
is no longer called by the frontend after the OTP flow is wired up.
"""

import logging
import threading

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr

from backend.users.users_storage import (
    create_user,
    authenticate_user,
    get_user_email,
    email_exists,
    get_notification_preference,
    set_notification_preference,
    EmailAlreadyRegisteredError,
)
from backend.auth.security import create_access_token
from backend.auth.dependencies import get_current_user
from backend.auth.otp_store import (
    generate_otp,
    verify_otp,
    resend_otp,
    clear_otp,
    OTPError,
    OTPExpiredError,
    OTPInvalidError,
    OTPMaxAttemptsError,
    OTPAlreadyUsedError,
    OTPResendCooldownError,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ─── Request / Response models ────────────────────────────────────────────────

class SendOtpRequest(BaseModel):
    email: EmailStr


class VerifyOtpRequest(BaseModel):
    email: EmailStr
    otp: str
    password: str


class ResendOtpRequest(BaseModel):
    email: EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class NotificationPreferenceRequest(BaseModel):
    enabled: bool


# ─── OTP Registration Flow ────────────────────────────────────────────────────

@router.post("/send-otp")
def send_otp(payload: SendOtpRequest):
    """
    Step 1 of registration. Checks whether the email is already in use,
    then generates and emails a 6-digit OTP. Does NOT create the account.
    """
    normalized = payload.email.strip().lower()

    if email_exists(normalized):
        raise HTTPException(
            status_code=409,
            detail=(
                "This email address is already registered. "
                "Please log in or use a different email address."
            ),
        )

    otp_code = generate_otp(normalized)

    # Send OTP email in background — non-blocking
    from backend.notifications.email_sender import send_otp_email
    threading.Thread(
        target=send_otp_email,
        args=(normalized, otp_code),
        daemon=True,
    ).start()

    logger.info("[auth] OTP send-otp requested for %s", normalized)
    return {"message": "Verification code sent. Please check your email."}


@router.post("/resend-otp")
def resend_otp_endpoint(payload: ResendOtpRequest):
    """
    Re-sends a fresh OTP for the given email. Subject to a 60-second cooldown.
    """
    normalized = payload.email.strip().lower()

    try:
        otp_code = resend_otp(normalized)
    except OTPResendCooldownError as e:
        raise HTTPException(status_code=429, detail=str(e))

    from backend.notifications.email_sender import send_otp_email
    threading.Thread(
        target=send_otp_email,
        args=(normalized, otp_code),
        daemon=True,
    ).start()

    return {"message": "A new verification code has been sent to your email."}


@router.post("/verify-otp", response_model=TokenResponse)
def verify_otp_endpoint(payload: VerifyOtpRequest):
    """
    Step 2 of registration. Verifies the OTP, creates the account, returns JWT.
    """
    if len(payload.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")

    normalized = payload.email.strip().lower()

    # Guard: re-check email availability (race condition protection)
    if email_exists(normalized):
        clear_otp(normalized)
        raise HTTPException(
            status_code=409,
            detail=(
                "This email address is already registered. "
                "Please log in or use a different email address."
            ),
        )

    try:
        verify_otp(normalized, payload.otp.strip())
    except OTPExpiredError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except OTPAlreadyUsedError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except OTPMaxAttemptsError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except OTPInvalidError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except OTPError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        user_id = create_user(normalized, payload.password)
    except EmailAlreadyRegisteredError:
        raise HTTPException(
            status_code=409,
            detail=(
                "This email address is already registered. "
                "Please log in or use a different email address."
            ),
        )

    # Send welcome email in background — non-blocking, failure is silent
    from backend.notifications.email_sender import send_welcome_email
    threading.Thread(
        target=send_welcome_email,
        args=(normalized,),
        daemon=True,
    ).start()

    logger.info("[auth] New account created via OTP flow for %s", normalized)
    token = create_access_token(user_id)
    return TokenResponse(access_token=token)


# ─── Legacy Register (kept for compatibility) ────────────────────────────────

@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterRequest):
    if len(payload.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")

    try:
        user_id = create_user(payload.email, payload.password)
    except EmailAlreadyRegisteredError:
        raise HTTPException(
            status_code=409,
            detail=(
                "This email address is already registered. "
                "Please log in or use a different email address."
            ),
        )

    import threading
    from backend.notifications.email_sender import send_welcome_email
    threading.Thread(
        target=send_welcome_email,
        args=(payload.email,),
        daemon=True,
    ).start()

    token = create_access_token(user_id)
    return TokenResponse(access_token=token)


# ─── Login ────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    user_id = authenticate_user(payload.email, payload.password)

    if user_id is None:
        raise HTTPException(status_code=401, detail="Incorrect email or password.")

    token = create_access_token(user_id)
    return TokenResponse(access_token=token)


# ─── Me ───────────────────────────────────────────────────────────────────────

@router.get("/me")
def get_me(user_id: str = Depends(get_current_user)):
    """
    Returns the current user's profile. Fetches the parsed name from
    the resumes table so the dashboard greeting shows the user's real
    name (e.g. "Srivasthav") instead of falling back to their email.
    Also returns email_notifications preference.
    """
    from backend.resume_extractor.resume_text_tidb_storage import get_resume

    email = get_user_email(user_id)
    if email is None:
        raise HTTPException(status_code=404, detail="User not found.")

    # Pull name from the latest resume (may be None if no resume yet)
    name: str | None = None
    try:
        resume_data = get_resume(user_id)
        if resume_data and resume_data.get("name"):
            name = resume_data["name"]
    except Exception:
        pass  # Name is best-effort — don't fail the /me endpoint

    email_notifications = get_notification_preference(user_id)

    return {
        "user_id": user_id,
        "email": email,
        "name": name,
        "email_notifications": email_notifications,
    }


# ─── Notification Preference ──────────────────────────────────────────────────

@router.patch("/me/notifications")
def update_notifications(
    payload: NotificationPreferenceRequest,
    user_id: str = Depends(get_current_user),
):
    """
    Persists the user's email notification preference.
    enabled=true  → user will receive recommendation emails (default)
    enabled=false → recommendation emails are skipped for this user
    """
    set_notification_preference(user_id, payload.enabled)
    return {"email_notifications": payload.enabled}