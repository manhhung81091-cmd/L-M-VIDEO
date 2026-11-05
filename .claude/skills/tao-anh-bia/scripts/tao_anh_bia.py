#!/usr/bin/env python3
"""Tạo ảnh bìa TikTok 9:16 theo bộ nhận diện Bé Sao.

Khung tiêu đề trắng viền xanh nằm trên tấm nền xanh, ngôi sao mascot ở góc,
chữ hook màu xanh in hoa, dòng nhấn mạnh có kiểu riêng và các điểm nhấn trang trí.

Ví dụ:
    python3 tao_anh_bia.py anh.jpg --hook "ĐÓN CON ĐI HỌC VỀ / SAO NGƯỜI CON LẠI / [vang] CÓ MÙI THẾ NÀY ?"

Mỗi dòng cách nhau bằng " / " (hoặc xuống dòng). Thẻ đặt đầu dòng để chọn kiểu:
    [to]    chữ xanh cỡ lớn
    [hong]  chữ trắng trong hình bầu dục hồng
    [the]   chữ trắng trong thẻ hồng xiên
    [vang]  vệt bút dạ vàng phía sau chữ
    [xanh]  hai vệt cọ xanh hai bên chữ
    [nen]   chữ trắng trên nền xanh bo tròn
Không gắn thẻ nào thì dòng nhấn mạnh được chọn tự động.
Emoji cuối dòng (ví dụ "TRÁI CAM 🍊") được vẽ màu nếu máy có font emoji.

Nếu thư mục ../assets có khung.png hoặc ngoi-sao.png (ảnh nền trong suốt),
script dùng các file đó thay cho khung và ngôi sao vẽ bằng code.
"""
import argparse
import hashlib
import math
import os
import random
import re
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
FONT_DIR = os.path.join(SKILL, "fonts")
ASSET_DIR = os.path.join(SKILL, "assets")

W, H = 1080, 1920
S = 2  # vẽ ở 2x rồi thu nhỏ để nét mịn

# ---- Bảng màu nhận diện (lấy theo khung mẫu) ----
XANH_VIEN = (24, 144, 240)      # viền khung, #1890F0
XANH_NEN_SANG = (140, 208, 252)  # tấm nền xanh, phần sáng
XANH_NEN_DAM = (52, 160, 246)    # tấm nền xanh, phần đậm
XANH_CHU = (30, 155, 233)        # chữ hook, #1E9BE9
TRANG_KHUNG = (250, 250, 250)
HONG = (244, 143, 180)           # #F48FB4
HONG_DAM = (236, 96, 146)
VANG = (255, 214, 46)            # #FFD62E
VANG_VIEN = (242, 165, 22)
VIEN_TOI = (45, 45, 45)

KIEU = {"to", "hong", "the", "vang", "xanh", "nen"}
KIEU_TU_DONG = ["hong", "the", "vang", "xanh"]

# Hình khung theo ảnh mẫu (toạ độ trên khung 2000x1000).
KHUNG_SAU = [(65, 150), (1975, 300), (1910, 872), (1230, 832), (118, 968)]
KHUNG_SAU_BO = [140, 110, 120, 600, 130]
KHUNG_TRUOC = [(122, 240), (1905, 55), (1958, 765), (195, 880)]
KHUNG_TRUOC_BO = 125


def s(v):
    return int(round(v * S))


# ------------------------------------------------------------------ hình học
def bo_goc(pts, radii, n=18):
    """Đa giác bo tròn từng góc (bán kính riêng mỗi góc)."""
    if not isinstance(radii, (list, tuple)):
        radii = [radii] * len(pts)
    out = []
    k = len(pts)
    for i in range(k):
        p0, p1, p2 = pts[i - 1], pts[i], pts[(i + 1) % k]
        d1 = (p0[0] - p1[0], p0[1] - p1[1])
        d2 = (p2[0] - p1[0], p2[1] - p1[1])
        l1, l2 = math.hypot(*d1), math.hypot(*d2)
        r = min(radii[i], l1 / 2, l2 / 2)
        a = (p1[0] + d1[0] / l1 * r, p1[1] + d1[1] / l1 * r)
        b = (p1[0] + d2[0] / l2 * r, p1[1] + d2[1] / l2 * r)
        for j in range(n + 1):
            t = j / n
            out.append((
                (1 - t) ** 2 * a[0] + 2 * (1 - t) * t * p1[0] + t * t * b[0],
                (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * p1[1] + t * t * b[1],
            ))
    return out


def mask_da_giac(size, pts):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).polygon(pts, fill=255)
    return m


