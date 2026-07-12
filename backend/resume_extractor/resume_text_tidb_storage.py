import json
import uuid

from sqlalchemy import text

from backend.database.config import engine
from backend.embedder.embeddings import generate_resume_embedding


def store_resume(user_id: str, resume_json: dict, search_queries: list) -> str:
    """
    Store a user's extracted resume and generated search queries.
    """

    resume_id = str(uuid.uuid4())
    embedding_text, embedding = generate_resume_embedding(
        resume_json,
        search_queries
    )
    name = resume_json.get("name", "")
    query = text("""
    INSERT INTO resumes (
        id,
        user_id,
        name,
        resume_data,
        search_queries,
        embedding_text,
        embedding
    )
    VALUES (
        :id,
        :user_id,
        :name,
        :resume_data,
        :search_queries,
        :embedding_text,
        CAST(:embedding AS VECTOR)
    )
    """)

    with engine.begin() as conn:
        conn.execute(
            query,
            {
                "id": resume_id,
                "user_id": user_id,
                "name": name,

                "resume_data": json.dumps(resume_json),
                "search_queries": json.dumps(search_queries),

                "embedding_text": embedding_text,
                "embedding": json.dumps(embedding),
            },
        )

    return resume_id


def _maybe_json_loads(value):
    """
    JSON columns may come back as already-parsed Python objects or
    as raw strings depending on the driver - handle both rather
    than assuming.
    """
    if isinstance(value, (str, bytes)):
        return json.loads(value)
    return value


def get_resume(user_id: str):
    """
    Get the latest resume for a user.
    """

    query = text("""
        SELECT
            name,
            resume_data,
            search_queries,
            embedding

        FROM resumes
        WHERE user_id = :user_id
        ORDER BY created_at DESC
        LIMIT 1
    """)

    with engine.connect() as conn:
        row = conn.execute(query, {"user_id": user_id}).fetchone()

    if row is None:
        return None

    return {
        "name": row.name,
        "resume": _maybe_json_loads(row.resume_data),
        "queries": _maybe_json_loads(row.search_queries),
        "embedding": _maybe_json_loads(row.embedding),
    }


def get_all_user_ids() -> list[str]:
    """
    Returns every distinct user_id (== email address) that has
    uploaded at least one resume.
    """
    query = text("SELECT DISTINCT user_id FROM resumes")

    with engine.connect() as conn:
        rows = conn.execute(query).fetchall()

    return [row[0] for row in rows]

def get_all_users() -> list:
    """
    Returns [{"user_id": ..., "email": ...}, ...] for every user who
    has uploaded at least one resume.
    """
    query = text("""
        SELECT DISTINCT r.user_id, u.email
        FROM resumes r
        JOIN users u ON u.user_id = r.user_id
    """)

    with engine.connect() as conn:
        rows = conn.execute(query).fetchall()

    return [{"user_id": row.user_id, "email": row.email} for row in rows]


def has_uploaded_resume(user_id: str) -> bool:
    """
    Quick existence check - used by recommendations/tailoring
    endpoints to tell a logged-in user "please upload a resume first"
    instead of a confusing error.
    """
    query = text("SELECT 1 FROM resumes WHERE user_id = :user_id LIMIT 1")

    with engine.connect() as conn:
        row = conn.execute(query, {"user_id": user_id}).fetchone()

    return row is not None

def get_all_search_queries() -> list[str]:
    """
    Returns every distinct search query across ALL users' resumes
    (all versions, not just latest), deduplicated. Used by the
    scheduled pipeline to know which roles to search job providers
    for, instead of a hardcoded list.
    """
    query = text("SELECT search_queries FROM resumes")
 
    with engine.connect() as conn:
        rows = conn.execute(query).fetchall()
 
    unique_queries = set()
 
    for row in rows:
        queries = _maybe_json_loads(row[0]) or []
        for q in queries:
            if q and q.strip():
                unique_queries.add(q.strip())
 
    return list(unique_queries)

