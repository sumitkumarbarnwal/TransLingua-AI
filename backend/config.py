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
    "nepali": "Helsinki-NLP/opus-mt-hi-en",      # Hindi/Nepali to English (Devanagari)
    "sinhalese": "Helsinki-NLP/opus-mt-mul-en",   # Multilingual to English (covers Sinhalese)
}

# Server settings
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# File upload settings
MAX_FILE_SIZE_MB = 50
ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"}
ALLOWED_PDF_EXTENSIONS = {".pdf"}
ALLOWED_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS | ALLOWED_PDF_EXTENSIONS
