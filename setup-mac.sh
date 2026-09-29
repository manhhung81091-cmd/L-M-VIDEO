#!/bin/bash
# Cài đặt công cụ dựng video bằng AI cho macOS (Apple Silicon hoặc Intel).
# Cách chạy: mở Terminal, gõ:  bash ~/Downloads/setup-mac.sh
set -u

TOOLS="$HOME/video-tools"
BIN="$TOOLS/bin"
VENV="$TOOLS/whisper-venv"

ok()   { echo "✅ $*"; }
warn() { echo "⚠️  $*"; }
step() { echo; echo "=== $* ==="; }

# 1. Hệ điều hành và chip
step "1. Kiểm tra máy"
ARCH="$(uname -m)"
if [ "$ARCH" = "arm64" ]; then CHIP="Apple Silicon (M1/M2/M3/M4...)"; FF_ARCH="arm64"; else CHIP="Intel"; FF_ARCH="amd64"; fi
ok "Bạn đang dùng macOS $(sw_vers -productVersion), chip $CHIP."

# 2. Thư mục
step "2. Tạo thư mục $TOOLS/bin"
mkdir -p "$BIN" && ok "Đã tạo $BIN"

# Nạp Homebrew nếu đã cài nhưng chưa có trong PATH
for b in /opt/homebrew/bin/brew /usr/local/bin/brew; do
  [ -x "$b" ] && eval "$("$b" shellenv)" && break
done

# 3. ffmpeg / ffprobe
step "3. Cài ffmpeg"
if command -v brew >/dev/null 2>&1; then
  echo "Dùng Homebrew để cài ffmpeg (có thể mất vài phút)..."
  brew install ffmpeg
  ln -sf "$(brew --prefix)/bin/ffmpeg" "$BIN/ffmpeg"
  ln -sf "$(brew --prefix)/bin/ffprobe" "$BIN/ffprobe"
else
  echo "Máy chưa có Homebrew → tải bản ffmpeg chạy sẵn cho chip $CHIP..."
  TMP="$(mktemp -d)"
  for tool in ffmpeg ffprobe; do
    curl -fL --retry 3 -o "$TMP/$tool.zip" \
      "https://ffmpeg.martin-riedl.de/redirect/latest/macos/$FF_ARCH/release/$tool.zip" \
      && unzip -o -q "$TMP/$tool.zip" -d "$BIN" \
      || warn "Tải $tool thất bại. Kiểm tra mạng rồi chạy lại file này."
  done
  chmod +x "$BIN/ffmpeg" "$BIN/ffprobe" 2>/dev/null
  # Gỡ "cách ly" của macOS để máy cho phép chạy file vừa tải
  xattr -d com.apple.quarantine "$BIN/ffmpeg" "$BIN/ffprobe" 2>/dev/null
  rm -rf "$TMP"
fi

# Thêm thư mục bin vào PATH cho các lần mở Terminal sau
if ! grep -q 'video-tools/bin' "$HOME/.zshrc" 2>/dev/null; then
  echo 'export PATH="$HOME/video-tools/bin:$PATH"' >> "$HOME/.zshrc"
fi
export PATH="$BIN:$PATH"

if "$BIN/ffmpeg" -version >/dev/null 2>&1; then
  ok "$("$BIN/ffmpeg" -version | head -1)"
else
  warn "ffmpeg chưa chạy được. Nếu macOS báo 'không thể mở', vào Cài đặt hệ thống → Quyền riêng tư & Bảo mật → bấm 'Vẫn cho phép', rồi chạy lại."
fi

# 4. Python + faster-whisper
step "4. Cài Python và faster-whisper"
PY=""
for p in python3.12 python3.11 python3.10 python3; do
  if command -v "$p" >/dev/null 2>&1 && "$p" -c 'import sys; sys.exit(0 if sys.version_info >= (3,9) else 1)' 2>/dev/null; then
    PY="$(command -v "$p")"; break
  fi
done
if [ -z "$PY" ]; then
  if command -v brew >/dev/null 2>&1; then
    brew install python@3.11 && PY="$(brew --prefix)/bin/python3.11"
  else
    warn "Máy chưa có Python. Một cửa sổ có thể hiện ra đề nghị cài 'Command Line Developer Tools' — hãy bấm Cài đặt (Install), đợi xong rồi chạy lại file này."
    xcode-select --install 2>/dev/null
    exit 1
  fi
fi
ok "Dùng Python: $("$PY" --version)"

[ -x "$VENV/bin/python" ] || "$PY" -m venv "$VENV"
"$VENV/bin/pip" install -q --upgrade pip
"$VENV/bin/pip" install -q faster-whisper && ok "Đã cài faster-whisper $("$VENV/bin/python" -c 'import faster_whisper; print(faster_whisper.__version__)')"

# 5. Tải mô hình medium và chạy thử
step "5. Tải mô hình 'medium' (~1.5 GB, chỉ tải một lần) và chạy thử"
"$BIN/ffmpeg" -loglevel error -y -f lavfi -i "sine=frequency=440:duration=3" -ar 16000 -ac 1 "$TOOLS/test.wav"
"$VENV/bin/python" - <<EOF
from faster_whisper import WhisperModel
m = WhisperModel("medium", device="cpu", compute_type="int8")
segs, info = m.transcribe("$TOOLS/test.wav")
list(segs)
print("✅ Mô hình medium đã tải xong và chạy được.")
EOF
[ $? -eq 0 ] || warn "Chưa tải được mô hình. Kiểm tra kết nối mạng rồi chạy lại file này (phần đã cài sẽ được bỏ qua)."

# 7. Tổng kết
step "Tổng kết"
echo "Hệ điều hành : macOS, chip $CHIP"
"$BIN/ffmpeg" -version >/dev/null 2>&1 && ok "ffmpeg/ffprobe chạy được" || warn "ffmpeg CHƯA ổn"
"$VENV/bin/python" -c 'import faster_whisper' 2>/dev/null && ok "faster-whisper đã cài" || warn "faster-whisper CHƯA cài"
ls "$HOME/.cache/huggingface/hub" 2>/dev/null | grep -q medium && ok "Mô hình medium đã có trên máy" || warn "Mô hình medium CHƯA tải xong"
