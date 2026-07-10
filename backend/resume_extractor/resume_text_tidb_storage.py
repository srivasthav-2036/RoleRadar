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


def update_resume(user_id: str, resume_json: dict, search_queries: list):
    """
    Update the latest resume for a user.
    """
    embedding_text, embedding = generate_resume_embedding(
        resume_json,
        search_queries
        )
    name = resume_json.get("name", "")
    query = text("""
        UPDATE resumes
        SET
            name = :name,
            resume_data = :resume_data,
            search_queries = :search_queries,
            embedding_text = :embedding_text,
            embedding = CAST(:embedding AS VECTOR)
        WHERE user_id = :user_id
    """)

    with engine.begin() as conn:
        conn.execute(
            query,
            {
                "user_id": user_id,
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

    # Dummy data for testing
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