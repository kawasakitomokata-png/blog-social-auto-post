#!/usr/bin/env python3
"""
RSSフィードを監視し、新記事を検知したらGroq APIで3パターンのSNS投稿文を生成し
記事内の写真（最大3枚）をそれぞれ割り当てて8時・12時・17時にスケジュールする。
"""

import os
import json
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import feedparser
import requests
from groq import Groq

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

# ── 設定 ──────────────────────────────────────────────
BASE_DIR             = Path(__file__).parent
RSS_URL              = "https://kawasakitomokata.life/feed"
WP_API               = "https://kawasakitomokata.life/wp-json/wp/v2"
POSTED_URLS_FILE     = BASE_DIR / "posted_urls.txt"
SCHEDULED_POSTS_FILE = BASE_DIR / "scheduled_posts.json"
LOG_FILE             = BASE_DIR / "check_new_post.log"
JST                  = ZoneInfo("Asia/Tokyo")
CHECK_HOURS          = [9, 12, 17]

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

# ── WordPress アイキャッチ画像を取得 ─────────────────────

def get_featured_image(article_url: str) -> str:
    """WordPressのアイキャッチ画像（featured_media）のURLを取得する。"""
    post_id = article_url.rstrip("/").split("/")[-1]
    try:
        r = requests.get(
            f"{WP_API}/posts/{post_id}",
            params={"_fields": "featured_media"}, timeout=10
        )
        if r.status_code == 200:
            media_id = r.json().get("featured_media")
            if media_id:
                r2 = requests.get(
                    f"{WP_API}/media/{media_id}",
                    params={"_fields": "source_url"}, timeout=10
                )
                if r2.status_code == 200:
                    src = r2.json().get("source_url")
                    if src:
                        print(f"  アイキャッチ画像: {src.split('/')[-1]}")
                        return src
    except Exception as e:
        logging.warning(f"アイキャッチ取得失敗: {e}")
    return None

# ── WordPress 記事内の写真URLを取得 ──────────────────────

def get_article_images(article_url: str) -> list:
    """
    記事本文で使われている写真URLを最大5枚取得する（アイキャッチは除く）。
    優先順位:
      1. メディアライブラリ（記事に添付された画像）
      2. 本文中の src / data-src / data-lazy-src 属性
    """
    post_id = article_url.rstrip("/").split("/")[-1]
    images = []

    # ① WordPress メディアライブラリ（添付画像）
    try:
        r = requests.get(
            f"{WP_API}/media",
            params={"parent": post_id, "per_page": 20,
                    "media_type": "image", "_fields": "source_url"},
            timeout=10
        )
        if r.status_code == 200:
            for m in r.json():
                src = m.get("source_url", "")
                if src and src not in images:
                    images.append(src)
    except Exception as e:
        logging.warning(f"メディア一覧取得失敗: {e}")

    # ② 本文 HTML から画像URLを抽出（Jetpack スライドショー対応）
    if len(images) < 5:
        try:
            r2 = requests.get(
                f"{WP_API}/posts/{post_id}",
                params={"_fields": "content"},
                timeout=10
            )
            if r2.status_code == 200:
                content_html = r2.json().get("content", {}).get("rendered", "")

                # src / data-src / data-lazy-src を探す
                # ※ Jetpack CDN URL はクエリパラメータ付きのため [^"\']*) で末尾まで取得
                pattern = (r'(?:src|data-src|data-lazy-src)'
                           r'=["\']([^"\']+\.(?:jpg|jpeg|png|webp)[^"\']*)["\']')
                raw_matches = re.findall(pattern, content_html, re.IGNORECASE)

                for raw_url in raw_matches:
                    # ① HTML エンティティを解除して クエリパラメータを除去
                    url = (raw_url
                           .replace('&#038;', '&').replace('&amp;', '&')
                           .split('?')[0])
                    # ② Jetpack CDN (i0.wp.com / i1.wp.com) → オリジナル WordPress URL に変換
                    url = re.sub(r'^https?://i\d+\.wp\.com/', 'https://', url)
                    # ③ リサイズ版（-300x200.jpg など）は除外
                    if re.search(r'-\d+x\d+\.', url):
                        continue
                    if url and url not in images:
                        images.append(url)
                    if len(images) >= 5:
                        break

                # ③ data-id フォールバック（src が取れなかった画像を補完）
                if len(images) < 5:
                    data_ids = re.findall(r'data-id=["\'](\d+)["\']', content_html)
                    for mid in data_ids:
                        if len(images) >= 5:
                            break
                        try:
                            rm = requests.get(
                                f"{WP_API}/media/{mid}",
                                params={"_fields": "source_url"}, timeout=10
                            )
                            if rm.status_code == 200:
                                src = rm.json().get("source_url", "")
                                if src and src not in images:
                                    images.append(src)
                        except Exception:
                            pass
        except Exception as e:
            logging.warning(f"本文画像取得失敗: {e}")

    print(f"  記事内写真候補: {len(images)}枚")
    return images[:5]