def to_mau(layer, mask, color, alpha=255):
    fill = Image.new("RGBA", layer.size, color + (alpha,))
    a = mask if alpha == 255 else mask.point(lambda v: v * alpha // 255)
    fill.putalpha(a)
    layer.alpha_composite(fill)


def gradient_doc(size, top, bottom):
    g = Image.new("RGBA", size)
    h = size[1]
    col = Image.new("RGBA", (1, h))
    for y in range(h):
        t = y / max(1, h - 1)
        col.putpixel((0, y), tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)) + (255,))
    return col.resize(size)


# ------------------------------------------------------------------ khung
def ve_khung(w, h, nghieng=0.75):
    """Khung tiêu đề (2 lớp) cỡ w x h pixel 2x. nghieng<1 làm khung bớt xiên."""
    pad = s(30)
    size = (w + 2 * pad, h + 2 * pad)
    layer = Image.new("RGBA", size, (0, 0, 0, 0))

    def map_pts(pts):
        return [(pad + x / 2000 * w, pad + y / 1000 * h) for x, y in pts]

    def flatten(pts, ref):
        # kéo các đỉnh về hình chữ nhật tham chiếu để giảm độ nghiêng
        return [(x, ry + (y - ry) * nghieng) for (x, y), (_, ry) in zip(pts, ref)]

    sau_ref = [(0, 160), (0, 160), (0, 900), (0, 900), (0, 900)]
    truoc_ref = [(0, 150), (0, 150), (0, 820), (0, 820)]
    sau = map_pts(flatten(KHUNG_SAU, sau_ref))
    truoc = map_pts(flatten(KHUNG_TRUOC, truoc_ref))
    k = h / 1000

    # lớp nền xanh
    sau_poly = bo_goc(sau, [r * k for r in KHUNG_SAU_BO])
    m_sau = mask_da_giac(size, sau_poly)
    grad = gradient_doc(size, XANH_NEN_SANG, XANH_NEN_DAM)
    grad.putalpha(m_sau)
    layer.alpha_composite(grad)
    # ánh sáng mép trong
    inner = m_sau.filter(ImageFilter.GaussianBlur(s(14)))
    glow = ImageChops.subtract(m_sau, inner)
    to_mau(layer, glow, (225, 245, 255), 200)
    ImageDraw.Draw(layer).line(sau_poly + [sau_poly[0]], fill=XANH_VIEN + (255,), width=s(3), joint="curve")

    # bóng đổ của tấm trắng
    truoc_poly = bo_goc(truoc, KHUNG_TRUOC_BO * k)
    m_truoc = mask_da_giac(size, truoc_poly)
    shadow = m_truoc.transform(size, Image.AFFINE, (1, 0, 0, 0, 1, -s(10))).filter(ImageFilter.GaussianBlur(s(12)))
    to_mau(layer, shadow, (20, 110, 210), 120)
    # tấm trắng
    to_mau(layer, m_truoc, TRANG_KHUNG)
    edge = ImageChops.subtract(m_truoc, m_truoc.filter(ImageFilter.GaussianBlur(s(10))))
    to_mau(layer, edge, (190, 225, 250), 160)
    ImageDraw.Draw(layer).line(truoc_poly + [truoc_poly[0]], fill=XANH_VIEN + (255,), width=s(3), joint="curve")
    return layer, pad


def khung_tu_file(w, h):
    path = os.path.join(ASSET_DIR, "khung.png")
    if not os.path.exists(path):
        return None
    im = Image.open(path).convert("RGBA").resize((w, h), Image.LANCZOS)
    return im, 0


