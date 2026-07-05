# -*- coding: utf-8 -*-
import cairosvg
from build_flow import left_doc, outlined_text, TILES, PINK

def render(name, w, h, body, tx=0, ty=0):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
           f'viewBox="0 0 {w} {h}"><g transform="translate({tx} {ty})">{body}</g></svg>')
    open(f"{name}.svg", "w").write(svg)
    cairosvg.svg2png(bytestring=svg.encode(), write_to=f"{name}.png",
                     output_width=w * 2, output_height=h * 2)
    print(name, f"{w*2}x{h*2}")

# 1) 特許出願書 + ¥0スタンプ
render("part_1_tokkyo", 350, 495, left_doc(), tx=-25, ty=-95)

# 2) 矢印
arrow = (f'<path d="M 375 372 L 448 372 L 448 352 L 492 385 L 448 418 L 448 398 '
         f'L 375 398 Z" fill="{PINK}" opacity="0.9"/>')
render("part_2_arrow", 137, 86, arrow, tx=-365, ty=-342)

# 3-6) 4要素タイル (アイコン + キャプション)
names = ["kanri", "joshiki", "kokka", "seito"]
for i, (fill, border, icon_fn, label) in enumerate(TILES):
    body = (f'<rect x="10" y="10" width="520" height="155" rx="16" '
            f'fill="{fill}" stroke="{border}" stroke-width="5"/>'
            + icon_fn(105, 88)
            + outlined_text(200, 105, label, 46, ls=4))
    render(f"part_{i+3}_{names[i]}", 540, 175, body)
