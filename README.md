# 読めるサイト

`公開/` を GitHub Pages にそのまま置く。**増やすときに触るのは `作品.json` と画像だけ。**

```bash
cd ~/Desktop/birdman/サイト
python3 build.py          # 公開/ を組み直す
cd 公開 && git add -A && git commit -m "..." && git push
```

## 話を足す

1. `原稿/02話/ページ/p01.png …` を組む（`compose.py 02話/pages.py`）
2. `作品.json` の `episodes` にある該当話から `"状態": "準備中"` を消す
3. `python3 build.py` → push

**ページ数はJSONに書かない。** 画像の実数から数えている。
書き写すと必ずずれて、「全22ページ」と言いながら21枚、が起きるため。
`ページ/` が空の話は自動的に「準備中」として一覧にだけ出る。

## 作品を足す

`作品.json` の `works` に1ブロック足す。`原稿` は別のフォルダでもよい。

```json
{ "id": "newwork", "title": "…", "logline": "…",
  "cover": "…/表紙.png", "card": "…/リンクカード.png",
  "原稿": "…/原稿", "status": "読み切り",
  "episodes": [ { "no": 1, "title": "…" } ] }
```

トップの作品一覧・作品トップ・各話のビューアは全部ここから生成される。
URLは `/w/<id>/` と `/w/<id>/01/`。**話ごとに固有のURLなので、
「3話から読んで」とリンクを渡せる。**

## 作りの決めごと

- 全部**相対パス**。GitHub Pages はリポジトリ名の下に入るので、
  絶対パスを使うと配置先を変えた瞬間に全部壊れる。
- `og:image` は**PNGのリンクカード**。表紙はwebpで、
  X・Threadsの展開がwebpを拾わないことがある。
- 読んだ位置は `localStorage` に作品・話ごとの鍵で残す（`yomi.<id>.<NN>`）。
  private window では読めないので、読めなくても成立するようにしてある。
