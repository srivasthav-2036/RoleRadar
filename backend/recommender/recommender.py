"""
recommender.py

Generates recommendations for a user using a hybrid filter instead
of a fixed "top 10":

    1. Vector search returns candidates sorted by embedding distance
       (closest first) - free, already computed, no API cost.
    2. DISTANCE_THRESHOLD cuts the list before spending any Gemini
       calls - only candidates that are at least roughly similar get
       sent for full matching. Since candidates arrive sorted
       ascending by distance, we can `break` the moment we cross the
       threshold instead of checking every remaining item.
    3. Each survivor gets a real Gemini match + score
       (calculate_score, 0-100).
    4. SCORE_THRESHOLD keeps only genuinely strong matches - not a
       fixed count, so a great week produces more recommendations
       and a quiet week produces fewer or none, rather than always
       forcing exactly 10.
    5. MAX_RECOMMENDATIONS is just a safety cap so one run can't
       flood a user with an unreasonable number of emails/entries.

TUNING NOTE: DISTANCE_THRESHOLD and SCORE_THRESHOLD below are
starting points, not scientifically derived. Log actual distance/
score values for real users and adjust based on where "genuinely
relevant" seems to separate from "not relevant" in your data.
"""

from backend.recommender.vector_search import search_similar_jobs
from backend.recommender.recommendation_storage import (
    get_recommended_job_ids,
    store_recommendations,
)

from backend.resume_extractor.resume_text_tidb_storage import get_resume
from backend.similarity_engine.engine import match_resume_to_job


DISTANCE_THRESHOLD = 0.7   # cosine distance cutoff - tune against real data
SCORE_THRESHOLD = 60       # Gemini match score (0-100) cutoff - "Good Match" is 75+
MAX_RECOMMENDATIONS = 15   # safety cap, not a target count


def generate_recommendations(
    user_id: str,
    candidate_pool: int = 300,
):
    """
    Recommendation Pipeline

    Resume
        ↓
    Resume Embedding
        ↓
    Fetch Previously Recommended Jobs (this user only)
        ↓
    Vector Search (excluding previous recommendations, sorted by distance)
        ↓
    Cheap distance-threshold cut (before any Gemini calls)
        ↓
    Gemini Matching (only on survivors)
        ↓
    Score-threshold filter (quality bar, not a fixed count)
        ↓
    Sort by Score, cap at MAX_RECOMMENDATIONS
        ↓
    Store Recommendations
        ↓
    Return Recommendations (may be empty - that's expected and fine)
    """

    # ---------------------------------------------------
    # Fetch Resume
    # ---------------------------------------------------

    resume_data = get_resume(user_id)

    if resume_data is None:
        raise ValueError("Resume not found.")

    resume_json = resume_data["resume"]
    resume_embedding = resume_data["embedding"]

    # ---------------------------------------------------
    # Fetch Already Recommended Job IDs (scoped to this user)
    # ---------------------------------------------------

    recommended_job_ids = get_recommended_job_ids(user_id)

    # ---------------------------------------------------
    # Vector Search
    # ---------------------------------------------------

    candidate_jobs = search_similar_jobs(
        resume_embedding=resume_embedding,
        top_k=candidate_pool,
        exclude_job_ids=list(recommended_job_ids),
    )

    recommendations = []

    # ---------------------------------------------------
    # Distance cut + Gemini Semantic Matching
    # ---------------------------------------------------

    for job in candidate_jobs:

        # candidate_jobs is sorted by distance ascending, so once we
        # cross the threshold, everything after is even less similar
        # if job["distance"] > DISTANCE_THRESHOLD:
        #     break
        distance = job.get("distance")

        if distance is None:
            continue

        if distance > DISTANCE_THRESHOLD:
            break

        result = match_resume_to_job(
            resume_profile=resume_json,
            job_profile=job["parsed_job"],
        )

        if not result.get("success", True):
            continue

        if result["score"] < SCORE_THRESHOLD:
            continue

        recommendations.append(
            {
                "job": job,
                "match": result,
                "score": result["score"],
            }
        )

    # ---------------------------------------------------
    # Final Ranking
    # ---------------------------------------------------

    recommendations.sort(
        key=lambda x: x["score"],
        reverse=True,
    )

    recommendations = recommendations[:MAX_RECOMMENDATIONS]

    # ---------------------------------------------------
    # Store Recommendations
    # ---------------------------------------------------

    if recommendations:
        store_recommendations(
            user_id=user_id,
            recommendations=recommendations,
        )

    return recommendations