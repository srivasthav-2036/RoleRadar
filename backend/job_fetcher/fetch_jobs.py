# """
# fetch_jobs.py

# Orchestrates all job providers, then deduplicates and sorts the
# combined results.
# """

# import re
# from concurrent.futures import ThreadPoolExecutor, as_completed
# from datetime import datetime
# from backend.jd_processor.jd_parser import parse_job_description
# from backend.jd_processor.jobs_tidb_storage import job_exists, store_job
# import sys
# import os

# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# from backend.job_fetcher.providers import (
#     adzuna,
#     jsearch,
#     lever,
#     greenhouse,
#     ashby,
#     # workable,
#     smartrecruiters,
#     workday,
# )


# def _call_adzuna(query, location):
#     return adzuna.fetch_jobs(query=query, location=location)


# def _call_jsearch(query, location):
#     return jsearch.fetch_jobs(query=query, country="in")


# def _call_lever(query, location):
#     return lever.fetch_jobs(role=query)


# def _call_greenhouse(query, location):
#     return greenhouse.fetch_jobs(role=query)


# def _call_ashby(query, location):
#     return ashby.fetch_jobs(role=query)


# def _call_smartrecruiters(query, location):
#     return smartrecruiters.fetch_jobs(role=query)


# PROVIDERS = {
#     "Adzuna": _call_adzuna,
#     "JSearch": _call_jsearch,
#     "Lever": _call_lever,
#     "Greenhouse": _call_greenhouse,
#     "Ashby": _call_ashby,
#     "SmartRecruiters": _call_smartrecruiters,
# }


# def _fetch_from_provider(name, call_fn, query, location):
#     try:
#         jobs = call_fn(query, location)
#         print(f"[{name}] {len(jobs)} jobs")
#         return jobs
#     except Exception as e:
#         print(f"[{name}] FAILED: {e}")
#         return []


# def _fetch_all_providers_concurrently(query, location):
#     all_jobs = []

#     with ThreadPoolExecutor(max_workers=len(PROVIDERS)) as executor:
#         futures = {
#             executor.submit(_fetch_from_provider, name, call_fn, query, location): name
#             for name, call_fn in PROVIDERS.items()
#         }

#         for future in as_completed(futures):
#             all_jobs.extend(future.result())

#     return all_jobs


# def _normalize_key_part(value):
#     if not value:
#         return ""
#     return re.sub(r"\s+", " ", value.strip().lower())


# def _dedupe_jobs(jobs):
#     best_by_key = {}

#     for job in jobs:
#         key = (
#             _normalize_key_part(job.get("company")),
#             _normalize_key_part(job.get("title")),
#             _normalize_key_part(job.get("location")),
#         )

#         existing = best_by_key.get(key)

#         if existing is None:
#             best_by_key[key] = job
#             continue

#         existing_len = len(existing.get("description") or "")
#         new_len = len(job.get("description") or "")

#         if new_len > existing_len:
#             best_by_key[key] = job

#     return list(best_by_key.values())


# def _parse_posted_at(ddmmyyyy_str):
#     if not ddmmyyyy_str:
#         return datetime.min

#     try:
#         return datetime.strptime(ddmmyyyy_str, "%d%m%Y")
#     except ValueError:
#         return datetime.min


# def _format_display_date(ddmmyyyy_str):
#     if not ddmmyyyy_str or len(ddmmyyyy_str) != 8:
#         return ddmmyyyy_str
#     return f"{ddmmyyyy_str[0:2]}/{ddmmyyyy_str[2:4]}/{ddmmyyyy_str[4:8]}"


# def _sort_jobs_by_date(jobs):
#     return sorted(
#         jobs,
#         key=lambda j: _parse_posted_at(j.get("posted_at")),
#         reverse=True,
#     )


# def fetch_all_jobs(query, location="India"):
#     """
#     Runs all providers concurrently, deduplicates the combined
#     results, sorts newest-first, parses + stores any new jobs, and
#     returns the final list. Each returned job dict has an "is_new"
#     flag (True if it was just inserted this run, False if it already
#     existed) - used by the scheduled pipeline to decide who to email.
#     """
#     print("=" * 60)
#     print(f"Fetching '{query}' jobs from {len(PROVIDERS)} providers")
#     print("=" * 60)

#     raw_jobs = _fetch_all_providers_concurrently(query, location)
#     print(f"\nTotal before dedup: {len(raw_jobs)}")

