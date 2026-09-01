@echo off
REM Double-click this file, or run it from Command Prompt.
setlocal

echo.
echo  FinDoc Assistant - setup
echo  ========================
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo  Python was not found.
  echo  Install it from python.org, and tick "Add Python to PATH"
  echo  on the first screen of the installer.
  echo.
  pause
  exit /b 1
)

echo  [1/4] Creating virtual environment
if not exist .venv (
  python -m venv .venv
  if errorlevel 1 goto failed
)

call .venv\Scripts\activate.bat

echo  [2/4] Installing dependencies. This downloads PyTorch, so expect
echo        3-5 minutes. Progress is hidden; it has not frozen.
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt
if errorlevel 1 goto failed

if not exist .env copy .env.example .env >nul

echo  [3/4] Checking the code
python -m pytest tests\ -q
if errorlevel 1 goto failed

echo  [4/4] Building both search indexes from the bundled documents
echo        The embedding model downloads once, about 90 MB.
python -m app.ingest --chunk-size 1000 --overlap 150 --collection findoc_1000
if errorlevel 1 goto failed
python -m app.ingest --chunk-size 500 --overlap 75 --collection findoc_500
if errorlevel 1 goto failed

echo.
echo  Setup finished.
echo.
echo  Starting the app. Open http://localhost:8000 in your browser.
echo  Press Ctrl+C in this window to stop it.
echo.
python -m uvicorn app.main:app --port 8000
goto end

:failed
echo.
echo  Something failed above. Copy the last error message for help.
echo.
pause
exit /b 1

:end
pause
