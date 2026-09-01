@echo off
REM Start the app after setup has already been run once.
call .venv\Scripts\activate.bat
echo Open http://localhost:8000
python -m uvicorn app.main:app --port 8000
pause
