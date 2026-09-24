"""Render a concise, editable daily review mind map as SVG."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from xml.sax.saxutils import escape

WIDTH = 2048
HEIGHT = 1180
CARD_W = 596
CARD_H = 252
ROWS = {3: [196, 494, 792], 2: [270, 718], 1: [494]}
PALETTE = [
    ("#607D6B", "#E7EFE9"),
    ("#6D8794", "#E8F0F3"),
    ("#A17C60", "#F4EDE5"),
    ("#8D7793", "#F0EAF1"),
    ("#A57976", "#F3E9E7"),
    ("#748C78", "#E9F0E9"),
]


def category_colors(data: dict) -> dict[str, tuple[str, str]]:
    categories = list(dict.fromkeys(item["category"] for item in data["branches"]))
    return {name: PALETTE[i] for i, name in enumerate(categories)}


def safe(value: object) -> str:
    return escape(str(value), {'"': "&quot;", "'": "&apos;"})


def text(x: int, y: int, value: object, css: str) -> str:
    return f'<text x="{x}" y="{y}" class="{css}">{safe(value)}</text>'


def card(item: dict, x: int, y: int, index: int,
         colors: dict[str, tuple[str, str]]) -> str:
    category = item["category"]
    accent, tint = colors[category]
    error = item.get("error")
    label = f"{error.get('label', '错题')} {error['number']:02d}" if error else "方法自检"
    note = error["mistake"] if error else item["check"]
    fix = error["fix"] if error else item["check_fix"]
    out = [
        f'<g aria-label="{safe(item["title"])}">',
        f'<rect x="{x}" y="{y}" width="{CARD_W}" height="{CARD_H}" rx="21" fill="#FFFFFF" stroke="#DDE3DD" stroke-width="1.5" filter="url(#soft-shadow)"/>',
        f'<rect x="{x}" y="{y + 26}" width="5" height="54" rx="2.5" fill="{accent}"/>',
        text(x + 31, y + 46, f"{index:02d}", "number"),
        f'<rect x="{x + CARD_W - 91}" y="{y + 25}" width="62" height="31" rx="15.5" fill="{tint}"/>',
        f'<text x="{x + CARD_W - 60}" y="{y + 46}" text-anchor="middle" class="category" fill="{accent}">{safe(category)}</text>',
        text(x + 31, y + 88, item["title"], "card-title"),
        text(x + 31, y + 126, item["rule"], "card-rule"),
        text(x + 31, y + 157, item["detail"], "card-detail"),
        f'<line x1="{x + 30}" y1="{y + 177}" x2="{x + CARD_W - 30}" y2="{y + 177}" stroke="#E6E8E3" stroke-width="1"/>',
        f'<circle cx="{x + 39}" cy="{y + 198}" r="4" fill="{("#B4775D" if error else accent)}"/>',
        text(x + 53, y + 204, label, "note-label error" if error else "note-label"),
        text(x + 198, y + 204, note, "note-text"),
        text(x + 31, y + 229, fix, "fix-text"),
        "</g>",
    ]
    return "\n".join(out)


def make_svg(data: dict) -> str:
    branches = data["branches"]
    if not 4 <= len(branches) <= 6:
        raise ValueError("Use 4 to 6 main branches")
    sides = {side: [item for item in branches if item["side"] == side] for side in ("left", "right")}
    if any(len(items) not in ROWS for items in sides.values()):
        raise ValueError("Each side must contain 1 to 3 branches")
    if sum(1 for item in branches if item.get("error")) != data["error_count"]:
        raise ValueError("error_count does not match branch data")
    colors = category_colors(data)

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}" role="img" aria-labelledby="map-title map-desc">',
           f'<title id="map-title">{safe(data["title"])}</title>',
           f'<desc id="map-desc">{safe(data["description"])}</desc>',
           '''<defs>
  <filter id="soft-shadow" x="-20%" y="-20%" width="140%" height="150%">
    <feDropShadow dx="0" dy="8" stdDeviation="12" flood-color="#4D6253" flood-opacity=".065"/>
  </filter>
  <style>
    text { font-family: "Noto Sans CJK SC", "Noto Sans SC", "Microsoft YaHei", "PingFang SC", sans-serif; fill: #27332D; }
    .eyebrow { font-size: 17px; font-weight: 700; letter-spacing: 2px; fill: #65746B; }
    .main-title { font-size: 50px; font-weight: 700; letter-spacing: 1px; }
    .subtitle { font-size: 22px; fill: #69776E; }
    .status { font-size: 18px; font-weight: 700; fill: #805A48; }
    .number { font-size: 19px; font-weight: 700; fill: #8B9890; }
    .category { font-size: 16px; font-weight: 700; }
    .card-title { font-size: 30px; font-weight: 700; }
    .card-rule { font-size: 22px; font-weight: 500; }
    .card-detail { font-size: 20px; fill: #67746B; }
    .note-label { font-size: 18px; font-weight: 700; fill: #607D6B; }
    .note-label.error { fill: #A36A52; }
    .note-text { font-size: 19px; fill: #5E6961; }
    .fix-text { font-size: 19px; font-weight: 600; fill: #4C6755; }
    .core-small { font-size: 18px; font-weight: 700; letter-spacing: 2px; fill: #BDD0C2; }
    .core-title { font-size: 48px; font-weight: 700; fill: #FFFFFF; }
    .core-subtitle { font-size: 25px; fill: #E0E8E0; }
    .core-count { font-size: 23px; font-weight: 600; fill: #FFFFFF; }
    .core-foot { font-size: 18px; fill: #C0CFC2; }
    .footer { font-size: 19px; fill: #66756A; }
    .footer-strong { font-size: 19px; font-weight: 700; fill: #344338; }
  </style>
</defs>''',
           f'<rect width="{WIDTH}" height="{HEIGHT}" fill="#F6F5F0"/>',
           '<circle cx="1024" cy="630" r="297" fill="#EDEFE9" opacity=".55"/>',
           text(76, 76, data["eyebrow"], "eyebrow"),
           text(76, 137, data["title"], "main-title"),
           text(78, 170, data["subtitle"], "subtitle"),
           f'<rect x="1553" y="87" width="414" height="45" rx="22.5" fill="#F3E7DF"/>',
           text(1581, 117, data["status"], "status"),
           '<line x1="76" y1="183" x2="1972" y2="183" stroke="#D8DFD7" stroke-width="1.5"/>']

    # Connections stay behind the topic nodes
    for side in ("left", "right"):
        items = sides[side]
        for j, (item, y) in enumerate(zip(items, ROWS[len(items)])):
            target_y = y + CARD_H // 2
            if side == "left":
                source_x, target_x = 772, 670
                source_y = [572, 630, 688][j] if len(items) == 3 else ([590, 670][j] if len(items) == 2 else 630)
                path = f'M {source_x} {source_y} C 704 {source_y}, 726 {target_y}, {target_x} {target_y}'
            else:
                source_x, target_x = 1276, 1378
                source_y = [572, 630, 688][j] if len(items) == 3 else ([590, 670][j] if len(items) == 2 else 630)
                path = f'M {source_x} {source_y} C 1344 {source_y}, 1322 {target_y}, {target_x} {target_y}'
            accent = colors[item["category"]][0]
            out.append(f'<path d="{path}" fill="none" stroke="{accent}" stroke-width="3.4" stroke-linecap="round" opacity=".8"/>')
            out.append(f'<circle cx="{target_x}" cy="{target_y}" r="5.5" fill="{accent}"/>')

    # Center concept: dark anchor for the six branches
    out.extend([
        '<rect x="772" y="473" width="504" height="314" rx="34" fill="#293A30" filter="url(#soft-shadow)"/>',
        '<circle cx="1024" cy="509" r="4" fill="#91B49B"/>',
        f'<text x="1024" y="520" text-anchor="middle" class="core-small">{safe(data["core_label"])}</text>',
        f'<text x="1024" y="601" text-anchor="middle" class="core-title">{safe(data["core_title"])}</text>',
        f'<text x="1024" y="646" text-anchor="middle" class="core-subtitle">{safe(data["core_subtitle"])}</text>',
        '<line x1="846" y1="682" x2="1202" y2="682" stroke="#799183" stroke-width="1.5"/>',
        f'<text x="1024" y="724" text-anchor="middle" class="core-count">{safe(data["workload"])}</text>',
        f'<text x="1024" y="755" text-anchor="middle" class="core-foot">{safe(data["core_foot"])}</text>',
    ])

    for side, x in (("left", 74), ("right", 1378)):
        items = sides[side]
        for j, (item, y) in enumerate(zip(items, ROWS[len(items)])):
            out.append(card(item, x, y, j + 1 if side == "left" else len(sides["left"]) + j + 1, colors))

    out.extend([
        '<line x1="76" y1="1095" x2="1972" y2="1095" stroke="#D8DFD7" stroke-width="1.5"/>',
        text(76, 1130, data["legend"], "footer-strong"),
        text(488, 1130, data["note_legend"], "footer"),
        text(1972, 1130, data["footer"], "footer" ).replace('x="1972"', 'x="1972" text-anchor="end"'),
        '</svg>',
    ])
    return "\n".join(out) + "\n"


def find_font(explicit: Path | None, bold: bool = False) -> Path:
    candidates = [
        explicit,
        Path(os.environ["GOOD_LEARNING_FONT"]) if os.environ.get("GOOD_LEARNING_FONT") else None,
        Path("C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/NotoSansSC-VF.ttf"),
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
        Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
        Path("/System/Library/Fonts/PingFang.ttc"),
    ]
    for path in candidates:
        if path and path.is_file():
            return path
    raise RuntimeError("No Chinese font found; supply --font and --bold-font for PNG output")


def make_png(data: dict, output: Path, regular_font: Path | None,
             bold_font: Path | None) -> None:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont

    scale = 2
    image = Image.new("RGB", (WIDTH * scale, HEIGHT * scale), "#F6F5F0")
    draw = ImageDraw.Draw(image)
    regular_path = find_font(regular_font)
    bold_path = find_font(bold_font or regular_font, bold=True)
    colors = category_colors(data)
    fonts: dict[tuple[int, bool], ImageFont.FreeTypeFont] = {}

    def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
        key = (size, bold)
        if key not in fonts:
            fonts[key] = ImageFont.truetype(bold_path if bold else regular_path, size * scale)
        return fonts[key]

    def rect(box: tuple[int, int, int, int], radius: int, fill: str,
             outline: str | None = None, width: int = 1) -> None:
        draw.rounded_rectangle(tuple(v * scale for v in box), radius * scale,
                               fill=fill, outline=outline, width=width * scale)

    def line(points: list[tuple[float, float]], fill: str, width: int = 1) -> None:
        draw.line([(int(x * scale), int(y * scale)) for x, y in points],
                  fill=fill, width=width * scale, joint="curve")

    def circle(x: float, y: float, radius: float, fill: str) -> None:
        draw.ellipse(((x-radius)*scale, (y-radius)*scale,
                      (x+radius)*scale, (y+radius)*scale), fill=fill)

    def write(x: int, y: int, value: object, size: int, fill: str,
              bold: bool = False, anchor: str = "lt") -> None:
        draw.text((x*scale, y*scale), str(value), font=font(size, bold),
                  fill=fill, anchor=anchor)

    def shadow(box: tuple[int, int, int, int], radius: int) -> None:
        layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        offset = 7
        ld.rounded_rectangle(((box[0])*scale, (box[1]+offset)*scale,
                              box[2]*scale, (box[3]+offset)*scale),
                             radius*scale, fill=(55, 79, 61, 22))
        image.paste(Image.alpha_composite(image.convert("RGBA"),
                                         layer.filter(ImageFilter.GaussianBlur(10*scale))).convert("RGB"))

    def curve(p0: tuple[float, float], p1: tuple[float, float],
              p2: tuple[float, float], p3: tuple[float, float], color: str) -> None:
        points = []
        for n in range(41):
            t = n / 40
            u = 1 - t
            x = u**3*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t**3*p3[0]
            y = u**3*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t**3*p3[1]
            points.append((x, y))
        line(points, color, 4)

    # Header and a quiet halo around the central concept
    circle(1024, 630, 297, "#EDEFE9")
    write(76, 53, data["eyebrow"], 17, "#65746B", True)
    write(76, 92, data["title"], 50, "#27332D", True)
    write(78, 149, data["subtitle"], 22, "#69776E")
    rect((1553, 87, 1967, 132), 23, "#F3E7DF")
    write(1581, 100, data["status"], 18, "#805A48", True)
    line([(76, 183), (1972, 183)], "#D8DFD7", 2)

    sides = {side: [item for item in data["branches"] if item["side"] == side]
             for side in ("left", "right")}
    for side in ("left", "right"):
        items = sides[side]
        for j, (item, y) in enumerate(zip(items, ROWS[len(items)])):
            ty = y + CARD_H / 2
            sy = [572, 630, 688][j] if len(items) == 3 else ([590, 670][j] if len(items) == 2 else 630)
            color = colors[item["category"]][0]
            if side == "left":
                curve((772, sy), (704, sy), (726, ty), (670, ty), color)
                circle(670, ty, 5.5, color)
            else:
                curve((1276, sy), (1344, sy), (1322, ty), (1378, ty), color)
                circle(1378, ty, 5.5, color)

    # Center
    shadow((772, 473, 1276, 787), 34)
    rect((772, 473, 1276, 787), 34, "#293A30")
    circle(1024, 509, 4, "#91B49B")
    write(1024, 505, data["core_label"], 18, "#BDD0C2", True, "mt")
    write(1024, 553, data["core_title"], 48, "#FFFFFF", True, "mt")
    write(1024, 621, data["core_subtitle"], 25, "#E0E8E0", False, "mt")
    line([(846, 682), (1202, 682)], "#799183", 2)
    write(1024, 705, data["workload"], 23, "#FFFFFF", True, "mt")
    write(1024, 745, data["core_foot"], 18, "#C0CFC2", False, "mt")

    # Topic cards and their attached review points
    for side, x in (("left", 74), ("right", 1378)):
        items = sides[side]
        for j, (item, y) in enumerate(zip(items, ROWS[len(items)])):
            category = item["category"]
            accent, tint = colors[category]
            shadow((x, y, x+CARD_W, y+CARD_H), 21)
            rect((x, y, x+CARD_W, y+CARD_H), 21, "#FFFFFF", "#DDE3DD", 2)
            rect((x, y+26, x+5, y+80), 2, accent)
            index = j+1 if side == "left" else len(sides["left"])+j+1
            write(x+31, y+27, f"{index:02d}", 19, "#8B9890", True)
            rect((x+CARD_W-91, y+25, x+CARD_W-29, y+56), 16, tint)
            write(x+CARD_W-60, y+30, category, 16, accent, True, "mt")
            write(x+31, y+62, item["title"], 30, "#27332D", True)
            write(x+31, y+108, item["rule"], 22, "#27332D")
            write(x+31, y+141, item["detail"], 20, "#67746B")
            line([(x+30, y+177), (x+CARD_W-30, y+177)], "#E6E8E3")
            error = item.get("error")
            circle(x+39, y+198, 4, "#B4775D" if error else accent)
            label = f"{error.get('label', '错题')} {error['number']:02d}" if error else "方法自检"
            write(x+53, y+187, label, 18, "#A36A52" if error else accent, True)
            write(x+198, y+187, error["mistake"] if error else item["check"], 19, "#5E6961")
            write(x+31, y+217, error["fix"] if error else item["check_fix"], 19, "#4C6755", True)

    line([(76, 1095), (1972, 1095)], "#D8DFD7", 2)
    write(76, 1114, data["legend"], 19, "#344338", True)
    write(488, 1114, data["note_legend"], 19, "#66756A")
    footer_width = draw.textlength(data["footer"], font=font(19)) / scale
    write(int(1972-footer_width), 1114, data["footer"], 19, "#66756A")

    output.parent.mkdir(parents=True, exist_ok=True)
    image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).save(output, optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--png", type=Path)
    parser.add_argument("--font", type=Path)
    parser.add_argument("--bold-font", type=Path)
    args = parser.parse_args()
    data = json.loads(args.source.read_text(encoding="utf-8"))
    svg = make_svg(data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(svg, encoding="utf-8")
    if args.png:
        make_png(data, args.png, args.font, args.bold_font)


if __name__ == "__main__":
    main()
