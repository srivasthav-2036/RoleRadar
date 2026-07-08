"""
Loads environment variables for the entire project.
Every provider imports values from here.

Example:
from config import ADZUNA_APP_ID
"""

import os
from dotenv import load_dotenv

# Loads your project's .env
load_dotenv()


# ===============================
# Adzuna
# ===============================

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_API_KEY = os.getenv("ADZUNA_API_KEY")
# ===============================
# RapidAPI (JSearch)
# ===============================

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")


# ===============================
# General
# ===============================

USER_AGENT = os.getenv(
    "USER_AGENT",
    "AI-Job-Hunter/1.0"
)

REQUEST_TIMEOUT = 20


# ===============================
# Common Headers
# ===============================

COMMON_HEADERS = {
    "User-Agent": USER_AGENT
}