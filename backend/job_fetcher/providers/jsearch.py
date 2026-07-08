# import requests
# from job_fetcher.config import RAPIDAPI_KEY

# BASE_URL = "https://jsearch.p.rapidapi.com/search-v2"

# HEADERS = {
#     "X-RapidAPI-Key": RAPIDAPI_KEY,
#     "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
#     "Content-Type": "application/json",
# }


# def fetch_jobs(query, country="in", max_pages=100, sort_by_date=True):
#     """
#     Fetch all jobs from JSearch v2 using cursor pagination.

#     Args:
#         query (str): Search query.
#         country (str): Country code (in, us, uk, etc.).
#         max_pages (int): Safety limit to prevent infinite loops.
#         sort_by_date (bool): If True, sort collected jobs newest-first
#             (client-side, since JSearch has no server-side sort param).

#     Returns:
#         list: List of job dictionaries.
#     """

#     all_jobs = []
#     cursor = None
#     page = 1

#     while page <= max_pages:

#         print(f"\nFetching Page {page}")

#         params = {
#             "query": query,
#             "country": country,
#             "date_posted": "all",
#             "num_pages": 1,
#         }

#         if cursor:
#             params["cursor"] = cursor

#         try:
#             response = requests.get(
#                 BASE_URL,
#                 headers=HEADERS,
#                 params=params,
#                 timeout=30,
#             )

#             print(f"Status Code: {response.status_code}")
#             response.raise_for_status()

#             result = response.json()

#             data = result.get("data", {})
#             jobs = data.get("jobs", [])

#             print(f"Found {len(jobs)} jobs")

#             if not jobs:
#                 print("No more jobs.")
#                 break

#             all_jobs.extend(jobs)

#             cursor = data.get("cursor")

#             if not cursor:
#                 print("No next cursor. Finished.")
#                 break

#             page += 1

#         except requests.exceptions.HTTPError:
#             print(response.text)
#             break

#         except Exception as e:
#             print(f"Error: {e}")
#             break

#     if sort_by_date:
#         # job_posted_at_timestamp is epoch seconds; missing values sort last
#         all_jobs.sort(
#             key=lambda j: j.get("job_posted_at_timestamp") or 0,
#             reverse=True,
#         )

#     print(f"\nTotal Jobs Collected: {len(all_jobs)}")

#     return all_jobs


# if __name__ == "__main__":

#     jobs = fetch_jobs(
#         query="Software Engineer",
#         country="in",
#         max_pages=10,
#     )

#     if jobs:

#         print("\n========== SAMPLE JOB ==========\n")

#         job = jobs[0]

#         print("Title      :", job.get("job_title"))
#         print("Company    :", job.get("employer_name"))
#         print("Location   :", job.get("job_location"))
#         print("Posted     :", job.get("job_posted_at"))
#         print("Publisher  :", job.get("job_publisher"))
#         print("Apply Link :", job.get("job_apply_link"))
#         print("\nJD:")
#         print(job.get("job_description"))

#         print("\nTotal Jobs Returned:", len(jobs))

# new norm code

import re
from datetime import datetime, timezone

import requests
from job_fetcher.config import RAPIDAPI_KEY

BASE_URL = "https://jsearch.p.rapidapi.com/search-v2"

SOURCE_NAME = "JSearch"

HEADERS = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
    "Content-Type": "application/json",
}

# Unified schema every provider should return. Keep this comment block
# identical across providers so it's easy to eyeball consistency.
#
# {
#     "id": str,                # f"{source}_<native id>" - globally unique
#     "title": str,
#     "company": str | None,
#     "location": str | None,
#     "description": str | None,   # cleaned plain text
#     "salary_min": float | None,
#     "salary_max": float | None,
#     "salary_currency": str | None,
#     "job_type": str | None,      # e.g. "full_time permanent" - free text, provider-normalized
#     "posted_at": str | None,     # ddmmyyyy
#     "apply_url": str | None,
#     "source": str,               # provider name, e.g. "Adzuna"
# }


def _clean_description(raw_text):
    """
    JSearch descriptions come through as plain text (not HTML), so there
    are no tags to strip - this just collapses whitespace the same way
    the other providers do, for consistent formatting.
    """
    if not raw_text:
        return raw_text

    text = re.sub(r"[ \t]+", " ", raw_text)
    text = re.sub(r"\n\s*\n+", "\n\n", text).strip()

    return text


