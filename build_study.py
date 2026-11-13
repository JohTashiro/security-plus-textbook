# -*- coding: utf-8 -*-
"""Build memorize-mode + knowledge-map HTML from data/{domain}.json

ID 方針（全体一意・変更禁止の契約）
--------------------------------
- Domain 表示: A / B / C / D / E
- Domain パス: a / b / c / d / e
- Chapter 表示: A-1, A-2, ...
- Chapter slug / ファイル: a-1.html
- Term ID（全体一意）: {chapter_slug}-{key}
  例: a-1-technical
  - 進捗・ブックマーク・マップリンク・小テストの term 参照はすべてこの ID
  - key は章内の短い識別子（technical など）。JSON の term.key に保持
- 公式試験番号（1.1 など）は chapter.official / 表示チップのみ。ID には使わない
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FONT = "https://fonts.googleapis.com/css2?family=M+PLUS+Rounded+1c:wght@400;500;700;800&display=swap"


def asset_version() -> str:
    h = hashlib.sha1()
    for path in sorted([*(ROOT / "css").glob("*.css"), *(ROOT / "js").glob("*.js")]):
        h.update(path.read_bytes())
    return h.hexdigest()[:8]


V = asset_version()

# 描画前に設定クラスを <html> に付けて、答えが一瞬見えるのを防ぐ（キーは js/app.js と共通）
SETTINGS_BOOT = (
    "<script>try{var s=JSON.parse(localStorage.getItem('spt-settings')||'{}'),"
    "c=document.documentElement.classList;if(s.memorize)c.add('memorize');"
    "if(s.dark===true||(s.dark===undefined&&matchMedia('(prefers-color-scheme: dark)').matches))"
    "c.add('dark');}catch(e){}</script>"
)

SETTINGS_NAV = """
  <section class="nav-section settings" aria-label="設定">
    <h2>設定</h2>
    <label class="switch-row">
      <span>覚えるモード<small>答えを隠してタップで表示</small></span>
      <input type="checkbox" role="switch" data-setting="memorize">
      <span class="switch" aria-hidden="true"></span>
    </label>
    <label class="switch-row">
      <span>ダークモード</span>
      <input type="checkbox" role="switch" data-setting="dark">
      <span class="switch" aria-hidden="true"></span>
    </label>
  </section>"""

DOMAINS = [
    {"code": "A", "title": "一般的なセキュリティ概念"},
    {"code": "B", "title": "脅威・脆弱性・緩和"},
    {"code": "C", "title": "セキュリティアーキテクチャ"},
    {"code": "D", "title": "セキュリティ運用"},
    {"code": "E", "title": "セキュリティプログラム管理・監督"},
]
for _d in DOMAINS:
    _slug = _d["code"].lower()
    _d["data_path"] = ROOT / "data" / f"{_slug}.json"
    _d["quiz_path"] = ROOT / "data" / f"{_slug}-quizzes.json"
    _d["out"] = ROOT / _slug
    _d["href"] = f"{_slug}/index.html"
    _d["ready"] = _d["data_path"].exists() and _d["quiz_path"].exists()

CHAPTER_ID_RE = re.compile(r"^[A-E]-[1-9][0-9]*$")
CHAPTER_SLUG_RE = re.compile(r"^[a-e]-[1-9][0-9]*$")
TERM_KEY_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
TERM_ID_RE = re.compile(r"^[a-e]-[1-9][0-9]*-[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")


def load_data(domain: dict) -> tuple[dict, dict]:
    data = json.loads(domain["data_path"].read_text(encoding="utf-8"))
    quizzes = json.loads(domain["quiz_path"].read_text(encoding="utf-8"))
    if data.get("domain") != domain["code"]:
        raise SystemExit(f'{domain["data_path"].name}: domain must be {domain["code"]}')
    return data, quizzes


# 現在ビルド中のドメイン（main() が切り替える）
DATA: dict = {}
QUIZZES: dict = {}


def validate_data(data: dict, quizzes: dict) -> None:
    """Fail the build if IDs are missing, malformed, or not globally unique."""
    errors: list[str] = []
    domain = str(data.get("domain", ""))
    if domain not in "ABCDE":
        errors.append(f'domain must be A-E, got {domain!r}')
    domain_slug = domain.lower()

    term_ids: list[str] = []
    chapter_ids: list[str] = []
    chapter_slugs: list[str] = []

    for ch in data.get("chapters", []):
        ch_id = ch.get("id", "")
        ch_slug = ch.get("slug") or str(ch_id).lower()
        chapter_ids.append(ch_id)
        chapter_slugs.append(ch_slug)

        if not CHAPTER_ID_RE.fullmatch(ch_id):
            errors.append(f"chapter id malformed: {ch_id!r}")
        if not CHAPTER_SLUG_RE.fullmatch(ch_slug):
            errors.append(f"chapter slug malformed: {ch_slug!r}")
        if ch_id.lower() != ch_slug:
            errors.append(f"chapter id/slug mismatch: {ch_id} vs {ch_slug}")
        if not ch_slug.startswith(f"{domain_slug}-"):
            errors.append(f"chapter {ch_id}: slug must start with {domain_slug}-")

        for g in ch.get("groups", []):
            for t in g.get("terms", []):
                tid = t.get("id", "")
                key = t.get("key") or ""
                term_ids.append(tid)
                if not TERM_ID_RE.fullmatch(tid):
                    errors.append(f"term id malformed: {tid!r} ({ch_id})")
                if key and not TERM_KEY_RE.fullmatch(key):
                    errors.append(f"term key malformed: {key!r} ({tid})")
                expected = f"{ch_slug}-{key}" if key else None
                if expected and tid != expected:
                    errors.append(
                        f"term id must be {{chapter_slug}}-{{key}}: "
                        f"got {tid!r}, expected {expected!r}"
                    )
                elif not key and not tid.startswith(f"{ch_slug}-"):
                    errors.append(f"term {tid!r} must start with {ch_slug}-")

    for label, values in (
        ("chapter id", chapter_ids),
        ("chapter slug", chapter_slugs),
        ("term id", term_ids),
    ):
        for name, count in Counter(values).items():
            if count > 1:
                errors.append(f"duplicate {label}: {name!r} x{count}")

    quiz_term_refs: list[str] = []
    known_terms = set(term_ids)
    for ch in data.get("chapters", []):
        ch_id = ch["id"]
        qs = quizzes.get(ch_id)
        if qs is None:
            errors.append(f"quizzes missing chapter key: {ch_id}")
            continue
        chapter_terms = {t["id"] for g in ch["groups"] for t in g["terms"]}
        covered = {q.get("term") for q in qs}
        missing = sorted(chapter_terms - covered)
        if missing:
            errors.append(f"{ch_id}: quiz missing terms: {missing}")
        for q in qs:
            ref = q.get("term", "")
            quiz_term_refs.append(ref)
            if ref not in known_terms:
                errors.append(f"{ch_id}: quiz term unknown: {ref!r}")
            elif ref not in chapter_terms:
                errors.append(f"{ch_id}: quiz term not in this chapter: {ref!r}")

    orphan_quiz_chapters = sorted(set(quizzes) - {c["id"] for c in data.get("chapters", [])})
    for ch_id in orphan_quiz_chapters:
        errors.append(f"quizzes has unknown chapter: {ch_id}")

    if errors:
        msg = "ID validation failed:\n- " + "\n- ".join(errors)
        raise SystemExit(msg)


def esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def rich(text: str) -> str:
    """Escape HTML; **bold** becomes highlight span."""
    parts = re.split(r"(\*\*.+?\*\*)", text)
    out = []
    for part in parts:
        m = re.fullmatch(r"\*\*(.+?)\*\*", part)
        if m:
            out.append(f'<span class="hl">{esc(m.group(1))}</span>')
        else:
            out.append(esc(part))
    return "".join(out)


def slug_of(ch: dict) -> str:
    return ch.get("slug") or str(ch["id"]).lower()


def chapter_href(ch: dict) -> str:
    return f'{slug_of(ch)}.html'


def domain_nav(active: str, *, show_search: bool = True, quiz_anchor: str | None = None) -> str:
    """Sidebar for Domain A pages: chapters + map (+ chapter quiz when on a chapter)."""
    chapter_links = []
    for ch in DATA["chapters"]:
        cls = ' class="active"' if active == ch["id"] else ""
        chapter_links.append(
            f'<a href="{esc(chapter_href(ch))}"{cls}>{esc(ch["id"])} {esc(ch["title"])}</a>'
        )

    extra = ""
    if quiz_anchor:
        extra = f'<a href="{esc(quiz_anchor)}">この章の小テスト</a>'

    map_cls = ' class="active"' if active == "map" else ""
    if active == "hub":
        back = '<a class="nav-back" href="../index.html">← ホーム</a>'
    else:
        back = (
            f'<a class="nav-back" href="index.html">'
            f'← Domain {esc(DATA["domain"])} ハブ</a>'
        )

    search = ""
    if show_search:
        search = """
  <div class="search-wrap">
    <input id="term-search" type="search" placeholder="用語を検索..." autocomplete="off">
  </div>"""

    return f"""
