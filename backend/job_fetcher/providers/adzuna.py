# """
# Adzuna Job Provider

# Fetch jobs from Adzuna API.

# Test:
# python providers/adzuna.py
# """

# import html
# import re
# from datetime import datetime

# import requests

# from job_fetcher.config import (
#     ADZUNA_APP_ID,
#     ADZUNA_API_KEY,
#     COMMON_HEADERS,
#     REQUEST_TIMEOUT,
# )


# BASE_URL = "https://api.adzuna.com/v1/api/jobs"

# _TAG_RE = re.compile(r"<[^>]+>")


# def _clean_description(raw_text):
#     """
#     Strip HTML tags/entities from whatever Adzuna returns.

#     This does NOT add, remove, or guess at content - it only removes
#     markup so you get the exact text Adzuna provided, cleanly.
#     If Adzuna truncated the text with "...", that truncation is
#     preserved as-is (there's no API param to request more).
#     """
#     if not raw_text:
#         return raw_text

#     text = _TAG_RE.sub(" ", raw_text)   # strip tags
#     text = html.unescape(text)          # decode &amp; &nbsp; etc.
#     text = re.sub(r"\s+", " ", text).strip()  # collapse whitespace

#     return text


# def _looks_truncated(text):
#     if not text:
#         return False
#     stripped = text.rstrip()
#     return stripped.endswith("...") or stripped.endswith("…")


# def _fetch_full_description_from_page(url, verbose=True):
#     """
#     Best-effort fallback: when Adzuna's own description is truncated,
#     fetch the actual job page (apply_url) and pull its visible text.

#     This does NOT invent content - it only extracts what the source
#     page actually renders in plain HTML. Returns None if the page
#     can't be fetched or looks JS-rendered / empty (nothing to extract).
#     """
#     try:
#         from bs4 import BeautifulSoup
#     except ImportError:
#         if verbose:
#             print("  [fallback] beautifulsoup4 not installed - skipping. "
#                   "Run: pip install beautifulsoup4")
#         return None

#     try:
#         response = requests.get(
#             url,
#             headers={"User-Agent": "Mozilla/5.0"},
#             timeout=15,
#         )
#         response.raise_for_status()
#     except Exception as e:
#         if verbose:
#             print(f"  [fallback] Could not fetch {url} -> {e}")
#         return None

#     try:
#         soup = BeautifulSoup(response.text, "html.parser")

#         for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside", "form"]):
#             tag.decompose()

#         # JD text is almost always written in <p> tags. Nav links, sidebar
#         # lists ("Similar jobs"), and footers ("Country selection", cookie
#         # notices, etc.) are typically <li>/<a>/<div> menu items, not <p>.
#         # Extracting only <p> text avoids pulling in that page chrome.
#         paragraphs = [
#             p.get_text(separator=" ", strip=True)
#             for p in soup.find_all("p")
#         ]
#         paragraphs = [p for p in paragraphs if len(p) > 40]

#         text = "\n\n".join(paragraphs)
#         text = re.sub(r"[ \t]+", " ", text).strip()

#         # Fallback: if the page isn't <p>-structured, use whole-page text
#         # as a last resort rather than returning nothing.
#         if len(text) < 200:
#             fallback_text = soup.get_text(separator="\n")
#             fallback_text = re.sub(r"[ \t]+", " ", fallback_text)
#             fallback_text = re.sub(r"\n\s*\n+", "\n\n", fallback_text).strip()
#             text = fallback_text

#         # If the page barely has any text, it's likely JS-rendered -
#         # not worth returning as it won't actually contain the JD.
#         if len(text) < 200:
#             if verbose:
#                 print(f"  [fallback] Page returned only {len(text)} chars of text "
#                       f"(likely JS-rendered) - keeping Adzuna's truncated version. {url}")
#             return None

#         if verbose:
#             print(f"  [fallback] Got {len(text)} chars from page - using this instead.")

#         return text
#     except Exception as e:
#         if verbose:
#             print(f"  [fallback] Parsing failed -> {e}")
#         return None


