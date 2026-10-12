#!/usr/bin/env python3
"""Video quảng cáo ngắn: Bọt vệ sinh Bé Sao (TikTok 9:16, 1080x1920, 30fps).

    python3 ad.py --clip be_rua_tay.mp4 --product product.png --model <piper.onnx> --out xuat

Cấu trúc:
  A. Clip bé (hook) + chữ mở đầu; sản phẩm "bay" vào góc như sticker.
  B. Sản phẩm phóng to ra giữa trên nền hồng mờ; tên thương hiệu; 3 huy hiệu
     lấy NGUYÊN từ nhãn chai (Dịu nhẹ an toàn / pH 5.5 cân bằng / Hương thơm dễ chịu).
  C. Lời kêu gọi đặt mua.
Mọi lời quảng cáo chỉ dùng thông tin in trên nhãn sản phẩm.
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
ROOT = os.path.dirname(HERE)
FONT_XB = os.path.join(ROOT, "video-01-con-lon-roi", "fonts", "Baloo2-ExtraBold.ttf")
FONT_SB = os.path.join(ROOT, "video-01-con-lon-roi", "fonts", "Baloo2-SemiBold.ttf")
NHAC = os.path.join(ROOT, "video-01-con-lon-roi", "nhac.py")
W, H, FPS = 1080, 1920, 30
PINK = (236, 72, 140)
PINK_L = (255, 214, 230)
BLUE = (22, 130, 220)
WHITE = (255, 255, 255)

# Lời đọc (giọng mẹ). "pH 5.5" viết theo cách đọc để giọng AI đọc đúng.
VO = [
    ("a", "Con gái mình giờ đã tự giữ vệ sinh sạch sẽ mỗi ngày."),
    ("b", "Bọt vệ sinh Bé Sao. Dịu nhẹ cho bé, sạch thơm mỗi ngày."),
    ("c", "Pê hát năm phẩy năm cân bằng, hương thơm dễ chịu."),
    ("d", "Mẹ đặt ngay cho bé nhé!"),
]
HOOK = "Bé tự giữ vệ sinh\nmỗi ngày rồi nè!"
BADGES = [("Dịu nhẹ", "an toàn"), ("pH 5.5", "cân bằng"), ("Hương thơm", "dễ chịu")]
CTA = "Mẹ đặt ngay cho bé nhé!"


# ---------- tiện ích ----------
def ease_out_back(t):
    t = min(max(t, 0.0), 1.0)
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


def ease_in_out(t):
    t = min(max(t, 0.0), 1.0)
    return 0.5 - 0.5 * math.cos(math.pi * t)


def font(path, size):
    return ImageFont.truetype(path, size)


def wav_dur(p):
    with wave.open(p) as w:
        return w.getnframes() / w.getframerate()


def text_center(draw, cx, y, text, fnt, fill, stroke, sw, spacing=6):
    bb = draw.multiline_textbbox((0, 0), text, font=fnt, align="center",
                                 stroke_width=sw, spacing=spacing)
    x = cx - (bb[2] - bb[0]) / 2 - bb[0]
    draw.multiline_text((x, y), text, font=fnt, fill=fill, align="center",
                        stroke_width=sw, stroke_fill=stroke, spacing=spacing)


def sparkle(draw, cx, cy, r, color):
    k = r * 0.28
    pts = [(cx, cy - r), (cx + k, cy - k), (cx + r, cy), (cx + k, cy + k),
           (cx, cy + r), (cx - k, cy + k), (cx - r, cy), (cx - k, cy - k)]
    draw.polygon(pts, fill=color)


def glow_disc(size, color, blur):
    im = Image.new("RGBA", (size, size), color[:3] + (0,))  # nền cùng màu, chỉ alpha = 0 -> không viền xám
    d = ImageDraw.Draw(im)
    m = blur * 2
    d.ellipse((m, m, size - m, size - m), fill=color)
    return im.filter(ImageFilter.GaussianBlur(blur))


def paste_center(base, im, cx, cy):
    base.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


# ---------- âm thanh ----------
def make_vo(model, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    trim = ("silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
            "silenceremove=start_periods=1:start_threshold=-45dB,areverse")
    for k, text in VO:
        wav = os.path.join(out_dir, k + ".wav")
        if os.path.exists(wav):
            continue
        raw = wav + ".raw.wav"
        subprocess.run([sys.executable, "-m", "piper", "-m", model, "-f", raw,
                        "--length-scale", "1.05"], input=text, text=True, check=True,
                       capture_output=True)
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", raw, "-af",
                        "aresample=48000," + trim, "-ac", "1", wav], check=True)
        os.remove(raw)


def synth_sfx(path, times, total, sr=48000):
    """Tiếng 'ting' lấp lánh nhỏ khi sản phẩm/huy hiệu xuất hiện."""
    out = np.zeros(int(total * sr))
    for t0, f0 in times:
        n = int(0.5 * sr)
        t = np.arange(n) / sr
        s = sum(np.sin(2 * np.pi * f0 * m * t) * a for m, a in ((1, 1), (2.01, .4), (3.02, .15)))
        s *= np.exp(-t * 9) * 0.25
        i = int(t0 * sr)
        out[i:i + n] += s[: max(0, len(out) - i)]
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((np.clip(out, -1, 1) * 32767).astype("<i2").tobytes())


# ---------- dựng ----------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clip", required=True)
    ap.add_argument("--product", required=True, help="PNG sản phẩm đã tách nền")
    ap.add_argument("--model", required=True, help="giọng Piper .onnx")
    ap.add_argument("--out", required=True)
    ap.add_argument("--name", default="BeSao_QuangCao_BotVeSinh")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    work = os.path.join(args.out, "stems")
    os.makedirs(work, exist_ok=True)

    make_vo(args.model, work)
    d = {k: wav_dur(os.path.join(work, k + ".wav")) for k, _ in VO}

    # --- mốc thời gian theo giọng đọc ---
    ta = 0.35
    a_end = max(5.0, ta + d["a"] + 0.35)              # hết phần clip
    t_sticker = a_end - 1.5                            # sản phẩm bay vào góc
    t_trans = a_end                                    # phóng ra giữa (0.6s)
    tb = a_end + 0.55
    tc = tb + d["b"] + 0.25
    td = tc + d["c"] + 0.45
    total = td + d["d"] + 1.3
    vo_starts = {"a": ta, "b": tb, "c": tc, "d": td}
    b_text = VO[1][1]
    t_badge = [tb + d["b"] * (b_text.index("Dịu") / len(b_text)),
               tc,
               tc + d["c"] * 0.55]
    t_cta = td - 0.15

    # --- tài nguyên hình ---
    prod = Image.open(args.product).convert("RGBA")
    pw, ph = prod.size
    f_hook = font(FONT_XB, 92)
    f_small = font(FONT_SB, 64)
    f_brand = font(FONT_XB, 190)
    f_b1 = font(FONT_XB, 44)
    f_b2 = font(FONT_SB, 36)
    f_cta = font(FONT_XB, 66)

    # khung hình clip (30fps, 1080x1920)
    raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", args.clip, "-vf",
                          f"scale={W}:{H}:flags=lanczos,fps={FPS}", "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], check=True, capture_output=True).stdout
    frames = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
    n_clip = len(frames)

    def clip_frame(t):
        i = min(int(t * FPS), n_clip - 1)
        return Image.fromarray(frames[i]).convert("RGBA")

    # nền phần B: khung cuối làm mờ + phủ hồng
    last = clip_frame(a_end).filter(ImageFilter.GaussianBlur(28))
    pink = Image.new("RGBA", (W, H))
    g = np.linspace(0, 1, H)[:, None]
    top, bot = np.array([255, 236, 244]), np.array([255, 196, 222])
    grad = (top * (1 - g) + bot * g).astype(np.uint8)
    pink = Image.fromarray(np.repeat(grad[:, None, :], W, 1).reshape(H, W, 3)).convert("RGBA")
    pink.putalpha(205)
    bg_b = last.copy()
    bg_b.alpha_composite(pink)
    halo = glow_disc(900, (255, 255, 255, 200), 60)

    rng = np.random.default_rng(3)
    sparks = [(rng.uniform(40, W - 40), rng.uniform(150, 1500), rng.uniform(10, 26),
               rng.uniform(0, 6.28), rng.uniform(1.5, 3.0)) for _ in range(16)]

    # vị trí sản phẩm: sticker (phần A) -> packshot (phần B)
    st_h, st_cx, st_cy = 430, 800, 1230
    pk_h, pk_cx, pk_cy = 900, 375, 950

    enc = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "rawvideo",
                            "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-c:v", "libx264", "-preset", "slow", "-crf", "18",
                            "-pix_fmt", "yuv420p", os.path.join(work, "video_only.mp4")],
                           stdin=subprocess.PIPE)
    n_total = int(round(total * FPS))
    for fi in range(n_total):
        t = fi / FPS
        # ----- nền -----
        if t < t_trans:
            frame = clip_frame(t)
        else:
            k = ease_in_out((t - t_trans) / 0.6)
            frame = Image.blend(clip_frame(min(t, a_end)), bg_b, k) if k < 1 else bg_b.copy()
        draw = ImageDraw.Draw(frame)

        # ----- phần A: chữ mở đầu -----
        if t < t_trans + 0.3:
            a_in = ease_out_back(t / 0.35)
            a_out = 1 - ease_in_out((t - t_trans) / 0.3) if t > t_trans else 1
            if a_in * a_out > 0.02:
                layer = Image.new("RGBA", (W, 420), (0, 0, 0, 0))
                text_center(ImageDraw.Draw(layer), W / 2, 30, HOOK, f_hook, WHITE, PINK, 9)
                s = max(0.01, a_in)
                layer = layer.resize((max(1, int(W * s)), max(1, int(420 * s))))
                if a_out < 1:
                    layer.putalpha(layer.getchannel("A").point(lambda v: int(v * a_out)))
                paste_center(frame, layer, W / 2, 330)

        # ----- sản phẩm -----
        if t >= t_sticker:
            if t < t_trans:
                p = ease_out_back((t - t_sticker) / 0.45)
                hh, cx, cy, rot = st_h * p, st_cx, st_cy, -8 + 3 * math.sin(t * 3)
            else:
                k = ease_in_out((t - t_trans) / 0.6)
                hh = st_h + (pk_h - st_h) * k
                cx = st_cx + (pk_cx - st_cx) * k
                cy = st_cy + (pk_cy - st_cy) * k + 14 * math.sin((t - t_trans) * 2.2) * k
                rot = -8 * (1 - k)
            if hh > 4:
                if t >= t_trans:
                    hs = int(hh * 1.05)
                    paste_center(frame, halo.resize((hs, hs)), cx, cy)
                else:
                    gs = int(hh * 1.15)
                    paste_center(frame, glow_disc(max(gs, 8), (255, 255, 255, 230), max(2, gs // 14)), cx, cy)
                im = prod.resize((max(1, int(pw * hh / ph)), max(1, int(hh))), Image.LANCZOS)
                if abs(rot) > 0.3:
                    im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
                shadow = Image.new("RGBA", (int(im.width * 0.8), max(8, int(hh * 0.06))), (0, 0, 0, 0))
                ImageDraw.Draw(shadow).ellipse((0, 0, shadow.width - 1, shadow.height - 1), fill=(160, 40, 90, 70))
                shadow = shadow.filter(ImageFilter.GaussianBlur(8))
                paste_center(frame, shadow, cx, cy + hh / 2 - 6)
                paste_center(frame, im, cx, cy)
                draw = ImageDraw.Draw(frame)

        # ----- phần B: thương hiệu + huy hiệu + lấp lánh -----
        if t >= t_trans + 0.2:
            k = ease_out_back((t - t_trans - 0.2) / 0.5)
            layer = Image.new("RGBA", (W, 420), (0, 0, 0, 0))
            ld = ImageDraw.Draw(layer)
            text_center(ld, W / 2, 10, "Bọt vệ sinh", f_small, PINK, WHITE, 6)
            text_center(ld, W / 2, 70, "Bé Sao", f_brand, BLUE, WHITE, 12)
            s = max(0.01, k)
            layer = layer.resize((max(1, int(W * s)), max(1, int(420 * s))))
            paste_center(frame, layer, W / 2, 330)
            for (x, y, r, ph0, sp) in sparks:
                a = 0.5 + 0.5 * math.sin(t * sp + ph0)
                if a > 0.35 and not (pk_cx - 260 < x < pk_cx + 260 and 520 < y < 1480):
                    sparkle(draw, x, y + 6 * math.sin(t + ph0), r * a, (255, 214, 64, int(255 * a)))
            for i, (l1, l2) in enumerate(BADGES):
                if t >= t_badge[i]:
                    k = ease_out_back((t - t_badge[i]) / 0.4)
                    bw, bh = 360, 140
                    pill = Image.new("RGBA", (bw + 30, bh + 30), (0, 0, 0, 0))
                    pd = ImageDraw.Draw(pill)
                    pd.rounded_rectangle((15, 19, bw + 15, bh + 19), 70, fill=(200, 40, 110, 60))
                    pill = pill.filter(ImageFilter.GaussianBlur(5))
                    pd = ImageDraw.Draw(pill)
                    pd.rounded_rectangle((15, 15, bw + 15, bh + 15), 70, fill=WHITE, outline=PINK, width=6)
                    sparkle(pd, 62, 85, 24, (255, 196, 40, 255))
                    pd.text((98, 30), l1, font=f_b1, fill=PINK)
                    pd.text((98, 84), l2, font=f_b2, fill=(90, 70, 90))
                    s = max(0.01, k)
                    pill = pill.resize((max(1, int(pill.width * s)), max(1, int(pill.height * s))))
                    paste_center(frame, pill, 768, 740 + i * 200)

        # ----- phần C: lời kêu gọi -----
        if t >= t_cta:
            k = ease_out_back((t - t_cta) / 0.45)
            pulse = 1 + 0.035 * math.sin((t - t_cta) * 7) * min(1, (t - t_cta))
            bw, bh = 860, 130
            ban = Image.new("RGBA", (bw + 40, bh + 40), (0, 0, 0, 0))
            bd = ImageDraw.Draw(ban)
            bd.rounded_rectangle((20, 26, bw + 20, bh + 26), 65, fill=(150, 20, 80, 90))
            ban = ban.filter(ImageFilter.GaussianBlur(6))
            bd = ImageDraw.Draw(ban)
            bd.rounded_rectangle((20, 20, bw + 20, bh + 20), 65, fill=PINK, outline=WHITE, width=6)
            text_center(bd, (bw + 40) / 2, 34, CTA, f_cta, WHITE, (170, 30, 90), 3)
            s = max(0.01, k * pulse)
            ban = ban.resize((max(1, int(ban.width * s)), max(1, int(ban.height * s))))
            paste_center(frame, ban, W / 2, 1470)

        enc.stdin.write(frame.convert("RGB").tobytes())
    enc.stdin.close()
    enc.wait()

    # --- âm thanh ---
    sfx = os.path.join(work, "sfx_ting.wav")
    synth_sfx(sfx, [(t_sticker, 1568), (t_trans + 0.1, 2093)] +
              [(tb_, 1760) for tb_ in t_badge] + [(t_cta, 2349)], total)
    music = os.path.join(work, "nhac_nen.wav")
    subprocess.run([sys.executable, NHAC, "--out", music, "--dur", f"{total:.3f}",
                    "--bpm", "96", "--warm-from", f"{t_trans:.3f}"], check=True)
    inp, fl = ["-i", os.path.join(work, "video_only.mp4")], []
    for i, (k, _) in enumerate(VO):
        inp += ["-i", os.path.join(work, k + ".wav")]
        fl.append(f"[{i + 1}:a]adelay={int(vo_starts[k] * 1000)}[v{i}]")
    n = len(VO) + 1
    inp += ["-i", music, "-i", sfx, "-i", args.clip]
    fl.append("".join(f"[v{i}]" for i in range(len(VO))) +
              f"amix=inputs={len(VO)}:normalize=0,apad,atrim=0:{total:.3f},"
              "acompressor=threshold=-20dB:ratio=2.5,loudnorm=I=-16:TP=-2[vo]")
    fl.append("[vo]asplit=2[vo1][vo2]")
    fl.append(f"[{n}:a]volume=-18dB[m]")
    fl.append("[m][vo2]sidechaincompress=threshold=0.03:ratio=4:attack=30:release=400,"
              f"afade=t=out:st={total - 1.2:.3f}:d=1.2[mus]")
    fl.append(f"[{n + 1}:a]volume=-10dB[sfx]")
    fl.append(f"[{n + 2}:a]highpass=f=900,atrim=0:{a_end:.3f},afade=t=out:st={a_end - 0.5:.3f}:d=0.5,"
              f"volume=-24dB,apad,atrim=0:{total:.3f}[nuoc]")
    fl.append("[vo1][mus][sfx][nuoc]amix=inputs=4:normalize=0,"
              "loudnorm=I=-14:TP=-1.5:LRA=9,aresample=48000[a]")
    mp4 = os.path.join(args.out, args.name + ".mp4")
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", *inp, "-filter_complex",
                    ";".join(fl), "-map", "0:v", "-map", "[a]", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-t", f"{total:.3f}",
                    "-movflags", "+faststart", mp4], check=True)
    print(f"Xong: {mp4} ({total:.2f}s)")
    print(f"  A clip+hook 0–{a_end:.2f} | sticker {t_sticker:.2f} | B packshot {t_trans:.2f}"
          f" | huy hiệu {', '.join(f'{x:.2f}' for x in t_badge)} | CTA {t_cta:.2f}")


if __name__ == "__main__":
    main()
