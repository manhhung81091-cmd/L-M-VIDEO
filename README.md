# L-M-VIDEO: bộ công cụ dựng video bằng AI

Các file cài đặt tự động cho máy tính của bạn:

| Máy | Cách chạy |
|---|---|
| **Windows** | Tải cả `setup-windows.bat` và `setup-windows.ps1` về cùng một thư mục, rồi **bấm đúp** vào `setup-windows.bat`. Nếu hiện hộp thoại hỏi quyền, bấm **Yes**. |
| **macOS** (Apple Silicon hoặc Intel) | Tải `setup-mac.sh` về thư mục Downloads, mở ứng dụng **Terminal**, gõ `bash ~/Downloads/setup-mac.sh` rồi nhấn Enter. |

Các file này sẽ làm lần lượt:

1. Nhận diện hệ điều hành và loại chip.
2. Tạo thư mục `video-tools/bin` trong thư mục người dùng.
3. Cài **ffmpeg** và **ffprobe**: ưu tiên Homebrew (Mac) hoặc winget/scoop/choco (Windows); nếu không có thì tải bản chạy sẵn đúng loại máy.
4. Cài Python (nếu máy chưa có), tạo môi trường `video-tools/whisper-venv` và cài **faster-whisper**.
5. Tải mô hình nhận dạng giọng nói **medium** (khoảng 1,5 GB, chỉ tải một lần) và chạy thử.
6. In bảng tổng kết: mục nào ổn, mục nào chưa ổn.

Chạy lại file bao nhiêu lần cũng được: phần đã cài xong sẽ không bị hỏng.

## Lệnh `/edit-video-ai` trong Claude Code

Repo có sẵn skill `.claude/skills/edit-video-ai`. Mở repo này trong Claude Code rồi gõ `/edit-video-ai` kèm yêu cầu, ví dụ:

> /edit-video-ai cắt video.mp4 từ 0:10 đến 1:30, đổi sang khung dọc 9:16 và gắn phụ đề tiếng Việt

Claude sẽ dùng ffmpeg và faster-whisper (do các file cài đặt ở trên cài vào `~/video-tools`) để:

- Cắt, ghép, tăng tốc, nén video, tách âm thanh, chụp ảnh bìa
- Đổi sang khung dọc 9:16 cho TikTok/Reels/Shorts (nền mờ hoặc cắt giữa)
- Chèn nhạc nền, cân bằng âm lượng
- Tự tạo phụ đề `.srt` từ giọng nói, sửa lỗi chính tả rồi gắn thẳng vào video

File gốc không bao giờ bị ghi đè; video mới được lưu cạnh file gốc.
