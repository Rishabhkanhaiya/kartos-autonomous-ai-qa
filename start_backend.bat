@echo off
echo ========================================================
echo Starting KARTOS Autonomous QA Backend on port 8000...
echo ========================================================
cd backend
call .\venv\Scripts\activate.bat
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
