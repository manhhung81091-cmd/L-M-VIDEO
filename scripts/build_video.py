#!/usr/bin/env python3
"""Clip "Ngày hội Đại đoàn kết toàn dân tộc – Ngày Văn hóa Việt Nam"
thôn Trung Thành – xã Hậu Lộc – tỉnh Thanh Hóa, 15/11/2026 (~15 phút).

Chạy:   python3 scripts/build_video.py
Kết quả: output/ngay_hoi_dai_doan_ket_2026.mp4

Nhạc nền: đặt các file nhạc (mp3/m4a/wav) vào media/music/ — chúng được phát
lần lượt theo thứ tự tên file (01_..., 02_..., 03_...), nối với nhau bằng
crossfade và lặp lại nếu chưa đủ dài. Nếu thư mục trống, script tự tạo nhạc nền nhẹ.

Cần: ffmpeg, Python 3 + Pillow + numpy.
"""
import glob
import os
import shutil
import subprocess
import textwrap
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "media", "images")
VID = os.path.join(ROOT, "media", "videos")
MUSIC_DIR = os.path.join(ROOT, "media", "music")
OUT = os.path.join(ROOT, "output")
WORK = os.path.join(OUT, "work")
FINAL = os.path.join(OUT, "ngay_hoi_dai_doan_ket_2026.mp4")

W, H, FPS = 1920, 1080, 30
TARGET = 15 * 60 + 30         # độ dài mong muốn (giây)
COVER, TITLE, OUTRO, CARD = 12.0, 8.0, 12.0, 6.0
XF = 1.2                  # độ dài mỗi hiệu ứng chuyển cảnh

FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_T = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
GOLD = (255, 205, 60)
RED = (200, 16, 30)

CROPS = {36: (0, 55, 1124, 895)}  # cắt viền đen + chữ "REDMI" của ảnh chụp màn hình

TRANSITIONS = ["fade", "smoothleft", "circleopen", "wipeleft", "slideup", "dissolve",
               "radial", "smoothright", "circlecrop", "diagtl", "hlslice", "fadewhite",
               "smoothup", "rectcrop", "wiperight", "vertopen", "pixelize", "horzopen"]

TRI_AN = [
    "Ân cần thăm hỏi sức khỏe, đời sống gia đình chính sách",
    "Trao quà, động viên các gia đình người có công với cách mạng",
    "Tri ân những người đã cống hiến cho Tổ quốc",
    "Thăm hỏi, tặng quà gia đình chính sách, người có công",
]