<aside class="sidebar" id="sidebar">
  <a class="brand" href="../index.html">Security+ Textbook<span>Domain {esc(DATA["domain"])}</span></a>
  {back}{search}
  <nav class="nav-section">
    <h2>Domain {esc(DATA["domain"])}</h2>
    {''.join(chapter_links)}
  </nav>
  <nav class="nav-section">
    <h2>ツール</h2>
    {extra}
    <a href="map.html"{map_cls}>Domain {esc(DATA["domain"])} 知識マップ</a>
  </nav>{SETTINGS_NAV}
</aside>
"""


def page(
    title: str,
    active: str,
    body: str,
    *,
    extra_js: str | list[str] = "",
    show_search: bool = True,
    quiz_anchor: str | None = None,
    wide: bool = False,
) -> str:
    scripts = f'<script src="../js/app.js?v={V}"></script>'
    extras = extra_js if isinstance(extra_js, list) else ([extra_js] if extra_js else [])
    for src in extras:
        scripts += f'\n  <script src="{src}?v={V}"></script>'
    main_cls = "main main-wide" if wide else "main"
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)} · Security+ Textbook</title>
  {SETTINGS_BOOT}
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="{FONT}" rel="stylesheet">
  <link rel="stylesheet" href="../css/app.css?v={V}">
</head>
<body>
  <button class="menu-toggle" id="menu-toggle" aria-label="メニュー">☰</button>
  <div class="app">
    {domain_nav(active, show_search=show_search, quiz_anchor=quiz_anchor)}
    <main class="{main_cls}">
      {body}
    </main>
  </div>
  {scripts}
</body>
</html>
"""


