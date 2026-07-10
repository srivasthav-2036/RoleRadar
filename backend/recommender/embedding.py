import os
from typing import List

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY_FOR_EMBEDDING")
)

# Use the latest Gemini embedding model available in the API.
# Keeping it in one place makes future upgrades easy.
EMBEDDING_MODEL = "gemini-embedding-001"


def generate_embedding(text: str) -> List[float]:
    """
    Generates a semantic embedding for the given text.

    Args:
        text: Input text.

    Returns:
        List[float]: Embedding vector.
    """

    if not text or not text.strip():
        raise ValueError("Cannot generate embedding for empty text.")

    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT"
        ),
    )

    return response.embeddings[0].values


def build_resume_embedding_text(profile: dict) -> str:
    """
    Converts parsed resume JSON into optimized text for embedding.
    """

    sections = []

    if profile.get("target_roles"):
        sections.append(
            "Target Roles: " +
            ", ".join(profile["target_roles"])
        )

    if profile.get("skills"):
        sections.append(
            "Skills: " +
            ", ".join(profile["skills"])
        )

    if profile.get("experience"):
        sections.append(
            "Experience: " +
            str(profile["experience"])
        )

    if profile.get("projects"):
        projects = []

        for project in profile["projects"]:
            if isinstance(project, dict):
                title = project.get("title", "")
                tech = ", ".join(project.get("technologies", []))
                projects.append(f"{title} ({tech})")
            else:
                projects.append(str(project))

        sections.append(
            "Projects: " +
            "; ".join(projects)
        )

    if profile.get("education"):
        sections.append(
            "Education: " +
            str(profile["education"])
        )

    if profile.get("certificates"):
        sections.append(
            "Certificates: " +
            ", ".join(profile["certificates"])
        )

    return "\n".join(sections)


def build_job_embedding_text(profile: dict) -> str:
    """
    Converts parsed job JSON into optimized text for embedding.
    """

    sections = []

    if profile.get("job_title"):
        sections.append(
            "Role: " + profile["job_title"]
        )

    if profile.get("required_skills"):
        sections.append(
            "Required Skills: " +
            ", ".join(profile["required_skills"])
        )

    if profile.get("preferred_skills"):
        sections.append(
            "Preferred Skills: " +
            ", ".join(profile["preferred_skills"])
        )

    if profile.get("experience"):
        sections.append(
            "Experience: " +
            str(profile["experience"])
        )

    if profile.get("education"):
        sections.append(
            "Education: " +
            str(profile["education"])
        )

    if profile.get("certifications"):
        sections.append(
            "Certifications: " +
            ", ".join(profile["certifications"])
        )

    return "\n".join(sections)