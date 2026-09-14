#!/usr/bin/env python3
"""Generate docs/architecture.png for the sonar-vortex kit.

Pure Pillow, no external services. Renders at 2x and downsamples with LANCZOS
for crisp anti-aliased edges/text. Re-run after editing to regenerate the PNG:

    python3 scripts/gen-architecture.py
"""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "docs", "architecture.png")

S = 2                      # supersample factor
W, H = 1600, 920           # final size
CW, CH = W * S, H * S      # canvas size

# palette
WHITE = (255, 255, 255)
INK = (31, 41, 55)         # slate-800
MUTED = (107, 114, 128)    # slate-500
LINE = (75, 85, 99)        # slate-600

SBX_FILL = (238, 244, 255)
SBX_EDGE = (76, 111, 255)
BOX_FILL = (255, 255, 255)
BOX_EDGE = (148, 163, 184)
PROXY_FILL = (255, 247, 237)
PROXY_EDGE = (245, 158, 11)
CLOUD_FILL = (245, 243, 255)
CLOUD_EDGE = (124, 58, 237)
GREEN = (16, 133, 71)
RED = (200, 60, 60)


def font(size, bold=False):
    candidates = (
        ["/System/Library/Fonts/Supplemental/Arial Bold.ttf",
         "/System/Library/Fonts/Helvetica.ttc"]
        if bold else
        ["/System/Library/Fonts/Supplemental/Arial.ttf",
         "/System/Library/Fonts/Helvetica.ttc"]
    )
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size * S)
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


def ctext(cx, y, s, f, fill=INK):
    text(cx, y, s, f, fill=fill, anchor="ma")


def arrow(x1, y1, x2, y2, color=LINE, width=3, dash=False):
    x1s, y1s, x2s, y2s = x1 * S, y1 * S, x2 * S, y2 * S
    if dash:
        # simple dashed segment
        import math
        total = math.hypot(x2s - x1s, y2s - y1s)
        dx, dy = (x2s - x1s) / total, (y2s - y1s) / total
        step, on = 14 * S, 9 * S
        t = 0
        while t < total:
            a = t
            b = min(t + on, total)
            d.line([x1s + dx * a, y1s + dy * a, x1s + dx * b, y1s + dy * b],
                   fill=color, width=width * S)
            t += step
    else:
        d.line([x1s, y1s, x2s, y2s], fill=color, width=width * S)
    # arrowhead
    import math
    ang = math.atan2(y2s - y1s, x2s - x1s)
    L = 12 * S
    for a in (ang + math.radians(150), ang - math.radians(150)):
        d.line([x2s, y2s, x2s + L * math.cos(a), y2s + L * math.sin(a)],
               fill=color, width=width * S)


f_title = font(30, bold=True)
f_sub = font(15)
f_h = font(19, bold=True)
f_b = font(14)
f_bs = font(12)
f_tag = font(12, bold=True)

# ---- title ----------------------------------------------------------------
text(60, 40, "Sonar Vortex — Docker Sandboxes kit", f_title)
text(60, 82, "Repo-aware context before the agent writes, real-time SonarQube verification after — token never enters the container.",
     f_sub, fill=MUTED)

# ---- sandbox (left) -------------------------------------------------------
SBX_X, SBX_Y, SBX_W, SBX_H = 60, 150, 640, 660
box(SBX_X, SBX_Y, SBX_W, SBX_H, SBX_FILL, SBX_EDGE, width=2, radius=22)
text(SBX_X + 26, SBX_Y + 22, "Docker Sandbox", f_h, fill=SBX_EDGE)
text(SBX_X + 26, SBX_Y + 50, "isolated microVM · egress-controlled", f_bs, fill=MUTED)

# agent
AG_X, AG_Y, AG_W, AG_H = SBX_X + 40, SBX_Y + 100, SBX_W - 80, 96
box(AG_X, AG_Y, AG_W, AG_H, BOX_FILL, BOX_EDGE)
text(AG_X + 22, AG_Y + 20, "Claude Code agent", f_h)
text(AG_X + 22, AG_Y + 52, "generates & edits code in the Vortex loop", f_b, fill=MUTED)

# mcp server
MC_X, MC_Y, MC_W, MC_H = AG_X, AG_Y + AG_H + 34, AG_W, 108
box(MC_X, MC_Y, MC_W, MC_H, BOX_FILL, BOX_EDGE)
text(MC_X + 22, MC_Y + 18, "SonarQube MCP Server", f_h)
text(MC_X + 22, MC_Y + 48, "sonar run mcp  (~/.sonar/mcp.sh)", f_b, fill=MUTED)
text(MC_X + 22, MC_Y + 72, "guidelines · deps · architecture · navigation", f_bs, fill=MUTED)

# cli
CL_X, CL_Y, CL_W, CL_H = AG_X, MC_Y + MC_H + 24, AG_W, 108
box(CL_X, CL_Y, CL_W, CL_H, BOX_FILL, BOX_EDGE)
text(CL_X + 22, CL_Y + 18, "SonarQube CLI  (sonar)", f_h)
text(CL_X + 22, CL_Y + 48, "analyze agentic · analyze secrets", f_b, fill=MUTED)
text(CL_X + 22, CL_Y + 72, "quality-gate status · list issues", f_bs, fill=MUTED)

# token sentinel note
TK_Y = CL_Y + CL_H + 22
box(AG_X, TK_Y, AG_W, 44, (236, 253, 245), GREEN, width=2, radius=12)
text(AG_X + 22, TK_Y + 13, "SONARQUBE_TOKEN = proxy-managed  (sentinel, not the real token)",
     f_tag, fill=GREEN)