def term_card(term: dict) -> str:
    examples = "".join(f"<li>{esc(x)}</li>" for x in term["examples"])
    plain = term["one_liner"].replace("**", "")
    search = " ".join(
        [term["ja"], term.get("en", ""), plain, *term["examples"]]
    ).lower()
    en = f'<span class="en">{esc(term["en"])}</span>' if term.get("en") else ""
    return f"""
<article class="memo-card" id="{esc(term["id"])}" data-search="{esc(search)}">
  <h3>{esc(term["ja"])}{en}</h3>
  <button type="button" class="reveal-btn" aria-expanded="false">答えを見る</button>
  <div class="answer">
    <p class="one-liner">{rich(term["one_liner"])}</p>
    <div class="examples">
      <div class="field-label">代表例</div>
      <ul class="example-list">{examples}</ul>
    </div>
  </div>
</article>
"""


def chapter_page(ch: dict, idx: int) -> str:
    blocks = []
    for group in ch["groups"]:
        cards = "".join(term_card(t) for t in group["terms"])
        blocks.append(
            f'<section class="group"><h2 class="group-title">{esc(group["title"])}</h2>{cards}</section>'
        )

    if idx > 0:
        prev = DATA["chapters"][idx - 1]
        prev_html = (
            f'<a href="{chapter_href(prev)}"><span>前の章</span>'
            f'{esc(prev["id"])} {esc(prev["title"])}</a>'
        )
    else:
        prev_html = (
            f'<a href="index.html"><span>戻る</span>Domain {esc(DATA["domain"])} ハブ</a>'
        )

    if idx < len(DATA["chapters"]) - 1:
        nxt = DATA["chapters"][idx + 1]
        next_html = (
            f'<a class="next" href="{chapter_href(nxt)}"><span>次の章</span>'
            f'{esc(nxt["id"])} {esc(nxt["title"])}</a>'
        )
    else:
        next_html = (
            f'<a class="next" href="index.html"><span>戻る</span>'
            f'Domain {esc(DATA["domain"])} ハブ</a>'
        )

    count = sum(len(g["terms"]) for g in ch["groups"])
    quiz_qs = QUIZZES.get(ch["id"], [])
    quiz_json = json.dumps(quiz_qs, ensure_ascii=False)
    official = ch.get("official")
    official_chip = (
        f'<span class="chip">公式 {esc(official)}</span>' if official else ""
    )
    quiz_block = f"""
<section class="quiz-section" id="quiz-section">
  <header class="quiz-header">
    <p class="eyebrow">小テスト · SY0-701風 4択</p>
    <h2>この章の確認問題</h2>
    <p>本番同様のシナリオ型・用語分類問題です。各用語を最低1回カバーしています（{len(quiz_qs)}問）。</p>
  </header>
  <div id="quiz" class="quiz"></div>
  <script type="application/json" id="quiz-data">{quiz_json}</script>
</section>
"""
    body = f"""
<header class="hero">
  <p class="eyebrow">Domain {esc(DATA["domain"])} · {esc(ch["id"])}</p>
  <h1>{esc(ch["title"])}</h1>
  <p>{esc(ch["blurb"])}</p>
  <div class="meta-row">
    <span class="chip">用語 {count}</span>
    <span class="chip">一言定義 + 代表例</span>
    {official_chip}
  </div>
  <div class="action-row">
    <a class="btn btn-primary" href="#quiz-section">小テスト {len(quiz_qs)}問</a>
    <a class="btn btn-ghost" href="map.html">知識マップ</a>
    <button type="button" class="btn btn-ghost memorize-only" id="reveal-all">すべて表示</button>
  </div>
</header>
<div id="empty-state" class="empty-state">該当する用語がありません</div>
{''.join(blocks)}
{quiz_block}
<nav class="pager">{prev_html}{next_html}</nav>
"""
    return page(
        f'{ch["id"]} {ch["title"]}',
        ch["id"],
        body,
        extra_js=["../js/quiz.js"],
        quiz_anchor="#quiz-section",
    )


