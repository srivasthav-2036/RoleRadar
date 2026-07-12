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

def get_stored_recommendations(user_id: str) -> list:
    """
    Returns this user's already-computed recommendations WITHOUT
    triggering a new Gemini run.
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

        job_text = row.job_text
        if isinstance(job_text, (str, bytes)):
            job_text = json.loads(job_text)
        job_text = job_text or {}

        results.append({
            "job_id": row.job_id,
            "title": row.title,
            "company": row.company,
            "apply_url": job_text.get("apply_url"),
            "score": row.score,
            "overall_match": (match_details or {}).get("overall_match"),
            "recommendation": (match_details or {}).get("recommendation"),
            "has_tailored_resume": bool(row.has_tailored_resume),
        })

    return results

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
 