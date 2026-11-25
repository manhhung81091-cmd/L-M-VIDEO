#!/usr/bin/env python3
"""Chọn khung hình đẹp nhất trong video để làm ảnh bìa.

Quét video (mặc định 4 khung/giây), chấm điểm từng khung có mặt người:
  - mặt to, rõ nét (không nhòe chuyển động)
  - hai mắt mở (không chớp, không nhắm)
  - đang cười (miệng cười, không méo khi đang nói dở)
rồi xuất các khung điểm cao nhất (cách nhau ít nhất 1 giây) và một ảnh lưới để xem.

    python3 chon_khung.py video.mp4 -o thu_muc_ra --top 8

Cần ffmpeg và opencv-python-headless<5. Điểm chỉ là gợi ý: luôn mở ảnh lưới
và tự chọn khung có biểu cảm tươi, tự nhiên, thấy rõ sản phẩm.
"""
import argparse
import glob
import os
import subprocess
import tempfile

import cv2
import numpy as np
from PIL import Image, ImageDraw

H = cv2.data.haarcascades
FACE = cv2.CascadeClassifier(os.path.join(H, "haarcascade_frontalface_default.xml"))
EYE = cv2.CascadeClassifier(os.path.join(H, "haarcascade_eye_tree_eyeglasses.xml"))
SMILE = cv2.CascadeClassifier(os.path.join(H, "haarcascade_smile.xml"))


def cham_diem(path):
    img = cv2.imread(path)
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ge = cv2.equalizeHist(g)
    faces = FACE.detectMultiScale(ge, 1.1, 6, minSize=(160, 160))
    if len(faces) == 0:
        return None
    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
    mat = g[y:y + h, x:x + w]
    net = cv2.Laplacian(mat, cv2.CV_64F).var()
    tren = ge[y:y + h // 2, x:x + w]
    mat_mo = len(EYE.detectMultiScale(tren, 1.1, 8, minSize=(w // 10, w // 10)))
    duoi = ge[y + h // 2:y + h, x:x + w]
    cuoi = SMILE.detectMultiScale(duoi, 1.6, 22, minSize=(w // 4, h // 10))
    diem = 0.0
    diem += min(net, 400) / 400 * 3          # rõ nét
    diem += min(mat_mo, 2) * 1.5               # mắt mở
    diem += 2.5 if len(cuoi) else 0          # cười
    diem += min(w / img.shape[1], 0.45) * 4    # mặt đủ to
    return diem, dict(net=round(net), mat=mat_mo, cuoi=len(cuoi), mat_rong=w)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--fps", type=float, default=4)
    ap.add_argument("--top", type=int, default=8)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["ffmpeg", "-v", "error", "-i", a.video, "-vf", f"fps={a.fps}",
                        "-q:v", "2", os.path.join(tmp, "k_%05d.jpg")], check=True)
        kq = []
        for p in sorted(glob.glob(os.path.join(tmp, "k_*.jpg"))):
            t = (int(os.path.basename(p)[2:7]) - 1) / a.fps
            d = cham_diem(p)
            if d:
                kq.append((d[0], t, p, d[1]))
        kq.sort(reverse=True)
        chon = []
        for d, t, p, info in kq:
            if all(abs(t - t2) >= 1 for _, t2, _, _ in chon):
                chon.append((d, t, p, info))
            if len(chon) >= a.top:
                break
        if not chon:
            print("Không thấy mặt người trong video.")
            return
        o = Image.new("RGB", (len(chon) * 216, 410), "white")
        dr = ImageDraw.Draw(o)
        for i, (d, t, p, info) in enumerate(chon):
            ra = os.path.join(a.out, f"khung_{t:05.2f}s.jpg")
            Image.open(p).save(ra, quality=95)
            o.paste(Image.open(p).resize((216, 384)), (i * 216, 0))
            dr.text((i * 216 + 6, 388), f"{t:.2f}s  {d:.1f}", fill=(0, 0, 0))
            print(f"{t:6.2f}s  điểm {d:4.1f}  {info}  -> {ra}")
        o.save(os.path.join(a.out, "_luoi.jpg"))
        print("Ảnh lưới:", os.path.join(a.out, "_luoi.jpg"))


if __name__ == "__main__":
    main()
