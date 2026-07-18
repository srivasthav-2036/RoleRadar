"""
pipeline_log.py

Backs the Activity Timeline and Live Scheduler Widget. Two concerns:

    - pipeline_runs: ONE row per scheduled_run.py execution (global,
      not per-user) - "Last synchronization" and "Next scheduled
      fetch" are derived from the most recent row here.
    - activity_log: per-user events (resume analyzed, jobs fetched,
      recommendations updated, email sent) - powers the Activity
      Timeline, and "emails sent" is just a COUNT of event_type=
      'email_sent' rows, so no separate email table is needed.
"""

from datetime import timedelta

from sqlalchemy import text

from backend.database.config import engine

SCHEDULE_INTERVAL_HOURS = 4  # matches the GitHub Actions cron (0 */4 * * *)


def start_pipeline_run() -> int:
    """Call at the START of scheduled_run.py. Returns the new run_id."""
    query = text("INSERT INTO pipeline_runs (started_at) VALUES (NOW())")
    with engine.begin() as conn:
        result = conn.execute(query)
        return result.lastrowid


def finish_pipeline_run(
    run_id: int,
    jobs_fetched: int,
    jobs_parsed: int,
    users_processed: int,
    recommendations_created: int,
    emails_sent: int,
):
    """Call at the END of scheduled_run.py, with the run's real totals."""
    query = text("""
        UPDATE pipeline_runs
        SET
            finished_at = NOW(),
            jobs_fetched = :jobs_fetched,
            jobs_parsed = :jobs_parsed,
            users_processed = :users_processed,
            recommendations_created = :recommendations_created,
            emails_sent = :emails_sent
        WHERE run_id = :run_id
    """)
    with engine.begin() as conn:
        conn.execute(query, {
            "run_id": run_id,
            "jobs_fetched": jobs_fetched,
            "jobs_parsed": jobs_parsed,
            "users_processed": users_processed,
            "recommendations_created": recommendations_created,
            "emails_sent": emails_sent,
        })


def get_last_pipeline_run():
    """
    Powers 'Last synchronization', 'Next scheduled fetch', and the
    Live Scheduler Widget's Jobs Found. Returns None if no run has
    ever completed yet (frontend shows "-").

    next_scheduled_at: computed from the real cron schedule
    (every 4 h from 00:00 UTC: 00, 04, 08, 12, 16, 20) so it's
    always correct regardless of when the last run actually finished.
    """
    from datetime import datetime, timezone

    query = text("""
        SELECT started_at, finished_at, jobs_fetched, jobs_parsed,
               users_processed, recommendations_created, emails_sent
        FROM pipeline_runs
        WHERE finished_at IS NOT NULL
        ORDER BY finished_at DESC
        LIMIT 1
    """)
    with engine.connect() as conn:
        row = conn.execute(query).fetchone()

    if row is None:
        return None

    # ── Compute next scheduled run from cron (every 4 h from 00:00 UTC) ──
    now_utc = datetime.now(timezone.utc)
    # Anchor: midnight UTC today
    midnight = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
    # Find the next multiple-of-4-hour slot that is strictly in the future
    for offset_h in range(0, 24 + SCHEDULE_INTERVAL_HOURS, SCHEDULE_INTERVAL_HOURS):
        candidate = midnight + timedelta(hours=offset_h)
        if candidate > now_utc:
            next_scheduled_at = candidate
            break
    else:
        next_scheduled_at = midnight + timedelta(hours=SCHEDULE_INTERVAL_HOURS)

    return {
        "started_at": row.started_at,
        "finished_at": row.finished_at,
        "next_scheduled_at": next_scheduled_at,
        "jobs_fetched": row.jobs_fetched,
        "jobs_parsed": row.jobs_parsed,
        "users_processed": row.users_processed,
        "recommendations_created": row.recommendations_created,
        "emails_sent": row.emails_sent,
    }



def log_activity(user_id: str, event_type: str, detail: dict | None = None):
    """
    event_type: one of 'resume_analyzed', 'search_queries_generated',
    'jobs_fetched', 'recommendations_updated', 'email_sent'
    """
    import json

    query = text("""
        INSERT INTO activity_log (user_id, event_type, detail)
        VALUES (:user_id, :event_type, :detail)
    """)
    with engine.begin() as conn:
        conn.execute(query, {
            "user_id": user_id,
            "event_type": event_type,
            "detail": json.dumps(detail) if detail else None,
        })


def get_activity_timeline(user_id: str, limit: int = 20) -> list:
    """Powers the Activity Timeline - most recent events first."""
    query = text("""
        SELECT event_type, detail, created_at
        FROM activity_log
        WHERE user_id = :user_id
        ORDER BY created_at DESC
        LIMIT :limit
    """)
    with engine.connect() as conn:
        rows = conn.execute(query, {"user_id": user_id, "limit": limit}).fetchall()

    import json
    results = []
    for row in rows:
        detail = row.detail
        if isinstance(detail, (str, bytes)):
            detail = json.loads(detail)
        results.append({
            "event_type": row.event_type,
            "detail": detail,
            "created_at": row.created_at,
        })
    return results


def get_emails_sent_count(user_id: str, since=None) -> int:
    """
    Powers 'Emails sent' stat card. since: optional datetime to
    filter from (e.g. start of this week) - pass None for all-time.
    """
    if since:
        query = text("""
            SELECT COUNT(*) FROM activity_log
            WHERE user_id = :user_id AND event_type = 'email_sent' AND created_at >= :since
        """)
        params = {"user_id": user_id, "since": since}
    else:
        query = text("""
            SELECT COUNT(*) FROM activity_log
            WHERE user_id = :user_id AND event_type = 'email_sent'
        """)
        params = {"user_id": user_id}

    with engine.connect() as conn:
        count = conn.execute(query, params).scalar()
    return count or 0
