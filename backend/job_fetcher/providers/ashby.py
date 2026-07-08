# import json
# from datetime import datetime
# from pathlib import Path

# import requests

# HERE = Path(__file__).parent

# ASHBY_URL = "https://jobs.ashbyhq.com/api/non-user-graphql"

# BOARD_QUERY = """
# query ApiJobBoardWithTeams($organizationHostedJobsPageName: String!) {
#   jobBoard: jobBoardWithTeams(
#     organizationHostedJobsPageName: $organizationHostedJobsPageName
#   ) {
#     teams {
#       id
#       name
#       externalName
#       parentTeamId
#     }
#     jobPostings {
#       id
#       title
#       teamId
#       locationId
#       locationName
#       workplaceType
#       employmentType
#       secondaryLocations {
#         locationId
#         locationName
#       }
#       compensationTierSummary
#       publishedDate
#     }
#   }
# }
# """

# # Separate query needed for full JD - the board query above intentionally
# # omits description text since it's a listings endpoint.
# JOB_DETAIL_QUERY = """
# query ApiJobPosting($organizationHostedJobsPageName: String!, $jobPostingId: String!) {
#   jobPosting(
#     organizationHostedJobsPageName: $organizationHostedJobsPageName
#     jobPostingId: $jobPostingId
#   ) {
#     id
#     descriptionHtml
#     descriptionPlain
#   }
# }
# """


# def load_companies():
#     with open(HERE / "ashby_companies.json", "r", encoding="utf-8") as f:
#         return json.load(f)


# def _parse_published_date(value):
#     if not value:
#         return datetime.min
#     try:
#         return datetime.fromisoformat(value.replace("Z", "+00:00"))
#     except ValueError:
#         return datetime.min


# def _fetch_description(company, job_id, headers):
#     """One extra request per job to get the full JD text."""

#     payload = {
#         "operationName": "ApiJobPosting",
#         "variables": {
#             "organizationHostedJobsPageName": company,
#             "jobPostingId": job_id,
#         },
#         "query": JOB_DETAIL_QUERY,
#     }

#     try:
#         response = requests.post(
#             ASHBY_URL,
#             json=payload,
#             headers=headers,
#             timeout=20,
#         )

#         if response.status_code != 200:
#             return None

#         posting = response.json().get("data", {}).get("jobPosting") or {}

#         return posting.get("descriptionPlain") or posting.get("descriptionHtml")

#     except Exception:
#         return None


# def fetch_jobs(role=None, sort_by_date=True, fetch_descriptions=True):

#     companies = load_companies()

#     headers = {
#         "User-Agent": "Mozilla/5.0",
#         "Content-Type": "application/json"
#     }

#     all_jobs = []

#     print(f"\nCompanies to scan : {len(companies)}")

#     for index, company in enumerate(companies, start=1):

#         print(f"\n[{index}/{len(companies)}] {company}")

#         payload = {
#             "operationName": "ApiJobBoardWithTeams",
#             "variables": {
#                 "organizationHostedJobsPageName": company
#             },
#             "query": BOARD_QUERY
#         }

#         try:

#             response = requests.post(
#                 ASHBY_URL,
#                 json=payload,
#                 headers=headers,
#                 timeout=20
#             )

#             if response.status_code != 200:
#                 print(f"Skipped ({response.status_code})")
#                 continue

#             data = response.json()

#             job_board = data.get("data", {}).get("jobBoard")

#             if not job_board:
#                 print("No jobs found")
#                 continue

#             teams = {
#                 team["id"]: team.get("externalName") or team.get("name")
#                 for team in job_board.get("teams", [])
#             }

#             jobs = job_board.get("jobPostings", [])

#             print(f"Found {len(jobs)} jobs")

#             for job in jobs:

#                 title = job.get("title", "")

#                 if role and role.lower() not in title.lower():
#                     continue

#                 secondary_locations = [
#                     loc["locationName"]
#                     for loc in job.get("secondaryLocations", [])
#                 ]

#                 job_id = job.get("id")

#                 description = None
#                 if fetch_descriptions:
#                     description = _fetch_description(company, job_id, headers)

#                 all_jobs.append({

#                     "provider": "ashby",

#                     "company": company,

#                     "job_id": job_id,

#                     "title": title,

#                     "location": job.get("locationName"),

#                     "secondary_locations": secondary_locations,

#                     "department": teams.get(job.get("teamId")),

#                     "employment_type": job.get("employmentType"),

#                     "workplace_type": job.get("workplaceType"),

#                     "salary": job.get("compensationTierSummary"),

#                     "published_date": job.get("publishedDate"),

#                     "description": description,

#                     "url": f"https://jobs.ashbyhq.com/{company}/{job_id}"
#                 })

#         except Exception as e:
#             print(e)

#     if sort_by_date:
#         all_jobs.sort(
#             key=lambda j: _parse_published_date(j.get("published_date")),
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

#     for job in jobs[:5]:
#         print(f"{job['title']} - {job['company']}")
#         print(f"Published: {job['published_date']}")
#         print(f"URL: {job['url']}")
#         print("JD:")
#         print(job['description'])
#         print("-" * 70)

#new norm code

import json
from datetime import datetime
from pathlib import Path

import requests

BASE_DIR = Path(__file__).parent.parent
COMPANIES_DIR = BASE_DIR / "companies"

ASHBY_URL = "https://jobs.ashbyhq.com/api/non-user-graphql"

SOURCE_NAME = "Ashby"

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

