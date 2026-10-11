#!/usr/bin/env python3
"""Dựng Video 01 — Con lớn rồi, mẹ không thể làm thay mãi (Nhà Có Em Bé).

    python3 tts.py  --out <vo>                        # giọng đọc (hoặc tự đặt NN.wav thu thật)
    python3 build.py --media <tư_liệu> --vo <vo> --out <thư_mục_xuất>

<tư_liệu> chứa Canh_01..09.mp4 (clip chuyển động); thiếu clip nào thì dùng Canh_NN.png
(zoom/pan nhẹ). Xuất: MP4 1080x1920 30fps + phụ đề .srt/.ass + timeline .csv + các stem âm thanh.
"""
import argparse
import csv
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from kich_ban import SCENES  # noqa: E402

W, H, FPS = 1080, 1920, 30
LEAD = 0.30     # lời đọc vào sau đầu cảnh
LEAD_FIRST = 0.15
TAIL = 0.55     # nghỉ sau lời đọc trước khi cắt
MUSIC_DB = -21  # nhạc nền so với giọng (trước ducking)
SFX_DB = -24    # tiếng nước cảnh 04 (rất nhỏ)


def run(cmd):
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", *cmd], check=True)


def duration(path):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                   "-of", "csv=p=0", path], text=True)
    return float(out.strip())


def ts_ass(t):
    t = max(0.0, t)
    m, s = divmod(t, 60)
    return f"0:{int(m):02d}:{s:05.2f}"


