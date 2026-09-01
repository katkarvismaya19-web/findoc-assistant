@echo off
REM Measure retrieval quality and print the number for your resume.
call .venv\Scripts\activate.bat
python -m eval.evaluate --collections findoc_1000 findoc_500 --k 3 --show-misses
echo.
pause
