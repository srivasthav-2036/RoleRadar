"""
tailoring.py

Two-step flow:
    1. GET  /preview/{job_id} -> editable tailored resume JSON
       (cached - instant if the scheduled pipeline already
       pre-generated it, otherwise generates once and caches it)
    2. POST /pdf (with possibly user-edited JSON) -> downloadable PDF

Requires login - job_id is checked against THIS user's own
recommendations (get_or_generate_tailored_resume enforces this), so
a user can't request a tailored resume for a job that was never
recommended to them.
"""

import os
import uuid

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from backend.resume_tailoring.pdf_generator import render_resume_html  # add to existing import line

from backend.resume_tailoring.tailor_resume import get_or_generate_tailored_resume
from backend.resume_tailoring.pdf_generator import generate_resume_pdf
from backend.auth.dependencies import get_current_user

router = APIRouter()

OUTPUT_DIR = "/tmp/roleradar_resumes"
os.makedirs(OUTPUT_DIR, exist_ok=True)


@router.get("/preview/{job_id}")
def tailor_preview(job_id: str, user_id: str = Depends(get_current_user)):
    try:
        tailored_resume = get_or_generate_tailored_resume(user_id=user_id, job_id=job_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {"tailored_resume": tailored_resume}


class TailoredResumePayload(BaseModel):
    tailored_resume: dict


@router.post("/pdf")
def tailor_pdf(
    payload: TailoredResumePayload,
    user_id: str = Depends(get_current_user),
):
    """
    Takes the (possibly user-edited) tailored resume JSON from the
    preview step and renders it to a downloadable PDF. user_id isn't
    used here directly - it's required so this endpoint stays behind
    login - but the actual content comes from the client-submitted
    (edited) JSON, since editing happens client-side after preview.
    """
    filename = f"{uuid.uuid4()}.pdf"
    output_path = os.path.join(OUTPUT_DIR, filename)

    generate_resume_pdf(payload.tailored_resume, output_path)

    return FileResponse(
        output_path,
        media_type="application/pdf",
        filename="tailored_resume.pdf",
    )


@router.get("/preview/{job_id}/html", response_class=HTMLResponse)
def tailor_preview_html(job_id: str, user_id: str = Depends(get_current_user)):
    try:
        tailored_resume = get_or_generate_tailored_resume(user_id=user_id, job_id=job_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return HTMLResponse(content=render_resume_html(tailored_resume))