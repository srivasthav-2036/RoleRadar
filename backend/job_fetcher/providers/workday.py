import html
import json
import re
import requests
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


BASE_DIR = Path(__file__).parent.parent
COMPANIES_DIR = BASE_DIR / "companies"

SOURCE_NAME = "Workday"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
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

_TAG_RE = re.compile(r"<[^>]+>")


def _clean_description(raw_html):
    """
    Strip HTML tags/entities from Workday's jobDescription field.

    Same double-unescape approach as greenhouse.py's _clean_description,
    since Workday's content can also come through double-encoded (e.g.
    the literal text "&lt;p&gt;" instead of a real "<p>" tag).
    """
    if not raw_html:
        return raw_html

    text = html.unescape(raw_html)
    text = _TAG_RE.sub(" ", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text).strip()

    return text


def load_companies():
    """
    workday_companies.json

    Example:
    [
      {"company": "NVIDIA", "url": "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite"},
      {"company": "Tesla",  "url": "https://tesla.wd1.myworkdayjobs.com/TeslaCareers"}
    ]

    Note: unlike Lever/Greenhouse/Ashby, Workday tenant subdomains and
    site names can't be derived from the company name alone - each
    entry needs its real myworkdayjobs.com URL, found by visiting the
    company's actual careers page.
    """
    with open(COMPANIES_DIR / "workday_companies.json", encoding="utf-8") as f:
        companies = json.load(f)

    for i, entry in enumerate(companies):
        if not isinstance(entry, dict) or "company" not in entry or "url" not in entry:
            raise ValueError(
                f"workday_companies.json entry #{i} is malformed: {entry!r}\n"
                "Each entry must be a dict with 'company' and 'url' keys "
                "(the full myworkdayjobs.com tenant URL)."
            )

    return companies


def _build_api_urls(tenant_site_url):
    """
    Derive the Workday CXS API endpoints from the public-facing tenant URL.

    e.g. "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite"
    -> domain = "nvidia.wd5.myworkdayjobs.com"
    -> tenant = "nvidia"                       (subdomain before ".wdN")
    -> site   = "NVIDIAExternalCareerSite"     (last path segment)
    -> search_url      = https://{domain}/wday/cxs/{tenant}/{site}/jobs
    -> detail_base_url = https://{domain}/wday/cxs/{tenant}/{site}
    """
    parsed = urlparse(tenant_site_url)
    domain = parsed.netloc
    tenant = domain.split(".")[0]
    site = parsed.path.strip("/").split("/")[-1]

    search_url = f"https://{domain}/wday/cxs/{tenant}/{site}/jobs"
    detail_base_url = f"https://{domain}/wday/cxs/{tenant}/{site}"

    return search_url, detail_base_url


def _parse_iso_date(value):
    """Parse Workday's ISO 'startDate' (e.g. '2026-07-01') into a sortable datetime."""
    if not value:
        return datetime.min
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.min


def _format_date_ddmmyyyy(iso_date_str):
    """Convert an ISO date string to ddmmyyyy, matching the other providers."""
    if not iso_date_str:
        return None
    try:
        dt = datetime.fromisoformat(iso_date_str.replace("Z", "+00:00"))
        return dt.strftime("%d%m%Y")
    except ValueError:
        return None


def _fetch_job_detail(detail_base_url, external_path):
    """
    One extra request per job for the full JD, exact posted date, and
    job type - Workday's search endpoint only returns summary fields
    and a vague relative posted string (e.g. "Posted 30+ Days Ago"),
    not real values.
    """
    try:
        url = detail_base_url + external_path

        response = requests.post(url, headers=HEADERS, timeout=20)

        if response.status_code != 200:
            return None, None, None, None

        data = response.json()
        posting_info = data.get("jobPostingInfo", {})

        description = _clean_description(posting_info.get("jobDescription"))
        posted_at_iso = posting_info.get("startDate")
        job_type = posting_info.get("timeType")
        job_req_id = posting_info.get("jobReqId")

        return description, posted_at_iso, job_type, job_req_id

    except Exception:
        return None, None, None, None


