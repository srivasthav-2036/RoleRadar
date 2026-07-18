"""
scheduled_run.py

The entry point for the scheduled pipeline (run every 4 hours via
GitHub Actions).

    1. Pull every distinct search query stored across all users'
       resumes (get_all_search_queries - deduplicated). Fetch jobs
       for ALL of them in ONE fetch_all_jobs() call.
    2. For every user who has uploaded a resume (get_all_users),
       run generate_recommendations(user_id).
    3. Email the user if they got any new recommendations.
    4. Log the run in pipeline_runs so the Live Scheduler widget
       always reflects the latest run data (last_sync, next_sync,
       jobs_fetched).

NOTE: Tailored resumes are NOT pre-generated here anymore - that was
removed on purpose. Generating a tailored resume for every new
recommendation, for every user, every run, was burning API calls
that might never even be used (a user may never click into half their
recommendations). Tailoring now happens ONLY on-demand.

Run with: python -m backend.maintenance.scheduled_run
"""

import logging

from backend.job_fetcher.fetch_jobs import fetch_all_jobs
from backend.recommender.recommender import generate_recommendations
from backend.resume_extractor.resume_text_tidb_storage import (
    get_all_users,
    get_all_search_queries,
)
from backend.notifications.email_sender import send_new_jobs_email
from backend.maintenance.pipeline_log import (
    start_pipeline_run,
    finish_pipeline_run,
    log_activity,
)

LOCATION = "India"


def run_scheduled_pipeline():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    run_id = start_pipeline_run()
    jobs_fetched = 0
    jobs_parsed = 0
    users_processed = 0
    recommendations_created = 0
    emails_sent = 0

    # search_queries = get_all_search_queries()
    # print(f"Found {len(search_queries)} unique search queries across all resumes.")

    # if not search_queries:
    #     print("No search queries found (no resumes uploaded yet?) - skipping fetch.")
    # else:
    #     fetched = fetch_all_jobs(search_queries, location=LOCATION)
    #     # fetch_all_jobs returns the count of jobs fetched/stored
    #     if isinstance(fetched, int):
    #         jobs_fetched = fetched
    #     elif isinstance(fetched, list):
    #         jobs_fetched = len(fetched)
    #     jobs_parsed = jobs_fetched  # treat as parsed = fetched

    users = get_all_users()
    print(f"Checking recommendations for {len(users)} users.")

    for user in users:
        user_id = user["user_id"]
        email = user["email"]
        users_processed += 1

        try:
            recommendations = generate_recommendations(user_id)
        except ValueError:
            continue
        except Exception as e:
            print(f"[scheduled_run] recommendation generation failed for {user_id}: {e}")
            continue

        if not recommendations:
            continue

        recommendations_created += len(recommendations)

        # Log activity for this user
        try:
            log_activity(user_id, "recommendations_updated", {
                "count": len(recommendations),
                "source": "scheduled_run",
            })
        except Exception:
            pass

        try:
            send_new_jobs_email(to_email=email, matched_jobs=recommendations)
            emails_sent += 1
            try:
                log_activity(user_id, "email_sent", {"count": 1})
            except Exception:
                pass
        except Exception as e:
            print(f"[scheduled_run] email failed for {user_id}: {e}")

    # Write run completion to pipeline_runs table
    finish_pipeline_run(
        run_id=run_id,
        jobs_fetched=jobs_fetched,
        jobs_parsed=jobs_parsed,
        users_processed=users_processed,
        recommendations_created=recommendations_created,
        emails_sent=emails_sent,
    )

    print(f"[scheduled_run] Done. jobs_fetched={jobs_fetched} users={users_processed} recs={recommendations_created} emails={emails_sent}")


if __name__ == "__main__":
    run_scheduled_pipeline()