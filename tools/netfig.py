"""ネットワーク構成図・概念図をインライン SVG で描き、章 HTML に差し込む共通部品。

各サイトの tools/build_diagrams.py から読み込んで使う（ccna/、linuc-1/）。
- 図は <!-- fig:ID --> ... <!-- /fig:ID --> の間に入る。実行のたびに外して入れ直すので、何度実行しても同じ結果になる。
- 色は CSS 変数（各サイトの css/doc.css の .net-fig）に任せるので、ダークモードでも読める。
"""
from __future__ import annotations

import html
import re
from pathlib import Path


# ---------------------------------------------------------------- primitives
def esc(s: str) -> str:
    return html.escape(s, quote=True)


def text_w(s: str, size: float) -> float:
    """ざっくりした文字幅の見積もり（全角=1em、半角=0.6em）。"""
    w = 0.0
    for ch in s:
        w += size if ord(ch) > 0x2E7F else size * 0.6
    return w


class Fig:
    def __init__(self, fid: str, w: int, h: int, title: str):
        self.fid, self.w, self.h, self.title = fid, w, h, title
        self.back: list[str] = []   # ゾーン・背景
        self.links: list[str] = []  # 線
        self.front: list[str] = []  # 機器・文字

    # -- text ---------------------------------------------------------------
    def text(self, x, y, s, cls="lbl", anchor="middle", layer="front"):
        getattr(self, layer).append(
            f'<text x="{x:g}" y="{y:g}" class="{cls}" text-anchor="{anchor}">{esc(s)}</text>'
        )

    def pill(self, x, y, s, cls="pill", size=10.5, anchor="middle"):
        w = text_w(s, size) + 14
        x0 = x - w / 2 if anchor == "middle" else (x - w if anchor == "end" else x)
        self.front.append(
            f'<g class="{cls}"><rect x="{x0:g}" y="{y - 9:g}" width="{w:g}" height="18" rx="9"/>'
            f'<text x="{x0 + w / 2:g}" y="{y + 3.6:g}" text-anchor="middle">{esc(s)}</text></g>'
        )

    def badge(self, x, y, n: str):
        self.front.append(
            f'<g class="badge"><circle cx="{x:g}" cy="{y:g}" r="9"/>'
            f'<text x="{x:g}" y="{y + 3.6:g}" text-anchor="middle">{esc(n)}</text></g>'
        )

    def zone(self, x, y, w, h, label=None, cls="zone"):
        self.back.append(f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="14" class="{cls}"/>')
        if label:
            self.text(x + 12, y + 18, label, "zone-lbl", "start", layer="back")

    # -- lines --------------------------------------------------------------
    def line(self, x1, y1, x2, y2, cls="link", arrow=False):
        m = f' marker-end="url(#{self.fid}-{cls.split()[-1]}-arr)"' if arrow else ""
        self.links.append(f'<line x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" class="{cls}"{m}/>')

    def path(self, d, cls="link", arrow=False):
        m = f' marker-end="url(#{self.fid}-{cls.split()[-1]}-arr)"' if arrow else ""
        self.links.append(f'<path d="{d}" class="{cls}"{m}/>')

    def arrow(self, x1, y1, x2, y2, kind="seq"):
        """矢印付きの線。kind は seq / seq-data / flow-ok / flow-ng。"""
        self.line(x1, y1, x2, y2, f"link {kind}", arrow=True)

    # -- 概念図用の箱 ---------------------------------------------------------
    def box(self, cx, cy, w, h, title, sub=None, cls="dev", tcls="lbl", scls="sub", layer="front"):
        """中心 (cx, cy) の角丸の箱。title（と sub）を中央に書く。"""
        part = [f'<rect x="{cx - w / 2:g}" y="{cy - h / 2:g}" width="{w:g}" height="{h:g}" rx="7" class="{cls}"/>']
        if sub:
            part.append(f'<text x="{cx:g}" y="{cy - 2:g}" class="{tcls}" text-anchor="middle">{esc(title)}</text>')
            part.append(f'<text x="{cx:g}" y="{cy + 13:g}" class="{scls}" text-anchor="middle">{esc(sub)}</text>')
        else:
            part.append(f'<text x="{cx:g}" y="{cy + 4:g}" class="{tcls}" text-anchor="middle">{esc(title)}</text>')
        getattr(self, layer).append("<g>" + "".join(part) + "</g>")

    # -- devices (cx, cy が中心) ----------------------------------------------
    def _arrows(self, cx, cy, a):
        return (f'<path class="ico" d="M{cx - a:g},{cy - 4:g}h{2 * a:g}m-4,-4l4,4l-4,4'
                f'M{cx + a:g},{cy + 4:g}h{-2 * a:g}m4,-4l-4,4l4,4"/>')

    def router(self, cx, cy):
        self.front.append(f'<g><circle cx="{cx:g}" cy="{cy:g}" r="18" class="dev"/>{self._arrows(cx, cy, 9)}</g>')
        return 18

    def switch(self, cx, cy, l3=False, label_in=None, w=44, h=26):
        s = f'<rect x="{cx - w / 2:g}" y="{cy - h / 2:g}" width="{w:g}" height="{h:g}" rx="5" class="dev"/>'
        if label_in:
            s += f'<text x="{cx:g}" y="{cy + 4:g}" class="in-lbl" text-anchor="middle">{esc(label_in)}</text>'
        else:
            s += self._arrows(cx, cy, 11)
        if l3:
            s += (f'<rect x="{cx + w / 2 - 12:g}" y="{cy - h / 2 - 7:g}" width="20" height="13" rx="4" class="tag-bg"/>'
                  f'<text x="{cx + w / 2 - 2:g}" y="{cy - h / 2 + 2.6:g}" class="tag-txt" text-anchor="middle">L3</text>')
        self.front.append(f"<g>{s}</g>")
        return h / 2

    def firewall(self, cx, cy):
        x, y = cx - 22, cy - 14
        self.front.append(
            f'<g><rect x="{x:g}" y="{y:g}" width="44" height="28" rx="4" class="dev"/>'
            f'<path class="ico" d="M{x:g},{cy:g}h44M{cx - 8:g},{y:g}v14M{cx + 10:g},{y:g}v14'
            f'M{cx - 15:g},{cy:g}v14M{cx + 2:g},{cy:g}v14M{cx + 17:g},{cy:g}v14"/></g>'
        )
        return 14

    def pc(self, cx, cy):
        self.front.append(
            f'<g><rect x="{cx - 15:g}" y="{cy - 13:g}" width="30" height="20" rx="3" class="dev"/>'
            f'<path class="ico" d="M{cx:g},{cy + 7:g}v5M{cx - 8:g},{cy + 13:g}h16"/></g>'
        )
        return 13

    def laptop(self, cx, cy):
        self.front.append(
            f'<g><rect x="{cx - 13:g}" y="{cy - 11:g}" width="26" height="17" rx="2.5" class="dev"/>'
            f'<path class="dev" d="M{cx - 18:g},{cy + 10:g}l4,-4h28l4,4z"/></g>'
        )
        return 11

    def server(self, cx, cy):
        x, y = cx - 13, cy - 18
        self.front.append(
            f'<g><rect x="{x:g}" y="{y:g}" width="26" height="36" rx="3" class="dev"/>'
            f'<path class="ico" d="M{x + 5:g},{cy - 7:g}h16M{x + 5:g},{cy + 1:g}h16"/>'
            f'<circle cx="{cx:g}" cy="{cy + 10:g}" r="2" class="ico-dot"/></g>'
        )
        return 18

    def ap(self, cx, cy):
        self.front.append(
            f'<g><rect x="{cx - 18:g}" y="{cy - 6:g}" width="36" height="12" rx="6" class="dev"/>'
            f'<path class="ico" d="M{cx - 6:g},{cy - 10:g}a8.5,8.5 0 0 1 12,0M{cx - 11:g},{cy - 15:g}a15,15 0 0 1 22,0"/></g>'
        )
        return 6

    def cloud(self, cx, cy, label=None):
        d = (f"M{cx - 44:g},{cy + 20:g}"
             f"a16,16 0 0 1 4,-31a22,22 0 0 1 38,-11a19,19 0 0 1 33,8"
             f"a15,15 0 0 1 13,34z")
        self.front.append(f'<path d="{d}" class="dev cloud"/>')
        if label:
            self.text(cx, cy + 9, label, "lbl")
        return 25

    def label(self, cx, cy, half, name, sub=None):
        self.text(cx, cy + half + 15, name, "lbl")
        if sub:
            self.text(cx, cy + half + 29, sub, "sub")

    # -- output -------------------------------------------------------------
    def svg(self) -> str:
        defs = "".join(
            f'<marker id="{self.fid}-{c}-arr" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" '
            f'markerHeight="7" orient="auto-start-reverse"><path d="M0,0L10,5L0,10z" class="arr-{c}"/></marker>'
            for c in ("flow-ok", "flow-ng", "seq", "seq-data")
        )
        body = "".join(self.back + self.links + self.front)
        return (
            f'<svg viewBox="0 0 {self.w} {self.h}" role="img" aria-labelledby="{self.fid}-t" '
            f'xmlns="http://www.w3.org/2000/svg"><title id="{self.fid}-t">{esc(self.title)}</title>'
            f"<defs>{defs}</defs>{body}</svg>"
        )


def figure(fig: Fig, num: str, caption: str, point: str) -> str:
    return (
        f'<!-- fig:{fig.fid} -->\n'
        f'<figure class="net-fig" id="{fig.fid}">'
        f'<div class="net-fig-scroll">{fig.svg()}</div>'
        f"<figcaption><strong>図 {esc(num)}</strong>{esc(caption)}</figcaption>"
        f'<p class="net-fig-point"><span>試験ポイント</span>{esc(point)}</p>'
        f"</figure>\n"
        f"<!-- /fig:{fig.fid} -->\n"
    )


def seq_lane(f: Fig, x, top, bottom):
    f.links.append(f'<line x1="{x:g}" y1="{top:g}" x2="{x:g}" y2="{bottom:g}" class="lane"/>')


def msg(f: Fig, x1, x2, y, label=None, cls="seq", lbl_cls="lbl", drop=6):
    """時系列図のメッセージ矢印（少し下がりながら進む）。"""
    f.line(x1, y, x2, y + drop, f"link {cls}", arrow=True)
    if label:
        f.text((x1 + x2) / 2, y - 6, label, lbl_cls)


FIG_BLOCK = re.compile(r"<!-- fig:([\w-]+) -->.*?<!-- /fig:\1 -->\r?\n", re.S)


def apply(chapters: Path, placements) -> None:
    """placements: (章番号, 直前に入れる見出しの文字列, 図を返す関数) の並び。ページ内の出現順に書く。"""
    pages: dict[str, str] = {}
    for ch, anchor, fn in placements:
        if ch not in pages:
            pages[ch] = FIG_BLOCK.sub("", (chapters / f"{ch}.html").read_bytes().decode("utf-8"))
        src = pages[ch]
        block = fn()
        if "\r\n" in src:
            block = block.replace("\n", "\r\n")
        if src.count(anchor) != 1:
            raise SystemExit(f"{ch}.html: anchor {anchor!r} not found exactly once")
        pages[ch] = src.replace(anchor, block + anchor)
    for ch, src in pages.items():
        (chapters / f"{ch}.html").write_bytes(src.encode("utf-8"))
    print(f"inserted {len(placements)} figures into {len(pages)} chapters")