def domain_index() -> str:
    cards = []
    total = 0
    for ch in DATA["chapters"]:
        n = sum(len(g["terms"]) for g in ch["groups"])
        total += n
        cards.append(
            f"""<a class="chapter-card" href="{esc(chapter_href(ch))}">
  <div class="code">{esc(ch["id"])}</div>
  <h2>{esc(ch["title"])}</h2>
  <p>{esc(ch["blurb"])} · {n}語</p>
</a>"""
        )
    body = f"""
<header class="hero">
  <p class="eyebrow">CompTIA Security+ SY0-701 · Domain {esc(DATA["domain"])}</p>
  <h1>Domain {esc(DATA["domain"])}<br>{esc(DATA["title"])}</h1>
  <p>{esc(DATA.get("intro") or "章を選んで覚える。関係性は Domain 知識マップで確認。")}</p>
  <div class="meta-row">
    <span class="chip">用語 {total}</span>
    <span class="chip">公式 Domain {esc(str(DATA.get("official", "1")))}</span>
  </div>
  <div class="action-row">
    <a class="btn btn-ghost" href="map.html">Domain {esc(DATA["domain"])} 知識マップ</a>
  </div>
</header>
<section class="chapter-grid">{''.join(cards)}</section>
"""
    # Hub: no chapter highlighted; search still useful for jumping via sidebar chapters
    return page(
        f'Domain {DATA["domain"]} {DATA["title"]}',
        "hub",
        body,
        show_search=False,
    )


