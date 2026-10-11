"""Kịch bản + phụ đề. Sửa lời thoại ở SCENES rồi chạy lại build.py.

Mỗi cảnh: key = đuôi tên file (01 ... 09), lines = danh sách (người nói, câu).
Người nói "" = lời dẫn. Thời gian trong cảnh được chia đều cho các câu.
"""

SCENES = [
    {"key": "01", "lines": [
        ("Mẹ", "Hôm nay Bé Sao đi học có ổn không nhỉ?"),
        ("Mẹ", "Không biết con có tự đi vệ sinh được không..."),
    ]},
    {"key": "02", "lines": [
        ("Bé Sao", "Ơ... giấy này dùng thế nào nhỉ?"),
    ]},
    {"key": "03", "transition": "fadewhite", "lines": [
        ("Mẹ", "Con nhớ nhé: gấp giấy lại, lau nhẹ từ trước ra sau."),
        ("Bé Sao", "Dạ, con nhớ rồi ạ!"),
    ]},
    {"key": "04", "lines": [
        ("Mẹ", "Và nhớ rửa tay với xà phòng thật sạch nha!"),
    ]},
    {"key": "05", "transition": "fadewhite", "lines": [
        ("Bé Sao", "À đúng rồi! Gấp giấy... lau từ trước ra sau!"),
    ]},
    {"key": "06", "lines": [
        ("Cô giáo", "Sao giỏi quá! Con tự làm được rồi đấy!"),
    ]},
    {"key": "07", "lines": [
        ("Bé Sao", "Mẹ ơi! Hôm nay con tự đi vệ sinh được rồi!"),
        ("Mẹ", "Ôi, con gái mẹ giỏi quá!"),
    ]},
    {"key": "08", "lines": [
        ("Mẹ", "Mẹ tự hào về con lắm, Bé Sao ạ!"),
    ]},
    {"key": "09", "lines": []},
]

TITLE = "BÉ SAO TỰ ĐI VỆ SINH"
CHANNEL = "Nhà Có Em Bé"
END_LINES = ["Mỗi ngày bé lớn thêm một chút ♥", "Theo dõi kênh Nhà Có Em Bé nhé!"]

# Màu chữ người nói (ASS dùng &HBBGGRR)
SPEAKER_COLOR = {
    "Mẹ": "&H00B469FF",       # hồng
    "Bé Sao": "&H0000C8FF",   # vàng cam
    "Cô giáo": "&H00E6A04B",  # xanh dương
}


def _ts(t):
    t = max(t, 0)
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def write_ass(path, starts, durs, total, w, h):
    font = "Baloo 2 ExtraBold"
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,{font},46,&H00FFFFFF,&H00FFFFFF,&H00602A8C,&H64000000,0,0,0,0,100,100,0,0,1,4,2,2,50,50,330,1
Style: Speaker,{font},34,&H00FFFFFF,&H00FFFFFF,&H00FFFFFF,&H64000000,0,0,0,0,100,100,0,0,1,3,1,2,50,50,330,1
Style: Title,{font},62,&H00FFFFFF,&H00FFFFFF,&H00B469FF,&H64000000,0,0,0,0,100,100,1,0,1,6,3,8,40,40,150,1
Style: Channel,{font},34,&H00B469FF,&H00FFFFFF,&H00FFFFFF,&H64000000,0,0,0,0,100,100,1,0,1,4,1,8,40,40,95,1
Style: End,{font},50,&H00FFFFFF,&H00FFFFFF,&H00B469FF,&H64000000,0,0,0,0,100,100,0,0,1,5,2,5,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    pop = r"{\fad(150,150)\t(0,180,\fscx106\fscy106)\t(180,320,\fscx100\fscy100)}"
    # Tiêu đề mở đầu
    ev.append(f"Dialogue: 1,{_ts(0.3)},{_ts(4.3)},Channel,,0,0,0,,{{\\fad(300,300)}}★ {CHANNEL} ★")
    ev.append(f"Dialogue: 1,{_ts(0.4)},{_ts(4.3)},Title,,0,0,0,,{{\\fad(300,300)}}{TITLE}")

    for sc, st, d in zip(SCENES, starts, durs):
        lines = sc["lines"]
        if not lines:
            continue
        a, b = st + 0.25, st + d - 0.45
        step = (b - a) / len(lines)
        for j, (who, text) in enumerate(lines):
            s, e = a + j * step, a + (j + 1) * step - 0.05
            if who:
                col = SPEAKER_COLOR.get(who, "&H00FFFFFF")
                ev.append(f"Dialogue: 2,{_ts(s)},{_ts(e)},Speaker,,0,0,0,,"
                          f"{{\\fad(150,150)\\pos({w//2},{h-330-135})\\an2\\3c{col}\\bord6}}{who}")
            ev.append(f"Dialogue: 2,{_ts(s)},{_ts(e)},Sub,,0,0,0,,{pop}{text}")

    # Thẻ kết ở cảnh cuối
    st_end = starts[-1] + 0.3
    ev.append(f"Dialogue: 1,{_ts(st_end)},{_ts(total)},End,,0,0,0,,"
              f"{{\\fad(400,0)\\pos({w//2},{h//2 + 120})}}{END_LINES[0]}\\N{{\\fs40\\3c&H00602A8C&}}{END_LINES[1]}")
    with open(path, "w", encoding="utf-8") as f:
        f.write(head + "\n".join(ev) + "\n")
