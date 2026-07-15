"""
usage_tracker.py

Tracks daily request/token usage per provider, persisted in the
database (NOT a local file) - this matters because GitHub Actions
runs each scheduled job in a fresh container with nothing preserved
between runs. A local counter would reset every 4 hours and be
useless for enforcing a rolling DAILY budget (RPD/TPD) across
multiple runs in the same day.

RPM/TPM (per-MINUTE limits) are handled separately, in-process, via
simple sleep-based pacing inside each provider's own module - since a
single run's burst of calls all happen within seconds of each other,
that doesn't need cross-process coordination the way a daily budget
does.
"""

from datetime import date

from sqlalchemy import text

from backend.database.config import engine


class DailyBudgetExhaustedError(Exception):
    """
    Raised when making a call would exceed today's request or token
    budget for a provider. Callers should stop attempting further
    calls for the rest of the day, not retry in a loop - the budget
    won't refill until the date rolls over.
    """
    pass


def _get_today_usage(provider: str) -> tuple[int, int]:
    query = text("""
        SELECT requests_used, tokens_used
        FROM api_usage
        WHERE provider = :provider AND usage_date = :usage_date
    """)

    with engine.connect() as conn:
        row = conn.execute(
            query, {"provider": provider, "usage_date": date.today()}
        ).fetchone()

    if row is None:
        return 0, 0

    return row.requests_used, row.tokens_used


def check_budget(
    provider: str,
    estimated_requests: int,
    estimated_tokens: int,
    rpd_limit: int,
    tpd_limit: int,
):
    """
    Call BEFORE making a request. Raises DailyBudgetExhaustedError if
    today's usage plus this call's estimate would exceed either the
    request or token daily limit.
    """
    requests_used, tokens_used = _get_today_usage(provider)

    if requests_used + estimated_requests > rpd_limit:
        raise DailyBudgetExhaustedError(
            f"{provider}: would exceed daily request limit "
            f"({requests_used}/{rpd_limit} used, tried to add {estimated_requests})"
        )

    if tokens_used + estimated_tokens > tpd_limit:
        raise DailyBudgetExhaustedError(
            f"{provider}: would exceed daily token limit "
            f"({tokens_used}/{tpd_limit} used, tried to add {estimated_tokens})"
        )


def record_usage(provider: str, requests: int, tokens: int):
    """
    Call AFTER a successful request, to log what was actually used.
    Upserts - creates today's row if it doesn't exist yet, otherwise
    increments it.
    """
    query = text("""
        INSERT INTO api_usage (provider, usage_date, requests_used, tokens_used)
        VALUES (:provider, :usage_date, :requests, :tokens)
        ON DUPLICATE KEY UPDATE
            requests_used = requests_used + :requests,
            tokens_used = tokens_used + :tokens
    """)

    with engine.begin() as conn:
        conn.execute(
            query,
            {
                "provider": provider,
                "usage_date": date.today(),
                "requests": requests,
                "tokens": tokens,
            },
        )


def estimate_tokens(text_content: str) -> int:
    """
    Rough heuristic (chars / 4) - not exact, but good enough for
    budget planning purposes. Errs slightly high is fine (safer to
    under-estimate remaining budget than over-estimate it).
    """
    return max(1, len(text_content) // 4)