BOARD_QUERY = """
query ApiJobBoardWithTeams($organizationHostedJobsPageName: String!) {
  jobBoard: jobBoardWithTeams(
    organizationHostedJobsPageName: $organizationHostedJobsPageName
  ) {
    teams {
      id
      name
      externalName
      parentTeamId
    }
    jobPostings {
      id
      title
      teamId
      locationId
      locationName
      workplaceType
      employmentType
      secondaryLocations {
        locationId
        locationName
      }
      compensationTierSummary
      publishedDate
    }
  }
}
"""

# Separate query needed for full JD - the board query above intentionally
# omits description text since it's a listings endpoint.
JOB_DETAIL_QUERY = """
query ApiJobPosting($organizationHostedJobsPageName: String!, $jobPostingId: String!) {
  jobPosting(
    organizationHostedJobsPageName: $organizationHostedJobsPageName
    jobPostingId: $jobPostingId
  ) {
    id
    descriptionHtml
    descriptionPlain
  }
}
"""


def load_companies():
    with open(COMPANIES_DIR / "ashby_companies.json", "r", encoding="utf-8") as f:
        return json.load(f)


def _parse_published_date(value):
    if not value:
        return datetime.min
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.min


def _format_date_ddmmyyyy(iso_date_str):
    """
    Convert Ashby's 'publishedDate' (e.g. '2024-01-15T10:30:00Z') to
    ddmmyyyy format (e.g. '15012024'), matching the other providers.
    """
    if not iso_date_str:
        return None

    try:
        dt = datetime.fromisoformat(iso_date_str.replace("Z", "+00:00"))
        return dt.strftime("%d%m%Y")
    except ValueError:
        return iso_date_str  # fall back to raw value rather than guessing


def _fetch_description(company, job_id, headers):
    """One extra request per job to get the full JD text."""

    payload = {
        "operationName": "ApiJobPosting",
        "variables": {
            "organizationHostedJobsPageName": company,
            "jobPostingId": job_id,
        },
        "query": JOB_DETAIL_QUERY,
    }

    try:
        response = requests.post(
            ASHBY_URL,
            json=payload,
            headers=headers,
            timeout=20,
        )

        if response.status_code != 200:
            return None

        posting = response.json().get("data", {}).get("jobPosting") or {}

        return posting.get("descriptionPlain") or posting.get("descriptionHtml")

    except Exception:
        return None


def _normalize_job(job, company, description, apply_url):
    """
    Map a raw Ashby job dict -> the unified schema (see module docstring
    block above). Mirrors providers/adzuna.py's _normalize_job.

    Ashby doesn't expose numeric salary fields - compensationTierSummary
    is a free-text tier label (e.g. "Tier 1"), not a min/max/currency
    breakdown, so salary_min/max/currency come through as None rather
    than guessed values. department, secondary_locations, and
    workplace_type are dropped since they're not part of the unified
    schema.
    """
    native_id = job.get("id")

    return {
        "id": f"ashby_{native_id}" if native_id else None,
        "title": job.get("title", ""),
        "company": company,
        "location": job.get("locationName"),
        "description": description,
        "salary_min": None,
        "salary_max": None,
        "salary_currency": None,
        "job_type": job.get("employmentType"),
        "posted_at": _format_date_ddmmyyyy(job.get("publishedDate")),
        "apply_url": apply_url,
        "source": SOURCE_NAME,
    }


def fetch_jobs(role=None, sort_by_date=True, fetch_descriptions=True):
    """
    Fetch jobs across all companies in ashby_companies.json, optionally
    filtered by role (case-insensitive substring match on title).

    Returns:
        list[dict] - each dict matches the unified job schema (see top
        of this file).
    """

    companies = load_companies()

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json"
    }

    raw_matches = []  # (raw_job, company, description, apply_url) pre-normalization,
                       # so we can still sort on the original publishedDate value

    print(f"\nCompanies to scan : {len(companies)}")

    for index, company in enumerate(companies, start=1):

        print(f"\n[{index}/{len(companies)}] {company}")

        payload = {
            "operationName": "ApiJobBoardWithTeams",
            "variables": {
                "organizationHostedJobsPageName": company
            },
            "query": BOARD_QUERY
        }

        try:

            response = requests.post(
                ASHBY_URL,
                json=payload,
                headers=headers,
                timeout=20
            )

            if response.status_code != 200:
                print(f"Skipped ({response.status_code})")
                continue

            data = response.json()

            job_board = data.get("data", {}).get("jobBoard")

            if not job_board:
                print("No jobs found")
                continue

            jobs = job_board.get("jobPostings", [])

            print(f"Found {len(jobs)} jobs")

            for job in jobs:

                title = job.get("title", "")

                if role and role.lower() not in title.lower():
                    continue

                job_id = job.get("id")

                description = None
                if fetch_descriptions:
                    description = _fetch_description(company, job_id, headers)

                apply_url = f"https://jobs.ashbyhq.com/{company}/{job_id}"

                raw_matches.append((job, company, description, apply_url))

        except Exception as e:
            print(e)

    if sort_by_date:
        raw_matches.sort(
            key=lambda item: _parse_published_date(item[0].get("publishedDate")),
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

    for job in jobs[:5]:
        print(f"{job['title']} - {job['company']}")
        print(f"Job type: {job['job_type']}")
        print(f"Posted: {job['posted_at']}")
        print(f"URL: {job['apply_url']}")
        print("JD:")
        print(job['description'])
        print("-" * 70)