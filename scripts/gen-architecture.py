#!/usr/bin/env python3
"""Generate docs/architecture.png for the sonar-vortex kit.

Pure Pillow, no external services. Renders at 2x and downsamples with LANCZOS
for crisp anti-aliased edges/text. Arrows are orthogonal and routed through
clear lanes; labels sit in gaps so nothing crosses a box edge or a line.

    python3 scripts/gen-architecture.py
"""
import math
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "docs", "architecture.png")

S = 2                      # supersample factor
W, H = 1640, 900           # final size
CW, CH = W * S, H * S

# palette
WHITE = (255, 255, 255)
INK = (31, 41, 55)
MUTED = (107, 114, 128)
LINE = (100, 116, 139)

SBX_FILL = (238, 244, 255)
SBX_EDGE = (76, 111, 255)
BOX_FILL = (255, 255, 255)
BOX_EDGE = (148, 163, 184)
PROXY_FILL = (255, 247, 237)
PROXY_EDGE = (245, 158, 11)
PROXY_INK = (176, 106, 0)
CLOUD_FILL = (245, 243, 255)
CLOUD_EDGE = (124, 58, 237)
GREEN = (16, 133, 71)
GREEN_FILL = (236, 253, 245)
RED = (200, 60, 60)
RED_FILL = (253, 242, 242)


def font(size, bold=False):
    names = ["Arial Bold.ttf", "Helvetica.ttc"] if bold else ["Arial.ttf", "Helvetica.ttc"]
    roots = ["/System/Library/Fonts/Supplemental/", "/System/Library/Fonts/", "/Library/Fonts/"]
    for n in names:
        for r in roots:
            p = os.path.join(r, n)
            if os.path.exists(p):
                try:
                    return ImageFont.truetype(p, size * S)
                except Exception:
                    pass
    return ImageFont.load_default()


img = Image.new("RGB", (CW, CH), WHITE)
d = ImageDraw.Draw(img)


def box(x, y, w, h, fill, edge, width=2, radius=16):
    d.rounded_rectangle([x * S, y * S, (x + w) * S, (y + h) * S],
                        radius=radius * S, fill=fill, outline=edge, width=width * S)


def text(x, y, s, f, fill=INK, anchor="la"):
    d.text((x * S, y * S), s, font=f, fill=fill, anchor=anchor)


def _head(x, y, ang, color, width):
    L = 13 * S
    for a in (ang + math.radians(150), ang - math.radians(150)):
        d.line([x, y, x + L * math.cos(a), y + L * math.sin(a)], fill=color, width=width * S)


def poly(points, color=LINE, width=3, dash=False):
    """Orthogonal polyline in data coords; arrowhead at the final point."""
    pts = [(x * S, y * S) for x, y in points]
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        if dash:
            total = math.hypot(x2 - x1, y2 - y1)
            if total == 0:
                continue
            dx, dy = (x2 - x1) / total, (y2 - y1) / total
            step, on = 15 * S, 9 * S
            t = 0.0
            while t < total:
                a, b = t, min(t + on, total)
                d.line([x1 + dx * a, y1 + dy * a, x1 + dx * b, y1 + dy * b], fill=color, width=width * S)
                t += step
        else:
            d.line([x1, y1, x2, y2], fill=color, width=width * S)
    (px, py), (qx, qy) = pts[-2], pts[-1]
    _head(qx, qy, math.atan2(qy - py, qx - px), color, width)


f_title = font(30, bold=True)
f_sub = font(15)
f_h = font(19, bold=True)
f_b = font(14)
f_bs = font(12)
f_lbl = font(12, bold=True)
f_tag = font(12, bold=True)

# ---- title ----------------------------------------------------------------
text(50, 34, "Sonar Vortex — Docker Sandboxes kit", f_title)
text(50, 76, "Repo-aware context before the agent writes, real-time SonarQube verification after — token never enters the container.",
     f_sub, fill=MUTED)