SECTIONS = [
    ("Đảng bộ – hạt nhân của khối đại đoàn kết", [
        (11, "Lễ trao tặng Huy hiệu Đảng đợt 19/5 và 02/9/2026 – Đảng bộ xã Hậu Lộc"),
        (37, "Lễ kết nạp đảng viên mới – Chi bộ Trung Thành, ngày 17/10/2026"),
        (38, "Phát biểu tại Lễ kết nạp đảng viên"),
        (40, "Công bố quyết định tặng Huy hiệu Đảng đợt 02/9/2026"),
        (39, "Đông đảo đảng viên tham dự buổi lễ"),
        (31, "Hội nghị tại Nhà văn hóa thôn Trung Thành"),
    ]),
    ("Uống nước nhớ nguồn – Đền ơn đáp nghĩa", [
        (n, TRI_AN[i % len(TRI_AN)]) for i, n in enumerate(
            [1, 24, 2, 3, 4, 5, 7, 8, 9, 17, 18, 21, 22, 25, 27, 28, 29, 30])
    ]),
    ("Tương thân tương ái – Lá lành đùm lá rách", [
        ("tham_01.jpg", "Thăm hỏi, động viên người bị bệnh hiểm nghèo"),
        ("tham_02.jpg", "Trao quà hỗ trợ gia đình khó khăn, neo đơn"),
        ("tham_03.jpg", "Chia sẻ, động viên người cao tuổi neo đơn"),
        ("tham_04.jpg", "Ân cần thăm hỏi, động viên gia đình có hoàn cảnh khó khăn"),
    ]),
    ("An ninh trật tự – Chung tay cùng dân ứng phó mưa lũ", [
        ("tham_05.jpg", "Tổ bảo vệ an ninh, trật tự thôn Trung Thành giúp dân di chuyển đồ đạc, ngày 17/9/2026"),
        ("tham_06.jpg", "Tuần tra, nắm tình hình ngập úng trong mưa lớn"),
        ("tham_07.jpg", "Khẩn trương ứng phó mưa lũ trên đồng ruộng"),
        ("tham_09.jpg", "Giúp nhân dân kê, di dời tài sản khỏi nước ngập"),
        ("tham_10.jpg", "Chung tay cùng bà con chống ngập"),
        ("tham_11.jpg", "Hỗ trợ di dời tài sản lên nơi cao ráo"),
        ("tham_12.jpg", "Lội nước kiểm tra các hộ dân vùng trũng"),
        ("tham_13.jpg", "Bám địa bàn, sẵn sàng hỗ trợ nhân dân"),
    ]),
    ("Mặt trận và các đoàn thể chung sức, đồng lòng", [
        (34, "Lễ kết nạp hội viên – kỷ niệm 96 năm Ngày thành lập Hội Nông dân Việt Nam"),
        (35, "Chi hội Cựu chiến binh Trung Thành kết nạp hội viên mới"),
        (16, "Giao lưu văn nghệ các CLB Liên thế hệ tự giúp nhau – Hội Người cao tuổi xã, 29/9/2026"),
        (6, "Nhân dân tham gia sinh hoạt tại nhà văn hóa"),
    ]),
    ("Phụ nữ Hậu Lộc tự tin, khỏe, đẹp", [
        (10, "Chi hội Phụ nữ trao quà cho các cháu – kỷ niệm 96 năm Ngày thành lập Hội LHPN Việt Nam"),
        (14, "Tiết mục múa áo dài chào mừng ngày 20/10"),
        (13, "Hội thi dân vũ \u201cPhụ nữ Hậu Lộc tự tin, khỏe, đẹp\u201d năm 2026"),
        (32, "Hội LHPN xã Hậu Lộc – đồng diễn áo dài"),
        (36, "Đội đồng diễn trước cổng trại Chi đội Trung Thành, ngày 15/8/2026"),
    ]),
    ("Tuổi trẻ vững bước tiến vào kỷ nguyên mới", [
        (33, "Dựng cổng trại Chi đội Trung Thành trong đêm"),
        (12, "Cổng trại Chi đội Trung Thành – \u201cTuổi trẻ xã Hậu Lộc vững bước tiến vào kỷ nguyên mới\u201d"),
        (15, "Thi kéo co sôi nổi, hào hứng"),
    ]),
    ("Chung tay xây dựng thôn xanh – sạch – đẹp", [
        (19, "Ra quân vệ sinh môi trường, ngày 20/9/2026"),
        (20, "Chung tay giữ gìn đường làng xanh – sạch – đẹp"),
    ]),
    ("Văn hóa làng – Đêm hội Trăng rằm", [
        (42, "Đêm hội Trăng rằm tại Nhà văn hóa thôn Trung Thành"),
        (43, "Đông đảo các cháu thiếu nhi và nhân dân tham dự"),
        (41, "Trao quà Trung thu cho các cháu"),
        (44, "Trao quà cho các cháu thiếu nhi"),
        (45, "Niềm vui đêm hội"),
        ("trungthu_1.mp4", "Múa lân vui Tết Trung thu"),
        ("trungthu_2.mp4", "Các cháu hào hứng đón nhận quà Trung thu"),
    ]),
]


# ---------------------------------------------------------------- tiện ích
def run(cmd):
    r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if r.returncode:
        raise SystemExit(f"ffmpeg lỗi:\n{r.stderr[-3000:]}")


def probe_dur(path):
    return float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]))


def font(path, size):
    return ImageFont.truetype(path, size)


def is_photo(it):
    return isinstance(it, int) or not it.lower().endswith(".mp4")


def load_photo(n):
    name = n if isinstance(n, str) else f"{n}.jpg"
    im = ImageOps.exif_transpose(Image.open(os.path.join(IMG, name))).convert("RGB")
    return im.crop(CROPS[n]) if n in CROPS else im


