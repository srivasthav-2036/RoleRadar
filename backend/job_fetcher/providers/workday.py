import html
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import requests

BASE_DIR = Path(__file__).parent.parent
COMPANIES_DIR = BASE_DIR / "companies"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Content-Type": "application/json",
}

_TAG_RE = re.compile(r"<[^>]+>")


def _clean_description(raw_html):
    """
    Strip HTML tags/entities from Workday's jobDescription field.
    Unescapes before AND after tag-stripping in case of double-encoding.
    """
    if not raw_html:
        return raw_html

    text = html.unescape(raw_html)
    text = _TAG_RE.sub(" ", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text).strip()

    return text


def _parse_date(date_str):
    if not date_str:
        return datetime.min
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except (ValueError, TypeError):
        return datetime.min


def load_companies():
    """
    workday_companies.json

    Example:

    [
      {
        "company":"NVIDIA",
        "url":"https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite"
      },
      {
        "company":"Tesla",
        "url":"https://tesla.wd1.myworkdayjobs.com/TeslaCareers"
      }
    ]

    Note: unlike Lever/Greenhouse/Ashby, Workday tenant subdomains and
    site names can't be derived from the company name alone - each
    entry needs its real myworkdayjobs.com URL, found by visiting the
    company's actual careers page.
    """

    with open(COMPANIES_DIR / "workday_companies.json", "r", encoding="utf-8") as f:
        companies = json.load(f)

    for i, entry in enumerate(companies):
        if not isinstance(entry, dict) or "company" not in entry or "url" not in entry:
            raise ValueError(
                f"workday_companies.json entry #{i} is malformed: {entry!r}\n"
                "Each entry must be a dict with 'company' and 'url' keys "
                "(the full myworkdayjobs.com tenant URL) - a plain "
                "company-name string isn't enough for Workday."
            )

    return companies


def _build_api_urls(tenant_site_url):
    """
    Derive the actual Workday CXS API endpoints from the public-facing
    tenant URL.

    e.g. "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite"
    -> domain   = "nvidia.wd5.myworkdayjobs.com"
    -> tenant   = "nvidia"                (subdomain before ".wdN")
    -> site     = "NVIDIAExternalCareerSite"  (last path segment)
    -> search   = https://{domain}/wday/cxs/{tenant}/{site}/jobs
    -> detail   = https://{domain}/wday/cxs/{tenant}/{site}{externalPath}
    """
    parsed = urlparse(tenant_site_url)
    domain = parsed.netloc
    tenant = domain.split(".")[0]
    site = parsed.path.strip("/").split("/")[-1]

    search_url = f"https://{domain}/wday/cxs/{tenant}/{site}/jobs"
    detail_base_url = f"https://{domain}/wday/cxs/{tenant}/{site}"

    return search_url, detail_base_url


def _fetch_job_detail(detail_base_url, external_path):
    """One extra request per job for the full JD - the search endpoint
    only returns summary fields, not description text."""
    try:
        url = detail_base_url + external_path

        response = requests.post(url, headers=HEADERS, timeout=20)

        if response.status_code != 200:
            return None, None

        data = response.json()
        posting_info = data.get("jobPostingInfo", {})

        description = _clean_description(posting_info.get("jobDescription"))
        job_req_id = posting_info.get("jobReqId")

        return description, job_req_id

    except Exception:
        return None, None


def _fetch_company(company, role=None, fetch_descriptions=True):

    jobs = []

    search_url, detail_base_url = _build_api_urls(company["url"])

    offset = 0
    limit = 20

    while True:

        payload = {
            "limit": limit,
            "offset": offset,
            "searchText": "",
        }

        try:

            response = requests.post(
                search_url,
                headers=HEADERS,
                json=payload,
                timeout=30
            )

            if response.status_code != 200:
                print(f"Skipped ({response.status_code})")
                break

            data = response.json()

            postings = data.get("jobPostings", [])

            if not postings:
                break

            print(f"Fetched {len(postings)} jobs")

            for job in postings:

                title = job.get("title", "")

                if role:
                    if role.lower() not in title.lower():
                        continue

                external_path = job.get("externalPath", "")

                description = None
                job_req_id = None

                if fetch_descriptions and external_path:
                    description, job_req_id = _fetch_job_detail(detail_base_url, external_path)

                jobs.append({

                    "provider": "workday",

                    "company": company["company"],

                    "job_id": job_req_id,

                    "title": title,

                    "location": job.get("locationsText"),

                    "country": None,

                    "department": None,

                    "employment_type": None,

                    "experience": None,

                    "released": job.get("postedOn"),

                    "url": company["url"].rstrip("/") + external_path,

                    "description": description,

                })

            offset += limit

        except Exception as e:
            print(e)
            break

    return jobs


def fetch_jobs(role=None, sort_by_date=True, fetch_descriptions=True):

    companies = load_companies()

    print(f"\nCompanies to scan : {len(companies)}")

    all_jobs = []

    for index, company in enumerate(companies, start=1):

        print(f"\n[{index}/{len(companies)}] {company['company']}")

        jobs = _fetch_company(company, role, fetch_descriptions)

        print(f"Matched : {len(jobs)}")

        all_jobs.extend(jobs)

    if sort_by_date:

        all_jobs.sort(
            key=lambda x: _parse_date(x["released"]),
            reverse=True
        )

    print("\n----------------------------")
    print("Finished")
    print("Matched Jobs :", len(all_jobs))
    print("----------------------------")

    return all_jobs


if __name__ == "__main__":

    jobs = fetch_jobs("Software Engineer")

    print()

    for job in jobs[:20]:

        print(job["title"])
        print(job["company"])
        print(job["location"])
        print(job["released"])
        print(job["url"])
        print("JD:")
        print(job["description"])
        print("-" * 70)