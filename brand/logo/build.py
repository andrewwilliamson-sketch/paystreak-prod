"""Generate the Paystreak Data logo SVGs.

Wordmarks are converted to outlines so the files render the same everywhere
(no font dependency). Fonts are not checked in; download the static TTFs from
Google Fonts into FONT_DIR before running:

  caslon-400.ttf   Libre Caslon Text 400
  intert-600.ttf   Inter Tight 600
  sserif-600.ttf   Source Serif 4 600 (opsz 60)

Usage: python3 build.py FONT_DIR
Requires: fonttools, uharfbuzz
"""
import math
import os
import sys

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "fonts")

INK = "#1B1915"      # deep charcoal, warm
GOLD = "#C9A227"
PAPER = "#F6F3EC"    # off-white

# Colour schemes: (strata, seam, text)
SCHEMES = {
    "light": (INK, GOLD, INK),            # for light backgrounds
    "dark": (PAPER, GOLD, PAPER),         # for dark backgrounds
    "mono-black": (INK, INK, INK),
    "mono-white": (PAPER, PAPER, PAPER),
}


def f(n):
    s = f"{n:.2f}".rstrip("0").rstrip(".")
    return "0" if s == "-0" else s


# ---------------------------------------------------------------- geometry

def clip(poly, a, b, c):
    """Keep the part of convex polygon `poly` where a*x + b*y <= c."""
    out = []
    for i, p in enumerate(poly):
        q = poly[(i + 1) % len(poly)]
        dp = a * p[0] + b * p[1] - c
        dq = a * q[0] + b * q[1] - c
        if dp <= 0:
            out.append(p)
        if (dp < 0 < dq) or (dq < 0 < dp):
            t = dp / (dp - dq)
            out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
    return out


def rect(x, y, w, h):
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def path(poly):
    return "M" + "L".join(f"{f(x)} {f(y)}" for x, y in poly) + "Z"


