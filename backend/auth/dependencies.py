"""
dependencies.py

get_current_user is a FastAPI dependency - add it to any route that
should require login. It reads the JWT from the Authorization header
(Bearer token), verifies it, and returns the authenticated user_id.

This replaces trusting a user_id/email passed directly in the request
body/URL, which was a real security hole - anyone could act as any
user just by naming a different id.
"""

import jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from backend.auth.security import decode_access_token

security_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> str:
    token = None
    if credentials:
        token = credentials.credentials

    if not token:
        token = request.query_params.get("token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing.",
        )

    try:
        user_id = decode_access_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired, please log in again.",
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
        )

    return user_id
