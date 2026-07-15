from backend.similarity_engine.scoring import calculate_score
from backend.similarity_engine.matcher import semantic_match


def match_resume_to_job(
    resume_profile: dict,
    job_profile: dict,
    model: str = "gemini-2.5-flash",
) -> dict:
    """
    Matches a resume against a job profile.

    Steps:
    1. Perform semantic matching using Gemini.
    2. Compute deterministic score.
    3. Return final result.
    """

    try:
        # Step 1: Semantic Matching
        match_result = semantic_match(
            resume_profile=resume_profile,
            job_profile=job_profile,
            model=model,
        )

        # Step 2: Deterministic Scoring
        final_result = calculate_score(
            resume_profile=resume_profile,
            job_profile=job_profile,
            match_result=match_result,
        )
        print("Final Result:", final_result)
        return final_result

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }