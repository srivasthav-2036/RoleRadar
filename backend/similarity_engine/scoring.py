from typing import Dict


# ==========================================================
# WEIGHTS
# ==========================================================

WEIGHTS_EXPERIENCED = {
    "skills": 60,
    "projects": 15,
    "experience": 15,
    "education": 10,
}

WEIGHTS_FRESHER = {
    "skills": 60,
    "projects": 30,
    "education": 10,
}


# ==========================================================
# SCORE MAPS
# ==========================================================

PROJECT_SCORE = {
    "Excellent": 100,
    "High": 85,
    "Medium": 65,
    "Low": 40,
}

EXPERIENCE_SCORE = {
    "Strong": 100,
    "Moderate": 75,
    "Weak": 40,
}

EDUCATION_SCORE = {
    "Meets": 100,
    "Partially Meets": 70,
    "Does Not Meet": 30,
}

CERTIFICATE_BONUS = {
    "Strong": 5,
    "Moderate": 3,
    "Weak": 1,
    "None": 0,
}


# ==========================================================
# EXPERIENCE CHECK
# ==========================================================

def has_professional_experience(resume_profile: Dict) -> bool:
    experience = resume_profile.get("experience", [])

    if not experience:
        return False

    for exp in experience:
        if (
            exp.get("company", "").strip()
            or exp.get("role", "").strip()
            or exp.get("description", "").strip()
        ):
            return True

    return False


# ==========================================================
# SKILL SCORE
# ==========================================================

def calculate_skill_score(job_profile: Dict, match_result: Dict) -> float:

    required = {
        s.lower().strip()
        for s in job_profile.get("required_skills", [])
        if s.strip()
    }

    preferred = {
        s.lower().strip()
        for s in job_profile.get("preferred_skills", [])
        if s.strip()
    }

    matched_required = {
        s.lower().strip()
        for s in match_result.get("matched_required_skills", [])
    }

    matched_preferred = {
        s.lower().strip()
        for s in match_result.get("matched_preferred_skills", [])
    }

    if not required and not preferred:
        return 50

    if not required:
        return round(
            (len(preferred & matched_preferred) / len(preferred)) * 100,
            2,
        )

    required_score = (
        len(required & matched_required)
        / len(required)
    ) * 100

    if preferred:
        preferred_score = (
            len(preferred & matched_preferred)
            / len(preferred)
        ) * 100
    else:
        preferred_score = required_score

    return round(
        required_score * 0.8 +
        preferred_score * 0.2,
        2,
    )


# ==========================================================
# OVERALL MATCH
# ==========================================================

def get_overall_match(score: float):

    if score >= 90:
        return "Excellent Match"

    elif score >= 75:
        return "Good Match"

    elif score >= 60:
        return "Average Match"

    return "Weak Match"


# ==========================================================
# MAIN
# ==========================================================

def calculate_score(
    resume_profile: Dict,
    job_profile: Dict,
    match_result: Dict,
):

    experienced = has_professional_experience(resume_profile)

    weights = (
        WEIGHTS_EXPERIENCED
        if experienced
        else WEIGHTS_FRESHER
    )

    skill_score = calculate_skill_score(
        job_profile,
        match_result,
    )

    project_score = PROJECT_SCORE.get(
        match_result["project_match"],
        40,
    )

    education_score = EDUCATION_SCORE.get(
        match_result["education_match"],
        30,
    )

    certificate_bonus = CERTIFICATE_BONUS.get(
        match_result["certificate_match"],
        0,
    )

    if experienced:

        experience_score = EXPERIENCE_SCORE.get(
            match_result["experience_match"],
            40,
        )

        final_score = (
            skill_score * 0.60
            + project_score * 0.15
            + experience_score * 0.15
            + education_score * 0.10
        )

    else:

        experience_score = None

        final_score = (
            skill_score * 0.60
            + project_score * 0.30
            + education_score * 0.10
        )

    final_score += certificate_bonus

    final_score = min(round(final_score, 2), 100)

    return {
        **match_result,
        "skill_score": round(skill_score, 2),
        "project_score": project_score,
        "experience_score": experience_score,
        "education_score": education_score,
        "certificate_bonus": certificate_bonus,
        "score": final_score,
        "overall_match": get_overall_match(final_score),
    }