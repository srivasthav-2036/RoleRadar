import json

from sqlalchemy import text

from backend.database.config import engine


def search_similar_jobs(
    resume_embedding: list[float],
    top_k: int = 30,
    exclude_job_ids: list[str] | None = None,
):
    """
    Perform vector search in TiDB.

    Args:
        resume_embedding:
            Embedding generated from the user's resume.

        top_k:
            Number of similar jobs to retrieve.

        exclude_job_ids:
            Jobs that have already been recommended.
    """

    exclude_job_ids = exclude_job_ids or []

    params = {
        "embedding": json.dumps(resume_embedding),
        "limit": top_k,
    }

    if exclude_job_ids:

        placeholders = []

        for i, job_id in enumerate(exclude_job_ids):
            key = f"job_id_{i}"
            placeholders.append(f":{key}")
            params[key] = job_id

        sql = text(f"""
            SELECT

                job_id,
                title,
                company,
                job_text,

                VEC_COSINE_DISTANCE(
                    embedding,
                    CAST(:embedding AS VECTOR)
                ) AS distance


            FROM jobs

            WHERE embedding IS NOT NULL
            AND job_id NOT IN ({",".join(placeholders)})

            ORDER BY distance ASC

            LIMIT :limit
        """)

    else:

        sql = text("""
            SELECT

                job_id,
                title,
                company,
                job_text,

                VEC_COSINE_DISTANCE(
                    embedding,
                    CAST(:embedding AS VECTOR)
                ) AS distance

            FROM jobs

            WHERE embedding IS NOT NULL

            ORDER BY distance ASC

            LIMIT :limit
        """)

    with engine.connect() as conn:

        rows = conn.execute(sql, params).mappings().all()

    jobs = []

    for row in rows:

        # job_text is stored as JSON - may come back as a str
        # depending on driver/version, so handle both cases
        raw = row["job_text"]
        job_text = json.loads(raw) if isinstance(raw, str) else (raw or {})

        jobs.append({

            "job_id": row["job_id"],

            "title": row["title"],

            "company": row["company"],

            "location": job_text.get("location"),

            "description": job_text.get("description"),

            "url": job_text.get("apply_url"),

            "provider": job_text.get("source"),

            "posted_date": job_text.get("posted_at"),

            "parsed_job": {

                "required_skills": job_text.get("required_skills") or [],

                "preferred_skills": job_text.get("preferred_skills") or [],

                "experience_required": job_text.get("experience_required"),

                "education_required": job_text.get("education_required"),

                "responsibilities": job_text.get("responsibilities") or [],

                "job_level": job_text.get("job_level"),

                "employment_type": job_text.get("employment_type"),

                "tools": job_text.get("tools") or [],

                "technologies": job_text.get("technologies") or [],

                "keywords": job_text.get("keywords") or [],

                "soft_skills": job_text.get("soft_skills") or [],

                "domains": job_text.get("domains") or [],

            },

            "distance": row["distance"],

        })

    return jobs