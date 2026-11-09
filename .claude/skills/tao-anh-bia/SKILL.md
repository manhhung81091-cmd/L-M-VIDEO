---
name: tao-anh-bia
description: Tạo ảnh bìa TikTok/Reels 9:16 theo bộ nhận diện Bé Sao (khung tiêu đề trắng viền xanh, ngôi sao vàng mặt cười, chữ hook xanh in hoa, dòng nhấn mạnh hồng/vàng/xanh, tia sáng, lấp lánh, bong bóng). Dùng khi người dùng gửi ảnh kèm câu hook, hoặc nhờ làm ảnh bìa, thumbnail, cover hay khung tiêu đề cho video.
---

# Tạo ảnh bìa theo nhận diện Bé Sao

Trả lời bằng tiếng Việt. Người dùng chỉ cần gửi **ảnh + câu hook**; mọi thứ còn lại do bạn quyết định theo bộ nhận diện dưới đây.

## Quy tắc người dùng đã chốt (luôn áp dụng, không cần hỏi lại)

1. **Kích thước:** 1080x1920 (9:16), JPG, đúng chuẩn ảnh bìa TikTok.
2. **Khung không bị mất trên lưới TikTok:** trang cá nhân hiện ảnh bìa dạng 3:4 (bỏ ~240px trên và dưới).
   Khung, chữ, ngôi sao, lấp lánh phải nằm trọn trong vùng y = 240…1680. Kiểm tra bằng `crop((0, 240, 1080, 1680))`.
3. **Khung to như mẫu gốc:** rộng gần hết ảnh (`TL_KHUNG = 1.0`), chữ to. Bản 90% chữ nhỏ bị người dùng chê "khung xấu".
4. **Cân đối, không dính sát đầu:** khoảng trống từ mép trên ô (y=240) tới khung = khoảng trống từ khung tới đỉnh tóc,
   mỗi bên ≥ 30px (`KHOANG_CACH`). Thiếu chỗ thì thu chữ nhẹ (tối thiểu 88%), còn lại đẩy ảnh xuống (lấp phía trên bằng mảng tường của ảnh).
   Đây là mặc định của script; **không** dùng `--giua` và không đặt `--y` nhỏ hơn 250.
5. **Ngôi sao luôn ở góc dưới bên trái khung.** Không tự chuyển sang phải.
6. **Thiết kế theo nội dung, không theo một khuôn:** giữ cố định khung (tấm trắng viền xanh, nền xanh), ngôi sao bên trái
   và màu nhận diện (xanh `#1E9BE9`, hồng, vàng). Còn kiểu dòng nhấn mạnh và icon thì **chọn theo nội dung từng video**,
   không lặp mãi thẻ hồng + vệt vàng (người dùng chê "như nhau, đơn điệu").
7. **Icon sticker cho bắt mắt:** dùng `--icon "🥣,😱"` (tối đa 3, viền trắng như sticker, đặt góc trên trái, góc dưới phải, góc trên phải).
   Chọn icon khớp nội dung: ăn dặm 🥣🍼, bất ngờ/lo lắng 😱😭, mùi thơm 🌸🍊, tắm/bọt 🛁🫧, đi học 🎒, bơi 💦🏊, quà 🎁, trời lạnh ❄️, mẹo/ý hay 💡, cảnh báo ⚠️, đúng/sai ✅❌.
   Không tự thêm tia vàng, tim, tia hồng vẽ bằng code (người dùng đã bỏ); dùng `--diem-nhan khong` khi đã có icon.
   Xem lại để icon không đè chữ.
8. **Dòng nhấn mạnh:** ngắn (~15 ký tự). Ưu tiên `[the]` (thẻ hồng), `[vang]`, `[xanh]`, `[to]`, `[gach]`, `[so]`.
   Hạn chế `[hong]` (bầu dục hồng): người dùng từng yêu cầu bỏ. Khi người dùng muốn "màu hồng" thì dùng `[the]`.
9. **Sau khi làm:** xem lại cả ảnh đầy đủ và bản cắt 3:4; lưu vào `anh-bia/<ten>_bia.jpg`, commit + push, gửi ảnh cho người dùng.

