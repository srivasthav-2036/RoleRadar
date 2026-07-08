"""
Diagnostic: hits a single Workable company with a few endpoint
variants and prints the FULL raw response (status + body), so we can
see the actual reason for the 404 instead of guessing.

Usage:
    python debug_workable.py canonical
"""

import sys
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}


def try_endpoint(label, url):
    print(f"\n--- {label} ---")
    print(f"URL: {url}")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        print(f"Status: {resp.status_code}")
        print(f"Body (first 500 chars):")
        print(resp.text[:500])
    except Exception as e:
        print(f"Request failed: {e}")


if __name__ == "__main__":
    company = sys.argv[1] if len(sys.argv) > 1 else "canonical"

    print(f"Testing company slug: {company}")

    try_endpoint(
        "v3 jobs endpoint (current code)",
        f"https://apply.workable.com/api/v3/accounts/{company}/jobs",
    )

    print(f"\n--- v1 widget endpoint (alternate) ---")
    widget_url = f"https://apply.workable.com/api/v1/widget/accounts/{company}"
    print(f"URL: {widget_url}")

    try:
        resp = requests.get(widget_url, headers=HEADERS, timeout=20)
        print(f"Status: {resp.status_code}")

        data = resp.json()
        jobs = data.get("jobs", [])
        print(f"Job count: {len(jobs)}")

        if jobs:
            print("\nFull JSON of first job (so we can see real field names):")
            import json
            print(json.dumps(jobs[0], indent=2))

            shortcode = jobs[0].get("shortcode")
            if shortcode:
                detail_url = f"https://apply.workable.com/api/v1/widget/accounts/{company}/jobs/{shortcode}"
                print(f"\n--- Attempting per-job detail endpoint (for full JD) ---")
                print(f"URL: {detail_url}")
                detail_resp = requests.get(detail_url, headers=HEADERS, timeout=20)
                print(f"Status: {detail_resp.status_code}")
                print("Body (first 1000 chars):")
                print(detail_resp.text[:1000])
        else:
            print("No jobs found for this company - try a different company slug "
                  "that has active openings (e.g. toggl, typeform, hotjar).")

    except Exception as e:
        print(f"Request failed: {e}")

    try_endpoint(
        "public careers page (not API - just to confirm the slug itself is right)",
        f"https://apply.workable.com/{company}/",
    )