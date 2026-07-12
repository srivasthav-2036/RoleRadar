import os
import json
import pdfplumber
from google import genai

from backend.resume_tailoring.resume_schema import RESUME_SCHEMA, SKILLS_CATEGORY_INSTRUCTIONS

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY_FOR_EXTRACTION")
)


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

Generate 5 best diverse search queries suitable for searching jobs.
Queries should be role-focused and based on the given resume text.
Examples:
- Python Developer
- Backend Developer
- AI Engineer
- Machine Learning Engineer

Resume text:

{resume_text}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    data = response.text.strip()

    if data.startswith("```"):
        data = data.replace("```json", "").replace("```", "").strip()

    parsed = json.loads(data)

    resume_json = parsed["resume"]
    search_queries = parsed["queries"]

    return resume_json, search_queries


# if __name__ == "__main__":

#     resume, queries = extract_resume("resume.pdf")

#     print("========== RESUME ==========")
#     print(json.dumps(resume, indent=4))

#     print("\n========== SEARCH QUERIES ==========")
#     print(json.dumps(queries, indent=4))