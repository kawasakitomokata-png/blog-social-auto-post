#!/usr/bin/env python3
"""
スケジュール済みの投稿を時刻になったらX（Twitter）とThreadsに送信するスクリプト。

使い方: cronで毎分実行
例: * * * * * /path/to/venv/bin/python /path/to/send_posts.py
"""

import os
import json
import logging
import requests
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import tweepy
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass  # GitHub Actions では環境変数から直接取得

# ── 設定 ──────────────────────────────────────────────
BASE_DIR = Path(__file__).parent

SCHEDULED_POSTS_FILE = BASE_DIR / "scheduled_posts.json"
LOG_FILE = BASE_DIR / "send_posts.log"
JST = ZoneInfo("Asia/Tokyo")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ── X（Twitter）投稿 ──────────────────────────────────

def post_to_x(text: str) -> bool:
    try:
        client = tweepy.Client(
            consumer_key=os.environ["X_API_KEY"],
            consumer_secret=os.environ["X_API_SECRET"],
            access_token=os.environ["X_ACCESS_TOKEN"],
            access_token_secret=os.environ["X_ACCESS_TOKEN_SECRET"],
        )
        response = client.create_tweet(text=text)
        tweet_id = response.data["id"]
        logging.info(f"X posted: tweet_id={tweet_id}")
        return True
    except Exception as e:
        logging.error(f"X post failed: {e}")
        return False


# ── Threads 投稿 ──────────────────────────────────────
# Threads API (Meta) は OAuth 2.0 Long-Lived Token を使用
# トークン取得後に THREADS_ACCESS_TOKEN と THREADS_USER_ID を .env に設定してください

def post_to_threads(text: str) -> bool:
    access_token = os.environ.get("THREADS_ACCESS_TOKEN", "")
    user_id = os.environ.get("THREADS_USER_ID", "")

    if not access_token or not user_id:
        logging.warning("Threads credentials not set. Skipping Threads post.")
        return False

    try:
        # Step 1: コンテナ作成
        create_url = f"https://graph.threads.net/v1.0/{user_id}/threads"
        res = requests.post(create_url, params={
            "media_type": "TEXT",
            "text": text,
            "access_token": access_token,
        })
        res.raise_for_status()
        container_id = res.json()["id"]

        # Step 2: 公開
        publish_url = f"https://graph.threads.net/v1.0/{user_id}/threads_publish"
        res2 = requests.post(publish_url, params={
            "creation_id": container_id,
            "access_token": access_token,
        })
        res2.raise_for_status()
        post_id = res2.json()["id"]
        logging.info(f"Threads posted: post_id={post_id}")
        return True
    except Exception as e:
        logging.error(f"Threads post failed: {e}")
        return False


# ── メイン ────────────────────────────────────────────

def main():
    if not SCHEDULED_POSTS_FILE.exists():
        return

    posts = json.loads(SCHEDULED_POSTS_FILE.read_text())
    now = datetime.now(JST)
    updated = False

    for post in posts:
        if post.get("sent"):
            continue

        send_at = datetime.fromisoformat(post["send_at"])
        if now < send_at:
            continue  # まだ時刻でない

        text = post["text"]
        platforms = post.get("platforms", ["x"])
        angle = post.get("angle", "")
        logging.info(f"Sending [{angle}]: {text[:40]}...")

        results = {}

        if "x" in platforms:
            results["x"] = post_to_x(text)

        if "threads" in platforms:
            results["threads"] = post_to_threads(text)

        if any(results.values()):
            post["sent"] = True
            post["sent_at"] = now.isoformat()
            post["results"] = results
            updated = True
            print(f"[送信完了] {angle} → {results}")
        else:
            logging.error(f"All platforms failed for: {angle}")

    if updated:
        SCHEDULED_POSTS_FILE.write_text(json.dumps(posts, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
