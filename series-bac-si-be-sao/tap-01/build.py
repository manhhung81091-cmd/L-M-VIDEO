#!/usr/bin/env python3
"""Bác sĩ Bé Sao — Tập 1: Tay sạch mà sao vẫn phải rửa? (TikTok 9:16, 1080x1920, 30fps)

    python3 build.py --real be_that.mp4 --sao ../nhan-vat/bac_si_be_sao.png --vo <thư_mục_vo> --out xuat

Cảnh: 1 bé thật + tiêu đề · 2 kính lúp soi tay bé · 3 phóng to tay bé, chấm nhỏ, chữ NHÌN SẠCH ≠ ĐÃ SẠCH ·
4 hai thẻ (trước khi ăn / sau khi đi vệ sinh) · 5 bé thật · 6 Bé Sao cười, gật đầu.
Bác sĩ Bé Sao là nhân vật dẫn NHỎ ở góc trên trái từ cảnh 2 tới hết; giữa màn hình dành cho chữ và hình.
Mọi chữ hiện từ từ từng chữ.
Giọng: <vo>/1.wav, 2.wav, 4.wav, 5.wav (giọng tạm AI hoặc thu thật, cùng tên file).
"""
import argparse
import math
import os
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
from kich_ban import LINES, NHAN, TITLE  # noqa: E402

FONTS = os.path.join(ROOT, "video-01-con-lon-roi", "fonts")
NHAC = os.path.join(ROOT, "video-01-con-lon-roi", "nhac.py")
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
W, H, FPS = 1080, 1920, 30
PINK, BLUE, WHITE, DARK = (236, 72, 140), (28, 110, 200), (255, 255, 255), (40, 30, 50)

# đoạn quay thật dùng cho từng cảnh (giây trong clip gốc)
REAL_SC1 = 0.0
REAL_SC5 = 8.0
REAL_HAND = 4.5                 # đoạn bé chỉ tay -> phóng to trong kính lúp
HAND_CENTER = (450, 960)        # vị trí tay bé trong khung 1080x1920
SAO_H = 400                     # Bác sĩ Bé Sao: nhỏ, đứng góc trên trái
LENS_R2 = 230                   # kính lúp ở cảnh 2


