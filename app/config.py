"""
Configuration Module for Autonomous Agent.
Loads environment variables and sets up project paths.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Base project directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
load_dotenv(dotenv_path=BASE_DIR / ".env")

# LLM Configuration (Groq free tier)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT_SECONDS", "30"))

# Storage Configuration
OUTPUT_DIR = BASE_DIR / os.getenv("OUTPUT_DIR", "output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Server Configuration
APP_HOST = os.getenv("APP_HOST", "127.0.0.1")
APP_PORT = int(os.getenv("APP_PORT", "8000"))
APP_ENV = os.getenv("APP_ENV", "development")


def is_llm_configured() -> bool:
    """
    Check if a legitimate Groq API key is configured.
    Returns False if key is empty, placeholder, or default template value.
    """
    if not GROQ_API_KEY:
        return False
    if "your_groq_api_key" in GROQ_API_KEY.lower():
        return False
    return True
