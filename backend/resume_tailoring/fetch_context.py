"""
fetch_context.py

Pulls together everything tailor_resume.py needs for one tailoring
request: the user's resume, the target job, and (if this job was
previously recommended to the user) the match_details Gemini already
computed - missing_skills, matched_skills, recommendation blurb - so
tailoring has strong signal on what to emphasize without re-deriving
it from scratch.
"""

import json

from sqlalchemy import text

from backend.database.config import engine
from backend.resume_extractor.resume_text_tidb_storage import get_resume


def _maybe_json_loads(value):
    if isinstance(value, (str, bytes)):
        return json.loads(value)
    return value


def get_job(job_id: str):
    """
    Fetch a single job's title, company, and job_text (unpacked)
    by job_id. Returns None if not found.

    NOTE: job_id is not unique on the jobs table (no PK on it - dupes
    across providers are expected), so if duplicates exist this
    returns whichever row TiDB returns first. Fine for tailoring
    purposes since duplicates are the same posting from different
    providers.
    """
    query = text("""
        SELECT job_id, title, company, job_text
        FROM jobs
        WHERE job_id = :job_id
        LIMIT 1
    """)

    with engine.connect() as conn:
        row = conn.execute(query, {"job_id": job_id}).fetchone()

    if row is None:
        return None

    job_text = _maybe_json_loads(row.job_text) or {}

    return {
        "job_id": row.job_id,
        "title": row.title,
        "company": row.company,
        "location": job_text.get("location"),
        "description": job_text.get("description"),
        "apply_url": job_text.get("apply_url"),
        "required_skills": job_text.get("required_skills", []),
        "preferred_skills": job_text.get("preferred_skills", []),
        "experience_required": job_text.get("experience_required"),
        "education_required": job_text.get("education_required"),
        "responsibilities": job_text.get("responsibilities", []),
        "job_level": job_text.get("job_level"),
        "employment_type": job_text.get("employment_type"),
        "tools": job_text.get("tools", []),
        "technologies": job_text.get("technologies", []),
        "keywords": job_text.get("keywords", []),
        "soft_skills": job_text.get("soft_skills", []),
        "domains": job_text.get("domains", []),
    }


def get_match_details(user_id: str, job_id: str):
    """
    Fetch match_details for this user+job if it was previously
    recommended. Returns None if no recommendation exists - tailoring
    still works without it, just with less signal.

    NOTE: recommendations has a UNIQUE KEY on (user_id, job_id), so
    there can only ever be one row per user+job - no ORDER BY/LIMIT
    needed to disambiguate.
    """
    query = text("""
        SELECT match_details
        FROM recommendations
        WHERE user_id = :user_id AND job_id = :job_id
    """)

    with engine.connect() as conn:
        row = conn.execute(
            query, {"user_id": user_id, "job_id": job_id}
        ).fetchone()

    if row is None or row.match_details is None:
        return None

    return _maybe_json_loads(row.match_details)


def build_tailoring_context(user_id: str, job_id: str):
    """
    Returns:
        {
            "resume": <resume JSON, extractor schema>,
            "job": <job dict from get_job>,
            "match_details": <dict or None>,
        }
    Raises ValueError if resume or job cannot be found - tailoring
    cannot proceed without both.
    """
    resume_data = get_resume(user_id)
    if resume_data is None:
        raise ValueError(f"No resume found for user_id={user_id}")

    job = get_job(job_id)
    if job is None:
        raise ValueError(f"No job found for job_id={job_id}")

    match_details = get_match_details(user_id, job_id)

    return {
        "resume": resume_data["resume"],
        "job": job,
        "match_details": match_details,
    }