"""Video 02 — Một câu nói của con khiến mẹ đứng hình! (Nhà Có Em Bé).

Lời thoại giữ NGUYÊN VĂN theo "Nha_Co_Em_Be_Video_02_Kich_Ban_CHOT_Gui_Claude.docx".
lines: (id file giọng, vai "be"/"me", câu). dur = thời lượng cảnh theo timeline gốc;
build.py tự nới cảnh nếu thoại dài hơn (không ép giọng bé nói gấp).
"""

SCENES = [
    {"key": "01", "dur": 3, "lead": 0.05, "zoom": (1.00, 1.04), "lines": [
        ("01a", "be", "Mẹ ơi! Hôm nay con tự làm được rồi!"),
        ("01b", "me", "Thật á con?"),
    ]},
    {"key": "02", "dur": 4, "sfx": True, "lines": [
        ("02", "be", "Con tự rửa tay…"),
    ]},
    {"key": "03", "dur": 4, "lines": [
        ("03", "be", "Con còn tự lấy giấy nữa!"),
    ]},
    {"key": "04", "dur": 5, "zoom": (1.00, 1.03), "lines": [
        ("04a", "me", "Ôi, con gái mẹ giỏi quá!"),
        ("04b", "be", "Mai con còn tự làm nữa cơ!"),
    ]},
    {"key": "05", "dur": 4, "in": 0.2, "zoom": (1.00, 1.05), "lines": [
        ("05", "me", "Hóa ra, con lớn lên từ những điều nhỏ xíu như thế."),
    ]},
    {"key": "06", "dur": 3, "in": 0.25, "lines": [],
     "cau_hoi": "Con nhà bạn đã biết\\Ntự làm việc gì rồi?"},
]
