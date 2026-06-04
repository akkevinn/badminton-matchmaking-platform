"""
Instagram story generator — 1080 x 1920 px.

This renderer is intentionally more editorial than the in-app leaderboard:
- real Prunus Sport logo from assets/prunus-sport.png
- branded hero header
- top-3 podium cards
- compact standings list for the remaining players
- badminton-themed decorative icons for more engaging story output
"""

from __future__ import annotations

import io
import math
import os
from pathlib import Path
from typing import Dict, List

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

W, H = 1080, 1920
ROOT = Path(__file__).resolve().parents[2]
LOGO_PATH = ROOT / "assets" / "prunus-sport.png"


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    paths = (
        [
            "/System/Library/Fonts/HelveticaNeue.ttc",
            "/System/Library/Fonts/Helvetica.ttc",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
        if bold
        else [
            "/System/Library/Fonts/HelveticaNeue.ttc",
            "/System/Library/Fonts/Helvetica.ttc",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    )
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _tw(draw: ImageDraw.ImageDraw, text: str, font) -> int:
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[2] - bb[0]


def _th(draw: ImageDraw.ImageDraw, text: str, font) -> int:
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[3] - bb[1]


def _trim(draw: ImageDraw.ImageDraw, text: str, font, max_w: int) -> str:
    if _tw(draw, text, font) <= max_w:
        return text
    short = text
    while len(short) > 1 and _tw(draw, short + "…", font) > max_w:
        short = short[:-1]
    return short + "…"


def _png(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.convert("RGB").save(buf, "PNG", optimize=True)
    return buf.getvalue()


def _gradient(size, top, bottom) -> Image.Image:
    img = Image.new("RGB", size)
    draw = ImageDraw.Draw(img)
    for y in range(size[1]):
        t = y / max(1, size[1] - 1)
        c = tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3))
        draw.line([(0, y), (size[0], y)], fill=c)
    return img.convert("RGBA")


def _glow(img: Image.Image, color, alpha: int, cx: int, cy: int, r: int) -> Image.Image:
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    for i in range(14, 0, -1):
        ri = r * i // 14
        ai = int(alpha * (1 - i / 14) * 2.2)
        draw.ellipse([cx - ri, cy - ri, cx + ri, cy + ri], fill=(*color, min(255, ai)))
    blur = layer.filter(ImageFilter.GaussianBlur(max(1, r // 4)))
    return Image.alpha_composite(img.convert("RGBA"), blur)


def _court_lines(size, color, alpha: int) -> Image.Image:
    ov = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(ov)
    c = (*color, alpha)
    x1, x2 = 120, size[0] - 120
    y1, y2 = 260, size[1] - 220
    draw.rounded_rectangle([x1, y1, x2, y2], radius=26, outline=c, width=2)
    mx = (x1 + x2) // 2
    my = (y1 + y2) // 2
    draw.line([(mx, y1), (mx, y2)], fill=c, width=2)
    draw.line([(x1, my), (x2, my)], fill=c, width=2)
    inset = 140
    draw.rounded_rectangle([x1 + inset, y1 + 120, x2 - inset, y2 - 120], radius=18, outline=c, width=2)
    return ov


def _dot_grid(size, color, alpha: int, step: int = 46) -> Image.Image:
    ov = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(ov)
    c = (*color, alpha)
    for y in range(0, size[1], step):
        for x in range(0, size[0], step):
            draw.ellipse([x, y, x + 3, y + 3], fill=c)
    return ov


def _hex_pattern(size, color, alpha: int) -> Image.Image:
    ov = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(ov)
    c = (*color, alpha)
    r = 26
    dx = r * math.sqrt(3)
    dy = r * 1.5
    row = 0
    y = 0.0
    while y < size[1] + r * 2:
        ox = dx / 2 if row % 2 else 0
        x = ox
        while x < size[0] + dx:
            pts = [
                (
                    x + r * math.cos(math.radians(60 * i - 30)),
                    y + r * math.sin(math.radians(60 * i - 30)),
                )
                for i in range(6)
            ]
            draw.polygon(pts, outline=c)
            x += dx
        y += dy
        row += 1
    return ov


def _load_logo(size: int) -> Image.Image:
    if LOGO_PATH.exists():
        try:
            img = Image.open(LOGO_PATH).convert("RGBA")
            return ImageOps.contain(img, (size, size))
        except Exception:
            pass
    return Image.new("RGBA", (size, size), (0, 0, 0, 0))


def _circle_badge(logo: Image.Image, size: int, bg, ring) -> Image.Image:
    badge = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(badge)
    draw.ellipse([0, 0, size - 1, size - 1], fill=bg, outline=ring, width=2)
    logo = ImageOps.contain(logo, (int(size * 0.76), int(size * 0.76)))
    lx = (size - logo.width) // 2
    ly = (size - logo.height) // 2
    badge.alpha_composite(logo, (lx, ly))
    return badge


def _draw_shuttlecock(draw: ImageDraw.ImageDraw, x: int, y: int, scale: float, color, alpha: int, angle: float = 0):
    feather = [(0, -64), (-38, -20), (-14, -18), (0, -40), (14, -18), (38, -20)]
    cone = [(-22, -8), (22, -8), (12, 24), (-12, 24)]

    def rot(px, py):
        a = math.radians(angle)
        rx = px * math.cos(a) - py * math.sin(a)
        ry = px * math.sin(a) + py * math.cos(a)
        return x + int(rx * scale), y + int(ry * scale)

    fc = (*color, alpha)
    outline = (*color, min(255, alpha + 20))
    for p1, p2 in zip(feather[::2], feather[1::2]):
        draw.line([rot(*p1), rot(*p2)], fill=fc, width=max(1, int(2 * scale)))
    for px, py in feather:
        draw.line([rot(0, -6), rot(px, py)], fill=fc, width=max(1, int(2 * scale)))
    draw.polygon([rot(*p) for p in cone], outline=outline, fill=(*color, max(30, alpha // 5)))
    draw.line([rot(-18, -8), rot(18, -8)], fill=fc, width=max(1, int(2 * scale)))


def _draw_racket(draw: ImageDraw.ImageDraw, x: int, y: int, scale: float, color, alpha: int, angle: float = -18):
    a = math.radians(angle)

    def rot(px, py):
        rx = px * math.cos(a) - py * math.sin(a)
        ry = px * math.sin(a) + py * math.cos(a)
        return x + int(rx * scale), y + int(ry * scale)

    c = (*color, alpha)
    w = max(2, int(4 * scale))
    draw.ellipse([rot(-34, -54), rot(34, 54)], outline=c, width=w)
    for off in (-18, 0, 18):
        draw.line([rot(off, -42), rot(off, 42)], fill=(*color, max(40, alpha // 2)), width=max(1, int(2 * scale)))
        draw.line([rot(-28, off), rot(28, off)], fill=(*color, max(40, alpha // 2)), width=max(1, int(2 * scale)))
    draw.line([rot(0, 52), rot(0, 122)], fill=c, width=max(3, int(8 * scale)))
    draw.rounded_rectangle([*rot(-9, 116), *rot(9, 162)], radius=6, fill=(*color, min(255, alpha + 20)))


def _card(draw: ImageDraw.ImageDraw, box, fill, outline=None, radius: int = 28):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=2 if outline else 0)


def _text_center(draw: ImageDraw.ImageDraw, box, text: str, font, fill):
    x1, y1, x2, y2 = box
    tw = _tw(draw, text, font)
    th = _th(draw, text, font)
    draw.text((x1 + (x2 - x1 - tw) / 2, y1 + (y2 - y1 - th) / 2), text, font=font, fill=fill)


def _story_base(pal: Dict, fmt: str) -> Image.Image:
    base = _gradient((W, H), pal["bg_top"], pal["bg_bottom"])
    for glow in pal.get("glows", []):
        base = _glow(base, glow["color"], glow["alpha"], glow["x"], glow["y"], glow["r"])

    if fmt in {"midnight", "neon"}:
        base = Image.alpha_composite(base, _court_lines((W, H), pal["pattern"], pal["pattern_alpha"]))
    elif fmt == "daylight":
        base = Image.alpha_composite(base, _dot_grid((W, H), pal["pattern"], pal["pattern_alpha"]))
    else:
        base = Image.alpha_composite(base, _hex_pattern((W, H), pal["pattern"], pal["pattern_alpha"]))

    deco = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(deco)
    dc = pal["deco"]
    _draw_shuttlecock(draw, 140, 230, 1.35, dc, pal["deco_alpha"], -24)
    _draw_shuttlecock(draw, 920, 1510, 1.0, dc, pal["deco_alpha"], 18)
    _draw_racket(draw, 930, 280, 1.3, dc, pal["deco_alpha"], -24)
    _draw_racket(draw, 150, 1640, 1.15, dc, pal["deco_alpha"], 20)
    return Image.alpha_composite(base, deco)


def _draw_header(ov: Image.Image, draw: ImageDraw.ImageDraw, tournament_name: str, pal: Dict):
    logo = _load_logo(170)
    badge = _circle_badge(logo, 132, pal["logo_bg"], pal["logo_ring"])
    ov.alpha_composite(badge, (74, 74))

    f_brand = _font(28, bold=True)
    f_title = _font(74, bold=True)
    f_sub = _font(24, bold=True)
    f_meta = _font(26)

    draw.text((228, 92), "PRUNUS SPORT", font=f_brand, fill=pal["brand"])
    draw.text((228, 132), "BADMINTON SESSION", font=f_sub, fill=pal["muted"])

    max_w = W - 220
    title = tournament_name.upper()
    words = title.split()
    lines = [title]
    if _tw(draw, title, f_title) > max_w and len(words) > 1:
        lines = []
        cur = []
        for w in words:
            attempt = " ".join(cur + [w])
            if cur and _tw(draw, attempt, f_title) > max_w:
                lines.append(" ".join(cur))
                cur = [w]
            else:
                cur.append(w)
        if cur:
            lines.append(" ".join(cur))
        lines = lines[:2]
        if len(lines) == 2:
            lines[1] = _trim(draw, lines[1], f_title, max_w)
    y = 270
    for line in lines:
        draw.text((74, y), line, font=f_title, fill=pal["text"])
        y += _th(draw, line, f_title) + 8

    tag = "FINAL LEADERBOARD"
    tag_font = _font(24, bold=True)
    tw = _tw(draw, tag, tag_font)
    tx, ty = 74, y + 18
    draw.rounded_rectangle([tx, ty, tx + tw + 40, ty + 52], radius=26, fill=pal["tag_bg"])
    draw.text((tx + 20, ty + 13), tag, font=tag_font, fill=pal["tag_text"])

    meta = "Doubles Matchmaking"
    draw.text((W - 78 - _tw(draw, meta, f_meta), ty + 13), meta, font=f_meta, fill=pal["muted"])
    return ty + 96


def _draw_top_three(draw: ImageDraw.ImageDraw, entries: List[Dict], pal: Dict, start_y: int):
    cards = [
        (54, start_y + 136, 318, start_y + 488),   # 2nd
        (334, start_y, 746, start_y + 540),        # 1st
        (762, start_y + 136, 1026, start_y + 488), # 3rd
    ]
    order = [2, 1, 3]
    medal = {1: "CHAMPION", 2: "2ND PLACE", 3: "3RD PLACE"}

    f_rank = _font(22, bold=True)
    f_name_big = _font(42, bold=True)
    f_name = _font(30, bold=True)
    f_pts_big = _font(62, bold=True)
    f_pts = _font(42, bold=True)
    f_meta = _font(22)
    f_skill = _font(24, bold=True)

    by_rank = {e["rank"]: e for e in entries}
    for rank, box in zip(order, cards):
        x1, y1, x2, y2 = box
        entry = by_rank.get(rank)
        fill = pal["podium_fill"]
        outline = pal["podium_outline"]
        if rank == 1:
            fill = pal["podium_fill_1"]
            outline = pal["gold"]
        elif rank == 2:
            outline = pal["silver"]
        elif rank == 3:
            outline = pal["bronze"]
        _card(draw, box, fill, outline, radius=34)

        badge_w = 124 if rank == 1 else 112
        draw.rounded_rectangle([x1 + 24, y1 + 24, x1 + 24 + badge_w, y1 + 68], radius=22, fill=pal["rank_pill"])
        draw.text((x1 + 24 + 18, y1 + 36), medal[rank], font=f_rank, fill=pal["rank_pill_text"])

        if not entry:
            draw.text((x1 + 28, y1 + 110), "Waiting for results", font=f_name, fill=pal["muted"])
            continue

        name_font = f_name_big if rank == 1 else f_name
        pts_font = f_pts_big if rank == 1 else f_pts
        name = _trim(draw, entry["player_name"], name_font, (x2 - x1) - 56)
        draw.text((x1 + 28, y1 + (118 if rank == 1 else 100)), name, font=name_font, fill=pal["text"])

        pts = f"{entry['total_points']} pts"
        draw.text((x1 + 28, y1 + (198 if rank == 1 else 168)), pts, font=pts_font, fill=pal["accent"])

        skill_box = [x1 + 28, y2 - 84, x1 + 128, y2 - 34]
        draw.rounded_rectangle(skill_box, radius=24, fill=pal["skill_bg"])
        _text_center(draw, skill_box, f"Skill {entry['skill']}", f_skill, pal["skill_text"])

        meta = f"W {entry['wins']}  ·  L {entry['losses']}  ·  GP {entry['games_played']}"
        draw.text((x1 + 28, y2 - 136), meta, font=f_meta, fill=pal["muted"])


def _draw_standings(draw: ImageDraw.ImageDraw, entries: List[Dict], pal: Dict, start_y: int):
    panel = [54, start_y, W - 54, H - 160]
    _card(draw, panel, pal["panel_fill"], pal["panel_outline"], radius=34)

    f_title = _font(28, bold=True)
    f_label = _font(18, bold=True)
    f_name = _font(28, bold=True)
    f_meta = _font(21)
    f_score = _font(30, bold=True)
    f_comp = _font(20, bold=True)

    draw.text((84, start_y + 34), "STANDINGS", font=f_title, fill=pal["text"])
    draw.text((W - 280, start_y + 38), "TOTAL POINTS", font=f_label, fill=pal["muted"])

    y = start_y + 96
    row_h = 112
    max_rows = min(len(entries), 8)
    for i, e in enumerate(entries[:max_rows]):
        ry = y + i * row_h
        if ry + row_h > panel[3] - 24:
            break
        fill = pal["row_fill_a"] if i % 2 == 0 else pal["row_fill_b"]
        if e["rank"] == 1:
            fill = pal["row_fill_1"]
        elif e["rank"] == 2:
            fill = pal["row_fill_2"]
        elif e["rank"] == 3:
            fill = pal["row_fill_3"]
        _card(draw, [82, ry, W - 82, ry + 92], fill, None, radius=24)

        rank_box = [104, ry + 20, 174, ry + 72]
        draw.rounded_rectangle(rank_box, radius=22, fill=pal["rank_chip_bg"])
        rank_text = f"#{e['rank']}"
        _text_center(draw, rank_box, rank_text, _font(24, bold=True), pal["rank_chip_text"])

        name = _trim(draw, e["player_name"], f_name, 410)
        draw.text((196, ry + 18), name, font=f_name, fill=pal["text"])
        sub = f"W {e['wins']}  L {e['losses']}  GP {e['games_played']}"
        draw.text((196, ry + 54), sub, font=f_meta, fill=pal["muted"])

        if e["compensation_points"] > 0:
            comp = f"+{e['compensation_points']:.1f} comp"
            draw.text((678, ry + 24), comp, font=f_comp, fill=pal["comp"])

        score = str(e["total_points"])
        sw = _tw(draw, score, f_score)
        draw.text((W - 112 - sw, ry + 28), score, font=f_score, fill=pal["accent"])


def _draw_footer(ov: Image.Image, draw: ImageDraw.ImageDraw, pal: Dict):
    footer_y = H - 120
    logo = _load_logo(74)
    badge = _circle_badge(logo, 64, pal["footer_logo_bg"], pal["footer_logo_ring"])
    ov.alpha_composite(badge, (74, footer_y - 8))

    f_brand = _font(24, bold=True)
    f_note = _font(20)
    draw.text((154, footer_y + 4), "Prunus Sport", font=f_brand, fill=pal["text"])
    draw.text((154, footer_y + 38), "Share this story after the tournament ends", font=f_note, fill=pal["muted"])

    note = "Win = 3 pts  |  Loss = 1 pt  |  compensation included"
    nw = _tw(draw, note, f_note)
    draw.text((W - 78 - nw, footer_y + 22), note, font=f_note, fill=pal["muted"])


def _render_story(tournament_name: str, entries: List[Dict], pal: Dict, fmt: str) -> bytes:
    base = _story_base(pal, fmt)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(ov)

    top_y = _draw_header(ov, draw, tournament_name, pal)
    _draw_top_three(draw, entries, pal, top_y)
    _draw_standings(draw, entries, pal, top_y + 576)
    _draw_footer(ov, draw, pal)
    return _png(Image.alpha_composite(base, ov))


PALETTES = {
    "midnight": {
        "bg_top": (8, 12, 24),
        "bg_bottom": (15, 24, 42),
        "glows": [
            {"color": (16, 185, 129), "alpha": 18, "x": 250, "y": 180, "r": 430},
            {"color": (59, 130, 246), "alpha": 12, "x": 900, "y": 1460, "r": 500},
        ],
        "pattern": (255, 255, 255),
        "pattern_alpha": 20,
        "deco": (173, 255, 220),
        "deco_alpha": 58,
        "text": (244, 248, 255),
        "muted": (150, 173, 204),
        "brand": (207, 248, 231),
        "accent": (34, 197, 94),
        "comp": (144, 174, 255),
        "gold": (250, 204, 21),
        "silver": (189, 198, 216),
        "bronze": (194, 120, 61),
        "logo_bg": (255, 255, 255, 240),
        "logo_ring": (255, 255, 255, 46),
        "footer_logo_bg": (255, 255, 255, 228),
        "footer_logo_ring": (255, 255, 255, 36),
        "tag_bg": (34, 197, 94, 255),
        "tag_text": (8, 18, 12),
        "rank_pill": (255, 255, 255, 28),
        "rank_pill_text": (232, 244, 255),
        "podium_fill": (15, 24, 42, 205),
        "podium_fill_1": (18, 31, 52, 235),
        "podium_outline": (255, 255, 255, 26),
        "panel_fill": (10, 18, 32, 214),
        "panel_outline": (255, 255, 255, 18),
        "row_fill_a": (255, 255, 255, 16),
        "row_fill_b": (255, 255, 255, 8),
        "row_fill_1": (250, 204, 21, 32),
        "row_fill_2": (189, 198, 216, 24),
        "row_fill_3": (194, 120, 61, 24),
        "rank_chip_bg": (255, 255, 255, 22),
        "rank_chip_text": (242, 247, 255),
        "skill_bg": (255, 255, 255, 16),
        "skill_text": (228, 238, 252),
    },
    "daylight": {
        "bg_top": (251, 253, 250),
        "bg_bottom": (231, 245, 236),
        "glows": [
            {"color": (34, 197, 94), "alpha": 10, "x": 200, "y": 240, "r": 360},
            {"color": (110, 231, 183), "alpha": 8, "x": 910, "y": 1440, "r": 420},
        ],
        "pattern": (21, 128, 61),
        "pattern_alpha": 22,
        "deco": (21, 128, 61),
        "deco_alpha": 52,
        "text": (18, 36, 24),
        "muted": (86, 112, 95),
        "brand": (21, 86, 44),
        "accent": (22, 163, 74),
        "comp": (13, 90, 56),
        "gold": (181, 119, 11),
        "silver": (109, 124, 114),
        "bronze": (150, 92, 45),
        "logo_bg": (255, 255, 255, 252),
        "logo_ring": (16, 24, 16, 16),
        "footer_logo_bg": (255, 255, 255, 250),
        "footer_logo_ring": (16, 24, 16, 14),
        "tag_bg": (22, 163, 74, 255),
        "tag_text": (255, 255, 255),
        "rank_pill": (22, 163, 74, 22),
        "rank_pill_text": (22, 86, 44),
        "podium_fill": (255, 255, 255, 212),
        "podium_fill_1": (255, 255, 255, 236),
        "podium_outline": (21, 86, 44, 20),
        "panel_fill": (255, 255, 255, 220),
        "panel_outline": (21, 86, 44, 18),
        "row_fill_a": (22, 163, 74, 16),
        "row_fill_b": (22, 163, 74, 8),
        "row_fill_1": (181, 119, 11, 18),
        "row_fill_2": (109, 124, 114, 14),
        "row_fill_3": (150, 92, 45, 14),
        "rank_chip_bg": (22, 163, 74, 16),
        "rank_chip_text": (22, 86, 44),
        "skill_bg": (22, 163, 74, 12),
        "skill_text": (22, 86, 44),
    },
    "neon": {
        "bg_top": (4, 7, 8),
        "bg_bottom": (5, 14, 16),
        "glows": [
            {"color": (163, 230, 53), "alpha": 22, "x": 260, "y": 200, "r": 440},
            {"color": (34, 211, 238), "alpha": 18, "x": 910, "y": 1320, "r": 460},
        ],
        "pattern": (163, 230, 53),
        "pattern_alpha": 26,
        "deco": (208, 255, 112),
        "deco_alpha": 72,
        "text": (240, 255, 219),
        "muted": (158, 196, 145),
        "brand": (222, 255, 181),
        "accent": (163, 230, 53),
        "comp": (99, 225, 240),
        "gold": (255, 220, 70),
        "silver": (196, 233, 196),
        "bronze": (211, 143, 73),
        "logo_bg": (255, 255, 255, 244),
        "logo_ring": (163, 230, 53, 56),
        "footer_logo_bg": (255, 255, 255, 236),
        "footer_logo_ring": (163, 230, 53, 46),
        "tag_bg": (163, 230, 53, 255),
        "tag_text": (12, 21, 10),
        "rank_pill": (163, 230, 53, 28),
        "rank_pill_text": (229, 255, 197),
        "podium_fill": (10, 19, 14, 218),
        "podium_fill_1": (13, 24, 17, 236),
        "podium_outline": (163, 230, 53, 36),
        "panel_fill": (7, 15, 11, 214),
        "panel_outline": (163, 230, 53, 24),
        "row_fill_a": (163, 230, 53, 14),
        "row_fill_b": (163, 230, 53, 7),
        "row_fill_1": (255, 220, 70, 22),
        "row_fill_2": (196, 233, 196, 18),
        "row_fill_3": (211, 143, 73, 16),
        "rank_chip_bg": (163, 230, 53, 18),
        "rank_chip_text": (235, 255, 214),
        "skill_bg": (163, 230, 53, 14),
        "skill_text": (235, 255, 214),
    },
    "gold": {
        "bg_top": (15, 10, 5),
        "bg_bottom": (29, 20, 10),
        "glows": [
            {"color": (212, 168, 58), "alpha": 20, "x": 260, "y": 240, "r": 430},
            {"color": (255, 214, 120), "alpha": 12, "x": 940, "y": 1260, "r": 420},
        ],
        "pattern": (212, 168, 58),
        "pattern_alpha": 18,
        "deco": (240, 207, 122),
        "deco_alpha": 58,
        "text": (252, 245, 224),
        "muted": (180, 156, 109),
        "brand": (247, 230, 183),
        "accent": (235, 191, 77),
        "comp": (255, 213, 110),
        "gold": (248, 212, 94),
        "silver": (204, 198, 190),
        "bronze": (189, 129, 72),
        "logo_bg": (255, 251, 244, 242),
        "logo_ring": (248, 212, 94, 48),
        "footer_logo_bg": (255, 251, 244, 236),
        "footer_logo_ring": (248, 212, 94, 42),
        "tag_bg": (235, 191, 77, 255),
        "tag_text": (26, 16, 6),
        "rank_pill": (248, 212, 94, 28),
        "rank_pill_text": (250, 239, 199),
        "podium_fill": (34, 24, 12, 220),
        "podium_fill_1": (40, 28, 14, 238),
        "podium_outline": (248, 212, 94, 34),
        "panel_fill": (24, 17, 8, 214),
        "panel_outline": (248, 212, 94, 18),
        "row_fill_a": (248, 212, 94, 10),
        "row_fill_b": (248, 212, 94, 5),
        "row_fill_1": (248, 212, 94, 18),
        "row_fill_2": (204, 198, 190, 14),
        "row_fill_3": (189, 129, 72, 14),
        "rank_chip_bg": (248, 212, 94, 14),
        "rank_chip_text": (250, 240, 208),
        "skill_bg": (248, 212, 94, 12),
        "skill_text": (250, 240, 208),
    },
}


def _format_story(tournament_name: str, entries: List[Dict], fmt: str) -> bytes:
    return _render_story(tournament_name, entries, PALETTES[fmt], fmt)


FORMATS = {
    "midnight": lambda tournament_name, entries: _format_story(tournament_name, entries, "midnight"),
    "daylight": lambda tournament_name, entries: _format_story(tournament_name, entries, "daylight"),
    "neon": lambda tournament_name, entries: _format_story(tournament_name, entries, "neon"),
    "gold": lambda tournament_name, entries: _format_story(tournament_name, entries, "gold"),
}


def generate_story(tournament_name: str, entries: List[Dict], fmt: str = "midnight") -> bytes:
    return FORMATS.get(fmt, FORMATS["midnight"])(tournament_name, entries)