#     deduped_jobs = _dedupe_jobs(raw_jobs)
#     removed = len(raw_jobs) - len(deduped_jobs)
#     print(f"Total after dedup : {len(deduped_jobs)} (removed {removed} duplicates)")

#     sorted_jobs = _sort_jobs_by_date(deduped_jobs)

#     for job in sorted_jobs:

#         job["posted_at"] = _format_display_date(job.get("posted_at"))

#         # checking if job already exists in the database before storing it,
#         # if it exists, we skip storing it to avoid duplicates
#         if job_exists(
#             job["id"],
#             job["company"],
#             job["title"],
#         ):
#             job["is_new"] = False
#             continue

#         # job not in database, we parse the job description and store it
#         parsed = parse_job_description(
#             title=job["title"],
#             company=job["company"],
#             description=job.get("description"),
#         )

#         store_job(job, parsed)
#         job["is_new"] = True

#     new_count = sum(1 for j in sorted_jobs if j.get("is_new"))
#     print(f"New jobs stored this run: {new_count}")

#     return sorted_jobs


# if __name__ == "__main__":
#     jobs = fetch_all_jobs("Software Engineer", location="India")

#     print(f"\nFinal job count: {len(jobs)}\n")

#     for job in jobs[:20]:
#         print(f"{job.get('title')} - {job.get('company')} ({job.get('source')})")
#         print(f"Posted: {job.get('posted_at')}")
#         print(f"URL: {job.get('apply_url')}")
#         print("-" * 70)

"""
fetch_jobs.py

Orchestrates all job providers, then deduplicates and sorts the
combined results.

QUEUE-BASED PARSING: new jobs are inserted into the DB IMMEDIATELY
upon fetch (insert_raw_job), before any parsing happens - so no job
is ever lost even if the daily Groq budget can't cover parsing all of
them in one run. Parsing happens separately, as a FIFO queue drain
(process_unparsed_queue): oldest unparsed jobs (from ANY previous
run) are always processed before newly fetched ones, since they have
an earlier created_at. Each scheduled run continues draining the
queue from where the last run left off - self-healing across
multiple runs/days with zero data loss.
"""

import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import sys
import os
import traceback

from backend.jd_processor.jd_parser import parse_job_descriptions_batch, BATCH_SIZE, DailyBudgetExhaustedError
from backend.jd_processor.jobs_tidb_storage import job_exists, insert_raw_job, get_unparsed_jobs, mark_job_parsed
from backend.embedder.embeddings import generate_job_embedding

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

MAX_JOBS_PER_RUN = 300  # safety cap on how many unparsed jobs one run attempts


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


def _call_smartrecruiters(query, location):
    return smartrecruiters.fetch_jobs(role=query)


PROVIDERS = {
    "Adzuna": _call_adzuna,
    "JSearch": _call_jsearch,
    "Lever": _call_lever,
    "Greenhouse": _call_greenhouse,
    "Ashby": _call_ashby,
    "SmartRecruiters": _call_smartrecruiters,
}


def _fetch_from_provider(name, call_fn, query, location):
    try:
        jobs = call_fn(query, location)
        print(f"[{name}] {len(jobs)} jobs")
        return jobs
    except Exception as e:
        print(f"[{name}] FAILED: {e}")
        return []


def _fetch_all_providers_concurrently(queries, location):
    all_jobs = []

    tasks = [
        (query, name, call_fn)
        for query in queries
        for name, call_fn in PROVIDERS.items()
    ]

    max_workers = min(len(tasks), 20)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_fetch_from_provider, name, call_fn, query, location): (query, name)
            for query, name, call_fn in tasks
        }

        for future in as_completed(futures):
            all_jobs.extend(future.result())

    return all_jobs


def _normalize_key_part(value):
    if not value:
        return ""
    return re.sub(r"\s+", " ", value.strip().lower())


def _dedupe_jobs(jobs):
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
    if not ddmmyyyy_str:
        return datetime.min
    try:
        return datetime.strptime(ddmmyyyy_str, "%d%m%Y")
    except ValueError:
        return datetime.min


def _format_display_date(ddmmyyyy_str):
    if not ddmmyyyy_str or len(ddmmyyyy_str) != 8:
        return ddmmyyyy_str
    return f"{ddmmyyyy_str[0:2]}/{ddmmyyyy_str[2:4]}/{ddmmyyyy_str[4:8]}"


