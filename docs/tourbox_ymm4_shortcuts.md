# TourBox × YMM4（ゆっくりMovieMaker4）ショートカット割り当て案

TourBox には YMM4 用の公式プリセットが無いため、TourBox Console（設定アプリ）で
「キーボードショートカットの送信」を各操作子に割り当てることで、擬似的にYMM4のショートカットを再現します。

参照元のショートカット一覧: https://note.com/wagawaga_wagasi/n/nfcf68288cedb

## 前提

TourBox Console 5.11.3 の「YMM4」プリセットで実際の画面を確認したところ、メインボタン部分
（`Side` / `Top` / `Tall` / `Short`）には **長押し（Long Press）は無く**、代わりに次の3種類が使えます。

- シングルクリック（例: `Side`）
- ダブルクリック（例: `Side x2`）
- 2ボタン同時押し「組み合わせ」（例: `Side + Top`）— 主要4ボタンから2つを選ぶ組み合わせが6通り
  （Side+Top, Side+Tall, Side+Short, Top+Tall, Top+Short, Tall+Short）

これに加えて、以下の操作子があります。

- `C1` / `C2`（キットボタン。**ダブルクリックは無い**が、`Tall`/`Short`/`Top`/`Side`など
  他のボタンとの2ボタン同時押しには対応）
- `Knob`（回転CW/CCW + 押し込み）
- `Dial`（回転CW/CCW + 押し込み）
- `Scroll`（上下 + 押し込み）
- `D-Pad`（上下左右。`Top`/`Side`など他ボタンとの組み合わせにも対応）
- `Side` を押しながら `Knob` を回す／`D-Pad` を押す、という「保持しながら操作」の組み合わせ

## 初心者向け

| YMM4機能 | ショートカットキー | TourBox割り当て |
|---|---|---|
| 切り取り | Ctrl+X | Side（シングル） |
| コピー | Ctrl+C | Side x2（ダブルクリック） |
| 貼り付け | Ctrl+V | Knob 押し込み |
| 削除 | DELETE | Short（シングル） |
| 元に戻す | Ctrl+Z | Dial 左回転 |
| やり直し | Ctrl+Y / Ctrl+Shift+Z | Dial 右回転 |
| プロジェクトを保存 | Ctrl+S | Top（シングル） |
| プロジェクトを別名で保存 | Ctrl+Shift+S | Side + Top（同時押し） |
| 再生/一時停止 | SPACE | Tall（シングル） |

## 中級者向け

| YMM4機能 | ショートカットキー | TourBox割り当て |
|---|---|---|
| すべて選択 | Ctrl+A | Tall x2（ダブルクリック） |
| グループ化 | Ctrl+G | Side + Tall（同時押し） |
| グループ化を解除 | Ctrl+Shift+G | Side + Short（同時押し） |
| 再生位置で分割 | Ctrl+B | Tall + C1（同時押し） |
| 再生位置のアイテムを分割 | Ctrl+Shift+B | Tall + C2（同時押し） |
| 動画の先頭に移動 | HOME | Top + Tall（同時押し） |
| 動画の末尾に移動 | END | Top + Short（同時押し） |
| 次の編集点へ移動 | Ctrl+RIGHT | Knob 右回転 |
| 前の編集点へ移動 | Ctrl+LEFT | Knob 左回転 |
| 再生速度を下げる | Ctrl+, | Scroll 下 |
| 再生速度を上げる | Ctrl+. | Scroll 上 |

## 上級者向け

| YMM4機能 | ショートカットキー | TourBox割り当て |
|---|---|---|
| 右のアイテムをすべて選択 | Ctrl+Shift+RIGHT | Side を押しながら Knob 右回転 |
| 左のアイテムをすべて選択 | Ctrl+Shift+LEFT | Side を押しながら Knob 左回転 |
| ひとつ上のアイテムを選択 | Ctrl+Alt+Shift+UP | Side を押しながら D-Pad 上 |
| ひとつ下のアイテムを選択 | Ctrl+Alt+Shift+DOWN | Side を押しながら D-Pad 下 |
| ひとつ左のアイテムを選択 | Ctrl+Alt+Shift+LEFT | Side を押しながら D-Pad 左 |
| ひとつ右のアイテムを選択 | Ctrl+Alt+Shift+RIGHT | Side を押しながら D-Pad 右 |
| 次のフレームへ移動 | RIGHT | D-Pad 右（シングル） |
| 前のフレームへ移動 | LEFT | D-Pad 左（シングル） |
| 上のレイヤーへ移動 | UP | D-Pad 上（シングル） |
| 下のレイヤーへ移動 | DOWN | D-Pad 下（シングル） |
| 次のキャラクターに変更 | Ctrl+D | C1（シングル） |
| 前のキャラクターに変更 | Ctrl+Shift+D | C2（シングル） |
| 編集エリアにフォーカスを移す | Ctrl+TAB | Top x2（ダブルクリック） |
| テンプレート一覧を開く | Ctrl+T | Short x2（ダブルクリック） |

## 空いている操作子（今後の追加・調整用）

- `Tall + Short` 同時押し
- `C1 + C2` 同時押し
- `Top + C1` / `Top + C2` 同時押し
- `Short + C1` / `Short + C2` 同時押し
- `Dial` 押し込み
- `Scroll` 押し込み

## TourBox Console での設定手順（概要）

1. TourBox Console を起動し、左のプリセットリストから「YMM4」プリセットを選択する
2. 上表の各操作子を選択し、「キーボードショートカットの送信（Keyboard Shortcut）」を選んで
   対応するキー入力（例: `Ctrl+X`）を登録する
3. ダブルクリック（`x2`）が必要な項目は、対象ボタンの `x2` の行に登録する
4. 2ボタン同時押しが必要な項目（例: `Side + Top`）は、メインボタン部分の「組み合わせを表示」を
   開き、該当する組み合わせの行に登録する
5. `Side` を押しながら `Knob`/`D-Pad` を操作する項目は、`Knob`/`D-Pad` 側の「組み合わせを表示」から
   `Side` を組み合わせ対象に選んで登録する
6. 設定後、YMM4を実際に操作しながら誤動作がないか確認し、必要に応じて頻度の高い機能を
   押しやすいボタン（Tall/Top/Side）へ入れ替える

## 補足

- お使いの機種（NEO / Elite / Elite Plus）やお好みの手（左右）によって最適な配置は変わります。
  上記は一案なので、実際の使用感に合わせて調整してください。
- ダブルクリックの反応時間はTourBox Console側で調整可能です。誤爆する場合は
  しきい値を伸ばすか、頻度の高い機能はシングルクリックに寄せてください。
- `C1` / `C2` にはダブルクリックが無いため、追加で機能を割り当てたい場合は
  `Tall + C1` のような2ボタン同時押しや、上表の「空いている操作子」を使ってください。
