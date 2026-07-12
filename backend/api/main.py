"""
main.py

FastAPI entry point. Run locally with:
    uvicorn api.main:app --reload

(run from inside backend/, same working directory as
maintenance/scheduled_run.py)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routers import auth, resumes, recommendations, tailoring

app = FastAPI(title="RoleRadar API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this to your actual frontend domain before going live
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(resumes.router, prefix="/api/resumes", tags=["resumes"])
app.include_router(recommendations.router, prefix="/api/recommendations", tags=["recommendations"])
app.include_router(tailoring.router, prefix="/api/tailoring", tags=["tailoring"])


@app.get("/")
def health_check():
    return {"status": "ok"}