#!/usr/bin/env python3
"""Dựng Video 02 — Một câu nói của con khiến mẹ đứng hình! (Nhà Có Em Bé).

    python3 giong.py --model <piper.onnx> --out <vo>      # hoặc tự đặt <id>.wav thu thật
    python3 build.py --media <tư_liệu> --vo <vo> --out <thư_mục_xuất>

<tư_liệu> chứa Canh_01..06.mp4 (thiếu clip thì dùng Canh_NN.png + zoom nhẹ).
Xuất: MP4 1080x1920 30fps, phụ đề .srt/.ass, timeline.csv, stems âm thanh.
"""
import argparse
import csv
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
V01 = os.path.join(os.path.dirname(HERE), "video-01-con-lon-roi")
sys.path.insert(0, HERE)
from kich_ban import SCENES  # noqa: E402

W, H, FPS = 1080, 1920, 30
LEAD = 0.25      # thoại vào sau đầu cảnh
GAP = 0.30       # nghỉ giữa 2 câu trong cùng cảnh
TAIL = 0.45      # nghỉ sau câu cuối trước khi cắt
MUSIC_DB = -20
SFX_DB = -26
BPM = 84         # nhạc vui ấm hơn video 01


def run(cmd):
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", *cmd], check=True)


def duration(path):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                   "-of", "csv=p=0", path], text=True)
    return float(out.strip())


def ts_ass(t):
    m, s = divmod(max(0.0, t), 60)
    return f"0:{int(m):02d}:{s:05.2f}"


