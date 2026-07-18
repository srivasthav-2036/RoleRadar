from sqlalchemy import text
import json
from backend.database.config import engine


def get_recommended_job_ids(user_id: str) -> set[str]:
    """
    Returns all job_ids that have already been recommended
    to the user.
    """

    sql = text("""
        SELECT job_id
        FROM recommendations
        WHERE user_id = :user_id
    """)

    with engine.connect() as conn:
        rows = conn.execute(
            sql,
            {"user_id": user_id},
        ).fetchall()

    return {row[0] for row in rows}

# def get_stored_recommendations(user_id: str) -> list:
#     """
#     Returns this user's already-computed recommendations WITHOUT
#     triggering a new Gemini run.
#     """
#     query = text("""
#         SELECT
#             r.job_id,
#             r.score,
#             r.match_details,
#             r.tailored_resume IS NOT NULL AS has_tailored_resume,
#             j.title,
#             j.company,
#             j.job_text
#         FROM recommendations r
#         JOIN jobs j ON j.job_id = r.job_id
#         WHERE r.user_id = :user_id
#         ORDER BY r.score DESC
#     """)

#     with engine.connect() as conn:
#         rows = conn.execute(query, {"user_id": user_id}).fetchall()

#     results = []
#     for row in rows:
#         match_details = row.match_details
#         if isinstance(match_details, (str, bytes)):
#             match_details = json.loads(match_details)

#         job_text = row.job_text
#         if isinstance(job_text, (str, bytes)):
#             job_text = json.loads(job_text)
#         job_text = job_text or {}

#         results.append({
#             "job_id": row.job_id,
#             "title": row.title,
#             "company": row.company,
#             "apply_url": job_text.get("apply_url"),
#             "score": row.score,
#             "overall_match": (match_details or {}).get("overall_match"),
#             "recommendation": (match_details or {}).get("recommendation"),
#             "has_tailored_resume": bool(row.has_tailored_resume),
#         })

#     return results
"""
REPLACE your existing get_stored_recommendations() in
recommender/recommendation_storage.py with this version - it now
also returns location, salary, experience, employment_type, and a
trimmed matched/missing skills list for the job card, without
pulling in the full match breakdown (that's what
get_recommendation_detail below is for - keeps the list endpoint
lean, per the "don't duplicate everything on the card" requirement).
"""



def _safe_string(val) -> str | None:
    if val is None:
        return None
    if isinstance(val, dict):
        keys = [str(k) for k, v in val.items() if v not in (False, None, "")]
        if not keys:
            keys = [str(k) for k in val.keys()]
        return ", ".join(keys)
    if isinstance(val, list):
        return ", ".join(str(x) for x in val)
    return str(val)


def get_stored_recommendations(user_id: str) -> list:
    """
    Returns this user's already-computed recommendations for the job
    card list view - lean enough for a grid of cards, not the full
    AI match breakdown (see get_recommendation_detail for that).
    """
    query = text("""
        SELECT
            r.job_id,
            r.score,
            r.match_details,
            r.tailored_resume IS NOT NULL AS has_tailored_resume,
            j.title,
            j.company,
            j.job_text
        FROM recommendations r
        JOIN jobs j ON j.job_id = r.job_id
        WHERE r.user_id = :user_id
        ORDER BY r.score DESC
    """)

    with engine.connect() as conn:
        rows = conn.execute(query, {"user_id": user_id}).fetchall()

    results = []
    for row in rows:
        match_details = row.match_details
        if isinstance(match_details, (str, bytes)):
            match_details = json.loads(match_details)
        match_details = match_details or {}

        job_text = row.job_text
        if isinstance(job_text, (str, bytes)):
            job_text = json.loads(job_text)
        job_text = job_text or {}

        results.append({
            "job_id": row.job_id,
            "title": row.title,
            "company": row.company,
            "location": _safe_string(job_text.get("location")),
            "apply_url": job_text.get("apply_url"),
            "salary_min": job_text.get("salary_min"),
            "salary_max": job_text.get("salary_max"),
            "salary_currency": job_text.get("salary_currency"),
            "experience_required": _safe_string(job_text.get("experience_required")),
            "employment_type": _safe_string(job_text.get("employment_type")),
            "score": row.score,
            "overall_match": match_details.get("overall_match"),
            "matched_skills": (match_details.get("matched_skills") or [])[:5],
            "missing_skills": (match_details.get("missing_skills") or [])[:3],
            "has_tailored_resume": bool(row.has_tailored_resume),
        })

    return results


