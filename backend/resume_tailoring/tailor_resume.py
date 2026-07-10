"""
tailor_resume.py

Uses Gemini to tailor a resume to a specific job. Hard constraint:
never invent experience, projects, skills, or achievements - only
reorder, reword, and optimize keyword usage within what's already
there. Returns JSON in the EXACT same schema as the input resume so
nothing downstream (PDF template, frontend editor) needs to branch
on shape.
"""

import json
import os

from dotenv import load_dotenv
from google import genai

from resume_tailoring.fetch_context import build_tailoring_context

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY_FOR_TAILORING")
)

TAILOR_PROMPT = """
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
- Return the resume in EXACTLY this same shape as the input resume
  JSON - same top-level keys, same nested structure. Do not add or
  remove keys.

==========================
OUTPUT
==========================

Return ONLY the tailored resume JSON (same schema as input resume).
Do not wrap it in another object, do not add commentary.
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


def generate_tailored_resume(user_id: str, job_id: str) -> dict:
    """
    Returns:
        {
            "tailored_resume": <resume JSON, same schema as original>,
            "job": <job dict, for the PDF header/context>,
        }

    This is the "editable preview" step - the frontend should show
    tailored_resume to the user for review/edits BEFORE calling
    pdf_generator.py.
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

    return {
        "tailored_resume": tailored_resume,
        "job": context["job"],
    }