# def _format_date_ddmmyyyy(iso_date_str):
#     """
#     Convert Adzuna's 'created' field (e.g. '2024-01-15T10:30:00Z')
#     to ddmmyyyy format (e.g. '15012024').
#     """
#     if not iso_date_str:
#         return None

#     try:
#         dt = datetime.fromisoformat(iso_date_str.replace("Z", "+00:00"))
#         return dt.strftime("%d%m%Y")
#     except ValueError:
#         return iso_date_str  # fall back to raw value rather than guessing


# def fetch_jobs(
#     query: str,
#     location: str = "India",
#     page: int = 1,
#     results_per_page: int = 20,
#     sort_by: str = "date",
#     try_full_description: bool = True,
# ):
#     """
#     Fetch jobs from Adzuna, sorted by posted date (newest first by default).

#     sort_by options (per Adzuna API): "date", "relevance", "salary", "hybrid"

#     try_full_description: when True, if Adzuna's own description looks
#         truncated ("..."), makes one extra request per truncated job
#         to scrape the actual job page (apply_url) for fuller text.
#         This is best-effort - some source sites are JS-rendered and
#         won't return usable text via a plain GET request.

#     Returns:
#         list[dict]
#     """

#     country = "in"  # India

#     url = (
#         f"{BASE_URL}/{country}/search/{page}"
#         f"?app_id={ADZUNA_APP_ID}"
#         f"&app_key={ADZUNA_API_KEY}"
#     )

#     params = {
#         "what": query,
#         "where": location,
#         "results_per_page": results_per_page,
#         "content-type": "application/json",
#         "sort_by": sort_by,
#     }

#     print("=" * 60)
#     print("Adzuna")
#     print(f"Searching : {query}")
#     print(f"Location  : {location}")
#     print(f"Sorted by : {sort_by}")
#     print("=" * 60)

#     try:

#         response = requests.get(
#             url,
#             params=params,
#             headers=COMMON_HEADERS,
#             timeout=REQUEST_TIMEOUT,
#         )

#         response.raise_for_status()

#         data = response.json()

#         results = data.get("results", [])

#         print(f"Found {len(results)} jobs\n")

#         jobs = []

#         for job in results:

#             description = _clean_description(job.get("description"))
#             apply_url = job.get("redirect_url")

#             if try_full_description and _looks_truncated(description) and apply_url:
#                 fuller_text = _fetch_full_description_from_page(apply_url)
#                 if fuller_text:
#                     description = fuller_text

#             jobs.append(
#                 {
#                     "id": job.get("id"),
#                     "title": job.get("title"),
#                     "company": job.get("company", {}).get("display_name"),
#                     "location": job.get("location", {}).get("display_name"),
#                     "description": description,
#                     "salary_min": job.get("salary_min"),
#                     "salary_max": job.get("salary_max"),
#                     "salary_currency": job.get("salary_currency"),
#                     "posted_at": _format_date_ddmmyyyy(job.get("created")),
#                     "apply_url": apply_url,
#                     "category": job.get("category", {}).get("label"),
#                     "contract_time": job.get("contract_time"),
#                     "contract_type": job.get("contract_type"),
#                     "latitude": job.get("latitude"),
#                     "longitude": job.get("longitude"),
#                     "source": "Adzuna",
#                 }
#             )

#         return jobs

#     except requests.exceptions.HTTPError as e:

#         print(f"HTTP Error : {e}")

#     except requests.exceptions.ConnectionError:

#         print("Connection Error")

#     except requests.exceptions.Timeout:

#         print("Request Timed Out")

#     except Exception as e:

#         print("Unexpected Error:", e)

#     return []


# if __name__ == "__main__":

#     jobs = fetch_jobs(
#         query="Software Engineer",
#         location="India",
#         sort_by="date",
#     )

#     print("\nReturned Jobs:", len(jobs))
#     print()

#     for i, job in enumerate(jobs, start=1):