# internal arrows agent <-> mcp/cli
arrow(AG_X + AG_W / 2, AG_Y + AG_H, MC_X + MC_W / 2, MC_Y, color=LINE)
arrow(MC_X + MC_W / 2, MC_Y, AG_X + AG_W / 2, AG_Y + AG_H, color=LINE)
arrow(AG_X + 120, MC_Y + MC_H, CL_X + 120, CL_Y, color=LINE)

# ---- proxy (middle) -------------------------------------------------------
PX_X, PX_Y, PX_W, PX_H = 760, 300, 320, 300
box(PX_X, PX_Y, PX_W, PX_H, PROXY_FILL, PROXY_EDGE, width=2, radius=20)
ctext(PX_X + PX_W / 2, PX_Y + 24, "sbx proxy", f_h, fill=(180, 110, 0))
ctext(PX_X + PX_W / 2, PX_Y + 54, "credential-injecting", f_bs, fill=MUTED)
d.line([(PX_X + 24) * S, (PX_Y + 88) * S, (PX_X + PX_W - 24) * S, (PX_Y + 88) * S],
       fill=PROXY_EDGE, width=1 * S)
text(PX_X + 24, PX_Y + 104, "• swaps  proxy-managed", f_b)
text(PX_X + 40, PX_Y + 128, "→ real token in", f_b, fill=MUTED)
text(PX_X + 40, PX_Y + 150, "Authorization: Bearer", f_b, fill=MUTED)
text(PX_X + 24, PX_Y + 184, "• enforces egress", f_b)
text(PX_X + 40, PX_Y + 208, "allowlist (deny-all)", f_b, fill=MUTED)
text(PX_X + 24, PX_Y + 244, "• TLS intercept on", f_b)
text(PX_X + 40, PX_Y + 268, "SonarQube hosts only", f_b, fill=MUTED)

# ---- cloud (right) --------------------------------------------------------
CD_X, CD_Y, CD_W, CD_H = 1140, 240, 400, 420
box(CD_X, CD_Y, CD_W, CD_H, CLOUD_FILL, CLOUD_EDGE, width=2, radius=22)
text(CD_X + 26, CD_Y + 22, "SonarQube Cloud", f_h, fill=CLOUD_EDGE)
text(CD_X + 26, CD_Y + 50, "sonarcloud.io  (EU)  ·  sonarqube.us  (US)", f_bs, fill=MUTED)

VX_X, VX_Y, VX_W, VX_H = CD_X + 26, CD_Y + 90, CD_W - 52, 300
box(VX_X, VX_Y, VX_W, VX_H, WHITE, CLOUD_EDGE, width=2, radius=16)
text(VX_X + 20, VX_Y + 16, "Sonar Vortex", f_h)
text(VX_X + 20, VX_Y + 44, "context + algorithmic analysis", f_bs, fill=MUTED)
items = [
    "Coding guidelines (project rules)",
    "Third-party dependency health",
    "Architecture graphs & constraints",
    "Semantic navigation (AST / flow)",
    "Quality gate + issues verdicts",
]
for i, it in enumerate(items):
    yy = VX_Y + 84 + i * 40
    d.ellipse([(VX_X + 20) * S, (yy + 5) * S, (VX_X + 30) * S, (yy + 15) * S],
              fill=CLOUD_EDGE)
    text(VX_X + 42, yy, it, f_b)

# ---- cross-zone arrows ----------------------------------------------------
# sandbox -> proxy (request, HTTPS w/ sentinel)
arrow(SBX_X + SBX_W, MC_Y + MC_H / 2, PX_X, PX_Y + 120, color=SBX_EDGE, width=4)
text((SBX_X + SBX_W + PX_X) / 2, MC_Y + MC_H / 2 - 44,
     "HTTPS via HTTPS_PROXY", f_bs, fill=SBX_EDGE, anchor="ma")
text((SBX_X + SBX_W + PX_X) / 2, MC_Y + MC_H / 2 - 24,
     "Bearer proxy-managed", f_bs, fill=MUTED, anchor="ma")

# proxy -> cloud (request, real token)
arrow(PX_X + PX_W, PX_Y + 120, CD_X, CD_Y + 140, color=PROXY_EDGE, width=4)
text((PX_X + PX_W + CD_X) / 2, PX_Y + 96,
     "Bearer <real token>", f_bs, fill=(180, 110, 0), anchor="ma")

# cloud -> sandbox (context + verdicts return)
arrow(CD_X, CD_Y + CD_H - 60, SBX_X + SBX_W, CL_Y + CL_H / 2,
      color=CLOUD_EDGE, width=4, dash=True)
text((SBX_X + SBX_W + CD_X) / 2, CL_Y + CL_H / 2 + 28,
     "context + analysis verdicts", f_bs, fill=CLOUD_EDGE, anchor="ma")

# ---- host token vault -----------------------------------------------------
HV_X, HV_Y, HV_W, HV_H = 760, 640, 320, 90
box(HV_X, HV_Y, HV_W, HV_H, (253, 242, 242), RED, width=2, radius=14)
ctext(HV_X + HV_W / 2, HV_Y + 16, "Host-side secret store", f_tag, fill=RED)
ctext(HV_X + HV_W / 2, HV_Y + 40, "real SonarQube USER token", f_bs, fill=INK)
ctext(HV_X + HV_W / 2, HV_Y + 60, "never written into the container", f_bs, fill=MUTED)
arrow(HV_X + HV_W / 2, HV_Y, PX_X + PX_W / 2, PX_Y + PX_H, color=RED, width=3, dash=True)

# footer
text(60, H - 34, "Kit: mixin · requires agent: claude · Apache-2.0", f_bs, fill=MUTED)

# ---- downsample + save ----------------------------------------------------
img = img.resize((W, H), Image.LANCZOS)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
img.save(OUT, "PNG")
print("wrote", os.path.normpath(OUT), img.size)
