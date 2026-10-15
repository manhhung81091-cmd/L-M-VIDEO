---
name: edit-video-ai
description: Edit videos with ffmpeg and auto-generate subtitles with faster-whisper — cut/trim, join clips, resize to 9:16 (TikTok/Reels/Shorts), add background music, burn in Vietnamese or other subtitles, extract audio, compress. Use when the user asks to edit, cut, join, subtitle, or convert a video, or types /edit-video-ai.
---

# Edit video with AI

Reply to the user in their language (usually Vietnamese).

## 1. Find the tools

```bash
python3 .claude/skills/edit-video-ai/scripts/find_tools.py
```

It prints `FFMPEG=`, `FFPROBE=` and `WHISPER_PYTHON=`. It prefers `~/video-tools`
(installed by `setup-mac.sh` / `setup-windows.bat` in the repo root) and falls back to `PATH`.

- `FFMPEG` empty → on the user's own computer, tell them to run the setup script for their OS
  (see `README.md`); in a cloud/Linux container, install ffmpeg with the package manager.
- `WHISPER_PYTHON` empty and subtitles are needed → `python3 -m pip install faster-whisper`, then rerun.

Use the printed paths in every command below (written as `ffmpeg`, `ffprobe`, `$WHISPER_PYTHON`).

## 2. Understand the request and the input

- Get the input file(s). If the user hasn't given one, ask for it.
- Inspect it first:
  `ffprobe -v error -show_entries format=duration:stream=codec_type,codec_name,width,height,r_frame_rate -of compact INPUT`
- If the request is vague ("make it nicer for TikTok"), state the concrete plan in one or two lines
  (e.g. "9:16, burned-in Vietnamese subtitles, louder audio") and proceed.
- Never overwrite the input. Write outputs next to it as `<name>_edited.mp4` (or a name describing the edit).

## 3. Recipes

Default output encoding (works everywhere, including phones):
`-c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart`
(written below as `$ENC`).

| Task | Command |
|---|---|
| Cut a segment | `ffmpeg -ss 00:00:10 -to 00:01:30 -i IN $ENC OUT` |
| Join clips (same format) | write `list.txt` with lines `file 'a.mp4'`, then `ffmpeg -f concat -safe 0 -i list.txt -c copy OUT` (re-encode with `$ENC` if formats differ) |
| 9:16 with blurred background | `ffmpeg -i IN -filter_complex "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20[bg];[0:v]scale=1080:1920:force_original_aspect_ratio=decrease[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2" $ENC OUT` |
| 9:16 center crop | `ffmpeg -i IN -vf "crop=ih*9/16:ih,scale=1080:1920" $ENC OUT` |
| Background music | `ffmpeg -i IN -stream_loop -1 -i MUSIC -filter_complex "[1:a]volume=0.15[m];[0:a][m]amix=inputs=2:duration=first[a]" -map 0:v -map "[a]" $ENC OUT` |
| Normalize loudness | `ffmpeg -i IN -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:v copy -c:a aac -b:a 192k OUT` |
| Remove audio | `ffmpeg -i IN -an -c:v copy OUT` |
| Extract audio | `ffmpeg -i IN -vn -c:a libmp3lame -q:a 2 OUT.mp3` |
| Speed ×1.25 | `ffmpeg -i IN -filter_complex "[0:v]setpts=PTS/1.25[v];[0:a]atempo=1.25[a]" -map "[v]" -map "[a]" $ENC OUT` |
| Compress | `$ENC` with `-crf 26`, add `-vf scale=-2:720` if still too big |
| Thumbnail | `ffmpeg -ss 00:00:05 -i IN -frames:v 1 OUT.jpg` |

## 4. Subtitles

1. Transcribe (model `medium` is the default; use `small` if the machine is slow, `large-v3` for best accuracy):
   ```bash
   $WHISPER_PYTHON .claude/skills/edit-video-ai/scripts/transcribe.py IN -o IN.srt --language vi
   ```
   Use `--max-chars 32` for vertical videos so lines fit.
2. Read the `.srt` and fix obvious mistakes (names, diacritics, technical terms) before burning in.
3. Burn in:
   ```bash
   ffmpeg -i IN -vf "subtitles=IN.srt:force_style='FontName=Arial,FontSize=14,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=0,MarginV=60,Alignment=2'" $ENC OUT
   ```
   For 9:16, apply the resize first and burn subtitles in a second pass (or chain filters: resize, then `subtitles=`).
   Or give a soft subtitle track instead: `ffmpeg -i IN -i IN.srt -c copy -c:s mov_text OUT`.

## 5. Check and report

- Run `ffprobe` on the output: check duration, resolution and that audio exists.
- For visual edits, grab one frame (`-frames:v 1`) and look at it before saying it's done.
- Tell the user where the output file is, what changed, and its duration/size. If anything failed, show the ffmpeg error.
