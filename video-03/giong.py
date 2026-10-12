#!/usr/bin/env python3
"""Tạo giọng TẠM cho 2 vai bằng Piper (offline), giọng vi_VN-vais1000 (dữ liệu CC BY 4.0).

    python3 giong.py --model vi_VN-vais1000-medium.onnx --out <thư_mục_vo>

- Mẹ: giọng gốc, nói chậm nhẹ.
- Bé: cùng giọng, nâng cao độ + formant (~5 nửa cung) cho trong và nhí hơn.
Có giọng thu thật thì đặt file <id>.wav (01a, 01b, 02, ...) vào thư mục vo và bỏ qua bước này.
"""
import argparse
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kich_ban import SCENES  # noqa: E402

ROLE = {
    "me": {"length": 1.08, "af": ""},
    "be": {"length": 0.98, "af": "rubberband=pitch=1.32:formant=shifted,"},
}
TRIM = ("silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
        "silenceremove=start_periods=1:start_threshold=-45dB,areverse")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    for sc in SCENES:
        for lid, role, text in sc["lines"]:
            raw = os.path.join(args.out, lid + "_raw.wav")
            wav = os.path.join(args.out, lid + ".wav")
            subprocess.run([sys.executable, "-m", "piper", "-m", args.model, "-f", raw,
                            "--length-scale", str(ROLE[role]["length"])],
                           input=text, text=True, check=True, capture_output=True)
            subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", raw, "-af",
                            ROLE[role]["af"] + "aresample=48000," + TRIM, "-ac", "1", wav],
                           check=True)
            os.remove(raw)
            print(lid, role, text)


if __name__ == "__main__":
    main()
