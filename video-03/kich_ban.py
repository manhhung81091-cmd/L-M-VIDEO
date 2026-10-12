"""Video 03 — Mẹ mệt, con mang nước (Nhà Có Em Bé). Lời thoại NGUYÊN VĂN theo kịch bản.

src: clip dùng cho cảnh. Không có clip 05 -> cảnh 05 dùng tiếp clip 04 (kéo dài, quay chậm).
crop_cx: clip 06 quay ngang -> cắt khung dọc 9:16 quanh tâm này (0–1).
"""

SCENES = [
    {"key": "01", "src": "01", "dur": 3, "lead": 0.05, "zoom": (1.00, 1.03), "lines": [
        ("01", "be", "Mẹ ơi… sao hôm nay mẹ không cười?"),
    ]},
    {"key": "02", "src": "02", "dur": 4, "zoom": (1.00, 1.03), "lines": [
        ("02", "me", "Mẹ chỉ hơi mệt một chút thôi con."),
    ]},
    {"key": "03", "src": "03", "dur": 4, "lines": [
        ("03", "be", "Mẹ ngồi đây nhé! Con có cái này!"),
    ]},
    {"key": "04", "src": "04", "dur": 3.5, "zoom": (1.00, 1.03), "lines": [
        ("04", "be", "Mẹ uống nước đi, cho đỡ mệt ạ!"),
    ]},
    {"key": "05", "src": "04", "dur": 4.5, "zoom": (1.03, 1.06), "lines": [
        ("05a", "me", "Ôi, ai dạy con quan tâm mẹ thế?"),
        ("05b", "be", "Mẹ dạy con mà!"),
    ]},
    {"key": "06", "src": "06", "dur": 4, "in": 0.3, "crop_cx": 0.52, "zoom": (1.00, 1.04), "lines": [
        ("06", "me", "Hóa ra, những điều mẹ dạy con mỗi ngày… con đều ghi nhớ."),
    ]},
]
