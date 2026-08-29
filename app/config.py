"""Runtime configuration, read from the environment."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
APP_ENV = os.getenv("APP_ENV", "development")
IS_PROD = APP_ENV == "production"

# Structured site content lives here so pages and the (later) RAG chatbot
# read from one source of truth.
SITE = {
    "name": "Pradyumna Prasad",
    "tagline": "Backend & AI/ML engineer. I build data pipelines, RAG systems, and APIs that ship.",
    "subline": (
        "3rd-year CSE (AI/ML) @ SIT  ·  Data & AI intern at Hexango  ·  "
        "400+ DSA problems  ·  MIT National Hackathon '25 winner"
    ),
    "location": "Tumakuru, India — open to Bengaluru / remote",
    "email": "pradyumnaprasad.05@gmail.com",
    "links": {
        "GitHub": "https://github.com/PradyumnaPrasad",
        "LinkedIn": "https://www.linkedin.com/in/pradyumnaprasad4536",
        "LeetCode": "https://leetcode.com/u/Pradyumna_Prasad/",
    },
    "resume_path": "/static/Pradyumna_Prasad_Resume.pdf",
}
