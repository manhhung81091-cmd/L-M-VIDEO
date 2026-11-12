#!/usr/bin/env python3
"""Dựng video tổng hợp hoạt động khu Trung Thành – xã Hậu Lộc (~15 phút).

Chạy:  python3 scripts/build_video.py
Kết quả: output/video_trung_thanh_2026.mp4

Cần: ffmpeg, Python 3 + Pillow + numpy.
Đặt nhạc nền riêng (mp3/m4a/wav) vào media/music/ thì script dùng file đó
thay cho nhạc nền tự tạo.
"""
import glob
import os
import shutil
import subprocess
import textwrap

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "media", "images")
VID = os.path.join(ROOT, "media", "videos")
MUSIC_DIR = os.path.join(ROOT, "media", "music")
OUT = os.path.join(ROOT, "output")
WORK = os.path.join(OUT, "work")

W, H, FPS = 1920, 1080, 30
TARGET = 15 * 60  # giây
INTRO, OUTRO, CARD = 10.0, 10.0, 5.0
FADE = 0.6

FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_T = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
GOLD = (245, 196, 66)

# Cắt bỏ viền thừa (left, top, right, bottom) cho ảnh chụp màn hình.
CROPS = {36: (0, 55, 1124, 895)}

TRI_AN = [
    "Ân cần thăm hỏi sức khỏe, đời sống gia đình chính sách",
    "Trao quà, động viên các gia đình người có công với cách mạng",
    "Tri ân những người đã cống hiến cho Tổ quốc",
    "Thăm hỏi, tặng quà gia đình chính sách, người có công",
]

SECTIONS = [
    ("Phần 1", "Công tác xây dựng Đảng", [
        (11, "Lễ trao tặng Huy hiệu Đảng đợt 19/5 và 02/9/2026 – Đảng bộ xã Hậu Lộc"),
        (37, "Lễ kết nạp đảng viên mới – Chi bộ Trung Thành, ngày 17/10/2026"),
        (38, "Phát biểu tại Lễ kết nạp đảng viên"),
        (40, "Công bố quyết định tặng Huy hiệu Đảng đợt 02/9/2026"),
        (39, "Đông đảo đảng viên tham dự buổi lễ"),
        (31, "Hội nghị tại Nhà văn hóa khu Trung Thành"),
    ]),
    ("Phần 2", "Uống nước nhớ nguồn – Đền ơn đáp nghĩa", [
        (n, TRI_AN[i % len(TRI_AN)]) for i, n in enumerate(
            [1, 24, 2, 3, 4, 5, 7, 8, 9, 17, 18, 21, 22, 25, 27, 28, 29, 30])
    ]),
    ("Phần 3", "Hoạt động các đoàn thể", [
        (34, "Lễ kết nạp hội viên – kỷ niệm 96 năm Ngày thành lập Hội Nông dân Việt Nam"),
        (35, "Chi hội Cựu chiến binh Trung Thành kết nạp hội viên mới"),
        (16, "Giao lưu văn nghệ các CLB Liên thế hệ tự giúp nhau – Hội Người cao tuổi xã, 29/9/2026"),
        (6, "Nhân dân tham gia sinh hoạt tại nhà văn hóa"),
    ]),
    ("Phần 4", "Phụ nữ Hậu Lộc tự tin, khỏe, đẹp", [
        (10, "Chi hội Phụ nữ trao quà cho các cháu – kỷ niệm 96 năm Ngày thành lập Hội LHPN Việt Nam"),
        (14, "Tiết mục múa áo dài chào mừng ngày 20/10"),
        (13, "Hội thi dân vũ “Phụ nữ Hậu Lộc tự tin, khỏe, đẹp” năm 2026"),
        (32, "Hội LHPN xã Hậu Lộc – đồng diễn áo dài"),
        (36, "Đội đồng diễn trước cổng trại Chi đội Trung Thành, ngày 15/8/2026"),
    ]),
    ("Phần 5", "Tuổi trẻ vững bước tiến vào kỷ nguyên mới", [
        (33, "Dựng cổng trại Chi đội Trung Thành trong đêm"),
        (12, "Cổng trại Chi đội Trung Thành – “Tuổi trẻ xã Hậu Lộc vững bước tiến vào kỷ nguyên mới”"),
        (15, "Thi kéo co sôi nổi, hào hứng"),
    ]),
    ("Phần 6", "Chung tay vì môi trường xanh – sạch – đẹp", [
        (19, "Ra quân vệ sinh môi trường, ngày 20/9/2026"),
        (20, "Chung tay giữ gìn đường làng xanh – sạch – đẹp"),
    ]),
    ("Phần 7", "Đêm hội Trăng rằm khu Trung Thành", [
        (42, "Đêm hội Trăng rằm tại Nhà văn hóa khu Trung Thành"),
        (43, "Đông đảo các cháu thiếu nhi và nhân dân tham dự"),
        (41, "Trao quà Trung thu cho các cháu"),
        (44, "Trao quà cho các cháu thiếu nhi"),
        (45, "Niềm vui đêm hội"),
        ("trungthu_1.mp4", "Múa lân vui Tết Trung thu"),
        ("trungthu_2.mp4", "Các cháu hào hứng đón nhận quà Trung thu"),
    ]),
]


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def probe_dur(path):
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path])
    return float(out)


