# 

"""
resume_extract.py

Migrated from Gemini to Groq (llama-3.1-8b-instant), same model
jd_parser.py uses, for consistency and to keep everything off
Gemini's restrictive free tier. Low volume (one call per user
upload), so uses simple per-call throttling rather than the full
sliding-window pacing jd_parser.py needs for bulk work - but still
checks the same DB-persisted daily budget (under a separate provider
name, so it doesn't compete with jd_parser.py's JD-parsing budget).
"""

import os
import time

import pdfplumber
from openai import OpenAI
from dotenv import load_dotenv

from backend.resume_tailoring.resume_schema import RESUME_SCHEMA, SKILLS_CATEGORY_INSTRUCTIONS, EDUCATION_GRADE_INSTRUCTIONS
from backend.rate_limiting.usage_tracker import check_budget, record_usage, estimate_tokens, DailyBudgetExhaustedError

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)

MODEL = "llama-3.1-8b-instant"
PROVIDER_NAME = "groq_resume_extraction"

# Same confirmed limits as jd_parser.py's llama-3.1-8b-instant usage -
# tracked under a SEPARATE provider name in api_usage so this doesn't
# compete with the JD-parsing budget.
RPD_LIMIT = 14400
TPD_LIMIT = 500000

MIN_SECONDS_BETWEEN_CALLS = 2.0  # simple fixed pacing - fine for low-volume, user-triggered calls

_last_call_time = 0.0


def _throttle():
    global _last_call_time
    elapsed = time.time() - _last_call_time
    if elapsed < MIN_SECONDS_BETWEEN_CALLS:
        time.sleep(MIN_SECONDS_BETWEEN_CALLS - elapsed)
    _last_call_time = time.time()


def extract_pdf_text(pdf_path: str) -> str:
    """Extract plain text from a PDF."""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()


def extract_resume(pdf_path: str):
    """
    Returns:
        resume_json (dict) - matches resume_tailoring.resume_schema.RESUME_SCHEMA
        search_queries (list[str])

    Raises DailyBudgetExhaustedError if today's Groq resume-extraction
    budget is already exhausted - caller (the upload endpoint) should
    surface this as a clear "try again later" error to the user.
    """
    resume_text = extract_pdf_text(pdf_path)

    prompt = f"""
You are an expert ATS Resume Parser.

Return ONLY valid JSON. No markdown. No explanation. No extra text.

Return exactly this schema:

{{
    "resume": {RESUME_SCHEMA},
    "queries": ["query1", "query2"]
}}

{SKILLS_CATEGORY_INSTRUCTIONS}

{EDUCATION_GRADE_INSTRUCTIONS}

Generate 3 best diverse search queries suitable for searching jobs.
Queries should be role-focused and based on the given resume text.
Examples:
- Python Developer
- Backend Developer
- AI Engineer
- Machine Learning Engineer

Resume text:

{resume_text}
"""

    estimated_tokens = estimate_tokens(prompt) + 1500  # rough output estimate

    check_budget(
        provider=PROVIDER_NAME,
        estimated_requests=1,
        estimated_tokens=estimated_tokens,
        rpd_limit=RPD_LIMIT,
        tpd_limit=TPD_LIMIT,
    )

    _throttle()

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )

    actual_tokens = response.usage.total_tokens if response.usage else estimated_tokens
    record_usage(provider=PROVIDER_NAME, requests=1, tokens=actual_tokens)

    import json
    parsed = json.loads(response.choices[0].message.content)

    return parsed["resume"], parsed["queries"]