#         print(f"{i}. {job['title']}")
#         print(f"Company : {job['company']}")
#         print(f"Location: {job['location']}")
#         print(f"Posted  : {job['posted_at']}")
#         print(f"Apply   : {job['apply_url']}")
#         print("JD:")
#         print(job['description'])
#         print("-" * 70)


# new norm code
"""
Adzuna Job Provider

Fetch jobs from Adzuna API.

Test:
python providers/adzuna.py
"""

import html
import re
from datetime import datetime

import requests

from job_fetcher.config import (
    ADZUNA_APP_ID,
    ADZUNA_API_KEY,
    COMMON_HEADERS,
    REQUEST_TIMEOUT,
)


BASE_URL = "https://api.adzuna.com/v1/api/jobs"

SOURCE_NAME = "Adzuna"

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


def _clean_description(raw_text):
    """
    Strip HTML tags/entities from whatever Adzuna returns.

    This does NOT add, remove, or guess at content - it only removes
    markup so you get the exact text Adzuna provided, cleanly.
    If Adzuna truncated the text with "...", that truncation is
    preserved as-is (there's no API param to request more).
    """
    if not raw_text:
        return raw_text

    text = _TAG_RE.sub(" ", raw_text)   # strip tags
    text = html.unescape(text)          # decode &amp; &nbsp; etc.
    text = re.sub(r"\s+", " ", text).strip()  # collapse whitespace

    return text


def _looks_truncated(text):
    if not text:
        return False
    stripped = text.rstrip()
    return stripped.endswith("...") or stripped.endswith("…")


