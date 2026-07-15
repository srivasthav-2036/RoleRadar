# import os
# from typing import List

# from dotenv import load_dotenv
# from google import genai
# from google.genai import types

# load_dotenv()

# client = genai.Client(
#     api_key=os.getenv("GEMINI_API_KEY_FOR_EMBEDDINGS")
# )

# EMBEDDING_MODEL = "gemini-embedding-001"


# def _embed(text: str) -> List[float]:
#     """
#     Generate an embedding using Gemini.
#     """

#     if not text or not text.strip():
#         raise ValueError("Embedding text cannot be empty.")

#     response = client.models.embed_content(
#         model=EMBEDDING_MODEL,
#         contents=text,
#         config=types.EmbedContentConfig(
#             task_type="RETRIEVAL_DOCUMENT"
#         ),
#     )

#     return response.embeddings[0].values


# def build_resume_text(
#     resume: dict,
#     search_queries: list[str]
# ) -> str:
#     """
#     Convert parsed resume JSON into semantic text for embedding.
#     """

#     sections = []

#     if resume.get("summary"):
#         sections.append(f"Summary: {resume['summary']}")

#     skills = resume.get("skills", {})

#     for category, values in skills.items():
#         if values:
#             sections.append(
#                 f"{category}: {', '.join(values)}"
#             )

#     for exp in resume.get("experience", []):

#         sections.append(
#             f"""
# Role: {exp.get("role", "")}
# Company: {exp.get("company", "")}
# Description: {exp.get("description", "")}
# Skills: {", ".join(exp.get("skills", []))}
# """
#         )

#     for project in resume.get("projects", []):

#         sections.append(
#             f"""
# Project: {project.get("title", "")}
# Description: {project.get("description", "")}
# Technologies: {", ".join(project.get("technologies", []))}
# Domain: {project.get("domain", "")}
# """
#         )

#     if resume.get("education"):
#         for edu in resume["education"]:
#             sections.append(
#                 f"""
# Degree: {edu.get("degree", "")}
# College: {edu.get("college", "")}
# CGPA: {edu.get("cgpa", "")}
# Year: {edu.get("year", "")}
# """
#             )

#     if resume.get("certifications"):
#         sections.append(
#             "Certifications: " +
#             ", ".join(resume["certifications"])
#         )

#     if resume.get("achievements"):
#         sections.append(
#             "Achievements: " +
#             ", ".join(resume["achievements"])
#         )

#     if resume.get("languages"):
#         sections.append(
#             "Languages: " +
#             ", ".join(resume["languages"])
#         )

#     if resume.get("domains"):
#         sections.append(
#             "Domains: " +
#             ", ".join(resume["domains"])
#         )

#     if resume.get("keywords"):
#         sections.append(
#             "Keywords: " +
#             ", ".join(resume["keywords"])
#         )

#     # These are used only as additional context,
#     # not as the primary retrieval signal.
#     if search_queries:
#         sections.append(
#             "Suggested Roles: " +
#             ", ".join(search_queries)
#         )

#     return "\n".join(sections)


# def build_job_text(
#     job: dict,
#     parsed: dict
# ) -> str:
#     """
#     Convert parsed job JSON into semantic text for embedding.
#     """

#     sections = []

#     sections.append(f"Title: {job['title']}")

#     if job.get("company"):
#         sections.append(f"Company: {job['company']}")

#     if parsed.get("required_skills"):
#         sections.append(
#             "Required Skills: " +
#             ", ".join(parsed["required_skills"])
#         )

#     if parsed.get("preferred_skills"):
#         sections.append(
#             "Preferred Skills: " +
#             ", ".join(parsed["preferred_skills"])
#         )

#     if parsed.get("experience_required"):
#         sections.append(
#             f"Experience: {parsed['experience_required']}"
#         )

#     if parsed.get("education_required"):
#         sections.append(
#             f"Education: {parsed['education_required']}"
#         )

#     if parsed.get("responsibilities"):
#         sections.append(
#             "Responsibilities: " +
#             ", ".join(parsed["responsibilities"])
#         )

