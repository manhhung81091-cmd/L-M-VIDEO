#!/usr/bin/env python3
"""Bác sĩ Bé Sao — Tập 1: Tay sạch mà sao vẫn phải rửa? (TikTok 9:16, 1080x1920, 30fps)

    python3 build.py --real be_that.mp4 --sao ../nhan-vat/bac_si_be_sao.png --vo <thư_mục_vo> --out xuat

Cảnh: 1 bé thật (quay thật) · 2 Bé Sao + kính lúp · 3 kính lúp phóng to tay bé, chấm nhỏ,
chữ NHÌN SẠCH ≠ ĐÃ SẠCH · 4 Bé Sao + 2 hình (trước khi ăn / sau khi đi vệ sinh) · 5 bé thật · 6 Bé Sao cười, gật đầu.
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


def magnifier(R):
    """Kính lúp hoạt hình: vành xanh, mặt kính trong, cán chéo xuống trái."""
    s = int(R * 3.2)
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx = cy = R * 1.15
    hx, hy = cx - R * 0.75 - R * 1.25, cy + R * 0.75 + R * 1.25
    d.line((cx - R * 0.72, cy + R * 0.72, hx + R * 0.15, hy - R * 0.15), fill=(120, 70, 40), width=int(R * 0.34))
    d.ellipse((hx - R * 0.2, hy - R * 0.2, hx + R * 0.2, hy + R * 0.2), fill=(120, 70, 40))
    d.ellipse((cx - R, cy - R, cx + R, cy + R), fill=(200, 235, 255, 90), outline=BLUE, width=int(R * 0.18))
    d.arc((cx - R * 0.68, cy - R * 0.68, cx + R * 0.68, cy + R * 0.68), 200, 260, fill=(255, 255, 255, 230),
          width=int(R * 0.12))
    return im, (cx, cy)


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
    lens_small, lens_c = magnifier(110)
    f_title = F("Baloo2-ExtraBold.ttf", 92)
    f_tap = F("Baloo2-ExtraBold.ttf", 50)
    f_nhan = F("Baloo2-ExtraBold.ttf", 88)
    f_card = F("Baloo2-ExtraBold.ttf", 46)
    em_rice, em_wc, em_soap = emoji("🍚", 150), emoji("🚽", 130), emoji("🧼", 150)
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
                center_text(dr, W / 2, 1290, txt, fnt, WHITE, DARK, 6)

    enc = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow",
                            "-crf", "19", "-pix_fmt", "yuv420p", os.path.join(args.out, "_video.mp4")],
                           stdin=subprocess.PIPE)
    real1, real5, realh = Real(args.real, REAL_SC1), Real(args.real, REAL_SC5), Real(args.real, REAL_HAND)
    hand_bg = None
    lens_end = (0, 0)
    for fi in range(int(round(total * FPS))):
        tt = fi / FPS
        if tt < sc[2][0]:                                   # ---- cảnh 1: bé thật + tiêu đề
            frame = real1.next()
            dr = ImageDraw.Draw(frame)
            k = ease_back(tt / 0.4)
            if tt < sc[1][1] - 0.15:
                lay = Image.new("RGBA", (W, 520), (0, 0, 0, 0))
                ld = ImageDraw.Draw(lay)
                ld.rounded_rectangle((W / 2 - 110, 20, W / 2 + 110, 92), 36, fill=PINK)
                center_text(ld, W / 2, 26, TITLE.split("\n")[0], f_tap, WHITE, PINK, 0)
                center_text(ld, W / 2, 120, "\n".join(TITLE.split("\n")[1:]), f_title, WHITE, PINK, 9)
                lay = lay.resize((max(1, int(W * k)), max(1, int(520 * k))))
                paste_c(frame, lay, W / 2, 380)
            subtitle(frame, tt)
        elif tt < sc[3][0]:                                 # ---- cảnh 2: Bé Sao + kính lúp
            lt = tt - sc[2][0]
            frame = bg.copy()
            dr = ImageDraw.Draw(frame)
            for (x, y, r, ph) in sparks:
                a = 0.5 + 0.5 * math.sin(tt * 2.3 + ph)
                if a > 0.4:
                    sparkle(dr, x, y, r * a, (255, 210, 60, int(230 * a)))
            k = ease_back(lt / 0.4)
            e = env("2", tt)
            hgt = 980 * max(0.01, k)
            cy = 1000 + 14 * math.sin(lt * 4) - 20 * e
            draw_sao(frame, 470, cy, hgt, rot=3 * math.sin(lt * 2.5) + 4 * e, sq=1 + 0.03 * e)
            if lt > 0.9:  # kính lúp bật ra cạnh bàn tay vẫy của Bé Sao
                kk = ease_back((lt - 0.9) / 0.4)
                lm = lens_small.resize((max(1, int(lens_small.width * kk)), max(1, int(lens_small.height * kk))))
                lx, ly = 850 + 10 * math.sin(lt * 3), 640 + 8 * math.cos(lt * 3)
                frame.alpha_composite(lm, (int(lx - lens_c[0] * kk), int(ly - lens_c[1] * kk)))
                lens_end = (lx, ly)
            subtitle(frame, tt)
        elif tt < sc[4][0]:                                 # ---- cảnh 3: phóng to tay bé
            lt = tt - sc[3][0]
            live = realh.next()
            if hand_bg is None:
                hand_bg = live.filter(ImageFilter.GaussianBlur(22))
                ov = Image.new("RGBA", (W, H), (255, 240, 248, 120))
                hand_bg.alpha_composite(ov)
            frame = hand_bg.copy()
            k = ease(lt / 0.45)
            R = 110 + (400 - 110) * k
            cx = lens_end[0] + (540 - lens_end[0]) * k
            cy = lens_end[1] + (900 - lens_end[1]) * k
            cs = 364
            hx, hy = HAND_CENTER
            crop = live.crop((hx - cs // 2, hy - cs // 2, hx + cs // 2, hy + cs // 2)).resize(
                (int(2 * R), int(2 * R)), Image.LANCZOS)
            cd = ImageDraw.Draw(crop)
            for (gx, gy, gr, gt, col, ph) in germs:
                if lt >= gt:
                    p = ease_back((lt - gt) / 0.25) * R / 400
                    x = R + gx * R / 400 + 3 * math.sin(tt * 6 + ph)
                    y = R + gy * R / 400 + 3 * math.cos(tt * 5 + ph)
                    rr = gr * p
                    cd.ellipse((x - rr, y - rr, x + rr, y + rr), fill=col + (215,),
                               outline=tuple(int(c * 0.6) for c in col) + (255,), width=max(1, int(rr * 0.2)))
            mask = Image.new("L", crop.size, 0)
            ImageDraw.Draw(mask).ellipse((0, 0, crop.width - 1, crop.height - 1), fill=255)
            crop.putalpha(mask)
            paste_c(frame, crop, cx, cy)
            dr = ImageDraw.Draw(frame)
            dr.ellipse((cx - R, cy - R, cx + R, cy + R), outline=BLUE, width=int(R * 0.12))
            dr.arc((cx - R * 0.8, cy - R * 0.8, cx + R * 0.8, cy + R * 0.8), 200, 250,
                   fill=(255, 255, 255, 200), width=int(R * 0.06))
            hx2, hy2 = cx - R * 0.72, cy + R * 0.72
            dr.line((hx2, hy2, hx2 - R * 0.5, hy2 + R * 0.5), fill=(120, 70, 40), width=int(R * 0.3))
            if lt > 1.3:
                kk = ease_back((lt - 1.3) / 0.4)
                lay = Image.new("RGBA", (W, 200), (0, 0, 0, 0))
                ld = ImageDraw.Draw(lay)
                center_text(ld, W / 2, 30, NHAN, f_nhan, WHITE, (215, 40, 60), 9)
                lay = lay.resize((max(1, int(W * kk)), max(1, int(200 * kk))))
                paste_c(frame, lay, W / 2, 330)
        elif tt < sc[5][0]:                                 # ---- cảnh 4: Bé Sao + 2 hình
            lt = tt - sc[4][0]
            frame = bg.copy()
            e = env("4", tt)
            point = ease((tt - card_t[0]) / 0.4)
            draw_sao(frame, 300, 1030 + 12 * math.sin(lt * 4) - 18 * e, 860,
                     rot=-7 * point + 3 * math.sin(lt * 2.5) + 3 * e, sq=1 + 0.03 * e)
            for i, (ct, em, lab) in enumerate(((card_t[0], em_rice, "Trước khi ăn"),
                                               (card_t[1], em_wc, "Sau khi\nđi vệ sinh"))):
                if tt >= ct:
                    kk = ease_back((tt - ct) / 0.4)
                    card = Image.new("RGBA", (420, 330), (0, 0, 0, 0))
                    cdr = ImageDraw.Draw(card)
                    cdr.rounded_rectangle((10, 16, 410, 320), 40, fill=(200, 60, 120, 50))
                    card = card.filter(ImageFilter.GaussianBlur(6))
                    cdr = ImageDraw.Draw(card)
                    cdr.rounded_rectangle((10, 10, 410, 314), 40, fill=WHITE, outline=PINK, width=7)
                    card.alpha_composite(em, (int(210 - em.width / 2), 28))
                    center_text(cdr, 210, 190 if "\n" not in lab else 170, lab, f_card, PINK, WHITE, 0, spacing=0)
                    card = card.resize((max(1, int(420 * kk)), max(1, int(330 * kk))))
                    paste_c(frame, card, 790, 640 + i * 370)
            if tt >= soap_t:
                kk = ease_back((tt - soap_t) / 0.4)
                s = em_soap.resize((max(1, int(em_soap.width * kk)), max(1, int(em_soap.height * kk))))
                paste_c(frame, s, 560 + 6 * math.sin(tt * 5), 1130)
            subtitle(frame, tt)
        elif tt < sc[6][0]:                                 # ---- cảnh 5: bé thật
            frame = real5.next()
            subtitle(frame, tt)
        else:                                               # ---- cảnh 6: Bé Sao cười, gật đầu
            lt = tt - sc[6][0]
            frame = bg.copy()
            dr = ImageDraw.Draw(frame)
            for i, (x, y, r, ph) in enumerate(sparks):
                a = ease_back((lt - i * 0.05) / 0.3)
                if a > 0:
                    sparkle(dr, x, y, r * min(a, 1.2), (255, 210, 60, 230))
            k = ease_back(lt / 0.3)
            nod = math.sin(lt * 2 * math.pi * 1.6)
            draw_sao(frame, 540, 1000 + 20 * abs(nod), 1000 * max(0.01, k), rot=6 * nod,
                     sq=1 - 0.05 * abs(nod))
        enc.stdin.write(frame.convert("RGB").tobytes())
    for r in (real1, real5, realh):
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