# ── Groq API で投稿文生成 ─────────────────────────────

def generate_posts(title: str, url: str, summary: str) -> list:
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    prompt = f"""以下のブログ記事をSNS（X・Threads）で紹介する投稿文を「3つの異なる切り口」で作成してください。

【記事タイトル】{title}
【内容概要】{summary}

【投稿フォーマット】
各投稿は必ず以下の順番で構成してください：
1. タイトル行：記事タイトルをそのまま1行目に
2. 紹介文：2〜3文で、読んだ人が「読んでみたい」と自然に思えるような文章
3. ハッシュタグ：3〜4個

【紹介文の書き方】
- 必ず2文以上で書く（1文だけはNG）
- まるで日記や手紙のような、温かく親しみやすい語り口
- 読者が「あ、わかるな」と共感できるような日常的な視点を盛り込む
- 「！」は1投稿に1個まで

【紹介文の良い例】
- 「うまくいかない日が続いても、少しずつ前に進んでいる気がします。今日の出来事、よかったら読んでみてください。」
- 「試行錯誤しながらも、ちゃんと解決できた。そんな小さな積み重ねが、毎日を少し豊かにしてくれる気がしています。」

【制約】
- 紹介文は40字以上・80字以内の完全な文章で書く
- URLは含めない（別途付加します）
- ハッシュタグはブログの内容に合ったものを選ぶ
- 3つの切り口はそれぞれ異なる視点で

以下のJSON形式のみで返してください（前後に余分な文字・```は不要）:
[
  {{"angle":"切り口（10字以内）","title":"{title}","body":"紹介文（60字以内）","hashtags":["タグ1","タグ2","タグ3"]}},
  {{"angle":"切り口","title":"{title}","body":"紹介文","hashtags":["タグ1","タグ2","タグ3"]}},
  {{"angle":"切り口","title":"{title}","body":"紹介文","hashtags":["タグ1","タグ2","タグ3"]}}
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
    """
    SCHEDULE_ONLY=1 の場合（21時チェックのみ）:
        → 翌日の8・12・17時の3枠を返す（即時投稿なし）
    通常（8・12・17時の実行）:
        → 今すぐ + 次の2つのチェック時刻を返す
    """
    now = datetime.now(JST)
    schedule_only = os.environ.get("SCHEDULE_ONLY") == "1"

    # 次の3チェック時刻を探す
    upcoming = []
    for day_offset in [0, 1, 2]:
        base = (now + timedelta(days=day_offset)).replace(
            hour=0, minute=0, second=0, microsecond=0)
        for h in CHECK_HOURS:
            t = base.replace(hour=h)
            if t > now:
                upcoming.append(t)
            if len(upcoming) == 3:
                break
        if len(upcoming) == 3:
            break

    if schedule_only:
        # 21時チェック: 即時投稿なし、翌日8・12・17時の3枠
        print("  [チェックのみモード] 翌日3枠にスケジュール登録")
        return upcoming[:3]
    else:
        # 通常: 今すぐ + 次の2枠
        return [now - timedelta(seconds=10)] + upcoming[:2]

# ── スケジュール登録 ──────────────────────────────────

def schedule_posts(title: str, url: str, posts: list, eyecatch_url: str, article_images: list):
    """
    投稿をスケジュール登録する。
    - 1枚目（9時 or 即時）: WordPressアイキャッチ画像
    - 2枚目（12時）: 記事内写真1枚目
    - 3枚目（17時）: 記事内写真2枚目（1枚しかない場合はアイキャッチで代替→2回目と被らない）
    """
    times = get_post_times()
    scheduled = load_scheduled_posts()

    # アイキャッチと重複する画像を記事内写真から除外（ファイル名でも比較）
    eyecatch_basename = eyecatch_url.split("/")[-1] if eyecatch_url else ""
    body_images = [
        img for img in article_images
        if img != eyecatch_url and img.split("/")[-1] != eyecatch_basename
    ]

    # 画像割り当て：3枚とも必ず異なる画像を使う
    # 記事内写真が1枚しかない場合は 3回目にアイキャッチを再利用（2回目との重複を避ける）
    # 記事内写真が0枚の場合は全枠アイキャッチ（やむを得ない）
    if len(body_images) >= 2:
        # 理想ケース: 3枚とも異なる
        img0 = eyecatch_url
        img1 = body_images[0]
        img2 = body_images[1]
    elif len(body_images) == 1:
        # 記事内写真1枚: 2回目=記事内、3回目=アイキャッチ（2回目と異なる）
        img0 = eyecatch_url
        img1 = body_images[0]
        img2 = eyecatch_url
        logging.warning("記事内写真が1枚のみ: 3回目にアイキャッチを再利用")
        print("  ⚠ 記事内写真1枚のみ → 3回目はアイキャッチを使用")
    else:
        # 記事内写真なし: 全枠アイキャッチ
        img0 = img1 = img2 = eyecatch_url
        logging.warning("記事内写真なし: 全枠アイキャッチを使用")
        print("  ⚠ 記事内写真なし → 全枠アイキャッチを使用")

    image_map = [img0, img1, img2]

    for i, (send_at, post) in enumerate(zip(times, posts)):
        hashtag_str = " ".join(f"#{tag.lstrip('#')}" for tag in post["hashtags"])
        post_title = post.get("title", title)
        body       = post.get("body", post.get("text", ""))
        full_text  = f"{post_title}\n\n{body}\n{url}\n\n{hashtag_str}"

        image_url = image_map[i] if i < len(image_map) else eyecatch_url

        # X は9時（i=0）と17時（i=2）のみ、12時（i=1）はThreadsのみ
        platforms = ["x", "threads"] if i != 1 else ["threads"]

        scheduled.append({
            "send_at": send_at.isoformat(),
            "angle":   post["angle"],
            "text":    full_text,
            "title":   title,
            "url":     url,
            "sent":    False,
            "platforms": platforms,
            "image_url": image_url,
        })
        logging.info(f"Scheduled [{post['angle']}] at {send_at.isoformat()} platforms={platforms} img={image_url}")

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

        try:
            posts          = generate_posts(title, url, summary)
            eyecatch       = get_featured_image(url)
            article_images = get_article_images(url)
            schedule_posts(title, url, posts, eyecatch, article_images)
            save_posted_url(url)  # 成功時のみURLを記録
            print(f"  → 今すぐ＋9・12・17時にスケジュール登録しました（9時=アイキャッチ、12・17時=記事内写真）")
        except Exception as e:
            logging.error(f"Error processing {url}: {e}")
            print(f"  エラー: {e}")
            print(f"  ※ 次回のチェックで再試行します")

    logging.info("=== RSS check finished ===")


if __name__ == "__main__":
    main()
