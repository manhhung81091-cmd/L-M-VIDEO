#!/usr/bin/env python3
"""Nhận dạng giọng nói bằng faster-whisper và ghi ra file phụ đề .srt.

Cách dùng:
  python transcribe.py VIDEO_HOẶC_AUDIO [-o out.srt] [--model medium]
                       [--language vi] [--max-chars 42]
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np


def load_audio(path):
    """Giải mã âm thanh bằng ffmpeg (16 kHz, mono) để không phụ thuộc phiên bản PyAV."""
    local = Path.home() / "video-tools" / "bin" / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg")
    ffmpeg = str(local) if local.exists() else shutil.which("ffmpeg")
    if not ffmpeg:
        sys.exit("Không tìm thấy ffmpeg. Hãy chạy file cài đặt trong README.md.")
    raw = subprocess.run([ffmpeg, "-nostdin", "-v", "error", "-i", path, "-vn",
                          "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768.0


def ts(seconds):
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def split_words(words, max_chars):
    """Chia các từ thành từng dòng phụ đề ngắn, không quá max_chars ký tự."""
    line = []
    for w in words:
        text = "".join(x.word for x in line + [w]).strip()
        if line and len(text) > max_chars:
            yield line
            line = []
        line.append(w)
    if line:
        yield line


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("-o", "--output")
    ap.add_argument("--model", default="medium")
    ap.add_argument("--language", default=None, help="vd: vi, en (bỏ trống để tự nhận)")
    ap.add_argument("--max-chars", type=int, default=42)
    args = ap.parse_args()

    from faster_whisper import WhisperModel

    out = Path(args.output or Path(args.input).with_suffix(".srt"))
    model = WhisperModel(args.model, device="auto", compute_type="int8")
    segments, info = model.transcribe(load_audio(args.input), language=args.language,
                                      word_timestamps=True, vad_filter=True)
    print(f"Ngôn ngữ: {info.language} ({info.language_probability:.0%})", file=sys.stderr)

    cues = []
    for seg in segments:
        if seg.words:
            for line in split_words(seg.words, args.max_chars):
                cues.append((line[0].start, line[-1].end,
                             "".join(w.word for w in line).strip()))
        elif seg.text.strip():
            cues.append((seg.start, seg.end, seg.text.strip()))

    with out.open("w", encoding="utf-8") as f:
        for i, (start, end, text) in enumerate(cues, 1):
            f.write(f"{i}\n{ts(start)} --> {ts(end)}\n{text}\n\n")
    print(out)


if __name__ == "__main__":
    main()
