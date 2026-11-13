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
    "c.add('dark');if(s.lang==='en')c.add('lang-en');if(s.lang==='es')c.add('lang-es');"
    "}catch(e){}</script>"
)


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


def i18n(ja: str, en: str, es: str) -> str:
    """Three parallel plain-text spans; CSS shows only the active language."""
    return (
        f'<span data-i18n="ja">{esc(ja)}</span>'
        f'<span data-i18n="en">{esc(en)}</span>'
        f'<span data-i18n="es">{esc(es)}</span>'
    )


def i18n_rich(ja: str, en: str, es: str, tag: str = "span", attrs: str = "") -> str:
    """Like i18n() but runs each variant through rich() (markdown-ish **bold**)."""
    out = []
    for key, text in (("ja", ja), ("en", en), ("es", es)):
        out.append(f'<{tag} data-i18n="{key}"{attrs}>{rich(text)}</{tag}>')
    return "".join(out)


# UI chrome strings shared across templates: key -> (ja, en, es)
UI = {
    "show_answer": ("答えを見る", "Show answer", "Ver respuesta"),
    "examples": ("代表例", "Examples", "Ejemplos"),
    "settings": ("設定", "Settings", "Ajustes"),
    "memorize_mode": ("覚えるモード", "Memorize mode", "Modo memorización"),
    "memorize_hint": ("答えを隠してタップで表示", "Hide answers, tap to reveal", "Oculta las respuestas, toca para verlas"),
    "dark_mode": ("ダークモード", "Dark mode", "Modo oscuro"),
    "language": ("言語", "Language", "Idioma"),
    "search_placeholder": ("用語を検索...", "Search terms...", "Buscar términos..."),
    "tools": ("ツール", "Tools", "Herramientas"),
    "chapter_quiz": ("この章の小テスト", "This chapter's quiz", "Cuestionario de este capítulo"),
    "domain_map": ("知識マップ", "Knowledge map", "Mapa de conocimiento"),
    "back_home": ("← ホーム", "← Home", "← Inicio"),
    "back_hub": ("← Domain {d} ハブ", "← Domain {d} hub", "← Hub del Domain {d}"),
    "hub": ("ハブ", "hub", "hub"),
    "terms_count": ("用語 {n}", "{n} terms", "{n} términos"),
    "official_chip": ("公式 {n}", "Official {n}", "Oficial {n}"),
    "quiz_eyebrow": ("小テスト · SY0-701風 4択", "Quiz · SY0-701 style, 4 choices", "Cuestionario · estilo SY0-701, 4 opciones"),
    "quiz_heading": ("この章の確認問題", "Chapter review questions", "Preguntas de repaso del capítulo"),
    "quiz_intro": (
        "本番同様のシナリオ型・用語分類問題です。各用語を最低1回カバーしています（{n}問）。",
        "Scenario-based questions in the style of the real exam, covering every term at least once ({n} questions).",
        "Preguntas basadas en escenarios al estilo del examen real; cada término se cubre al menos una vez ({n} preguntas).",
    ),
    "quiz_button": ("小テスト {n}問", "Quiz ({n})", "Cuestionario ({n})"),
    "show_all": ("すべて表示", "Show all", "Mostrar todo"),
    "hide_all": ("すべて隠す", "Hide all", "Ocultar todo"),
    "no_terms": ("該当する用語がありません", "No matching terms", "No se encontraron términos"),
    "one_liner_chip": ("一言定義 + 代表例", "One-line definition + examples", "Definición breve + ejemplos"),
    "prev_chapter": ("前の章", "Previous chapter", "Capítulo anterior"),
    "next_chapter": ("次の章", "Next chapter", "Siguiente capítulo"),
    "back": ("戻る", "Back", "Volver"),
    "chapters_count": ("章一覧 · 覚えるモード · 知識マップ · 用語 {n}", "Chapters · memorize mode · knowledge map · {n} terms", "Capítulos · modo memorización · mapa de conocimiento · {n} términos"),
    "domains_nav": ("Domains", "Domains", "Domains"),
    "map_nav": ("マップ", "Map", "Mapa"),
    "full_map": ("全体の知識マップ", "Full knowledge map", "Mapa de conocimiento completo"),
    "home_title": ("Security+ 教科書", "Security+ Textbook", "Manual de Security+"),
    "home_tagline": (
        "Domain を選んで、覚えるモードと知識マップで定着させる。",
        "Pick a domain, then lock it in with memorize mode and the knowledge map.",
        "Elige un dominio y refuérzalo con el modo memorización y el mapa de conocimiento.",
    ),
    "global_map_title": ("知識マップ", "Knowledge map", "Mapa de conocimiento"),
    "overview": ("全体", "Overview", "Visión general"),
    "global_map_tagline": (
        "Domain を選ぶと、その Domain の用語マップへ進みます。章ラベルは各章の覚えるモードへリンクします（用語 {n}）。",
        "Pick a domain to open its term map. Chapter labels link to that chapter's memorize mode ({n} terms).",
        "Elige un dominio para abrir su mapa de términos. Las etiquetas de capítulo enlazan al modo memorización de ese capítulo ({n} términos).",
    ),
    "domain_hero_fallback": (
        "章を選んで覚える。関係性は Domain 知識マップで確認。",
        "Pick a chapter to study. Check relationships in the Domain knowledge map.",
        "Elige un capítulo para estudiar. Revisa las relaciones en el mapa de conocimiento del Domain.",
    ),
    "domain_map_tagline": (
        "用語だけを階層表示。同じカテゴリは同じ階層。タップすると意味と教科書リンクが出ます。",
        "Terms shown as a hierarchy; same category, same level. Tap one to see its meaning and a link to the textbook.",
        "Términos mostrados como jerarquía; misma categoría, mismo nivel. Toca uno para ver su significado y un enlace al manual.",
    ),
    "panel_meaning": ("意味", "Meaning", "Significado"),
    "panel_close": ("閉じる", "Close", "Cerrar"),
    "panel_link": ("教科書で見る（{ch}）", "View in textbook ({ch})", "Ver en el manual ({ch})"),
    "all_correct": ("全問正解！", "All correct!", "¡Todo correcto!"),
    "retry": ("復習して再挑戦しよう", "Review and try again", "Repasa e inténtalo de nuevo"),
    "quiz_score": ("正解", "Score", "Aciertos"),
    "prep": ("準備中", "Coming soon", "Próximamente"),
}


