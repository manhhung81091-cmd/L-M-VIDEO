#!/usr/bin/env python3
"""Dựng video "Bé Sao tự đi vệ sinh" cho kênh Nhà Có Em Bé.

Cách dùng:
    python3 build.py --clips <thư_mục_clip> --font <thư_mục_font> --out bé-sao.mp4

Thư mục clip chứa các file có tên kết thúc bằng 01.mp4 ... 09.mp4.
Cảnh nào là ảnh tĩnh (.webp/.jpg/.png) sẽ được làm hiệu ứng zoom chậm.
Lời thoại/phụ đề sửa trong subtitles.py.
"""
import argparse
import glob
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from subtitles import SCENES, write_ass  # noqa: E402

W, H, FPS = 720, 1280, 24
XFADE = 0.4  # giây chuyển cảnh


def find_scene(clips_dir, key):
    for ext in ("mp4", "mov", "webp", "jpg", "jpeg", "png"):
        hits = sorted(glob.glob(os.path.join(clips_dir, f"*{key}.{ext}")))
        if hits:
            return hits[0]
    sys.exit(f"Không tìm thấy cảnh {key} trong {clips_dir}")


def duration(path):
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path], text=True)
    return float(out.strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clips", required=True)
    ap.add_argument("--font", required=True, help="thư mục chứa Baloo2-ExtraBold.ttf")
    ap.add_argument("--out", default="be-sao.mp4")
    ap.add_argument("--still", default=5.0, type=float, help="độ dài cảnh ảnh tĩnh (giây)")
    args = ap.parse_args()

    inputs, filters, durs = [], [], []
    n = 0  # số input đã thêm
    for i, sc in enumerate(SCENES):
        path = find_scene(args.clips, sc["key"])
        is_still = not path.endswith((".mp4", ".mov"))
        if is_still:
            d = args.still
            frames = int(d * FPS)
            inputs += ["-loop", "1", "-t", str(d), "-i", path,
                       "-f", "lavfi", "-t", str(d), "-i", "anullsrc=r=44100:cl=stereo"]
            v = n
            n += 2
            filters.append(
                f"[{v}:v]scale={W*2}:{H*2},zoompan=z='min(zoom+0.0008,1.08)':d={frames}"
                f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={FPS},"
                f"setsar=1,format=yuv420p,trim=duration={d},setpts=PTS-STARTPTS[v{i}]")
            filters.append(f"[{v+1}:a]aformat=sample_rates=44100:channel_layouts=stereo[a{i}]")
        else:
            d = duration(path)
            inputs += ["-i", path]
            idx = n
            n += 1
            filters.append(
                f"[{idx}:v]scale={W}:{H}:force_original_aspect_ratio=decrease,"
                f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,fps={FPS},setsar=1,format=yuv420p,"
                f"setpts=PTS-STARTPTS[v{i}]")
            filters.append(
                f"[{idx}:a]aformat=sample_rates=44100:channel_layouts=stereo,"
                f"asetpts=PTS-STARTPTS[a{i}]")
        durs.append(d)

    # Ghép bằng chuyển cảnh mờ dần (xfade) + hòa âm (acrossfade)
    starts, t = [0.0], durs[0]
    vprev, aprev = "v0", "a0"
    for i in range(1, len(SCENES)):
        off = t - XFADE
        starts.append(off)
        trans = SCENES[i].get("transition", "fade")
        filters.append(f"[{vprev}][v{i}]xfade=transition={trans}:duration={XFADE}:offset={off:.3f}[vx{i}]")
        filters.append(f"[{aprev}][a{i}]acrossfade=d={XFADE}[ax{i}]")
        vprev, aprev = f"vx{i}", f"ax{i}"
        t = off + durs[i]
    total = t

    ass = os.path.abspath(os.path.splitext(args.out)[0] + ".ass")
    write_ass(ass, starts, durs, total, W, H)
    filters.append(
        f"[{vprev}]subtitles='{ass}':fontsdir='{os.path.abspath(args.font)}',"
        f"fade=t=in:st=0:d=0.5,fade=t=out:st={total-0.8:.3f}:d=0.8[vout]")
    filters.append(
        f"[{aprev}]loudnorm=I=-16:TP=-1.5:LRA=11,afade=t=in:d=0.5,"
        f"afade=t=out:st={total-0.8:.3f}:d=0.8[aout]")

    cmd = ["ffmpeg", "-y", "-v", "error", *inputs,
           "-filter_complex", ";".join(filters),
           "-map", "[vout]", "-map", "[aout]",
           "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-profile:v", "high",
           "-pix_fmt", "yuv420p", "-r", str(FPS),
           "-c:a", "aac", "-b:a", "160k", "-ar", "44100",
           "-movflags", "+faststart", args.out]
    subprocess.run(cmd, check=True)
    print(f"Xong: {args.out} ({total:.1f}s)")


if __name__ == "__main__":
    main()
