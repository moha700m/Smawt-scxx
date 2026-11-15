@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (echo Install Python 3.11+ first.& pause & exit /b 1)
py -3 -m venv .venv
if errorlevel 1 (echo Could not create virtual environment.& pause & exit /b 1)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (echo Dependency installation failed.& pause & exit /b 1)
python -m pip install -e .
if errorlevel 1 (echo SMAET REC package installation failed.& pause & exit /b 1)
echo Installation complete. Install FFmpeg separately and add it to PATH.
pause
