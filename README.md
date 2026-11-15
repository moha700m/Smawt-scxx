# SMAET REC
A local-first Windows 11 desktop recording studio. The desktop control app runs on the machine; any future local HTTP control endpoint must bind to `127.0.0.1` only. AirPlay reception, if added, is a separate LAN-facing receiver and must never expose the control API.

## Current implementation
- Arabic-first RTL desktop UI built with PySide6.
- Live Windows desktop preview (MSS capture).
- MP4 recording through FFmpeg's Windows `gdigrab` input (H.264); recording state and elapsed time are shown.
- Simple project save/open (JSON) and remembers the last layout in the user's local app-data folder.
- Drawing overlay on the preview (pen and clear).
- Output folder shortcut and explicit FFmpeg availability checks.

## Not yet implemented / hardware verification required
- iPhone USB mirroring: iOS does not expose a generic USB screen-mirroring API to Windows. No fake device is shown.
- iPhone AirPlay reception: requires a compatible Windows AirPlay receiver component. This build reports it as unavailable rather than pretending to connect.
- Microphone/system-audio mixing, 4K capture, touch telemetry, and installer signing are not claimed as working.

## Run on Windows 11
1. Install Python 3.11 or newer.
2. Install FFmpeg and ensure `ffmpeg.exe` is on PATH.
3. Run `install.bat`, then `run.bat`.

## Build a Windows folder release
Run `build.bat`. PyInstaller writes `dist\\SMAET-REC\\`. This is an unsigned folder package, not an installer.

The preview and recording capture the primary desktop. Recording is H.264 MP4 at 30 FPS by default. Test on the target PC before relying on it.