# ==== boxes ================================================================
# Docker Sandbox (left)
SBX = dict(x=50, y=150, w=560, h=560)
box(SBX["x"], SBX["y"], SBX["w"], SBX["h"], SBX_FILL, SBX_EDGE, radius=22)
text(SBX["x"] + 24, SBX["y"] + 20, "Docker Sandbox", f_h, fill=SBX_EDGE)
text(SBX["x"] + 24, SBX["y"] + 48, "isolated microVM · egress-controlled", f_bs, fill=MUTED)
SBX_R = SBX["x"] + SBX["w"]      # 610

# agent
box(90, 210, 480, 88, BOX_FILL, BOX_EDGE)
text(112, 230, "Claude Code agent", f_h)
text(112, 262, "generates & edits code in the Vortex loop", f_b, fill=MUTED)

# MCP server
MCP_CY = 385
box(90, 330, 480, 108, BOX_FILL, BOX_EDGE)
text(112, 348, "SonarQube MCP Server + Vortex", f_h)
text(112, 378, "wired by: sonar integrate claude", f_b, fill=MUTED)
text(112, 402, "guidelines · deps · architecture · navigation", f_bs, fill=MUTED)

# CLI
CLI_CY = 525
box(90, 470, 480, 108, BOX_FILL, BOX_EDGE)
text(112, 488, "SonarQube CLI  (sonar)", f_h)
text(112, 518, "analyze agentic · analyze secrets", f_b, fill=MUTED)
text(112, 542, "quality-gate status · list issues", f_bs, fill=MUTED)

# token sentinel note
box(90, 610, 480, 44, GREEN_FILL, GREEN, radius=12)
text(330, 632, "SONARQUBE_CLI_TOKEN = proxy placeholder  (not the real token)",
     f_tag, fill=GREEN, anchor="mm")

# internal arrows (kept inside the sandbox)
poly([(330, 298), (330, 330)], color=LINE, width=3)          # agent -> mcp
poly([(360, 330), (360, 298)], color=LINE, width=3)          # mcp -> agent
poly([(200, 438), (200, 470)], color=LINE, width=3)          # mcp -> cli

# sbx proxy (middle)
PX = dict(x=720, y=270, w=320, h=290)
box(PX["x"], PX["y"], PX["w"], PX["h"], PROXY_FILL, PROXY_EDGE, radius=20)
PX_CX = PX["x"] + PX["w"] / 2
text(PX_CX, PX["y"] + 22, "sbx proxy", f_h, fill=PROXY_INK, anchor="ma")
text(PX_CX, PX["y"] + 50, "credential-injecting", f_bs, fill=MUTED, anchor="ma")
d.line([(PX["x"] + 22) * S, (PX["y"] + 82) * S, (PX["x"] + PX["w"] - 22) * S, (PX["y"] + 82) * S],
       fill=PROXY_EDGE, width=1 * S)
bx = PX["x"] + 24
text(bx, PX["y"] + 98, "• swaps  placeholder", f_b)
text(bx + 16, PX["y"] + 120, "→ real token (Bearer)", f_b, fill=MUTED)
text(bx, PX["y"] + 150, "• enforces egress", f_b)
text(bx + 16, PX["y"] + 172, "allowlist (deny-all)", f_b, fill=MUTED)
text(bx, PX["y"] + 202, "• TLS intercept on", f_b)
text(bx + 16, PX["y"] + 224, "SonarQube hosts only", f_b, fill=MUTED)
PX_R = PX["x"] + PX["w"]         # 1040
PX_B = PX["y"] + PX["h"]         # 560

# SonarQube Cloud (right)
CD = dict(x=1160, y=210, w=430, h=470)
box(CD["x"], CD["y"], CD["w"], CD["h"], CLOUD_FILL, CLOUD_EDGE, radius=22)
text(CD["x"] + 26, CD["y"] + 20, "SonarQube Cloud", f_h, fill=CLOUD_EDGE)
text(CD["x"] + 26, CD["y"] + 48, "sonarcloud.io (EU)  ·  sonarqube.us (US)", f_bs, fill=MUTED)