def F(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


def ease_back(t):
    t = min(max(t, 0.0), 1.0)
    return 1 + 2.70158 * (t - 1) ** 3 + 1.70158 * (t - 1) ** 2


def ease(t):
    t = min(max(t, 0.0), 1.0)
    return 0.5 - 0.5 * math.cos(math.pi * t)


def wav_info(p):
    with wave.open(p) as w:
        sr = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(float) / 32768
    return len(x) / sr, x, sr


class Real:
    """Đọc tuần tự khung hình quay thật (đã xoay dọc) từ một mốc thời gian."""

    def __init__(self, path, start):
        self.p = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{start}", "-i", path,
                                   "-vf", f"scale={W}:{H},fps={FPS}", "-f", "rawvideo",
                                   "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
        self.last = None

    def next(self):
        b = self.p.stdout.read(W * H * 3)
        if len(b) == W * H * 3:
            self.last = Image.frombuffer("RGB", (W, H), b).convert("RGBA")
        return self.last.copy()

    def close(self):
        self.p.kill()


def center_text(d, cx, y, text, fnt, fill, stroke, sw, spacing=8, embedded=False):
    bb = d.multiline_textbbox((0, 0), text, font=fnt, align="center", stroke_width=sw, spacing=spacing)
    d.multiline_text((cx - (bb[2] - bb[0]) / 2 - bb[0], y), text, font=fnt, fill=fill, align="center",
                     stroke_width=sw, stroke_fill=stroke, spacing=spacing)
    return bb[3] - bb[1]


def wrap(d, text, fnt, maxw):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if d.textlength(t, font=fnt) <= maxw:
            cur = t
        else:
            lines.append(cur)
            cur = w_
    lines.append(cur)
    if len(lines) > 2:  # tối đa 2 dòng: chia đôi theo số chữ
        n = len(words) // 2 + len(words) % 2
        lines = [" ".join(words[:n]), " ".join(words[n:])]
    return "\n".join(lines)


def reveal(frame, txt, fnt, cx, y, t0, t1, tt, fill, stroke, sw, spacing=10, fade=0.22, rise=14):
    """Vẽ chữ hiện TỪ TỪ từng chữ: chữ thứ i xuất hiện tại t0 + (t1-t0)*vị_trí/độ_dài,
    mờ dần -> rõ trong `fade` giây và nhích lên `rise` px. Bố cục cố định (không nhảy dòng)."""
    if tt < t0:
        return
    lay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    lines = txt.split("\n")
    asc, desc = fnt.getmetrics()
    lh = asc + desc + spacing
    total_chars = max(1, len(txt.replace("\n", " ")))
    pos = 0
    for li, line in enumerate(lines):
        lw = d.textlength(line, font=fnt)
        x0 = cx - lw / 2
        words = line.split(" ")
        for wi, w_ in enumerate(words):
            prefix = " ".join(words[:wi]) + (" " if wi else "")
            ta = t0 + (t1 - t0) * pos / total_chars
            pos += len(w_) + 1
            if tt < ta:
                continue
            a = min(1.0, (tt - ta) / fade)
            e = 1 - (1 - a) ** 3
            col = fill[:3] + (int(255 * e),)
            scol = stroke[:3] + (int(255 * e),)
            d.text((x0 + d.textlength(prefix, font=fnt), y + li * lh + rise * (1 - e)), w_, font=fnt,
                   fill=col, stroke_width=sw, stroke_fill=scol)
    frame.alpha_composite(lay)


def sparkle(d, cx, cy, r, color):
    k = r * 0.28
    d.polygon([(cx, cy - r), (cx + k, cy - k), (cx + r, cy), (cx + k, cy + k),
               (cx, cy + r), (cx - k, cy + k), (cx - r, cy), (cx - k, cy - k)], fill=color)


def paste_c(base, im, cx, cy):
    base.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


def emoji(ch, size):
    f = ImageFont.truetype(EMOJI, 109)
    im = Image.new("RGBA", (140, 140), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((8, 8), ch, font=f, embedded_color=True)
    im = im.crop(im.getbbox())
    return im.resize((size, int(im.height * size / im.width)), Image.LANCZOS)


def background():
    g = np.linspace(0, 1, H)[:, None, None]
    top, bot = np.array([214, 238, 255]), np.array([255, 243, 249])
    arr = (top * (1 - g) + bot * g).astype(np.uint8) * np.ones((1, W, 1), np.uint8)
    bg = Image.fromarray(arr).convert("RGBA")
    d = ImageDraw.Draw(bg)
    rng = np.random.default_rng(5)
    for _ in range(14):
        x, y, r = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(40, 160)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, 70))
    return bg.filter(ImageFilter.GaussianBlur(18))


