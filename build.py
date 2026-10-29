#!/usr/bin/env python3
"""作品.json とページ画像から、公開用の静的サイトを組み立てる。

**増やすときに触るのは 作品.json と画像だけ**にしてある。
話を足す → 原稿/NN話/ページ/ に組んだPNGを置いて 作品.json に1行、
作品を足す → 作品.json に1ブロック。どちらも build.py は書き換えない。

ページ数はJSONに書かず**画像の実数から数える**。書き写すと必ずずれるため。
"""
import json, shutil, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
OUT  = HERE / "docs"       # GitHub Pages は main の /docs をそのまま配れる
WEB_W, WEB_Q = 1240, 86        # 画面で読むのに足りる幅。線画はこの辺で網点が潰れない

def webp(src: Path, dst: Path, width=WEB_W):
    if dst.exists() and dst.stat().st_mtime > src.stat().st_mtime:
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    im = Image.open(src)
    im = im.convert("L") if im.mode != "L" else im      # 白黒原稿なので階調は1本で足りる
    if im.width != width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im.save(dst, "WEBP", quality=WEB_Q, method=6)

def icon(dst: Path):
    """タブの印。16pxまで落ちるので字1文字——絵を縮めると何も読めなくなる。"""
    if dst.exists(): return
    o = subprocess.run(["find", "/System/Library/AssetsV2", "/System/Library/Fonts",
                        "/Library/Fonts", str(Path.home()/"Library/Fonts"),
                        "-iname", "ShipporiMincho-Regular.otf"],
                       capture_output=True, text=True).stdout.strip().split("\n")[0]
    im = Image.new("RGB", (192, 192), (17, 18, 22))
    ImageDraw.Draw(im).text((96, 100), "鳥", font=ImageFont.truetype(o, 150),
                            fill=(222, 218, 210), anchor="mm")
    im.save(dst)

def esc(s): return (s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
                     .replace('"',"&quot;"))

def head(title, desc, up, og_img, og_url, kind="website"):
    """up は公開ルートへの相対（"" / "../../" など）。
    GitHub Pages はリポジトリ名の下に入るので、絶対パスを使うと全部壊れる。"""
    return f"""<!doctype html>
<html lang="ja">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta property="og:type" content="{kind}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:image" content="{esc(og_img)}">
<meta property="og:url" content="{esc(og_url)}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{up}a/icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Shippori+Mincho+B1:wght@600;800&family=Zen+Kaku+Gothic+New:wght@400;500;700&display=swap">
<link rel="stylesheet" href="{up}a/site.css">
"""

def bar(up, home, right=""):
    return (f'<header class="bar"><div class="wrap">'
            f'<a class="home" href="{up}">{esc(home)}</a>'
            f'<span class="spacer"></span>{right}</div>'
            f'<div class="rail"><span id="rail"></span></div></header>\n')

def foot(up, site):
    return (f'<footer class="wrap"><p>{esc(site["name"])} — {esc(site["tagline"])}</p>'
            f'<p><a href="{up}">作品の一覧へ</a></p></footer>\n')

