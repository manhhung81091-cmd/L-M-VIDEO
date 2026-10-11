"""Video 01 — Con lớn rồi, mẹ không thể làm thay mãi (Nhà Có Em Bé).

Lời đọc + chữ nhấn giữ NGUYÊN VĂN theo "Kich_Ban_Ban_Giao_Claude.docx".
dur = thời lượng cảnh theo timeline gốc (giây); build.py tự kéo dài
cảnh nếu lời đọc dài hơn, để không phải ép giọng đọc nhanh.
"""

SCENES = [
    {"key": "01", "dur": 5, "vo": "Từ ngày con đi mẫu giáo, mẹ mới nhận ra…",
     "nhan": "TỪ NGÀY CON ĐI MẪU GIÁO…", "zoom": (1.00, 1.04)},
    {"key": "02", "dur": 4, "vo": "Có những việc mẹ không thể làm thay con mãi.",
     "nhan": "MẸ KHÔNG THỂ LÀM THAY MÃI", "zoom": (1.00, 1.04)},
    {"key": "03", "dur": 5, "vo": "Ở nhà, mẹ kiên nhẫn dạy con từng chút một.",
     "nhan": "DẠY CON TỪNG CHÚT MỘT", "in": "dissolve", "in_d": 0.2, "warm": True},
    {"key": "04", "dur": 4, "vo": "Từ việc tự rửa tay…",
     "nhan": "TỰ RỬA TAY", "keep_audio": True},
    {"key": "05", "dur": 5, "vo": "Đến những thói quen vệ sinh nhỏ mỗi ngày.",
     "nhan": "THÓI QUEN NHỎ MỖI NGÀY"},
    {"key": "06", "dur": 5, "vo": "Con dần biết tự làm, và nhờ cô giúp khi cần.",
     "nhan": "CON TỰ TIN HƠN MỖI NGÀY", "zoom": (1.00, 1.05)},
    {"key": "07", "dur": 5, "vo": "Con không cần giỏi ngay đâu, con yêu.",
     "nhan": "CON KHÔNG CẦN GIỎI NGAY"},
    {"key": "08", "dur": 6,
     "vo": "Chỉ cần mỗi ngày, con tự lập thêm một chút. Mẹ sẽ luôn đồng hành cùng con.",
     "nhan": "MẸ LUÔN ĐỒNG HÀNH CÙNG CON"},
    {"key": "09", "dur": 3, "vo": "",
     "nhan": "NHÀ CÓ EM BÉ", "in": "dissolve", "in_d": 0.3},
]
