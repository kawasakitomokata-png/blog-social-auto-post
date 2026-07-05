# -*- coding: utf-8 -*-
import cairosvg, math

NAVY = "#2C4770"; GOLD = "#F7C948"; GOLD_D = "#E0A800"
RED = "#C93A3A"; PINK = "#ff4fae"; GRAY = "#8A94A6"; LINE = "#B8C0CC"

def outlined_text(x, y, s, size, ls=2, anchor="start"):
    """白抜き+ピンク縁取り(袋文字): 太ストロークの下層 + 白文字の上層"""
    common = (f'font-family="IPAGothic" font-size="{size}" font-weight="bold" '
              f'letter-spacing="{ls}" text-anchor="{anchor}"')
    return (f'<text x="{x}" y="{y}" {common} fill="{PINK}" stroke="{PINK}" '
            f'stroke-width="{size*0.28:.1f}" stroke-linejoin="round">{s}</text>'
            f'<text x="{x}" y="{y}" {common} fill="#ffffff">{s}</text>')

def gear(cx, cy, r=19):
    teeth = ""
    for i in range(8):
        a = i * 45
        teeth += (f'<rect x="{cx-4}" y="{cy-r-6}" width="8" height="10" rx="2" '
                  f'fill="{NAVY}" transform="rotate({a} {cx} {cy})"/>')
    return (teeth + f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{NAVY}"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r*0.42:.0f}" fill="#ffffff"/>')

def icon_kanri(cx, cy):  # 管理のみ: フォルダ + 歯車
    return (f'<g transform="translate({cx} {cy})">'
            f'<rect x="-46" y="-36" width="38" height="16" rx="5" fill="{GOLD_D}"/>'
            f'<rect x="-46" y="-26" width="92" height="60" rx="7" fill="{GOLD}" stroke="{GOLD_D}" stroke-width="3"/>'
            + gear(30, 22) + '</g>')

def icon_joshiki(cx, cy):  # 常識的: 天秤
    pan = (f'<line x1="{{s}}" y1="-32" x2="{{l}}" y2="-6" stroke="{NAVY}" stroke-width="3"/>'
           f'<line x1="{{s}}" y1="-32" x2="{{r}}" y2="-6" stroke="{NAVY}" stroke-width="3"/>'
           f'<path d="M {{l}} -6 A 15 15 0 0 0 {{r}} -6 Z" fill="{NAVY}"/>')
    left = pan.format(s=-40, l=-55, r=-25)
    right = pan.format(s=40, l=25, r=55)
    return (f'<g transform="translate({cx} {cy})">'
            f'<rect x="-4" y="-40" width="8" height="72" rx="3" fill="{NAVY}"/>'
            f'<rect x="-46" y="-38" width="92" height="7" rx="3.5" fill="{NAVY}"/>'
            f'<circle cx="0" cy="-42" r="6" fill="{GOLD}" stroke="{GOLD_D}" stroke-width="2"/>'
            f'<rect x="-28" y="30" width="56" height="9" rx="4" fill="{NAVY}"/>'
            + left + right + '</g>')

def icon_kokka(cx, cy):  # 国家財産: 議事堂風の建物 + 金貨
    cols = "".join(f'<rect x="{x}" y="-12" width="11" height="34" fill="{NAVY}"/>'
                   for x in (-42, -19, 4, 27))
    return (f'<g transform="translate({cx} {cy})">'
            f'<polygon points="-50,-14 -1,-40 48,-14" fill="{NAVY}"/>'
            f'<rect x="-50" y="-14" width="98" height="6" fill="{GRAY}"/>'
            + cols +
            f'<rect x="-50" y="22" width="98" height="8" rx="3" fill="{NAVY}"/>'
            f'<rect x="-56" y="30" width="110" height="8" rx="3" fill="{GRAY}"/>'
            f'<circle cx="42" cy="-30" r="18" fill="{GOLD}" stroke="{GOLD_D}" stroke-width="3"/>'
            f'<text x="42" y="-22" font-family="IPAGothic" font-size="22" font-weight="bold" '
            f'fill="{NAVY}" text-anchor="middle">¥</text></g>')

def icon_seito(cx, cy):  # 正当: 盾 + チェック
    return (f'<g transform="translate({cx} {cy})">'
            f'<path d="M -36 -38 L 36 -38 L 36 4 Q 36 30 0 44 Q -36 30 -36 4 Z" '
            f'fill="{NAVY}" stroke="#1E3252" stroke-width="3"/>'
            f'<path d="M -17 0 L -4 15 L 21 -15" fill="none" stroke="{GOLD}" '
            f'stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/></g>')

def left_doc():  # 縮小版: 特許出願書 + ¥0スタンプ
    return f'''
  <g transform="rotate(-4 190 300)">
    <rect x="68" y="128" width="250" height="360" rx="7" fill="#000000" opacity="0.12"/>
    <rect x="60" y="120" width="250" height="360" rx="7" fill="#FFFFFF" stroke="#C9C2B2" stroke-width="3"/>
    <rect x="60" y="120" width="250" height="12" rx="6" fill="{NAVY}"/>
    <text x="185" y="172" font-family="IPAGothic" font-size="27" font-weight="bold"
          fill="{NAVY}" text-anchor="middle" letter-spacing="4">特許出願書</text>
    <line x1="95" y1="185" x2="275" y2="185" stroke="{NAVY}" stroke-width="2"/>
    <g transform="translate(185 235) scale(0.75)">
      <circle cx="0" cy="0" r="34" fill="{GOLD}"/>
      <circle cx="0" cy="0" r="34" fill="none" stroke="{GOLD_D}" stroke-width="3"/>
      <rect x="-11" y="28" width="22" height="8" rx="3" fill="{GRAY}"/>
      <path d="M -8 20 L -5 4 L -12 4 L 0 -18 L -3 2 L 4 2 Z" fill="#FFFFFF"/>
    </g>
    <g fill="{LINE}">
      <rect x="92" y="300" width="186" height="7" rx="3.5"/>
      <rect x="92" y="318" width="186" height="7" rx="3.5"/>
      <rect x="92" y="336" width="140" height="7" rx="3.5"/>
      <rect x="92" y="362" width="186" height="7" rx="3.5"/>
    </g>
    <rect x="88" y="392" width="194" height="42" rx="5" fill="#EEF3FA" stroke="{NAVY}" stroke-width="2"/>
    <text x="185" y="419" font-family="IPAGothic" font-size="16" font-weight="bold"
          fill="{NAVY}" text-anchor="middle">条件：ロイヤリティー ０円</text>
  </g>
  <g transform="rotate(-12 268 490)">
    <circle cx="268" cy="490" r="82" fill="#FFFFFF" opacity="0.9"/>
    <circle cx="268" cy="490" r="82" fill="none" stroke="{RED}" stroke-width="6"/>
    <circle cx="268" cy="490" r="71" fill="none" stroke="{RED}" stroke-width="2.5"/>
    <line x1="205" y1="441" x2="331" y2="441" stroke="{RED}" stroke-width="2.5"/>
    <text x="268" y="462" font-family="IPAGothic" font-size="15" font-weight="bold"
          fill="{RED}" text-anchor="middle">ロイヤリティー</text>
    <text x="268" y="522" font-family="IPAGothic" font-size="56" font-weight="bold"
          fill="{RED}" text-anchor="middle">¥0</text>
    <line x1="200" y1="532" x2="336" y2="532" stroke="{RED}" stroke-width="2.5"/>
    <text x="268" y="552" font-family="IPAGothic" font-size="14" font-weight="bold"
          fill="{RED}" text-anchor="middle" letter-spacing="4">条件付</text>
  </g>'''

TILES = [
    ("#f2bedd", "#e9a6cf", icon_kanri,  "管理のみ"),
    ("#d9bcef", "#c7a3e6", icon_joshiki, "常識的"),
    ("#e0b3ea", "#cf9adf", icon_kokka,  "国家財産"),
    ("#f1c4d8", "#e6a9c4", icon_seito,  "正当"),
]

def build(with_captions):
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="770" viewBox="0 0 1080 770">']
    parts.append(left_doc())
    # 矢印
    parts.append(f'<path d="M 375 372 L 448 372 L 448 352 L 492 385 L 448 418 L 448 398 L 375 398 Z" '
                 f'fill="{PINK}" opacity="0.9"/>')
    for i, (fill, border, icon_fn, label) in enumerate(TILES):
        y = 50 + i * 170
        parts.append(f'<rect x="520" y="{y}" width="520" height="155" rx="16" '
                     f'fill="{fill}" stroke="{border}" stroke-width="5"/>')
        if with_captions:
            parts.append(icon_fn(615, y + 78))
            parts.append(outlined_text(710, y + 95, label, 46, ls=4))
        else:
            parts.append(f'<g transform="translate(780 {y+78}) scale(1.35)">{icon_fn(0, 0)}</g>')
    parts.append('</svg>')
    return "".join(parts)

for name, cap in (("flow_caption", True), ("flow_icons_only", False)):
    svg = build(cap)
    open(f"{name}.svg", "w").write(svg)
    cairosvg.svg2png(bytestring=svg.encode(), write_to=f"{name}.png",
                     output_width=1620, output_height=1155)
print("done")
