"""
tailor_resume.py

Uses Gemini to tailor a resume to a specific job. Hard constraint:
never invent experience, projects, skills, or achievements - only
reorder, reword, and optimize keyword usage within what's already
there.

Two-layer safety on the output shape:
    1. The prompt now includes the EXACT target schema (shared with
       resume_extract.py via resume_tailoring/resume_schema.py),
       instead of just saying "same shape as input" - Gemini is told
       precisely what keys and structure to return.
    2. validate_resume_shape() checks the result actually has all
       required top-level keys before it's trusted downstream.

Caching: get_or_generate_tailored_resume() is the entry point the
API/frontend should call. It checks recommendations.tailored_resume
first - if already generated, returns the cached JSON with zero
Gemini calls. Only generates (and then saves) if nothing is cached
yet.
"""

import json
import os

from dotenv import load_dotenv
from google import genai

from backend.resume_tailoring.resume_schema import (
    RESUME_SCHEMA,
    SKILLS_CATEGORY_INSTRUCTIONS,
    validate_resume_shape,
)
from backend.resume_tailoring.fetch_context import (
    build_tailoring_context,
    get_recommendation,
)
from backend.recommender.recommendation_storage import save_tailored_resume

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY_FOR_TAILORING")
)

TAILOR_PROMPT = f"""
You are an expert resume tailoring assistant for RoleRadar.

You will be given:
- A candidate's resume (JSON)
- A target job (JSON)
- Match details from a prior analysis, if available (missing skills,
  matched skills, a short recommendation note) - use this as a guide
  for what to emphasize, not as new facts to add.

==========================
STRICT RULES
==========================

- NEVER invent experience, projects, skills, certifications, or
  achievements that are not already present in the resume.
- You MAY reorder items (e.g. put most relevant project first).
- You MAY reword bullet points/descriptions for clarity and keyword
  alignment with the job - but the underlying fact/claim must remain
  true to the original.
- You MAY reorder or lightly rephrase skill entries for ATS keyword
  matching, but do NOT add a skill that isn't already listed
  somewhere in the resume.
- You MAY rewrite the "summary" field to better align with the job,
  as long as it stays truthful to the resume content.
- Do NOT change factual fields: company names, dates/duration,
  degree, college, cgpa, year, contact info.
- Return ONLY valid JSON, no markdown, no explanation.

{SKILLS_CATEGORY_INSTRUCTIONS}

==========================
REQUIRED OUTPUT SCHEMA
==========================

Return EXACTLY this schema - same top-level keys, same nesting
(except "skills", whose category names are dynamic - see above).
Every top-level key must be present even if empty ("" or []):

{RESUME_SCHEMA}

Do not wrap this in another object. Do not add commentary. Return
only the JSON above, filled in with tailored content.
"""


def _extract_json(text: str) -> dict:
    text = text.strip()

    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines)

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("Gemini did not return valid JSON.")

    return json.loads(text[start:end + 1])


def _generate_tailored_resume(user_id: str, job_id: str) -> dict:
    """
    Always calls Gemini - no caching here. Use
    get_or_generate_tailored_resume() instead unless you specifically
    need to force a fresh generation.
    """
    context = build_tailoring_context(user_id, job_id)

    prompt = f"""
Candidate Resume:
{json.dumps(context["resume"], indent=2)}

Target Job:
{json.dumps(context["job"], indent=2)}

Match Details (may be null if not previously analyzed):
{json.dumps(context["match_details"], indent=2)}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[TAILOR_PROMPT, prompt],
    )

    tailored_resume = _extract_json(response.text)

    missing_keys = validate_resume_shape(tailored_resume)
    if missing_keys:
        raise ValueError(
            f"Tailored resume is missing required keys: {missing_keys}. "
            "Gemini did not follow the required schema."
        )

    return tailored_resume


def get_or_generate_tailored_resume(user_id: str, job_id: str) -> dict:
    """
    The entry point the app/API should call when a user clicks
    "Get Tailored Resume".

    1. Confirms this job was actually recommended to this user (via
       get_recommendation - raises ValueError if not).
    2. If a tailored_resume is already cached on that recommendation
       row, returns it directly - no Gemini call.
    3. Otherwise generates it, saves it to recommendations.tailored_resume,
       and returns it.
    """
    recommendation = get_recommendation(user_id, job_id)

    if recommendation is None:
        raise ValueError(
            f"Job {job_id} was not recommended to user {user_id} - "
            "tailoring is only available for recommended jobs."
        )

    if recommendation["tailored_resume"] is not None:
        return recommendation["tailored_resume"]

    tailored_resume = _generate_tailored_resume(user_id, job_id)

    save_tailored_resume(
        user_id=user_id,
        job_id=job_id,
        tailored_resume=tailored_resume,
    )

    return tailored_resume