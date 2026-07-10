"""
fetch_jobs.py

Orchestrates all job providers, then deduplicates and sorts the
combined results.

Order of operations (matters for performance):
    1. Fetch from all providers concurrently (provider-level threads -
       each provider still processes its own companies sequentially
       internally, but all 8 providers run at the same time as each
       other)
    2. Deduplicate BEFORE sorting - shrinks the list first, so the
       sort that follows has fewer items to work through
    3. Sort by posted date, newest first

Assumes every provider's fetch_jobs() returns dicts matching the
shared schema:
    id, title, company, location, description, salary_min,
    salary_max, salary_currency, job_type, posted_at (ddmmyyyy),
    apply_url, source

Usage:
    from job_fetcher.fetch_jobs import fetch_all_jobs
    jobs = fetch_all_jobs("Software Engineer", location="India")
"""

import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from jd_processor.jd_parser import parse_job_description
from jd_processor.jobs_tidb_storage import job_exists, store_job
import sys
import os

# Automatically tells Python to look inside the 'backend' folder for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from job_fetcher.providers import (
    adzuna,
    jsearch,
    lever,
    greenhouse,
    ashby,
    # workable,
    smartrecruiters,
    workday,
)


# Providers fall into two call shapes:
#   - Aggregator APIs (Adzuna, JSearch): take a free-text query + location
#   - Company-list scanners (Lever, Greenhouse, Ashby, Workable,
#     SmartRecruiters, Workday): take a role filter applied per-company
#
# These small wrappers normalize every provider to the same call
# signature: fn(query, location) -> list[dict]
#
# NOTE: workday.py's actual fetch_jobs() signature was not available
# in this session - _call_workday assumes it matches the other
# company-list scanners (role=None). Verify/adjust against the real
# file. If wrong, it fails gracefully below rather than crashing.

def _call_adzuna(query, location):
    return adzuna.fetch_jobs(query=query, location=location)


def _call_jsearch(query, location):
    return jsearch.fetch_jobs(query=query, country="in")


def _call_lever(query, location):
    return lever.fetch_jobs(role=query)


def _call_greenhouse(query, location):
    return greenhouse.fetch_jobs(role=query)


def _call_ashby(query, location):
    return ashby.fetch_jobs(role=query)


# def _call_workable(query, location):
#     return workable.fetch_jobs(role=query)


def _call_smartrecruiters(query, location):
    return smartrecruiters.fetch_jobs(role=query)


# def _call_workday(query, location):
#     return workday.fetch_jobs(role=query)


PROVIDERS = {
    "Adzuna": _call_adzuna,
    "JSearch": _call_jsearch,
    "Lever": _call_lever,
    "Greenhouse": _call_greenhouse,
    "Ashby": _call_ashby,
    # "Workable": _call_workable,
    "SmartRecruiters": _call_smartrecruiters,
    # "Workday": _call_workday,
}


def _fetch_from_provider(name, call_fn, query, location):
    """
    Runs one provider's fetch_jobs(). Wrapped in try/except so a
    single provider crashing (bad import, unexpected signature,
    network failure) doesn't take down the whole run - it just means
    fewer results for that one provider.
    """
    try:
        jobs = call_fn(query, location)
        print(f"[{name}] {len(jobs)} jobs")
        return jobs
    except Exception as e:
        print(f"[{name}] FAILED: {e}")
        return []


def _fetch_all_providers_concurrently(query, location):
    """
    Runs all providers' fetch_jobs() in parallel threads. This is
    provider-level concurrency only - each provider still loops
    through its own companies sequentially inside itself, but all
    providers run alongside each other rather than one after another.
    """
    all_jobs = []

    with ThreadPoolExecutor(max_workers=len(PROVIDERS)) as executor:
        futures = {
            executor.submit(_fetch_from_provider, name, call_fn, query, location): name
            for name, call_fn in PROVIDERS.items()
        }

        for future in as_completed(futures):
            all_jobs.extend(future.result())

    return all_jobs


