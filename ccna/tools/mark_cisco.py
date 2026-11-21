#!/usr/bin/env python3
"""CCNA のページで「Cisco 機器に限った知識」に目印を付ける。

使い方:  python3 ccna/tools/mark_cisco.py

- IOS のコマンド・設定例（コードブロック）は内容から自動で判定する。
- Cisco 独自の機能名・用語（本文）と、それを問う小テストは下の一覧で指定する。
- 目印は data-vendor="cisco" 属性と、data-gen="1" の付いた追加要素だけで表す。
  実行のたびにいったん全部外してから付け直すので、何度実行しても同じ結果になる。
- 設定パネルに「Cisco 固有を薄く表示」スイッチを足す（js/app.js の data-setting で動く）。
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# IOS の書き方だと判断する行頭（コードブロックの自動判定）
IOS_LINE = re.compile(
    r"^\s*(show |interface |switchport|router |ip route|ipv6 route|ipv6 unicast|ipv6 router|ip nat|"
    r"access-list|ip access-list|spanning-tree|vlan \d|channel-group|ntp |username |line vty|"
    r"S\*\s|ip address dhcp|ip helper)",
    re.M,
)
# 箇条書きの中で IOS の show コマンドを使った確認
IOS_SHOW = re.compile(r"\bshow (interfaces|vlan|spanning-tree|etherchannel|ip|ipv6|standby|vrrp|ntp|lacp)\b")

# (章, タグ, 要素の文字列（tr は先頭の文字列、それ以外は部分一致）, 汎用・標準での言い方 または None)
TEXT_MARKS = (
    ("02", "p", "Cisco IOS 系での確認例", None),
    ("03", "p", "確認例（Cisco）", None),
    ("04", "tr", "DTP", "標準の自動交渉はない。両端を trunk に固定するのが汎用的なやり方"),
    ("04", "h2", "Rapid PVST+（スパニングツリー）",
     "標準は RSTP（IEEE 802.1w）と MSTP（802.1s）。ルートブリッジやポート役割の考え方は共通"),
    ("04", "tr", "PortFast", "標準の呼び方はエッジポート（RSTP の edge port）"),
    ("04", "tr", "BPDU Guard", "他社にも同じ働きの機能があり、名前が違う（BPDU protection など）"),
    ("04", "tr", "Root Guard", None),
    ("04", "tr", "Loop Guard", None),
    ("04", "tr", "BPDU Filter", None),
    ("05", "p", "エンタープライズでは Lightweight AP + WLC が主流",
     "「Lightweight AP」「WLC」は Cisco の呼び方。AP とコントローラ間の CAPWAP は標準（RFC 5415）で、"
     "コントローラをクラウドに置くクラウド管理型も広く使われる"),
    ("06", "tr", "HSRP", "標準は VRRP（考え方は同じ）"),
    ("07", "p", "IOS XE での NAT/PAT", None),
)

# Cisco 固有の知識（IOS のコマンドや Cisco の機能名）が答えになる小テスト
QUIZ_MARKS = {
    "02": {"Q6"},
    "04": {"Q2", "Q6", "Q9", "Q12"},
    "05": {"Q4", "Q10"},
    "06": {"Q5", "Q10"},
    "07": {"Q10", "Q12"},
}

LEGEND = (
    '<p class="vendor-legend" data-gen="1"><span class="vendor-badge">Cisco 固有</span>'
    "の付いた部分は、Cisco 機器だけの書き方や機能名です。他社製品やクラウドでも通じる考え方を優先し、"
    "ここは「Cisco ではこう書く・こう呼ぶ」と押さえれば十分です。</p>"
)
SWITCH = (
    '<label class="switch-row" data-gen="1">\n'
    "      <span>Cisco 固有を薄く表示</span>\n"
    '      <input type="checkbox" role="switch" data-setting="dim-cisco">\n'
    '      <span class="switch" aria-hidden="true"></span>\n'
    "    </label>"
)
HEAD_OLD = "if(s.memorize)c.add('memorize');"
HEAD_NEW = HEAD_OLD + "if(s['dim-cisco'])c.add('dim-cisco');"


def strip_marks(src: str) -> str:
    src = src.replace(' data-vendor="cisco"', "")
    src = re.sub(r'<(p|span) class="vendor-(note|legend)" data-gen="1">.*?</\1>', "", src, flags=re.S)
    src = re.sub(r'\s*<label class="switch-row" data-gen="1">.*?</label>', "", src, flags=re.S)
    return src.replace(HEAD_NEW, HEAD_OLD)


def plain(s: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def add_attr(src: str, start: int) -> str:
    """start にある開始タグに data-vendor を足す。"""
    end = src.index(">", start)
    return src[:end] + ' data-vendor="cisco"' + src[end:]


def add_settings(src: str) -> str:
    src = src.replace(HEAD_OLD, HEAD_NEW, 1)
    m = re.search(r'data-setting="dark">\s*<span class="switch" aria-hidden="true"></span>\s*</label>', src)
    if not m:
        raise SystemExit("settings switch not found")
    return src[: m.end()] + "\n    " + SWITCH + src[m.end():]


def mark_chapter(ch: str, src: str) -> tuple[str, int]:
    src = strip_marks(src)
    count = 0
    # 1) IOS のコードブロック（後ろから処理して位置ずれを防ぐ）
    for m in reversed(list(re.finditer(r"<pre>(<code[^>]*>)(.*?)</code></pre>", src, re.S))):
        if IOS_LINE.search(html.unescape(m.group(2))):
            src = add_attr(src, m.start())
            count += 1
    # 2) show コマンドで確かめる箇条書き
    for m in reversed(list(re.finditer(r"<li>(.*?)</li>", src, re.S))):
        if "<pre>" not in m.group(1) and IOS_SHOW.search(plain(m.group(1))):
            src = add_attr(src, m.start())
            count += 1
    # 3) 一覧で指定した本文
    for c, tag, key, generic in TEXT_MARKS:
        if c != ch:
            continue
        hits = []
        for m in re.finditer(rf"<{tag}\b[^>]*>(.*?)</{tag}>", src, re.S):
            text = plain(m.group(1))
            if (text.startswith(key) if tag == "tr" else key in text):
                hits.append(m)
        if len(hits) != 1:
            raise SystemExit(f"{ch}.html: {tag} {key!r} matched {len(hits)} times")
        m = hits[0]
        if generic:
            note_text = f"汎用・標準では：{html.escape(generic)}"
            if tag == "tr":
                cell_end = m.group(0).rindex("</td>")
                pos = m.start() + cell_end
                src = src[:pos] + f'<span class="vendor-note" data-gen="1">{note_text}</span>' + src[pos:]
            else:
                src = src[: m.end()] + f'<p class="vendor-note" data-gen="1">{note_text}</p>' + src[m.end():]
        src = add_attr(src, m.start())
        count += 1
    # 4) 説明の一文と設定スイッチ
    if count:
        m = re.search(r'<article class="doc-body"><h1[^>]*>.*?</h1>', src, re.S)
        src = src[: m.end()] + LEGEND + src[m.end():]
    return add_settings(src), count


def mark_quiz(ch: str, src: str) -> tuple[str, int]:
    src = strip_marks(src)
    m = re.search(r'(<script type="application/json" id="quiz-data">)(.*?)(</script>)', src, re.S)
    qs = json.loads(m.group(2))
    ids = QUIZ_MARKS.get(ch, set())
    found = set()
    for q in qs:
        q.pop("vendor", None)
        if q["id"] in ids:
            q["vendor"] = "cisco"
            found.add(q["id"])
    if found != ids:
        raise SystemExit(f"quiz {ch}: ids not found {ids - found}")
    src = src[: m.start(2)] + json.dumps(qs, ensure_ascii=False) + src[m.end(2):]
    return add_settings(src), len(found)


def main() -> None:
    total = {"chapters": 0, "quizzes": 0}
    for kind, fn in (("chapters", mark_chapter), ("quizzes", mark_quiz)):
        for path in sorted((ROOT / kind).glob("*.html")):
            raw = path.read_bytes().decode("utf-8")
            crlf = "\r\n" in raw
            src, n = fn(path.stem, raw.replace("\r\n", "\n"))
            if crlf:
                src = src.replace("\n", "\r\n")
            path.write_bytes(src.encode("utf-8"))
            total[kind] += n
    print(f"marked {total['chapters']} places in chapters, {total['quizzes']} quiz questions")


if __name__ == "__main__":
    main()
