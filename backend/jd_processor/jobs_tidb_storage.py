# import json

# from sqlalchemy import text

# from backend.database.config import engine
# from backend.embedder.embeddings import generate_job_embedding


# def job_exists(job_id: str, company: str, title: str) -> bool:
#     """
#     Returns True if the job already exists in TiDB.
#     """
#     query = text("""
#         SELECT 1
#         FROM jobs
#         WHERE
#             job_id = :job_id
#             AND company = :company
#             AND title = :title
#         LIMIT 1
#     """)

#     with engine.connect() as conn:
#         row = conn.execute(
#             query,
#             {
#                 "job_id": job_id,
#                 "company": company,
#                 "title": title,
#             },
#         ).fetchone()

#     return row is not None


# def store_job(job: dict, parsed: dict):
#     """
#     Store the job. Only job_id, title, company are kept as separate
#     columns (job_id is NOT a primary key - dupes across providers are
#     expected and handled by job_exists before this is ever called).

#     Everything else - raw job fields (location, description,
#     apply_url, source, posted_at) and Gemini-parsed fields
#     (required_skills, preferred_skills, etc.) - is bundled into a
#     single job_text JSON column instead of separate columns.

#     embedding_text / embedding stay as their own columns since
#     embedding has to remain a proper VECTOR type for similarity search.
#     """
#     embedding_text, embedding = generate_job_embedding(job, parsed)

#     job_text = {
#         "location": job.get("location"),
#         "description": job.get("description"),
#         "apply_url": job.get("apply_url"),
#         "source": job.get("source"),
#         "posted_at": job.get("posted_at"),

#         "required_skills": parsed["required_skills"],
#         "preferred_skills": parsed["preferred_skills"],
#         "experience_required": parsed["experience_required"],
#         "education_required": parsed["education_required"],
#         "responsibilities": parsed["responsibilities"],
#         "job_level": parsed["job_level"],
#         "employment_type": parsed["employment_type"],
#         "tools": parsed["tools"],
#         "technologies": parsed["technologies"],
#         "keywords": parsed["keywords"],
#         "soft_skills": parsed["soft_skills"],
#         "domains": parsed["domains"],
#     }

#     query = text("""
#         INSERT INTO jobs (
#             job_id,
#             title,
#             company,
#             job_text,
#             embedding_text,
#             embedding
#         )
#         VALUES (
#             :job_id,
#             :title,
#             :company,
#             :job_text,
#             :embedding_text,
#             CAST(:embedding AS VECTOR)
#         )
#     """)

#     with engine.begin() as conn:
#         conn.execute(
#             query,
#             {
#                 "job_id": job["id"],
#                 "title": job["title"],
#                 "company": job["company"],
#                 "job_text": json.dumps(job_text),
#                 "embedding_text": embedding_text,
#                 "embedding": json.dumps(embedding),
#             },
#         )

"""
jobs_tidb_storage.py

Replaces the old store_job() (which only ran AFTER successful
parsing) with three functions matching the new insert-immediately,
parse-later queue design:

    - job_exists()      unchanged - dedup check at fetch time
    - insert_raw_job()   NEW - inserts a job the moment it's fetched,
                         BEFORE parsing, with parsed=false
    - get_unparsed_jobs() NEW - FIFO read of the parsing queue
    - mark_job_parsed()  NEW - merges parsed fields + embedding into
                         the existing row, sets parsed=true

job_text keeps its EXISTING flat shape (required_skills, technologies,
etc. all top-level keys) - unchanged from before, so vector_search.py
and fetch_context.py need NO changes. The only difference is WHEN
those keys get populated: at insert time job_text has just the raw
fetched fields (location, description, apply_url, source, posted_at);
mark_job_parsed() merges the parsed fields in later via a
read-modify-write.

Uses `id` (the real auto-increment PRIMARY KEY) to target rows for
updates, NOT job_id - job_id is not unique (duplicate postings across
providers are expected), so it's not safe to use for UPDATE/WHERE
targeting a single row.
"""

