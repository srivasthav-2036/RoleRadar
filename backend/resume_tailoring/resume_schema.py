"""
resume_schema.py

Single source of truth for the resume JSON schema, used by both
resume_extract.py (initial parsing) and tailor_resume.py (tailoring).
Lives in resume_tailoring/ since that's where it's mainly consumed;
resume_extract.py imports it from here too, so both stay in sync
instead of drifting into two different hardcoded copies.

IMPORTANT: "skills" is an OPEN dict, not a fixed set of categories.
Earlier versions forced skills into predefined buckets (programming,
frameworks, libraries, databases, cloud, tools, other) - that's wrong
because a candidate's real skill areas (e.g. "AI/ML", "DevOps",
"Mobile Development", "Data Engineering") don't reliably fit those
boxes and either get miscategorized or dropped. Instead, category
NAMES are generated based on what's actually in the resume.
"""

RESUME_SCHEMA = """{
    "name": "",
    "contact": {
        "email": "",
        "phone": "",
        "location": "",
        "linkedin": "",
        "github": "",
        "portfolio": ""
    },
    "summary": "",
    "skills": {
        "<category_name>": ["skill1", "skill2"]
    },
    "experience": [
        {"company": "", "role": "", "duration": "", "description": "", "skills": []}
    ],
    "projects": [
        {"title": "", "description": "", "technologies": [], "domain": ""}
    ],
    "education": [
        {"degree": "", "college": "", "cgpa": "", "percentage": "", "year": ""}
    ],
    "certifications": [],
    "achievements": [],
    "languages": [],
    "preferred_roles": [],
    "domains": [],
    "keywords": []
}"""

SKILLS_CATEGORY_INSTRUCTIONS = """
For "skills": group the candidate's actual skills into categories
that genuinely reflect their background - do NOT force them into a
fixed predefined list. Choose category names based on what's really
there. Examples of reasonable category names (use only if they fit
this candidate): "programming_languages", "ai_ml", "backend",
"frontend", "cloud_devops", "databases", "mobile", "data_engineering",
"tools". Use snake_case for category names. Do not invent categories
with no skills in them - omit empty categories entirely.
"""

EDUCATION_GRADE_INSTRUCTIONS = """
For "education" entries, distinguish CGPA from PERCENTAGE - they are
different grading systems and must not be mixed up:
- "cgpa": use ONLY if the source expresses the grade on a scale (e.g.
  "9.25/10", "3.8/4.0"). Leave empty ("") if not applicable.
- "percentage": use ONLY if the source expresses the grade as a
  percentage (e.g. "98.8%"). Leave empty ("") if not applicable.
A candidate may legitimately have CGPA for one degree and percentage
for another (e.g. college uses CGPA, high school uses percentage) -
handle each education entry independently. NEVER put a percentage
value into the "cgpa" field or vice versa.
"""

# Used to validate Gemini's output actually has the right shape.
# Only checks top-level structural keys - "skills" subcategory names
# are intentionally NOT validated here since they're dynamic by design.
REQUIRED_TOP_LEVEL_KEYS = [
    "name", "contact", "summary", "skills", "experience",
    "projects", "education", "certifications", "achievements",
    "languages", "preferred_roles", "domains", "keywords",
]


def validate_resume_shape(resume: dict) -> list[str]:
    """
    Returns a list of missing/invalid top-level keys (empty list =
    valid). Doesn't raise - callers decide whether a missing key is
    fatal or fixable. "skills" is checked for being a dict (since
    categories are dynamic), not for specific subkeys.
    """
    missing = [key for key in REQUIRED_TOP_LEVEL_KEYS if key not in resume]

    if "skills" in resume and not isinstance(resume["skills"], dict):
        missing.append("skills (must be a dict of category -> list)")

    return missing