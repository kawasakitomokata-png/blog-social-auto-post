# -*- coding: utf-8 -*-
"""太古の海（約35億年前・単細胞生物の時代）のイメージ画像を生成する。

SVG を組み立てて PNG に書き出す。実行すると
  eyecatch/ancient_ocean_35億年前.png
が出力される。
"""
import math
import random

import cairosvg

W, H = 1600, 900
SURFACE = 150          # 海面の高さ
SEABED = 720           # 海底のライン
random.seed(20260726)

parts = []
add = parts.append


def rnd(a, b):
    return random.uniform(a, b)


# ---------------------------------------------------------------- 定義
add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
    f'viewBox="0 0 {W} {H}">')
add('''<defs>
  <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%"   stop-color="#c9622f"/>
    <stop offset="55%"  stop-color="#e08a45"/>
    <stop offset="100%" stop-color="#f0b072"/>
  </linearGradient>
  <linearGradient id="sea" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%"   stop-color="#3f9c85"/>
    <stop offset="22%"  stop-color="#238073"/>
    <stop offset="55%"  stop-color="#0f5359"/>
    <stop offset="82%"  stop-color="#08303d"/>
    <stop offset="100%" stop-color="#041a24"/>
  </linearGradient>
  <linearGradient id="ray" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%"   stop-color="#ffe9c0" stop-opacity="0.42"/>
    <stop offset="60%"  stop-color="#bdf0dc" stop-opacity="0.12"/>
    <stop offset="100%" stop-color="#bdf0dc" stop-opacity="0"/>
  </linearGradient>
  <linearGradient id="bed" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%"   stop-color="#3b3026"/>
    <stop offset="100%" stop-color="#150f0f"/>
  </linearGradient>
  <linearGradient id="strom" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%"   stop-color="#5d6b45"/>
    <stop offset="35%"  stop-color="#6b5b3f"/>
    <stop offset="100%" stop-color="#332a20"/>
  </linearGradient>
  <radialGradient id="cell" cx="35%" cy="30%" r="75%">
    <stop offset="0%"   stop-color="#d8fff0" stop-opacity="0.95"/>
    <stop offset="55%"  stop-color="#8fe6c4" stop-opacity="0.72"/>
    <stop offset="100%" stop-color="#3fae95" stop-opacity="0.35"/>
  </radialGradient>
  <radialGradient id="glow" cx="50%" cy="50%" r="50%">
    <stop offset="0%"   stop-color="#aef4d8" stop-opacity="0.35"/>
    <stop offset="100%" stop-color="#aef4d8" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="sun" cx="50%" cy="50%" r="50%">
    <stop offset="0%"   stop-color="#fff3d0" stop-opacity="0.95"/>
    <stop offset="45%"  stop-color="#ffcf8a" stop-opacity="0.45"/>
    <stop offset="100%" stop-color="#ffcf8a" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="vent" cx="50%" cy="100%" r="80%">
    <stop offset="0%"   stop-color="#ff7a2a" stop-opacity="0.45"/>
    <stop offset="55%"  stop-color="#c2451c" stop-opacity="0.14"/>
    <stop offset="100%" stop-color="#c2451c" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="rock" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%"   stop-color="#4a3a3f"/>
    <stop offset="45%"  stop-color="#251d26"/>
    <stop offset="100%" stop-color="#120d14"/>
  </linearGradient>
  <radialGradient id="vignette" cx="50%" cy="45%" r="72%">
    <stop offset="55%"  stop-color="#000000" stop-opacity="0"/>
    <stop offset="100%" stop-color="#001018" stop-opacity="0.45"/>
  </radialGradient>
  <filter id="blur6"><feGaussianBlur stdDeviation="6"/></filter>
  <filter id="blur14"><feGaussianBlur stdDeviation="14"/></filter>
  <filter id="blur28"><feGaussianBlur stdDeviation="28"/></filter>
</defs>''')

# ---------------------------------------------------------------- 空（酸素のない赤い空）
add(f'<rect width="{W}" height="{SURFACE}" fill="url(#sky)"/>')
add(f'<circle cx="1180" cy="42" r="130" fill="url(#sun)"/>')

