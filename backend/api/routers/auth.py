"""
auth.py

Register and login. Login returns a JWT the frontend stores and
sends as "Authorization: Bearer <token>" on every subsequent request.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr

from backend.users.users_storage import (
    create_user,
    authenticate_user,
    get_user_email,
    EmailAlreadyRegisteredError,
)
from backend.auth.security import create_access_token
from backend.auth.dependencies import get_current_user

router = APIRouter()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterRequest):
    if len(payload.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")

    try:
        user_id = create_user(payload.email, payload.password)
    except EmailAlreadyRegisteredError as e:
        raise HTTPException(status_code=409, detail=str(e))

    # Send welcome email in background — non-blocking, failure is silent
    import threading
    from backend.notifications.email_sender import send_welcome_email
    threading.Thread(
        target=send_welcome_email,
        args=(payload.email,),
        daemon=True,
    ).start()

    token = create_access_token(user_id)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    user_id = authenticate_user(payload.email, payload.password)

    if user_id is None:
        raise HTTPException(status_code=401, detail="Incorrect email or password.")

    token = create_access_token(user_id)
    return TokenResponse(access_token=token)


@router.get("/me")
def get_me(user_id: str = Depends(get_current_user)):
    """
    Returns the current user's profile. Fetches the parsed name from
    the resumes table so the dashboard greeting shows the user's real
    name (e.g. "Srivasthav") instead of falling back to their email.
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

    return {
        "user_id": user_id,
        "email": email,
        "name": name,
    }