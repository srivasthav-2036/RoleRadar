"""
matcher.py

Semantic resume-to-job matching using Groq (llama-3.1-8b-instant).

BATCH MODE (v2):
Instead of one LLM call per job, semantic_match_batch() sends ONE
resume profile and up to MATCH_BATCH_SIZE job profiles in a single
request.  The LLM returns a "results" array with one entry per job,
identified by "job_index".  This mirrors the pattern used by
jd_parser.parse_job_descriptions_batch().

Token savings example (MATCH_BATCH_SIZE = 10):
  Before: 10 calls × ~1,500 tokens = 15,000 tokens
  After:  1 call  × ~4,500 tokens  =  4,500 tokens   (70% reduction)

RATE-LIMITING:
Uses the shared GroqThrottle class (backend/rate_limiting/groq_throttle.py)
for per-minute sliding-window pacing and exponential-backoff retry on
429s.  Daily budget is tracked via usage_tracker (same as jd_parser).

CONCURRENCY:
Multiple user pipelines run in separate daemon threads.  They share the
module-level _throttle instance, so whichever thread reaches
wait_for_capacity() first may sleep while the other thread's requests
age out of the 60-second window — naturally serialising API calls
without blocking the web server.

FALLBACK MODEL:
If llama-3.1-8b-instant is deprecated, switch MODEL to
"openai/gpt-oss-20b" and update limits to (RPM=30, TPM=8000).
"""

import json
import logging
import os
import time

from openai import OpenAI
from dotenv import load_dotenv

from backend.rate_limiting.usage_tracker import (
    check_budget,
    record_usage,
    estimate_tokens,
    DailyBudgetExhaustedError,
)
from backend.rate_limiting.groq_throttle import GroqThrottle

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Client + model constants
# ---------------------------------------------------------------------------

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY_FOR_SEMANTIC_MATCHING"),
    base_url="https://api.groq.com/openai/v1",
)

MODEL         = "llama-3.1-8b-instant"
PROVIDER_NAME = "groq_semantic_matching"

# Confirmed free-tier limits for llama-3.1-8b-instant (Groq console).
# Update if you switch models.
RPM_LIMIT = 30
RPD_LIMIT = 14_400
TPM_LIMIT = 6_000
TPD_LIMIT = 500_000

# Number of jobs evaluated in a single LLM call.
# Lower values are safer if resume/job JSONs are large.
# Higher values reduce API calls and token cost but risk partial failures.
# Default: 5 — conservative for 8B model accuracy on structured output.
MATCH_BATCH_SIZE = 5

# Module-level throttle (shared across all threads, NOT shared with jd_parser)
_throttle = GroqThrottle(rpm_limit=RPM_LIMIT, tpm_limit=TPM_LIMIT, label="[matcher]")

# ---------------------------------------------------------------------------
# System prompt (used for BOTH single and batch calls)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """
You are the semantic matching engine for an AI job recommendation platform called RoleRadar.

Your task is to compare a structured candidate profile with one or more structured job profiles.

==========================
RULES
==========================

- Use ONLY the provided JSON.
- Never invent skills, experience, education, projects, certifications or achievements.
- If information is missing, assume it is unavailable.
- Use semantic understanding instead of only exact keyword matching.
- Treat closely related technologies as matches where appropriate.
- Do NOT infer skills that are not evident from the data.
- Return ONLY valid JSON.
- Do NOT wrap JSON in markdown.
- Do NOT include explanations outside JSON.
- Do NOT return null values. Use empty lists ("[]") where appropriate.

==========================
TASKS (per job)
==========================

1. REQUIRED SKILLS
Identify ALL required skills satisfied by the candidate.
Return: matched_required_skills

2. PREFERRED SKILLS
Identify ALL preferred skills satisfied by the candidate.
Return: matched_preferred_skills

3. MATCHED SKILLS
Return the union of all matched required and preferred skills.
Return: matched_skills

4. MISSING SKILLS
Return ONLY required skills that are missing. Do NOT include preferred skills.
Return: missing_skills

5. PROJECT MATCH
Evaluate how relevant the candidate's projects are (technologies, domains, descriptions, responsibilities).
Return ONLY one: Excellent | High | Medium | Low

6. EXPERIENCE MATCH
Evaluate ONLY professional experience.
If no professional experience: do NOT penalize a fresher; evaluate whether projects demonstrate comparable skills.
Return ONLY one: Strong | Moderate | Weak
Examples:
  No experience + excellent projects → Moderate
  Relevant internships              → Strong
  Unrelated experience              → Weak

7. EDUCATION
Return ONLY one: Meets | Partially Meets | Does Not Meet

8. CERTIFICATES
Consider relevance to the job.
Return ONLY one: Strong | Moderate | Weak | None

9. RECOMMENDATION
Maximum 30 words. Mention strongest strengths and biggest missing required skill (if any).
Do NOT mention percentages.

==========================
BATCH OUTPUT FORMAT
==========================

When evaluating multiple jobs, return EXACTLY this JSON:

{
    "results": [
        {
            "job_index": 0,
            "matched_required_skills": [],
            "matched_preferred_skills": [],
            "matched_skills": [],
            "missing_skills": [],
            "project_match": "",
            "experience_match": "",
            "education_match": "",
            "certificate_match": "",
            "recommendation": ""
        }
    ]
}

Each entry in "results" MUST include its "job_index" matching the ### JOB <index> label.
Include one entry per job. Do NOT skip any job.
"""

# Used for single-job calls (backward compat); returns a plain object not wrapped in "results"
_SINGLE_JOB_OUTPUT_NOTE = """
==========================
SINGLE JOB OUTPUT FORMAT
==========================

