#!/usr/bin/env python3
"""Generate factory.svg (ASCII gear + slogan + animated belt) for the profile README."""
import math

# ---------- palette (Factorio GUI inspired) ----------
BG = "#1b1b1b"
PANEL = "#242324"
BORDER = "#3c3a3c"
ORANGE = ["#5a2e08", "#8a4610", "#b45f14", "#d9771a", "#f08a1e", "#ffa52b", "#ffb94d", "#ffcf7a", "#ffe3ad"]
TEXT = "#e8e4dc"
DIM = "#6f6a66"
BELT = "#d8a81c"
BELT_DARK = "#8f6c0f"
SI = "#6cb6ff"
U235 = "#7dff3a"
SLOGAN = "#ffa52b"

# ---------- geometry ----------
CW = 7.2          # char width in px
LH = 2 * CW       # line height; 2:1 keeps the gear circular
FS = 12.0         # font size
FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'DejaVu Sans Mono', 'Liberation Mono', monospace"


TEETH = 8
SPOKES = 4          # 4 spokes + 8 teeth share a 90 deg period -> seamless loop
FRAMES = 12         # frames per 90 deg of rotation
FRAME_DUR = 0.3     # seconds per frame


def gear(phase=0.0, W=58, H=29):
    """Render one ASCII gear frame; `phase` rotates teeth and spokes (radians)."""
    aspect = 2.0
    cx, cy = W / 2, H / 2
    r_out, r_body, r_hub, r_hole, teeth = 14.4, 11.0, 5.0, 2.3, TEETH

    def inside(xf, yf):
        dx, dy = (xf - cx) / aspect, yf - cy
        r, a = math.hypot(dx, dy), math.atan2(dy, dx) - phase
        ins = r < r_body or (r < r_out and math.cos(a * teeth + math.pi) > 0.0)
        if not ins or r < r_hole:
            return False
        if r_hub < r < r_body - 1.7:
            for k in range(SPOKES):
                th = k * 2 * math.pi / SPOKES + math.pi / 2 + phase
                d = abs(-math.sin(th) * dx + math.cos(th) * dy)
                along = math.cos(th) * dx + math.sin(th) * dy
                if d < 1.15 and along > 0:
                    break
            else:
                return False
        return True

    ramp = " .:-=+*#%@"
    S = 6
    rows = []
    for y in range(H):
        line = ""
        for x in range(W):
            c = sum(inside(x + (i + .5) / S, y + (j + .5) / S) for i in range(S) for j in range(S))
            f = c / (S * S)
            # cells with little coverage stay empty -> less "dust" on rotated frames
            line += " " if f < 0.3 else ramp[min(9, int((f - 0.3) / 0.7 * 8 + 1.5))]
        rows.append(line)
    return rows


SLOGAN_1 = r"""
 _____ _  _ ___   ___ _   ___ _____ ___  _____   __
|_   _| || | __| | __/_\ / __|_   _/ _ \| _ \ \ / /
  | | | __ | _|  | _/ _ \ (__  | || (_) |   /\ V /
  |_| |_||_|___| |_/_/ \_\___| |_| \___/|_|_\ |_|
""".strip("\n").split("\n")

SLOGAN_2 = r"""
 __  __ _   _ ___ _____    ___ ___  _____      __
|  \/  | | | / __|_   _|  / __| _ \/ _ \ \    / /
| |\/| | |_| \__ \ | |   | (_ |   / (_) \ \/\/ /
|_|  |_|\___/|___/ |_|    \___|_|_\\___/ \_/\_/
""".strip("\n").split("\n")


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(x, y, s, fill, cols=None, extra=""):
    tl = f' textLength="{cols * CW:.1f}" lengthAdjust="spacingAndGlyphs"' if cols else ""
    return f'<text x="{x:.1f}" y="{y:.1f}" fill="{fill}"{tl}{extra}>{esc(s)}</text>'


def gear_text(x, y, line, ramp):
    """One gear row, coloured per character density (tspans grouped by run)."""
    out = []
    run, cur = "", None
    for ch in line:
        lvl = ramp.index(ch)
        if lvl != cur and run:
            out.append((cur, run))
            run = ""
        cur, run = lvl, run + ch
    out.append((cur, run))
    spans = "".join(
        f'<tspan fill="{ORANGE[max(0, lvl - 1)]}">{esc(r)}</tspan>' if lvl else f'<tspan>{esc(r)}</tspan>'
        for lvl, r in out
    )
    return (f'<text x="{x:.1f}" y="{y:.1f}" textLength="{len(line) * CW:.1f}" '
            f'lengthAdjust="spacingAndGlyphs">{spans}</text>')


