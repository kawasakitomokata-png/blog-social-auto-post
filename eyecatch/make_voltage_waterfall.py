"""電池電圧の「滝」比喩アニメ：硫黄(落差小) vs 酸素(落差大=約4V) の比較。

電子のスタート準位は両者同じ高さ。酸素は電子を強く引きつけるため着地点が
低く、落差(=電圧)が大きい。電圧に比例して落差を描く(硫黄≈2V→170px /
酸素≈4V→340px、85px/V で一致)。電子が滝のように流れ落ちる。
出力: voltage_waterfall.gif / .mp4 / 代表 voltage_waterfall.png
"""
import math
import io
import cairosvg
import numpy as np
from PIL import Image
import imageio.v2 as imageio

W, H = 960, 600
BG = "#07090d"
PLAT = "#cfd8e3"
BLUE = "#5fb0ff"
SUB = 60          # 1ループのフレーム数
FPS = 20
CYCLES = 3        # 1ループ中に電子が落ちる回数(シームレス)
SECONDS = 15

Y_TOP = 130
PX_PER_V = 85.0
COLS = [
    {"name": "硫黄", "cx": 270, "volt": 2.0, "arrow_x": 150, "side": -1, "drop": "落差 小"},
    {"name": "酸素", "cx": 690, "volt": 4.0, "arrow_x": 810, "side": +1, "drop": "落差 大"},
]


def glow(cx, cy, r, color, layers=3):
    out = []
    for i in range(layers, 0, -1):
        rr = r + i * r * 0.8
        op = 0.10 * (layers - i + 1) / layers + 0.05
        out.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rr:.1f}" fill="{color}" opacity="{op:.3f}"/>')
    out.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{color}"/>')
    return "\n".join(out)


def column(c, t):
    cx = c["cx"]
    y_bot = Y_TOP + c["volt"] * PX_PER_V
    s = []

    # 落差を測る矢印（外側）
    ax = c["arrow_x"]
    s.append(f'<line x1="{ax}" y1="{Y_TOP}" x2="{ax}" y2="{y_bot:.1f}" stroke="#6b7686" stroke-width="2"/>')
    for yy, d in [(Y_TOP, 1), (y_bot, -1)]:
        s.append(f'<path d="M{ax},{yy + d*0:.1f} l-6,{d*12} l12,0 z" fill="#6b7686"/>')
    s.append(f'<text x="{ax + c["side"]*8}" y="{(Y_TOP+y_bot)/2:.1f}" font-family="Noto Sans CJK JP, sans-serif" '
             f'font-size="18" font-weight="bold" fill="#9aa6b4" text-anchor="{"end" if c["side"]<0 else "start"}">{c["drop"]}</text>')

    # 上の準位（電子スタート）と下の準位（着地）
    s.append(f'<rect x="{cx-78}" y="{Y_TOP-7}" width="156" height="9" rx="4" fill="{PLAT}"/>')
    s.append(f'<rect x="{cx-78}" y="{y_bot-2:.1f}" width="156" height="9" rx="4" fill="{PLAT}"/>')

    # 落ちる電子（滝）
    streams = [-46, 0, 46]
    for si, sx in enumerate(streams):
        for d in range(5):
            phase = (d / 5.0 + si * 0.13 + t * CYCLES) % 1.0
            ey = Y_TOP + phase * (y_bot - Y_TOP)
            ex = cx + sx + 6 * math.sin(phase * math.pi * 2 + si)
            s.append(glow(ex, ey, 5, BLUE, layers=2))

    # ラベル
    s.append(f'<text x="{cx}" y="{Y_TOP-22}" font-family="Noto Sans CJK JP, sans-serif" '
             f'font-size="30" font-weight="bold" fill="#e9eef5" text-anchor="middle">{c["name"]}</text>')
    s.append(f'<text x="{cx}" y="{y_bot+34:.1f}" font-family="Arial, sans-serif" '
             f'font-size="26" font-weight="bold" fill="#ffd34d" text-anchor="middle">≈ {c["volt"]:.1f} V</text>')
    return "\n".join(s)


def build_svg(frame):
    t = frame / SUB
    cols = "\n".join(column(c, t) for c in COLS)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <rect width="{W}" height="{H}" fill="{BG}"/>
  <text x="{W/2}" y="50" font-family="Noto Sans CJK JP, sans-serif" font-size="34" font-weight="bold" fill="#ffffff" text-anchor="middle">落差大 ＝ 高電圧</text>
  <line x1="{W/2}" y1="120" x2="{W/2}" y2="500" stroke="#1b2230" stroke-width="2"/>
  {cols}
  <text x="{W/2}" y="565" font-family="Noto Sans CJK JP, sans-serif" font-size="30" font-weight="bold" fill="#7fc0ff" text-anchor="middle">硫黄 ＜＜＜ 酸素</text>
</svg>'''


base = []
for f in range(SUB):
    png = cairosvg.svg2png(bytestring=build_svg(f).encode("utf-8"), output_width=W, output_height=H)
    base.append(Image.open(io.BytesIO(png)).convert("RGB"))

total = FPS * SECONDS
frames = [base[i % SUB] for i in range(total)]

base[0].save("voltage_waterfall.png")
frames[0].save("voltage_waterfall.gif", save_all=True, append_images=frames[1:],
               duration=int(1000 / FPS), loop=0, optimize=True)
print(f"GIF OK ({len(frames)} frames, {len(frames)/FPS:.1f}s)")
imageio.mimwrite("voltage_waterfall.mp4", [np.asarray(fr) for fr in frames],
                 fps=FPS, codec="libx264", quality=8, macro_block_size=8)
print(f"MP4 OK ({len(frames)/FPS:.1f}s)")