def update_search_queries(user_id: str, new_queries: list[str]):
    """
    Replaces (not appends) the preferred-roles search_queries on a
    user's most recent resume row. Used both for first-time
    confirmation of the Gemini-suggested roles and for later edits -
    either way, this overwrites whatever was there before.
    """
    with engine.begin() as conn:

        latest = conn.execute(
            text("""
                SELECT id FROM resumes
                WHERE user_id = :user_id
                ORDER BY created_at DESC
                LIMIT 1
            """),
            {"user_id": user_id},
        ).fetchone()

        if latest is None:
            raise ValueError(f"No resume found for user_id={user_id}")

        conn.execute(
            text("""
                UPDATE resumes
                SET search_queries = :search_queries
                WHERE id = :id
            """),
            {
                "search_queries": json.dumps(new_queries),
                "id": latest.id,
            },
        )


def update_resume(user_id: str, resume_json: dict, search_queries: list):
    """
    Update the LATEST resume for a user (not all of their resume
    rows). Scoped to the specific resume id, the same pattern as
    update_search_queries - a user can have multiple resume versions
    (get_resume() always reads the most recent one), so updating by
    user_id alone would overwrite every version with identical
    content and destroy their resume history.
    """
    embedding_text, embedding = generate_resume_embedding(
        resume_json,
        search_queries
    )
    name = resume_json.get("name", "")

    with engine.begin() as conn:

        latest = conn.execute(
            text("""
                SELECT id FROM resumes
                WHERE user_id = :user_id
                ORDER BY created_at DESC
                LIMIT 1
            """),
            {"user_id": user_id},
        ).fetchone()

        if latest is None:
            raise ValueError(f"No resume found for user_id={user_id}")

        conn.execute(
            text("""
                UPDATE resumes
                SET
                    name = :name,
                    resume_data = :resume_data,
                    search_queries = :search_queries,
                    embedding_text = :embedding_text,
                    embedding = CAST(:embedding AS VECTOR)
                WHERE id = :id
            """),
            {
                "id": latest.id,
                "name": name,
                "resume_data": json.dumps(resume_json),
                "search_queries": json.dumps(search_queries),
                "embedding_text": embedding_text,
                "embedding": json.dumps(embedding),
            },
        )


def delete_resume(user_id: str):
    """
    Delete all resumes for a user.
    """

    query = text("""
        DELETE FROM resumes
        WHERE user_id = :user_id
    """)

    with engine.begin() as conn:
        conn.execute(query, {"user_id": user_id})


if __name__ == "__main__":

    resume_json = {
        "summary": "AI & ML Student",
        "skills": {
            "programming": ["Python", "C++"],
            "frameworks": ["FastAPI", "Flask"],
            "libraries": ["pandas"],
            "databases": ["TiDB"]
        },
        "experience": [],
        "projects": [
            {
                "title": "RoleRadar",
                "description": "AI Job Recommendation Platform",
                "technologies": ["FastAPI", "Gemini", "TiDB"],
                "domain": "AI"
            }
        ],
        "education": [],
        "certifications": [],
        "achievements": [],
        "languages": ["English"],
        "preferred_roles": ["Backend Developer"],
        "domains": ["AI"],
        "keywords": ["Python", "FastAPI"]
    }

    search_queries = [
        "Python Developer",
        "Backend Developer",
        "FastAPI Developer"
    ]

    USER_ID = "test_user"

    # uncomment to test store and get
    # print("Storing resume...")
    # resume_id = store_resume(USER_ID, resume_json, search_queries)
    # print(f"Stored Resume ID: {resume_id}")

    # print("\nFetching resume...")
    # data = get_resume(USER_ID)
    # print(data)

    # Uncomment to test update
    # resume_json["summary"] = "Updated Summary"
    # update_resume(USER_ID, resume_json, search_queries)
    # print(get_resume(USER_ID))

    # Uncomment to test delete
    delete_resume(USER_ID)
    print(get_resume(USER_ID))