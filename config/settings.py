"""
Application Settings & Configuration
AI Resume Analyzer and ATS Score Checker
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"
STYLES_DIR = BASE_DIR / "styles"

# Load environment variables
load_dotenv(BASE_DIR / ".env")

# Ensure required directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# App Metadata
APP_NAME = "AI Resume Analyzer & ATS Score Checker"
APP_SUBTITLE = "Smart ATS Compatibility Evaluation & Resume Optimization"
APP_VERSION = "1.0.0"

# ATS Scoring Weights (Total = 1.0)
DEFAULT_WEIGHTS = {
    "skills": 0.40,
    "experience": 0.20,
    "education": 0.15,
    "keywords": 0.15,
    "formatting": 0.10
}

# File Upload Settings
MAX_FILE_SIZE_MB = 10
ALLOWED_EXTENSIONS = [".pdf", ".docx"]

# Database Settings
DATABASE_PATH = str(DATA_DIR / "analyses.db")
DEFAULT_ENABLE_HISTORY = True

# AI Provider API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "").strip()
DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip()

# Scoring Disclaimer
ATS_DISCLAIMER = (
    "Note: The calculated ATS score is an estimated compatibility score "
    "based on rule-based NLP algorithms, skills matching, keyword density, and "
    "structural formatting checks. It does not represent any specific company's "
    "proprietary Applicant Tracking System."
)

PRIVACY_NOTICE = (
    "Privacy Notice: Your resume is processed in-memory for analysis. "
    "Original resume files and full text are NOT permanently saved on our servers. "
    "Only anonymized high-level metrics (scores, skills matched, job title) are stored "
    "in your local database history if enabled."
)
