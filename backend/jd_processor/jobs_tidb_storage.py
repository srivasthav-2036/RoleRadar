import json

from sqlalchemy import text

from backend.database.config import engine


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
    Store the original job and its parsed data.
    """

    query = text("""
        INSERT INTO jobs (
            job_id,
            title,
            company,
            location,
            description,
            url,
            provider,
            posted_date,

            required_skills,
            preferred_skills,
            experience_required,
            education_required,
            responsibilities,
            job_level,
            employment_type,
            tools,
            technologies,
            keywords,
            soft_skills,
            domains
        )
        VALUES (
            :job_id,
            :title,
            :company,
            :location,
            :description,
            :url,
            :provider,
            :posted_date,

            :required_skills,
            :preferred_skills,
            :experience_required,
            :education_required,
            :responsibilities,
            :job_level,
            :employment_type,
            :tools,
            :technologies,
            :keywords,
            :soft_skills,
            :domains
        )
    """)

    with engine.begin() as conn:
        conn.execute(
            query,
            {
                "job_id": job["job_id"],
                "title": job["title"],
                "company": job["company"],
                "location": job.get("location"),
                "description": job.get("description"),
                "url": job.get("url"),
                "provider": job.get("provider"),
                "posted_date": job.get("posted_at"),

                "required_skills": json.dumps(parsed["required_skills"]),
                "preferred_skills": json.dumps(parsed["preferred_skills"]),
                "experience_required": parsed["experience_required"],
                "education_required": parsed["education_required"],
                "responsibilities": json.dumps(parsed["responsibilities"]),
                "job_level": parsed["job_level"],
                "employment_type": parsed["employment_type"],
                "tools": json.dumps(parsed["tools"]),
                "technologies": json.dumps(parsed["technologies"]),
                "keywords": json.dumps(parsed["keywords"]),
                "soft_skills": json.dumps(parsed["soft_skills"]),
                "domains": json.dumps(parsed["domains"]),
            },
        )