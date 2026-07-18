"""
engine.py

Orchestrates resume-to-job matching:
    1. semantic_match_batch() / semantic_match() — Groq LLM call (batched,
       rate-limited, retried)
    2. calculate_score()                         — deterministic, no API call

match_resume_to_jobs_batch() is the primary entry point for the
recommender: it takes a resume and a list of jobs, runs them through
the LLM in one (or more, if list > MATCH_BATCH_SIZE) calls, applies
scoring to each, and returns a list of results.

match_resume_to_job() is kept for backward compatibility.
"""

import logging

from backend.similarity_engine.scoring import calculate_score
from backend.similarity_engine.matcher import (
    semantic_match,
    semantic_match_batch,
    MATCH_BATCH_SIZE,
)
from backend.rate_limiting.usage_tracker import DailyBudgetExhaustedError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Batch entry point (used by recommender.py)
# ---------------------------------------------------------------------------

def match_resume_to_jobs_batch(
    resume_profile: dict,
    jobs: list[dict],
    batch_size: int = MATCH_BATCH_SIZE,
) -> list[dict]:
    """
    Match a resume against a list of job profiles using batched LLM calls.

    Jobs are sent to the LLM in chunks of `batch_size`.  The resume is
    included once per batch, not once per job.  Each batch is retried
    independently on transient errors so a single failed batch doesn't
    abort the whole run.

    Parameters
    ----------
    resume_profile : dict
        Parsed resume JSON.
    jobs : list[dict]
        Each element must be a parsed job profile dict (the "parsed_job"
        sub-dict from the candidate_jobs list in recommender.py).
    batch_size : int
        Jobs per LLM call.  Defaults to MATCH_BATCH_SIZE from matcher.py.

    Returns
    -------
    list[dict]
        One result dict per job, in the same order as `jobs`.
        Failed/missing entries have {"success": False, "error": "..."}.
    """
    if not jobs:
        return []

    all_results: list[dict] = []
    total = len(jobs)
    num_batches = (total + batch_size - 1) // batch_size

    logger.info(
        "[engine] Starting batch match: %d job(s) in %d batch(es) of up to %d.",
        total, num_batches, batch_size,
    )

    for batch_num, start in enumerate(range(0, total, batch_size), start=1):
        batch_jobs = jobs[start : start + batch_size]
        n = len(batch_jobs)

        logger.info(
            "[engine] Batch %d/%d — %d job(s) (indices %d–%d).",
            batch_num, num_batches, n, start, start + n - 1,
        )

        try:
            match_results = semantic_match_batch(
                resume_profile=resume_profile,
                job_profiles=batch_jobs,
            )
        except DailyBudgetExhaustedError as exc:
            logger.error(
                "[engine] Batch %d/%d — daily Groq budget exhausted. "
                "Filling remaining %d job(s) as failed and stopping. %s",
                batch_num, num_batches, total - start, exc,
            )
            # Fill all remaining jobs with budget-exhausted error
            remaining = total - start
            all_results.extend(
                [{"success": False, "error": f"daily_budget_exhausted: {exc}"}]
                * remaining
            )
            break

        except Exception as exc:
            logger.error(
                "[engine] Batch %d/%d — unrecoverable error, skipping %d job(s). %s",
                batch_num, num_batches, n, exc,
            )
            all_results.extend(
                [{"success": False, "error": str(exc)}] * n
            )
            continue

        # Score each match result from this batch
        batch_output: list[dict] = []
        for i, (job_profile, match_result) in enumerate(
            zip(batch_jobs, match_results)
        ):
            job_title = job_profile.get("title", "<unknown>")

            if match_result is None:
                logger.warning(
                    "[engine] Batch %d/%d, job %d ('%s'): LLM returned no result.",
                    batch_num, num_batches, start + i, job_title,
                )
                batch_output.append(
                    {"success": False, "error": "llm_missing_result"}
                )
                continue

            try:
                final_result = calculate_score(
                    resume_profile=resume_profile,
                    job_profile=job_profile,
                    match_result=match_result,
                )
                logger.debug(
                    "[engine] Batch %d/%d, job %d ('%s') — score=%.1f (%s)",
                    batch_num, num_batches, start + i, job_title,
                    final_result.get("score", 0),
                    final_result.get("overall_match", ""),
                )
                batch_output.append(final_result)

            except Exception as exc:
                logger.warning(
                    "[engine] Batch %d/%d, job %d ('%s'): scoring failed. %s",
                    batch_num, num_batches, start + i, job_title, exc,
                )
                batch_output.append({"success": False, "error": str(exc)})

        all_results.extend(batch_output)

    logger.info(
        "[engine] Batch match complete: %d/%d results returned.",
        len(all_results), total,
    )
    return all_results


# ---------------------------------------------------------------------------
# Single-job entry point (backward compat)
# ---------------------------------------------------------------------------

def match_resume_to_job(
    resume_profile: dict,
    job_profile:    dict,
    model: str = "groq/llama-3.1-8b-instant",   # informational only
) -> dict:
    """
    Match a resume against a single job profile.

    Kept for backward compatibility.  New callers should use
    match_resume_to_jobs_batch() to reduce API call count.

    Returns
    -------
    dict
        On success: full scoring result with "score", "overall_match", etc.
        On failure: {"success": False, "error": "<reason>"}
    """
    job_title = job_profile.get("title", "<unknown>")
    try:
        match_result = semantic_match(
            resume_profile=resume_profile,
            job_profile=job_profile,
        )
        final_result = calculate_score(
            resume_profile=resume_profile,
            job_profile=job_profile,
            match_result=match_result,
        )
        logger.debug(
            "[engine] Matched '%s' — score=%.1f (%s)",
            job_title,
            final_result.get("score", 0),
            final_result.get("overall_match", ""),
        )
        return final_result

    except DailyBudgetExhaustedError as exc:
        logger.error(
            "[engine] Daily Groq budget exhausted — stopping. %s", exc
        )
        return {"success": False, "error": f"daily_budget_exhausted: {exc}"}

    except Exception as exc:
        logger.warning(
            "[engine] Failed to match job '%s': %s", job_title, exc
        )
        return {"success": False, "error": str(exc)}