def map_page() -> str:
    payload = json.dumps(DATA, ensure_ascii=False)
    body = f"""
<header class="hero">
  <p class="eyebrow">Domain {esc(DATA["domain"])}</p>
  <h1>知識マップ</h1>
  <p>用語だけを階層表示。同じカテゴリは同じ階層。タップすると意味と教科書リンクが出ます。</p>
</header>
<div class="mindmap-wrap">
  <div id="mindmap" class="mindmap"></div>
</div>
<aside class="term-panel" id="term-panel" aria-hidden="true">
  <button type="button" class="term-panel-close" id="term-panel-close" aria-label="閉じる">×</button>
  <p class="term-panel-kicker">意味</p>
  <h2 id="term-panel-title"></h2>
  <button type="button" class="reveal-btn" id="term-panel-reveal" aria-expanded="false">答えを見る</button>
  <p class="term-panel-meaning" id="term-panel-meaning"></p>
  <a class="term-panel-link" id="term-panel-link" href="#">教科書で見る</a>
</aside>
<script type="application/json" id="mindmap-data">{payload}</script>
"""
    return page(
        f'Domain {DATA["domain"]} 知識マップ',
        "map",
        body,
        extra_js="../js/map.js",
        show_search=False,
        wide=True,
    )


def root_sidebar(*, map_active: bool = False) -> str:
    nav_links = []
    for d in DOMAINS:
        if d["ready"]:
            nav_links.append(
                f'<a href="{esc(d["href"])}">{esc(d["code"])}. {esc(d["title"])}</a>'
            )
        else:
            nav_links.append(
                f'<a href="#" class="nav-disabled" aria-disabled="true">{esc(d["code"])}. {esc(d["title"])}（準備中）</a>'
            )
    map_cls = ' class="active"' if map_active else ""
    return f"""
<aside class="sidebar" id="sidebar">
  <a class="brand" href="index.html">Security+ Textbook<span>SY0-701</span></a>
  <nav class="nav-section">
    <h2>Domains</h2>
    {''.join(nav_links)}
  </nav>
  <nav class="nav-section">
    <h2>マップ</h2>
    <a href="map.html"{map_cls}>全体の知識マップ</a>
  </nav>{SETTINGS_NAV}
</aside>"""


def root_index(term_counts: dict[str, int]) -> str:
    cards = []
    for d in DOMAINS:
        if d["ready"]:
            cards.append(
                f"""<a class="chapter-card" href="{esc(d["href"])}">
  <div class="code">DOMAIN {esc(d["code"])}</div>
  <h2>{esc(d["title"])}</h2>
  <p>章一覧 · 覚えるモード · 知識マップ · 用語 {term_counts[d["code"]]}</p>
</a>"""
            )
        else:
            cards.append(
                f"""<div class="chapter-card is-disabled" aria-disabled="true">
  <div class="code">DOMAIN {esc(d["code"])}</div>
  <h2>{esc(d["title"])}</h2>
  <p>準備中</p>
</div>"""
            )

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Security+ Textbook</title>
  {SETTINGS_BOOT}
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="{FONT}" rel="stylesheet">
  <link rel="stylesheet" href="css/app.css?v={V}">
</head>
<body>
  <button class="menu-toggle" id="menu-toggle" aria-label="メニュー">☰</button>
  <div class="app">
    {root_sidebar()}
    <main class="main">
      <header class="hero">
        <p class="eyebrow">Personal Study App</p>
        <h1>Security+ 教科書</h1>
        <p>Domain を選んで、覚えるモードと知識マップで定着させる。</p>
        <div class="action-row">
          <a class="btn btn-ghost" href="map.html">全体の知識マップ</a>
        </div>
      </header>
      <section class="chapter-grid">
        {''.join(cards)}
      </section>
    </main>
  </div>
  <script src="js/app.js?v={V}"></script>