def seam_lines(p0, p1, half):
    """Two parallel half-planes either side of the line p0->p1, `half` apart
    from it. Returns (a, b, c) for the line normal form a*x + b*y = c."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy)
    a, b = dy / L, -dx / L          # unit normal
    c = a * p0[0] + b * p0[1]
    return a, b, c, half


def split_by_band(poly, band):
    """Return the pieces of `poly` outside the band |a*x+b*y-c| <= half."""
    a, b, c, half = band
    left = clip(poly, a, b, c - half)
    right = clip(poly, -a, -b, -(c + half))
    return [p for p in (left, right) if len(p) >= 3]


def inside_band(poly, band):
    a, b, c, half = band
    p = clip(poly, a, b, c + half)
    p = clip(p, -a, -b, -(c - half))
    return p


# ---------------------------------------------------------------- marks
# Every mark is drawn on a 48 x 48 grid: at 16px one unit is 1/3 px, so
# bars are kept >= 9 units (3px) and gaps >= 4 units (1.3px).

def area(poly):
    return abs(sum(p[0] * q[1] - q[0] * p[1]
                   for p, q in zip(poly, poly[1:] + poly[:1]))) / 2


def circle_poly(cx, cy, r, n=96):
    return [(cx + r * math.cos(2 * math.pi * i / n),
             cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def within(poly, shape):
    """Intersect convex `poly` with convex polygon `shape`."""
    cx = sum(p[0] for p in shape) / len(shape)
    cy = sum(p[1] for p in shape) / len(shape)
    for i, p in enumerate(shape):
        q = shape[(i + 1) % len(shape)]
        a, b = q[1] - p[1], -(q[0] - p[0])
        c = a * p[0] + b * p[1]
        if a * cx + b * cy > c:      # keep the side the centre is on
            a, b, c = -a, -b, -c
        poly = clip(poly, a, b, c)
        if len(poly) < 3:
            return []
    return poly


def build(beds, seam_axis, cut, vein, shape=None, min_area=12):
    cut_b = seam_lines(*seam_axis, cut)
    vein_b = seam_lines(*seam_axis, vein)
    rock = []
    for bed in beds:
        if shape:
            bed = within(bed, shape)
        rock += [p for p in split_by_band(bed, cut_b) if area(p) >= min_area]
    gold = inside_band(shape or rect(0, 0, 48, 48), vein_b)
    return rock, [gold]


def mark_v1():
    """Strata: four horizontal beds cut by one gold seam at a low, natural dip."""
    beds = [rect(0, y, 48, 9) for y in (0, 13, 26, 39)]
    return build(beds, (SEAM_V1[0], SEAM_V1[1]), 6.2, 3.4)


def mark_v2():
    """Fault: the beds step down across the seam, as a real vein offsets rock."""
    a, b = SEAM_V2
    cut_b = seam_lines(a, b, 6.4)
    vein_b = seam_lines(a, b, 3.6)
    sq = rect(0, 0, 48, 48)

    def side(pieces, want_left):
        return [p for p in pieces
                if (sum(x for x, _ in p) / len(p) < 24) == want_left]

    rock = []
    for y in (0, 19, 38):                       # left: three beds
        rock += side(split_by_band(rect(0, y, 48, 10), cut_b), True)
    for y in (9.5, 28.5):                       # right: offset half a step
        rock += side(split_by_band(rect(0, y, 48, 10), cut_b), False)
    rock = [p for p in (within(p, sq) for p in rock) if p and area(p) >= 12]
    return rock, [inside_band(sq, vein_b)]


def mark_v3():
    """Core: a round core sample (and a seal) with beds and the seam."""
    shape = circle_poly(24, 24, 24)
    beds = [rect(0, y, 48, 10) for y in (0, 12.67, 25.33, 38)]
    return build(beds, (SEAM_V3[0], SEAM_V3[1]), 6.0, 3.3, shape=shape, min_area=30)


SEAM_V1 = ((0, 41), (48, 7))
SEAM_V2 = ((7, 48), (41, 0))
SEAM_V3 = ((0, 40), (48, 8))


MARKS = {"v1": mark_v1, "v2": mark_v2, "v3": mark_v3}


def mark_group(key, scheme, x=0, y=0, s=1.0):
    rock, gold = MARKS[key]()
    strata, seam, _ = SCHEMES[scheme]
    rock_d = "".join(path(p) for p in rock)
    gold_d = "".join(path(p) for p in gold)
    t = f' transform="translate({f(x)} {f(y)}) scale({f(s)})"' if (x or y or s != 1) else ""
    return (f'<g{t}><path fill="{strata}" d="{rock_d}"/>'
            f'<path fill="{seam}" d="{gold_d}"/></g>')


# ---------------------------------------------------------------- type

def text_path(font_file, text, size, tracking=0.0, features=None):
    """Shape `text` with HarfBuzz and return (svg path d, width, cap height).
    Coordinates: baseline at y=0, y grows downwards."""
    blob = hb.Blob.from_file_path(font_file)
    face = hb.Face(blob)
    font = hb.Font(face)
    upem = face.upem
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, features or {"kern": True, "liga": True})

    tt = TTFont(font_file)
    gs = tt.getGlyphSet()
    order = tt.getGlyphOrder()
    scale = size / upem
    pen = SVGPathPen(gs)
    x = 0.0
    track = tracking * upem
    n = len(buf.glyph_infos)
    for i, (info, pos) in enumerate(zip(buf.glyph_infos, buf.glyph_positions)):
        name = order[info.codepoint]
        tp = TransformPen(pen, (scale, 0, 0, -scale,
                                (x + pos.x_offset) * scale, -pos.y_offset * scale))
        gs[name].draw(tp)
        x += pos.x_advance + (track if i < n - 1 else 0)
    cap = tt["OS/2"].sCapHeight * scale
    return pen.getCommands(), x * scale, cap


def fonts():
    return {
        "caslon": os.path.join(FONT_DIR, "caslon-400.ttf"),
        "inter": os.path.join(FONT_DIR, "intert-600.ttf"),
        "sserif": os.path.join(FONT_DIR, "sserif-600.ttf"),
    }


# ---------------------------------------------------------------- lockups

def lockup(key, scheme):
    F = fonts()
    _, _, ink = SCHEMES[scheme]
    if key == "v1":
        # Mark 48 tall; Caslon cap height aligned to the mark's outer beds.
        size = 46
        d, w, cap = text_path(F["caslon"], "Paystreak Data", size, tracking=0.01)
        mark_h = 48
        gap = 20
        base = (mark_h + cap) / 2  # optically centre caps on mark
        tx = mark_h + gap
        width = tx + w
        body = (mark_group(key, scheme) +
                f'<path fill="{ink}" transform="translate({f(tx)} {f(base)})" d="{d}"/>')
        return width, mark_h, body
    if key == "v2":
        size = 40
        d, w, cap = text_path(F["inter"], "Paystreak Data", size, tracking=-0.012)
        mark_h = 48
        gap = 18
        base = (mark_h + cap) / 2
        tx = mark_h + gap
        width = tx + w
        body = (mark_group(key, scheme) +
                f'<path fill="{ink}" transform="translate({f(tx)} {f(base)})" d="{d}"/>')
        return width, mark_h, body
    if key == "v3":
        # Stacked, tracked capitals: PAYSTREAK over DATA, private-bank style.
        mark_h = 56
        d1, w1, cap1 = text_path(F["sserif"], "PAYSTREAK", 36, tracking=0.11)
        d2, w2, cap2 = text_path(F["sserif"], "DATA", 17, tracking=0.42)
        line_gap = 10
        block = cap1 + line_gap + cap2
        top = (mark_h - block) / 2
        tx = mark_h + 18
        width = tx + max(w1, w2)
        s = mark_h / 48
        # DATA sits after a short gold-free hairline rule so the stack reads as one name
        rule_w = max(w1 - w2 - 10, 0)
        body = (mark_group(key, scheme, s=s) +
                f'<path fill="{ink}" transform="translate({f(tx)} {f(top + cap1)})" d="{d1}"/>'
                f'<path fill="{ink}" transform="translate({f(tx)} {f(top + block)})" d="{d2}"/>'
                f'<rect fill="{ink}" x="{f(tx + w2 + 10)}" y="{f(top + block - cap2 / 2 - 0.75)}" '
                f'width="{f(rule_w)}" height="1.5"/>')
        return width, mark_h, body
    raise KeyError(key)


def svg(width, height, body, title, pad=0):
    w, h = width + 2 * pad, height + 2 * pad
    inner = f'<g transform="translate({f(pad)} {f(pad)})">{body}</g>' if pad else body
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {f(w)} {f(h)}" '
            f'width="{f(w)}" height="{f(h)}" role="img" aria-label="{title}">'
            f'<title>{title}</title>{inner}</svg>\n')


def favicon(key):
    """Mark on a charcoal tile so it reads on light and dark browser chrome."""
    inner = mark_group(key, "dark", x=5, y=5, s=38 / 48)
    body = f'<rect width="48" height="48" rx="6" fill="{INK}"/>{inner}'
    return svg(48, 48, body, "Paystreak Data")


NAMES = {"v1": "strata", "v2": "fault", "v3": "core"}


def main():
    for key, name in NAMES.items():
        out = os.path.join(HERE, f"{key}-{name}")
        os.makedirs(out, exist_ok=True)
        for scheme in SCHEMES:
            w, h, body = lockup(key, scheme)
            with open(os.path.join(out, f"paystreak-{key}-lockup-{scheme}.svg"), "w") as fh:
                fh.write(svg(w, h, body, "Paystreak Data"))
            with open(os.path.join(out, f"paystreak-{key}-mark-{scheme}.svg"), "w") as fh:
                fh.write(svg(48, 48, mark_group(key, scheme), "Paystreak Data"))
        with open(os.path.join(out, f"paystreak-{key}-favicon.svg"), "w") as fh:
            fh.write(favicon(key))
        print("wrote", out)


if __name__ == "__main__":
    main()
