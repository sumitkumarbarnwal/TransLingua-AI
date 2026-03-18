@echo off
echo ============================================
echo  TransLingua - Starting Server
echo ============================================
echo.

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Start the server
echo Starting server at http://localhost:8000
echo Press Ctrl+C to stop.
echo.
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