def ts_srt(t):
    ms = int(round(max(0.0, t) * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def plan(media, vo_dir):
    rows, t = [], 0.0
    for sc in SCENES:
        clip = os.path.join(media, f"Canh_{sc['key']}.mp4")
        src = clip if os.path.exists(clip) else os.path.join(media, f"Canh_{sc['key']}.png")
        xin = sc.get("in", 0.0)
        start = t - xin
        lead = sc.get("lead", LEAD)
        cur = start + xin + lead
        lines = []
        for lid, role, text in sc["lines"]:
            f = os.path.join(vo_dir, lid + ".wav")
            d = duration(f)
            lines.append(dict(id=lid, role=role, text=text, file=f, start=cur, dur=d))
            cur += d + GAP
        need = (cur - GAP + TAIL - start) if lines else 0
        seg = max(sc["dur"] + xin, need)
        rows.append(dict(sc, src=src, start=start, seg=seg, xin=xin, vo=lines))
        t = start + seg
    return rows, t


def video_filter(r, i):
    seg = r["seg"]
    z0, z1 = r.get("zoom", (1.0, 1.0))
    f = []
    if r["src"].endswith(".png"):
        z0, z1 = r.get("zoom", (1.0, 1.04))
        f.append(f"loop=loop=-1:size=1,fps={FPS}")
    else:
        src_len = duration(r["src"])
        if seg > src_len - 0.02:  # chậm lại vừa đủ, không đứng hình
            f.append(f"setpts={seg / (src_len - 0.05):.4f}*PTS")
        f.append(f"fps={FPS}")
    f.append(f"trim=duration={seg:.3f},setpts=PTS-STARTPTS")
    ze = f"({z0}+({z1}-{z0})*t/{seg:.3f})"
    f.append(f"scale=w='2*trunc({W}*{ze}/2)':h='2*trunc({H}*{ze}/2)':eval=frame:flags=lanczos")
    f.append(f"crop={W}:{H}:(iw-{W})/2:(ih-{H})/2")
    f.append("unsharp=5:5:0.35")
    f.append(f"setsar=1,format=yuv420p,settb=1/{FPS}")
    return f"[{i}:v]" + ",".join(f) + f"[v{i}]"


def write_subs(rows, total, ass_path, srt_path):
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Baloo 2 ExtraBold,70,&H00FFFFFF,&H00FFFFFF,&H00302830,&H78000000,0,0,0,0,100,100,0,0,1,5,2,2,120,120,500,1
Style: Hoi,Baloo 2 ExtraBold,84,&H00FFFFFF,&H00FFFFFF,&H00602A8C,&H50000000,0,0,0,0,100,100,0,0,1,7,3,2,90,90,520,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev, srt = [], []
    pop = r"{\fad(80,80)\t(0,140,\fscx104\fscy104)\t(140,260,\fscx100\fscy100)}"
    for r in rows:
        end_scene = r["start"] + r["seg"]
        for k, ln in enumerate(r["vo"]):
            a = ln["start"] - 0.05
            nxt = r["vo"][k + 1]["start"] - 0.05 if k + 1 < len(r["vo"]) else end_scene - 0.05
            b = min(ln["start"] + ln["dur"] + 0.35, nxt)
            ev.append(f"Dialogue: 2,{ts_ass(a)},{ts_ass(b)},Sub,,0,0,0,,{pop}{ln['text']}")
            srt.append((a, b, ln["text"]))
        if r.get("cau_hoi"):
            a = r["start"] + r["xin"] + 0.1
            ev.append(f"Dialogue: 3,{ts_ass(a)},{ts_ass(total)},Hoi,,0,0,0,,"
                      f"{{\\fad(350,0)}}{r['cau_hoi']}")
            srt.append((a, total, r["cau_hoi"].replace("\\N", " ")))
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
    ap.add_argument("--name", default="NhaCoEmBe_Video02_MotCauNoi")
    args = ap.parse_args()
    stems = os.path.join(args.out, "stems")
    os.makedirs(stems, exist_ok=True)

    rows, total = plan(args.media, args.vo)
    lines = [ln for r in rows for ln in r["vo"]]

    # 1. Giọng thoại (bé + mẹ) đặt đúng mốc
    inp, f = [], []
    for k, ln in enumerate(lines):
        inp += ["-i", ln["file"]]
        f.append(f"[{k}:a]aformat=sample_rates=48000:channel_layouts=mono,"
                 f"adelay={int(ln['start'] * 1000)}[d{k}]")
    f.append("".join(f"[d{k}]" for k in range(len(lines))) +
             f"amix=inputs={len(lines)}:normalize=0,apad,atrim=0:{total:.3f},highpass=f=80,"
             "acompressor=threshold=-20dB:ratio=2.5:attack=5:release=120,"
             "loudnorm=I=-16:TP=-2:LRA=7[vo]")
    vo_wav = os.path.join(stems, "giong_thoai.wav")
    run([*inp, "-filter_complex", ";".join(f), "-map", "[vo]", "-ar", "48000", vo_wav])

    # 2. Nhạc nền piano tự tổng hợp, ấm hơn từ cảnh 05
    music_wav = os.path.join(stems, "nhac_nen.wav")
    warm = next(r["start"] for r in rows if r["key"] == "05")
    subprocess.run([sys.executable, os.path.join(V01, "nhac.py"), "--out", music_wav,
                    "--dur", f"{total:.3f}", "--warm-from", f"{warm:.3f}", "--bpm", str(BPM)],
                   check=True)

    # 3. Tiếng nước rất nhẹ ở cảnh 02 (âm thanh gốc clip)
    sfx_wav = os.path.join(stems, "sfx_nuoc.wav")
    r2 = next(r for r in rows if r.get("sfx"))
    if r2["src"].endswith(".mp4"):
        run(["-i", r2["src"], "-af",
             f"highpass=f=900,atrim=0:{r2['seg']:.3f},afade=t=in:d=0.2,"
             f"afade=t=out:st={r2['seg'] - 0.3:.3f}:d=0.3,volume={SFX_DB}dB,"
             f"adelay={int(r2['start'] * 1000)}:all=1,apad,atrim=0:{total:.3f}",
             "-ar", "48000", "-ac", "2", sfx_wav])
    else:
        run(["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", f"{total:.3f}", sfx_wav])

    # 4. Phụ đề + câu hỏi cuối
    ass = os.path.join(args.out, args.name + ".ass")
    srt = os.path.join(args.out, args.name + ".srt")
    write_subs(rows, total, ass, srt)

    # 5. Hình + âm thanh
    inputs, fl = [], []
    for i, r in enumerate(rows):
        if r["src"].endswith(".png"):
            inputs += ["-loop", "1", "-t", f"{r['seg']:.3f}"]
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
    fl.append(f"[{cur}]subtitles='{ass}':fontsdir='{os.path.join(V01, 'fonts')}'[vout]")
    n = len(rows)
    inputs += ["-i", vo_wav, "-i", music_wav, "-i", sfx_wav]
    fl.append(f"[{n}:a]asplit=2[vo1][vo2]")
    fl.append(f"[{n + 1}:a]volume={MUSIC_DB}dB[mus]")
    fl.append("[mus][vo2]sidechaincompress=threshold=0.03:ratio=4:attack=30:release=400[duck]")
    fl.append(f"[duck]afade=t=out:st={total - 1.5:.3f}:d=1.5[mus2]")
    fl.append(f"[vo1][mus2][{n + 2}:a]amix=inputs=3:normalize=0,"
              "loudnorm=I=-14:TP=-1.5:LRA=9,aresample=48000[aout]")
    mp4 = os.path.join(args.out, args.name + ".mp4")
    run([*inputs, "-filter_complex", ";".join(fl), "-map", "[vout]", "-map", "[aout]",
         "-t", f"{total:.3f}", "-r", str(FPS),
         "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-profile:v", "high",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", mp4])

    # 6. Timeline
    with open(os.path.join(args.out, "timeline.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["Cảnh", "Tư liệu", "Bắt đầu (s)", "Kết thúc (s)", "Chuyển cảnh vào",
                    "Câu", "Vai", "Thoại bắt đầu (s)", "Thoại dài (s)", "Lời thoại"])
        for r in rows:
            trans = f"hòa tan {r['xin']}s" if r["xin"] else "cắt thẳng"
            base = [r["key"], os.path.basename(r["src"]), f"{r['start']:.2f}",
                    f"{r['start'] + r['seg']:.2f}", trans]
            if not r["vo"]:
                w.writerow(base + ["", "", "", "", "(chữ: " + r.get("cau_hoi", "").replace("\\N", " ") + ")"])
            for ln in r["vo"]:
                w.writerow(base + [ln["id"], "Bé" if ln["role"] == "be" else "Mẹ",
                                   f"{ln['start']:.2f}", f"{ln['dur']:.2f}", ln["text"]])
    print(f"Xong: {mp4}  ({total:.2f}s)")
    for r in rows:
        print(f"  Cảnh {r['key']}: {r['start']:6.2f} → {r['start'] + r['seg']:6.2f} ({r['seg']:.2f}s)")


if __name__ == "__main__":
    main()
