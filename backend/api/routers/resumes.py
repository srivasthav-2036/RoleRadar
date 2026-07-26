"""
resumes.py

Handles resume upload: PDF -> extract -> store. Requires login -
user_id comes from the verified JWT (get_current_user), never from
client input, so a user can only ever upload a resume for their own
account.

After storing the resume, a background thread runs recommendations
against the EXISTING jobs table only (no new job fetch), then emails
any matches found and logs activity events.

Pipeline status polling:
  GET /pipeline-status  -> {"status": "running"|"done", "step": str}
  The frontend polls this after upload to show live progress.
"""

import os
import tempfile
import threading
import time

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends

from backend.resume_extractor.resume_extract import extract_resume
from backend.resume_extractor.resume_text_tidb_storage import (
    store_resume,
    get_resume,
    delete_resume,
    has_uploaded_resume,
    update_resume,
)
from backend.auth.dependencies import get_current_user

router = APIRouter()

# ─── In-memory pipeline status (per user_id) ─────────────────────────────────
# Cleared when done. Simple dict — fine for single-process uvicorn.
# Shape: { user_id: {"status": "running"|"done", "step": str, "ts": float} }
_pipeline_status: dict = {}
_status_lock = threading.Lock()


def _set_status(user_id: str, status: str, step: str):
    with _status_lock:
        _pipeline_status[user_id] = {
            "status": status,
            "step": step,
            "ts": time.time(),
        }


def _clear_status(user_id: str):
    with _status_lock:
        _pipeline_status.pop(user_id, None)


def _post_upload_pipeline(user_id: str, email: str):
    """
    Background task: run recommendations from existing jobs only,
    send email if matches found, log activity events.
    Called in a daemon thread — failures are logged but never raised.
    Updates _pipeline_status so the frontend can poll progress.
    """
    try:
        from backend.recommender.recommender import generate_recommendations
        from backend.notifications.email_sender import send_new_jobs_email
        from backend.maintenance.pipeline_log import log_activity

        _set_status(user_id, "running", "Analyzing your resume\u2026")
        log_activity(user_id, "resume_analyzed")

        _set_status(user_id, "running", "Updating your profile\u2026")
        log_activity(user_id, "search_queries_generated")

        _set_status(user_id, "running", "Finding the best matches from our current job database\u2026")
        new_recs = generate_recommendations(user_id)

        _set_status(user_id, "running", "Ranking recommendations\u2026")

        if new_recs:
            log_activity(user_id, "recommendations_updated", {
                "count": len(new_recs),
                "source": "resume_upload",
            })

            from backend.users.users_storage import get_notification_preference
            if get_notification_preference(user_id):
                _set_status(user_id, "running", "Sending your recommendation email\u2026")

                matched_jobs = [
                    {
                        "job": {
                            "job_id": rec["job"].get("job_id", ""),
                            "title": rec["job"].get("title", ""),
                            "company": rec["job"].get("company", ""),
                        },
                        "score": rec.get("score", ""),
                    }
                    for rec in new_recs
                ]
                send_new_jobs_email(email, matched_jobs)
                log_activity(user_id, "email_sent", {"count": 1})

        _set_status(user_id, "done", "Done!")

        # Keep "done" status for 30 s so the frontend can read it, then clear
        time.sleep(30)
        _clear_status(user_id)

    except Exception as exc:
        print(f"[resumes] Post-upload pipeline error for {user_id}: {exc}")
        _set_status(user_id, "done", "Done!")
        time.sleep(30)
        _clear_status(user_id)


@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        resume_json, search_queries = extract_resume(tmp_path)

        # Upsert: update existing row if the user has uploaded before,
        # otherwise create a new one. This avoids duplicate rows on re-upload.
        if has_uploaded_resume(user_id):
            update_resume(user_id, resume_json, search_queries)
            resume_id = "updated"
        else:
            resume_id = store_resume(
                user_id=user_id,
                resume_json=resume_json,
                search_queries=search_queries,
            )
    finally:
        os.remove(tmp_path)

    # Fetch user email for notifications — best-effort, don't block upload
    try:
        from backend.users.users_storage import get_user_email
        user_email = get_user_email(user_id) or ""
    except Exception:
        user_email = ""

    # Mark pipeline as starting before the thread launches
    _set_status(user_id, "running", "Analyzing your resume\u2026")

    # Run recommendations + email in background (non-blocking)
    threading.Thread(
        target=_post_upload_pipeline,
        args=(user_id, user_email),
        daemon=True,
    ).start()

    return {
        "resume_id": resume_id,
        "resume": resume_json,
        "search_queries": search_queries,
    }


@router.get("/pipeline-status")
def get_pipeline_status(user_id: str = Depends(get_current_user)):
    """
    Returns the current background pipeline status for the authenticated user.
    Frontend polls this (every 2-3 s) after upload to show live progress.

    Response:
      {"status": "idle"}               -- no pipeline running
      {"status": "running", "step": "..."}
      {"status": "done",    "step": "Done!"}
    """
    with _status_lock:
        entry = _pipeline_status.get(user_id)

    if entry is None:
        return {"status": "idle"}

    return {"status": entry["status"], "step": entry["step"]}


@router.get("/me")
def get_my_resume(user_id: str = Depends(get_current_user)):
    """
    Returns the current user's latest resume (name, resume JSON, and
    search queries). Returns 404 if no resume has been uploaded yet.
    """
    data = get_resume(user_id)
    if data is None:
        raise HTTPException(status_code=404, detail="No resume found.")

    # Strip embedding from response -- not needed by the frontend
    return {
        "name": data.get("name"),
        "resume": data.get("resume"),
        "queries": data.get("queries"),
    }


@router.delete("/me")
def delete_my_resume(user_id: str = Depends(get_current_user)):
    """
    Deletes all resumes for the current user. This also means
    recommendations can no longer be refreshed until a new resume
    is uploaded.
    """
    delete_resume(user_id)
    return {"deleted": True}