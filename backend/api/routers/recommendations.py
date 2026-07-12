"""
recommendations.py

Two separate endpoints:
    GET  /              -> read already-computed recommendations
                            (fast, no Gemini calls, what a "my
                            recommendations" page should use)
    POST /refresh        -> trigger a live run (vector search + Gemini
                            matching for anything genuinely new since
                            last check) - use sparingly, e.g. a
                            "Check for new matches" button, not on
                            every page load

Both require login. Both check that the user has uploaded a resume
first and return a clear message if not, instead of a confusing
error.
"""

from fastapi import APIRouter, HTTPException, Depends

from backend.recommender.recommender import generate_recommendations
from backend.recommender.recommendation_storage import get_stored_recommendations
from backend.resume_extractor.resume_text_tidb_storage import has_uploaded_resume
from backend.auth.dependencies import get_current_user

router = APIRouter()


def _require_resume(user_id: str):
    if not has_uploaded_resume(user_id):
        raise HTTPException(
            status_code=400,
            detail="Please upload a resume before viewing recommendations.",
        )


@router.get("/")
def list_recommendations(user_id: str = Depends(get_current_user)):
    _require_resume(user_id)

    recommendations = get_stored_recommendations(user_id)

    return {
        "count": len(recommendations),
        "recommendations": recommendations,
    }


@router.post("/refresh")
def refresh_recommendations(user_id: str = Depends(get_current_user)):
    _require_resume(user_id)

    try:
        new_recommendations = generate_recommendations(user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "new_count": len(new_recommendations),
        "new_recommendations": [
            {
                "job_id": rec["job"]["job_id"],
                "title": rec["job"]["title"],
                "company": rec["job"]["company"],
                "score": rec["score"],
                "overall_match": rec["match"].get("overall_match"),
                "recommendation": rec["match"].get("recommendation"),
            }
            for rec in new_recommendations
        ],
    }