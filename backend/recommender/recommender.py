"""
recommender.py

Generates recommendations for a user using a hybrid filter:

    1. Vector search returns candidates sorted by embedding distance
       (closest first) - free, already computed, no API cost.
    2. DISTANCE_THRESHOLD cuts the list before spending any LLM
       calls - only candidates that are at least roughly similar get
       sent for full matching. Since candidates arrive sorted
       ascending by distance, we stop the moment we cross the
       threshold.
    3. Surviving jobs are sent to the LLM in batches of MATCH_BATCH_SIZE
       (via match_resume_to_jobs_batch) - the resume is included once
       per batch, not once per job, cutting token usage by ~70%.
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

import logging

from backend.recommender.vector_search import search_similar_jobs
from backend.recommender.recommendation_storage import (
    get_recommended_job_ids,
    store_recommendations,
)
from backend.resume_extractor.resume_text_tidb_storage import get_resume
from backend.similarity_engine.engine import match_resume_to_jobs_batch
from backend.rate_limiting.usage_tracker import DailyBudgetExhaustedError

logger = logging.getLogger(__name__)

DISTANCE_THRESHOLD = 0.7   # cosine distance cutoff — tune against real data
SCORE_THRESHOLD    = 60    # match score (0-100) cutoff
MAX_RECOMMENDATIONS = 15   # safety cap, not a target count


def generate_recommendations(
    user_id: str,
    candidate_pool: int = 30,
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
    Distance-threshold cut (free — no API calls)
        ↓
    Batched Groq Matching (survivors only, MATCH_BATCH_SIZE jobs per call)
        ↓
    Score-threshold filter (quality bar, not a fixed count)
        ↓
    Sort by Score, cap at MAX_RECOMMENDATIONS
        ↓
    Store Recommendations
        ↓
    Return Recommendations (may be empty — that's expected and fine)
    """

    # ---------------------------------------------------
    # Fetch Resume
    # ---------------------------------------------------

    resume_data = get_resume(user_id)

    if resume_data is None:
        raise ValueError("Resume not found.")

    resume_json      = resume_data["resume"]
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

    # ---------------------------------------------------
    # Distance cut (free — no LLM involved)
    # ---------------------------------------------------
    # candidate_jobs is sorted ascending by distance, so we stop as
    # soon as we cross the threshold — everything after is farther away.

    survivors: list[dict] = []
    for job in candidate_jobs:
        distance = job.get("distance")
        if distance is None:
            continue
        if distance > DISTANCE_THRESHOLD:
            logger.debug(
                "[recommender] user=%s: distance %.4f > threshold %.4f — "
                "stopping distance cut at %d survivors.",
                user_id, distance, DISTANCE_THRESHOLD, len(survivors),
            )
            break
        survivors.append(job)

    if not survivors:
        logger.info(
            "[recommender] user=%s: no candidates passed the distance "
            "threshold — no recommendations generated.",
            user_id,
        )
        return []

    logger.info(
        "[recommender] user=%s: %d/%d candidate(s) passed the distance "
        "threshold — sending to batched LLM matching.",
        user_id, len(survivors), len(candidate_jobs),
    )

    # ---------------------------------------------------
    # Batched Groq Semantic Matching + Scoring
    # ---------------------------------------------------

    job_profiles = [job["parsed_job"] for job in survivors]

    match_results = match_resume_to_jobs_batch(
        resume_profile=resume_json,
        jobs=job_profiles,
    )

    # ---------------------------------------------------
    # Score filter + collect recommendations
    # ---------------------------------------------------

    recommendations = []
    skipped_failures = 0
    budget_exhausted = False

    for job, result in zip(survivors, match_results):
        if not result.get("success", True):
            error_msg = result.get("error", "unknown")

            if "daily_budget_exhausted" in error_msg:
                logger.error(
                    "[recommender] user=%s: daily Groq budget exhausted — "
                    "stopping. %d recommendation(s) collected so far.",
                    user_id, len(recommendations),
                )
                budget_exhausted = True
                break

            skipped_failures += 1
            logger.warning(
                "[recommender] user=%s: skipped job '%s' due to match error: %s",
                user_id,
                job.get("parsed_job", {}).get("title", "<unknown>"),
                error_msg,
            )
            continue

        score = result["score"]
        if score < SCORE_THRESHOLD:
            logger.debug(
                "[recommender] user=%s: job '%s' score %.1f < threshold %d — skipped.",
                user_id,
                job.get("parsed_job", {}).get("title", "<unknown>"),
                score, SCORE_THRESHOLD,
            )
            continue

        logger.info(
            "[recommender] user=%s: job '%s' accepted — score=%.1f (%s)",
            user_id,
            job.get("parsed_job", {}).get("title", "<unknown>"),
            score,
            result.get("overall_match", ""),
        )
        recommendations.append(
            {
                "job":   job,
                "match": result,
                "score": score,
            }
        )

    if skipped_failures:
        logger.warning(
            "[recommender] user=%s: %d job(s) skipped due to match errors.",
            user_id, skipped_failures,
        )

    # ---------------------------------------------------
    # Final Ranking
    # ---------------------------------------------------

    recommendations.sort(key=lambda x: x["score"], reverse=True)
    recommendations = recommendations[:MAX_RECOMMENDATIONS]

    # ---------------------------------------------------
    # Store Recommendations
    # ---------------------------------------------------

    if recommendations:
        store_recommendations(
            user_id=user_id,
            recommendations=recommendations,
        )

    logger.info(
        "[recommender] user=%s: pipeline complete — %d recommendation(s) stored%s.",
        user_id,
        len(recommendations),
        " (budget exhausted, run was partial)" if budget_exhausted else "",
    )

    return recommendations