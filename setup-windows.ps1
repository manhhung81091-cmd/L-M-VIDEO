# Cài đặt công cụ dựng video bằng AI cho Windows.
# Cách chạy dễ nhất: bấm đúp vào file "setup-windows.bat" nằm cùng thư mục.
$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

$Tools = Join-Path $env:USERPROFILE "video-tools"
$Bin   = Join-Path $Tools "bin"
$Venv  = Join-Path $Tools "whisper-venv"

function Ok($m)   { Write-Host "[OK] $m" -ForegroundColor Green }
function Warn($m) { Write-Host "[!]  $m" -ForegroundColor Yellow }
function Step($m) { Write-Host "`n=== $m ===" -ForegroundColor Cyan }
function Has($c)  { [bool](Get-Command $c -ErrorAction SilentlyContinue) }
function Refresh-Path {
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                [Environment]::GetEnvironmentVariable("Path", "User")
}

# 1. Hệ điều hành và chip
Step "1. Kiem tra may"
$arch = $env:PROCESSOR_ARCHITECTURE
$os = (Get-CimInstance Win32_OperatingSystem).Caption
Ok "Ban dang dung $os, kien truc $arch."

# 2. Thư mục
Step "2. Tao thu muc $Bin"
New-Item -ItemType Directory -Force -Path $Bin | Out-Null
Ok "Da tao $Bin"

# 3. ffmpeg / ffprobe
Step "3. Cai ffmpeg"
$ffOk = $false
if (Has winget) {
    Write-Host "Dung winget de cai ffmpeg (neu hien hop thoai hoi quyen, hay bam Yes)..."
    winget install -e --id Gyan.FFmpeg --accept-source-agreements --accept-package-agreements
    Refresh-Path
    $ffOk = Has ffmpeg
} elseif (Has scoop) {
    scoop install ffmpeg; Refresh-Path; $ffOk = Has ffmpeg
} elseif (Has choco) {
    choco install ffmpeg -y; Refresh-Path; $ffOk = Has ffmpeg
}

if ($ffOk) {
    $src = Split-Path (Get-Command ffmpeg).Source
    Copy-Item (Join-Path $src "ffmpeg.exe"), (Join-Path $src "ffprobe.exe") $Bin -Force -ErrorAction SilentlyContinue
} else {
    Write-Host "Khong co trinh quan ly goi (hoac cai loi) -> tai ban ffmpeg chay san cho Windows x64..."
    $zip = Join-Path $env:TEMP "ffmpeg.zip"
    $ext = Join-Path $env:TEMP "ffmpeg-extract"
    try {
        Invoke-WebRequest "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip" -OutFile $zip
        Remove-Item $ext -Recurse -Force -ErrorAction SilentlyContinue
        Expand-Archive $zip $ext -Force
        Get-ChildItem $ext -Recurse -Include ffmpeg.exe, ffprobe.exe | Copy-Item -Destination $Bin -Force
    } catch { Warn "Tai ffmpeg that bai: $_ . Kiem tra mang roi chay lai." }
}

# Thêm bin vào PATH của người dùng
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*video-tools\bin*") {
    [Environment]::SetEnvironmentVariable("Path", "$Bin;$userPath", "User")
}
$env:Path = "$Bin;$env:Path"

$ffmpeg = Join-Path $Bin "ffmpeg.exe"
if (Test-Path $ffmpeg) { Ok ((& $ffmpeg -version | Select-Object -First 1)) } else { Warn "ffmpeg chua chay duoc." }

# 4. Python + faster-whisper
Step "4. Cai Python va faster-whisper"
function Find-Python {
    foreach ($v in "3.12", "3.11", "3.10") {
        if (Has py) { & py "-$v" -c "import sys" 2>$null; if ($LASTEXITCODE -eq 0) { return @("py", "-$v") } }
    }
    if (Has python) {
        & python -c "import sys; sys.exit(0 if sys.version_info >= (3,9) else 1)" 2>$null
        if ($LASTEXITCODE -eq 0) { return @("python") }
    }
    return $null
}
$py = Find-Python
if (-not $py) {
    if (Has winget) {
        Write-Host "May chua co Python -> cai Python 3.11 bang winget..."
        winget install -e --id Python.Python.3.11 --accept-source-agreements --accept-package-agreements
        Refresh-Path
        $py = Find-Python
    }
    if (-not $py) {
        Warn "Chua cai duoc Python. Hay tai tai https://www.python.org/downloads/ , khi cai nho tick 'Add python.exe to PATH', roi chay lai file nay."
        Read-Host "Nhan Enter de thoat"; exit 1
    }
}
$pyExe = $py[0]; $pyArgs = @($py | Select-Object -Skip 1)
Ok ("Dung Python: " + (& $pyExe @pyArgs --version))

$venvPy = Join-Path $Venv "Scripts\python.exe"
if (-not (Test-Path $venvPy)) { & $pyExe @pyArgs -m venv $Venv }
& $venvPy -m pip install -q --upgrade pip
& $venvPy -m pip install -q faster-whisper
if ($LASTEXITCODE -eq 0) { Ok "Da cai faster-whisper" } else { Warn "Cai faster-whisper loi." }

# 5. Tải mô hình medium và chạy thử
Step "5. Tai mo hinh 'medium' (~1.5 GB, chi tai mot lan) va chay thu"
$wav = Join-Path $Tools "test.wav"
& $ffmpeg -loglevel error -y -f lavfi -i "sine=frequency=440:duration=3" -ar 16000 -ac 1 $wav
$testPy = Join-Path $Tools "test_whisper.py"
@"
from faster_whisper import WhisperModel
m = WhisperModel("medium", device="cpu", compute_type="int8")
segs, info = m.transcribe(r"$wav")
list(segs)
print("[OK] Mo hinh medium da tai xong va chay duoc.")
"@ | Set-Content -Encoding UTF8 $testPy
& $venvPy $testPy
if ($LASTEXITCODE -ne 0) { Warn "Chua tai duoc mo hinh. Kiem tra mang roi chay lai file nay." }

# 7. Tổng kết
Step "Tong ket"
Write-Host "He dieu hanh : $os ($arch)"
if (Test-Path $ffmpeg) { Ok "ffmpeg/ffprobe chay duoc" } else { Warn "ffmpeg CHUA on" }
& $venvPy -c "import faster_whisper" 2>$null
if ($LASTEXITCODE -eq 0) { Ok "faster-whisper da cai" } else { Warn "faster-whisper CHUA cai" }
$hub = Join-Path $env:USERPROFILE ".cache\huggingface\hub"
if (Get-ChildItem $hub -Filter "*medium*" -ErrorAction SilentlyContinue) { Ok "Mo hinh medium da co tren may" } else { Warn "Mo hinh medium CHUA tai xong" }
Read-Host "`nXong. Nhan Enter de dong cua so"
