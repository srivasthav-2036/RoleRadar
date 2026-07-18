# import json
# import os
# from google import genai
# from dotenv import load_dotenv

# load_dotenv()

# client = genai.Client(
#     api_key=os.getenv("GEMINI_API_KEY_FOR_JD_PARSING")
# )


# JD_PARSER_PROMPT = """
# You are an expert Job Description parser.

# You will be given:

# - Job Title
# - Company Name
# - Job Description

# The description may be:
# - Complete
# - Partial
# - Truncated
# - Empty
# - Not available


# Your goal is to extract the most accurate structured information.

# Rules:

# - Use ALL available information (title, company and description).
# - If the description is incomplete, use the title and company as additional context.
# - Infer only information that is highly likely.
# - Never invent experience requirements, education requirements or responsibilities.
# - If a field cannot be determined confidently, return an empty string or empty list.

# Return ONLY valid JSON.

# {
#     "required_skills": [],
#     "preferred_skills": [],
#     "experience_required": "",
#     "education_required": "",
#     "responsibilities": [],
#     "job_level": "",
#     "employment_type": "",
#     "tools": [],
#     "technologies": [],
#     "keywords": [],
#     "soft_skills": [],
#     "domains": []
# }
# """


# def parse_job_description(
#     title: str,
#     company: str,
#     description: str | None,
# ) -> dict:
#     """
#     Parse a job description using Gemini.
#     """

#     content = f"""
# Job Title:
# {title}

# Company:
# {company}

# Job Description:
# {description or "Not available"}
# """

#     response = client.models.generate_content(
#         model="gemini-2.5-flash",
#         contents=f"{JD_PARSER_PROMPT}\n\n{content}",
#     )

#     text = response.text.strip()

#     if text.startswith("```json"):
#         text = text[7:-3].strip()
#     elif text.startswith("```"):
#         text = text[3:-3].strip()

#     return json.loads(text)

"""
jd_parser.py

Uses Groq for JD parsing - Gemini's free tier daily quota (20
requests/day) was far too low for this volume.

MODEL CHOICE: llama-3.1-8b-instant, based on actual confirmed limits
from the Groq console (30 RPM / 14,400 RPD / 6,000 TPM / 500,000 TPD)
- far better RPD/TPD than openai/gpt-oss-20b (30/1,000/8,000/200,000).
Groq HAS announced this model's deprecation, so if it stops working,
switch MODEL below to "openai/gpt-oss-20b" and update the four limit
constants to (30, 1000, 8000, 200000) - confirmed from the same
console table.

TPM (6,000/minute) is the tight constraint here, not RPM (30/minute
is generous) - a single batch call's tokens can approach or exceed
6,000 by itself depending on job description lengths. So pacing uses
a sliding 60-second window tracking actual tokens used, not a fixed
sleep interval - a fixed interval can't tell the difference between
"3 small batches" and "1 big batch" using the same time budget.

RPD/TPD (daily limits) are checked against a DB-persisted counter
(rate_limiting/usage_tracker.py) since they accumulate across
multiple separate scheduled runs per day, which a fixed in-process
sleep can't coordinate.
"""

import json
import logging
import os
import re
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

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY_FOR_JD_PARSING"),
    base_url="https://api.groq.com/openai/v1",
)

MODEL         = "llama-3.1-8b-instant"
PROVIDER_NAME = "groq_jd_parsing"

# Confirmed from Groq console for this model — update if you switch models.
RPM_LIMIT = 30
RPD_LIMIT = 14_400
TPM_LIMIT = 6_000
TPD_LIMIT = 500_000

# Jobs per LLM call.  TPM=6000 is the tight constraint; keep batches
# small enough that one call's tokens stay comfortably under the limit.
# 5 is a good balance between throughput and per-call token cost.
BATCH_SIZE = 5

# Per-module throttle instance (independent window from matcher.py)
_throttle = GroqThrottle(rpm_limit=RPM_LIMIT, tpm_limit=TPM_LIMIT, label="[jd_parser]")

__all__ = [
    "parse_job_descriptions_batch",
    "parse_job_description",
    "DailyBudgetExhaustedError",
]


JD_PARSER_PROMPT = """
You are an expert Job Description parser optimized for SEMANTIC
SEARCH RETRIEVAL - not a general summarizer. Every word costs
embedding tokens later, so be concise.

Return ONLY valid JSON.

You will be given:

- Job Title
- Company Name
- Job Description

The description may be complete, partial, truncated, empty, or not
available.

OUTPUT RULES:
- Extract concise information only (short phrases, never full sentences).
- Normalize skills and technologies (e.g. ReactJS -> React, Node -> Node.js).
- Remove duplicates across all fields.
- Responsibilities must be 3-10 word action phrases.
- If the description is incomplete, use only high-confidence information from the title and company.
- Never invent years of experience, salary, certifications or technologies.
- Leave fields empty instead of guessing.

INCOMPLETE DESCRIPTIONS:
- If the description is empty, partial, or truncated, use the job
  title and company as additional context.
- Only infer high-confidence, generic role information - never invent
  years of experience, education requirements, certifications,
  salary, or specific technologies UNLESS nearly universal for that
  exact role (e.g. "SQL" for "Data Analyst" is reasonable; a specific
  cloud vendor is not).
- Prefer precision over completeness - leave a field EMPTY rather
  than guessing.

FIELD LIMITS (hard maximums - never exceed):
- required_skills: max 20 items
- preferred_skills: max 10 items
- technologies: max 20 items
- tools: max 15 items
- responsibilities: max 8 items
- soft_skills: max 8 items
- domains: max 5 items
- keywords: max 15 items

Each result must follow EXACTLY this JSON schema:

{
    "required_skills": [],
    "preferred_skills": [],
    "experience_required": "",
    "education_required": "",
    "responsibilities": [],
    "job_level": "",
    "employment_type": "",
    "tools": [],
    "technologies": [],
    "keywords": [],
    "soft_skills": [],
    "domains": []
}
"""