## Bộ nhận diện (giữ cố định)

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
   | `[vethong]` | vệt bút dạ hồng sau chữ | nội dung về bọt vệ sinh (chai hồng); người dùng thích dùng thay vệt vàng khi nói về bọt |
   | `[xanh]` | vệt cọ xanh hai bên chữ | con số, "chỉ 1 bước" |
   | `[to]` | chữ xanh cỡ rất lớn | cụm 1–3 từ, có thể kèm emoji (`TRÁI CAM 🍊`) |
   | `[nen]` | chữ trắng trên nền xanh bo tròn | lời gọi, dòng mở |
   | `[so]` | số đầu dòng rất to (`[so] 3 SAI LẦM`) | danh sách, "3 sai lầm", "5 mẹo" |
   | `[gach]` | gạch chân hồng mảnh dưới dòng | dòng chủ đề cuối |

   Có thể gắn `[to]` cho nhiều dòng liền nhau (mẫu "CÓ CON RỒI / MỚI THẤY"). Hook chỉ 2 dòng thì có thể để cả hai dòng thường, dòng đầu to (mẫu "MẸ CÓ BÉ GÁI").

   Dòng nhấn mạnh phải **ngắn** (khoảng 15 ký tự, như "GHIỀN CÁI NÀY", "BƯỚC NÀY", "CHUA LÒM"), nếu không chữ bị thu nhỏ và mất điểm nhấn.
   Câu dài thì tách phần còn lại sang dòng riêng; ảnh còn nhiều chỗ phía trên đầu thì dùng 4 dòng.
   Đổi kiểu giữa các ảnh để loạt bìa không bị lặp. Không gắn thẻ thì script tự chọn.
4. Chạy:
   ```bash
   python3 .claude/skills/tao-anh-bia/scripts/tao_anh_bia.py ANH --hook "DÒNG 1 / [vang] DÒNG 2 / DÒNG 3" -o ANH_bia.jpg
   ```
   Tuỳ chọn:
   - `--sao trai|an`: ngôi sao luôn bên trái; chỉ ẩn khi dòng có icon lớn
   - `--diem-nhan tu-dong|khong|...`: điểm nhấn quanh khung, kết hợp bằng dấu phẩy:
     `tia-vang`, `tia-hong` (3 tia hình nêm hai bên một dòng ngắn), `tia-vang-goc`, `tia-hong-goc` (tia ở góc trên phải khung),
     `lap-lanh`, `bong-bong`, `tim`. Mặc định tự chọn theo kiểu dòng nhấn mạnh, giống các mẫu: vệt vàng hoặc chữ to → chỉ lấp lánh (**không tự thêm tia vàng**: người dùng đã yêu cầu bỏ tia vàng nhiều lần, chỉ dùng khi họ yêu cầu);
     hồng/thẻ/số/gạch chân → chỉ lấp lánh (**không tự thêm tim hay tia hồng ở góc**: người dùng đã yêu cầu bỏ); 2 dòng thường → chỉ lấp lánh. Dòng có emoji lớn thường để `khong` và `--sao an`.
   - `--nhich N`: nhích khung lên N px (âm để hạ xuống) sau khi tự đặt; dùng khi người dùng nói "cao/thấp thêm xíu" (xíu ≈ 25px). Không lên quá y=250.
   - `--dau Y`: toạ độ y (trên ảnh 1080x1920) của đỉnh đầu (gồm cả tóc) người trong ảnh. Dùng khi script không tự tìm thấy mặt hoặc tìm sai.
   - `--khung-trong-suot`: xuất thêm PNG trong suốt để chèn lên video trong CapCut hoặc ffmpeg.
   - Không đưa ảnh: chỉ xuất khung PNG trong suốt.
   **Không được che đầu người trong ảnh.** Script tự nhận diện khuôn mặt (cần `python3 -m pip install "opencv-python-headless<5"`)
   rồi đặt khung theo quy tắc 4 ở trên. Dòng in ra "Đỉnh đầu ở y≈…" cho biết kết quả nhận diện.
5. **Xem lại ảnh kết quả** (mở file bằng Read), cả ảnh đầy đủ lẫn bản cắt 3:4. Kiểm tra: khung trọn trong ô 3:4, có khoảng trống cân đối trên và dưới, không che đầu, mặt hay sản phẩm, chữ không tràn khung, dấu tiếng Việt đủ. Nhận diện đầu sai thì ước lượng y của đỉnh tóc trên ảnh gốc rồi chạy lại với `--dau Y`.
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
