# semantic_engine/matcher.py

import json
import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY_FOR_SEMANTIC_MATCHING")
)


SYSTEM_PROMPT = """
You are the semantic matching engine for an AI job recommendation platform called RoleRadar.

Your task is to compare a structured candidate profile with a structured job profile.

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
TASKS
==========================

1. REQUIRED SKILLS

Identify ALL required skills satisfied by the candidate.

Return:

matched_required_skills

2. PREFERRED SKILLS

Identify ALL preferred skills satisfied by the candidate.

Return:

matched_preferred_skills

3. MATCHED SKILLS

Return the union of all matched required and preferred skills.

Return:

matched_skills

4. MISSING SKILLS

Return ONLY required skills that are missing.

Do NOT include preferred skills.

Return:

missing_skills

5. PROJECT MATCH

Evaluate how relevant the candidate's projects are.

Consider:

- technologies
- domains
- project descriptions
- responsibilities

Return ONLY one:

Excellent
High
Medium
Low

6. EXPERIENCE MATCH

Evaluate ONLY professional experience.

If the candidate has no professional experience:

- Do NOT penalize them for being a fresher.
- Evaluate whether their projects demonstrate comparable practical skills.

Return ONLY one:

Strong
Moderate
Weak

Examples

No experience + excellent projects
→ Moderate

Relevant internships
→ Strong

Unrelated experience
→ Weak

7. EDUCATION

Return ONLY one:

Meets
Partially Meets
Does Not Meet

8. CERTIFICATES

Return ONLY one:

Strong
Moderate
Weak
None

Consider relevance to the job.

9. RECOMMENDATION

Maximum 30 words.

Mention:

- strongest strengths
- biggest missing required skill (if any)

Do NOT mention percentages.

==========================
OUTPUT
==========================

Return EXACTLY this JSON.

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


def _extract_json(text: str) -> dict:
    """
    Extract JSON even if Gemini accidentally wraps it
    in markdown code fences.
    """

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


def semantic_match(
    resume_profile: dict,
    job_profile: dict,
    model: str = "gemini-2.5-flash",
) -> dict:
    """
    Compare a structured resume with a structured job profile.

    Returns
    -------
    dict
        Semantic matching result.
    """

    prompt = f"""
Candidate Profile

{json.dumps(resume_profile, indent=2)}

Job Profile

{json.dumps(job_profile, indent=2)}
"""

    response = client.models.generate_content(
        model=model,
        contents=[
            SYSTEM_PROMPT,
            prompt,
        ],
    )

    return _extract_json(response.text)