def _normalize_key_part(value):
    """Lowercase + collapse whitespace, for stable exact-match comparison."""
    if not value:
        return ""
    return re.sub(r"\s+", " ", value.strip().lower())


def _dedupe_jobs(jobs):
    """
    Exact-match dedup on normalized (company, title, location).

    Adzuna and JSearch are both aggregators, so the same real posting
    can legitimately come back from both. When a duplicate is found,
    keeps whichever version has the longer/more complete description,
    since providers differ in whether they've already fetched the
    full JD.
    """
    best_by_key = {}

    for job in jobs:
        key = (
            _normalize_key_part(job.get("company")),
            _normalize_key_part(job.get("title")),
            _normalize_key_part(job.get("location")),
        )

        existing = best_by_key.get(key)

        if existing is None:
            best_by_key[key] = job
            continue

        existing_len = len(existing.get("description") or "")
        new_len = len(job.get("description") or "")

        if new_len > existing_len:
            best_by_key[key] = job

    return list(best_by_key.values())


def _parse_posted_at(ddmmyyyy_str):
    """
    Parses the shared 'ddmmyyyy' posted_at format into a datetime for
    sorting. Missing/unparseable dates sort last (not first), so a
    job with no date doesn't get incorrectly treated as "newest".
    """
    if not ddmmyyyy_str:
        return datetime.min

    try:
        return datetime.strptime(ddmmyyyy_str, "%d%m%Y")
    except ValueError:
        return datetime.min

def _format_display_date(ddmmyyyy_str):
    """Converts stored ddmmyyyy to dd/mm/yyyy for final output."""
    if not ddmmyyyy_str or len(ddmmyyyy_str) != 8:
        return ddmmyyyy_str
    return f"{ddmmyyyy_str[0:2]}/{ddmmyyyy_str[2:4]}/{ddmmyyyy_str[4:8]}"

def _sort_jobs_by_date(jobs):
    return sorted(
        jobs,
        key=lambda j: _parse_posted_at(j.get("posted_at")),
        reverse=True,
    )


def fetch_all_jobs(query, location="India"):
    """
    Runs all providers concurrently, deduplicates the combined
    results, sorts newest-first, and returns the final list.
    """
    print("=" * 60)
    print(f"Fetching '{query}' jobs from {len(PROVIDERS)} providers")
    print("=" * 60)

    raw_jobs = _fetch_all_providers_concurrently(query, location)
    print(f"\nTotal before dedup: {len(raw_jobs)}")

    deduped_jobs = _dedupe_jobs(raw_jobs)
    removed = len(raw_jobs) - len(deduped_jobs)
    print(f"Total after dedup : {len(deduped_jobs)} (removed {removed} duplicates)")

    sorted_jobs = _sort_jobs_by_date(deduped_jobs)
    sorted_jobs = _sort_jobs_by_date(deduped_jobs)

    for job in sorted_jobs:

        job["posted_at"] = _format_display_date(job.get("posted_at"))
        # # checking if job already exists in the database before storing it, 
        # # if it exists, we skip storing it to avoid duplicates
        # if job_exists(
        #     job["job_id"],
        #     job["company"],
        #     job["title"],
        # ):
        #     continue
        # # job not in database, we parse the job description and store it
        # parsed = parse_job_description(
        #     title=job["title"],
        #     company=job["company"],
        #     description=job.get("description"),
        # )

        # store_job(job, parsed)

    return sorted_jobs


if __name__ == "__main__":
    jobs = fetch_all_jobs("Software Engineer", location="India")

    print(f"\nFinal job count: {len(jobs)}\n")

    for job in jobs[:20]:
        print(f"{job.get('title')} - {job.get('company')} ({job.get('source')})")
        print(f"Posted: {job.get('posted_at')}")
        print(f"URL: {job.get('apply_url')}")
        print("-" * 70)
