# TransLingua — Nepali & Sinhalese to English Translation System

An AI/ML-powered solution for extracting text from images and PDFs containing Nepali (Devanagari) and Sinhalese scripts, and translating them to English.

---

## 🌟 Features

| Feature | Description |
|---------|-------------|
| **OCR Extraction** | Extract text from images (PNG, JPG, BMP, TIFF, WebP) and PDFs |
| **Neural Translation** | Translate Nepali and Sinhalese to English using MarianMT models |
| **Full Pipeline** | Upload → OCR → Translate in one click |
| **Offline Capable** | All models cached locally after first download |
| **ML Feedback Loop** | Users submit corrections to improve future translations |
| **Multi-page PDF** | Process multi-page PDF documents with page-by-page OCR |
| **Beautiful UI** | Modern web interface with dark/light themes |

## 📋 Prerequisites

1. **Python 3.9+** — [Download](https://www.python.org/downloads/)
2. **Tesseract OCR** — [Download for Windows](https://github.com/UB-Mannheim/tesseract/wiki)
   - During installation, select **Additional language data**:
     - ✅ Nepali (`nep`)
     - ✅ Sinhala (`sin`)
   - Add Tesseract to your system PATH

## 🚀 Quick Start

### Windows

```batch
# 1. Run the setup script (first time only)
setup.bat

# 2. Start the application
start.bat

# 3. Open browser
# Navigate to http://localhost:8000
```

### Manual Setup

```bash
# 1. Create virtual environment
python -m venv venv

# 2. Activate it
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3. Install dependencies
pip install -r backend/requirements.txt

# 4. Start the server
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 🏗 Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Frontend   │────▶│   FastAPI    │────▶│  Tesseract   │
│  (HTML/CSS/  │     │   Server     │     │    OCR       │
│    JS)       │◀────│              │◀────│   Engine     │
└──────────────┘     │              │     └──────────────┘
                     │              │     ┌──────────────┐
                     │              │────▶│  MarianMT    │
                     │              │     │  Translation │
                     │              │◀────│   Models     │
                     └──────────────┘     └──────────────┘
                            │
                     ┌──────────────┐
                     │   Feedback   │
                     │   Storage    │
                     │  (JSONL)     │
                     └──────────────┘
```

## 📁 Project Structure

```
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI application & routes
│   │   ├── ocr.py            # Tesseract OCR with preprocessing
│   │   ├── translator.py     # MarianMT neural translation
│   │   ├── pdf_processor.py  # PDF to image conversion
│   │   └── models.py         # Pydantic data models
│   ├── config.py             # Application configuration
│   └── requirements.txt      # Python dependencies
├── frontend/
│   ├── index.html            # Main web interface
│   ├── css/style.css         # Design system & styles
│   └── js/app.js             # Frontend application logic
├── models/                   # Cached ML models (auto-created)
├── uploads/                  # Temporary file uploads
├── feedback/                 # User feedback for ML training
├── setup.bat                 # Windows setup script
├── start.bat                 # Windows startup script
└── README.md                 # This file
```

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Web interface |
| `POST` | `/api/ocr` | Extract text from image/PDF |
| `POST` | `/api/translate` | Translate text to English |
| `POST` | `/api/pipeline` | Full OCR + Translation pipeline |
| `POST` | `/api/feedback` | Submit translation corrections |
| `GET` | `/api/status` | System & model status |
| `GET` | `/api/feedback/export/{language}` | Export feedback data |

## 🤖 ML Models

### OCR — Tesseract
- **Nepali**: Uses `nep` trained data (Devanagari script recognition)
- **Sinhalese**: Uses `sin` trained data (Sinhala script recognition)
- Image preprocessing: grayscale, contrast enhancement, sharpening, noise reduction

### Translation — MarianMT (HuggingFace)
- **Nepali → English**: `Helsinki-NLP/opus-mt-hi-en` (Devanagari family)
- **Sinhalese → English**: `Helsinki-NLP/opus-mt-mul-en` (Multilingual)
- Models are downloaded once and cached in `./models/` for offline use
- Uses beam search (num_beams=4) for translation quality

## 🔄 Machine Learning Feedback Loop

The system collects user feedback to enable future model improvement:

1. Users rate translation quality (1-5 stars)
2. Users can provide corrected translations
3. Feedback is stored as JSONL files in `./feedback/`
4. Exported feedback can be used to fine-tune the translation models

### Export Feedback for Training

```bash
curl http://localhost:8000/api/feedback/export/nepali
curl http://localhost:8000/api/feedback/export/sinhalese
```

## 🔧 Configuration

Create a `.env` file in the project root:

```env
# Tesseract path (if not in system PATH)
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe

# Server settings
HOST=0.0.0.0
PORT=8000
DEBUG=true
```

## 🌐 Offline Operation

After initial setup:
1. Translation models are cached locally in `./models/`
2. Tesseract OCR runs entirely offline
3. No internet connection required for operation
4. Works on internal/air-gapped networks

## 📝 License

This project is developed for translating Nepali and Sinhalese literature to English, making it accessible to a wider audience.