Return EXACTLY this JSON (no "results" wrapper):

{
    "matched_required_skills": [],
    "matched_preferred_skills": [],
    "matched_skills": [],
    "missing_skills": [],
    "project_match": "",
    "experience_match": "",
    "education_match": "",
    "certificate_match": "",
    "recommendation": ""
}
"""

# ---------------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------------

def _strip_markdown(text: str) -> str:
    """Remove optional markdown code fences from model output."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines)
    return text


def _extract_json_object(text: str) -> dict:
    """
    Extract the outermost JSON object from model output, even if the
    model adds stray text before/after.
    """
    text = _strip_markdown(text)
    start = text.find("{")
    end   = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON object found in model response: {text[:200]!r}")
    return json.loads(text[start : end + 1])


# ---------------------------------------------------------------------------
# Core Groq call
# ---------------------------------------------------------------------------

def _call_groq(
    system_prompt: str,
    user_prompt:   str,
    estimated_output_tokens: int,
) -> str:
    """
    Make one Groq chat-completion call:
    1. Estimate token cost and check daily budget.
    2. Wait for per-minute capacity.
    3. Call Groq with exponential-backoff retry on 429.
    4. Record actual token usage.
    """
    estimated_input = estimate_tokens(system_prompt + user_prompt)
    estimated_total = estimated_input + estimated_output_tokens

    check_budget(
        provider=PROVIDER_NAME,
        estimated_requests=1,
        estimated_tokens=estimated_total,
        rpd_limit=RPD_LIMIT,
        tpd_limit=TPD_LIMIT,
    )

    _throttle.wait_for_capacity(estimated_total)

    def _do_call() -> str:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )
        actual_tokens = (
            response.usage.total_tokens if response.usage else estimated_total
        )
        _throttle.record_call(actual_tokens)
        record_usage(provider=PROVIDER_NAME, requests=1, tokens=actual_tokens)
        logger.debug(
            "[matcher] Groq call succeeded (tokens=%d)", actual_tokens
        )
        return response.choices[0].message.content

    return _throttle.call_with_retry(_do_call)


# ---------------------------------------------------------------------------
# Public API — batch
# ---------------------------------------------------------------------------

def semantic_match_batch(
    resume_profile: dict,
    job_profiles:   list[dict],
) -> list[dict | None]:
    """
    Match ONE resume against MULTIPLE job profiles in a single LLM call.

    Parameters
    ----------
    resume_profile : dict
        Parsed resume JSON (sent once for the whole batch).
    job_profiles : list[dict]
        List of parsed job description JSONs to evaluate.

    Returns
    -------
    list[dict | None]
        Same length as `job_profiles`, same order.  Each element is the
        match result dict, or None if the LLM omitted that job_index.
        Callers must treat None entries as failed matches and skip them.

    Raises
    ------
    DailyBudgetExhaustedError
        When today's Groq budget is exhausted — callers should stop
        processing further batches for the rest of the day.
    Exception
        Any unrecoverable error after all retries.
    """
    if not job_profiles:
        return []

    n = len(job_profiles)

    # Build numbered job block — resume sent once, jobs labelled ### JOB N
    numbered_jobs = "\n\n".join(
        f"### JOB {i}\n{json.dumps(jp, separators=(',', ':'))}"
        for i, jp in enumerate(job_profiles)
    )

    user_prompt = (
        f"Candidate Profile:\n{json.dumps(resume_profile, separators=(',', ':'))}"
        f"\n\n{numbered_jobs}"
    )

    # Estimated output: ~200 tokens per job result
    estimated_output = n * 200

    t0 = time.time()
    raw = _call_groq(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        estimated_output_tokens=estimated_output,
    )
    elapsed = time.time() - t0

    parsed = _extract_json_object(raw)
    results_list = parsed.get("results") if isinstance(parsed, dict) else parsed

    if not isinstance(results_list, list):
        raise ValueError(
            f"[matcher] Batch response did not contain a 'results' array. "
            f"Got: {str(parsed)[:200]}"
        )

    by_index: dict[int, dict] = {}
    for item in results_list:
        idx = item.get("job_index")
        if idx is not None:
            by_index[int(idx)] = item

    results: list[dict | None] = []
    missing: list[int] = []
    for i in range(n):
        if i in by_index:
            results.append(by_index[i])
        else:
            missing.append(i)
            results.append(None)

    if missing:
        logger.warning(
            "[matcher] Batch missing %d/%d job(s) at indices %s — "
            "those jobs will be skipped this run.",
            len(missing), n, missing,
        )

    logger.info(
        "[matcher] Batch of %d job(s) completed in %.1f s "
        "(%d matched, %d missing).",
        n, elapsed, n - len(missing), len(missing),
    )

    return results


# ---------------------------------------------------------------------------
# Public API — single job (backward compat, wraps batch)
# ---------------------------------------------------------------------------

def semantic_match(
    resume_profile: dict,
    job_profile:    dict,
    model: str = MODEL,   # kept for backward-compat; ignored (Groq used)
) -> dict:
    """
    Match a resume against a single job profile.

    This is a thin wrapper around semantic_match_batch() kept for
    backward compatibility.  For bulk matching, call
    semantic_match_batch() directly to avoid per-job overhead.

    Raises
    ------
    ValueError
        If the LLM fails to return a result for the job.
    DailyBudgetExhaustedError
        When today's Groq budget is exhausted.
    Exception
        Any unrecoverable error after all retries.
    """
    results = semantic_match_batch(resume_profile, [job_profile])
    if not results or results[0] is None:
        raise ValueError(
            "[matcher] LLM did not return a result for the job profile."
        )
    return results[0]