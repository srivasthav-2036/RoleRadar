# import json
# from pathlib import Path

# import requests

# HERE = Path(__file__).parent

# LEVER_URL = "https://api.lever.co/v0/postings/{company}?mode=json"


# def load_companies():
#     with open(HERE / "lever_companies.json", "r", encoding="utf-8") as f:
#         return json.load(f)


# def fetch_jobs(role=None, sort_by_date=True):

#     companies = load_companies()

#     all_jobs = []

#     headers = {
#         "User-Agent": "Mozilla/5.0"
#     }

#     print(f"\nCompanies to scan : {len(companies)}")

#     for index, company in enumerate(companies, start=1):

#         print(f"\n[{index}/{len(companies)}] {company}")

#         try:

#             url = LEVER_URL.format(company=company)

#             response = requests.get(
#                 url,
#                 headers=headers,
#                 timeout=20
#             )

#             if response.status_code != 200:
#                 print(f"Skipped ({response.status_code})")
#                 continue

#             jobs = response.json()

#             print(f"Found {len(jobs)} jobs")

#             for job in jobs:

#                 title = job.get("text", "")

#                 if role:
#                     if role.lower() not in title.lower():
#                         continue

#                 categories = job.get("categories", {})

#                 # Lever's "lists" field holds extra JD sections like
#                 # "What you'll do", "Requirements", etc.
#                 lists = job.get("lists", [])
#                 extra_sections = []
#                 for section in lists:
#                     section_text = section.get("text", "")
#                     section_content = section.get("content", "")
#                     extra_sections.append(f"{section_text}\n{section_content}")

#                 all_jobs.append({
#                     "provider": "lever",

#                     "company": company,

#                     "job_id": job.get("id"),

#                     "title": title,

#                     "location": categories.get("location"),

#                     "department": categories.get("team"),

#                     "commitment": categories.get("commitment"),

#                     "workplace": categories.get("workplace"),

#                     "url": job.get("hostedUrl"),

#                     "created_at": job.get("createdAt"),

#                     "updated_at": job.get("updatedAt"),

#                     "description": job.get("descriptionPlain") or job.get("description"),

#                     "description_sections": "\n\n".join(extra_sections),
#                 })

#         except Exception as e:
#             print(e)

#     if sort_by_date:
#         # createdAt is epoch millis; missing values sort last
#         all_jobs.sort(key=lambda j: j.get("created_at") or 0, reverse=True)

#     print("\n----------------------------")
#     print("Finished")
#     print("Matched Jobs :", len(all_jobs))
#     print("----------------------------")

#     return all_jobs


# if __name__ == "__main__":

#     jobs = fetch_jobs("Software Engineer")

#     print()

#     for job in jobs[:5]:
#         print(f"{job['title']} - {job['company']}")
#         print(f"Posted (epoch ms): {job['created_at']}")
#         print(f"URL: {job['url']}")
#         print("JD:")
#         print(job['description'])
#         if job['description_sections']:
#             print("\nAdditional sections:")
#             print(job['description_sections'])
#         print("-" * 70)

# new norm code

import json
from datetime import datetime
from pathlib import Path

import requests

BASE_DIR = Path(__file__).parent.parent
COMPANIES_DIR = BASE_DIR / "companies"

LEVER_URL = "https://api.lever.co/v0/postings/{company}?mode=json"

SOURCE_NAME = "Lever"

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


def load_companies():
    with open(COMPANIES_DIR / "lever_companies.json", "r", encoding="utf-8") as f:
        return json.load(f)


def _format_date_ddmmyyyy(epoch_millis):
    """
    Convert Lever's 'createdAt' (epoch milliseconds, e.g. 1705315800000)
    to ddmmyyyy format (e.g. '15012024'), matching the other providers.
    Lever is the only provider that gives epoch millis instead of an
    ISO8601 string, so this parser is different from the others.
    """
    if not epoch_millis:
        return None

    try:
        dt = datetime.fromtimestamp(epoch_millis / 1000)
        return dt.strftime("%d%m%Y")
    except (ValueError, OSError, TypeError):
        return None  # unparseable rather than guessing


def _build_description(job):
    """
    Lever splits JD text across a main description field and a separate
    'lists' field (extra sections like "What you'll do", "Requirements").
    The unified schema only has one description field, so both are
    merged here into a single block of text.
    """
    main_text = job.get("descriptionPlain") or job.get("description") or ""

    extra_sections = []
    for section in job.get("lists", []):
        section_text = section.get("text", "")
        section_content = section.get("content", "")
        extra_sections.append(f"{section_text}\n{section_content}")

    combined = "\n\n".join([main_text] + extra_sections) if extra_sections else main_text

    return combined.strip() or None


def _normalize_job(job, company):
    """
    Map a raw Lever job dict -> the unified schema (see module docstring
    block above). Mirrors providers/adzuna.py's _normalize_job.

    Lever doesn't expose salary fields, so those come through as None
    rather than guessed values. department and workplace (remote/onsite)
    are dropped since they're not part of the unified schema.
    """
    native_id = job.get("id")
    categories = job.get("categories", {})

    return {
        "id": f"lever_{native_id}" if native_id else None,
        "title": job.get("text", ""),
        "company": company,
        "location": categories.get("location"),
        "description": _build_description(job),
        "salary_min": None,
        "salary_max": None,
        "salary_currency": None,
        "job_type": categories.get("commitment"),
        "posted_at": _format_date_ddmmyyyy(job.get("createdAt")),
        "apply_url": job.get("hostedUrl"),
        "source": SOURCE_NAME,
    }


def fetch_jobs(role=None, sort_by_date=True):
    """
    Fetch jobs across all companies in lever_companies.json, optionally
    filtered by role (case-insensitive substring match on title).

    Returns:
        list[dict] - each dict matches the unified job schema (see top
        of this file).
    """

    companies = load_companies()

    raw_matches = []  # (raw_job, company) pairs, pre-normalization, so we
                       # can still sort on the original epoch createdAt value

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    print(f"\nCompanies to scan : {len(companies)}")

    for index, company in enumerate(companies, start=1):

        # print(f"\n[{index}/{len(companies)}] {company}")

        try:

            url = LEVER_URL.format(company=company)

            response = requests.get(
                url,
                headers=headers,
                timeout=20
            )

            if response.status_code != 200:
                # print(f"Skipped ({response.status_code})")
                continue

            jobs = response.json()

            # print(f"Found {len(jobs)} jobs")

            for job in jobs:

                title = job.get("text", "")

                if role:
                    if role.lower() not in title.lower():
                        continue

                raw_matches.append((job, company))

        except Exception as e:
            print(e)

    if sort_by_date:
        # createdAt is epoch millis; missing values sort last
        raw_matches.sort(key=lambda pair: pair[0].get("createdAt") or 0, reverse=True)

    all_jobs = [
        _normalize_job(job, company)
        for job, company in raw_matches
    ]

    print("\n----------------------------")
    print("Finished")
    print("Matched Jobs :", len(all_jobs))
    print("----------------------------")

    return all_jobs


if __name__ == "__main__":

    jobs = fetch_jobs("Software Engineer")

    print()

    for job in jobs[:5]:
        print(f"{job['title']} - {job['company']}")
        print(f"Job type: {job['job_type']}")
        print(f"Posted: {job['posted_at']}")
        print(f"URL: {job['apply_url']}")
        print("JD:")
        print(job['description'])
        print("-" * 70)