def font(path, size):
    return ImageFont.truetype(path, size)


def load_photo(n):
    im = Image.open(os.path.join(IMG, f"{n}.jpg")).convert("RGB")
    if n in CROPS:
        im = im.crop(CROPS[n])
    return im


def compose(im):
    """Đặt ảnh vào khung 16:9, nền là chính ảnh đó làm mờ."""
    bg = im.copy()
    s = max(W / bg.width, H / bg.height)
    bg = bg.resize((int(bg.width * s) + 1, int(bg.height * s) + 1), Image.LANCZOS)
    bg = bg.crop(((bg.width - W) // 2, (bg.height - H) // 2,
                  (bg.width - W) // 2 + W, (bg.height - H) // 2 + H))
    bg = bg.filter(ImageFilter.GaussianBlur(40))
    bg = Image.blend(bg, Image.new("RGB", (W, H), (0, 0, 0)), 0.35)
    s = min(W / im.width, H / im.height)
    fg = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    bg.paste(fg, ((W - fg.width) // 2, (H - fg.height) // 2))
    return bg


def caption_png(path, label, text):
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    lines = textwrap.wrap(text, 62)
    bar_h = 70 + 58 * len(lines)
    grad = Image.new("L", (1, bar_h + 80))
    for y in range(bar_h + 80):
        grad.putpixel((0, y), int(200 * min(1, y / 80)))
    grad = grad.resize((W, bar_h + 80))
    black = Image.new("RGBA", (W, bar_h + 80), (0, 0, 0, 255))
    black.putalpha(grad)
    ov.alpha_composite(black, (0, H - bar_h - 80))
    d = ImageDraw.Draw(ov)
    y0 = H - bar_h
    d.rectangle((80, y0 + 4, 88, H - 40), fill=GOLD)
    d.text((110, y0), label.upper(), font=font(FONT_B, 26), fill=GOLD)
    for i, ln in enumerate(lines):
        d.text((110, y0 + 38 + 58 * i), ln, font=font(FONT_B, 44),
               fill="white", stroke_width=2, stroke_fill=(0, 0, 0))
    ov.save(path)


def centered(d, y, text, f, fill, stroke=3):
    w = d.textlength(text, font=f)
    d.text(((W - w) / 2, y), text, font=f, fill=fill,
           stroke_width=stroke, stroke_fill=(0, 0, 0))


def title_png(path, base, top, big, sub=None):
    bg = base.filter(ImageFilter.GaussianBlur(14))
    bg = Image.blend(bg, Image.new("RGB", (W, H), (10, 20, 40)), 0.55)
    d = ImageDraw.Draw(bg)
    fb = font(FONT_T, 84)
    lines = textwrap.wrap(big, 34)
    total = 60 + 105 * len(lines) + (70 if sub else 0)
    y = (H - total) / 2
    centered(d, y, top, font(FONT_B, 40), GOLD)
    y += 70
    for ln in lines:
        centered(d, y, ln, fb, "white", 4)
        y += 105
    d.rectangle((W / 2 - 160, y + 5, W / 2 + 160, y + 10), fill=GOLD)
    if sub:
        centered(d, y + 30, sub, font(FONT_R, 40), (235, 235, 235), 2)
    bg.save(path)


KB = [  # hiệu ứng Ken Burns luân phiên
    ("1+0.10*on/{n}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
    ("1.10-0.10*on/{n}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
    ("1.10", "(iw-iw/zoom)*on/{n}", "ih/2-(ih/zoom/2)"),
    ("1.10", "(iw-iw/zoom)*(1-on/{n})", "ih/2-(ih/zoom/2)"),
]

ENC = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p",
       "-r", str(FPS), "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2"]


def photo_seg(out, still, cap, dur, k):
    n = int(round(dur * FPS))
    z, x, y = (s.format(n=n) for s in KB[k % len(KB)])
    fo = dur - FADE
    vf = (f"[0]scale={W*2}:{H*2},zoompan=z='{z}':x='{x}':y='{y}':d={n}:s={W}x{H}:fps={FPS}[v];"
          f"[v][1]overlay,fade=in:st=0:d={FADE},fade=out:st={fo:.3f}:d={FADE},format=yuv420p[o]")
    inputs = ["-i", still] + (["-i", cap] if cap else [])
    if not cap:
        vf = vf.replace("[v][1]overlay,", "[v]null,")
    run(["ffmpeg", "-y", *inputs, "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
         "-filter_complex", vf, "-map", "[o]", "-map", f"{2 if cap else 1}:a",
         "-t", f"{dur:.3f}", *ENC, out])


def video_seg(out, src, cap, dur):
    fo = dur - FADE
    vf = (f"[0:v]scale={W}:{H}:force_original_aspect_ratio=decrease,"
          f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={FPS}[v];"
          f"[1]format=rgba,fade=out:st=6:d=1:alpha=1[c];"
          f"[v][c]overlay,fade=in:st=0:d={FADE},fade=out:st={fo:.3f}:d={FADE},format=yuv420p[o];"
          f"[0:a]afade=in:st=0:d={FADE},afade=out:st={fo:.3f}:d={FADE}[a]")
    run(["ffmpeg", "-y", "-i", src, "-loop", "1", "-t", f"{dur:.3f}", "-i", cap,
         "-filter_complex", vf, "-map", "[o]", "-map", "[a]", "-t", f"{dur:.3f}", *ENC, out])


def make_music(path, dur, sr=48000):
    """Nhạc nền nhẹ nhàng tự tạo (không vướng bản quyền)."""
    t = np.arange(int(dur * sr)) / sr
    out = np.zeros_like(t)
    hz = lambda m: 440 * 2 ** ((m - 69) / 12)
    prog = [[48, 55, 60, 64, 67], [45, 52, 57, 60, 64],
            [41, 48, 53, 57, 60], [43, 50, 55, 59, 62]]  # C – Am – F – G
    bar = 4.0
    for b in range(int(dur / bar) + 1):
        chord = prog[b % 4]
        s0 = int(b * bar * sr)
        L = int((bar + 2) * sr)
        tt = np.arange(L) / sr
        env = np.minimum(1, tt / 1.2) * np.exp(-tt / 6) * (tt < bar + 2)
        env *= np.clip((bar + 2 - tt) / 1.5, 0, 1)
        pad = sum(np.sin(2 * np.pi * hz(m) * tt) + 0.3 * np.sin(4 * np.pi * hz(m) * tt)
                  for m in chord[:4]) * 0.05 * env
        arp = np.zeros(L)
        for i, m in enumerate([chord[2], chord[3], chord[4], chord[3]] * 2):
            st = int(i * 0.5 * sr)
            tn = np.arange(L - st) / sr
            arp[st:] += (np.sin(2 * np.pi * hz(m + 12) * tn)
                         + 0.25 * np.sin(4 * np.pi * hz(m + 12) * tn)) * np.exp(-tn * 2.8) * 0.06
        seg = pad + arp
        e = min(len(out), s0 + L)
        out[s0:e] += seg[: e - s0]
    for dly, g in ((0.23, 0.35), (0.41, 0.25), (0.67, 0.15)):  # vang nhẹ
        k = int(dly * sr)
        out[k:] += out[:-k] * g
    out = np.convolve(out, np.ones(6) / 6, mode="same")
    fade = int(3 * sr)
    out[:fade] *= np.linspace(0, 1, fade)
    out[-fade:] *= np.linspace(1, 0, fade)
    out = out / np.max(np.abs(out)) * 0.8
    pcm = (np.stack([out, out], 1) * 32767).astype(np.int16)
    import wave
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def main():
    os.makedirs(WORK, exist_ok=True)
    n_photos = sum(1 for _, _, items in SECTIONS for it, _ in items if isinstance(it, int))
    vid_total = sum(probe_dur(os.path.join(VID, it)) for _, _, items in SECTIONS
                    for it, _ in items if isinstance(it, str))
    fixed = INTRO + OUTRO + CARD * len(SECTIONS) + vid_total
    pd = round((TARGET - fixed) / n_photos, 2)
    print(f"{n_photos} ảnh × {pd}s, video {vid_total:.1f}s")

    segs, ducks, t = [], [], 0.0

    def add(path, dur, duck=False):
        nonlocal t
        segs.append(path)
        if duck:
            ducks.append((t, t + dur))
        t += dur

    # Mở đầu
    p = os.path.join(WORK, "intro.png")
    title_png(p, compose(load_photo(42)), "XÃ HẬU LỘC",
              "KHU TRUNG THÀNH", "Nhìn lại những hoạt động nổi bật năm 2026")
    o = os.path.join(WORK, "s000_intro.mp4")
    photo_seg(o, p, None, INTRO, 0)
    add(o, INTRO)

    k = 1
    for si, (lab, name, items) in enumerate(SECTIONS, 1):
        first = next(it for it, _ in items if isinstance(it, int))
        p = os.path.join(WORK, f"card{si}.png")
        title_png(p, compose(load_photo(first)), lab.upper(), name)
        o = os.path.join(WORK, f"s{si}00_card.mp4")
        photo_seg(o, p, None, CARD, 0)
        add(o, CARD)
        for j, (it, text) in enumerate(items, 1):
            cap = os.path.join(WORK, f"cap{si}_{j}.png")
            caption_png(cap, name, text)
            o = os.path.join(WORK, f"s{si}{j:02d}.mp4")
            if isinstance(it, int):
                still = os.path.join(WORK, f"img{it}.png")
                compose(load_photo(it)).save(still)
                photo_seg(o, still, cap, pd, k)
                k += 1
                add(o, pd)
            else:
                d = probe_dur(os.path.join(VID, it))
                video_seg(o, os.path.join(VID, it), cap, d)
                add(o, d, duck=True)
            print(f"  xong {os.path.basename(o)}  ({t/60:.1f} phút)", flush=True)

    # Kết thúc
    p = os.path.join(WORK, "outro.png")
    title_png(p, compose(load_photo(43)), "KHU TRUNG THÀNH – XÃ HẬU LỘC",
              "Xin chân thành cảm ơn!", "Đoàn kết – Đổi mới – Sáng tạo – Xây dựng quê hương giàu đẹp")
    o = os.path.join(WORK, "s999_outro.mp4")
    photo_seg(o, p, None, OUTRO, 1)
    add(o, OUTRO)

    lst = os.path.join(WORK, "list.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{s}'\n" for s in segs)
    joined = os.path.join(WORK, "joined.mp4")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", joined])

    own = sorted(glob.glob(os.path.join(MUSIC_DIR, "*")))
    music = own[0] if own else os.path.join(WORK, "music.wav")
    if not own:
        make_music(music, t)
    duck = "+".join(f"between(t,{a:.2f},{b:.2f})" for a, b in ducks) or "0"
    final = os.path.join(OUT, "video_trung_thanh_2026.mp4")
    run(["ffmpeg", "-y", "-i", joined, "-stream_loop", "-1", "-i", music, "-filter_complex",
         f"[1:a]atrim=0:{t:.2f},volume='if({duck},0.12,0.55)':eval=frame,"
         f"afade=out:st={t-3:.2f}:d=3[m];[0:a][m]amix=inputs=2:duration=first:normalize=0[a]",
         "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
         "-movflags", "+faststart", final])
    print(f"HOÀN THÀNH: {final}  ({probe_dur(final)/60:.2f} phút)")


if __name__ == "__main__":
    if not shutil.which("ffmpeg"):
        raise SystemExit("Chưa cài ffmpeg")
    main()
