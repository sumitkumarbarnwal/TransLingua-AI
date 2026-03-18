@echo off
echo ============================================
echo  TransLingua - Setup Script
echo  Nepali ^& Sinhalese to English Translator
echo ============================================
echo.

:: Check Python
python --version 2>nul
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.9+ from https://www.python.org/
    pause
    exit /b 1
)

:: Create virtual environment
echo [1/4] Creating virtual environment...
if not exist "venv" (
    python -m venv venv
)
call venv\Scripts\activate.bat

:: Install Python dependencies
echo [2/4] Installing Python dependencies...
pip install -r backend\requirements.txt

:: Check Tesseract
echo.
echo [3/4] Checking Tesseract OCR...
tesseract --version 2>nul
if errorlevel 1 (
    echo.
    echo [WARNING] Tesseract OCR is not installed.
    echo Please install Tesseract OCR:
    echo   1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
    echo   2. During installation, select additional languages:
    echo      - Nepali ^(nep^)
    echo      - Sinhala ^(sin^)
    echo   3. Add Tesseract to PATH or set TESSERACT_CMD in .env file
    echo.
) else (
    echo Tesseract is installed.
    echo.
    echo Checking language packs...
    tesseract --list-langs 2>nul | findstr "nep" >nul
    if errorlevel 1 (
        echo [WARNING] Nepali language pack not found.
        echo Download nep.traineddata from:
        echo https://github.com/tesseract-ocr/tessdata/blob/main/nep.traineddata
        echo Place it in Tesseract's tessdata folder.
    ) else (
        echo   Nepali [nep] - OK
    )
    tesseract --list-langs 2>nul | findstr "sin" >nul
    if errorlevel 1 (
        echo [WARNING] Sinhalese language pack not found.
        echo Download sin.traineddata from:
        echo https://github.com/tesseract-ocr/tessdata/blob/main/sin.traineddata
        echo Place it in Tesseract's tessdata folder.
    ) else (
        echo   Sinhalese [sin] - OK
    )
)

:: Create necessary directories
echo.
echo [4/4] Creating directories...
if not exist "uploads" mkdir uploads
if not exist "models" mkdir models
if not exist "feedback" mkdir feedback

echo.
echo ============================================
echo  Setup complete!
echo  Run 'start.bat' to start the application.
echo ============================================
pause