# 遠景の火山島
add('<g opacity="0.45" fill="#7b3f2c">'
    '<path d="M120 150 L260 44 L330 92 L400 60 L520 150 Z"/>'
    '<path d="M980 150 L1080 78 L1160 150 Z"/>'
    '</g>')
add('<g opacity="0.3" fill="#e9c39a" filter="url(#blur14)">'
    '<path d="M240 60 q18 -40 40 -54 q-6 34 6 54 z"/></g>')

# ---------------------------------------------------------------- 海
add(f'<rect y="{SURFACE}" width="{W}" height="{H - SURFACE}" fill="url(#sea)"/>')

# 海面のうねり
wave = [f'M0 {SURFACE}']
for x in range(0, W + 40, 40):
    wave.append(f'L{x} {SURFACE + math.sin(x / 90.0) * 7 + math.sin(x / 37.0) * 3:.1f}')
wave.append(f'L{W} {SURFACE + 26} L0 {SURFACE + 26} Z')
add(f'<path d="{" ".join(wave)}" fill="#8fe0c8" opacity="0.5" filter="url(#blur6)"/>')
add(f'<path d="{" ".join(wave[:-1])}" fill="none" stroke="#ffe6bd" '
    f'stroke-width="2.5" opacity="0.55"/>')

# ---------------------------------------------------------------- 光の柱
add('<g filter="url(#blur28)" opacity="0.85">')
for x0, w0, w1, ln in [(1120, 70, 220, 600), (900, 46, 160, 480), (1350, 40, 150, 420),
                       (640, 34, 130, 360), (300, 26, 110, 300)]:
    add(f'<path d="M{x0} {SURFACE} L{x0 + w0} {SURFACE} '
        f'L{x0 + w0 + w1 * 0.55} {SURFACE + ln} L{x0 - w1 * 0.45} {SURFACE + ln} Z" '
        f'fill="url(#ray)"/>')
add('</g>')

# ---------------------------------------------------------------- 海底
bed = [f'M0 {SEABED + 60}']
for x in range(0, W + 50, 50):
    y = SEABED + math.sin(x / 210.0) * 26 + math.sin(x / 63.0) * 8
    bed.append(f'L{x} {y:.1f}')
bed.append(f'L{W} {H} L0 {H} Z')
add(f'<path d="{" ".join(bed)}" fill="url(#bed)"/>')
add(f'<path d="{" ".join(bed[:-3])}" fill="none" stroke="#6f8a6a" '
    f'stroke-width="4" opacity="0.35"/>')

# ---------------------------------------------------------------- 熱水噴出孔（ブラックスモーカー）
def smoker(cx, base, scale, opacity):
    g = [f'<g opacity="{opacity}" transform="translate({cx},{base}) scale({scale})">']
    # 足元の熱の輝き
    g.append('<ellipse cx="0" cy="-6" rx="120" ry="46" fill="url(#vent)" '
             'filter="url(#blur14)"/>')
    # 岩の煙突（ごつごつした輪郭）
    g.append('<path d="M-64 8 L-44 -52 L-52 -66 L-34 -104 L-26 -136 L-8 -152 '
             'L14 -150 L22 -128 L34 -96 L28 -76 L46 -36 L62 8 Z" fill="url(#rock)"/>')
    g.append('<path d="M-64 8 L-44 -52 L-52 -66 L-34 -104 L-26 -136 L-8 -152 '
             'L-4 -150 L-14 -100 L-20 -40 L-24 8 Z" fill="#5b4650" opacity="0.55"/>')
    g.append('<path d="M-10 -152 L14 -150 L16 -158 L-8 -160 Z" fill="#0d0910"/>')
    # 硫化物の析出（ざらつき）
    for i in range(14):
        g.append(f'<circle cx="{rnd(-52, 52):.0f}" cy="{rnd(-140, 4):.0f}" '
                 f'r="{rnd(1.5, 4):.1f}" fill="#7a5f52" opacity="{rnd(0.1, 0.3):.2f}"/>')
    # 立ちのぼる黒煙
    plume = ['M-14 -156']
    for i in range(1, 7):
        y = -156 - i * 44
        x = math.sin(i * 0.55) * (6 + i * 4)
        w = 12 + i * 7
        plume.append(f'Q{x - w:.0f} {y + 22:.0f} {x - w * 0.7:.0f} {y:.0f}')
    for i in range(6, 0, -1):
        y = -156 - i * 44
        x = math.sin(i * 0.55) * (6 + i * 4)
        w = 12 + i * 7
        plume.append(f'Q{x + w:.0f} {y - 22:.0f} {x + w * 0.7:.0f} {y + 44:.0f}')
    plume.append('Z')
    g.append(f'<path d="{" ".join(plume)}" fill="#171622" opacity="0.5" '
             f'filter="url(#blur28)"/>')
    g.append(f'<path d="{" ".join(plume)}" fill="#0f0e18" opacity="0.35" '
             f'filter="url(#blur14)" transform="scale(0.72,0.9)"/>')
    g.append('</g>')
    add(''.join(g))


