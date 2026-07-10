from backend.recommender.vector_search import search_similar_jobs
from backend.recommender.recommendation_storage import (
    get_recommended_job_ids,
    store_recommendations,
)

from backend.resume_extractor.resume_text_tidb_storage import get_resume
from backend.similarity_engine.engine import match_resume_to_job


def generate_recommendations(
    user_id: str,
    top_k: int = 10,
    candidate_pool: int = 300,
):
    """
    Recommendation Pipeline

    Resume
        ↓
    Resume Embedding
        ↓
    Fetch Previously Recommended Jobs
        ↓
    Vector Search (excluding previous recommendations)
        ↓
    Gemini Matching
        ↓
    Sort by Score
        ↓
    Store Recommendations
        ↓
    Return Top Recommendations
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
    # Fetch Already Recommended Job IDs
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
    # Gemini Semantic Matching
    # ---------------------------------------------------

    for job in candidate_jobs:

        result = match_resume_to_job(
            resume_profile=resume_json,
            job_profile=job["parsed_job"],
        )

        if not result.get("success", True):
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

    recommendations = recommendations[:top_k]

    # ---------------------------------------------------
    # Store Recommendations
    # ---------------------------------------------------

    if recommendations:
        store_recommendations(
            user_id=user_id,
            recommendations=recommendations,
        )

    return recommendations