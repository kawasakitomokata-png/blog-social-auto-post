"""リチウム原子モデルのアニメーション生成（黒背景・最外殻電子を強調＋パルス）。

最外殻電子（L殻の1個）を白いリングで強調し、大きくなったり小さくなったり
脈動させることで「最外殻電子は放出されやすい」特性を視覚的に示す。
出力: lithium_atom_dark.gif / .mp4 / 代表フレーム lithium_atom_dark.png
"""
import math
import io
import cairosvg
import numpy as np
from PIL import Image
import imageio.v2 as imageio

W = H = 600
CX = CY = 300
R_INNER = 120   # K殻
R_OUTER = 215   # L殻（最外殻）
FRAMES = 90

BG = "#050608"
ORBIT = "#27313f"


def glow_dot(cx, cy, r, color, layers=4):
    """中心の点＋外側に半透明の輝きを重ねて発光表現。"""
    out = []
    for i in range(layers, 0, -1):
        rr = r + i * r * 0.9
        op = 0.10 * (layers - i + 1) / layers + 0.04
        out.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rr:.1f}" '
                   f'fill="{color}" opacity="{op:.3f}"/>')
    out.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{color}"/>')
    return "\n".join(out)


def nucleus():
    parts = []
    # 中性子（青）
    for x, y in [(288, 282), (318, 288), (282, 316), (316, 320)]:
        parts.append(glow_dot(x, y, 18, "#4f9dff", layers=2))
    # 陽子（赤）
    for x, y in [(302, 300), (278, 296), (320, 310)]:
        parts.append(glow_dot(x, y, 18, "#ff5a52", layers=2))
    return "\n".join(parts)


def build_svg(frame):
    t = frame / FRAMES
    a_in = 2 * math.pi * (2 * t)            # 内殻2回転
    a_out = 2 * math.pi * (1 * t) + math.pi * 1.15  # 外殻1回転
    pulse = math.sin(2 * math.pi * (3 * t))  # 3回脈動（シームレス）

    # 内殻電子2個（小さな青い点）
    inner = []
    for k in range(2):
        ang = a_in + k * math.pi
        ex = CX + R_INNER * math.cos(ang)
        ey = CY + R_INNER * math.sin(ang)
        inner.append(glow_dot(ex, ey, 6, "#7fc0ff", layers=3))
    inner_s = "\n".join(inner)

    # 最外殻電子（強調＋パルス）
    ox = CX + R_OUTER * math.cos(a_out)
    oy = CY + R_OUTER * math.sin(a_out)
    e_r = 11 + 6 * pulse                 # 4〜17 で拡大縮小
    ring_r = e_r + 16 + 4 * pulse
    ring_op = 0.55 + 0.35 * (pulse * 0.5 + 0.5)
    outer = (
        glow_dot(ox, oy, e_r, "#8fd0ff", layers=5)
        + f'<circle cx="{ox:.1f}" cy="{oy:.1f}" r="{ring_r:.1f}" fill="none" '
          f'stroke="#ffffff" stroke-width="2.4" opacity="{ring_op:.3f}"/>'
    )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <rect width="{W}" height="{H}" fill="{BG}"/>
  <circle cx="{CX}" cy="{CY}" r="{R_INNER}" fill="none" stroke="{ORBIT}" stroke-width="2"/>
  <circle cx="{CX}" cy="{CY}" r="{R_OUTER}" fill="none" stroke="{ORBIT}" stroke-width="2"/>
  {nucleus()}
  <g>
    <text x="358" y="262" font-family="Arial, sans-serif" font-size="18" font-weight="bold" fill="#9aa6b4" text-anchor="start">3</text>
    <text x="392" y="300" font-family="Arial, sans-serif" font-size="46" font-weight="bold" fill="#e9eef5" text-anchor="middle">Li</text>
  </g>
  {inner_s}
  {outer}
  <text x="{CX}" y="555" font-family="Noto Sans CJK JP, sans-serif" font-size="22" font-weight="bold" fill="#e9eef5" text-anchor="middle">最外殻電子は放出されやすい</text>
</svg>'''


frames = []
for f in range(FRAMES):
    png = cairosvg.svg2png(bytestring=build_svg(f).encode("utf-8"),
                           output_width=W, output_height=H)
    frames.append(Image.open(io.BytesIO(png)).convert("RGB"))

frames[len(frames) // 4].save("lithium_atom_dark.png")
frames[0].save("lithium_atom_dark.gif", save_all=True, append_images=frames[1:],
               duration=45, loop=0, optimize=True)
print("GIF OK")

imageio.mimwrite("lithium_atom_dark.mp4", [np.asarray(fr) for fr in frames],
                 fps=30, codec="libx264", quality=8, macro_block_size=8)
print("MP4 OK")
