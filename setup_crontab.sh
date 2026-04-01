#!/bin/bash
# crontab 設定スクリプト
# 実行: bash setup_crontab.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="$SCRIPT_DIR/venv/bin/python"

# venv がなければ作成して依存パッケージをインストール
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo "venv を作成します..."
    python3 -m venv "$SCRIPT_DIR/venv"
    "$SCRIPT_DIR/venv/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"
fi

# .env が未作成なら .env.example をコピー
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
    echo "⚠️  .env ファイルを作成しました。APIキーを設定してください: $SCRIPT_DIR/.env"
fi

# 既存の該当行を削除してから追加
crontab -l 2>/dev/null | grep -v "social_auto_post" > /tmp/crontab_tmp

cat >> /tmp/crontab_tmp << EOF

# ブログ新記事チェック（毎時0分・30分）
0,30 * * * * $PYTHON $SCRIPT_DIR/check_new_post.py >> $SCRIPT_DIR/check_new_post.log 2>&1

# スケジュール投稿送信（毎分）
* * * * * $PYTHON $SCRIPT_DIR/send_posts.py >> $SCRIPT_DIR/send_posts.log 2>&1
EOF

crontab /tmp/crontab_tmp
rm /tmp/crontab_tmp

echo "✅ crontab に登録しました。現在の設定:"
crontab -l | grep "social_auto_post"