def synth_sfx(path, events, total, sr=48000):
    out = np.zeros(int(total * sr))
    for t0, f0, dur, amp in events:
        n = int(dur * sr)
        t = np.arange(n) / sr
        s = sum(np.sin(2 * np.pi * f0 * m * t) * a for m, a in ((1, 1), (2.01, .35), (3.03, .12)))
        s *= np.exp(-t * (5 / dur)) * amp
        i = int(t0 * sr)
        out[i:i + n] += s[: max(0, len(out) - i)]
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((np.clip(out, -1, 1) * 32767).astype("<i2").tobytes())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--real", required=True)
    ap.add_argument("--sao", required=True)
    ap.add_argument("--vo", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--name", default="BacSiBeSao_Tap01_TaySachMaSaoVanPhaiRua")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    vo = {k: wav_info(os.path.join(args.vo, k + ".wav")) for k, _, _ in LINES}
    text = {k: t for k, _, t in LINES}
    d = {k: v[0] for k, v in vo.items()}

    # ---- timeline (theo độ dài giọng) ----
    sc = {}
    t = 0.0
    sc[1] = (t, max(3.5, 0.25 + d["1"] + 0.45)); t += sc[1][1]
    sc[2] = (t, 0.35 + d["2"] + 0.45); t += sc[2][1]
    sc[3] = (t, 3.2); t += sc[3][1]
    sc[4] = (t, 0.3 + d["4"] + 0.6); t += sc[4][1]
    sc[5] = (t, max(2.6, 0.25 + d["5"] + 0.6)); t += sc[5][1]
    sc[6] = (t, 2.4); t += sc[6][1]
    total = t
    vo_at = {"1": sc[1][0] + 0.25, "2": sc[2][0] + 0.35, "4": sc[4][0] + 0.3, "5": sc[5][0] + 0.25}
    t4 = text["4"]
    card_t = [vo_at["4"] + 0.05, vo_at["4"] + d["4"] * t4.index("sau khi") / len(t4)]
    soap_t = vo_at["4"] + d["4"] * t4.index("xà phòng") / len(t4)

    def env(k, tt):  # độ lớn giọng tại thời điểm tt (để Bé Sao "nói" nhún theo)
        _, x, sr = vo[k]
        i = int((tt - vo_at[k]) * sr)
        if i < 0 or i >= len(x):
            return 0.0
        seg = x[i:i + sr // FPS]
        return min(1.0, float(np.sqrt((seg ** 2).mean())) * 6) if len(seg) else 0.0

    # ---- tài nguyên ----
    sao = Image.open(args.sao).convert("RGBA")
    bg = background()
    f_title = F("Baloo2-ExtraBold.ttf", 92)
    f_tap = F("Baloo2-ExtraBold.ttf", 50)
    f_nhan = F("Baloo2-ExtraBold.ttf", 88)
    f_card_big = F("Baloo2-ExtraBold.ttf", 68)
    em_rice, em_wc, em_soap = emoji("🍚", 190), emoji("🚽", 160), emoji("🧼", 140)
    rng = np.random.default_rng(11)
    germs = []
    for _ in range(30):
        a, r = rng.uniform(0, 2 * math.pi), 330 * math.sqrt(rng.uniform(0.02, 1))
        germs.append((math.cos(a) * r, math.sin(a) * r, rng.uniform(9, 24), rng.uniform(0.35, 1.7),
                      [(120, 200, 70), (160, 100, 220), (240, 150, 50), (70, 180, 200)][rng.integers(4)],
                      rng.uniform(0, 6.28)))
    sparks = [(rng.uniform(60, W - 60), rng.uniform(200, 1500), rng.uniform(10, 24), rng.uniform(0, 6.28))
              for _ in range(12)]

    def draw_sao(frame, cx, cy, hgt, rot=0.0, sq=1.0):
        w_ = int(sao.width * hgt / sao.height)
        im = sao.resize((max(1, int(w_ / sq ** 0.5)), max(1, int(hgt * sq))), Image.LANCZOS)
        if abs(rot) > 0.2:
            im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
        sh = Image.new("RGBA", (int(w_ * 0.7), 40), (0, 0, 0, 0))
        ImageDraw.Draw(sh).ellipse((0, 0, sh.width - 1, 39), fill=(60, 80, 140, 60))
        paste_c(frame, sh.filter(ImageFilter.GaussianBlur(8)), cx, cy + hgt / 2 - 10)
        paste_c(frame, im, cx, cy - (hgt * sq - hgt) / 2)
        return w_

    def draw_lens(frame, src, cx, cy, R, zoom, src_c, germs_t=None):
        """Kính lúp: trong mặt kính là hình phóng to `zoom` lần quanh điểm src_c của khung gốc."""
        R = max(2.0, R)
        cs = int(2 * R / zoom)
        sx, sy = src_c
        crop = src.crop((int(sx - cs / 2), int(sy - cs / 2), int(sx + cs / 2), int(sy + cs / 2))).resize(
            (int(2 * R), int(2 * R)), Image.LANCZOS)
        if germs_t is not None:
            cd = ImageDraw.Draw(crop)
            for (gx, gy, gr, gt, col, ph) in germs:
                if germs_t >= gt:
                    p = ease_back((germs_t - gt) / 0.25) * R / 400
                    x = R + gx * R / 400 + 3 * math.sin(germs_t * 6 + ph)
                    y = R + gy * R / 400 + 3 * math.cos(germs_t * 5 + ph)
                    rr = gr * p
                    cd.ellipse((x - rr, y - rr, x + rr, y + rr), fill=col + (215,),
                               outline=tuple(int(c * 0.6) for c in col) + (255,), width=max(1, int(rr * 0.2)))
        mask = Image.new("L", crop.size, 0)
        ImageDraw.Draw(mask).ellipse((0, 0, crop.width - 1, crop.height - 1), fill=255)
        crop.putalpha(mask)
        paste_c(frame, crop, cx, cy)
        dr = ImageDraw.Draw(frame)
        hx2, hy2 = cx + R * 0.72, cy + R * 0.72
        dr.line((hx2, hy2, hx2 + R * 0.55, hy2 + R * 0.55), fill=(120, 70, 40), width=max(2, int(R * 0.28)))
        dr.ellipse((cx - R, cy - R, cx + R, cy + R), outline=BLUE, width=max(2, int(R * 0.12)))
        dr.arc((cx - R * 0.8, cy - R * 0.8, cx + R * 0.8, cy + R * 0.8), 200, 250,
               fill=(255, 255, 255, 200), width=max(1, int(R * 0.06)))

    def subtitle(frame, tt):
        for k in vo_at:
            a, b = vo_at[k] - 0.05, vo_at[k] + d[k] + 0.3
            if a <= tt <= b:
                dr = ImageDraw.Draw(frame)
                size = 60
                while True:  # tối đa 2 dòng, tự thu nhỏ chữ cho vừa khung
                    fnt = F("Baloo2-ExtraBold.ttf", size)
                    txt = wrap(dr, text[k], fnt, 920)
                    if max(dr.textlength(ln, font=fnt) for ln in txt.split("\n")) <= 940 or size <= 44:
                        break
                    size -= 2
                reveal(frame, txt, fnt, W / 2, 1290, vo_at[k] - 0.05, vo_at[k] + d[k] * 0.92, tt,
                       WHITE, DARK, 6)

    enc = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow",
                            "-crf", "19", "-pix_fmt", "yuv420p", os.path.join(args.out, "_video.mp4")],
                           stdin=subprocess.PIPE)
    real1, real5, realh = Real(args.real, REAL_SC1), Real(args.real, REAL_SC5), Real(args.real, REAL_HAND)
    real2 = Real(args.real, REAL_SC1 + sc[1][1])  # cảnh 2 nối tiếp đoạn quay của cảnh 1
    hand_bg = None
    lens_end = (0, 0)
    for fi in range(int(round(total * FPS))):
        tt = fi / FPS
        if tt < sc[2][0]:                                   # ---- cảnh 1: bé thật + tiêu đề
            frame = real1.next()
            dr = ImageDraw.Draw(frame)
            if tt < sc[1][1] - 0.15:
                a = int(255 * ease(tt / 0.3))
                pill = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                pd = ImageDraw.Draw(pill)
                pd.rounded_rectangle((W / 2 - 110, 140, W / 2 + 110, 212), 36, fill=PINK[:3] + (a,))
                frame.alpha_composite(pill)
                reveal(frame, TITLE.split("\n")[0], f_tap, W / 2, 144, 0.0, 0.05, tt, WHITE, PINK, 0)
                reveal(frame, "\n".join(TITLE.split("\n")[1:]), f_title, W / 2, 240, 0.25, 1.1, tt,
                       WHITE, PINK, 9)
            subtitle(frame, tt)
        elif tt < sc[3][0]:                                 # ---- cảnh 2: kính lúp soi tay bé (quay thật)
            lt = tt - sc[2][0]
            frame = real2.next()
            src = frame.copy()
            frame.alpha_composite(Image.new("RGBA", (W, H), (255, 245, 250, 70)))
            if lt > 0.6:  # kính lúp bay vào rồi lướt từ tờ tranh tới bàn tay
                k = ease_back((lt - 0.6) / 0.45)
                m = ease((lt - 0.9) / (sc[2][1] - 1.2))
                cx = 760 + (HAND_CENTER[0] + 40 - 760) * m
                cy = 760 + (HAND_CENTER[1] - 760) * m
                R = LENS_R2 * max(0.02, k)
                draw_lens(frame, src, cx, cy, R, 1.8, (cx, cy))
                lens_end = (cx, cy)
            subtitle(frame, tt)
        elif tt < sc[4][0]:                                 # ---- cảnh 3: phóng to tay bé + chấm nhỏ
            lt = tt - sc[3][0]
            live = realh.next()
            if hand_bg is None:
                hand_bg = live.filter(ImageFilter.GaussianBlur(22))
                hand_bg.alpha_composite(Image.new("RGBA", (W, H), (255, 240, 248, 120)))
            frame = hand_bg.copy()
            k = ease(lt / 0.45)
            R = LENS_R2 + (400 - LENS_R2) * k
            cx = lens_end[0] + (540 - lens_end[0]) * k
            cy = lens_end[1] + (880 - lens_end[1]) * k
            draw_lens(frame, live, cx, cy, R, 2.2, HAND_CENTER, germs_t=lt)
            reveal(frame, NHAN, f_nhan, W / 2, 1335, sc[3][0] + 1.2, sc[3][0] + 1.9, tt,
                   WHITE, (215, 40, 60), 9, fade=0.25, rise=20)
        elif tt < sc[5][0]:                                 # ---- cảnh 4: 2 thẻ hình ở giữa
            lt = tt - sc[4][0]
            frame = bg.copy()
            dr = ImageDraw.Draw(frame)
            for (x, y, r, ph) in sparks:
                a = 0.5 + 0.5 * math.sin(tt * 2.3 + ph)
                if a > 0.45 and y > 560:
                    sparkle(dr, x, y, r * a, (255, 210, 60, int(220 * a)))
            for i, (ct, em, lab) in enumerate(((card_t[0], em_rice, "Trước khi ăn"),
                                               (card_t[1], em_wc, "Sau khi đi vệ sinh"))):
                if tt >= ct:
                    a = ease((tt - ct) / 0.35)
                    kk = 0.85 + 0.15 * ease_back((tt - ct) / 0.4)
                    cw, ch = 700, 300
                    card = Image.new("RGBA", (cw + 20, ch + 26), (0, 0, 0, 0))
                    cdr = ImageDraw.Draw(card)
                    cdr.rounded_rectangle((10, 18, cw + 10, ch + 18), 46, fill=(200, 60, 120, 50))
                    card = card.filter(ImageFilter.GaussianBlur(7))
                    cdr = ImageDraw.Draw(card)
                    cdr.rounded_rectangle((10, 10, cw + 10, ch + 10), 46, fill=WHITE, outline=PINK, width=8)
                    card.alpha_composite(em, (60, int(10 + ch / 2 - em.height / 2)))
                    reveal(card, lab if i == 0 else "Sau khi\nđi vệ sinh", f_card_big, 460,
                           ch / 2 + 10 - (40 if i == 0 else 80), ct + 0.15, ct + 0.6, tt, PINK, WHITE, 0, rise=8)
                    card = card.resize((max(1, int(card.width * kk)), max(1, int(card.height * kk))))
                    card.putalpha(card.getchannel("A").point(lambda v, a=a: int(v * a)))
                    paste_c(frame, card, 600, 735 + i * 345)
            if tt >= soap_t:
                kk = ease_back((tt - soap_t) / 0.4)
                s_ = em_soap.resize((max(1, int(em_soap.width * kk)), max(1, int(em_soap.height * kk))))
                paste_c(frame, s_, 885 + 5 * math.sin(tt * 5), 905)
            subtitle(frame, tt)
        elif tt < sc[6][0]:                                 # ---- cảnh 5: bé thật
            frame = real5.next()
            subtitle(frame, tt)
        else:                                               # ---- cảnh 6: bé thật + Bé Sao cười, gật đầu
            lt = tt - sc[6][0]
            frame = real5.next()
            dr = ImageDraw.Draw(frame)
            for i, (x, y, r, ph) in enumerate(sparks[:8]):
                a = ease_back((lt - i * 0.06) / 0.3)
                if a > 0:
                    ang = i / 8 * 2 * math.pi
                    sparkle(dr, 200 + math.cos(ang) * 240, 380 + math.sin(ang) * 240, 16 * min(a, 1.2),
                            (255, 210, 60, 230))
        if tt >= sc[2][0]:                                  # Bác sĩ Bé Sao nhỏ ở góc trên trái
            lt = tt - sc[2][0]
            k = ease_back(lt / 0.45)
            talk = max(env("2", tt), env("4", tt))
            rot = 3 * math.sin(tt * 2.5) + 4 * talk
            sq, dy = 1 + 0.035 * talk, 8 * math.sin(tt * 4) - 10 * talk
            if sc[4][0] <= tt < sc[5][0]:
                rot -= 9 * ease((tt - card_t[0]) / 0.4)      # nghiêng chỉ sang 2 thẻ
            if tt >= sc[6][0]:                               # bật cười, gật đầu
                nod = math.sin((tt - sc[6][0]) * 2 * math.pi * 1.6)
                rot, sq, dy = 7 * nod, 1 - 0.06 * abs(nod), 12 * abs(nod)
            draw_sao(frame, 200, 375 + dy, SAO_H * max(0.02, k), rot=rot, sq=sq)
        enc.stdin.write(frame.convert("RGB").tobytes())
    for r in (real1, real2, real5, realh):
        r.close()
    enc.stdin.close()
    enc.wait()

    # ---- âm thanh ----
    sfx = os.path.join(args.out, "_sfx.wav")
    ev = [(sc[2][0] + 0.05, 1568, 0.4, 0.22), (sc[2][0] + 0.9, 2093, 0.35, 0.18),
          (sc[3][0] + 0.05, 1318, 0.5, 0.2), (sc[3][0] + 1.3, 2349, 0.45, 0.22),
          (card_t[0], 1760, 0.35, 0.18), (card_t[1], 1976, 0.35, 0.18), (soap_t, 2637, 0.35, 0.16),
          (sc[6][0] + 0.05, 2093, 0.5, 0.2)]
    ev += [(sc[3][0] + g[3], 3000 + 400 * (i % 3), 0.12, 0.05) for i, g in enumerate(germs[:12])]
    synth_sfx(sfx, ev, total)
    music = os.path.join(args.out, "_nhac.wav")
    subprocess.run([sys.executable, NHAC, "--out", music, "--dur", f"{total:.3f}", "--bpm", "100"], check=True)
    inp, fl = ["-i", os.path.join(args.out, "_video.mp4")], []
    for i, (k, _, _) in enumerate(LINES):
        inp += ["-i", os.path.join(args.vo, k + ".wav")]
        fl.append(f"[{i + 1}:a]adelay={int(vo_at[k] * 1000)}[v{i}]")
    n = len(LINES) + 1
    inp += ["-i", music, "-i", sfx]
    fl.append("".join(f"[v{i}]" for i in range(len(LINES))) +
              f"amix=inputs={len(LINES)}:normalize=0,apad,atrim=0:{total:.3f},"
              "acompressor=threshold=-20dB:ratio=2.5,loudnorm=I=-16:TP=-2[vo]")
    fl.append("[vo]asplit=2[vo1][vo2]")
    fl.append(f"[{n}:a]volume=-19dB[m]")
    fl.append(f"[m][vo2]sidechaincompress=threshold=0.03:ratio=4:attack=30:release=400,"
              f"afade=t=out:st={total - 1.2:.3f}:d=1.2[mus]")
    fl.append(f"[{n + 1}:a]volume=-8dB[sfx]")
    fl.append("[vo1][mus][sfx]amix=inputs=3:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=9,aresample=48000[a]")
    mp4 = os.path.join(args.out, args.name + ".mp4")
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", *inp, "-filter_complex", ";".join(fl),
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-t", f"{total:.3f}", "-movflags", "+faststart", mp4], check=True)
    for f_ in ("_video.mp4", "_sfx.wav", "_nhac.wav"):
        os.remove(os.path.join(args.out, f_))
    print(f"Xong: {mp4} ({total:.2f}s)")
    for i in range(1, 7):
        print(f"  Cảnh {i}: {sc[i][0]:5.2f} → {sc[i][0] + sc[i][1]:5.2f}")


if __name__ == "__main__":
    main()
