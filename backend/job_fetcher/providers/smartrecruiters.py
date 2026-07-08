# import html
# import json
# import re
# from datetime import datetime
# from pathlib import Path

# import requests

# HERE = Path(__file__).parent

# SMART_URL = "https://api.smartrecruiters.com/v1/companies/{}/postings"
# SMART_DETAIL_URL = "https://api.smartrecruiters.com/v1/companies/{}/postings/{}"

# _TAG_RE = re.compile(r"<[^>]+>")


# def _clean_description(raw_html):
#     """
#     Strip HTML tags/entities from SmartRecruiters' jobAd section text.
#     Unescapes before AND after tag-stripping in case of double-encoding.
#     This only removes markup - it does not alter or guess at the text.
#     """
#     if not raw_html:
#         return raw_html

#     text = html.unescape(raw_html)
#     text = _TAG_RE.sub(" ", text)
#     text = html.unescape(text)
#     text = re.sub(r"[ \t]+", " ", text)
#     text = re.sub(r"\n\s*\n+", "\n\n", text).strip()

#     return text


# def _flatten_label(field):
#     """
#     SmartRecruiters returns department/employment_type/experience as
#     nested dicts like {'id': '...', 'label': '...'}. This pulls just
#     the human-readable label instead of the raw dict.
#     """
#     if isinstance(field, dict):
#         return field.get("label")
#     return field


# def _parse_released(value):
#     """Parse SmartRecruiters' ISO8601 'releasedDate' into a sortable datetime."""
#     if not value:
#         return datetime.min
#     try:
#         return datetime.fromisoformat(value.replace("Z", "+00:00"))
#     except ValueError:
#         return datetime.min


# def load_companies():
#     with open(HERE / "smartrecruiters_companies.json", "r", encoding="utf-8") as f:
#         return json.load(f)


# def _fetch_full_description(company, job_id, headers):
#     """
#     One extra request per job to get the full JD - SmartRecruiters'
#     list endpoint only returns summary fields. Full text lives under
#     jobAd.sections in the detail response. Also returns the real
#     public apply URL, since the list endpoint's 'ref' field is just
#     the internal API link, not something a person can open.
#     """
#     try:
#         url = SMART_DETAIL_URL.format(company, job_id)

#         response = requests.get(url, headers=headers, timeout=20)

#         if response.status_code != 200:
#             return None, None

#         detail = response.json()

#         sections_data = detail.get("jobAd", {}).get("sections", {})

#         sections = []
#         for key in ("jobDescription", "qualifications", "additionalInformation"):
#             section = sections_data.get(key, {})
#             text = section.get("text")
#             if text:
#                 title = section.get("title") or key
#                 sections.append(f"{title}\n{_clean_description(text)}")

#         description = "\n\n".join(sections) if sections else None
#         apply_url = detail.get("applyUrl")

#         return description, apply_url

#     except Exception:
#         return None, None


# def fetch_jobs(role=None, sort_by_date=True, fetch_descriptions=True):

#     companies = load_companies()

#     headers = {
#         "User-Agent": "Mozilla/5.0",
#         "Accept": "application/json"
#     }

#     all_jobs = []

#     print(f"\nCompanies to scan : {len(companies)}")

#     for index, company in enumerate(companies, start=1):

#         print(f"\n[{index}/{len(companies)}] {company}")

#         try:

#             response = requests.get(
#                 SMART_URL.format(company),
#                 headers=headers,
#                 timeout=20
#             )

#             if response.status_code != 200:
#                 print(f"Skipped ({response.status_code})")
#                 continue

#             jobs = response.json().get("content", [])

#             print(f"Found {len(jobs)} jobs")

#             for job in jobs:

#                 title = job.get("name", "")

#                 if role:
#                     if role.lower() not in title.lower():
#                         continue

#                 location = job.get("location", {})

#                 job_id = job.get("id")

#                 description = None
#                 apply_url = job.get("ref")  # fallback if detail call fails/is skipped

#                 if fetch_descriptions and job_id:
#                     description, fetched_url = _fetch_full_description(company, job_id, headers)
#                     if fetched_url:
#                         apply_url = fetched_url

#                 all_jobs.append({

#                     "provider": "smartrecruiters",

#                     "company": company,

#                     "job_id": job_id,

#                     "title": title,

#                     "location": location.get("city"),

#                     "country": location.get("country"),

#                     "department": _flatten_label(job.get("department")),

#                     "employment_type": _flatten_label(job.get("typeOfEmployment")),

#                     "experience": _flatten_label(job.get("experienceLevel")),

#                     "url": apply_url,

#                     "released": job.get("releasedDate"),

#                     "description": description,
#                 })

#         except Exception as e:

#             print(e)

#     if sort_by_date:
#         all_jobs.sort(
#             key=lambda j: _parse_released(j.get("released")),
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
#         print(f"Location: {job['location']}, {job['country']}")
#         print(f"Department: {job['department']} | {job['employment_type']} | {job['experience']}")
#         print(f"Released: {job['released']}")
#         print(f"URL: {job['url']}")
#         print("JD:")
#         print(job['description'])
#         print("-" * 70)


# new norm code

import html
import json
import re
from datetime import datetime
from pathlib import Path

import requests

BASE_DIR = Path(__file__).parent.parent
COMPANIES_DIR = BASE_DIR / "companies"

SMART_URL = "https://api.smartrecruiters.com/v1/companies/{}/postings"
SMART_DETAIL_URL = "https://api.smartrecruiters.com/v1/companies/{}/postings/{}"

