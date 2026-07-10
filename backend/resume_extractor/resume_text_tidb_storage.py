import json
import uuid

from sqlalchemy import text

from backend.database.config import engine


def store_resume(user_id: str, resume_json: dict, search_queries: list) -> str:
    """
    Store a user's extracted resume and generated search queries.
    """

    resume_id = str(uuid.uuid4())

    query = text("""
        INSERT INTO resumes (
            id,
            user_id,
            resume_data,
            search_queries
        )
        VALUES (
            :id,
            :user_id,
            :resume_data,
            :search_queries
        )
    """)

    with engine.begin() as conn:
        conn.execute(
            query,
            {
                "id": resume_id,
                "user_id": user_id,
                "resume_data": json.dumps(resume_json),
                "search_queries": json.dumps(search_queries),
            },
        )

    return resume_id


def get_resume(user_id: str):
    """
    Get the latest resume for a user.
    """

    query = text("""
        SELECT
            resume_data,
            search_queries
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
        "resume": json.loads(row.resume_data),
        "queries": json.loads(row.search_queries)
    }


def update_resume(user_id: str, resume_json: dict, search_queries: list):
    """
    Update the latest resume for a user.
    """

    query = text("""
        UPDATE resumes
        SET
            resume_data = :resume_data,
            search_queries = :search_queries
        WHERE user_id = :user_id
    """)

    with engine.begin() as conn:
        conn.execute(
            query,
            {
                "user_id": user_id,
                "resume_data": json.dumps(resume_json),
                "search_queries": json.dumps(search_queries),
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