#!/usr/bin/env python3
"""Tạo giọng đọc TẠM (nữ miền Bắc, vi-VN-HoaiMyNeural) cho từng cảnh.

    python3 tts.py --out <thư_mục_vo> [--rate -10%]

Mỗi cảnh ra 1 file NN.wav (đã cắt khoảng lặng đầu/cuối).
Nếu thu giọng thật: đặt file 01.wav ... 08.wav vào thư mục vo và bỏ qua bước này.
"""
import argparse
import asyncio
import os
import subprocess
import sys

import certifi

# Proxy HTTPS của môi trường dùng CA riêng
if os.path.exists("/root/.ccr/ca-bundle.crt"):
    certifi.where = lambda: "/root/.ccr/ca-bundle.crt"
import edge_tts  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kich_ban import SCENES  # noqa: E402

VOICE = "vi-VN-HoaiMyNeural"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--rate", default="-10%")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    for sc in SCENES:
        if not sc["vo"]:
            continue
        mp3 = os.path.join(args.out, sc["key"] + ".mp3")
        wav = os.path.join(args.out, sc["key"] + ".wav")
        asyncio.run(edge_tts.Communicate(sc["vo"], VOICE, rate=args.rate).save(mp3))
        trim = ("silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
                "silenceremove=start_periods=1:start_threshold=-45dB,areverse")
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", mp3, "-af", trim,
                        "-ar", "48000", "-ac", "1", wav], check=True)
        os.remove(mp3)
        print(sc["key"], sc["vo"])


if __name__ == "__main__":
    main()