smoker(300, SEABED + 40, 1.0, 0.95)
smoker(1420, SEABED + 30, 0.7, 0.7)

# ---------------------------------------------------------------- ストロマトライト（シアノバクテリアの塔）
def stromatolite(cx, top, w, h):
    g = [f'<g transform="translate({cx},{top})">']
    g.append(f'<path d="M{-w/2} {h} Q{-w/2 - 6} {h*0.35} {-w*0.32} 0 '
             f'Q0 {-w*0.30} {w*0.32} 0 Q{w/2 + 6} {h*0.35} {w/2} {h} Z" fill="url(#strom)"/>')
    # 層構造（ラミナ）
    for i in range(1, 7):
        t = i / 7.0
        yy = h * t
        ww = w * (0.66 + 0.34 * t) / 2
        g.append(f'<path d="M{-ww:.0f} {yy:.0f} Q0 {yy - w*0.13:.0f} {ww:.0f} {yy:.0f}" '
                 f'fill="none" stroke="#9a8659" stroke-width="2" opacity="0.35"/>')
    # 表面の微生物マット
    g.append(f'<path d="M{-w*0.34} 4 Q0 {-w*0.32} {w*0.34} 4 Q0 {-w*0.14} {-w*0.34} 4 Z" '
             f'fill="#4f8f63" opacity="0.75"/>')
    # 酸素の泡
    for i in range(5):
        g.append(f'<circle cx="{rnd(-w*0.3, w*0.3):.0f}" cy="{rnd(-70, -14):.0f}" '
                 f'r="{rnd(2.5, 5.5):.1f}" fill="#d9fff2" opacity="{rnd(0.35, 0.75):.2f}"/>')
    g.append('</g>')
    add(''.join(g))


for cx, w, h in [(620, 120, 170), (760, 86, 130), (880, 150, 210), (1030, 96, 150),
                 (1140, 70, 110), (460, 74, 120), (1290, 110, 160)]:
    base = SEABED + math.sin(cx / 210.0) * 26 + math.sin(cx / 63.0) * 8
    stromatolite(cx, base - h + 30, w, h)

# ---------------------------------------------------------------- 単細胞生物たち
def coccus(cx, cy, r, op):
    """球菌（丸い単細胞）"""
    add(f'<g opacity="{op:.2f}">'
        f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r*2.6:.0f}" fill="url(#glow)"/>'
        f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r:.1f}" fill="url(#cell)"/>'
        f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r:.1f}" fill="none" '
        f'stroke="#e6fff6" stroke-width="1.2" opacity="0.7"/>'
        f'<circle cx="{cx - r*0.25:.0f}" cy="{cy + r*0.1:.0f}" r="{r*0.34:.1f}" '
        f'fill="#2f7f6d" opacity="0.55"/>'
        f'<circle cx="{cx - r*0.34:.0f}" cy="{cy - r*0.36:.0f}" r="{r*0.2:.1f}" '
        f'fill="#ffffff" opacity="0.8"/></g>')


