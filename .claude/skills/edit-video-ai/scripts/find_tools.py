#!/usr/bin/env python3
"""In ra đường dẫn ffmpeg, ffprobe và Python có faster-whisper (dạng KEY=giá trị).

Ưu tiên bộ công cụ do setup-mac.sh / setup-windows.bat cài vào ~/video-tools,
nếu không có thì dùng bản có sẵn trong PATH.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

home = Path.home() / "video-tools"
exe = ".exe" if os.name == "nt" else ""


def find_bin(name):
    local = home / "bin" / f"{name}{exe}"
    if local.exists():
        return str(local)
    return shutil.which(name) or ""


def has_whisper(py):
    try:
        return subprocess.run([py, "-c", "import faster_whisper"],
                              capture_output=True).returncode == 0
    except OSError:
        return False


venv_py = home / "whisper-venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
candidates = [str(venv_py)] if venv_py.exists() else []
candidates.append(sys.executable)
whisper_py = next((p for p in candidates if has_whisper(p)), "")

print(f"FFMPEG={find_bin('ffmpeg')}")
print(f"FFPROBE={find_bin('ffprobe')}")
print(f"WHISPER_PYTHON={whisper_py}")
