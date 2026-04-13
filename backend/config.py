"""
Configuration for the Nepali & Sinhalese Translation System.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
MODELS_DIR = BASE_DIR / "models"
FEEDBACK_DIR = BASE_DIR / "feedback"
FRONTEND_DIR = BASE_DIR / "frontend"

# Ensure directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)
FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)

# Tesseract OCR Configuration
# On Windows, set the path to tesseract executable
TESSERACT_CMD = os.getenv("TESSERACT_CMD", r"C:\Program Files\Tesseract-OCR\tesseract.exe")

# Supported languages mapping (Tesseract language codes)
OCR_LANGUAGES = {
    "nepali": "nep",       # Nepali (Devanagari script)
    "sinhalese": "sin",    # Sinhalese (Sinhala script)
}

# Translation model mapping (HuggingFace model identifiers)
TRANSLATION_MODELS = {
    "nepali": "Helsinki-NLP/opus-mt-hi-en",       # Hindi to English (Nepali uses same Devanagari script)
    "sinhalese": "Helsinki-NLP/opus-mt-mul-en",   # Multilingual to English (covers Sinhalese)
}

# Server settings
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# LLM Translation Settings
USE_LLM = os.getenv("USE_LLM", "true").lower() == "true"
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")

# Debug logging
import sys
print(f"[CONFIG] USE_LLM={USE_LLM}", file=sys.stderr)
print(f"[CONFIG] LLM_API_KEY={'***' if LLM_API_KEY else 'NOT SET'}", file=sys.stderr)
print(f"[CONFIG] LLM_BASE_URL={LLM_BASE_URL}", file=sys.stderr)
print(f"[CONFIG] LLM_MODEL={LLM_MODEL}", file=sys.stderr)

# File upload settings
MAX_FILE_SIZE_MB = 50
ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"}
ALLOWED_PDF_EXTENSIONS = {".pdf"}
ALLOWED_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS | ALLOWED_PDF_EXTENSIONS