import json

from sqlalchemy import text

from backend.database.config import engine


def job_exists(job_id: str, company: str, title: str) -> bool:
    """
    Returns True if this job already has a row in the DB (regardless
    of parsed status) - dedup check at fetch time.
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
            {"job_id": job_id, "company": company, "title": title},
        ).fetchone()

    return row is not None


def insert_raw_job(job: dict) -> None:
    """
    Inserts a job IMMEDIATELY on fetch, before any parsing. job_text
    holds only the raw fetched fields at this point; parsed=false;
    embedding=NULL until mark_job_parsed() runs later.
    """
    raw_job_text = {
        "location": job.get("location"),
        "description": job.get("description"),
        "apply_url": job.get("apply_url"),
        "source": job.get("source"),
        "posted_at": job.get("posted_at"),
    }

    query = text("""
        INSERT INTO jobs (job_id, title, company, job_text, parsed)
        VALUES (:job_id, :title, :company, :job_text, FALSE)
    """)

    with engine.begin() as conn:
        conn.execute(
            query,
            {
                "job_id": job["id"],
                "title": job["title"],
                "company": job["company"],
                "job_text": json.dumps(raw_job_text),
            },
        )


def get_unparsed_jobs(limit: int) -> list[dict]:
    """
    FIFO read: oldest unparsed jobs first (by created_at - jobs left
    over from earlier runs always come before jobs just inserted this
    run). Returns each row's real `id` (PK) - callers MUST pass this
    (not job_id) to mark_job_parsed().
    """
    query = text("""
        SELECT id, job_id, title, company, job_text
        FROM jobs
        WHERE parsed = FALSE
        ORDER BY created_at ASC
        LIMIT :limit
    """)

    with engine.connect() as conn:
        rows = conn.execute(query, {"limit": limit}).fetchall()

    results = []
    for row in rows:
        job_text = row.job_text
        if isinstance(job_text, (str, bytes)):
            job_text = json.loads(job_text)
        job_text = job_text or {}

        results.append({
            "row_id": row.id,
            "job_id": row.job_id,
            "title": row.title,
            "company": row.company,
            "description": job_text.get("description"),
        })

    return results


def mark_job_parsed(row_id: int, parsed: dict, embedding_text: str, embedding: list) -> None:
    """
    Merges parsed fields into the existing job_text (keeping the raw
    fields already there via a read-modify-write, not overwriting
    them), stores the embedding, and sets parsed=true.
    """
    with engine.begin() as conn:
        row = conn.execute(
            text("SELECT job_text FROM jobs WHERE id = :id"),
            {"id": row_id},
        ).fetchone()

        if row is None:
            raise ValueError(f"No job found with id={row_id}")

        job_text = row.job_text
        if isinstance(job_text, (str, bytes)):
            job_text = json.loads(job_text)
        job_text = job_text or {}

        job_text.update({
            "required_skills": parsed.get("required_skills", []),
            "preferred_skills": parsed.get("preferred_skills", []),
            "experience_required": parsed.get("experience_required"),
            "education_required": parsed.get("education_required"),
            "responsibilities": parsed.get("responsibilities", []),
            "job_level": parsed.get("job_level"),
            "employment_type": parsed.get("employment_type"),
            "tools": parsed.get("tools", []),
            "technologies": parsed.get("technologies", []),
            "keywords": parsed.get("keywords", []),
            "soft_skills": parsed.get("soft_skills", []),
            "domains": parsed.get("domains", []),
        })

        conn.execute(
            text("""
                UPDATE jobs
                SET
                    job_text = :job_text,
                    embedding_text = :embedding_text,
                    embedding = CAST(:embedding AS VECTOR),
                    parsed = TRUE
                WHERE id = :id
            """),
            {
                "id": row_id,
                "job_text": json.dumps(job_text),
                "embedding_text": embedding_text,
                "embedding": json.dumps(embedding),
            },
        )