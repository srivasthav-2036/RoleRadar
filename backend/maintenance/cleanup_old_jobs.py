"""
cleanup_old_jobs.py

Deletes jobs older than RETENTION_DAYS, along with any
recommendations that pointed to them. recommendations.job_id has no
DB-level FK to jobs.job_id (job_id isn't unique in jobs - duplicate
job_ids across providers are expected, so TiDB can't enforce a FK
with ON DELETE CASCADE here) - so the link is cleaned up manually,
in one script, so the two tables never drift out of sync.

Uses the jobs.updated_at column as the cutoff. This works because
store_job() only ever INSERTs (job_exists() prevents re-inserting an
existing row), so updated_at is effectively set-once at insert time
for every row today.

CAUTION: if an UPDATE path for existing job rows is ever added later
(e.g. refreshing a stale posting in place instead of inserting a new
row), updated_at would reset on that row and this script would treat
it as "new" again, delaying its cleanup. If that happens, switch back
to a dedicated immutable created_at column instead.

Run this on a schedule (cron / APScheduler) every 6 days.
"""

from sqlalchemy import text

from backend.database.config import engine

RETENTION_DAYS = 6


def cleanup_old_jobs():
    with engine.begin() as conn:

        # 1. Find job_ids about to be deleted
        stale_rows = conn.execute(
            text("""
                SELECT DISTINCT job_id
                FROM jobs
                WHERE updated_at < NOW() - INTERVAL :days DAY
            """),
            {"days": RETENTION_DAYS},
        ).fetchall()

        stale_job_ids = [row[0] for row in stale_rows]

        if not stale_job_ids:
            print("No stale jobs to clean up.")
            return

        # 2. Delete recommendations pointing to those job_ids first
        placeholders = ",".join(f":id{i}" for i in range(len(stale_job_ids)))
        params = {f"id{i}": jid for i, jid in enumerate(stale_job_ids)}

        deleted_recs = conn.execute(
            text(f"DELETE FROM recommendations WHERE job_id IN ({placeholders})"),
            params,
        )

        # 3. Delete the stale jobs themselves
        deleted_jobs = conn.execute(
            text("""
                DELETE FROM jobs
                WHERE updated_at < NOW() - INTERVAL :days DAY
            """),
            {"days": RETENTION_DAYS},
        )

        print(f"Deleted {deleted_jobs.rowcount} jobs")
        print(f"Deleted {deleted_recs.rowcount} linked recommendations")


if __name__ == "__main__":
    cleanup_old_jobs()