def _build_location(job):
    """
    JSearch splits location across job_city/job_state/job_country rather
    than giving one combined string. Build a single display string from
    whichever parts are present, without guessing at missing ones.
    """
    parts = [
        job.get("job_city"),
        job.get("job_state"),
        job.get("job_country"),
    ]
    parts = [p for p in parts if p]
    return ", ".join(parts) if parts else None


def _format_date_ddmmyyyy(epoch_timestamp):
    """
    Convert JSearch's 'job_posted_at_timestamp' (epoch seconds) to
    ddmmyyyy format (e.g. '15012024'), matching the other providers.
    """
    if not epoch_timestamp:
        return None

    try:
        dt = datetime.fromtimestamp(epoch_timestamp, tz=timezone.utc)
        return dt.strftime("%d%m%Y")
    except (ValueError, OSError, OverflowError):
        return None  # unusable timestamp - don't guess


def _normalize_job(job, description):
    """
    Map a raw JSearch job dict -> the unified schema (see module
    docstring block above). Mirrors providers/adzuna.py's _normalize_job.
    """
    native_id = job.get("job_id")

    return {
        "id": f"jsearch_{native_id}" if native_id else None,
        "title": job.get("job_title"),
        "company": job.get("employer_name"),
        "location": _build_location(job),
        "description": description,
        "salary_min": job.get("job_min_salary"),
        "salary_max": job.get("job_max_salary"),
        "salary_currency": job.get("job_salary_currency"),
        "job_type": job.get("job_employment_type"),
        "posted_at": _format_date_ddmmyyyy(job.get("job_posted_at_timestamp")),
        "apply_url": job.get("job_apply_link"),
        "source": SOURCE_NAME,
    }


def fetch_jobs(query, country="in", max_pages=100, sort_by_date=True):
    """
    Fetch all jobs from JSearch v2 using cursor pagination.

    Args:
        query (str): Search query.
        country (str): Country code (in, us, uk, etc.).
        max_pages (int): Safety limit to prevent infinite loops.
        sort_by_date (bool): If True, sort collected jobs newest-first
            (client-side, since JSearch has no server-side sort param).

    Returns:
        list[dict] - each dict matches the unified job schema (see top
        of this file).
    """

    raw_jobs = []
    cursor = None
    page = 1

    while page <= max_pages:

        print(f"\nFetching Page {page}")

        params = {
            "query": query,
            "country": country,
            "date_posted": "all",
            "num_pages": 1,
        }

        if cursor:
            params["cursor"] = cursor

        try:
            response = requests.get(
                BASE_URL,
                headers=HEADERS,
                params=params,
                timeout=30,
            )

            print(f"Status Code: {response.status_code}")
            response.raise_for_status()

            result = response.json()

            data = result.get("data", {})
            jobs = data.get("jobs", [])

            print(f"Found {len(jobs)} jobs")

            if not jobs:
                print("No more jobs.")
                break

            raw_jobs.extend(jobs)

            cursor = data.get("cursor")

            if not cursor:
                print("No next cursor. Finished.")
                break

            page += 1

        except requests.exceptions.HTTPError:
            print(response.text)
            break

        except Exception as e:
            print(f"Error: {e}")
            break

    if sort_by_date:
        # job_posted_at_timestamp is epoch seconds; missing values sort last.
        # Sorted here on the raw field, before normalization turns it into
        # a ddmmyyyy string that can't be sorted the same way.
        raw_jobs.sort(
            key=lambda j: j.get("job_posted_at_timestamp") or 0,
            reverse=True,
        )

    all_jobs = [
        _normalize_job(job, _clean_description(job.get("job_description")))
        for job in raw_jobs
    ]

    print(f"\nTotal Jobs Collected: {len(all_jobs)}")

    return all_jobs


if __name__ == "__main__":

    jobs = fetch_jobs(
        query="Software Engineer",
        country="in",
        max_pages=10,
    )

    if jobs:

        print("\n========== SAMPLE JOB ==========\n")

        job = jobs[0]

        print("Title      :", job.get("title"))
        print("Company    :", job.get("company"))
        print("Location   :", job.get("location"))
        print("Job type   :", job.get("job_type"))
        print("Posted     :", job.get("posted_at"))
        print("Apply Link :", job.get("apply_url"))
        print("\nJD:")
        print(job.get("description"))

        print("\nTotal Jobs Returned:", len(jobs))