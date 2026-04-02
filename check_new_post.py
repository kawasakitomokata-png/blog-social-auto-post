#!/usr/bin/env python3
"""
RSSフィードを監視し、新記事を検知したらGemini APIで3パターンのSNS投稿文を生成して
翌日9時・12時・17時にスケジュールするスクリプト。

使い方: GitHub Actionsで30分おきに自動実行
"""

import os
import json
import logging
import re
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import feedparser
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass  # GitHub Actions では環境変数から直接取得

# ── 設定 ──────────────────────────────────────────────
BASE_DIR = Path(__file__).parent

RSS_URL = "https://kawasakitomokata.life/feed"
POSTED_URLS_FILE = BASE_DIR / "posted_urls.txt"
SCHEDULED_POSTS_FILE = BASE_DIR / "scheduled_posts.json"
LOG_FILE = BASE_DIR / "check_new_post.log"
JST = ZoneInfo("Asia/Tokyo")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

SCHEDULE_HOURS = [9, 12, 17]  # 翌日 9時、12時、17時

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


# ── Gemini API で投稿文生成 ────────────────────────────

def generate_posts(title: str, url: str, summary: str) -> list[dict]:
    """3つの切り口でX投稿文（140字以内）＋ハッシュタグを生成して返す。"""
    api_key = os.environ["GEMINI_API_KEY"]
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={api_key}"

    prompt = f"""以下のブログ記事をX（Twitter）で紹介する投稿文を「3つの異なる切り口」で作成してください。

【記事タイトル】{title}
【記事URL】{url}
【内容概要】{summary}

【要件】
- 各投稿は本文＋URLで140字以内に収める
- 各投稿にハッシュタグを3〜5個付ける（投稿本文の後に）
- URLは含めず、本文とハッシュタグだけを返す（URLは別途付加します）
- 切り口はそれぞれ明確に異なる視点にする（例: コスパ、機能紹介、ターゲットユーザー など）
- 読者の興味を引く自然な日本語で書く

以下のJSON形式のみで返してください（前後に余分な文字・```は不要）:
[
  {{
    "angle": "切り口の説明（10字以内）",
    "text": "投稿本文（ハッシュタグなし・URL含めず・120字以内）",
    "hashtags": ["タグ1", "タグ2", "タグ3"]
  }},
  {{
    "angle": "切り口の説明",
    "text": "投稿本文",
    "hashtags": ["タグ1", "タグ2", "タグ3", "タグ4"]
  }},
  {{
    "angle": "切り口の説明",
    "text": "投稿本文",
    "hashtags": ["タグ1", "タグ2", "タグ3"]
  }}
]"""

    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 1024}
    }).encode("utf-8")

    req = urllib.request.Request(
        api_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            result = json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        raise Exception(f"Gemini API エラー {e.code}: {body[:300]}")

    raw = result["candidates"][0]["content"]["parts"][0]["text"].strip()

    # JSON部分のみ抽出
    match = re.search(r'\[.*\]', raw, re.DOTALL)
    if match:
        raw = match.group(0)
    return json.loads(raw)


# ── スケジュール登録 ──────────────────────────────────

def schedule_posts(title: str, url: str, posts: list[dict]):
    """3パターンを翌日9・12・17時にスケジュール登録する。"""
    now = datetime.now(JST)
    tomorrow = (now + timedelta(days=1)).date()
    scheduled = load_scheduled_posts()

    for hour, post in zip(SCHEDULE_HOURS, posts):
        send_at = datetime(
            tomorrow.year, tomorrow.month, tomorrow.day,
            hour, 0, 0, tzinfo=JST
        ).isoformat()

        hashtag_str = " ".join(f"#{tag.lstrip('#')}" for tag in post["hashtags"])
        full_text = f"{post['text']}\n{url}\n\n{hashtag_str}"

        scheduled.append({
            "send_at": send_at,
            "angle": post["angle"],
            "text": full_text,
            "title": title,
            "url": url,
            "sent": False,
            "platforms": ["x", "threads"],
        })
        logging.info(f"Scheduled [{post['angle']}] at {send_at}")

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
        title = entry.title
        url = entry.link
        summary = entry.get("summary", "")[:500]

        logging.info(f"New post detected: {title} ({url})")
        print(f"[新記事検知] {title}")
        print(f"  URL: {url}")

        try:
            posts = generate_posts(title, url, summary)
            schedule_posts(title, url, posts)
            save_posted_url(url)
            print(f"  → 翌日 9時・12時・17時にスケジュール登録しました")
        except Exception as e:
            logging.error(f"Error processing {url}: {e}")
            print(f"  エラー: {e}")

    logging.info("=== RSS check finished ===")


if __name__ == "__main__":
    main()