#     if parsed.get("tools"):
#         sections.append(
#             "Tools: " +
#             ", ".join(parsed["tools"])
#         )

#     if parsed.get("technologies"):
#         sections.append(
#             "Technologies: " +
#             ", ".join(parsed["technologies"])
#         )

#     if parsed.get("soft_skills"):
#         sections.append(
#             "Soft Skills: " +
#             ", ".join(parsed["soft_skills"])
#         )

#     if parsed.get("domains"):
#         sections.append(
#             "Domains: " +
#             ", ".join(parsed["domains"])
#         )

#     if parsed.get("keywords"):
#         sections.append(
#             "Keywords: " +
#             ", ".join(parsed["keywords"])
#         )

#     return "\n".join(sections)


# def generate_resume_embedding(
#     resume_json: dict,
#     search_queries: list[str]
# ):
#     """
#     Returns:
#         embedding_text,
#         embedding_vector
#     """

#     embedding_text = build_resume_text(
#         resume_json,
#         search_queries
#     )

#     embedding = _embed(embedding_text)

#     return embedding_text, embedding


# def generate_job_embedding(
#     job: dict,
#     parsed: dict
# ):
#     """
#     Returns:
#         embedding_text,
#         embedding_vector
#     """

#     embedding_text = build_job_text(
#         job,
#         parsed
#     )

#     embedding = _embed(embedding_text)

#     return embedding_text, embedding

"""
embeddings.py

Uses Jina AI (jina-embeddings-v3) instead of Gemini for embeddings.

IMPORTANT: function signatures (generate_resume_embedding,
generate_job_embedding) are UNCHANGED from the Gemini version - every
other file that calls these (jobs_tidb_storage.py, resume_text_tidb_storage.py)
needs NO changes.

Jina's task-aware embeddings are used correctly here: job postings
are embedded as "retrieval.passage" (the searchable corpus), resumes
as "retrieval.query" (what searches against that corpus) - this
matches how vector_search.py actually uses them (resume embedding
searches against stored job embeddings).

DIMENSION: 1024 (Jina v3's practical default). This is DIFFERENT from
Gemini's 3072 - jobs.embedding and resumes.embedding columns must be
resized (see sql/migrate_to_jina_and_groq.sql), and old Gemini-based
embeddings are unusable (different vector space, not just dimension).

Rate limits (Jina free tier): 100 RPM, 100,000 TPM, max 2 concurrent,
10M lifetime token trial pool (not a daily reset - it's a one-time
pool). Pacing here keeps calls safely under 100 RPM; there's no
attempt to track the lifetime pool precisely (no reliable way to
query remaining balance from this API) - monitor usage via your Jina
dashboard periodically instead.
"""

import os
import time
from typing import List

import requests
from dotenv import load_dotenv

load_dotenv()

JINA_API_KEY = os.getenv("JINA_API_KEY")
JINA_URL = "https://api.jina.ai/v1/embeddings"
JINA_MODEL = "jina-embeddings-v3"
JINA_DIMENSIONS = 1024

MIN_SECONDS_BETWEEN_CALLS = 0.7  # keeps us safely under Jina's 100 RPM

_last_call_time = 0.0


def _throttle():
    global _last_call_time
    elapsed = time.time() - _last_call_time
    if elapsed < MIN_SECONDS_BETWEEN_CALLS:
        time.sleep(MIN_SECONDS_BETWEEN_CALLS - elapsed)
    _last_call_time = time.time()


def _embed(text: str, task: str) -> List[float]:
    """
    Generate a single embedding using Jina. task is either
    "retrieval.passage" (for documents being searched, i.e. jobs) or
    "retrieval.query" (for the search input, i.e. a resume).
    """
    if not text or not text.strip():
        raise ValueError("Embedding text cannot be empty.")

    _throttle()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {JINA_API_KEY}",
    }
    payload = {
        "input": [text],
        "model": JINA_MODEL,
        "dimensions": JINA_DIMENSIONS,
        "task": task,
    }

    response = requests.post(JINA_URL, headers=headers, json=payload, timeout=30)
    response.raise_for_status()

    return response.json()["data"][0]["embedding"]


