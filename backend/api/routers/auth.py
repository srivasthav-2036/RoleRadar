"""
auth.py

Register and login. Login returns a JWT the frontend stores and
sends as "Authorization: Bearer <token>" on every subsequent request.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from backend.users.users_storage import (
    create_user,
    authenticate_user,
    EmailAlreadyRegisteredError,
)
from backend.auth.security import create_access_token

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

    token = create_access_token(user_id)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    user_id = authenticate_user(payload.email, payload.password)

    if user_id is None:
        raise HTTPException(status_code=401, detail="Incorrect email or password.")

    token = create_access_token(user_id)
    return TokenResponse(access_token=token)