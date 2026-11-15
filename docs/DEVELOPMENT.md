# Development

## Requirements
- Windows 11 (x64)
- Python 3.11+
- FFmpeg build containing the `gdigrab` input and `libx264` encoder, available on PATH

## Setup and run
1. Run `install.bat` to create `.venv` and install PySide6, MSS, and PyInstaller.
2. Install FFmpeg separately and ensure `ffmpeg.exe` is available on PATH.
3. Run `run.bat`.

The desktop application does not start an HTTP server and opens no listening control socket. It captures the primary Windows desktop for preview using MSS and records the desktop through FFmpeg's `gdigrab` input at 30 FPS, H.264, MP4. Audio is intentionally disabled in this build.

## Current verified scope
Implemented in source: Arabic RTL desktop interface, primary-monitor preview, pen/highlighter overlay, FFmpeg MP4 recording controls, output-folder shortcut, JSON project save/open, and last-output-folder persistence.

Not implemented: iPhone USB screen ingestion, AirPlay receiver, microphone/system-audio recording, multi-monitor selection, 4K mode selection, touch/click telemetry, and installer signing. The iPhone action displays an explicit limitation message and never fabricates a connection.

## Package
Run `build.bat` to create an unsigned PyInstaller folder package under `dist/SMAET-REC/`. This is not an installer. Build and hardware testing must be performed on Windows 11; a GitHub source commit cannot certify that the capture backend works on a particular PC.
