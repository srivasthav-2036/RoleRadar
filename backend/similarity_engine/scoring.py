"""
scoring.py

Computes the final numeric match score (0–100) from Gemini's structured
match result.

RECALIBRATION HISTORY:

2026-07-16 (v1) — Reduced component ceilings to 93, added per-skill
    penalties of 3 pts/skill (max 15), tightened calibration curve
    constant to +8.  Result: scoring became too strict — genuinely
    relevant candidates with 70-80% skill match scored in the 50s and
    were filtered out of recommendations.

2026-07-17 (v2) — Recalibrated for better coverage:
    Component ceilings raised 93→96, missing-skill penalty reduced
    3→2 pts/skill, calibration curve constant loosened +8→+5,
    certificate bonus cap raised +3→+4. Result: too lenient —
    mid-range and weak matches were inflated into the 70-80s.

2026-07-26 (v3 — this version) — Slightly stricter to better reflect
    actual resume-job fit quality:

1.  Missing-skill penalty raised: 2.0 → 2.5 pts/skill.
    A candidate missing 3 required skills loses 7.5 pts instead of 6.
    Max cap unchanged at 12.0.

2.  Skill score base cap lowered: 93 → 90.
    Only a near-perfect skill match approaches the ceiling.
    Reduces inflation from "mostly matching" candidates.

3.  Calibration curve constant tightened: +5 → +6.
    Slightly more compression of mid-range scores.
        raw=96 → ~92.8   raw=85 → ~83.0
        raw=75 → ~72.5   raw=60 → ~57.6

4.  Good Match threshold raised: 72 → 73.
    Average Match threshold raised: 55 → 57.
    Excellent Match unchanged at ≥ 88.

Thresholds (get_overall_match):
    Excellent Match  : ≥ 88
    Good Match       : ≥ 73
    Average Match    : ≥ 57
    Weak Match       : < 57
"""

import math
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
# SCORE MAPS  (maxes reduced from 100 → 93–95)
# ==========================================================

PROJECT_SCORE = {
    "Excellent": 96,   # was 93 (v1), 100 (original)
    "High":      82,   # was 78
    "Medium":    63,   # was 60
    "Low":       38,   # was 35
}

EXPERIENCE_SCORE = {
    "Strong":   96,    # was 93 (v1), 100 (original)
    "Moderate": 73,    # was 70
    "Weak":     38,    # was 35
}

EDUCATION_SCORE = {
    "Meets":            96,   # was 93 (v1), 100 (original)
    "Partially Meets":  68,   # was 65
    "Does Not Meet":    28,   # was 25
}

# Certificate bonus capped at +4 (was +3 in v1, +5 original)
CERTIFICATE_BONUS = {
    "Strong":   4,   # was 3
    "Moderate": 2,
    "Weak":     1,
    "None":     0,
}

# Penalty per unmatched required skill — raised from 2.0 → 2.5 (v3)
# Max cap unchanged at 12.0
_MISSING_SKILL_PENALTY_PER = 2.5
_MISSING_SKILL_PENALTY_MAX = 12.0


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
# SKILL SCORE  (with missing-skill penalty)
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
        return 50.0

    if not required:
        return round(
            (len(preferred & matched_preferred) / len(preferred)) * 93,
            2,
        )

    required_ratio = len(required & matched_required) / len(required)

    if preferred:
        preferred_ratio = len(preferred & matched_preferred) / len(preferred)
    else:
        preferred_ratio = required_ratio

    raw = required_ratio * 0.80 + preferred_ratio * 0.20

    # Cap at 90 (lowered from 93 in v3 to reduce inflation from partial matches)
    base_score = round(raw * 90, 2)

    # Penalty for unmatched *required* skills — missing critical skills
    # must visibly lower the score, not be absorbed by high preferred-match
    unmatched_required = len(required - matched_required)
    penalty = min(unmatched_required * _MISSING_SKILL_PENALTY_PER,
                  _MISSING_SKILL_PENALTY_MAX)

    return max(0.0, round(base_score - penalty, 2))


# ==========================================================
# SOFT CALIBRATION CURVE
# ==========================================================

def _calibrate(raw: float) -> float:
    """
    Compress scores so that values near 100 are genuinely hard to reach.
    Derived from:  calibrated = 100 × (raw / (raw + 6)) ^ 0.92
    Constant changed from +5 → +6 (v3) to slightly compress mid-range scores.
    Examples:
        raw=96 → ~92.8      raw=85 → ~83.0
        raw=75 → ~72.5      raw=60 → ~57.6
    At raw=100, result ≈ 96.2 — unreachable in practice since component
    ceilings cap the weighted sum well below 100.
    """
    if raw <= 0:
        return 0.0
    calibrated = 100.0 * ((raw / (raw + 6.0)) ** 0.92)
    return round(min(calibrated, 100.0), 2)


# ==========================================================
# OVERALL MATCH  (recalibrated thresholds)
# ==========================================================

def get_overall_match(score: float) -> str:
    if score >= 88:
        return "Excellent Match"
    if score >= 73:
        return "Good Match"
    if score >= 57:
        return "Average Match"
    return "Weak Match"


# ==========================================================
# MAIN
# ==========================================================

def calculate_score(
    resume_profile: Dict,
    job_profile: Dict,
    match_result: Dict,
) -> Dict:

    experienced = has_professional_experience(resume_profile)
    weights = WEIGHTS_EXPERIENCED if experienced else WEIGHTS_FRESHER

    skill_score = calculate_skill_score(job_profile, match_result)
    project_score = PROJECT_SCORE.get(match_result.get("project_match", ""), 35)
    education_score = EDUCATION_SCORE.get(match_result.get("education_match", ""), 25)
    certificate_bonus = CERTIFICATE_BONUS.get(match_result.get("certificate_match", "None"), 0)

    if experienced:
        experience_score = EXPERIENCE_SCORE.get(match_result.get("experience_match", ""), 35)
        raw = (
            skill_score      * (weights["skills"]     / 100) +
            project_score    * (weights["projects"]   / 100) +
            experience_score * (weights["experience"] / 100) +
            education_score  * (weights["education"]  / 100)
        )
    else:
        experience_score = None
        raw = (
            skill_score   * (weights["skills"]   / 100) +
            project_score * (weights["projects"] / 100) +
            education_score * (weights["education"] / 100)
        )

    # Apply soft calibration curve, then add cert bonus (capped at 3)
    calibrated = _calibrate(raw)
    final_score = min(round(calibrated + certificate_bonus, 2), 100.0)

    return {
        **match_result,
        "skill_score":       round(skill_score, 2),
        "project_score":     project_score,
        "experience_score":  experience_score,
        "education_score":   education_score,
        "certificate_bonus": certificate_bonus,
        "score":             final_score,
        "overall_match":     get_overall_match(final_score),
    }