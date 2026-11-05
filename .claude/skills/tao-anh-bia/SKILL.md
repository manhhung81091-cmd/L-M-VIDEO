---
name: tao-anh-bia
description: Tạo ảnh bìa TikTok/Reels 9:16 theo bộ nhận diện Bé Sao (khung tiêu đề trắng viền xanh, ngôi sao vàng mặt cười, chữ hook xanh in hoa, dòng nhấn mạnh hồng/vàng/xanh, tia sáng, lấp lánh, bong bóng). Dùng khi người dùng gửi ảnh kèm câu hook, hoặc nhờ làm ảnh bìa, thumbnail, cover hay khung tiêu đề cho video.
---

# Tạo ảnh bìa theo nhận diện Bé Sao

Trả lời bằng tiếng Việt. Người dùng chỉ cần gửi **ảnh + câu hook**; mọi thứ còn lại do bạn quyết định theo bộ nhận diện dưới đây.

## Bộ nhận diện (giữ cố định)

- **Cỡ và vị trí khung (người dùng chốt):** khung thu còn 90% (`TL_KHUNG = 0.9`), để khi đăng lên lưới TikTok không mất góc nào.
  Khung nằm trong ô 3:4 và **không dính sát đầu**: khoảng trống từ mép trên ô (y=240) tới khung bằng khoảng trống từ khung tới đỉnh tóc,
  mỗi bên ít nhất 40px. Thiếu chỗ thì thu chữ (tối đa còn 80%), rồi đẩy ảnh xuống. Không dùng `--giua` (làm mất dòng đầu trên lưới).
- **Vùng an toàn ảnh bìa:** TikTok hiển thị ảnh bìa trên trang cá nhân dạng 3:4, cắt khoảng 240px phía trên và 240px phía dưới.
  Khung (kể cả ngôi sao, lấp lánh) phải nằm trọn trong vùng y = 240…1680. Mặc định mép trên tấm nền xanh ở y = 258, không đặt cao hơn y = 250: trên lưới TikTok khung nằm sát mép trên ô, thấy trọn viền xanh, giống ảnh chụp trang kênh của người dùng. Khung được chạm nhẹ ngọn tóc nhưng không che trán.
  Khi kiểm tra, cắt thử vùng 3:4 (`crop((0, 240, 1080, 1680))`) và xem khung có trọn vẹn, cân đối không.

Ảnh bìa mẫu đã duyệt nằm trong `mau/` (mau-01 … mau-10). Xem vài ảnh trong đó trước khi làm bìa đầu tiên của phiên để bám đúng phong cách.

- Khổ 1080x1920 (9:16). Ảnh nền được cắt vừa khung, không méo.
- Khung tiêu đề ở phía trên: tấm trắng viền xanh `#1890F0` nằm nghiêng trên tấm nền xanh gradient `#8CD0FC` → `#34A0F6`.
- Ngôi sao vàng mặt cười **luôn ở góc dưới bên trái** khung (đúng nhận diện; chỉ ẩn khi dòng có icon lớn như trái cam).
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
   | `[so]` | số đầu dòng rất to (`[so] 3 SAI LẦM`) | danh sách, "3 sai lầm", "5 mẹo" |
   | `[gach]` | gạch chân hồng mảnh dưới dòng | dòng chủ đề cuối |

   Có thể gắn `[to]` cho nhiều dòng liền nhau (mẫu "CÓ CON RỒI / MỚI THẤY"). Hook chỉ 2 dòng thì thường để cả hai dòng thường: dòng đầu to, tia hồng hai bên (mẫu "MẸ CÓ BÉ GÁI").

   Dòng nhấn mạnh phải **ngắn** (khoảng 15 ký tự, như "GHIỀN CÁI NÀY", "BƯỚC NÀY", "CHUA LÒM"), nếu không chữ bị thu nhỏ và mất điểm nhấn.
   Câu dài thì tách phần còn lại sang dòng riêng; ảnh còn nhiều chỗ phía trên đầu thì dùng 4 dòng.
   Đổi kiểu giữa các ảnh để loạt bìa không bị lặp. Không gắn thẻ thì script tự chọn.
4. Chạy:
   ```bash
   python3 .claude/skills/tao-anh-bia/scripts/tao_anh_bia.py ANH --hook "DÒNG 1 / [vang] DÒNG 2 / DÒNG 3" -o ANH_bia.jpg
   ```
   Tuỳ chọn:
   - `--sao trai|phai|an`: vị trí ngôi sao (ẩn khi dòng có emoji lớn hoặc chỗ trái che mặt)
   - `--diem-nhan tu-dong|khong|...`: điểm nhấn quanh khung, kết hợp bằng dấu phẩy:
     `tia-vang`, `tia-hong` (3 tia hình nêm hai bên một dòng ngắn), `tia-vang-goc`, `tia-hong-goc` (tia ở góc trên phải khung),
     `lap-lanh`, `bong-bong`, `tim`. Mặc định tự chọn theo kiểu dòng nhấn mạnh, giống các mẫu: vệt vàng hoặc chữ to → chỉ lấp lánh (**không tự thêm tia vàng**: người dùng đã yêu cầu bỏ tia vàng nhiều lần, chỉ dùng khi họ yêu cầu);
     hồng/thẻ/số/gạch chân → chỉ lấp lánh (**không tự thêm tim hay tia hồng ở góc**: người dùng đã yêu cầu bỏ); 2 dòng thường → tia hồng hai bên dòng đầu. Dòng có emoji lớn thường để `khong` và `--sao an`.
   - `--y 258`: mép trên tấm nền xanh của khung (px). Không đặt nhỏ hơn 250 (sẽ bị TikTok cắt mất).
   - `--dau Y`: toạ độ y (trên ảnh 1080x1920) của đỉnh đầu (gồm cả tóc) người trong ảnh. Dùng khi script không tự tìm thấy mặt hoặc tìm sai.
   - `--khung-trong-suot`: xuất thêm PNG trong suốt để chèn lên video trong CapCut hoặc ffmpeg.
   - Không đưa ảnh: chỉ xuất khung PNG trong suốt.
   **Không được che đầu người trong ảnh.** Script tự nhận diện khuôn mặt (cần `python3 -m pip install "opencv-python-headless<5"`),
   rồi kéo khung lên cao, thu nhỏ chữ (tối đa còn 72%), và nếu vẫn chạm thì đẩy ảnh nền xuống, để mép dưới khung nằm trên đỉnh tóc.
   Ngôi sao tự chuyển sang phía không có đầu. Dòng in ra "Đỉnh đầu ở y≈…" cho biết kết quả nhận diện.
5. **Xem lại ảnh kết quả** (mở file bằng Read). Kiểm tra: khung và ngôi sao không che đầu, mặt hay sản phẩm chính, chữ không tràn khung, dấu tiếng Việt đủ. Nếu vẫn che, nhìn ảnh gốc để ước lượng y của đỉnh tóc rồi chạy lại với `--dau Y` (và `--sao` nếu cần).
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

### Icon ảnh thay cho emoji

Emoji trong hook được thay bằng ảnh gốc trong `assets/` nếu có (khai báo ở `ICON_THAY_EMOJI` trong script):
- 🍊 → `assets/icon-cam.png` (trái cam nguyên + nửa trái, dùng cho hook về mùi cam)

Người dùng gửi icon mới (PNG nền trong suốt) thì cắt sát viền, lưu vào `assets/icon-<tên>.png` và thêm emoji tương ứng vào `ICON_THAY_EMOJI`.
