import json
import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY_FOR_JD_PARSING")
)


JD_PARSER_PROMPT = """
You are an expert Job Description parser.

You will be given:

- Job Title
- Company Name
- Job Description

The description may be:
- Complete
- Partial
- Truncated
- Empty
- Not available


Your goal is to extract the most accurate structured information.

Rules:

- Use ALL available information (title, company and description).
- If the description is incomplete, use the title and company as additional context.
- Infer only information that is highly likely.
- Never invent experience requirements, education requirements or responsibilities.
- If a field cannot be determined confidently, return an empty string or empty list.

Return ONLY valid JSON.

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


def parse_job_description(
    title: str,
    company: str,
    description: str | None,
) -> dict:
    """
    Parse a job description using Gemini.
    """

    content = f"""
Job Title:
{title}

Company:
{company}

Job Description:
{description or "Not available"}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"{JD_PARSER_PROMPT}\n\n{content}",
    )

    text = response.text.strip()

    if text.startswith("```json"):
        text = text[7:-3].strip()
    elif text.startswith("```"):
        text = text[3:-3].strip()

    return json.loads(text)