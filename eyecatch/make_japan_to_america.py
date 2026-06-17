"""「日本からジェット機でアメリカへ」イラスト生成。

簡略化した日本地図(mapsicon, パブリックドメイン)を左に配置し、太平洋を渡って
画面右上(アメリカ方面・地図なし)へ向かうジェット機と飛行ルートを描く。
出力: japan_to_america.svg / japan_to_america.png
"""
import io
import cairosvg

W, H = 1000, 600

# 日本地図グループ（mapsicon 由来、viewBox 0..1024 相当）
JP_GROUP = open("/tmp/jp_group.txt").read()

# 日本を左下寄りに配置（高さ約430px）
JP_SCALE = 430 / 1024
JP_TX, JP_TY = 70, 150

# 飛行ルート（成田空港→アメリカ方面）。機体は日本に近い半分の距離に短縮。
PX0, PY0 = 398, 388          # 出発（成田空港）
PCX, PCY = 530, 270          # 制御点（弧）
PX1, PY1 = 660, 258          # 機体の現在位置（アメリカへ向かう途中）

JET = '''<g transform="translate({x},{y}) rotate({rot}) scale(1.25)">
  <path d="M38,0 L6,9 -26,7 -22,2 -8,2 -18,-7 -10,-7 6,-2 6,-9 12,-10 13,-2 Z"
        fill="#eef3f8" stroke="#9fb2c6" stroke-width="1.2" stroke-linejoin="round"/>
  <path d="M-2,-2 L-20,-22 -12,-22 8,-4 Z" fill="#d7e2ee" stroke="#9fb2c6" stroke-width="1"/>
  <path d="M-2,2 L-20,22 -12,22 8,4 Z" fill="#d7e2ee" stroke="#9fb2c6" stroke-width="1"/>
  <circle cx="22" cy="0" r="2.4" fill="#7fc0ff"/>
  <circle cx="14" cy="0" r="2.0" fill="#9bd0ff"/>
</g>'''


def build_svg():
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <defs>
    <linearGradient id="ocean" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#bfe3f7"/>
      <stop offset="1" stop-color="#8fc7ec"/>
    </linearGradient>
    <radialGradient id="sun" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0" stop-color="#fff6d8"/>
      <stop offset="1" stop-color="#ffe39a" stop-opacity="0"/>
    </radialGradient>
  </defs>

  <!-- 海/空の背景 -->
  <rect width="{W}" height="{H}" fill="url(#ocean)"/>
  <circle cx="860" cy="120" r="180" fill="url(#sun)"/>

  <!-- 日本地図 -->
  <g transform="translate({JP_TX},{JP_TY}) scale({JP_SCALE})">
    <g fill="#ffffff" opacity="0.0"></g>
    <g transform="translate(6,8)" fill="#1f7a3f" opacity="0.25">{JP_GROUP}</g>
    {JP_GROUP_FILL}
  </g>

  <!-- 飛行ルート -->
  <path d="M{PX0},{PY0} Q{PCX},{PCY} {PX1},{PY1}" fill="none"
        stroke="#ff5a52" stroke-width="4" stroke-linecap="round"
        stroke-dasharray="2 14"/>
  <circle cx="{PX0}" cy="{PY0}" r="7" fill="#ff5a52" stroke="#ffffff" stroke-width="2.5"/>

  <!-- ジェット機（ルート先端、進行方向へ機首） -->
  {jet}

  <!-- ラベル -->
  <text x="{JP_TX+150}" y="{JP_TY+250}" font-family="Noto Sans CJK JP, sans-serif"
        font-size="40" font-weight="bold" fill="#16652f" text-anchor="middle"
        stroke="#ffffff" stroke-width="4" paint-order="stroke">日本</text>
  <text x="{PX0+14}" y="{PY0+30}" font-family="Noto Sans CJK JP, sans-serif" font-size="20"
        font-weight="bold" fill="#16466e" text-anchor="start"
        stroke="#ffffff" stroke-width="3.5" paint-order="stroke">成田空港</text>
</svg>'''


# 日本本体（緑塗り）
JP_GROUP_FILL = JP_GROUP.replace('fill="#000000"', 'fill="#3aa55f"').replace(
    "stroke=\"none\"", 'stroke="#1f7a3f" stroke-width="6"')

# 機首の角度（弧の終点での接線方向 ≈ 制御点→終点）
import math
ang = math.degrees(math.atan2(PY1 - PCY, PX1 - PCX))
jet = JET.format(x=PX1, y=PY1, rot=ang)

svg = build_svg()
open("/home/user/blog-social-auto-post/eyecatch/japan_to_america.svg", "w").write(svg)
cairosvg.svg2png(bytestring=svg.encode("utf-8"),
                 write_to="/home/user/blog-social-auto-post/eyecatch/japan_to_america.png",
                 output_width=W, output_height=H)
print("OK")