def build_resume_text(resume: dict, search_queries: list[str]) -> str:
    """
    Convert parsed resume JSON into semantic text for embedding.
    """
    sections = []

    if resume.get("summary"):
        sections.append(f"Summary: {resume['summary']}")

    skills = resume.get("skills", {})
    for category, values in skills.items():
        if values:
            sections.append(f"{category}: {', '.join(values)}")

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
Percentage: {edu.get("percentage", "")}
Year: {edu.get("year", "")}
"""
            )

    if resume.get("certifications"):
        print(type(resume["certifications"]))
        print(resume["certifications"])
        sections.append("Certifications: " + ", ".join(resume["certifications"]))

    if resume.get("achievements"):
        sections.append("Achievements: " + ", ".join(resume["achievements"]))

    if resume.get("languages"):
        sections.append("Languages: " + ", ".join(resume["languages"]))

    if resume.get("domains"):
        sections.append("Domains: " + ", ".join(resume["domains"]))

    if resume.get("keywords"):
        sections.append("Keywords: " + ", ".join(resume["keywords"]))

    if search_queries:
        sections.append("Suggested Roles: " + ", ".join(search_queries))

    return "\n".join(sections)


def build_job_text(job: dict, parsed: dict) -> str:
    """
    Convert parsed job JSON into semantic text for embedding.

    OPTIMIZED for retrieval quality vs. token cost - deliberately
    DROPS these fields from the embedding text (still stored in
    job_text/DB for display and scoring elsewhere, just not fed into
    the embedding):
        - preferred_skills: usually overlaps required_skills or adds
          noise without much discriminative retrieval value
        - responsibilities: often generic/boilerplate phrasing
          ("collaborate with cross-functional teams") that doesn't
          differentiate similar jobs well
        - soft_skills: nearly universal across all jobs (teamwork,
          communication) - low signal for job-to-resume matching

    tools and technologies are MERGED into one deduped section - they
    overlap heavily in practice, and splitting them into two labeled
    sections wastes tokens on formatting without adding signal.

    Estimated reduction vs. the previous version: ~35-40% fewer
    embedding tokens per job (rough estimate based on typical field
    sizes under the new FIELD_LIMITS in jd_parser.py - actual
    reduction varies with real content length).
    """
    sections = [f"Title: {job['title']}"]

    if job.get("company"):
        sections.append(f"Company: {job['company']}")

    if parsed.get("required_skills"):
        sections.append("Required Skills: " + ", ".join(parsed["required_skills"]))

    tech_and_tools = list(dict.fromkeys(
        (parsed.get("technologies") or []) + (parsed.get("tools") or [])
    ))
    if tech_and_tools:
        sections.append("Technologies: " + ", ".join(tech_and_tools))

    if parsed.get("experience_required"):
        sections.append(f"Experience: {parsed['experience_required']}")

    if parsed.get("education_required"):
        sections.append(f"Education: {parsed['education_required']}")

    if parsed.get("domains"):
        sections.append("Domains: " + ", ".join(parsed["domains"]))

    if parsed.get("keywords"):
        sections.append("Keywords: " + ", ".join(parsed["keywords"]))

    return "\n".join(sections)


def generate_resume_embedding(resume_json: dict, search_queries: list[str]):
    """
    Returns: embedding_text, embedding_vector
    Unchanged signature from the Gemini version.
    """
    embedding_text = build_resume_text(resume_json, search_queries)
    embedding = _embed(embedding_text, task="retrieval.query")
    return embedding_text, embedding


def generate_job_embedding(job: dict, parsed: dict):
    """
    Returns: embedding_text, embedding_vector
    Unchanged signature from the Gemini version.
    """
    embedding_text = build_job_text(job, parsed)
    embedding = _embed(embedding_text, task="retrieval.passage")
    return embedding_text, embedding