def compose(im, dim=0.35):
    """Đặt ảnh vào khung 16:9; phần thừa là chính ảnh đó làm mờ."""
    s = max(W / im.width, H / im.height)
    bg = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    bg = bg.crop(((bg.width - W) // 2, (bg.height - H) // 2,
                  (bg.width - W) // 2 + W, (bg.height - H) // 2 + H))
    bg = bg.filter(ImageFilter.GaussianBlur(40))
    bg = Image.blend(bg, Image.new("RGB", (W, H)), dim)
    s = min(W / im.width, H / im.height)
    fg = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    bg.paste(fg, ((W - fg.width) // 2, (H - fg.height) // 2))
    return bg


def centered(d, y, text, f, fill, stroke=3):
    w = d.textlength(text, font=f)
    d.text(((W - w) / 2, y), text, font=f, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0))


def caption_png(path, label, text):
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    lines = textwrap.wrap(text, 62)
    bar_h = 70 + 58 * len(lines)
    g = Image.linear_gradient("L").resize((W, bar_h + 80))
    g = g.point(lambda v: min(200, int(v * 1.6)))
    shade = Image.new("RGBA", (W, bar_h + 80), (0, 0, 0, 255))
    shade.putalpha(g)
    ov.alpha_composite(shade, (0, H - bar_h - 80))
    d = ImageDraw.Draw(ov)
    y0 = H - bar_h
    d.rectangle((80, y0 + 4, 88, H - 40), fill=GOLD)
    d.text((110, y0), label.upper(), font=font(FONT_B, 26), fill=GOLD)
    for i, ln in enumerate(lines):
        d.text((110, y0 + 38 + 58 * i), ln, font=font(FONT_B, 44), fill="white",
               stroke_width=2, stroke_fill=(0, 0, 0))
    ov.save(path)


def title_png(path, base, top, big, sub=None, size=84):
    bg = base.filter(ImageFilter.GaussianBlur(14))
    bg = Image.blend(bg, Image.new("RGB", (W, H), (60, 8, 10)), 0.6)
    d = ImageDraw.Draw(bg)
    lines = textwrap.wrap(big, 40)
    lh = int(size * 1.25)
    total = 70 + lh * len(lines) + (80 if sub else 0)
    y = (H - total) / 2
    centered(d, y, top, font(FONT_B, 40), GOLD)
    y += 70
    for ln in lines:
        centered(d, y, ln, font(FONT_T, size), "white", 4)
        y += lh
    d.rectangle((W / 2 - 180, y + 8, W / 2 + 180, y + 13), fill=GOLD)
    if sub:
        centered(d, y + 35, sub, font(FONT_R, 40), (240, 240, 240), 2)
    bg.save(path)


# ---------------------------------------------------------------- đoạn hình
KB = [  # Ken Burns luân phiên: phóng to, thu nhỏ, lia trái→phải, lia phải→trái
    ("1+0.10*on/{n}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
    ("1.10-0.10*on/{n}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
    ("1.10", "(iw-iw/zoom)*on/{n}", "ih/2-(ih/zoom/2)"),
    ("1.10", "(iw-iw/zoom)*(1-on/{n})", "ih/2-(ih/zoom/2)"),
]
ENC = ["-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
       "-r", str(FPS), "-video_track_timescale", "15360"]


def photo_seg(out, still, cap, dur, k):
    n = int(round(dur * FPS))
    z, x, y = (s.format(n=n) for s in KB[k % len(KB)])
    g = f"[0]scale={W*2}:{H*2},zoompan=z='{z}':x='{x}':y='{y}':d={n}:s={W}x{H}:fps={FPS}"
    if cap:
        g += (f"[v];[1]format=rgba,fade=in:st=1.2:d=0.8:alpha=1,"
              f"fade=out:st={dur-XF-0.9:.2f}:d=0.6:alpha=1[c];[v][c]overlay")
    run(["ffmpeg", "-y", "-i", still] + (["-loop", "1", "-t", f"{dur:.3f}", "-i", cap] if cap else [])
        + ["-filter_complex", g + ",format=yuv420p[o]", "-map", "[o]", "-t", f"{dur:.3f}", *ENC, out])


def video_seg(out, src, cap, dur):
    g = (f"[0:v]scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,"
         f"setsar=1,fps={FPS}[v];[1]format=rgba,fade=in:st=1.2:d=0.8:alpha=1,"
         f"fade=out:st=7:d=1:alpha=1[c];[v][c]overlay,format=yuv420p[o]")
    run(["ffmpeg", "-y", "-i", src, "-loop", "1", "-t", f"{dur:.3f}", "-i", cap,
         "-filter_complex", g, "-map", "[o]", "-t", f"{dur:.3f}", *ENC, out])


# ---------------------------------------------------------------- nhạc
def synth_music(path, dur, sr=48000):
    """Nhạc nền nhẹ tự tạo (dùng khi chưa có file nhạc trong media/music)."""
    t = np.zeros(int(dur * sr))
    hz = lambda m: 440 * 2 ** ((m - 69) / 12)
    prog = [[48, 55, 60, 64, 67], [45, 52, 57, 60, 64], [41, 48, 53, 57, 60], [43, 50, 55, 59, 62]]
    bar = 4.0
    for b in range(int(dur / bar) + 1):
        ch, s0, L = prog[b % 4], int(b * bar * sr), int((bar + 2) * sr)
        tt = np.arange(L) / sr
        env = np.minimum(1, tt / 1.2) * np.exp(-tt / 6) * np.clip((bar + 2 - tt) / 1.5, 0, 1)
        seg = sum(np.sin(2 * np.pi * hz(m) * tt) + 0.3 * np.sin(4 * np.pi * hz(m) * tt)
                  for m in ch[:4]) * 0.05 * env
        for i, m in enumerate([ch[2], ch[3], ch[4], ch[3]] * 2):
            st = int(i * 0.5 * sr)
            tn = np.arange(L - st) / sr
            seg[st:] += np.sin(2 * np.pi * hz(m + 12) * tn) * np.exp(-tn * 2.8) * 0.06
        e = min(len(t), s0 + L)
        t[s0:e] += seg[: e - s0]
    for dly, gain in ((0.23, 0.35), (0.41, 0.25), (0.67, 0.15)):
        k = int(dly * sr)
        t[k:] += t[:-k] * gain
    t = t / np.max(np.abs(t)) * 0.8
    with wave.open(path, "wb") as w:
        w.setnchannels(2), w.setsampwidth(2), w.setframerate(sr)
        w.writeframes((np.stack([t, t], 1) * 32767).astype(np.int16).tobytes())


def music_files():
    return sorted(f for f in glob.glob(os.path.join(MUSIC_DIR, "*"))
                   if f.lower().endswith((".mp3", ".m4a", ".wav", ".aac", ".ogg", ".flac", ".webm", ".opus")))


def music_bed(path, dur):
    """Nối các bài trong media/music bằng crossfade, lặp đến đủ `dur` giây."""
    files = music_files()
    if not files:
        synth_music(path, dur)
        return "nhạc tự tạo"
    total, seq = 0.0, []
    while total < dur + 5:
        for f in files:
            seq.append(f)
            total += probe_dur(f) - 4
    args, g = [], ""
    for i, f in enumerate(seq):
        args += ["-i", f]
        g += f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.5[m{i}];"
    prev = "m0"
    for i in range(1, len(seq)):
        g += f"[{prev}][m{i}]acrossfade=d=4:c1=tri:c2=tri[x{i}];"
        prev = f"x{i}"
    g += f"[{prev}]atrim=0:{dur:.2f},afade=in:d=2,afade=out:st={dur-5:.2f}:d=5[o]"
    run(["ffmpeg", "-y", *args, "-filter_complex", g, "-map", "[o]", "-ar", "48000", path])
    return ", ".join(os.path.basename(f) for f in files)


# ---------------------------------------------------------------- dựng
def main():
    os.makedirs(WORK, exist_ok=True)
    target = TARGET
    if music_files():  # clip dài đúng bằng các bài hát nối lại
        target = sum(probe_dur(f) for f in music_files()) - 4 * (len(music_files()) - 1)
        print(f"Độ dài theo nhạc: {target/60:.2f} phút")
    photos = [it for _, items in SECTIONS for it, _ in items if is_photo(it)]
    clips = [it for _, items in SECTIONS for it, _ in items if not is_photo(it)]
    vid_total = sum(probe_dur(os.path.join(VID, c)) for c in clips)
    n_segs = 3 + len(SECTIONS) + len(photos) + len(clips)       # bìa, tựa, kết + thẻ phần + …
    fixed = COVER + TITLE + OUTRO + CARD * len(SECTIONS) + vid_total
    pd = round((target + XF * (n_segs - 1) - fixed) / len(photos), 2)
    print(f"{len(photos)} ảnh × {pd}s, {len(clips)} video ({vid_total:.0f}s), {n_segs} cảnh")

    segs = []  # (file, duration, audio_src or None)

    cover = load_photo("cover.jpg")
    p = os.path.join(WORK, "cover.png")
    compose(cover, dim=0.25).save(p)
    o = os.path.join(WORK, "s000_cover.mp4")
    photo_seg(o, p, None, COVER, 0)
    segs.append((o, COVER, None))

    p = os.path.join(WORK, "title.png")
    title_png(p, compose(load_photo(42)), "THÔN TRUNG THÀNH – XÃ HẬU LỘC – TỈNH THANH HÓA",
              "Ngày hội Đại đoàn kết toàn dân tộc", "Ngày Văn hóa Việt Nam • 15/11/2026", size=80)
    o = os.path.join(WORK, "s001_title.mp4")
    photo_seg(o, p, None, TITLE, 1)
    segs.append((o, TITLE, None))

    k = 2
    for si, (name, items) in enumerate(SECTIONS, 1):
        first = next(it for it, _ in items if is_photo(it))
        p = os.path.join(WORK, f"card{si}.png")
        title_png(p, compose(load_photo(first)), f"PHẦN {si}", name)
        o = os.path.join(WORK, f"s{si}00_card.mp4")
        photo_seg(o, p, None, CARD, 0)
        segs.append((o, CARD, None))
        for j, (it, text) in enumerate(items, 1):
            cap = os.path.join(WORK, f"cap{si}_{j}.png")
            caption_png(cap, name, text)
            o = os.path.join(WORK, f"s{si}{j:02d}.mp4")
            if is_photo(it):
                still = os.path.join(WORK, f"img_{os.path.splitext(str(it))[0]}.png")
                compose(load_photo(it)).save(still)
                photo_seg(o, still, cap, pd, k)
                k += 1
                segs.append((o, pd, None))
            else:
                src = os.path.join(VID, it)
                d = probe_dur(src)
                video_seg(o, src, cap, d)
                segs.append((o, d, src))
            print(f"  xong {os.path.basename(o)}", flush=True)

    p = os.path.join(WORK, "outro.png")
    title_png(p, compose(cover), "THÔN TRUNG THÀNH – XÃ HẬU LỘC",
              "Đoàn kết – Đổi mới – Sáng tạo", "Xây dựng quê hương giàu đẹp", size=80)
    o = os.path.join(WORK, "s999_outro.mp4")
    photo_seg(o, p, None, OUTRO, 1)
    segs.append((o, OUTRO, None))

    # ---- ghép hình bằng các hiệu ứng chuyển cảnh xfade
    args, g, starts = [], "", []
    t = 0.0
    for i, (f, d, _) in enumerate(segs):
        args += ["-i", f]
        starts.append(t)
        t += d - XF
    total = t + XF
    prev = "0:v"
    for i in range(1, len(segs)):
        off = starts[i]
        tr = TRANSITIONS[(i - 1) % len(TRANSITIONS)]
        g += f"[{prev}][{i}:v]xfade=transition={tr}:duration={XF}:offset={off:.3f}[v{i}];"
        prev = f"v{i}"
    g += f"[{prev}]fade=in:d=1.5,fade=out:st={total-2.5:.2f}:d=2.5,format=yuv420p[o]"
    video = os.path.join(WORK, "video_only.mp4")
    print("Đang ghép các cảnh với hiệu ứng chuyển cảnh…", flush=True)
    run(["ffmpeg", "-y", *args, "-filter_complex", g, "-map", "[o]", *ENC, video])

    # ---- âm thanh: nhạc nền + tiếng gốc của video (nhạc hạ nhỏ khi có video)
    music = os.path.join(WORK, "music.wav")
    used = music_bed(music, total)
    ducks = [(starts[i], starts[i] + d) for i, (_, d, a) in enumerate(segs) if a]
    duck = "+".join(f"between(t,{a+0.5:.2f},{b-0.5:.2f})" for a, b in ducks) or "0"
    args, g = ["-i", video, "-i", music], f"[1:a]volume='if({duck},0.18,0.9)':eval=frame[m];"
    mix = ["[m]"]
    for n, (i, (_, d, a)) in enumerate([(i, s) for i, s in enumerate(segs) if s[2]], 2):
        args += ["-i", a]
        ms = int(starts[i] * 1000)
        g += (f"[{n}:a]aresample=48000,aformat=channel_layouts=stereo,afade=in:d={XF},"
              f"afade=out:st={d-XF:.2f}:d={XF},adelay={ms}|{ms},volume=1.3[c{n}];")
        mix.append(f"[c{n}]")
    g += f"{''.join(mix)}amix=inputs={len(mix)}:duration=first:normalize=0,alimiter=limit=0.95[a]"
    run(["ffmpeg", "-y", *args, "-filter_complex", g, "-map", "0:v", "-map", "[a]",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", f"{total:.2f}",
         "-movflags", "+faststart", FINAL])
    preview = FINAL.replace(".mp4", "_xem_thu_720p.mp4")
    run(["ffmpeg", "-y", "-i", FINAL, "-vf", "scale=1280:720", "-c:v", "libx264", "-preset",
         "veryfast", "-crf", "27", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", preview])
    print(f"Nhạc: {used}")
    print(f"HOÀN THÀNH: {FINAL}  ({probe_dur(FINAL)/60:.2f} phút)")


if __name__ == "__main__":
    if not shutil.which("ffmpeg"):
        raise SystemExit("Chưa cài ffmpeg")
    main()
