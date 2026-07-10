import os
from typing import List

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

EMBEDDING_MODEL = "gemini-embedding-001"


def _embed(text: str) -> List[float]:
    """
    Generate an embedding using Gemini.
    """

    if not text or not text.strip():
        raise ValueError("Embedding text cannot be empty.")

    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT"
        ),
    )

    return response.embeddings[0].values


def build_resume_text(
    resume: dict,
    search_queries: list[str]
) -> str:
    """
    Convert parsed resume JSON into semantic text for embedding.
    """

    sections = []

    if resume.get("summary"):
        sections.append(f"Summary: {resume['summary']}")

    skills = resume.get("skills", {})

    for category, values in skills.items():
        if values:
            sections.append(
                f"{category}: {', '.join(values)}"
            )

    for exp in resume.get("experience", []):

        sections.append(
            f"""
Role: {exp.get("role", "")}
Company: {exp.get("company", "")}
Description: {exp.get("description", "")}
Skills: {", ".join(exp.get("skills", []))}
"""
        )

    for project in resume.get("projects", []):

        sections.append(
            f"""
Project: {project.get("title", "")}
Description: {project.get("description", "")}
Technologies: {", ".join(project.get("technologies", []))}
Domain: {project.get("domain", "")}
"""
        )

    if resume.get("education"):
        for edu in resume["education"]:
            sections.append(
                f"""
Degree: {edu.get("degree", "")}
College: {edu.get("college", "")}
CGPA: {edu.get("cgpa", "")}
Year: {edu.get("year", "")}
"""
            )

    if resume.get("certifications"):
        sections.append(
            "Certifications: " +
            ", ".join(resume["certifications"])
        )

    if resume.get("achievements"):
        sections.append(
            "Achievements: " +
            ", ".join(resume["achievements"])
        )

    if resume.get("languages"):
        sections.append(
            "Languages: " +
            ", ".join(resume["languages"])
        )

    if resume.get("domains"):
        sections.append(
            "Domains: " +
            ", ".join(resume["domains"])
        )

    if resume.get("keywords"):
        sections.append(
            "Keywords: " +
            ", ".join(resume["keywords"])
        )

    # These are used only as additional context,
    # not as the primary retrieval signal.
    if search_queries:
        sections.append(
            "Suggested Roles: " +
            ", ".join(search_queries)
        )

    return "\n".join(sections)


def build_job_text(
    job: dict,
    parsed: dict
) -> str:
    """
    Convert parsed job JSON into semantic text for embedding.
    """

    sections = []

    sections.append(f"Title: {job['title']}")

    if job.get("company"):
        sections.append(f"Company: {job['company']}")

    if parsed.get("required_skills"):
        sections.append(
            "Required Skills: " +
            ", ".join(parsed["required_skills"])
        )

    if parsed.get("preferred_skills"):
        sections.append(
            "Preferred Skills: " +
            ", ".join(parsed["preferred_skills"])
        )

    if parsed.get("experience_required"):
        sections.append(
            f"Experience: {parsed['experience_required']}"
        )

    if parsed.get("education_required"):
        sections.append(
            f"Education: {parsed['education_required']}"
        )

    if parsed.get("responsibilities"):
        sections.append(
            "Responsibilities: " +
            ", ".join(parsed["responsibilities"])
        )

    if parsed.get("tools"):
        sections.append(
            "Tools: " +
            ", ".join(parsed["tools"])
        )

    if parsed.get("technologies"):
        sections.append(
            "Technologies: " +
            ", ".join(parsed["technologies"])
        )

    if parsed.get("soft_skills"):
        sections.append(
            "Soft Skills: " +
            ", ".join(parsed["soft_skills"])
        )

    if parsed.get("domains"):
        sections.append(
            "Domains: " +
            ", ".join(parsed["domains"])
        )

    if parsed.get("keywords"):
        sections.append(
            "Keywords: " +
            ", ".join(parsed["keywords"])
        )

    return "\n".join(sections)


def generate_resume_embedding(
    resume_json: dict,
    search_queries: list[str]
):
    """
    Returns:
        embedding_text,
        embedding_vector
    """

    embedding_text = build_resume_text(
        resume_json,
        search_queries
    )

    embedding = _embed(embedding_text)

    return embedding_text, embedding


def generate_job_embedding(
    job: dict,
    parsed: dict
):
    """
    Returns:
        embedding_text,
        embedding_vector
    """

    embedding_text = build_job_text(
        job,
        parsed
    )

    embedding = _embed(embedding_text)

    return embedding_text, embedding