"""世界地図イラスト生成。

Natural Earth (public domain) の land GeoJSON を正距円筒図法で SVG に投影し、
海(背景)＋大陸(塗り)のシンプルでフラットな世界地図を描く。
出力: world_map.svg / world_map.png
"""
import json
import cairosvg

W, H = 1000, 520
PAD = 20
land = json.load(open("/tmp/land.json"))

# 経度-180..180 / 緯度 84..-60 あたりを画面にフィット（南極は省きぎみ）
LON0, LON1 = -180, 180
LAT0, LAT1 = 83, -56


def project(lon, lat):
    x = PAD + (lon - LON0) / (LON1 - LON0) * (W - 2 * PAD)
    y = PAD + (LAT0 - lat) / (LAT0 - LAT1) * (H - 2 * PAD)
    return x, y


def ring_to_path(ring):
    pts = []
    for lon, lat in ring:
        x, y = project(lon, lat)
        pts.append(f"{x:.1f},{y:.1f}")
    return "M" + " L".join(pts) + " Z"


paths = []
for feat in land["features"]:
    geom = feat["geometry"]
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for poly in polys:
        d = " ".join(ring_to_path(ring) for ring in poly)
        paths.append(d)

land_path = "\n".join(
    f'<path d="{d}" fill="#5fbf74" stroke="#3f9f57" stroke-width="0.8"/>' for d in paths)

SVG = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <defs>
    <linearGradient id="sea" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#bfe3f7"/>
      <stop offset="1" stop-color="#8fc7ec"/>
    </linearGradient>
  </defs>
  <rect width="{W}" height="{H}" fill="url(#sea)"/>
  <!-- 緯度経度のうすいグリッド -->
  <g stroke="#ffffff" stroke-opacity="0.35" stroke-width="1">
    <line x1="{W/2}" y1="0" x2="{W/2}" y2="{H}"/>
    <line x1="0" y1="{H/2}" x2="{W}" y2="{H/2}"/>
  </g>
  {land_path}
</svg>'''

open("/home/user/blog-social-auto-post/eyecatch/world_map.svg", "w").write(SVG)
cairosvg.svg2png(bytestring=SVG.encode("utf-8"),
                 write_to="/home/user/blog-social-auto-post/eyecatch/world_map.png",
                 output_width=W * 2, output_height=H * 2)
print(f"OK ({len(paths)} polygons)")
