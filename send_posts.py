#!/usr/bin/env python3
"""
スケジュール済みの投稿を時刻になったらX（Twitter）とThreadsに送信するスクリプト。
image_url（WordPress写真）をダウンロードしてXにアップロード、ThreadsにはURLをそのまま渡す。
"""

import os
import json
import logging
import tempfile
import requests
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import tweepy

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

BASE_DIR             = Path(__file__).parent
SCHEDULED_POSTS_FILE = BASE_DIR / "scheduled_posts.json"
LOG_FILE             = BASE_DIR / "send_posts.log"
JST                  = ZoneInfo("Asia/Tokyo")

logging.basicConfig(
    filename=LOG_FILE, level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ── X（Twitter）投稿 ──────────────────────────────────

def post_to_x(text: str, image_url: str = None) -> bool:
    try:
        client = tweepy.Client(
            consumer_key=os.environ["X_API_KEY"],
            consumer_secret=os.environ["X_API_SECRET"],
            access_token=os.environ["X_ACCESS_TOKEN"],
            access_token_secret=os.environ["X_ACCESS_TOKEN_SECRET"],
        )

        media_id = None
        if image_url:
            # WordPress写真をダウンロードして一時ファイルに保存しXにアップロード
            try:
                r = requests.get(image_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
                r.raise_for_status()
                suffix = ".jpg" if "jpg" in image_url.lower() or "jpeg" in image_url.lower() else ".png"
                with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                    tmp.write(r.content)
                    tmp_path = tmp.name

                auth = tweepy.OAuth1UserHandler(
                    os.environ["X_API_KEY"],
                    os.environ["X_API_SECRET"],
                    os.environ["X_ACCESS_TOKEN"],
                    os.environ["X_ACCESS_TOKEN_SECRET"],
                )
                api_v1 = tweepy.API(auth)
                media = api_v1.media_upload(filename=tmp_path)
                media_id = media.media_id
                print(f"  📷 画像アップロード完了: media_id={media_id}")
            except Exception as e:
                logging.warning(f"X画像アップロード失敗（テキストのみで続行）: {e}")
                media_id = None
            finally:
                try:
                    Path(tmp_path).unlink()
                except Exception:
                    pass

        if media_id:
            response = client.create_tweet(text=text, media_ids=[media_id])
        else:
            response = client.create_tweet(text=text)

        tweet_id = response.data["id"]
        logging.info(f"X posted: tweet_id={tweet_id}")
        print(f"  ✅ X投稿成功: tweet_id={tweet_id}")
        return True
    except Exception as e:
        logging.error(f"X post failed: {e}")
        print(f"  ❌ X投稿失敗: {e}")
        return False

# ── Threads 投稿 ──────────────────────────────────────

def post_to_threads(text: str, image_url: str = None) -> bool:
    access_token = os.environ.get("THREADS_ACCESS_TOKEN", "")
    user_id      = os.environ.get("THREADS_USER_ID", "")

    if not access_token or not user_id:
        logging.warning("Threads credentials not set.")
        return False

    try:
        create_url = f"https://graph.threads.net/v1.0/{user_id}/threads"

        if image_url:
            params = {"media_type": "IMAGE", "image_url": image_url,
                      "text": text, "access_token": access_token}
        else:
            params = {"media_type": "TEXT", "text": text, "access_token": access_token}

        res = requests.post(create_url, params=params)
        res.raise_for_status()
        container_id = res.json()["id"]

        import time; time.sleep(3)

        res2 = requests.post(
            f"https://graph.threads.net/v1.0/{user_id}/threads_publish",
            params={"creation_id": container_id, "access_token": access_token}
        )
        res2.raise_for_status()
        post_id = res2.json()["id"]
        logging.info(f"Threads posted: post_id={post_id}")
        print(f"  ✅ Threads投稿成功: post_id={post_id}")
        return True
    except Exception as e:
        logging.error(f"Threads post failed: {e}")
        print(f"  ❌ Threads投稿失敗: {e}")
        return False

# ── メイン ────────────────────────────────────────────

def main():
    if not SCHEDULED_POSTS_FILE.exists():
        return

    posts   = json.loads(SCHEDULED_POSTS_FILE.read_text())
    now     = datetime.now(JST)
    updated = False

    for post in posts:
        if post.get("sent"):
            continue

        send_at = datetime.fromisoformat(post["send_at"])
        if now < send_at:
            continue

        text      = post["text"]
        platforms = post.get("platforms", ["x"])
        angle     = post.get("angle", "")
        image_url = post.get("image_url")   # X・Threads共通のWordPress写真URL

        logging.info(f"Sending [{angle}]: {text[:40]}...")
        print(f"[送信] {angle}")

        results = {}

        if "x" in platforms:
            results["x"] = post_to_x(text, image_url)

        if "threads" in platforms:
            results["threads"] = post_to_threads(text, image_url)

        if any(results.values()):
            post["sent"]    = True
            post["sent_at"] = now.isoformat()
            post["results"] = results
            updated = True
            print(f"[送信完了] {angle} → {results}")
        else:
            logging.error(f"All platforms failed for: {angle}")

    if updated:
        SCHEDULED_POSTS_FILE.write_text(
            json.dumps(posts, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