def ts_srt(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def plan(media, vo_dir):
    """Tính thời lượng từng cảnh (kéo dài nếu lời đọc dài hơn timeline)."""
    rows, t = [], 0.0
    for i, sc in enumerate(SCENES):
        clip = os.path.join(media, f"Canh_{sc['key']}.mp4")
        img = os.path.join(media, f"Canh_{sc['key']}.png")
        src = clip if os.path.exists(clip) else img
        vo = os.path.join(vo_dir, sc["key"] + ".wav")
        vo_len = duration(vo) if sc["vo"] and os.path.exists(vo) else 0.0
        lead = LEAD_FIRST if i == 0 else LEAD
        xin = sc.get("in_d", 0.0) if sc.get("in") else 0.0
        d = max(sc["dur"] + xin, xin + lead + vo_len + TAIL)
        start = t - xin  # cảnh hòa tan bắt đầu chồng lên cảnh trước
        rows.append(dict(sc, src=src, vo_file=vo if vo_len else "", vo_len=vo_len,
                         seg=d, start=start, show=start + xin, xin=xin,
                         vo_start=start + xin + lead if vo_len else None))
        t = start + d
    return rows, t


def video_filter(r, i):
    src_len = duration(r["src"]) if r["src"].endswith(".mp4") else None
    seg = r["seg"]
    z0, z1 = r.get("zoom", (1.0, 1.0))
    f = []
    if src_len is None:  # ảnh tĩnh -> zoom nhẹ
        z0, z1 = r.get("zoom", (1.0, 1.04))
        f.append(f"loop=loop=-1:size=1,fps={FPS}")
    else:
        if seg > src_len - 0.02:  # chậm lại vừa đủ thay vì đứng hình
            f.append(f"setpts={seg / (src_len - 0.05):.4f}*PTS")
        f.append(f"fps={FPS}")
    f.append(f"trim=duration={seg:.3f},setpts=PTS-STARTPTS")
    # zoom mượt: scale theo thời gian rồi crop giữa (không dùng zoompan để tránh rung)
    ze = f"({z0}+({z1}-{z0})*t/{seg:.3f})"
    f.append(f"scale=w='2*trunc({W}*{ze}/2)':h='2*trunc({H}*{ze}/2)':eval=frame:flags=lanczos")
    f.append(f"crop={W}:{H}:(iw-{W})/2:(ih-{H})/2")
    f.append("unsharp=5:5:0.35")
    if r.get("warm"):
        f.append("colorbalance=rs=0.04:gs=0.01:bs=-0.05:rm=0.03:bm=-0.03")
    f.append(f"setsar=1,format=yuv420p,settb=1/{FPS}")
    return f"[{i}:v]" + ",".join(f) + f"[v{i}]"


def write_subs(rows, total, ass_path, srt_path):
    font_sub, font_hl = "Baloo 2 SemiBold", "Baloo 2 ExtraBold"
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,{font_sub},68,&H00FFFFFF,&H00FFFFFF,&H00302830,&H78000000,0,0,0,0,100,100,0,0,1,4.5,2,2,120,120,470,1
Style: Nhan,{font_hl},58,&H00FFFFFF,&H00FFFFFF,&H00602A8C,&H50000000,0,0,0,0,100,100,2,0,1,5,1.5,2,120,120,650,1
Style: Kenh,{font_hl},104,&H00FFFFFF,&H00FFFFFF,&H00602A8C,&H50000000,0,0,0,0,100,100,4,0,1,7,3,8,80,80,560,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev, srt = [], []
    for r in rows:
        if r["key"] == "09":
            ev.append(f"Dialogue: 1,{ts_ass(r['show'] + 0.15)},{ts_ass(total)},Kenh,,0,0,0,,"
                      f"{{\\fad(450,0)}}{r['nhan']}")
            continue
        a, b = r["show"] + 0.15, r["start"] + r["seg"] - 0.12
        ev.append(f"Dialogue: 1,{ts_ass(a)},{ts_ass(b)},Nhan,,0,0,0,,{{\\fad(220,160)}}{r['nhan']}")
        if not r["vo_len"]:
            continue
        # câu dài (cảnh 08) chia theo câu, thời gian tỉ lệ số ký tự
        parts = [p.strip() + "." for p in r["vo"].split(". ") if p.strip()]
        parts[-1] = parts[-1].rstrip(".") + ("." if r["vo"].endswith(".") else "")
        if len(parts) == 1:
            parts = [r["vo"]]
        total_chars = sum(len(p) for p in parts)
        t = r["vo_start"] - 0.08
        end_all = min(r["vo_start"] + r["vo_len"] + 0.35, r["start"] + r["seg"] - 0.05)
        span = end_all - t
        for p in parts:
            d = span * len(p) / total_chars
            ev.append(f"Dialogue: 2,{ts_ass(t)},{ts_ass(t + d - 0.04)},Sub,,0,0,0,,{p}")
            srt.append((t, t + d - 0.04, p))
            t += d
    with open(ass_path, "w", encoding="utf-8") as fh:
        fh.write(head + "\n".join(ev) + "\n")
    with open(srt_path, "w", encoding="utf-8") as fh:
        for n, (a, b, p) in enumerate(srt, 1):
            fh.write(f"{n}\n{ts_srt(a)} --> {ts_srt(b)}\n{p}\n\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--media", required=True)
    ap.add_argument("--vo", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--name", default="NhaCoEmBe_Video01_ConLonRoi")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    stems = os.path.join(args.out, "stems")
    os.makedirs(stems, exist_ok=True)

    rows, total = plan(args.media, args.vo)

    # --- 1. Stem giọng đọc liền mạch ---
    vo_inputs, vo_f = [], []
    for r in [r for r in rows if r["vo_len"]]:
        k = len(vo_inputs) // 2
        vo_inputs += ["-i", r["vo_file"]]
        ms = int(r["vo_start"] * 1000)
        vo_f.append(f"[{k}:a]aformat=sample_rates=48000:channel_layouts=mono,adelay={ms}[d{k}]")
    nvo = len(vo_inputs) // 2
    vo_f.append("".join(f"[d{k}]" for k in range(nvo)) +
                f"amix=inputs={nvo}:normalize=0,apad,atrim=0:{total:.3f},"
                "highpass=f=80,acompressor=threshold=-20dB:ratio=2.5:attack=5:release=120,"
                "loudnorm=I=-16:TP=-2:LRA=7[vo]")
    vo_wav = os.path.join(stems, "giong_doc.wav")
    run([*vo_inputs, "-filter_complex", ";".join(vo_f), "-map", "[vo]", "-ar", "48000", vo_wav])

    # --- 2. Nhạc nền (tự tổng hợp), ấm hơn từ cảnh 07 ---
    music_wav = os.path.join(stems, "nhac_nen.wav")
    warm = next(r["show"] for r in rows if r["key"] == "07")
    subprocess.run([sys.executable, os.path.join(HERE, "nhac.py"), "--out", music_wav,
                    "--dur", f"{total:.3f}", "--warm-from", f"{warm:.3f}"], check=True)

    # --- 3. SFX nước rửa tay (âm thanh gốc clip 04, rất nhỏ) ---
    r4 = next(r for r in rows if r["key"] == "04")
    sfx_wav = os.path.join(stems, "sfx_nuoc.wav")
    if r4["src"].endswith(".mp4") and r4.get("keep_audio"):
        run(["-i", r4["src"], "-af",
             f"highpass=f=900,atrim=0:{r4['seg']:.3f},afade=t=in:d=0.3,"
             f"afade=t=out:st={r4['seg'] - 0.4:.3f}:d=0.4,volume={SFX_DB}dB,"
             f"adelay={int(r4['start'] * 1000)}:all=1,apad,atrim=0:{total:.3f}",
             "-ar", "48000", "-ac", "2", sfx_wav])
    else:
        run(["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", f"{total:.3f}", sfx_wav])

    # --- 4. Phụ đề ---
    ass = os.path.join(args.out, args.name + ".ass")
    srt = os.path.join(args.out, args.name + ".srt")
    write_subs(rows, total, ass, srt)

    # --- 5. Hình + ghép + âm thanh ---
    inputs, fl = [], []
    for i, r in enumerate(rows):
        if r["src"].endswith(".png"):
            inputs += ["-loop", "1", "-t", f"{r['seg']:.3f}", "-i", r["src"]]
        else:
            inputs += ["-i", r["src"]]
        fl.append(video_filter(r, i))
    cur, t_end = "v0", rows[0]["seg"]
    for i in range(1, len(rows)):
        r = rows[i]
        if r["xin"]:
            fl.append(f"[{cur}][v{i}]xfade=transition=dissolve:duration={r['xin']}:"
                      f"offset={t_end - r['xin']:.3f}[c{i}]")
        else:
            fl.append(f"[{cur}][v{i}]concat=n=2:v=1:a=0,settb=1/{FPS}[c{i}]")
        cur, t_end = f"c{i}", r["start"] + r["seg"]
    fontsdir = os.path.join(HERE, "fonts")
    fl.append(f"[{cur}]subtitles='{ass}':fontsdir='{fontsdir}'[vout]")

    n = len(rows)
    inputs += ["-i", vo_wav, "-i", music_wav, "-i", sfx_wav]
    fl.append(f"[{n}:a]asplit=2[vo1][vo2]")
    fl.append(f"[{n + 1}:a]volume={MUSIC_DB}dB[mus]")
    fl.append("[mus][vo2]sidechaincompress=threshold=0.03:ratio=4:attack=40:release=500[duck]")
    fl.append(f"[duck]afade=t=out:st={total - 1.5:.3f}:d=1.5[mus2]")
    fl.append(f"[vo1][mus2][{n + 2}:a]amix=inputs=3:normalize=0,"
              "loudnorm=I=-14:TP=-1.5:LRA=9,aresample=48000[aout]")
    mp4 = os.path.join(args.out, args.name + ".mp4")
    run([*inputs, "-filter_complex", ";".join(fl), "-map", "[vout]", "-map", "[aout]",
         "-t", f"{total:.3f}", "-r", str(FPS),
         "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-profile:v", "high",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", mp4])

    # --- 6. Timeline (EDL dạng bảng) ---
    with open(os.path.join(args.out, "timeline.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["Cảnh", "Tư liệu", "Bắt đầu (s)", "Kết thúc (s)", "Thời lượng (s)",
                    "Chuyển cảnh vào", "Lời đọc bắt đầu (s)", "Lời đọc dài (s)", "Lời đọc", "Chữ nhấn"])
        for r in rows:
            w.writerow([r["key"], os.path.basename(r["src"]), f"{r['start']:.2f}",
                        f"{r['start'] + r['seg']:.2f}", f"{r['seg']:.2f}",
                        f"hòa tan {r['xin']}s" if r["xin"] else "cắt thẳng",
                        f"{r['vo_start']:.2f}" if r["vo_start"] is not None else "",
                        f"{r['vo_len']:.2f}" if r["vo_len"] else "", r["vo"], r["nhan"]])
    print(f"Xong: {mp4}  ({total:.2f}s)")
    for r in rows:
        print(f"  Cảnh {r['key']}: {r['start']:6.2f} → {r['start'] + r['seg']:6.2f}  "
              f"({r['seg']:.2f}s, lời {r['vo_len']:.2f}s)  {os.path.basename(r['src'])}")


if __name__ == "__main__":
    main()
