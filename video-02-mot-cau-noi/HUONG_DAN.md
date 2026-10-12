# Video 02 — Một câu nói của con khiến mẹ đứng hình!

Kênh TikTok **Nhà Có Em Bé**. Video dọc 9:16, 1080×1920, 30fps, dài **23,17 giây**.

Video dựng từ 6 clip chuyển động Canh_01 → Canh_06, giữ đúng thứ tự. Lời thoại giữ nguyên văn theo kịch bản chốt.

## Timeline

| Cảnh | Thời gian | Chuyển cảnh vào | Thoại |
|---|---|---|---|
| 01 | 0:00.00–0:03.17 | — | **Bé:** Mẹ ơi! Hôm nay con tự làm được rồi! / **Mẹ:** Thật á con? |
| 02 | 0:03.17–0:07.17 | Cắt thẳng | **Bé:** Con tự rửa tay… (kèm tiếng nước rất nhẹ) |
| 03 | 0:07.17–0:11.17 | Cắt thẳng | **Bé:** Con còn tự lấy giấy nữa! |
| 04 | 0:11.17–0:16.17 | Cắt thẳng | **Mẹ:** Ôi, con gái mẹ giỏi quá! / **Bé:** Mai con còn tự làm nữa cơ! |
| 05 | 0:15.97–0:20.17 | Hòa tan 0,2s | **Mẹ (kể):** Hóa ra, con lớn lên từ những điều nhỏ xíu như thế. |
| 06 | 0:19.92–0:23.17 | Hòa tan 0,25s | Không lời. Chữ: "Con nhà bạn đã biết tự làm việc gì rồi?" |

- Cảnh 01 cần thêm 0,17 giây để nói đủ 2 câu thoại.
- Nhạc ấm hơn từ cảnh 05 và tắt dần trong 1,5 giây cuối.
- Chữ có sẵn trên tấm biển trong cảnh 05 ("Con gái của mẹ thật giỏi!") được giữ nguyên, vì không che mặt nhân vật và không trùng với phụ đề.

## Âm thanh

- **Giọng thoại là giọng AI tạm.** Mình dùng Piper với giọng `vi_VN-vais1000`, chạy offline.
  - Bộ dữ liệu giọng này dùng giấy phép CC BY 4.0. Nếu cần ghi nguồn: *Giọng đọc: VAIS-1000 (CC BY 4.0)*.
  - Vai bé dùng cùng giọng đó, nâng cao độ thêm khoảng 5 nửa cung. Nghe phân biệt được với giọng mẹ, nhưng không giống giọng trẻ con thật.
  - Nên thay bằng giọng thu thật: đặt các file `01a.wav`, `01b.wav`, `02.wav`, `03.wav`, `04a.wav`, `04b.wav`, `05.wav` vào một thư mục rồi chạy lại lệnh dựng. Thời lượng từng cảnh sẽ tự căn theo giọng mới.
- **Nhạc nền:** piano tự tổng hợp bằng `../video-01-con-lon-roi/nhac.py`, nhịp 84 BPM, không vướng bản quyền.
- **Âm lượng tổng:** -14 LUFS, đúng chuẩn TikTok.

## Lệnh dựng lại

```bash
python3 giong.py --model vi_VN-vais1000-medium.onnx --out vo   # bỏ qua nếu có giọng thu thật
python3 build.py --media <thư_mục_Canh_NN.mp4> --vo vo --out xuat
```

## Khi đăng TikTok

- **Caption** (theo kịch bản): "Đôi khi chỉ một câu nói của con cũng đủ khiến mẹ vui cả ngày 🥹 Con nhà bạn đã tự làm được điều gì khiến bạn bất ngờ nhất?"
- **Hashtag:** `#NhaCoEmBe #MeVaBe #ConDiMauGiao #DayConTuLap #NuoiDayCon`
- **Bật nhãn "Nội dung do AI tạo".** Video dùng hình AI và giọng AI.
- **Tắt phụ đề tự động của TikTok**, vì video đã có sẵn phụ đề.
- **Sau 24–48 giờ, so sánh với video 01** (thời gian xem trung bình 5,9 giây, tỉ lệ xem hết 3,81%).