SOURCE_NAME = "SmartRecruiters"

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
    Strip HTML tags/entities from SmartRecruiters' jobAd section text.
    Unescapes before AND after tag-stripping in case of double-encoding.
    This only removes markup - it does not alter or guess at the text.
    """
    if not raw_html:
        return raw_html

    text = html.unescape(raw_html)
    text = _TAG_RE.sub(" ", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text).strip()

    return text


def _flatten_label(field):
    """
    SmartRecruiters returns department/employment_type/experience as
    nested dicts like {'id': '...', 'label': '...'}. This pulls just
    the human-readable label instead of the raw dict.
    """
    if isinstance(field, dict):
        return field.get("label")
    return field


def _build_location(location):
    """
    Combine SmartRecruiters' separate city/country fields into a single
    'location' string, matching the unified schema (one location field,
    not separate city/country keys).
    """
    city = location.get("city")
    country = location.get("country")
    parts = [p for p in (city, country) if p]
    return ", ".join(parts) if parts else None


def _parse_released(value):
    """Parse SmartRecruiters' ISO8601 'releasedDate' into a sortable datetime."""
    if not value:
        return datetime.min
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.min


def _format_date_ddmmyyyy(iso_date_str):
    """
    Convert SmartRecruiters' 'releasedDate' (e.g. '2024-01-15T10:30:00Z')
    to ddmmyyyy format (e.g. '15012024'), matching the other providers.
    """
    if not iso_date_str:
        return None

    try:
        dt = datetime.fromisoformat(iso_date_str.replace("Z", "+00:00"))
        return dt.strftime("%d%m%Y")
    except ValueError:
        return iso_date_str  # fall back to raw value rather than guessing


def load_companies():
    with open(COMPANIES_DIR / "smartrecruiters_companies.json", "r", encoding="utf-8") as f:
        return json.load(f)


def _fetch_full_description(company, job_id, headers):
    """
    One extra request per job to get the full JD - SmartRecruiters'
    list endpoint only returns summary fields. Full text lives under
    jobAd.sections in the detail response. Also returns the real
    public apply URL, since the list endpoint's 'ref' field is just
    the internal API link, not something a person can open.
    """
    try:
        url = SMART_DETAIL_URL.format(company, job_id)

        response = requests.get(url, headers=headers, timeout=20)

        if response.status_code != 200:
            return None, None

        detail = response.json()

        sections_data = detail.get("jobAd", {}).get("sections", {})

        sections = []
        for key in ("jobDescription", "qualifications", "additionalInformation"):
            section = sections_data.get(key, {})
            text = section.get("text")
            if text:
                title = section.get("title") or key
                sections.append(f"{title}\n{_clean_description(text)}")

        description = "\n\n".join(sections) if sections else None
        apply_url = detail.get("applyUrl")

        return description, apply_url

    except Exception:
        return None, None


def _normalize_job(job, company, description, apply_url):
    """
    Map a raw SmartRecruiters job dict -> the unified schema (see module
    docstring block above). Mirrors providers/adzuna.py's _normalize_job.

    SmartRecruiters doesn't expose salary fields, so those come through
    as None rather than guessed values. department/experience are
    dropped since they're not part of the unified schema.
    """
    native_id = job.get("id")

    return {
        "id": f"smartrecruiters_{native_id}" if native_id else None,
        "title": job.get("name", ""),
        "company": company,
        "location": _build_location(job.get("location", {})),
        "description": description,
        "salary_min": None,
        "salary_max": None,
        "salary_currency": None,
        "job_type": _flatten_label(job.get("typeOfEmployment")),
        "posted_at": _format_date_ddmmyyyy(job.get("releasedDate")),
        "apply_url": apply_url,
        "source": SOURCE_NAME,
    }


def fetch_jobs(role=None, sort_by_date=True, fetch_descriptions=True):
    """
    Fetch jobs across all companies in smartrecruiters_companies.json,
    optionally filtered by role (case-insensitive substring match on
    title).

    Returns:
        list[dict] - each dict matches the unified job schema (see top
        of this file).
    """

    companies = load_companies()

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }

    raw_matches = []  # (raw_job, company, description, apply_url) pre-normalization,
                       # so we can still sort on the original releasedDate value

    print(f"\nCompanies to scan : {len(companies)}")

    for index, company in enumerate(companies, start=1):

        print(f"\n[{index}/{len(companies)}] {company}")

        try:

            response = requests.get(
                SMART_URL.format(company),
                headers=headers,
                timeout=20
            )

            if response.status_code != 200:
                print(f"Skipped ({response.status_code})")
                continue

            jobs = response.json().get("content", [])

            print(f"Found {len(jobs)} jobs")

            for job in jobs:

                title = job.get("name", "")

                if role:
                    if role.lower() not in title.lower():
                        continue

                job_id = job.get("id")

                description = None
                apply_url = job.get("ref")  # fallback if detail call fails/is skipped

                if fetch_descriptions and job_id:
                    description, fetched_url = _fetch_full_description(company, job_id, headers)
                    if fetched_url:
                        apply_url = fetched_url

                raw_matches.append((job, company, description, apply_url))

        except Exception as e:

            print(e)

    if sort_by_date:
        raw_matches.sort(
            key=lambda item: _parse_released(item[0].get("releasedDate")),
            reverse=True,
        )

    all_jobs = [
        _normalize_job(job, company, description, apply_url)
        for job, company, description, apply_url in raw_matches
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
        print(f"Location: {job['location']}")
        print(f"Job type: {job['job_type']}")
        print(f"Posted: {job['posted_at']}")
        print(f"URL: {job['apply_url']}")
        print("JD:")
        print(job['description'])
        print("-" * 70)