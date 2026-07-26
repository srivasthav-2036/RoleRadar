"""
otp_store.py

Thread-safe in-memory OTP registry for email verification during registration.

Design decisions:
  - Stored in-memory (dict) — OTPs are short-lived (10 min) and don't need
    to survive server restarts. If the server restarts, the user simply
    requests a fresh OTP.
  - If you later scale to multiple uvicorn workers or processes, replace
    this with a Redis-backed store using the same interface.
  - OTP values are NEVER logged or included in error messages.

Flow:
  1. generate_otp(email)  → 6-digit string (also clears old entry for email)
  2. verify_otp(email, code) → True on match, raises OTPError on any failure
  3. resend_otp(email)    → generates a fresh OTP (resets expiry + attempts)
"""

import logging
import random
import string
import threading
import time
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# ─── Configuration ─────────────────────────────────────────────────────────────
OTP_EXPIRY_SECONDS = 600        # 10 minutes
OTP_MAX_ATTEMPTS   = 5          # lock out after 5 wrong guesses
OTP_LENGTH         = 6
OTP_DIGITS         = string.digits

# Minimum seconds between resend requests (rate-limit resend)
OTP_RESEND_COOLDOWN_SECONDS = 60


# ─── Exceptions ────────────────────────────────────────────────────────────────

class OTPError(Exception):
    """Base class for OTP verification failures."""


class OTPExpiredError(OTPError):
    """The OTP has expired or was never generated."""


class OTPInvalidError(OTPError):
    """The supplied code is incorrect."""


class OTPMaxAttemptsError(OTPError):
    """Too many failed attempts — this OTP is now locked."""


class OTPAlreadyUsedError(OTPError):
    """The OTP was already successfully used."""


class OTPResendCooldownError(OTPError):
    """Resend requested too soon after the previous send."""


# ─── Internal storage ──────────────────────────────────────────────────────────

@dataclass
class _OTPEntry:
    code:       str
    expires_at: float          # epoch seconds
    attempts:   int   = 0
    used:       bool  = False
    created_at: float = field(default_factory=time.time)


_store: dict[str, _OTPEntry] = {}
_lock  = threading.Lock()


# ─── Public API ────────────────────────────────────────────────────────────────

def generate_otp(email: str) -> str:
    """
    Generate a new 6-digit OTP for *email*, overwriting any previous entry.
    Returns the OTP code (caller must pass it to send_otp_email — do NOT log it).
    """
    email = email.strip().lower()
    code  = "".join(random.choices(OTP_DIGITS, k=OTP_LENGTH))
    entry = _OTPEntry(
        code=code,
        expires_at=time.time() + OTP_EXPIRY_SECONDS,
    )
    with _lock:
        _store[email] = entry

    logger.info("[otp_store] OTP generated for %s (expiry in %ds)", email, OTP_EXPIRY_SECONDS)
    return code  # caller emails this; never log it here


def verify_otp(email: str, code: str) -> None:
    """
    Verify the OTP for *email*. On success marks it as used.
    Raises one of the OTPError subclasses on failure — callers convert these
    to HTTP 400 responses with a user-facing message (no raw OTP in messages).
    """
    email = email.strip().lower()
    code  = code.strip()

    with _lock:
        entry = _store.get(email)

        if entry is None:
            raise OTPExpiredError("No OTP was found for this email. Please request a new code.")

        if entry.used:
            raise OTPAlreadyUsedError("This code has already been used. Please request a new code.")

        if time.time() > entry.expires_at:
            _store.pop(email, None)
            raise OTPExpiredError("Your verification code has expired. Please request a new code.")

        if entry.attempts >= OTP_MAX_ATTEMPTS:
            raise OTPMaxAttemptsError(
                "Too many incorrect attempts. Please request a new verification code."
            )

        if entry.code != code:
            entry.attempts += 1
            remaining = OTP_MAX_ATTEMPTS - entry.attempts
            logger.warning(
                "[otp_store] Invalid OTP attempt for %s (%d remaining)",
                email,
                remaining,
            )
            raise OTPInvalidError(
                f"Incorrect verification code. {remaining} attempt(s) remaining."
            )

        # ✓ correct
        entry.used = True
        _store.pop(email, None)  # clean up immediately after success

    logger.info("[otp_store] OTP verified successfully for %s", email)


def resend_otp(email: str) -> str:
    """
    Generate a fresh OTP for *email*, respecting the resend cooldown.
    Returns the new OTP code.
    """
    email = email.strip().lower()

    with _lock:
        existing = _store.get(email)
        if existing and not existing.used:
            elapsed = time.time() - existing.created_at
            if elapsed < OTP_RESEND_COOLDOWN_SECONDS:
                wait = int(OTP_RESEND_COOLDOWN_SECONDS - elapsed)
                raise OTPResendCooldownError(
                    f"Please wait {wait} seconds before requesting a new code."
                )

    # Generate outside the lock (generate_otp re-acquires it)
    return generate_otp(email)


def clear_otp(email: str) -> None:
    """Remove any pending OTP for *email* (e.g. after account creation)."""
    with _lock:
        _store.pop(email.strip().lower(), None)
