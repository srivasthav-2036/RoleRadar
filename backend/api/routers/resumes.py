"""
resumes.py

Handles resume upload: PDF -> extract -> store. Requires login -
user_id comes from the verified JWT (get_current_user), never from
client input, so a user can only ever upload a resume for their own
account.
"""

import os
import tempfile

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends

from backend.resume_extractor.resume_extract import extract_resume
from backend.resume_extractor.resume_text_tidb_storage import store_resume
from backend.auth.dependencies import get_current_user

router = APIRouter()


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

        resume_id = store_resume(
            user_id=user_id,
            # name=resume_json.get("name"),
            resume_json=resume_json,
            search_queries=search_queries,
        )
    finally:
        os.remove(tmp_path)

    return {
        "resume_id": resume_id,
        "resume": resume_json,
        "search_queries": search_queries,
    }