</body>
</html>
"""


def global_map_page(hub_domains: list[dict]) -> str:
    payload = json.dumps(
        {"root": "SY0-701", "domains": hub_domains},
        ensure_ascii=False,
    )
    total_terms = sum(int(d.get("terms", 0)) for d in hub_domains)
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>全体の知識マップ · Security+ Textbook</title>
  {SETTINGS_BOOT}
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="{FONT}" rel="stylesheet">
  <link rel="stylesheet" href="css/app.css?v={V}">
</head>
<body>
  <button class="menu-toggle" id="menu-toggle" aria-label="メニュー">☰</button>
  <div class="app">
    {root_sidebar(map_active=True)}
    <main class="main main-wide">
      <header class="hero">
        <p class="eyebrow">SY0-701 · 全体</p>
        <h1>知識マップ</h1>
        <p>Domain を選ぶと、その Domain の用語マップへ進みます。章ラベルは各章の覚えるモードへリンクします（用語 {total_terms}）。</p>
      </header>
      <div class="mindmap-wrap">
        <div id="mindmap" class="mindmap"></div>
      </div>
      <script type="application/json" id="hubmap-data">{payload}</script>
    </main>
  </div>
  <script src="js/app.js?v={V}"></script>
  <script src="js/hub-map.js?v={V}"></script>
</body>
</html>
"""


def main() -> None:
    global DATA, QUIZZES
    ready = [d for d in DOMAINS if d["ready"]]
    loaded = []
    seen_ids: Counter[str] = Counter()
    for d in ready:
        data, quizzes = load_data(d)
        validate_data(data, quizzes)
        seen_ids.update(t["id"] for ch in data["chapters"] for g in ch["groups"] for t in g["terms"])
        loaded.append((d, data, quizzes))
    dupes = sorted(i for i, n in seen_ids.items() if n > 1)
    if dupes:
        raise SystemExit(f"term id duplicated across domains: {dupes}")
    print(f"validated: {len(seen_ids)} unique term ids across {len(ready)} domain(s)")

    term_counts: dict[str, int] = {}
    hub_domains: list[dict] = []
    for d, data, quizzes in loaded:
        DATA, QUIZZES = data, quizzes
        out: Path = d["out"]
        if out.exists():
            shutil.rmtree(out)
        out.mkdir(parents=True, exist_ok=True)

        (out / "index.html").write_text(domain_index(), encoding="utf-8")
        (out / "map.html").write_text(map_page(), encoding="utf-8")
        total = 0
        chapter_summaries = []
        for i, ch in enumerate(DATA["chapters"]):
            path = out / f"{slug_of(ch)}.html"
            path.write_text(chapter_page(ch, i), encoding="utf-8")
            n = sum(len(g["terms"]) for g in ch["groups"])
            total += n
            chapter_summaries.append(
                {
                    "id": ch["id"],
                    "slug": slug_of(ch),
                    "title": ch["title"],
                    "terms": n,
                }
            )
            print(f"wrote {out.name}/{path.name}: {n} terms")
        term_counts[d["code"]] = total
        hub_domains.append(
            {
                "code": d["code"],
                "title": data.get("title") or d["title"],
                "terms": total,
                "map": f'{d["code"].lower()}/map.html',
                "href": d["href"],
                "chapters": chapter_summaries,
            }
        )

    (ROOT / "index.html").write_text(root_index(term_counts), encoding="utf-8")
    (ROOT / "map.html").write_text(global_map_page(hub_domains), encoding="utf-8")
    print("wrote map.html (global hub)")

    legacy = ROOT / "domain1"
    if legacy.exists():
        shutil.rmtree(legacy)
        print("removed domain1/")

    print("done → " + ", ".join(f"{d['out'].name}/" for d in ready))


if __name__ == "__main__":
    main()
