"""
dashboard.py

Three endpoints backing the dashboard's stat cards, activity
timeline, and skill galaxy:

    GET /stats            -> DashboardStats (8 values for stat cards)
    GET /activity         -> ActivityTimeline events (most-recent-first)
    GET /skill-frequency  -> SkillFrequency list (for Skill Galaxy)

All three require login. Values are computed from real DB state - no
hardcoded numbers, no frontend-side calculations.
"""

from fastapi import APIRouter, Depends

from backend.recommender.recommendation_storage import (
    get_new_matches_today,
    get_average_match_score,
    get_skill_frequency,
)
from backend.resume_extractor.resume_text_tidb_storage import get_resume_strength
from backend.maintenance.pipeline_log import (
    get_last_pipeline_run,
    get_activity_timeline,
    get_emails_sent_count,
)
from backend.jd_processor.jobs_tidb_storage import get_total_jobs_count
from backend.auth.dependencies import get_current_user

router = APIRouter()


@router.get("/stats")
def dashboard_stats(user_id: str = Depends(get_current_user)):
    """
    Powers all 8 stat cards on the dashboard. Every value comes
    from the DB — the frontend never fabricates any of these.
    Returns null (not 0) for metrics that have no data yet so the
    frontend can show '-' instead of a misleading zero.
    """
    last_run = get_last_pipeline_run()

    last_sync_str = None
    if last_run and last_run.get("finished_at"):
        finished_at = last_run["finished_at"]
        last_sync_str = finished_at.isoformat() + "Z" if finished_at.tzinfo is None else finished_at.isoformat()

    next_sync_str = None
    if last_run and last_run.get("next_scheduled_at"):
        next_scheduled_at = last_run["next_scheduled_at"]
        next_sync_str = next_scheduled_at.isoformat() + "Z" if next_scheduled_at.tzinfo is None else next_scheduled_at.isoformat()

    return {
        "new_matches_today": get_new_matches_today(user_id),
        "avg_match_score": get_average_match_score(user_id),
        "resume_strength": get_resume_strength(user_id),
        "applications_this_week": None,  # Not tracked yet — reserved field
        "emails_sent": get_emails_sent_count(user_id),
        "jobs_fetched_today": get_total_jobs_count(),
        "last_sync": last_sync_str,
        "next_sync": next_sync_str,
    }


@router.get("/activity")
def dashboard_activity(
    user_id: str = Depends(get_current_user),
    limit: int = 20,
):
    """
    Returns the user's pipeline activity events, most recent first.
    Powers the Activity Timeline component.
    """
    events = get_activity_timeline(user_id, limit=limit)

    serialized = []
    for event in events:
        created_at = event["created_at"]
        created_at_str = str(created_at)
        if hasattr(created_at, "isoformat"):
            created_at_str = created_at.isoformat() + "Z" if created_at.tzinfo is None else created_at.isoformat()
        
        serialized.append({
            "event_type": event["event_type"],
            "detail": event["detail"],
            "created_at": created_at_str,
        })

    return {"events": serialized}


@router.get("/skill-frequency")
def dashboard_skill_frequency(user_id: str = Depends(get_current_user)):
    """
    Powers the Skill Galaxy and Resume Insights Panel.
    Returns skills sorted by frequency (how many of the user's
    recommended jobs matched on each skill).
    """
    skills = get_skill_frequency(user_id)
    return {"skills": skills}
