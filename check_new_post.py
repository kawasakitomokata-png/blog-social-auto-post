#!/usr/bin/env python3
"""
RSSフィードを監視し、新記事を検知したらGroq APIで3パターンのSNS投稿文＋
アイキャッチ画像（3種類）を生成して8時・12時・17時にスケジュールするスクリプト。
"""

import os
import json
import logging
import re
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import feedparser
import requests
from groq import Groq
from PIL import Image, ImageEnhance, ImageDraw, ImageFont

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

# ── 設定 ──────────────────────────────────────────────
BASE_DIR     = Path(__file__).parent
EYECATCH_DIR = BASE_DIR / "eyecatch"
GITHUB_RAW   = "https://raw.githubusercontent.com/kawasakitomokata-png/blog-social-auto-post/main/eyecatch"

RSS_URL             = "https://kawasakitomokata.life/feed"
WP_API              = "https://kawasakitomokata.life/wp-json/wp/v2"
POSTED_URLS_FILE    = BASE_DIR / "posted_urls.txt"
SCHEDULED_POSTS_FILE= BASE_DIR / "scheduled_posts.json"
LOG_FILE            = BASE_DIR / "check_new_post.log"
JST                 = ZoneInfo("Asia/Tokyo")
CHECK_HOURS         = [8, 12, 17]