def t(key: str, **kwargs) -> str:
    ja, en, es = UI[key]
    if kwargs:
        ja, en, es = ja.format(**kwargs), en.format(**kwargs), es.format(**kwargs)
    return i18n(ja, en, es)


SETTINGS_NAV = f"""
  <section class="nav-section settings" aria-label="設定">
    <h2>{t("settings")}</h2>
    <label class="switch-row">
      <span>{t("memorize_mode")}<small>{t("memorize_hint")}</small></span>
      <input type="checkbox" role="switch" data-setting="memorize">
      <span class="switch" aria-hidden="true"></span>
    </label>
    <label class="switch-row">
      <span>{t("dark_mode")}</span>
      <input type="checkbox" role="switch" data-setting="dark">
      <span class="switch" aria-hidden="true"></span>
    </label>
    <div class="lang-row" role="group" aria-label="{UI['language'][0]} / {UI['language'][1]} / {UI['language'][2]}">
      <button type="button" class="lang-btn" data-lang-btn="ja">日本語</button>
      <button type="button" class="lang-btn" data-lang-btn="en">EN</button>
      <button type="button" class="lang-btn" data-lang-btn="es">ES</button>
    </div>
  </section>"""

DOMAINS = [
    {
        "code": "A",
        "title": "一般的なセキュリティ概念",
        "title_en": "General Security Concepts",
        "title_es": "Conceptos generales de seguridad",
    },
    {
        "code": "B",
        "title": "脅威・脆弱性・緩和",
        "title_en": "Threats, Vulnerabilities & Mitigations",
        "title_es": "Amenazas, vulnerabilidades y mitigaciones",
    },
    {
        "code": "C",
        "title": "セキュリティアーキテクチャ",
        "title_en": "Security Architecture",
        "title_es": "Arquitectura de seguridad",
    },
    {
        "code": "D",
        "title": "セキュリティ運用",
        "title_en": "Security Operations",
        "title_es": "Operaciones de seguridad",
    },
    {
        "code": "E",
        "title": "セキュリティプログラム管理・監督",
        "title_en": "Security Program Management & Oversight",
        "title_es": "Gestión y supervisión del programa de seguridad",
    },
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


def slug_of(ch: dict) -> str:
    return ch.get("slug") or str(ch["id"]).lower()


def chapter_href(ch: dict) -> str:
    return f'{slug_of(ch)}.html'


def domain_nav(active: str, *, show_search: bool = True, quiz_anchor: str | None = None) -> str:
    """Sidebar for Domain A pages: chapters + map (+ chapter quiz when on a chapter)."""
    chapter_links = []
    for ch in DATA["chapters"]:
        cls = ' class="active"' if active == ch["id"] else ""
        title = i18n(ch["title"], ch.get("title_en") or ch["title"], ch.get("title_es") or ch["title"])
        chapter_links.append(
            f'<a href="{esc(chapter_href(ch))}"{cls}>{esc(ch["id"])} {title}</a>'
        )

    extra = ""
    if quiz_anchor:
        extra = f'<a href="{esc(quiz_anchor)}">{t("chapter_quiz")}</a>'

    map_cls = ' class="active"' if active == "map" else ""
    if active == "hub":
        back = f'<a class="nav-back" href="../index.html">{t("back_home")}</a>'
    else:
        back = f'<a class="nav-back" href="index.html">{t("back_hub", d=esc(DATA["domain"]))}</a>'

    search = ""
    if show_search:
        ph_ja, ph_en, ph_es = UI["search_placeholder"]
        search = f"""
  <div class="search-wrap">
    <input id="term-search" type="search" placeholder="{esc(ph_ja)}" autocomplete="off"
      data-ph-ja="{esc(ph_ja)}" data-ph-en="{esc(ph_en)}" data-ph-es="{esc(ph_es)}">
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
    <h2>{t("tools")}</h2>
    {extra}
    <a href="map.html"{map_cls}>Domain {esc(DATA["domain"])} {t("domain_map")}</a>
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
  <link rel="icon" type="image/svg+xml" href="../favicon.svg">
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
    examples_ja = "".join(f"<li>{esc(x)}</li>" for x in term["examples"])
    examples_en = "".join(f"<li>{esc(x)}</li>" for x in term.get("examples_en", [])) or examples_ja
    examples_es = "".join(f"<li>{esc(x)}</li>" for x in term.get("examples_es", [])) or examples_ja
    plain = term["one_liner"].replace("**", "")
    search = " ".join(
        [term["ja"], term.get("en", ""), term.get("es", ""), plain, *term["examples"]]
    ).lower()
    en_sub = f'<span class="en">{esc(term["en"])}</span>' if term.get("en") else ""
    name_en = esc(term.get("name_en") or term.get("en") or term["ja"])
    name_es = esc(term.get("es") or term["ja"])
    one_liner_en = term.get("one_liner_en") or term["one_liner"]
    one_liner_es = term.get("one_liner_es") or term["one_liner"]
    return f"""
<article class="memo-card" id="{esc(term["id"])}" data-search="{esc(search)}">
  <h3>
    <span data-i18n="ja">{esc(term["ja"])}{en_sub}</span>
    <span data-i18n="en">{name_en}</span>
    <span data-i18n="es">{name_es}</span>
  </h3>
  <button type="button" class="reveal-btn" aria-expanded="false">{t("show_answer")}</button>
  <div class="answer">
    {i18n_rich(term["one_liner"], one_liner_en, one_liner_es, tag="p", attrs=' class="one-liner"')}
    <div class="examples">
      <div class="field-label">{t("examples")}</div>
      <ul class="example-list" data-i18n="ja">{examples_ja}</ul>
      <ul class="example-list" data-i18n="en">{examples_en}</ul>
      <ul class="example-list" data-i18n="es">{examples_es}</ul>
    </div>
  </div>
</article>
"""


def chapter_page(ch: dict, idx: int) -> str:
    blocks = []
    for group in ch["groups"]:
        cards = "".join(term_card(t) for t in group["terms"])
        g_title = i18n(group["title"], group.get("title_en") or group["title"], group.get("title_es") or group["title"])
        blocks.append(
            f'<section class="group"><h2 class="group-title">{g_title}</h2>{cards}</section>'
        )

    def ch_title(c: dict) -> str:
        return i18n(c["title"], c.get("title_en") or c["title"], c.get("title_es") or c["title"])

    if idx > 0:
        prev = DATA["chapters"][idx - 1]
        prev_html = (
            f'<a href="{chapter_href(prev)}"><span>{t("prev_chapter")}</span>'
            f'<span>{esc(prev["id"])} {ch_title(prev)}</span></a>'
        )
    else:
        prev_html = (
            f'<a href="index.html"><span>{t("back")}</span>'
            f'<span>Domain {esc(DATA["domain"])} {t("hub")}</span></a>'
        )

    if idx < len(DATA["chapters"]) - 1:
        nxt = DATA["chapters"][idx + 1]
        next_html = (
            f'<a class="next" href="{chapter_href(nxt)}"><span>{t("next_chapter")}</span>'
            f'<span>{esc(nxt["id"])} {ch_title(nxt)}</span></a>'
        )
    else:
        next_html = (
            f'<a class="next" href="index.html"><span>{t("back")}</span>'
            f'<span>Domain {esc(DATA["domain"])} {t("hub")}</span></a>'
        )

    count = sum(len(g["terms"]) for g in ch["groups"])
    quiz_qs = QUIZZES.get(ch["id"], [])
    quiz_json = json.dumps(quiz_qs, ensure_ascii=False)
    official = ch.get("official")
    official_chip = (
        f'<span class="chip">{t("official_chip", n=esc(official))}</span>' if official else ""
    )
    quiz_block = f"""
<section class="quiz-section" id="quiz-section">
  <header class="quiz-header">
    <p class="eyebrow">{t("quiz_eyebrow")}</p>
    <h2>{t("quiz_heading")}</h2>
    <p>{t("quiz_intro", n=len(quiz_qs))}</p>
  </header>
  <div id="quiz" class="quiz"></div>
  <script type="application/json" id="quiz-data">{quiz_json}</script>
</section>
"""
    body = f"""
<header class="hero">
  <p class="eyebrow">Domain {esc(DATA["domain"])} · {esc(ch["id"])}</p>
  <h1>{ch_title(ch)}</h1>
  <p data-i18n="ja">{esc(ch["blurb"])}</p>
  <p data-i18n="en">{esc(ch.get("blurb_en") or ch["blurb"])}</p>
  <p data-i18n="es">{esc(ch.get("blurb_es") or ch["blurb"])}</p>
  <div class="meta-row">
    <span class="chip">{t("terms_count", n=count)}</span>
    <span class="chip">{t("one_liner_chip")}</span>
    {official_chip}
  </div>
  <div class="action-row">
    <a class="btn btn-primary" href="#quiz-section">{t("quiz_button", n=len(quiz_qs))}</a>
    <a class="btn btn-ghost" href="map.html">{t("domain_map")}</a>
    <button type="button" class="btn btn-ghost memorize-only" id="reveal-all"
      data-show-all-ja="{UI['show_all'][0]}" data-show-all-en="{UI['show_all'][1]}" data-show-all-es="{UI['show_all'][2]}"
      data-hide-all-ja="{UI['hide_all'][0]}" data-hide-all-en="{UI['hide_all'][1]}" data-hide-all-es="{UI['hide_all'][2]}"
    >{t("show_all")}</button>
  </div>
</header>
<div id="empty-state" class="empty-state">{t("no_terms")}</div>
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
        title = i18n(ch["title"], ch.get("title_en") or ch["title"], ch.get("title_es") or ch["title"])
        blurb_ja = f'{esc(ch["blurb"])} · {n}語'
        blurb_en = f'{esc(ch.get("blurb_en") or ch["blurb"])} · {n} terms'
        blurb_es = f'{esc(ch.get("blurb_es") or ch["blurb"])} · {n} términos'
        cards.append(
            f"""<a class="chapter-card" href="{esc(chapter_href(ch))}">
  <div class="code">{esc(ch["id"])}</div>
  <h2>{title}</h2>
  <p data-i18n="ja">{blurb_ja}</p>
  <p data-i18n="en">{blurb_en}</p>
  <p data-i18n="es">{blurb_es}</p>
</a>"""
        )
    domain_title = i18n(DATA["title"], DATA.get("title_en") or DATA["title"], DATA.get("title_es") or DATA["title"])
    intro_ja = DATA.get("intro") or UI["domain_hero_fallback"][0]
    intro_en = DATA.get("intro_en") or UI["domain_hero_fallback"][1]
    intro_es = DATA.get("intro_es") or UI["domain_hero_fallback"][2]
    body = f"""
<header class="hero">
  <p class="eyebrow">CompTIA Security+ SY0-701 · Domain {esc(DATA["domain"])}</p>
  <h1>Domain {esc(DATA["domain"])}<br>{domain_title}</h1>
  {i18n_rich(intro_ja, intro_en, intro_es, tag="p")}
  <div class="meta-row">
    <span class="chip">{t("terms_count", n=total)}</span>
    <span class="chip">{t("official_chip", n=f'Domain {esc(str(DATA.get("official", "1")))}')}</span>
  </div>
  <div class="action-row">
    <a class="btn btn-ghost" href="map.html">Domain {esc(DATA["domain"])} {t("domain_map")}</a>
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
  <h1>{t("global_map_title")}</h1>
  <p>{t("domain_map_tagline")}</p>
</header>
<div class="mindmap-wrap">
  <div id="mindmap" class="mindmap"></div>
</div>
<aside class="term-panel" id="term-panel" aria-hidden="true">
  <button type="button" class="term-panel-close" id="term-panel-close" aria-label="{UI['panel_close'][0]}">×</button>
  <p class="term-panel-kicker">{t("panel_meaning")}</p>
  <h2 id="term-panel-title"></h2>
  <button type="button" class="reveal-btn" id="term-panel-reveal" aria-expanded="false">{t("show_answer")}</button>
  <p class="term-panel-meaning" id="term-panel-meaning"></p>
  <a class="term-panel-link" id="term-panel-link" href="#"></a>
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
        title = i18n(d["title"], d.get("title_en") or d["title"], d.get("title_es") or d["title"])
        if d["ready"]:
            nav_links.append(
                f'<a href="{esc(d["href"])}">{esc(d["code"])}. {title}</a>'
            )
        else:
            nav_links.append(
                f'<a href="#" class="nav-disabled" aria-disabled="true">{esc(d["code"])}. {title}'
                f'（{t("prep")}）</a>'
            )
    map_cls = ' class="active"' if map_active else ""
    return f"""
<aside class="sidebar" id="sidebar">
  <a class="brand" href="index.html">Security+ Textbook<span>SY0-701</span></a>
  <nav class="nav-section">
    <h2>{t("domains_nav")}</h2>
    {''.join(nav_links)}
  </nav>
  <nav class="nav-section">
    <h2>{t("map_nav")}</h2>
    <a href="map.html"{map_cls}>{t("full_map")}</a>
  </nav>{SETTINGS_NAV}
</aside>"""


def root_index(term_counts: dict[str, int]) -> str:
    cards = []
    for d in DOMAINS:
        title = i18n(d["title"], d.get("title_en") or d["title"], d.get("title_es") or d["title"])
        if d["ready"]:
            cards.append(
                f"""<a class="chapter-card" href="{esc(d["href"])}">
  <div class="code">DOMAIN {esc(d["code"])}</div>
  <h2>{title}</h2>
  <p>{t("chapters_count", n=term_counts[d["code"]])}</p>
</a>"""
            )
        else:
            cards.append(
                f"""<div class="chapter-card is-disabled" aria-disabled="true">
  <div class="code">DOMAIN {esc(d["code"])}</div>
  <h2>{title}</h2>
  <p>{t("prep")}</p>
</div>"""
            )

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Security+ Textbook</title>
  {SETTINGS_BOOT}
  <link rel="icon" type="image/svg+xml" href="favicon.svg">
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
        <h1>{t("home_title")}</h1>
        <p>{t("home_tagline")}</p>
        <div class="action-row">
          <a class="btn btn-ghost" href="map.html">{t("full_map")}</a>
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
  <link rel="icon" type="image/svg+xml" href="favicon.svg">
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
        <p class="eyebrow">SY0-701 · {t("overview")}</p>
        <h1>{t("global_map_title")}</h1>
        <p>{t("global_map_tagline", n=total_terms)}</p>
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
                    "title_en": ch.get("title_en") or ch["title"],
                    "title_es": ch.get("title_es") or ch["title"],
                    "terms": n,
                }
            )
            print(f"wrote {out.name}/{path.name}: {n} terms")
        term_counts[d["code"]] = total
        hub_domains.append(
            {
                "code": d["code"],
                "title": data.get("title") or d["title"],
                "title_en": data.get("title_en") or d["title_en"],
                "title_es": data.get("title_es") or d["title_es"],
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
