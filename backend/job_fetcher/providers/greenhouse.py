# import html
# import json
# import re
# import requests
# from datetime import datetime
# from pathlib import Path



# GREENHOUSE_URL = "https://boards-api.greenhouse.io/v1/boards/{}/jobs"
# HERE = Path(__file__).parent

# _TAG_RE = re.compile(r"<[^>]+>")


# def _clean_description(raw_html):
#     """
#     Strip HTML tags/entities from Greenhouse's 'content' field.

#     Greenhouse returns content as HTML, and it can come through
#     double-encoded (e.g. the literal text "&lt;p&gt;" instead of a
#     real "<p>" tag). So we unescape first to normalize any encoded
#     entities into real characters, then strip tags, then unescape
#     once more to catch entities that were inside the original tags
#     (e.g. &amp;). This only removes markup - it does not alter or
#     guess at the actual text.
#     """
#     if not raw_html:
#         return raw_html

#     text = html.unescape(raw_html)      # normalize &lt;p&gt; -> <p> etc.
#     text = _TAG_RE.sub(" ", text)       # strip real tags
#     text = html.unescape(text)          # catch any remaining entities
#     text = re.sub(r"[ \t]+", " ", text)
#     text = re.sub(r"\n\s*\n+", "\n\n", text).strip()

#     return text


# def load_companies():

#     with open(HERE / "greenhouse_companies.json", encoding="utf-8") as f:
#         return json.load(f)


# def _parse_updated_at(value):
#     """Parse Greenhouse's ISO8601 updated_at into a sortable datetime."""
#     if not value:
#         return datetime.min
#     try:
#         return datetime.fromisoformat(value)
#     except ValueError:
#         return datetime.min


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

#             url = GREENHOUSE_URL.format(company)

#             response = requests.get(
#                 url,
#                 headers=headers,
#                 params={"content": "true"},
#                 timeout=20
#             )

#             if response.status_code != 200:
#                 print(f"Skipped ({response.status_code})")
#                 continue

#             jobs = response.json().get("jobs", [])

#             print(f"Found {len(jobs)} jobs")

#             for job in jobs:

#                 title = job.get("title", "")

#                 if role:

#                     if role.lower() not in title.lower():
#                         continue

#                 all_jobs.append({

#                     "provider": "greenhouse",

#                     "company": company,

#                     "job_id": job.get("id"),

#                     "title": title,

#                     "location": job.get("location", {}).get("name"),

#                     "url": job.get("absolute_url"),

#                     "updated_at": job.get("updated_at"),

#                     "description": _clean_description(job.get("content")),
#                 })

#         except Exception as e:

#             print(e)

#     if sort_by_date:
#         all_jobs.sort(
#             key=lambda j: _parse_updated_at(j.get("updated_at")),
#             reverse=True,
#         )

#     print("\n----------------------------")
#     print("Finished")
#     print("Matched Jobs :", len(all_jobs))
#     print("----------------------------")

#     return all_jobs


# if __name__ == "__main__":

#     jobs = fetch_jobs("Software Engineer")

#     print()

#     for job in jobs[:20]:
#         print(f"{job['title']} - {job['company']}")
#         print(f"Updated: {job['updated_at']}")
#         print(f"URL: {job['url']}")
#         print("JD:")
#         print(job['description'])
#         print("-" * 70)


# new norm code

import html
import json
import re
import requests
from datetime import datetime
from pathlib import Path



GREENHOUSE_URL = "https://boards-api.greenhouse.io/v1/boards/{}/jobs"
BASE_DIR = Path(__file__).parent.parent
COMPANIES_DIR = BASE_DIR / "companies"

SOURCE_NAME = "Greenhouse"

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

_TAG_RE = re.compile(r"<[^>]+>")