def main():
    cfg  = json.loads((HERE / "作品.json").read_text(encoding="utf-8"))
    site = cfg["site"]
    base = site["base"].rstrip("/") + "/"

    if OUT.exists(): shutil.rmtree(OUT / "w", ignore_errors=True)
    OUT.mkdir(exist_ok=True)
    (OUT / ".nojekyll").write_text("")
    (OUT / "a").mkdir(exist_ok=True)
    for f in ("site.css", "reader.js"):
        shutil.copy(HERE / "部品" / f, OUT / "a" / f)
    icon(OUT / "a" / "icon.png")

    cards = []
    for w in cfg["works"]:
        wid, genko = w["id"], Path(w["原稿"]).expanduser()
        webp(Path(w["cover"]).expanduser(), OUT / "img" / wid / "cover.webp", 1400)
        cover_rel = f"img/{wid}/cover.webp"
        card_rel = cover_rel
        if w.get("card"):                      # SNSの展開用。webpだと出ない先がある
            dst = OUT / "img" / wid / "card.png"
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(Path(w["card"]).expanduser(), dst)
            card_rel = f"img/{wid}/card.png"

        # ── 各話を書き出す。ページが無い話は「準備中」として一覧にだけ出す ──
        eps = []
        for e in w["episodes"]:
            nn   = f"{e['no']:02d}"
            srcs = sorted((genko / f"{nn}話" / "ページ").glob("p*.png"))
            for i, p in enumerate(srcs, 1):
                webp(p, OUT / "img" / wid / nn / f"p{i:02d}.webp")
            eps.append({**e, "nn": nn, "pages": len(srcs)})

        live = [e for e in eps if e["pages"]]
        for idx, e in enumerate(live):
            nn, n = e["nn"], e["pages"]
            up    = "../../../"
            d     = OUT / "w" / wid / nn
            d.mkdir(parents=True, exist_ok=True)
            title = f'{w["title"]} 第{e["no"]}話「{e["title"]}」'
            url   = f'{base}w/{wid}/{nn}/'
            figs  = "\n".join(
                f'<figure class="page" id="p{i:02d}" data-n="{i}">'
                f'<img src="{up}img/{wid}/{nn}/p{i:02d}.webp" width="1240" height="1753" '
                f'alt="第{e["no"]}話 {i}ページ目" loading="{"eager" if i<=2 else "lazy"}" '
                f'decoding="async"><figcaption>{i:02d} / {n}</figcaption></figure>'
                for i in range(1, n + 1))
            nav = []
            if idx + 1 < len(live):
                nx = live[idx + 1]
                nav.append(f'<a class="btn" href="../{nx["nn"]}/">次の話へ　第{nx["no"]}話</a>')
            if idx > 0:
                pv = live[idx - 1]
                nav.append(f'<a class="btn ghost" href="../{pv["nn"]}/">第{pv["no"]}話に戻る</a>')
            nav.append(f'<a class="btn ghost" href="../">話の一覧</a>')

            (d / "index.html").write_text(
                head(title, w["logline"], up, base + card_rel, url, "article")
                + bar(up, site["name"],
                      f'<p class="counter">第{e["no"]}話 <b id="cur">—</b> / {n}</p>')
                + f'''<main class="wrap">
<section class="hero" style="padding-block:24px 0">
  <p class="eyebrow">{esc(w["title"])}　第{e["no"]}話</p>
  <h1 style="font-size:clamp(24px,7vw,34px)">{esc(e["title"])}</h1>
  <div class="howto"><span class="arrow">←</span>
  <span>右開きです。コマもセリフも<b>右から左へ</b>読みます。全{n}ページ、下に続けて並べてあります。</span></div>
</section>
<section class="pages" id="pages" data-key="{wid}.{nn}" data-total="{n}">
{figs}
</section>
<section class="end">
  <p class="mark">第{e["no"]}話 了</p>
  <p class="n">{n}ページ</p>
  <div class="nav">{"".join(nav)}</div>
</section>
</main>
<div class="resume" id="resumeBar" hidden><button class="btn" id="resumeBtn" type="button"></button></div>
<script src="{up}a/reader.js"></script>
''' + foot(up, site), encoding="utf-8")

        # ── 作品トップ ──
        up = "../../"
        rows = []
        for e in eps:
            if e["pages"]:
                rows.append(f'<li><a href="{e["nn"]}/"><span class="no">{e["nn"]}</span>'
                            f'<span class="ttl">{esc(e["title"])}</span>'
                            f'<span class="st">全{e["pages"]}ページ</span></a></li>')
            else:
                rows.append(f'<li><div class="soon"><span class="no">{e["nn"]}</span>'
                            f'<span class="ttl">{esc(e["title"])}</span>'
                            f'<span class="st">{esc(e.get("状態","準備中"))}</span></div></li>')
        first = live[0]["nn"] if live else None
        (OUT / "w" / wid).mkdir(parents=True, exist_ok=True)
        (OUT / "w" / wid / "index.html").write_text(
            head(w["title"], w["logline"], up, base + card_rel, f"{base}w/{wid}/")
            + bar(up, site["name"])
            + f'''<main class="wrap">
<section class="hero">
  <figure><img src="{up}{cover_rel}" width="1400" height="788"
    alt="『{esc(w["title"])}』表紙" fetchpriority="high"></figure>
  <p class="eyebrow" style="margin-top:24px">{esc(w.get("ruby",""))}　{esc(w["status"])}</p>
  <h1>{esc(w["title"])}</h1>
  <p class="logline">{esc(w["logline"])}</p>
  <p class="about">{esc(w.get("about",""))}</p>
  <div class="cta">
    {f'<a class="btn" href="{first}/">第1話を読む</a>' if first else ''}
    <a class="btn ghost" href="#eps">話の一覧</a>
  </div>
</section>
<section id="eps" style="padding-block:40px 56px">
  <p class="eyebrow">話の一覧</p>
  <ul class="eps">{"".join(rows)}</ul>
</section>
</main>
''' + foot(up, site), encoding="utf-8")

        n_live = sum(e["pages"] for e in live)
        cards.append(f'''<a class="card" href="w/{wid}/">
  <img src="{cover_rel}" width="1400" height="788" alt="『{esc(w["title"])}』表紙">
  <div><p class="meta">{esc(w["status"])}　{len(live)}話公開中　全{n_live}ページ</p>
  <h2>{esc(w["title"])}</h2><p class="l">{esc(w["logline"])}</p></div></a>''')

    # ── トップ（作品の棚）──
    first_cover = f'img/{cfg["works"][0]["id"]}/card.png'
    (OUT / "index.html").write_text(
        head(site["name"], site["tagline"], "", base + first_cover, base)
        + bar("", site["name"])
        + f'''<main class="wrap">
<section style="padding-block:34px 0">
  <h1 style="font-size:clamp(26px,7vw,36px)">{esc(site["name"])}</h1>
  <p class="logline" style="color:var(--dim);margin-top:12px">{esc(site["tagline"])}</p>
</section>
<section class="shelf">{"".join(cards)}</section>
</main>
''' + foot("", site), encoding="utf-8")

    n = len(list(OUT.rglob("*.html")))
    print(f"OK  {OUT}  HTML {n}枚  画像 {len(list((OUT/'img').rglob('*.webp')))}枚")

if __name__ == "__main__":
    sys.exit(main())
