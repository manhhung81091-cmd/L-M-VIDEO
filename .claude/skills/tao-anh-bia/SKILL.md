---
name: tao-anh-bia
description: Tạo ảnh bìa TikTok/Reels 9:16 theo bộ nhận diện Bé Sao (khung tiêu đề trắng viền xanh, ngôi sao vàng mặt cười, chữ hook xanh in hoa, dòng nhấn mạnh hồng/vàng/xanh, tia sáng, lấp lánh, bong bóng). Dùng khi người dùng gửi ảnh kèm câu hook, hoặc nhờ làm ảnh bìa, thumbnail, cover hay khung tiêu đề cho video.
---

# Tạo ảnh bìa theo nhận diện Bé Sao

Trả lời bằng tiếng Việt. Người dùng chỉ cần gửi **ảnh + câu hook**; mọi thứ còn lại do bạn quyết định theo bộ nhận diện dưới đây.

## Bộ nhận diện (giữ cố định)

- Khổ 1080x1920 (9:16). Ảnh nền được cắt vừa khung, không méo.
- Khung tiêu đề ở phía trên: tấm trắng viền xanh `#1890F0` nằm nghiêng trên tấm nền xanh gradient `#8CD0FC` → `#34A0F6`.
- Ngôi sao vàng mặt cười ở góc dưới bên trái khung (có thể đổi sang phải hoặc ẩn).
- Chữ: Open Sans đậm, IN HOA, màu xanh `#1E9BE9`. Thường 2–3 dòng: dòng mở, **một dòng nhấn mạnh**, dòng phụ nhỏ hơn.
- Màu nhấn: hồng `#F48FB4`, vàng `#FFD62E`.

## Cách làm

1. Lấy đường dẫn ảnh người dùng gửi (ảnh tải lên nằm trong thư mục `images/` mà hệ thống báo, hoặc file trong repo).
   Nếu là video: `ffmpeg -ss 1 -i video.mp4 -frames:v 1 anh.jpg` rồi dùng ảnh đó.
2. Chia hook thành 2–3 dòng ngắn (mỗi dòng tối đa khoảng 30 ký tự), giữ nguyên chữ người dùng viết, chỉ sửa chính tả nếu sai rõ ràng.
3. Chọn **một** dòng nhấn mạnh (cụm từ gây tò mò hoặc lợi ích chính) và gắn thẻ kiểu:

   | Thẻ | Trông như thế nào | Hợp với |
   |---|---|---|
   | `[hong]` | chữ trắng trong hình bầu dục hồng | cảm xúc, "ghiền", "mê" |
   | `[the]` | chữ trắng trong thẻ hồng xiên | công dụng, tên tính năng |
   | `[vang]` | vệt bút dạ vàng sau chữ | câu hỏi, điều bất ngờ |
   | `[xanh]` | vệt cọ xanh hai bên chữ | con số, "chỉ 1 bước" |
   | `[to]` | chữ xanh cỡ rất lớn | cụm 1–3 từ, có thể kèm emoji (`TRÁI CAM 🍊`) |
   | `[nen]` | chữ trắng trên nền xanh bo tròn | lời gọi, dòng mở |

   Đổi kiểu giữa các ảnh để loạt bìa không bị lặp. Không gắn thẻ thì script tự chọn.
4. Chạy:
   ```bash
   python3 .claude/skills/tao-anh-bia/scripts/tao_anh_bia.py ANH --hook "DÒNG 1 / [vang] DÒNG 2 / DÒNG 3" -o ANH_bia.jpg
   ```
   Tuỳ chọn:
   - `--sao trai|phai|an`: vị trí ngôi sao (ẩn khi dòng có emoji lớn hoặc chỗ trái che mặt)
   - `--diem-nhan tu-dong|khong|tia-vang,tia-hong,lap-lanh,bong-bong,tim`: điểm nhấn quanh khung. Mặc định tự chọn theo kiểu dòng nhấn mạnh. Sản phẩm tắm gội hợp với `bong-bong`, nội dung tình cảm hợp với `tim`.
   - `--y 60`: đẩy khung xuống (px) nếu khung che mặt hoặc sản phẩm.
   - `--khung-trong-suot`: xuất thêm PNG trong suốt để chèn lên video trong CapCut hoặc ffmpeg.
   - Không đưa ảnh: chỉ xuất khung PNG trong suốt.
5. **Xem lại ảnh kết quả** (mở file bằng Read). Kiểm tra: khung không che mặt hay sản phẩm chính, chữ không tràn khung, dấu tiếng Việt đủ. Nếu che thì chỉnh `--y` hoặc `--sao`, chạy lại.
6. Gửi ảnh cho người dùng (SendUserFile) và nói ngắn gọn đã chọn kiểu nhấn mạnh nào. Lưu file kết quả cạnh ảnh gốc, không ghi đè ảnh gốc.

## Chèn khung lên video

```bash
python3 .claude/skills/tao-anh-bia/scripts/tao_anh_bia.py --hook "..." -o khung.png
ffmpeg -i video.mp4 -i khung.png -filter_complex "[1:v][0:v]scale2ref[k][v];[v][k]overlay=0:0:enable='lt(t,3)'" -c:a copy video_co_khung.mp4
```
Bỏ `:enable='lt(t,3)'` để khung hiện suốt video (3 = số giây khung hiện ở đầu). Video phải là khổ dọc 9:16.

## Ảnh gốc của thương hiệu

Nếu `assets/khung.png` hoặc `assets/ngoi-sao.png` tồn tại, script dùng chúng thay cho bản vẽ bằng code (xem `assets/README.md`).
Font Open Sans nằm trong `fonts/` (giấy phép OFL), không cần cài thêm. Cần Python 3 và Pillow (`python3 -m pip install pillow`).