def filament(cx, cy, n, r, ang, op):
    """糸状性のシアノバクテリア"""
    g = [f'<g opacity="{op:.2f}">']
    for i in range(n):
        t = i - (n - 1) / 2.0
        x = cx + math.cos(ang) * t * r * 1.75
        y = cy + math.sin(ang) * t * r * 1.75 + math.sin(i * 0.8) * r * 0.35
        g.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="url(#cell)"/>')
        g.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="none" '
                 f'stroke="#dcfff2" stroke-width="1" opacity="0.55"/>')
    g.append('</g>')
    add(''.join(g))


def rod(cx, cy, w, h, ang, op):
    """桿菌（棒状の単細胞）"""
    add(f'<g opacity="{op:.2f}" transform="translate({cx:.0f},{cy:.0f}) rotate({ang:.0f})">'
        f'<rect x="{-w/2:.1f}" y="{-h/2:.1f}" width="{w:.1f}" height="{h:.1f}" '
        f'rx="{h/2:.1f}" fill="url(#cell)" stroke="#dcfff2" stroke-width="1.1"/>'
        f'<circle cx="{-w*0.15:.1f}" cy="0" r="{h*0.24:.1f}" fill="#2f7f6d" opacity="0.5"/>'
        f'</g>')


# 奥（小さく淡い）
for _ in range(46):
    coccus(rnd(0, W), rnd(SURFACE + 30, SEABED - 10), rnd(3, 7), rnd(0.20, 0.40))
for _ in range(10):
    filament(rnd(60, W - 60), rnd(SURFACE + 60, SEABED - 40), random.randint(4, 8),
             rnd(3, 5), rnd(-0.9, 0.9), rnd(0.22, 0.40))

# 中景
for _ in range(16):
    coccus(rnd(0, W), rnd(SURFACE + 40, SEABED), rnd(9, 16), rnd(0.55, 0.8))
for _ in range(6):
    rod(rnd(80, W - 80), rnd(SURFACE + 60, SEABED - 30), rnd(30, 54), rnd(13, 20),
        rnd(-40, 40), rnd(0.5, 0.75))
for _ in range(5):
    filament(rnd(120, W - 120), rnd(SURFACE + 80, SEABED - 60), random.randint(5, 9),
             rnd(7, 10), rnd(-0.7, 0.7), rnd(0.55, 0.8))

# 手前（大きくはっきり）— 分裂中の細胞も置く
coccus(268, 386, 40, 0.95)
coccus(1330, 300, 34, 0.92)
coccus(1180, 560, 26, 0.9)
# 二分裂
add('<g opacity="0.95"><circle cx="640" cy="300" r="120" fill="url(#glow)"/></g>')
coccus(604, 300, 36, 0.95)
coccus(668, 302, 33, 0.95)
rod(880, 430, 96, 38, -18, 0.9)
filament(430, 620, 9, 15, 0.25, 0.9)

# ---------------------------------------------------------------- 浮遊粒子と気泡
for _ in range(150):
    x, y = rnd(0, W), rnd(SURFACE, H)
    add(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rnd(0.8, 2.6):.1f}" '
        f'fill="#dff8ec" opacity="{rnd(0.1, 0.45):.2f}"/>')
for _ in range(40):
    x, y = rnd(0, W), rnd(SURFACE + 20, SEABED)
    r = rnd(2, 7)
    add(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="none" '
        f'stroke="#eafff7" stroke-width="1" opacity="{rnd(0.15, 0.5):.2f}"/>')

# ---------------------------------------------------------------- 全体の色被り
add(f'<rect width="{W}" height="{H}" fill="#0a2a33" opacity="0.10"/>')
add(f'<rect y="{H - 220}" width="{W}" height="220" fill="#02121a" opacity="0.35" '
    f'filter="url(#blur28)"/>')
add(f'<rect width="{W}" height="{H}" fill="url(#vignette)"/>')

add('</svg>')

svg = "\n".join(parts)
out_svg = "eyecatch/ancient_ocean.svg"
out_png = "eyecatch/ancient_ocean_35oku.png"
with open(out_svg, "w", encoding="utf-8") as f:
    f.write(svg)
cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=out_png,
                 output_width=W, output_height=H)
print("wrote", out_svg, out_png)