VX = dict(x=CD["x"] + 26, y=CD["y"] + 86, w=CD["w"] - 52, h=350)
box(VX["x"], VX["y"], VX["w"], VX["h"], WHITE, CLOUD_EDGE, radius=16)
text(VX["x"] + 20, VX["y"] + 16, "Sonar Vortex", f_h)
text(VX["x"] + 20, VX["y"] + 44, "context + algorithmic analysis", f_bs, fill=MUTED)
items = [
    "Coding guidelines (project rules)",
    "Third-party dependency health",
    "Architecture graphs & constraints",
    "Semantic navigation (AST / flow)",
    "Quality gate + issues verdicts",
]
for i, it in enumerate(items):
    yy = VX["y"] + 86 + i * 44
    d.ellipse([(VX["x"] + 20) * S, (yy + 5) * S, (VX["x"] + 30) * S, (yy + 15) * S], fill=CLOUD_EDGE)
    text(VX["x"] + 44, yy, it, f_b)
CD_L = CD["x"]                   # 1160
CD_B = CD["y"] + CD["h"]         # 680

# host-side secret store (below proxy)
HV = dict(x=720, y=600, w=320, h=94)
box(HV["x"], HV["y"], HV["w"], HV["h"], RED_FILL, RED, radius=14)
HV_CX = HV["x"] + HV["w"] / 2
text(HV_CX, HV["y"] + 18, "Host-side secret store", f_tag, fill=RED, anchor="ma")
text(HV_CX, HV["y"] + 42, "real SonarQube USER token", f_bs, fill=INK, anchor="ma")
text(HV_CX, HV["y"] + 62, "never written into the container", f_bs, fill=MUTED, anchor="ma")

# ==== cross-zone arrows (orthogonal, in clear lanes) =======================
REQ_Y = MCP_CY                                   # 385, the request lane
# sandbox -> proxy  (label sits in the gap, above the line)
poly([(SBX_R, REQ_Y), (PX["x"], REQ_Y)], color=SBX_EDGE, width=4)
gap1_cx = (SBX_R + PX["x"]) / 2                  # 665
text(gap1_cx, REQ_Y - 42, "sends", f_lbl, fill=SBX_EDGE, anchor="ma")
text(gap1_cx, REQ_Y - 26, "placeholder", f_lbl, fill=SBX_EDGE, anchor="ma")

# proxy -> cloud
poly([(PX_R, REQ_Y), (CD_L, REQ_Y)], color=PROXY_EDGE, width=4)
gap2_cx = (PX_R + CD_L) / 2                      # 1100
text(gap2_cx, REQ_Y - 42, "sends", f_lbl, fill=PROXY_INK, anchor="ma")
text(gap2_cx, REQ_Y - 26, "real token", f_lbl, fill=PROXY_INK, anchor="ma")

# cloud -> sandbox  (return path routed through the bottom lane; label in open space)
RET_Y = 770
RISER_X = 665                                    # between sandbox (610) and proxy (720)
poly([(1400, CD_B), (1400, RET_Y), (RISER_X, RET_Y), (RISER_X, CLI_CY), (SBX_R, CLI_CY)],
     color=CLOUD_EDGE, width=4, dash=True)
text((RISER_X + 1400) / 2, RET_Y - 24, "returns context + analysis verdicts",
     f_lbl, fill=CLOUD_EDGE, anchor="ma")

# secret store -> proxy (real token stays host-side)
poly([(HV_CX, HV["y"]), (HV_CX, PX_B)], color=RED, width=3, dash=True)

# legend
lx, ly = 50, H - 40
d.line([lx * S, ly * S, (lx + 34) * S, ly * S], fill=LINE, width=4 * S)
text(lx + 44, ly - 8, "request", f_bs, fill=MUTED)
poly([(lx + 130, ly), (lx + 176, ly)], color=CLOUD_EDGE, width=4, dash=True)
text(lx + 186, ly - 8, "return", f_bs, fill=MUTED)
text(lx + 260, ly - 8, "·  mixin · requires agent: claude · Apache-2.0", f_bs, fill=MUTED)

# ==== downsample + save ====================================================
img = img.resize((W, H), Image.LANCZOS)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
img.save(OUT, "PNG")
print("wrote", os.path.normpath(OUT), img.size)
