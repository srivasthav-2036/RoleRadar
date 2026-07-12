"""
fetch_context.py

Pulls together everything tailor_resume.py needs for one tailoring
request: the user's resume, the target job, and the recommendation
row that connects them.

IMPORTANT: tailoring is only allowed for jobs that were actually
recommended to this user. get_recommendation() is the gate - if no
recommendation row exists for (user_id, job_id), tailoring is
refused. This prevents tailoring against arbitrary jobs from the
jobs table that this user was never matched with.
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


def get_recommendation(user_id: str, job_id: str):
    """
    Fetch the full recommendation row for this user+job. Returns
    None if this job was never recommended to this user - callers
    MUST treat None as "tailoring not allowed", not just "no extra
    context available".

    recommendations has a UNIQUE KEY on (user_id, job_id), so there
    can only ever be one row.
    """
    query = text("""
        SELECT recommendation_id, score, match_details, tailored_resume
        FROM recommendations
        WHERE user_id = :user_id AND job_id = :job_id
    """)

    with engine.connect() as conn:
        row = conn.execute(
            query, {"user_id": user_id, "job_id": job_id}
        ).fetchone()

    if row is None:
        return None

    return {
        "recommendation_id": row.recommendation_id,
        "score": row.score,
        "match_details": _maybe_json_loads(row.match_details),
        "tailored_resume": _maybe_json_loads(row.tailored_resume),
    }


def build_tailoring_context(user_id: str, job_id: str):
    """
    Returns:
        {
            "resume": <resume JSON, extractor schema>,
            "job": <job dict from get_job>,
            "match_details": <dict or None>,
        }

    Raises ValueError if:
        - resume not found
        - this job was never recommended to this user (the gate)
        - job not found in jobs table (shouldn't happen if the
          recommendation row exists, but checked anyway)
    """
    resume_data = get_resume(user_id)
    if resume_data is None:
        raise ValueError(f"No resume found for user_id={user_id}")

    recommendation = get_recommendation(user_id, job_id)
    if recommendation is None:
        raise ValueError(
            f"Job {job_id} was not recommended to user {user_id} - "
            "tailoring is only available for recommended jobs."
        )

    job = get_job(job_id)
    if job is None:
        raise ValueError(f"No job found for job_id={job_id}")

    return {
        "resume": resume_data["resume"],
        "job": job,
        "match_details": recommendation["match_details"],
    }