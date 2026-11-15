@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\pyinstaller.exe (echo Run install.bat first.& pause & exit /b 1)
.venv\Scripts\pyinstaller.exe --noconfirm --clean --windowed --name SMAET-REC --paths src src\smaet_rec\__main__.py
if errorlevel 1 (echo Build failed.& pause & exit /b 1)
echo Build output: dist\SMAET-REC\
pause