def belt_svg(x, y, cols):
    """Animated conveyor belt: items + chevrons scroll left under a clip."""
    unit = "[Si]>>>>>>>>>[U235]>>>>>>>>>"
    n = cols // len(unit) + 3
    period = len(unit) * CW
    parts = []
    for i in range(n):
        bx = x + i * len(unit) * CW
        parts.append(text(bx, y, "[Si]", SI, 4))
        parts.append(text(bx + 4 * CW, y, ">>>>>>>>>", BELT_DARK, 9))
        parts.append(text(bx + 13 * CW, y, "[U235]", U235, 6, ' class="u"'))
        parts.append(text(bx + 19 * CW, y, ">>>>>>>>>", BELT_DARK, 9))
    rail = "=" * cols
    return "\n".join([
        text(x, y - LH, rail, BELT, cols),
        f'<g clip-path="url(#beltclip)"><g>'
        f'<animateTransform attributeName="transform" type="translate" '
        f'from="0 0" to="{-period:.1f} 0" dur="3.5s" repeatCount="indefinite"/>',
        *parts,
        '</g></g>',
        text(x, y + LH, rail, BELT, cols),
    ])


def main():
    step = (math.pi / 2) / FRAMES
    frames = [gear(phase=k * step) for k in range(FRAMES)]
    ramp = " .:-=+*#%@"
    g = frames[0]
    GW, GH = len(g[0]), len(g)
    RW = 51                                 # right column width (cols)
    PAD = 2
    GAP = 4
    cols = PAD + GW + GAP + RW + PAD
    rows = GH + 2
    W, H = cols * CW, rows * LH + 6

    gx = PAD * CW
    rx = (PAD + GW + GAP) * CW
    top = LH + 3

    # right column layout: slogan(4) gap slogan(4) gap belt(3) gap status(1) = 15 rows
    right_rows = 4 + 1 + 4 + 2 + 3 + 2 + 1
    ry = top + ((GH - right_rows) // 2) * LH

    body = []
    total = FRAMES * FRAME_DUR
    for k, frame in enumerate(frames):
        vis = ";".join("1" if i == k else "0" for i in range(FRAMES))
        keys = ";".join(f"{i / FRAMES:.4f}" for i in range(FRAMES))
        body.append(f'<g opacity="{1 if k == 0 else 0}">'
                    f'<animate attributeName="opacity" values="{vis}" keyTimes="{keys}" '
                    f'calcMode="discrete" dur="{total}s" repeatCount="indefinite"/>')
        for i, line in enumerate(frame):
            body.append(gear_text(gx, top + i * LH, line, ramp))
        body.append('</g>')

    y = ry
    for line in SLOGAN_1:
        body.append(text(rx, y, line.ljust(RW), TEXT, RW)); y += LH
    y += LH
    for line in SLOGAN_2:
        body.append(text(rx, y, line.ljust(RW), SLOGAN, RW)); y += LH
    y += 2 * LH
    belt_y = y + LH
    body.append(belt_svg(rx, belt_y, RW))
    y = belt_y + 3 * LH
    status = "power 100%   inserters ok   biters none   alt-mode on"
    body.append(text(rx, y, status.ljust(RW), DIM, RW))

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" width="{W:.0f}" height="{H:.0f}" role="img" aria-label="The factory must grow">
<style>
  text {{ font-family: {FONT}; font-size: {FS}px; white-space: pre; }}
  .u {{ filter: url(#glow); animation: pulse 1.6s ease-in-out infinite; }}
  @keyframes pulse {{ 0%,100% {{ opacity: .75 }} 50% {{ opacity: 1 }} }}
</style>
<defs>
  <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur stdDeviation="1.6" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <clipPath id="beltclip"><rect x="{rx:.1f}" y="{belt_y - LH + 2:.1f}" width="{RW * CW:.1f}" height="{LH:.1f}"/></clipPath>
</defs>
<rect width="100%" height="100%" rx="6" fill="{PANEL}" stroke="{BORDER}"/>
{chr(10).join(body)}
</svg>
'''
    with open("factory.svg", "w") as f:
        f.write(svg)
    print(f"factory.svg written: {cols} cols x {rows} rows -> {W:.0f}x{H:.0f}px")


if __name__ == "__main__":
    main()