def _clean_description(raw_html):
    """
    Strip HTML tags/entities from Greenhouse's 'content' field.

    Greenhouse returns content as HTML, and it can come through
    double-encoded (e.g. the literal text "&lt;p&gt;" instead of a
    real "<p>" tag). So we unescape first to normalize any encoded
    entities into real characters, then strip tags, then unescape
    once more to catch entities that were inside the original tags
    (e.g. &amp;). This only removes markup - it does not alter or
    guess at the actual text.
    """
    if not raw_html:
        return raw_html

    text = html.unescape(raw_html)      # normalize &lt;p&gt; -> <p> etc.
    text = _TAG_RE.sub(" ", text)       # strip real tags
    text = html.unescape(text)          # catch any remaining entities
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text).strip()

    return text


def load_companies():

    with open(COMPANIES_DIR / "greenhouse_companies.json", encoding="utf-8") as f:
        return json.load(f)


def _parse_updated_at(value):
    """Parse Greenhouse's ISO8601 updated_at into a sortable datetime."""
    if not value:
        return datetime.min
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return datetime.min


def _format_date_ddmmyyyy(iso_date_str):
    """
    Convert Greenhouse's 'updated_at' (e.g. '2024-01-15T10:30:00-05:00')
    to ddmmyyyy format (e.g. '15012024'), matching the other providers.
    """
    if not iso_date_str:
        return None

    try:
        dt = datetime.fromisoformat(iso_date_str)
        return dt.strftime("%d%m%Y")
    except ValueError:
        return iso_date_str  # fall back to raw value rather than guessing


def _normalize_job(job, company, description):
    """
    Map a raw Greenhouse job dict -> the unified schema (see module
    docstring block above). Mirrors providers/adzuna.py's _normalize_job.

    Greenhouse's board API doesn't expose salary or employment-type
    fields, so those come through as None rather than guessed values.
    """
    native_id = job.get("id")

    return {
        "id": f"greenhouse_{native_id}" if native_id else None,
        "title": job.get("title", ""),
        "company": company,
        "location": job.get("location", {}).get("name"),
        "description": description,
        "salary_min": None,
        "salary_max": None,
        "salary_currency": None,
        "job_type": None,
        "posted_at": _format_date_ddmmyyyy(job.get("updated_at")),
        "apply_url": job.get("absolute_url"),
        "source": SOURCE_NAME,
    }


def fetch_jobs(role=None, sort_by_date=True):
    """
    Fetch jobs across all companies in greenhouse_companies.json,
    optionally filtered by role (case-insensitive substring match on
    title).

    Returns:
        list[dict] - each dict matches the unified job schema (see top
        of this file).
    """

    companies = load_companies()

    raw_matches = []  # (raw_job, company) pairs, pre-normalization, so we
                       # can still sort on the original updated_at value

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    print(f"\nCompanies to scan : {len(companies)}")

    for index, company in enumerate(companies, start=1):

        # print(f"\n[{index}/{len(companies)}] {company}")

        try:

            url = GREENHOUSE_URL.format(company)

            response = requests.get(
                url,
                headers=headers,
                params={"content": "true"},
                timeout=20
            )

            if response.status_code != 200:
                # print(f"Skipped ({response.status_code})")
                continue

            jobs = response.json().get("jobs", [])

            # print(f"Found {len(jobs)} jobs")

            for job in jobs:

                title = job.get("title", "")

                if role:

                    if role.lower() not in title.lower():
                        continue

                raw_matches.append((job, company))

        except Exception as e:

            print(e)

    if sort_by_date:
        raw_matches.sort(
            key=lambda pair: _parse_updated_at(pair[0].get("updated_at")),
            reverse=True,
        )

    all_jobs = [
        _normalize_job(job, company, _clean_description(job.get("content")))
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

    for job in jobs[:20]:
        print(f"{job['title']} - {job['company']}")
        print(f"Posted: {job['posted_at']}")
        print(f"URL: {job['apply_url']}")
        print("JD:")
        print(job['description'])
        print("-" * 70)