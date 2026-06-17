"""リチウム原子モデルのアニメーション生成（電子が軌道を回る GIF / MP4）。"""
import math
import io
import cairosvg
from PIL import Image
import imageio.v2 as imageio

W = H = 600
CX = CY = 300
R_INNER = 120   # K殻
R_OUTER = 220   # L殻
FRAMES = 72


def electron(cx, cy):
    return (
        f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="14" fill="#3a78c2" '
        f'stroke="#28568f" stroke-width="2"/>'
        f'<text x="{cx:.1f}" y="{cy:.1f}" font-family="Arial, sans-serif" '
        f'font-size="18" font-weight="bold" fill="#ffffff" text-anchor="middle" '
        f'dominant-baseline="central">−</text>'
    )


def build_svg(frame):
    t = frame / FRAMES
    # 内殻：2個（180度対称）、外殻：1個。内殻を2回転・外殻を1回転でシームレスループ。
    a_in = 2 * math.pi * (2 * t)
    a_out = 2 * math.pi * (1 * t) + math.pi / 4

    e = []
    for k in range(2):
        ang = a_in + k * math.pi
        e.append(electron(CX + R_INNER * math.cos(ang), CY + R_INNER * math.sin(ang)))
    e.append(electron(CX + R_OUTER * math.cos(a_out), CY + R_OUTER * math.sin(a_out)))
    electrons = "\n".join(e)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <rect width="{W}" height="{H}" fill="#ffffff"/>
  <circle cx="{CX}" cy="{CY}" r="{R_INNER}" fill="none" stroke="#9bbcd6" stroke-width="3"/>
  <circle cx="{CX}" cy="{CY}" r="{R_OUTER}" fill="none" stroke="#9bbcd6" stroke-width="3"/>
  <g>
    <circle cx="288" cy="282" r="20" fill="#c9ced6" stroke="#8a909a" stroke-width="2"/>
    <circle cx="318" cy="288" r="20" fill="#c9ced6" stroke="#8a909a" stroke-width="2"/>
    <circle cx="282" cy="316" r="20" fill="#c9ced6" stroke="#8a909a" stroke-width="2"/>
    <circle cx="316" cy="320" r="20" fill="#c9ced6" stroke="#8a909a" stroke-width="2"/>
    <circle cx="302" cy="300" r="20" fill="#e8554e" stroke="#b23a34" stroke-width="2"/>
    <circle cx="278" cy="296" r="20" fill="#e8554e" stroke="#b23a34" stroke-width="2"/>
    <circle cx="320" cy="310" r="20" fill="#e8554e" stroke="#b23a34" stroke-width="2"/>
    <text x="302" y="300" font-family="Arial, sans-serif" font-size="22" font-weight="bold" fill="#ffffff" text-anchor="middle" dominant-baseline="central">+</text>
    <text x="278" y="296" font-family="Arial, sans-serif" font-size="22" font-weight="bold" fill="#ffffff" text-anchor="middle" dominant-baseline="central">+</text>
    <text x="320" y="310" font-family="Arial, sans-serif" font-size="22" font-weight="bold" fill="#ffffff" text-anchor="middle" dominant-baseline="central">+</text>
  </g>
  <g>
    <rect x="372" y="252" width="96" height="104" rx="12" fill="#ffffff" stroke="#444b54" stroke-width="3"/>
    <text x="384" y="280" font-family="Arial, sans-serif" font-size="20" font-weight="bold" fill="#7a818a" text-anchor="start">3</text>
    <text x="420" y="322" font-family="Arial, sans-serif" font-size="50" font-weight="bold" fill="#444b54" text-anchor="middle">Li</text>
    <text x="420" y="346" font-family="Noto Sans CJK JP, sans-serif" font-size="13" fill="#7a818a" text-anchor="middle">リチウム</text>
  </g>
  {electrons}
  <text x="{CX}" y="565" font-family="Noto Sans CJK JP, sans-serif" font-size="25" font-weight="bold" fill="#444b54" text-anchor="middle">リチウム原子モデル（陽子3・電子3）</text>
</svg>'''


frames = []
for f in range(FRAMES):
    png = cairosvg.svg2png(bytestring=build_svg(f).encode("utf-8"),
                           output_width=W, output_height=H)
    frames.append(Image.open(io.BytesIO(png)).convert("RGB"))

# GIF（ループ）
frames[0].save("lithium_atom.gif", save_all=True, append_images=frames[1:],
               duration=60, loop=0, optimize=True)
print("GIF OK")

# MP4
import numpy as np
imageio.mimwrite("lithium_atom.mp4", [np.asarray(fr) for fr in frames],
                 fps=30, codec="libx264", quality=8, macro_block_size=8)
print("MP4 OK")