def _normalize_job(job, company, description, posted_at_iso, job_type, job_req_id, apply_url):
    """
    Map a raw Workday job dict -> the unified schema (see module
    docstring block above). Mirrors providers/greenhouse.py's _normalize_job.

    Workday doesn't consistently expose salary fields across tenants,
    so those come through as None rather than guessed values.
    """
    native_id = job_req_id or job.get("externalPath")

    return {
        "id": f"workday_{native_id}" if native_id else None,
        "title": job.get("title", ""),
        "company": company,
        "location": job.get("locationsText"),
        "description": description,
        "salary_min": None,
        "salary_max": None,
        "salary_currency": None,
        "job_type": job_type,
        "posted_at": _format_date_ddmmyyyy(posted_at_iso),
        "apply_url": apply_url,
        "source": SOURCE_NAME,
    }


def _fetch_company(company_entry, role=None, fetch_descriptions=True, max_results=200):
    """
    Paginates a single Workday company's postings.

    Returns (company, matches) where matches is a list of
    (raw_job, description, posted_at_iso, job_type, job_req_id, apply_url)
    tuples - kept un-normalized so fetch_jobs() can sort on the raw
    posted_at_iso value before formatting to ddmmyyyy, same pattern as
    greenhouse.py's raw_matches / _normalize_job split.
    """
    company = company_entry["company"]
    search_url, detail_base_url = _build_api_urls(company_entry["url"])

    matches = []
    offset = 0
    limit = 20
    total_fetched = 0

    while True:

        payload = {
            "limit": limit,
            "offset": offset,
            # Pass role to Workday's own search so it filters server-side
            # instead of pulling every open role at the company first.
            "searchText": role or "",
        }

        try:
            response = requests.post(search_url, headers=HEADERS, json=payload, timeout=30)

            if response.status_code != 200:
                # print(f"Skipped ({response.status_code})")
                break

            data = response.json()
            postings = data.get("jobPostings", [])
            total = data.get("total", 0)

            if not postings:
                break

            total_fetched += len(postings)
            # print(f"Fetched {len(postings)} jobs ({total_fetched} of {total} total)")

            for job in postings:

                title = job.get("title", "")

                if role and role.lower() not in title.lower():
                    continue

                external_path = job.get("externalPath", "")

                description = posted_at_iso = job_type = job_req_id = None

                if fetch_descriptions and external_path:
                    description, posted_at_iso, job_type, job_req_id = _fetch_job_detail(
                        detail_base_url, external_path
                    )

                apply_url = company_entry["url"].rstrip("/") + external_path

                matches.append((job, description, posted_at_iso, job_type, job_req_id, apply_url))

            offset += limit

            # Stop conditions: reported total reached, this was a partial/
            # last page, or the safety cap was hit (avoids runaway
            # pagination on very large companies like NVIDIA).
            if offset >= total:
                break

            if len(postings) < limit:
                break

            if total_fetched >= max_results:
                # print(f"Hit max_results cap ({max_results}) - stopping pagination")
                break

        except Exception as e:
            print(e)
            break

    return company, matches


def fetch_jobs(role=None, sort_by_date=True, fetch_descriptions=True, max_results=200):
    """
    Fetch jobs across all companies in workday_companies.json,
    optionally filtered by role (case-insensitive substring match on
    title).

    Returns:
        list[dict] - each dict matches the unified job schema (see top
        of this file).
    """

    companies = load_companies()

    raw_matches = []  # (job, company, description, posted_at_iso, job_type, job_req_id, apply_url)

    # print(f"\nCompanies to scan : {len(companies)}")

    for index, company_entry in enumerate(companies, start=1):

        # print(f"\n[{index}/{len(companies)}] {company_entry['company']}")

        company, matches = _fetch_company(company_entry, role, fetch_descriptions, max_results)

        # print(f"Matched : {len(matches)}")

        for job, description, posted_at_iso, job_type, job_req_id, apply_url in matches:
            raw_matches.append(
                (job, company, description, posted_at_iso, job_type, job_req_id, apply_url)
            )

    if sort_by_date:
        raw_matches.sort(
            key=lambda entry: _parse_iso_date(entry[3]),
            reverse=True,
        )

    all_jobs = [
        _normalize_job(job, company, description, posted_at_iso, job_type, job_req_id, apply_url)
        for job, company, description, posted_at_iso, job_type, job_req_id, apply_url in raw_matches
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