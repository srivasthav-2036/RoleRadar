"""
users_storage.py

Real account storage: user_id (UUID) + email (unique, used to log
in) + password_hash. Two tables involved:
    - users: account identity (this file)
    - resumes: resume content, user_id is a normal reference to
      users.user_id (not enforced as a DB-level FK - TiDB FK support
      has caveats - so this reference is maintained in application
      code, same pattern as jobs/recommendations elsewhere in this
      codebase)
"""

import uuid

from sqlalchemy import text

from backend.database.config import engine
from backend.auth.security import hash_password, verify_password


class EmailAlreadyRegisteredError(Exception):
    pass


def create_user(email: str, password: str) -> str:
    """
    Registers a new user. Raises EmailAlreadyRegisteredError if the
    email is already taken. Returns the new user_id.
    """
    normalized_email = email.strip().lower()
    password_hash = hash_password(password)
    user_id = str(uuid.uuid4())

    with engine.begin() as conn:
        existing = conn.execute(
            text("SELECT user_id FROM users WHERE email = :email"),
            {"email": normalized_email},
        ).fetchone()

        if existing is not None:
            raise EmailAlreadyRegisteredError(
                f"An account with email {normalized_email} already exists."
            )

        conn.execute(
            text("""
                INSERT INTO users (user_id, email, password_hash)
                VALUES (:user_id, :email, :password_hash)
            """),
            {
                "user_id": user_id,
                "email": normalized_email,
                "password_hash": password_hash,
            },
        )

    return user_id


def authenticate_user(email: str, password: str) -> str | None:
    """
    Verifies email+password. Returns the user_id if valid, None if
    the email doesn't exist or the password is wrong. Deliberately
    doesn't distinguish "no such email" from "wrong password" in the
    return value - callers should show a generic error either way,
    so as not to reveal whether an email is registered.
    """
    normalized_email = email.strip().lower()

    with engine.connect() as conn:
        row = conn.execute(
            text("""
                SELECT user_id, password_hash
                FROM users
                WHERE email = :email
            """),
            {"email": normalized_email},
        ).fetchone()

    if row is None:
        return None

    if not verify_password(password, row.password_hash):
        return None

    return row.user_id


def get_user_email(user_id: str) -> str | None:
    """Returns the email for a user_id, or None if not found."""
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT email FROM users WHERE user_id = :user_id"),
            {"user_id": user_id},
        ).fetchone()

    return row.email if row else None