# ------------------------------------------------------------------ ngôi sao
def ve_ngoi_sao(size):
    """Ngôi sao mascot vàng có mặt cười, nền trong suốt, cỡ size x size."""
    path = os.path.join(ASSET_DIR, "ngoi-sao.png")
    if os.path.exists(path):
        im = Image.open(path).convert("RGBA")
        im.thumbnail((size, size), Image.LANCZOS)
        return im

    k = 4
    N = size * k
    R = N * 0.47
    cx, cy = N / 2, N * 0.53
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        r = R if i % 2 == 0 else R * 0.52
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))

    def star_mask(grow):
        m = Image.new("L", (N, N), 0)
        ImageDraw.Draw(m).polygon(pts, fill=255)
        m = m.filter(ImageFilter.GaussianBlur(R * 0.09))
        return m.point(lambda v: 255 if v > grow else 0).filter(ImageFilter.GaussianBlur(1.5))

    m_ngoai = star_mask(60)
    m_trong = star_mask(118)
    img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    to_mau(img, m_ngoai, (233, 158, 8))

    # thân sao: gradient tròn sáng ở giữa-trên
    gx, gy = cx - R * 0.1, cy - R * 0.25
    step = 4
    small = Image.new("RGBA", (N // step, N // step))
    sp = small.load()
    for y in range(N // step):
        for x in range(N // step):
            d = math.hypot(x * step - gx, y * step - gy) / (R * 1.15)
            d = min(1, d)
            c0, c1 = (255, 238, 92), (255, 196, 18)
            sp[x, y] = tuple(int(c0[i] + (c1[i] - c0[i]) * d) for i in range(3)) + (255,)
    body = small.resize((N, N), Image.BILINEAR)
    body.putalpha(m_trong)
    img.alpha_composite(body)

    d = ImageDraw.Draw(img)
    # vệt bóng láng
    hl = Image.new("L", (N, N), 0)
    hd = ImageDraw.Draw(hl)
    hd.ellipse([cx - R * 0.12, cy - R * 0.82, cx + R * 0.0, cy - R * 0.5], fill=170)
    hd.ellipse([cx - R * 0.78, cy - R * 0.28, cx - R * 0.5, cy - R * 0.2], fill=150)
    hd.ellipse([cx + R * 0.45, cy - R * 0.28, cx + R * 0.62, cy - R * 0.21], fill=130)
    hd.ellipse([cx - R * 0.66, cy + R * 0.35, cx - R * 0.6, cy + R * 0.55], fill=110)
    hl = ImageChops.multiply(hl.filter(ImageFilter.GaussianBlur(R * 0.025)), m_trong)
    to_mau(img, hl, (255, 255, 240))

    # má hồng
    ma = Image.new("L", (N, N), 0)
    md = ImageDraw.Draw(ma)
    for sx in (-1, 1):
        ex = cx + sx * R * 0.4
        md.ellipse([ex - R * 0.14, cy + R * 0.13, ex + R * 0.14, cy + R * 0.28], fill=200)
    to_mau(img, ma.filter(ImageFilter.GaussianBlur(R * 0.02)), (255, 110, 130))

    # mắt
    for sx in (-1, 1):
        ex, ey = cx + sx * R * 0.3, cy - R * 0.02
        d.ellipse([ex - R * 0.12, ey - R * 0.14, ex + R * 0.12, ey + R * 0.14], fill=(20, 18, 22, 255))
        d.ellipse([ex - R * 0.07, ey - R * 0.1, ex + R * 0.02, ey - R * 0.01], fill=(255, 255, 255, 255))
        d.ellipse([ex + R * 0.03, ey + R * 0.03, ex + R * 0.07, ey + R * 0.07], fill=(255, 255, 255, 255))

    # miệng cười
    mx, my = cx, cy + R * 0.06
    mw, mh = R * 0.15, R * 0.2
    mouth = Image.new("L", (N, N), 0)
    ImageDraw.Draw(mouth).pieslice([mx - mw, my - mh, mx + mw, my + mh], 0, 180, fill=255)
    to_mau(img, mouth, (58, 22, 18))
    tongue = Image.new("L", (N, N), 0)
    ImageDraw.Draw(tongue).ellipse([mx - mw * 0.7, my + mh * 0.35, mx + mw * 0.7, my + mh * 1.3], fill=255)
    to_mau(img, ImageChops.multiply(tongue, mouth), (236, 84, 106))

    return img.resize((size, size), Image.LANCZOS)


# ------------------------------------------------------------------ điểm nhấn
def ve_tia(d, cx, cy, huong, dai, mau, vien, rong=s(13), goc=34):
    """Ba tia toả ra từ (cx, cy) theo hướng (độ)."""
    for da in (-goc, 0, goc):
        a = math.radians(huong + da)
        r0 = s(16)
        r1 = r0 + dai * (1.0 if da == 0 else 0.8)
        p0 = (cx + r0 * math.cos(a), cy + r0 * math.sin(a))
        p1 = (cx + r1 * math.cos(a), cy + r1 * math.sin(a))
        for color, wd in ((vien, rong + s(5)), (mau, rong)):
            d.line([p0, p1], fill=color + (255,), width=wd)
            for p in (p0, p1):
                d.ellipse([p[0] - wd / 2, p[1] - wd / 2, p[0] + wd / 2, p[1] + wd / 2], fill=color + (255,))


def ve_lap_lanh(d, cx, cy, r, mau):
    pts = []
    for i in range(8):
        a = -math.pi / 2 + i * math.pi / 4
        rr = r if i % 2 == 0 else r * 0.22
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=mau + (255,))


def ve_bong_bong(layer, cx, cy, r):
    m = Image.new("L", layer.size, 0)
    md = ImageDraw.Draw(m)
    md.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    ring = ImageChops.subtract(m, m.filter(ImageFilter.GaussianBlur(r * 0.25)))
    to_mau(layer, m, (210, 238, 255), 70)
    to_mau(layer, ring, (120, 195, 250), 230)
    d = ImageDraw.Draw(layer)
    d.ellipse([cx - r * 0.55, cy - r * 0.6, cx - r * 0.15, cy - r * 0.25], fill=(255, 255, 255, 230))


def ve_tim(d, cx, cy, r, mau):
    d.ellipse([cx - r, cy - r * 0.8, cx, cy + r * 0.2], fill=mau + (255,))
    d.ellipse([cx, cy - r * 0.8, cx + r, cy + r * 0.2], fill=mau + (255,))
    d.polygon([(cx - r * 0.95, cy - r * 0.15), (cx + r * 0.95, cy - r * 0.15), (cx, cy + r * 1.05)], fill=mau + (255,))


# ------------------------------------------------------------------ chữ
EMOJI_RE = re.compile(
    "([\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\u2300-\u23FF][\uFE0F\u200D\U0001F3FB-\U0001F3FF"
    "\U0001F000-\U0001FAFF]*)"
)

_emoji_font = None


def font_emoji():
    global _emoji_font
    if _emoji_font is not None:
        return _emoji_font or None
    cands = [
        "/System/Library/Fonts/Apple Color Emoji.ttc",
        "C:/Windows/Fonts/seguiemj.ttf",
        "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
        "/usr/share/fonts/noto/NotoColorEmoji.ttf",
    ]
    for p in cands:
        if not os.path.exists(p):
            continue
        for sz in (109, 160, 137, 96, 64):
            try:
                _emoji_font = ImageFont.truetype(p, sz)
                return _emoji_font
            except OSError:
                continue
    _emoji_font = False
    return None


def anh_emoji(chuoi, cao):
    f = font_emoji()
    if f is None:
        return None
    try:
        box = f.getbbox(chuoi)
        im = Image.new("RGBA", (box[2] + 20, box[3] + 20), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((10, 10), chuoi, font=f, embedded_color=True)
    except Exception:
        return None
    bb = im.getbbox()
    if not bb:
        return None
    im = im.crop(bb)
    return im.resize((max(1, int(im.width * cao / im.height)), int(cao)), Image.LANCZOS)


_fonts = {}


def font(size, dam=True):
    name = "OpenSans-ExtraBold.ttf" if dam else "OpenSans-Bold.ttf"
    key = (name, size)
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(os.path.join(FONT_DIR, name), size)
    return _fonts[key]


class Dong:
    def __init__(self, text, kieu):
        self.kieu = kieu
        parts = [p for p in EMOJI_RE.split(text) if p]
        self.runs = [(p, bool(EMOJI_RE.fullmatch(p))) for p in parts]
        self.text = "".join(p for p, e in self.runs if not e).strip()
        self.co_emoji = any(e for _, e in self.runs)
        self.size = 0

    def do_rong(self, size):
        f = font(size, self.dam)
        w = 0
        for p, e in self.runs:
            if e:
                w += int(size * 1.15) + s(8) if font_emoji() else 0
            else:
                w += f.getlength(p)
        return w

    @property
    def dam(self):
        return self.kieu in ("to", "hong", "the", "nen", "vang", "xanh")

    def chieu_cao(self):
        if self.kieu in ("hong", "the", "nen"):
            return self.size * 1.62
        return self.size * 1.3


def phan_tich_hook(hook):
    raw = [x.strip() for x in re.split(r"\s*/\s*|\n", hook) if x.strip()]
    dong = []
    for x in raw:
        m = re.match(r"\[(\w+)\]\s*(.*)", x)
        kieu = "thuong"
        if m and m.group(1).lower() in KIEU:
            kieu, x = m.group(1).lower(), m.group(2)
        dong.append(Dong(x.upper() if not EMOJI_RE.search(x) else upper_giu_emoji(x), kieu))
    if dong and all(d.kieu == "thuong" for d in dong):
        if len(dong) == 1:
            dong[0].kieu = "to"
        else:
            idx = 1 if len(dong) >= 2 else 0
            if len(dong) >= 3:
                # dòng ngắn nhất trong các dòng sau dòng đầu thường là ý chính
                idx = min(range(1, len(dong)), key=lambda i: len(dong[i].text))
            h = int(hashlib.md5(hook.encode()).hexdigest(), 16)
            dong[idx].kieu = KIEU_TU_DONG[h % len(KIEU_TU_DONG)]
    return dong


def upper_giu_emoji(x):
    return "".join(p if EMOJI_RE.fullmatch(p) else p.upper() for p in EMOJI_RE.split(x) if p)


def be_rong_hinh(d, size):
    """Bề rộng cả dòng kèm hình trang trí của kiểu chữ."""
    tw = d.do_rong(size)
    return {
        "hong": tw * 1.12 + size * 1.3,
        "the": tw + size * 1.75,
        "nen": tw + size * 1.2,
        "vang": tw + size * 1.2,
        "xanh": tw + size * 3.2,
    }.get(d.kieu, tw)


def gioi_han(d, rong):
    return rong + {"hong": s(50), "the": s(40), "nen": s(40), "xanh": s(130)}.get(d.kieu, 0)


def chon_co_chu(dong, rong_toi_da, ty_le=1.0):
    n = len(dong)
    for i, d in enumerate(dong):
        if d.kieu == "to":
            base = 104
        elif d.kieu in ("hong", "the", "nen", "vang", "xanh"):
            base = 76
        elif i == 0:
            base = 66
        else:
            base = 50 if n >= 3 else 58
        size = s(base * ty_le)
        while be_rong_hinh(d, size) > gioi_han(d, rong_toi_da) and size > s(28):
            size -= s(1)
        d.size = size


def ve_net_co(layer, x0, x1, ymid, cao, mau, seed, so_net=16):
    rnd = random.Random(seed)
    tmp = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    for _ in range(so_net):
        y = ymid + (rnd.random() - 0.5) * cao
        wd = int(cao * rnd.uniform(0.25, 0.5))
        a = rnd.randint(140, 210)
        xa = x0 + rnd.uniform(0, 0.06) * (x1 - x0)
        xb = x1 - rnd.uniform(0, 0.06) * (x1 - x0)
        d.line([(xa, y + rnd.uniform(-3, 3) * S), (xb, y + rnd.uniform(-3, 3) * S)], fill=mau + (a,), width=max(2, wd))
    tmp = tmp.filter(ImageFilter.GaussianBlur(S * 0.8))
    layer.alpha_composite(tmp)


def ve_dong(layer, d, cx, cy, seed):
    draw = ImageDraw.Draw(layer)
    size = d.size
    tw = d.do_rong(size)
    mau_chu = XANH_CHU
    if d.kieu == "hong":
        ew, eh = tw * 1.12 + size * 1.3, size * 1.5
        draw.ellipse([cx - ew / 2, cy - eh / 2, cx + ew / 2, cy + eh / 2], fill=HONG + (255,), outline=VIEN_TOI + (255,), width=s(1.5))
        mau_chu = (255, 255, 255)
    elif d.kieu == "the":
        bw, bh = tw + size * 1.5, size * 1.5
        k = bh * 0.14
        pts = [(cx - bw / 2, cy - bh / 2), (cx + bw / 2 + k, cy - bh / 2), (cx + bw / 2 - k, cy + bh / 2), (cx - bw / 2, cy + bh / 2)]
        draw.polygon(bo_goc(pts, s(10)), fill=(247, 166, 200, 255), outline=VIEN_TOI + (255,), width=s(1.5))
        mau_chu = (255, 255, 255)
    elif d.kieu == "nen":
        bw, bh = tw + size * 1.2, size * 1.45
        draw.rounded_rectangle([cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2], radius=bh / 2, fill=XANH_CHU + (255,))
        mau_chu = (255, 255, 255)
    elif d.kieu == "vang":
        ve_net_co(layer, cx - tw / 2 - size * 0.6, cx + tw / 2 + size * 0.6, cy + size * 0.08, size * 0.85, (255, 230, 80), seed, 18)
        ve_net_co(layer, cx - tw / 2 - size * 0.3, cx + tw / 2 + size * 0.3, cy + size * 0.15, size * 0.5, (250, 175, 160), seed + 1, 6)
    elif d.kieu == "xanh":
        for side in (-1, 1):
            inner = cx + side * (tw / 2 - size * 0.25)
            outer = cx + side * (tw / 2 + size * 1.6)
            ve_net_co(layer, min(inner, outer), max(inner, outer), cy + size * 0.05, size * 0.8, (74, 168, 238), seed + side, 14)

    # chữ + emoji
    f = font(size, d.dam)
    x = cx - tw / 2
    for p, e in d.runs:
        if e:
            im = anh_emoji(p, size * 1.15)
            if im is not None:
                x += s(8)
                layer.alpha_composite(im, (int(x), int(cy - im.height / 2)))
                x += int(size * 1.15)
            continue
        if d.kieu in ("hong", "the", "nen"):
            draw.text((x + s(2), cy + s(3)), p, font=f, fill=(0, 0, 0, 50), anchor="lm")
        draw.text((x, cy), p, font=f, fill=mau_chu + (255,), anchor="lm")
        x += f.getlength(p)
    return tw


# ------------------------------------------------------------------ ghép
def nen_9_16(path, day_xuong=0):
    ext = os.path.splitext(path)[1].lower()
    if ext in (".mp4", ".mov", ".m4v", ".mkv", ".webm"):
        raise SystemExit("Hãy đưa ảnh (jpg/png). Với video, lấy 1 khung hình bằng ffmpeg trước: "
                         "ffmpeg -ss 1 -i video.mp4 -frames:v 1 anh.jpg")
    im = Image.open(path)
    try:
        from PIL import ImageOps
        im = ImageOps.exif_transpose(im)
    except Exception:
        pass
    im = im.convert("RGB")
    r = max(W / im.width, H / im.height)
    im = im.resize((math.ceil(im.width * r), math.ceil(im.height * r)), Image.LANCZOS)
    left = (im.width - W) // 2
    top = (im.height - H) // 2
    im = im.crop((left, top, left + W, top + H))
    if day_xuong > 0:
        # đẩy ảnh xuống, phần trống phía trên lấp bằng chính ảnh làm mờ
        mo = im.resize((W, H)).filter(ImageFilter.GaussianBlur(30))
        mo.paste(im, (0, day_xuong))
        im = mo
    return im


def kich_thuoc_khung(dong, ty_le=1.0):
    """Cỡ chữ từng dòng, chiều cao khối chữ và chiều cao khung (đơn vị 2x)."""
    chon_co_chu(dong, s(800), ty_le)
    gap = s(8 * ty_le)
    hc = sum(d.chieu_cao() for d in dong) + gap * (len(dong) - 1)
    ch = max(s(360 * ty_le), int(hc / 0.56))
    return gap, hc, ch


DAY_KHUNG = 0.985  # mép dưới tấm nền xanh, tính theo chiều cao khung


def xep_khung_tranh_dau(hook, y_top, dinh_dau, le=14):
    """Chọn tỉ lệ chữ và vị trí khung sao cho mép dưới khung nằm trên đỉnh đầu.

    Trả về (y_top, ty_le, do_day_anh): do_day_anh > 0 nghĩa là phải đẩy ảnh nền
    xuống bấy nhiêu px vì khung nhỏ nhất vẫn chạm đầu."""
    if dinh_dau is None:
        return y_top, 1.0, 0
    gioi_han = dinh_dau - le
    dong = phan_tich_hook(hook)
    y_min = 24
    for i in range(8):
        k = 1.0 - 0.04 * i
        _, _, ch = kich_thuoc_khung(dong, k)
        cao = ch / S * DAY_KHUNG
        if y_top + cao <= gioi_han:
            return y_top, k, 0
        if y_min + cao <= gioi_han:
            return int(gioi_han - cao), k, 0
    k = 1.0 - 0.04 * 7
    _, _, ch = kich_thuoc_khung(dong, k)
    return y_min, k, int(y_min + ch / S * DAY_KHUNG - gioi_han)


def tim_dinh_dau(anh):
    """Ước lượng toạ độ y của đỉnh đầu người trong ảnh 1080x1920 (None nếu không thấy).

    Cần OpenCV (pip install opencv-python-headless). Trả về (y_dinh_dau, x_trai, x_phai)."""
    try:
        import cv2
        import numpy as np
    except ImportError:
        return None
    if not hasattr(cv2, "CascadeClassifier"):  # OpenCV 5 bỏ Haar; cần opencv-python-headless<5
        return None
    g = cv2.cvtColor(np.array(anh.convert("RGB")), cv2.COLOR_RGB2GRAY)
    g = cv2.equalizeHist(g)
    faces = []
    for name in ("haarcascade_frontalface_default.xml", "haarcascade_profileface.xml"):
        cas = cv2.CascadeClassifier(os.path.join(cv2.data.haarcascades, name))
        for (x, y, w, h) in cas.detectMultiScale(g, 1.1, 6, minSize=(110, 110)):
            if y < H * 0.75:
                faces.append((x, y, w, h))
        if faces:
            break
    if not faces:
        return None
    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
    # khung mặt Haar bắt đầu ở trán; tóc nhô thêm khoảng 0,2-0,25 chiều cao mặt
    return int(y - 0.3 * h), int(x - 0.25 * w), int(x + 1.25 * w)


def tao_lop_phu(hook, sao="trai", diem_nhan="tu-dong", y_top=60, ty_le=1.0):
    dong = phan_tich_hook(hook)
    if not dong:
        raise SystemExit("Hook trống.")
    seed = int(hashlib.md5(hook.encode()).hexdigest()[:8], 16)

    cw = s(1000)
    gap, hc, ch = kich_thuoc_khung(dong, ty_le)

    layer = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    x0 = (W * S - cw) // 2
    y0 = s(y_top)

    kf = khung_tu_file(cw, ch) or ve_khung(cw, ch)
    khung, pad = kf
    layer.alpha_composite(khung, (x0 - pad, y0 - pad))

    # chữ: căn giữa vùng trắng (lệch phải nhẹ vì ngôi sao ở trái)
    cx = x0 + cw * 0.52
    cy = y0 + ch * 0.52 - hc / 2
    vi_tri = []
    for i, d in enumerate(dong):
        hh = d.chieu_cao()
        mid = cy + hh / 2
        tw = ve_dong(layer, d, cx, mid, seed + i * 7)
        vi_tri.append((d, mid, tw))
        cy += hh + gap

    # điểm nhấn
    dr = ImageDraw.Draw(layer)
    chon = set(diem_nhan.split(",")) if diem_nhan != "tu-dong" else set()
    nhan = next((v for v in vi_tri if v[0].kieu in ("vang", "hong", "the", "nen", "xanh", "to")), vi_tri[0])
    if diem_nhan == "tu-dong":
        if nhan[0].kieu == "vang":
            chon = {"tia-vang", "lap-lanh"}
        elif nhan[0].kieu in ("hong", "the"):
            chon = {"tia-hong", "tim"}
        else:
            chon = {"lap-lanh", "bong-bong"}
    if "khong" in chon:
        chon = set()

    if "tia-vang" in chon:
        d, mid, tw = nhan if nhan[0].kieu != "vang" or len(vi_tri) < 2 else vi_tri[max(0, vi_tri.index(nhan) - 1)]
        half = tw / 2 + s(40)
        ve_tia(dr, cx - half, mid - s(4), 180, s(46), VANG, VANG_VIEN)
        ve_tia(dr, cx + half, mid - s(4), 0, s(46), VANG, VANG_VIEN)
    if "tia-hong" in chon:
        ve_tia(dr, x0 + cw * 0.86, y0 + ch * 0.2, -40, s(58), (255, 150, 190), HONG_DAM, rong=s(16), goc=30)
    if "lap-lanh" in chon:
        ve_lap_lanh(dr, x0 + cw * 0.96, y0 + ch * 0.06, s(30), VANG)
        ve_lap_lanh(dr, x0 + cw * 0.9, y0 - s(4), s(16), (255, 255, 255))
        ve_lap_lanh(dr, x0 + cw * 0.2, y0 + ch * 1.02, s(20), VANG)
    if "bong-bong" in chon:
        ve_bong_bong(layer, x0 + cw * 0.97, y0 + ch * 0.92, s(26))
        ve_bong_bong(layer, x0 + cw * 0.92, y0 + ch * 1.04, s(15))
        ve_bong_bong(layer, x0 + cw * 1.0, y0 + ch * 1.1, s(9))
    if "tim" in chon:
        ve_tim(dr, x0 + cw * 0.08, y0 + ch * 0.12, s(20), HONG)
        ve_tim(dr, x0 + cw * 0.14, y0 + ch * 0.02, s(12), (255, 180, 205))

    if sao != "an":
        st = ve_ngoi_sao(s(190 * max(ty_le, 0.85)))
        sx = x0 - s(40) if sao == "trai" else x0 + cw - st.width + s(40)
        sy = int(y0 + ch * 0.86 - st.height / 2)
        layer.alpha_composite(st, (int(sx), sy))

    return layer.resize((W, H), Image.LANCZOS)


def main():
    ap = argparse.ArgumentParser(description="Tạo ảnh bìa TikTok theo bộ nhận diện Bé Sao")
    ap.add_argument("anh", nargs="?", help="ảnh nền (jpg/png). Bỏ trống nếu chỉ cần khung trong suốt")
    ap.add_argument("--hook", required=True, help='các dòng cách nhau bằng " / ", thẻ [to] [hong] [the] [vang] [xanh] [nen]')
    ap.add_argument("-o", "--out", help="file kết quả (mặc định <tên ảnh>_bia.jpg)")
    ap.add_argument("--sao", choices=["trai", "phai", "an"], default="trai", help="vị trí ngôi sao")
    ap.add_argument("--diem-nhan", default="tu-dong",
                    help="tu-dong | khong | kết hợp: tia-vang,tia-hong,lap-lanh,bong-bong,tim")
    ap.add_argument("--y", type=int, default=60, help="khoảng cách từ mép trên tới khung (px)")
    ap.add_argument("--khung-trong-suot", action="store_true",
                    help="xuất thêm PNG nền trong suốt để chèn lên video (CapCut/ffmpeg)")
    ap.add_argument("--dau", type=int,
                    help="toạ độ y (px, trên ảnh 1080x1920) của đỉnh đầu người trong ảnh; "
                         "bỏ trống để tự nhận diện khuôn mặt")
    ap.add_argument("--che-dau", action="store_true", help="tắt chế độ tránh che đầu")
    a = ap.parse_args()

    y_top, ty_le, day = a.y, 1.0, 0
    sao = a.sao
    if a.anh:
        nen = nen_9_16(a.anh)
        dau = None
        if not a.che_dau:
            if a.dau is not None:
                dau = a.dau
            else:
                kq = tim_dinh_dau(nen)
                if kq:
                    dau, xt, xp = kq
                    # ngôi sao nằm ngay trên đầu thì chuyển sang phía còn lại
                    if sao == "trai" and xt < 230:
                        sao = "phai" if xp < W - 230 else sao
                    elif sao == "phai" and xp > W - 230:
                        sao = "trai" if xt > 230 else sao
                else:
                    print("Không tự tìm thấy khuôn mặt; nếu khung che đầu hãy chạy lại với --dau <y đỉnh đầu>.")
        if dau is not None:
            y_top, ty_le, day = xep_khung_tranh_dau(a.hook, a.y, dau)
            print(f"Đỉnh đầu ở y≈{dau}px → khung đặt ở y={y_top}, cỡ chữ x{ty_le:.2f}"
                  + (f", đẩy ảnh xuống {day}px" if day else ""))
            if day:
                nen = nen_9_16(a.anh, day)

    lop = tao_lop_phu(a.hook, sao, a.diem_nhan, y_top, ty_le)
    if a.anh:
        base = os.path.splitext(a.anh)[0]
        out = a.out or base + "_bia.jpg"
        nen = nen.convert("RGBA")
        nen.alpha_composite(lop)
        nen.convert("RGB").save(out, quality=95)
        print("Đã lưu ảnh bìa:", out)
        if a.khung_trong_suot:
            p = os.path.splitext(out)[0] + "_khung.png"
            lop.save(p)
            print("Đã lưu khung trong suốt:", p)
    else:
        out = a.out or "khung_hook.png"
        lop.save(out)
        print("Đã lưu khung trong suốt:", out)


if __name__ == "__main__":
    sys.exit(main())