FIELD_LIMITS = {
    "required_skills": 20,
    "preferred_skills": 10,
    "technologies": 20,
    "tools": 15,
    "responsibilities": 8,
    "soft_skills": 8,
    "domains": 5,
    "keywords": 15,
}

def _prepare_description(description: str | None, max_chars: int = 3500) -> str:
    """
    Clean a raw job description before sending it to Groq.
    Keeps the database untouched.
    """
    if not description:
        return "Not available"

    # collapse whitespace
    description = re.sub(r"\s+", " ", description).strip()

    # remove very long legal/privacy tails
    stop_markers = [
        "Equal Opportunity Employer",
        "Privacy Policy",
        "Cookie Policy",
        "Accessibility",
        "EEO Statement",
        "Accommodation",
        "About Us",
    ]

    for marker in stop_markers:
        pos = description.find(marker)
        if pos != -1:
            description = description[:pos]
            break

    return description[:max_chars]

def _enforce_field_limits(parsed: dict) -> dict:
    """
    Programmatic safety net - the prompt asks the model to respect
    these limits, but LLMs don't always comply exactly. This
    guarantees it regardless of model behavior.
    """
    for field, limit in FIELD_LIMITS.items():
        value = parsed.get(field)
        if isinstance(value, list) and len(value) > limit:
            parsed[field] = value[:limit]
    return parsed

def _call_groq_json(prompt: str) -> str:
    """
    Makes one Groq call with JSON mode enforced.
    Checks the daily budget first, then paces against the per-minute
    sliding window, then calls Groq with exponential-backoff retry on 429.
    """
    estimated_input  = estimate_tokens(prompt)
    estimated_output = 1200   # conservative; corrected after call
    estimated_total  = estimated_input + estimated_output

    logger.debug(
        "[jd_parser] estimated_input=%d, estimated_total=%d, TPM_LIMIT=%d",
        estimated_input, estimated_total, TPM_LIMIT,
    )

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
                {"role": "system", "content": JD_PARSER_PROMPT},
                {"role": "user",   "content": prompt},
            ],
            response_format={"type": "json_object"},
        )
        actual_tokens = response.usage.total_tokens if response.usage else estimated_total
        _throttle.record_call(actual_tokens)
        record_usage(provider=PROVIDER_NAME, requests=1, tokens=actual_tokens)
        logger.debug("[jd_parser] Groq call succeeded (tokens=%d)", actual_tokens)
        return response.choices[0].message.content

    return _throttle.call_with_retry(_do_call)


def parse_job_description(title: str, company: str, description: str | None) -> dict:
    """
    Parse a SINGLE job description. Prefer parse_job_descriptions_batch()
    for multiple jobs - fewer requests, same TPM cost either way.
    """
    prompt = f"""

Job Title:
{title}

Company:
{company}

Job Description:
{_prepare_description(description)}

Return ONLY the JSON object for this one job.
"""
    text_response = _call_groq_json(prompt)
    return _enforce_field_limits(json.loads(text_response))


def parse_job_descriptions_batch(jobs: list[dict]) -> list[dict | None]:
    """
    Parses MULTIPLE jobs in ONE Groq call. jobs: list of
    {"title": ..., "company": ..., "description": ...}

    Returns a list the SAME LENGTH as input, same order. Each element
    is the parsed dict, or None if Gemini/Groq's response didn't
    include that job's index - callers MUST skip None entries (that
    job stays unparsed, retried automatically next run since it's
    never marked as stored).

    Raises DailyBudgetExhaustedError if today's budget is already
    too tight for this call - callers should stop attempting further
    batches for the rest of the day.
    """
    if not jobs:
        return []

    numbered_jobs = "\n\n".join(
        f"### JOB {i}\n"
        f"Title: {job['title']}\n"
        f"Company: {job['company']}\n"
        f"Description:{_prepare_description(job.get('description'))}"
        for i, job in enumerate(jobs)
    )

#     batch_prompt = f"""
# {JD_PARSER_PROMPT}

# You will be given MULTIPLE jobs below, each labeled "### JOB <index>"
# starting from 0. Return a JSON OBJECT with a single key "results",
# whose value is a JSON array. Each array element MUST include a
# "job_index" integer field matching the label of the job it
# corresponds to, IN ADDITION to all the schema fields above.

# {numbered_jobs}
# """

    batch_prompt = f"""

    Parse every job.

    Return:

    {{
        "results":[
            {{
                "job_index":0,
                ...
            }}
        ]
    }}

    Each object MUST contain its matching job_index.

    {numbered_jobs}
    """

    text_response = _call_groq_json(batch_prompt)
    parsed = json.loads(text_response)

    # JSON mode requires a top-level object, not a bare array - so
    # results are nested under "results" per the prompt above
    results_list = parsed.get("results") if isinstance(parsed, dict) else parsed

    if not isinstance(results_list, list):
        raise ValueError("Groq did not return a JSON array of results for the batch.")

    by_index = {}
    for item in results_list:
        idx = item.get("job_index")
        if idx is not None:
            by_index[idx] = item

    results = []
    missing = []
    for i in range(len(jobs)):
        if i in by_index:
            results.append(_enforce_field_limits(by_index[i]))
        else:
            missing.append(i)
            results.append(None)

    if missing:
        logger.warning(
            "[jd_parser] Batch missing %d/%d job(s) at positions %s — "
            "skipped this run, retried automatically next run.",
            len(missing), len(jobs), missing,
        )

    return results