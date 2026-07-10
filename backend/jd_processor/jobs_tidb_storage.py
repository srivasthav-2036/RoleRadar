import json

from sqlalchemy import text

from backend.database.config import engine
from backend.embedder.embeddings import generate_job_embedding


def job_exists(job_id: str, company: str, title: str) -> bool:
    """
    Returns True if the job already exists in TiDB.
    """
    query = text("""
        SELECT 1
        FROM jobs
        WHERE
            job_id = :job_id
            AND company = :company
            AND title = :title
        LIMIT 1
    """)

    with engine.connect() as conn:
        row = conn.execute(
            query,
            {
                "job_id": job_id,
                "company": company,
                "title": title,
            },
        ).fetchone()

    return row is not None


def store_job(job: dict, parsed: dict):
    """
    Store the job. Only job_id, title, company are kept as separate
    columns (job_id is NOT a primary key - dupes across providers are
    expected and handled by job_exists before this is ever called).

    Everything else - raw job fields (location, description,
    apply_url, source, posted_at) and Gemini-parsed fields
    (required_skills, preferred_skills, etc.) - is bundled into a
    single job_text JSON column instead of separate columns.

    embedding_text / embedding stay as their own columns since
    embedding has to remain a proper VECTOR type for similarity search.
    """
    embedding_text, embedding = generate_job_embedding(job, parsed)

    job_text = {
        "location": job.get("location"),
        "description": job.get("description"),
        "apply_url": job.get("apply_url"),
        "source": job.get("source"),
        "posted_at": job.get("posted_at"),

        "required_skills": parsed["required_skills"],
        "preferred_skills": parsed["preferred_skills"],
        "experience_required": parsed["experience_required"],
        "education_required": parsed["education_required"],
        "responsibilities": parsed["responsibilities"],
        "job_level": parsed["job_level"],
        "employment_type": parsed["employment_type"],
        "tools": parsed["tools"],
        "technologies": parsed["technologies"],
        "keywords": parsed["keywords"],
        "soft_skills": parsed["soft_skills"],
        "domains": parsed["domains"],
    }

    query = text("""
        INSERT INTO jobs (
            job_id,
            title,
            company,
            job_text,
            embedding_text,
            embedding
        )
        VALUES (
            :job_id,
            :title,
            :company,
            :job_text,
            :embedding_text,
            CAST(:embedding AS VECTOR)
        )
    """)

    with engine.begin() as conn:
        conn.execute(
            query,
            {
                "job_id": job["id"],
                "title": job["title"],
                "company": job["company"],
                "job_text": json.dumps(job_text),
                "embedding_text": embedding_text,
                "embedding": json.dumps(embedding),
            },
        )