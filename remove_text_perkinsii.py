# -*- coding: utf-8 -*-
"""C. perkinsii の画像から白い文字を消して背景になじませる。

白い文字だけをマスクとして抽出し、その部分を「素の背景」で置き換える。
背景レベルは、文字でもフィラメント・輝点でもない画素だけを使った局所平均として
推定し、同じく局所的に測ったばらつきの粒状ノイズを乗せて周囲となじませる。
近傍画素の単純コピーはマゼンタのフィラメントを拾って滲むので使わない。
画像全体の統計も黒い余白に引きずられて暗くなりすぎるので使わない。
"""
import numpy as np
import cv2
from PIL import Image

SRC = "C・パーキンシー.png"
DST = "C・パーキンシー_文字消し.png"

# 文字がある領域（x0, y0, x1, y1）
TEXT_BOXES = [
    (90, 34, 325, 88),     # タイトル "C. perkinsii"
    (384, 36, 406, 162),   # 縦書きクレジット "Credit: © DudinLab"
    (70, 404, 306, 441),   # キャプション1行目 "organism called"
    (98, 441, 270, 476),   # キャプション2行目 "C. perkinsii."
]

rgba = Image.open(SRC).convert("RGBA")
alpha = np.asarray(rgba)[:, :, 3].copy()
img = np.asarray(rgba.convert("RGB")).astype(np.uint8)
H, W = img.shape[:2]

# ---------------------------------------------------------------- 文字マスク
# 白い文字＝R,G,B がそろって明るい。マゼンタ/黄/シアンの像の成分は
# どれか1チャンネルが暗いので min チャンネルのしきい値でよく分離できる。
mn = img.min(axis=2)
white = (mn > 55).astype(np.uint8) * 255

mask = np.zeros((H, W), np.uint8)
for x0, y0, x1, y1 in TEXT_BOXES:
    mask[y0:y1, x0:x1] = white[y0:y1, x0:x1]

# アンチエイリアスのふちまで確実に覆う
mask = cv2.dilate(mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)), 1)
print("mask px:", int((mask > 0).sum()))

# ---------------------------------------------------------------- 素の背景を推定
# 背景レベルは「文字でも明るい構造でもない画素」だけを使った局所平均で求める。
# 画像全体の統計を使うと黒い余白に引きずられて暗くなりすぎるので必ず局所で見る。
f = img.astype(np.float32)
valid = (mask == 0).astype(np.float32)
bright = f.max(axis=2)


def local_mean(x, w, weight):
    """weight が 1 の画素だけを使った w×w の局所平均。"""
    num = cv2.boxFilter(x * weight, -1, (w, w), normalize=False)
    den = cv2.boxFilter(weight, -1, (w, w), normalize=False)
    return num / np.maximum(den, 1e-3)


# 局所平均より暗い画素＝フィラメントや輝点でない素の背景
coarse = local_mean(bright, 31, valid)
dark = (valid > 0) & (bright <= coarse)
dark = dark.astype(np.float32)

W_BG = 41
base = np.empty_like(f)
var = np.empty_like(f)
for c in range(3):
    m1 = local_mean(f[..., c], W_BG, dark)
    m2 = local_mean(f[..., c] ** 2, W_BG, dark)
    base[..., c] = m1
    var[..., c] = np.maximum(m2 - m1 ** 2, 0.0)
base = cv2.GaussianBlur(base, (0, 0), 2.0)

# 暗部だけを見た分散は本来のばらつきより小さく出るので少し持ち上げる
noise_sigma = np.clip(np.sqrt(var) * 1.9, 1.0, 16.0)
noise_sigma = cv2.GaussianBlur(noise_sigma, (0, 0), 2.0)

rng = np.random.default_rng(7)
fill = base + rng.normal(0, 1, (H, W, 3)).astype(np.float32) * noise_sigma

# ---------------------------------------------------------------- 合成
# マスクのふちを少しぼかして、埋めた部分と元画像の境目を消す
soft = cv2.GaussianBlur(mask.astype(np.float32) / 255.0, (0, 0), 1.6)
soft = np.clip(soft * 1.35, 0, 1)[:, :, None]
out = img.astype(np.float32) * (1 - soft) + fill * soft
out = np.clip(out, 0, 255).astype(np.uint8)

Image.fromarray(np.dstack([out, alpha]), "RGBA").save(DST)
print("wrote", DST)