logging.basicConfig(
    filename=LOG_FILE, level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ── ユーティリティ ────────────────────────────────────

def load_posted_urls() -> set:
    if not POSTED_URLS_FILE.exists():
        return set()
    return set(POSTED_URLS_FILE.read_text().splitlines())

def save_posted_url(url: str):
    with open(POSTED_URLS_FILE, "a") as f:
        f.write(url + "\n")

def load_scheduled_posts() -> list:
    if not SCHEDULED_POSTS_FILE.exists():
        return []
    return json.loads(SCHEDULED_POSTS_FILE.read_text())

def save_scheduled_posts(posts: list):
    SCHEDULED_POSTS_FILE.write_text(json.dumps(posts, ensure_ascii=False, indent=2))

# ── WordPress 記事内の画像URL一覧を取得 ───────────────

def get_article_images(article_url: str) -> list[str]:
    """
    記事内で使われている写真URLを最大3枚取得する。
    優先順位:
      1. メディアライブラリ（記事に添付された画像）
      2. 本文中の <img> タグ
      3. アイキャッチ画像（featured_media）
    """
    post_id = article_url.rstrip("/").split("/")[-1]
    images = []

    try:
        # 1. 記事に添付されたメディア一覧（実際に使用した写真が含まれる）
        r = requests.get(
            f"{WP_API}/media",
            params={"parent": post_id, "per_page": 10,
                    "media_type": "image", "_fields": "source_url"},
            timeout=10
        )
        if r.status_code == 200:
            for m in r.json():
                src = m.get("source_url", "")
                # スケールされたサムネイルは除外（元サイズのみ）
                if src and "-scaled" not in src or src.endswith(".jpg") or src.endswith(".jpeg"):
                    if src not in images:
                        images.append(src)
    except Exception as e:
        logging.warning(f"メディア一覧取得失敗: {e}")

    # 2. 本文中の <img> タグからURL抽出
    if len(images) < 3:
        try:
            r2 = requests.get(
                f"{WP_API}/posts/{post_id}",
                params={"_fields": "content,featured_media"},
                timeout=10
            )
            if r2.status_code == 200:
                data = r2.json()
                content_html = data.get("content", {}).get("rendered", "")
                # src= からURLを抽出
                found = re.findall(
                    r'src=["\']([^"\']+\.(?:jpg|jpeg|png|webp))["\']',
                    content_html, re.IGNORECASE
                )
                # 大きい画像のみ（-150x150 等のサムネは除外）
                for url in found:
                    if not re.search(r'-\d+x\d+\.', url) and url not in images:
                        images.append(url)
                    if len(images) >= 3:
                        break

                # 3. アイキャッチ（featured_media）をフォールバックに追加
                media_id = data.get("featured_media")
                if media_id and len(images) < 3:
                    r3 = requests.get(
                        f"{WP_API}/media/{media_id}",
                        params={"_fields": "source_url"}, timeout=10
                    )
                    if r3.status_code == 200:
                        src = r3.json().get("source_url")
                        if src and src not in images:
                            images.insert(0, src)  # アイキャッチは先頭に
        except Exception as e:
            logging.warning(f"本文画像取得失敗: {e}")

    print(f"  取得した記事内写真: {len(images)}枚")
    return images[:3]  # 最大3枚

# ── フォント ───────────────────────────────────────────

def find_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    candidates = (
        ["/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
         "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"]
        if bold else
        ["/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
         "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc"]
    )
    # GitHub Actions (Ubuntu) 用
    candidates += [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()

# ── 共通: 画像リサイズ＆補正 ──────────────────────────

def prepare_bg(src: Image.Image, brightness=1.25, contrast=0.93, color=1.10) -> Image.Image:
    W, H = 1200, 630
    img = src.copy()
    iw, ih = img.size
    scale = max(W / iw, H / ih)
    img = img.resize((int(iw * scale), int(ih * scale)), Image.LANCZOS)
    iw2, ih2 = img.size
    img = img.crop(((iw2 - W) // 2, (ih2 - H) // 2,
                    (iw2 - W) // 2 + W, (ih2 - H) // 2 + H))
    img = ImageEnhance.Brightness(img).enhance(brightness)
    img = ImageEnhance.Contrast(img).enhance(contrast)
    img = ImageEnhance.Color(img).enhance(color)
    return img

def draw_text_centered(draw, text, font, y, fill, shadow=(0,0,0,140)):
    W = 1200
    bbox = draw.textbbox((0, 0), text, font=font)
    x = (W - (bbox[2] - bbox[0])) // 2
    draw.text((x+2, y+2), text, font=font, fill=shadow)
    draw.text((x, y), text, font=font, fill=fill)

def overlay_gradient(img: Image.Image, direction="bottom",
                     color=(10,8,5), max_alpha=190) -> Image.Image:
    W, H = img.size
    ov = Image.new("RGBA", (W, H), (0,0,0,0))
    d  = ImageDraw.Draw(ov)
    for i in range(H):
        if direction == "bottom":
            t = max(0, (i - H//2) / (H//2))
        else:  # top
            t = max(0, (H//2 - i) / (H//2))
        alpha = int(max_alpha * min(t, 1.0))
        d.rectangle([(0,i),(W,i)], fill=(*color, alpha))
    return Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")

# ── スタイル1: 下部グラデーション・中央タイトル（朝8時）──

def style1(bg: Image.Image, title: str) -> Image.Image:
    img = overlay_gradient(prepare_bg(bg, brightness=1.30), "bottom", max_alpha=195)
    draw = ImageDraw.Draw(img)
    f_tag  = find_font(20, bold=False)
    f_main = find_font(88, bold=True)
    f_sub  = find_font(22, bold=False)
    # タグ
    tag = "川﨑知容のブログ"
    bbox = draw.textbbox((0,0), tag, font=f_tag)
    tx = (1200 - (bbox[2]-bbox[0])) // 2
    draw.text((tx, 405), tag, font=f_tag, fill=(255,245,220))
    # タイトル
    draw_text_centered(draw, title, f_main, 438, (255,255,255))
    # URL
    draw_text_centered(draw, "kawasakitomokata.life", f_sub, 572, (200,190,175))
    return img

# ── スタイル2: 上部グラデーション・タイトル上部（昼12時）─

def style2(bg: Image.Image, title: str) -> Image.Image:
    img = overlay_gradient(prepare_bg(bg, brightness=1.20, color=1.05),
                           "top", color=(5,10,20), max_alpha=210)
    draw = ImageDraw.Draw(img)
    f_tag  = find_font(20, bold=False)
    f_main = find_font(82, bold=True)
    f_sub  = find_font(22, bold=False)
    # タグ
    draw_text_centered(draw, "川﨑知容のブログ", f_tag, 42, (200,220,255))
    # タイトル
    draw_text_centered(draw, title, f_main, 82, (255,255,255))
    # URL（下）
    f_url = find_font(20, bold=False)
    draw_text_centered(draw, "kawasakitomokata.life", f_url, 590, (180,180,180))
    return img

# ── スタイル3: 中央帯・白ボックスタイトル（夕17時）──────

def style3(bg: Image.Image, title: str) -> Image.Image:
    img = prepare_bg(bg, brightness=1.15, contrast=0.90)
    # 全体に薄いオーバーレイ
    ov = Image.new("RGBA", (1200,630), (0,0,0,90))
    img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
    draw = ImageDraw.Draw(img)
    f_main = find_font(76, bold=True)
    f_sub  = find_font(22, bold=False)
    # 中央白帯
    bbox = draw.textbbox((0,0), title, font=f_main)
    tw = bbox[2]-bbox[0]
    th = bbox[3]-bbox[1]
    pad_x, pad_y = 48, 24
    box_x = (1200 - tw) // 2 - pad_x
    box_y = 240
    box_w = tw + pad_x*2
    box_h = th + pad_y*2
    # 白帯（半透明）
    band = Image.new("RGBA", (1200,630), (0,0,0,0))
    bd = ImageDraw.Draw(band)
    bd.rounded_rectangle([box_x, box_y, box_x+box_w, box_y+box_h],
                          radius=12, fill=(255,255,255,230))
    img = Image.alpha_composite(img.convert("RGBA"), band).convert("RGB")
    draw = ImageDraw.Draw(img)
    # タイトル（黒）
    tx = (1200 - tw) // 2
    draw.text((tx, box_y + pad_y), title, font=f_main, fill=(30,30,30))
    # URL
    draw_text_centered(draw, "kawasakitomokata.life", f_sub, 592, (220,215,205))
    return img

# ── アイキャッチ3枚生成 ───────────────────────────────

def download_image(url: str, dest: Path) -> bool:
    """画像をダウンロードしてdestに保存。成功したらTrue。"""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        dest.write_bytes(r.content)
        return True
    except Exception as e:
        logging.warning(f"画像DL失敗 {url}: {e}")
        return False


def generate_eyecatch_images(title: str, article_url: str) -> list:
    """
    記事内の写真を最大3枚使い、それぞれ異なるスタイルのアイキャッチを生成する。
    写真が1〜2枚しかない場合は同じ写真を使い回す。
    """
    img_urls = get_article_images(article_url)
    if not img_urls:
        print("  記事内の画像が取得できませんでした（テキストのみで投稿）")
        return [None, None, None]

    EYECATCH_DIR.mkdir(exist_ok=True)
    post_id = article_url.rstrip("/").split("/")[-1]
    styles  = [style1, style2, style3]
    paths   = []

    for i, style_fn in enumerate(styles, 1):
        # 使う写真: i枚目があればそれ、なければ最後の写真を使い回す
        url = img_urls[min(i - 1, len(img_urls) - 1)]
        tmp = EYECATCH_DIR / f"_src_{post_id}_{i}.jpg"
        out = EYECATCH_DIR / f"eyecatch_{post_id}_{i}.jpg"

        if not download_image(url, tmp):
            paths.append(None)
            continue

        try:
            bg     = Image.open(tmp).convert("RGB")
            result = style_fn(bg, title)
            result.save(out, "JPEG", quality=93)
            paths.append(str(out.relative_to(BASE_DIR)))
            print(f"  アイキャッチ{i}生成: {out.name}（写真{min(i, len(img_urls))}枚目）")
        except Exception as e:
            logging.warning(f"スタイル{i}生成失敗: {e}")
            paths.append(None)
        finally:
            if tmp.exists():
                tmp.unlink()

    return paths

# ── Groq API で投稿文生成 ─────────────────────────────

def generate_posts(title: str, url: str, summary: str) -> list[dict]:
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    prompt = f"""以下のブログ記事をX（Twitter）で紹介する投稿文を「3つの異なる切り口」で作成してください。

【記事タイトル】{title}
【記事URL】{url}
【内容概要】{summary}

【要件】
- 各投稿は本文＋URLで140字以内に収める
- 各投稿にハッシュタグを3〜5個付ける（投稿本文の後に）
- URLは含めず、本文とハッシュタグだけを返す（URLは別途付加します）
- 切り口はそれぞれ明確に異なる視点にする
- 読者の興味を引く自然な日本語で書く

以下のJSON形式のみで返してください（前後に余分な文字・```は不要）:
[
  {{"angle":"切り口（10字以内）","text":"本文（120字以内）","hashtags":["タグ1","タグ2","タグ3"]}},
  {{"angle":"切り口","text":"本文","hashtags":["タグ1","タグ2","タグ3"]}},
  {{"angle":"切り口","text":"本文","hashtags":["タグ1","タグ2","タグ3"]}}
]"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=1024, temperature=0.7,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = response.choices[0].message.content.strip()
    match = re.search(r'\[.*\]', raw, re.DOTALL)
    if match:
        raw = match.group(0)
    return json.loads(raw)

# ── 投稿時刻を決定 ───────────────────────────────────

def get_post_times() -> list:
    now = datetime.now(JST)
    immediate = now - timedelta(seconds=10)
    upcoming = []
    for day_offset in [0, 1]:
        base = (now + timedelta(days=day_offset)).replace(
            hour=0, minute=0, second=0, microsecond=0)
        for h in CHECK_HOURS:
            t = base.replace(hour=h)
            if t > now:
                upcoming.append(t)
            if len(upcoming) == 2:
                break
        if len(upcoming) == 2:
            break
    return [immediate] + upcoming

# ── スケジュール登録 ──────────────────────────────────

def schedule_posts(title: str, url: str, posts: list[dict], image_paths: list, article_images: list):
    times = get_post_times()
    scheduled = load_scheduled_posts()

    for i, (send_at, post, img_path) in enumerate(zip(times, posts, image_paths)):
        hashtag_str = " ".join(f"#{tag.lstrip('#')}" for tag in post["hashtags"])
        full_text = f"{post['text']}\n{url}\n\n{hashtag_str}"

        # Threads用: WordPressに既にある記事内写真を使う（i枚目、なければ先頭）
        threads_image_url = article_images[min(i, len(article_images) - 1)] if article_images else None

        scheduled.append({
            "send_at": send_at.isoformat(),
            "angle": post["angle"],
            "text": full_text,
            "title": title,
            "url": url,
            "sent": False,
            "platforms": ["x", "threads"],
            "image_path": img_path,              # X用（ローカルファイル・アイキャッチ）
            "image_url": threads_image_url,      # Threads用（WordPress画像URL）
        })
        logging.info(f"Scheduled [{post['angle']}] at {send_at.isoformat()} img={img_path}")

    save_scheduled_posts(scheduled)

# ── メイン ────────────────────────────────────────────

def main():
    logging.info("=== RSS check started ===")
    posted_urls = load_posted_urls()

    feed = feedparser.parse(RSS_URL)
    if feed.bozo:
        logging.error(f"RSS parse error: {feed.bozo_exception}")
        return

    new_entries = [e for e in feed.entries if e.link not in posted_urls]
    if not new_entries:
        logging.info("No new posts found.")
        print("新着記事なし")
        return

    for entry in new_entries:
        title   = entry.title
        url     = entry.link
        summary = entry.get("summary", "")[:500]

        logging.info(f"New post detected: {title} ({url})")
        print(f"[新記事検知] {title}")
        print(f"  URL: {url}")

        save_posted_url(url)

        try:
            posts           = generate_posts(title, url, summary)
            article_images  = get_article_images(url)
            image_paths     = generate_eyecatch_images(title, url)
            schedule_posts(title, url, posts, image_paths, article_images)
            print(f"  → 今すぐ＋8・12・17時にスケジュール登録しました（画像付き）")
        except Exception as e:
            logging.error(f"Error processing {url}: {e}")
            print(f"  エラー: {e}")
            print(f"  ※ URLは記録済みのため次回からスキップされます")

    logging.info("=== RSS check finished ===")


if __name__ == "__main__":
    main()
