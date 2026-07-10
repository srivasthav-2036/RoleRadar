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