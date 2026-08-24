#!/usr/bin/env python3
"""
send_posts.yml の「送信済みフラグをコミット＆プッシュ」ステップから呼び出す。
リモート（origin/main）の scheduled_posts.json に、
このジョブ実行中にローカルで sent:true になったエントリの状態だけをマージして上書きする。
（check_rss.yml が同時に新しい記事をコミットしていても、その内容を消さずに済む）
"""
import json

with open('/tmp/remote_posts.json') as f:
    remote = json.load(f)
with open('scheduled_posts.json') as f:
    local = json.load(f)

local_map = {(p['send_at'], p.get('angle', '')): p for p in local}
for p in remote:
    key = (p['send_at'], p.get('angle', ''))
    if key in local_map and local_map[key].get('sent'):
        p['sent'] = True
        p['sent_at'] = local_map[key].get('sent_at')
        p['results'] = local_map[key].get('results', {})

with open('scheduled_posts.json', 'w') as f:
    json.dump(remote, f, ensure_ascii=False, indent=2)

print('Merge OK')
