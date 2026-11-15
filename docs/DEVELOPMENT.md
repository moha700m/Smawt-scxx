# Development

## Local development
- Windows 11
- Python 3.10+
- FFmpeg available on PATH

Run `run.bat` to start the Tkinter desktop UI. The app launches no HTTP server and opens no listening network socket. Screen capture uses FFmpeg's Windows `gdigrab` input and writes MP4 files to the selected local folder.

## Current scope
The initial MVP records the Windows desktop at 30 or 60 fps with H.264. Audio capture, iPhone USB ingestion, and AirPlay receiver integration are intentionally not represented as implemented. Each requires a separately tested capture path and device-level validation.

## Build
Run `build.bat` to produce `dist/SMAET-REC.exe` with PyInstaller. Build and runtime verification must be performed on Windows 11; this repository automation environment cannot certify Windows hardware capture.
