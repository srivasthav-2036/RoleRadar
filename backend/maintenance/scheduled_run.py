"""
scheduled_run.py

The entry point for the scheduled pipeline (run every 4 hours via
GitHub Actions).

    1. Pull every distinct search query stored across all users'
       resumes (get_all_search_queries - deduplicated). Fetch jobs
       for each, using a single shared "India" location.
    2. For every user who has uploaded a resume (get_all_users - now
       returns {user_id, email} pairs, since user_id is a real
       account id, not the email itself), run
       generate_recommendations(user_id).
    3. For each new recommendation, pre-generate and cache its
       tailored resume (get_or_generate_tailored_resume) before the
       email goes out.
    4. Email the user's real address (looked up via get_all_users,
       NOT user_id itself anymore).

Run with: python -m maintenance.scheduled_run
"""

from backend.job_fetcher.fetch_jobs import fetch_all_jobs
from backend.recommender.recommender import generate_recommendations
from backend.resume_extractor.resume_text_tidb_storage import (
    get_all_users,
    get_all_search_queries,
)
from backend.resume_tailoring.tailor_resume import get_or_generate_tailored_resume
from backend.notifications.email_sender import send_new_jobs_email

LOCATION = "India"


def run_scheduled_pipeline():
    search_queries = get_all_search_queries()
    print(f"Found {len(search_queries)} unique search queries across all resumes.")

    if not search_queries:
        print("No search queries found (no resumes uploaded yet?) - skipping fetch.")
    else:
        for query in search_queries:
            fetch_all_jobs(query, location=LOCATION)

    users = get_all_users()
    print(f"Checking recommendations for {len(users)} users.")

    for user in users:
        user_id = user["user_id"]
        email = user["email"]

        try:
            recommendations = generate_recommendations(user_id)
        except ValueError:
            continue
        except Exception as e:
            print(f"[scheduled_run] recommendation generation failed for {user_id}: {e}")
            continue

        if not recommendations:
            continue

        for rec in recommendations:
            job_id = rec["job"]["job_id"]
            try:
                get_or_generate_tailored_resume(user_id, job_id)
            except Exception as e:
                print(
                    f"[scheduled_run] tailoring failed for user={user_id} "
                    f"job={job_id}: {e}"
                )

        send_new_jobs_email(to_email=email, matched_jobs=recommendations)


if __name__ == "__main__":
    run_scheduled_pipeline()