def _sort_jobs_by_date(jobs):
    return sorted(
        jobs,
        key=lambda j: _parse_posted_at(j.get("posted_at")),
        reverse=True,
    )


def process_unparsed_queue(max_jobs_per_run: int = MAX_JOBS_PER_RUN):
    """
    Pulls the oldest unparsed jobs (FIFO by created_at), parses them
    in batches via Groq, generates a Jina embedding for each
    successful parse, and marks it parsed=true - one job at a time
    within each batch's results, so a mid-batch failure doesn't lose
    progress on jobs already completed.

    Stops gracefully (NOT an error, doesn't fail the workflow) if the
    daily Groq budget is exhausted - remaining jobs stay parsed=false
    and are picked up automatically by a future run's FIFO queue.
    """
    unparsed = get_unparsed_jobs(limit=max_jobs_per_run)
    print(f"Unparsed queue: {len(unparsed)} job(s) to process this run (FIFO, oldest first).")

    for i in range(0, len(unparsed), BATCH_SIZE):
        chunk = unparsed[i:i + BATCH_SIZE]

        try:
            parsed_list = parse_job_descriptions_batch([
                {"title": j["title"], "company": j["company"], "description": (j["description"] or "")[:4000]}
                for j in chunk
            ])
        except DailyBudgetExhaustedError as e:
            remaining = len(unparsed) - i
            print(
                f"[fetch_jobs] Daily Groq budget exhausted - stopping gracefully for today. "
                f"{remaining} job(s) remain unparsed, will resume automatically next run. Detail: {e}"
            )
            return
        except Exception:
            print(f"[fetch_jobs] batch parse FAILED for queue positions {i}-{i+len(chunk)}")
            traceback.print_exc()
            continue  # this chunk's jobs stay unparsed, retried next run

        for job, parsed in zip(chunk, parsed_list):
            if parsed is None:
                continue  # missing from batch response - stays unparsed, retried next run

            try:
                embedding_text, embedding = generate_job_embedding(job, parsed)
                mark_job_parsed(job["row_id"], parsed, embedding_text, embedding)
            except Exception as e:
                print(
                    f"[fetch_jobs] embedding/mark_parsed FAILED for job row_id={job['row_id']}: {e} "
                    f"- stays unparsed, will be RE-PARSED next run (parsing succeeded but "
                    f"embedding didn't, so this job isn't marked complete)."
                )


def fetch_all_jobs(queries, location="India"):
    """
    Accepts a LIST of search queries. Runs all (query, provider)
    combinations concurrently, deduplicates the combined results
    across all queries, then inserts any genuinely new jobs
    IMMEDIATELY (unparsed) - no job is ever silently dropped even if
    parsing can't keep up. Finally drains the FIFO parsing queue for
    this run.

    Pass a single query as a one-item list: fetch_all_jobs(["Software Engineer"])
    """
    if isinstance(queries, str):
        queries = [queries]

    print("=" * 60)
    print(f"Fetching {len(queries)} quer{'y' if len(queries) == 1 else 'ies'} "
          f"from {len(PROVIDERS)} providers")
    print("=" * 60)

    raw_jobs = _fetch_all_providers_concurrently(queries, location)
    print(f"\nTotal before dedup: {len(raw_jobs)}")

    deduped_jobs = _dedupe_jobs(raw_jobs)
    removed = len(raw_jobs) - len(deduped_jobs)
    print(f"Total after dedup : {len(deduped_jobs)} (removed {removed} duplicates)")

    sorted_jobs = _sort_jobs_by_date(deduped_jobs)

    new_count = 0
    for job in sorted_jobs:
        job["posted_at"] = _format_display_date(job.get("posted_at"))

        if job_exists(job["id"], job["company"], job["title"]):
            job["is_new"] = False
            continue

        insert_raw_job(job)
        job["is_new"] = True
        new_count += 1

    print(f"New jobs inserted (unparsed) this run: {new_count}")

    process_unparsed_queue()

    return sorted_jobs


if __name__ == "__main__":
    jobs = fetch_all_jobs(["Software Engineer"], location="India")

    print(f"\nFinal job count: {len(jobs)}\n")

    for job in jobs[:20]:
        print(f"{job.get('title')} - {job.get('company')} ({job.get('source')})")
        print(f"Posted: {job.get('posted_at')}")
        print(f"URL: {job.get('apply_url')}")
        print("-" * 70)