def _fetch_full_description_from_page(url, verbose=True):
    """
    Best-effort fallback: when Adzuna's own description is truncated,
    fetch the actual job page (apply_url) and pull its visible text.

    This does NOT invent content - it only extracts what the source
    page actually renders in plain HTML. Returns None if the page
    can't be fetched or looks JS-rendered / empty (nothing to extract).
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        if verbose:
            print("  [fallback] beautifulsoup4 not installed - skipping. "
                  "Run: pip install beautifulsoup4")
        return None

    try:
        response = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15,
        )
        response.raise_for_status()
    except Exception as e:
        if verbose:
            print(f"  [fallback] Could not fetch {url} -> {e}")
        return None

    try:
        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside", "form"]):
            tag.decompose()

        # JD text is almost always written in <p> tags. Nav links, sidebar
        # lists ("Similar jobs"), and footers ("Country selection", cookie
        # notices, etc.) are typically <li>/<a>/<div> menu items, not <p>.
        # Extracting only <p> text avoids pulling in that page chrome.
        paragraphs = [
            p.get_text(separator=" ", strip=True)
            for p in soup.find_all("p")
        ]
        paragraphs = [p for p in paragraphs if len(p) > 40]

        text = "\n\n".join(paragraphs)
        text = re.sub(r"[ \t]+", " ", text).strip()

        # Fallback: if the page isn't <p>-structured, use whole-page text
        # as a last resort rather than returning nothing.
        if len(text) < 200:
            fallback_text = soup.get_text(separator="\n")
            fallback_text = re.sub(r"[ \t]+", " ", fallback_text)
            fallback_text = re.sub(r"\n\s*\n+", "\n\n", fallback_text).strip()
            text = fallback_text

        # If the page barely has any text, it's likely JS-rendered -
        # not worth returning as it won't actually contain the JD.
        if len(text) < 200:
            if verbose:
                print(f"  [fallback] Page returned only {len(text)} chars of text "
                      f"(likely JS-rendered) - keeping Adzuna's truncated version. {url}")
            return None

        if verbose:
            print(f"  [fallback] Got {len(text)} chars from page - using this instead.")

        return text
    except Exception as e:
        if verbose:
            print(f"  [fallback] Parsing failed -> {e}")
        return None


def _format_date_ddmmyyyy(iso_date_str):
    """
    Convert Adzuna's 'created' field (e.g. '2024-01-15T10:30:00Z')
    to ddmmyyyy format (e.g. '15012024').
    """
    if not iso_date_str:
        return None

    try:
        dt = datetime.fromisoformat(iso_date_str.replace("Z", "+00:00"))
        return dt.strftime("%d%m%Y")
    except ValueError:
        return iso_date_str  # fall back to raw value rather than guessing


def _build_job_type(contract_time, contract_type):
    """
    Merge Adzuna's two separate fields (contract_time: full_time/part_time,
    contract_type: permanent/contract) into a single free-text job_type
    field, since not every provider will split these the same way.
    """
    parts = [p for p in (contract_time, contract_type) if p]
    return " ".join(parts) if parts else None


def _normalize_job(job, description):
    """
    Map a raw Adzuna job dict -> the unified schema (see module docstring
    block above). This is the function to mirror when adding other
    providers.
    """
    native_id = job.get("id")

    return {
        "id": f"adzuna_{native_id}" if native_id else None,
        "title": job.get("title"),
        "company": job.get("company", {}).get("display_name"),
        "location": job.get("location", {}).get("display_name"),
        "description": description,
        "salary_min": job.get("salary_min"),
        "salary_max": job.get("salary_max"),
        "salary_currency": job.get("salary_currency"),
        "job_type": _build_job_type(job.get("contract_time"), job.get("contract_type")),
        "posted_at": _format_date_ddmmyyyy(job.get("created")),
        "apply_url": job.get("redirect_url"),
        "source": SOURCE_NAME,
    }


def fetch_jobs(
    query: str,
    location: str = "India",
    page: int = 1,
    results_per_page: int = 20,
    sort_by: str = "date",
    try_full_description: bool = True,
):
    """
    Fetch jobs from Adzuna, sorted by posted date (newest first by default).

    sort_by options (per Adzuna API): "date", "relevance", "salary", "hybrid"

    try_full_description: when True, if Adzuna's own description looks
        truncated ("..."), makes one extra request per truncated job
        to scrape the actual job page (apply_url) for fuller text.
        This is best-effort - some source sites are JS-rendered and
        won't return usable text via a plain GET request.

    Returns:
        list[dict] - each dict matches the unified job schema (see top
        of this file).
    """

    country = "in"  # India

    url = (
        f"{BASE_URL}/{country}/search/{page}"
        f"?app_id={ADZUNA_APP_ID}"
        f"&app_key={ADZUNA_API_KEY}"
    )

    params = {
        "what": query,
        "where": location,
        "results_per_page": results_per_page,
        "content-type": "application/json",
        "sort_by": sort_by,
    }

    print("=" * 60)
    print("Adzuna")
    print(f"Searching : {query}")
    print(f"Location  : {location}")
    print(f"Sorted by : {sort_by}")
    print("=" * 60)

    try:

        response = requests.get(
            url,
            params=params,
            headers=COMMON_HEADERS,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        data = response.json()

        results = data.get("results", [])

        print(f"Found {len(results)} jobs\n")

        jobs = []

        for job in results:

            description = _clean_description(job.get("description"))
            apply_url = job.get("redirect_url")

            if try_full_description and _looks_truncated(description) and apply_url:
                fuller_text = _fetch_full_description_from_page(apply_url)
                if fuller_text:
                    description = fuller_text

            jobs.append(_normalize_job(job, description))

        return jobs

    except requests.exceptions.HTTPError as e:

        print(f"HTTP Error : {e}")

    except requests.exceptions.ConnectionError:

        print("Connection Error")

    except requests.exceptions.Timeout:

        print("Request Timed Out")

    except Exception as e:

        print("Unexpected Error:", e)

    return []


if __name__ == "__main__":

    jobs = fetch_jobs(
        query="Software Engineer",
        location="India",
        sort_by="date",
    )

    print("\nReturned Jobs:", len(jobs))
    print()

    for i, job in enumerate(jobs, start=1):
        
        print(f"{i}. {job['title']}")
        print(f"Company : {job['company']}")
        print(f"Location: {job['location']}")
        print(f"Job type: {job['job_type']}")
        print(f"Posted  : {job['posted_at']}")
        print(f"Apply   : {job['apply_url']}")
        print("JD:")
        print(job['description'])
        print("-" * 70)