def get_recommendation_detail(user_id: str, job_id: str):
    """
    Full detail for the job drawer - job info (including description,
    for the left panel) + the COMPLETE match_details breakdown, read
    directly from the backend, not recomputed. Returns None if this
    job was never recommended to this user.
    """
    query = text("""
        SELECT
            r.job_id,
            r.score,
            r.match_details,
            r.tailored_resume IS NOT NULL AS has_tailored_resume,
            j.title,
            j.company,
            j.job_text
        FROM recommendations r
        JOIN jobs j ON j.job_id = r.job_id
        WHERE r.user_id = :user_id AND r.job_id = :job_id
    """)

    with engine.connect() as conn:
        row = conn.execute(query, {"user_id": user_id, "job_id": job_id}).fetchone()

    if row is None:
        return None

    match_details = row.match_details
    if isinstance(match_details, (str, bytes)):
        match_details = json.loads(match_details)
    match_details = match_details or {}

    job_text = row.job_text
    if isinstance(job_text, (str, bytes)):
        job_text = json.loads(job_text)
    job_text = job_text or {}

    return {
        "job_id": row.job_id,
        "title": row.title,
        "company": row.company,
        "description": job_text.get("description"),
        "location": _safe_string(job_text.get("location")),
        "apply_url": job_text.get("apply_url"),
        "salary_min": job_text.get("salary_min"),
        "salary_max": job_text.get("salary_max"),
        "salary_currency": job_text.get("salary_currency"),
        "experience_required": _safe_string(job_text.get("experience_required")),
        "education_required": _safe_string(job_text.get("education_required")),
        "employment_type": _safe_string(job_text.get("employment_type")),
        "score": row.score,
        "has_tailored_resume": bool(row.has_tailored_resume),
        # Full breakdown, read directly - none of this is recomputed
        "overall_match": match_details.get("overall_match"),
        "skill_score": match_details.get("skill_score"),
        "project_score": match_details.get("project_score"),
        "experience_score": match_details.get("experience_score"),
        "education_score": match_details.get("education_score"),
        "certificate_bonus": match_details.get("certificate_bonus"),
        "experience_match": match_details.get("experience_match"),
        "education_match": match_details.get("education_match"),
        "project_match": match_details.get("project_match"),
        "certificate_match": match_details.get("certificate_match"),
        "matched_required_skills": match_details.get("matched_required_skills", []),
        "matched_preferred_skills": match_details.get("matched_preferred_skills", []),
        "matched_skills": match_details.get("matched_skills", []),
        "missing_skills": match_details.get("missing_skills", []),
        "recommendation": match_details.get("recommendation"),
    }


def get_new_matches_today(user_id: str) -> int:
    """Powers the 'New AI matches today' stat card."""
    query = text("""
        SELECT COUNT(*) FROM recommendations
        WHERE user_id = :user_id AND DATE(recommended_at) = CURDATE()
    """)
    with engine.connect() as conn:
        count = conn.execute(query, {"user_id": user_id}).scalar()
    return count or 0


def get_average_match_score(user_id: str):
    """
    Powers the 'Average match score' stat card. Returns None (not 0)
    if the user has no recommendations yet - frontend should show
    "-" for None, not a misleading 0.
    """
    query = text("SELECT AVG(score) FROM recommendations WHERE user_id = :user_id")
    with engine.connect() as conn:
        avg = conn.execute(query, {"user_id": user_id}).scalar()
    return round(avg, 1) if avg is not None else None


def get_skill_frequency(user_id: str) -> list:
    """
    Powers the Skill Galaxy. Aggregates matched_skills across all of
    this user's recommendations - "frequency" = how many of their
    recommended jobs actually matched on that skill.
    """
    query = text("""
        SELECT match_details FROM recommendations WHERE user_id = :user_id
    """)
    with engine.connect() as conn:
        rows = conn.execute(query, {"user_id": user_id}).fetchall()

    counts = {}
    for row in rows:
        match_details = row.match_details
        if isinstance(match_details, (str, bytes)):
            match_details = json.loads(match_details)
        match_details = match_details or {}

        for skill in match_details.get("matched_skills", []):
            counts[skill] = counts.get(skill, 0) + 1

    return [
        {"skill": skill, "count": count}
        for skill, count in sorted(counts.items(), key=lambda x: x[1], reverse=True)
    ]

def store_recommendations(
    user_id: str,
    recommendations: list[dict],
):
    """
    Stores newly generated recommendations. score is a real column
    since it's used for sorting/filtering; everything else Gemini +
    scoring.py produced (recommendation text, missing skills, per-
    category verdicts, score breakdown) goes into match_details JSON
    so it's not silently discarded.
    """

    sql = text("""
        INSERT INTO recommendations (
            user_id,
            job_id,
            score,
            match_details
        )
        VALUES (
            :user_id,
            :job_id,
            :score,
            :match_details
        )
    """)

    with engine.begin() as conn:

        for rec in recommendations:

            match = rec["match"]

            match_details = {
                "overall_match": match.get("overall_match"),
                "recommendation": match.get("recommendation"),
                "matched_required_skills": match.get("matched_required_skills", []),
                "matched_preferred_skills": match.get("matched_preferred_skills", []),
                "matched_skills": match.get("matched_skills", []),
                "missing_skills": match.get("missing_skills", []),
                "project_match": match.get("project_match"),
                "experience_match": match.get("experience_match"),
                "education_match": match.get("education_match"),
                "certificate_match": match.get("certificate_match"),
                "skill_score": match.get("skill_score"),
                "project_score": match.get("project_score"),
                "experience_score": match.get("experience_score"),
                "education_score": match.get("education_score"),
                "certificate_bonus": match.get("certificate_bonus"),
            }

            conn.execute(
                sql,
                {
                    "user_id": user_id,
                    "job_id": rec["job"]["job_id"],
                    "score": rec["score"],
                    "match_details": json.dumps(match_details),
                },
            )



def save_tailored_resume(user_id: str, job_id: str, tailored_resume: dict):
    """
    Caches a generated tailored resume onto its recommendation row,
    so get_or_generate_tailored_resume() never has to call Gemini
    again for this user+job combination.
    """
    query = text("""
        UPDATE recommendations
        SET tailored_resume = :tailored_resume
        WHERE user_id = :user_id AND job_id = :job_id
    """)
 
    with engine.begin() as conn:
        conn.execute(
            query,
            {
                "user_id": user_id,
                "job_id": job_id,
                "tailored_resume": json.dumps(tailored_resume),
            },
        )
 