"""Bác sĩ Bé Sao — Tập 1: Tay sạch mà sao vẫn phải rửa? Lời thoại NGUYÊN VĂN theo kịch bản."""

TITLE = "TẬP 1\nTAY SẠCH MÀ SAO\nVẪN PHẢI RỬA?"
NHAN = "NHÌN SẠCH ≠ ĐÃ SẠCH"

# (id, vai, câu)  vai: "be" = bé thật, "sao" = Bác sĩ Bé Sao
LINES = [
    ("1", "be", "Bé Sao ơi, tay con có bẩn đâu! Sao mẹ cứ bảo rửa?"),
    ("2", "sao", "Cho Bé Sao xem nào! À, có những thứ bé xíu trên tay mà mắt mình không nhìn thấy đấy!"),
    ("4", "sao", "Trước khi ăn và sau khi đi vệ sinh, con nhớ rửa tay với xà phòng nhé!"),
    ("5", "be", "À… con mới kiểm tra bằng mắt thôi!"),
]

# giọng tạm Piper: độ dài âm (chậm/nhanh) + bộ lọc cao độ
ROLE = {
    "be": {"length": 1.0, "af": "rubberband=pitch=1.32:formant=shifted,"},
    "sao": {"length": 0.98, "af": "rubberband=pitch=1.16:formant=shifted,"},
}
