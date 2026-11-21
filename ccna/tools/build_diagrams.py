#!/usr/bin/env python3
"""CCNA の章ページにネットワーク構成図（インライン SVG）を差し込む。

使い方:  python3 ccna/tools/build_diagrams.py
章 HTML を Markdown から作り直したあとも、このスクリプトを実行すれば図が戻る。
描画の共通部品はリポジトリ直下の tools/netfig.py にある。
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parent / "tools"))
from netfig import Fig, figure, msg, seq_lane, apply  # noqa: E402


# ---------------------------------------------------------------- diagrams
def fig_base() -> str:
    f = Fig("fig-1-1", 720, 500, "本教材のベース構成図")
    f.zone(16, 88, 500, 404, "本社")
    f.zone(540, 88, 164, 262, "支店")

    # links
    f.line(326, 62, 258, 124)
    f.line(394, 62, 606, 126)
    f.line(250, 158, 250, 201)
    for x in (170, 330):
        f.line(250, 229, x, 282)
    f.line(192, 291, 308, 291)
    f.line(192, 299, 308, 299)
    f.line(352, 295, 436, 295)
    for ax in (110, 390):
        for cx in (170, 330):
            f.line(ax, 362, cx, 308)
    f.line(110, 388, 60, 432)
    f.line(110, 388, 150, 433)
    f.line(390, 388, 350, 432)
    f.line(390, 388, 430, 427)
    f.line(620, 158, 620, 217)
    f.line(620, 243, 620, 297)
    f.line(268, 140, 602, 140, "link vpn")
    f.pill(436, 140, "IPsec VPN（拠点間）", "pill pill-accent")

    # devices
    f.cloud(360, 42, "インターネット")
    f.label(250, 140, f.router(250, 140), "R1 エッジルータ")
    f.label(250, 215, f.firewall(250, 215), "NGFW")
    for x, n in ((170, "コア1"), (330, "コア2")):
        f.label(x, 295, f.switch(x, 295, l3=True), n)
    f.switch(460, 295, label_in="WLC", w=48)
    for x, n in ((110, "アクセス1"), (390, "アクセス2")):
        f.label(x, 375, f.switch(x, 375), n)
    f.label(60, 445, f.pc(60, 445), "PC", "VLAN 10")
    f.label(150, 445, f.ap(150, 439), "AP", "PoE 給電")
    f.label(350, 445, f.pc(350, 445), "PC", "VLAN 20")
    f.label(430, 445, f.server(430, 445), "サーバ")
    f.label(620, 140, f.router(620, 140), "支店ルータ")
    f.label(620, 230, f.switch(620, 230), "スイッチ")
    f.label(620, 310, f.pc(620, 310), "PC")

    # 章バッジ
    f.badge(205, 128, "6")
    f.badge(205, 152, "7")
    f.badge(212, 215, "8")
    f.badge(250, 352, "4")
    f.badge(250, 274, "4")
    f.badge(190, 440, "5")
    f.badge(500, 295, "5")

    # 凡例
    f.zone(540, 366, 164, 126, None, "legend")
    f.text(554, 388, "丸数字 = 詳しく扱う章", "sub", "start")
    for i, s in enumerate(("スイッチング（VLAN・STP）", "無線 LAN", "ルーティング", "IP サービス（NAT）",
                           "セキュリティ（ACL・VPN）")):
        y = 408 + i * 18
        f.badge(563, y - 3.5, str(4 + i))
        f.text(578, y, s, "sub", "start")
    return figure(
        f, "1-1",
        "この教材で使う架空の会社ネットワーク。丸数字の章で、それぞれの部分を詳しく扱います。",
        "機器がどの層にあるかで、障害の影響範囲が変わる。アクセス層の障害は一部の端末だけ、コア層の障害はネットワーク全体に広がる。",
    )


def fig_tiers() -> str:
    f = Fig("fig-1-2", 720, 262, "2階層・3階層・Spine-leaf の比較")
    panels = (
        (120, "2階層（コラプストコア）", "中小規模のキャンパス"),
        (360, "3階層", "大規模なキャンパス"),
        (600, "Spine-leaf", "データセンター"),
    )
    for cx, title, use in panels:
        f.zone(cx - 112, 8, 224, 246, None, "panel")
        f.text(cx, 32, title, "lbl")
        f.text(cx, 242, use, "sub")

    def row(cx, y, n, gap, name, w=52):
        xs = [cx + (i - (n - 1) / 2) * gap for i in range(n)]
        for x in xs:
            f.switch(x, y, label_in=name, w=w, h=24)
        return xs

    def mesh(top, ty, bottom, by):
        for a in top:
            for b in bottom:
                f.line(a, ty + 12, b, by - 12)

    # 2階層
    t = row(120, 90, 2, 90, "Core/Dist", w=66)
    b = row(120, 196, 3, 70, "Access")
    f.line(t[0] + 33, 90, t[1] - 33, 90)
    mesh(t, 90, b, 196)
    # 3階層
    c = row(360, 74, 2, 90, "Core")
    d = row(360, 140, 2, 90, "Dist")
    a = row(360, 206, 3, 72, "Access")
    f.line(c[0] + 26, 74, c[1] - 26, 74)
    mesh(c, 74, d, 140)
    mesh(d, 140, a, 206)
    # Spine-leaf
    s = row(600, 90, 2, 90, "Spine")
    lf = row(600, 196, 4, 54, "Leaf", w=46)
    mesh(s, 90, lf, 196)
    f.text(600, 222, "leaf 同士はつながない", "sub")
    return figure(
        f, "1-2",
        "代表的なトポロジの比較。線は機器同士の接続を表します。",
        "2階層はコアとディストリビューションを1つにまとめた形。Spine-leaf では、どの leaf 間の通信も spine を1台だけ経由するので、遅延が読みやすい。",
    )


def fig_vlan() -> str:
    f = Fig("fig-4-1", 720, 336, "VLAN とトランク")
    # 凡例
    f.line(24, 26, 46, 26, "link v10")
    f.text(52, 30, "VLAN 10", "sub", "start")
    f.line(112, 26, 134, 26, "link v20")
    f.text(140, 30, "VLAN 20", "sub", "start")
    f.line(200, 26, 222, 26, "link trunk")
    f.text(228, 30, "トランク", "sub", "start")

    f.line(232, 110, 488, 110, "link trunk")
    f.text(360, 98, "トランク（802.1Q）Gi0/24", "lbl")
    f.text(360, 130, "allowed 10,20,30,99 ／ native 99", "sub")
    pcs = ((130, 210, "v10", "PC-A", "VLAN 10（SALES）"), (290, 210, "v20", "PC-B", "VLAN 20"),
           (430, 510, "v10", "PC-C", "VLAN 10（SALES）"), (590, 510, "v20", "PC-D", "VLAN 20"))
    for x, sx, c, n, sub in pcs:
        f.line(sx + (-10 if x < sx else 10), 123, x, 192, f"link {c}")
        f.label(x, 205, f.pc(x, 205), n, sub)
    f.text(155, 160, "access", "sub")
    f.text(565, 160, "access", "sub")
    for x, n in ((210, "SW1"), (510, "SW2")):
        f.switch(x, 110)
        f.text(x, 82, n, "lbl")

    # フレーム
    f.text(150, 276, "トランク上を流れるフレーム", "sub", "start")
    x = 150
    for wdt, s, cls in ((84, "宛先 MAC", "fld"), (84, "送信元 MAC", "fld"), (104, "802.1Q タグ", "fld fld-tag"),
                        (54, "タイプ", "fld"), (110, "データ", "fld")):
        f.front.append(f'<rect x="{x}" y="284" width="{wdt}" height="26" class="{cls}"/>')
        f.text(x + wdt / 2, 301, s, "fld-txt" + (" fld-tag-txt" if "tag" in cls else ""))
        x += wdt
    f.text(352, 326, "4 バイト・VLAN ID 入り", "sub")
    return figure(
        f, "4-1",
        "同じ VLAN の端末は、スイッチをまたいでもトランク経由で直接届きます。VLAN 10 と 20 の間は、ルータか L3 スイッチを通らないと通信できません。",
        "アクセスポートは1つの VLAN だけでタグなし。トランクは複数の VLAN を 802.1Q タグ付きで運ぶ。native VLAN だけはタグなしで運ばれ、両端で一致していないと不具合になる。",
    )


def fig_stp() -> str:
    f = Fig("fig-4-3", 720, 318, "STP のポート役割")
    sw1, sw2, sw3 = (360, 70), (220, 214), (500, 214)
    f.line(*sw1, *sw2)
    f.line(*sw1, *sw3)
    f.line(sw2[0], 214, 360, 214)
    f.line(360, 214, sw3[0], 214, "link blocked")
    for p in (sw1, sw2, sw3):
        f.switch(*p)
    f.text(392, 66, "SW1 ルートブリッジ", "lbl", "start")
    f.text(392, 82, "priority 24576（最小）", "sub", "start")
    f.label(220, 214, 13, "SW2", "priority 32768 / MAC が小さい")
    f.label(500, 214, 13, "SW3", "priority 32768 / MAC が大きい")

    def on(p, q, t):
        return p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t

    f.pill(*on(sw1, sw2, 0.28), "DP", "pill pill-ok")
    f.pill(*on(sw1, sw3, 0.28), "DP", "pill pill-ok")
    f.pill(*on(sw2, sw1, 0.3), "RP", "pill pill-accent")
    f.pill(*on(sw3, sw1, 0.3), "RP", "pill pill-accent")
    f.pill(282, 214, "DP", "pill pill-ok")
    f.pill(434, 214, "ALT ✕", "pill pill-ng")

    y = 290
    for x, tag, cls, s in ((40, "RP", "pill pill-accent", "ルートポート：ルートへの最良の出口"),
                           (290, "DP", "pill pill-ok", "指定ポート：区間の転送役"),
                           (500, "ALT", "pill pill-ng", "代替ポート：待機（ブロック）")):
        f.pill(x, y, tag, cls, anchor="start")
        f.text(x + 40, y + 4, s, "sub", "start")
    return figure(
        f, "4-3",
        "3台のスイッチで三角形のループができている例（1つの VLAN）。SW2–SW3 間は、Bridge ID が小さい SW2 側が転送し、SW3 側をブロックしてループを防ぎます。",
        "ルートブリッジは Bridge ID（優先度＋MAC）が最も小さいスイッチ。ルート以外のスイッチには RP が1つ、各区間には DP が1つあり、残りのポートはブロックされる。",
    )


def fig_wlc() -> str:
    f = Fig("fig-5-1", 720, 300, "Lightweight AP と WLC")
    f.path("M190,124 C262,30 556,30 620,124", "link capwap")
    f.pill(405, 52, "CAPWAP トンネル（制御・データ）", "pill pill-accent")
    for y in (95, 185):
        f.line(80, y + (8 if y < 140 else -8), 168, 140 + (-6 if y < 140 else 6), "link wifi")
    f.line(208, 140, 308, 140)
    f.line(352, 140, 448, 140)
    f.line(492, 136, 596, 136)
    f.line(492, 144, 596, 144)
    f.text(258, 132, "access / trunk", "sub")
    f.text(400, 132, "trunk", "sub")
    f.text(544, 128, "LAG", "sub")

    f.label(60, 95, f.laptop(60, 95), "社員の端末")
    f.label(60, 185, f.laptop(60, 185), "ゲストの端末")
    f.label(190, 140, f.ap(190, 140), "Lightweight AP", "Local モード")
    f.label(330, 140, f.switch(330, 140), "アクセス SW")
    f.label(470, 140, f.switch(470, 140, l3=True), "コア／ディストリ")
    f.switch(620, 140, label_in="WLC", w=48)
    f.text(620, 172, "SSID・認証・電波を集中管理", "sub")

    f.zone(190, 232, 470, 56, None, "legend")
    f.text(206, 254, "SSID「CORP」 → VLAN 10（社員）", "sub", "start")
    f.text(206, 275, "SSID「GUEST」 → VLAN 30（ゲスト・社内から隔離）", "sub", "start")
    f.text(644, 265, "※ 例", "sub", "end")
    return figure(
        f, "5-1",
        "Lightweight AP は単独では設定を持たず、CAPWAP トンネルで WLC とやり取りします。AP をつなぐポートは、SSID が1つならアクセス、複数の VLAN を載せるならトランクにします。",
        "コントローラ型は SSID・セキュリティ・電波の設定を WLC で一括管理する。SSID と VLAN の対応を、有線側の VLAN・トランクの設定と揃えることが大切。",
    )


def fig_routing() -> str:
    f = Fig("fig-6-1", 720, 300, "経路表と構成の対応")
    f.zone(236, 36, 468, 112, "OSPF area 0", "zone zone-accent")
    f.line(135, 95, 252, 95)
    f.line(288, 95, 452, 95)
    f.line(488, 95, 608, 95)
    f.text(188, 86, "203.0.113.1", "sub")
    f.text(370, 86, "10.0.0.0/30", "sub")
    f.text(296, 112, ".1  Gi0/1", "sub", "start")
    f.text(444, 112, ".2", "sub", "end")
    f.cloud(90, 95, "ISP")
    f.label(270, 95, f.router(270, 95), "R1")
    f.label(470, 95, f.router(470, 95), "R2")
    f.label(630, 95, f.switch(630, 95), "10.10.0.0/24")

    f.zone(60, 166, 600, 122, None, "legend")
    f.text(78, 189, "R1# show ip route", "mono mono-muted", "start")
    rows = (("S*", "0.0.0.0/0 [1/0] via 203.0.113.1", "既定ルート（静的・AD 1）"),
            ("O", "10.10.0.0/24 [110/20] via 10.0.0.2", "OSPF で学習（AD 110）"),
            ("C", "10.0.0.0/30 is directly connected", "直結（AD 0）"))
    for i, (code, rest, note) in enumerate(rows):
        y = 216 + i * 24
        f.text(78, y, code, "mono mono-code", "start")
        f.text(106, y, rest, "mono", "start")
        f.text(642, y, "← " + note, "sub", "end")
    return figure(
        f, "6-1",
        "本文の出力例と同じアドレスで描いた構成。R1 から見て、ISP への既定ルートは静的、10.10.0.0/24 は R2 から OSPF で学習しています。",
        "行頭のコードで経路の出どころを、[AD/メトリック] で優先度を読み取る。宛先に合う経路が複数あれば、最長一致 → AD → メトリックの順で決まる。",
    )


def fig_fhrp() -> str:
    f = Fig("fig-6-2", 720, 312, "FHRP の仮想ゲートウェイ")
    f.zone(36, 92, 648, 74, None, "zone zone-accent")
    f.line(338, 62, 230, 109)
    f.line(382, 62, 490, 109)
    f.line(238, 125, 482, 125, "link hello")
    f.text(360, 118, "Hello", "sub")
    f.text(360, 152, "仮想 IP 192.168.10.1", "lbl lbl-accent")
    f.line(230, 143, 348, 197, "link active")
    f.line(490, 143, 372, 197)
    for x in (250, 360, 470):
        f.line(360, 223, x, 252)
    f.cloud(360, 42, "上位ネットワーク")
    f.router(220, 125)
    f.router(500, 125)
    f.text(194, 121, "R1  Active", "lbl", "end")
    f.text(194, 137, "192.168.10.2・priority 110", "sub", "end")
    f.text(526, 121, "R2  Standby", "lbl", "start")
    f.text(526, 137, "192.168.10.3・priority 100", "sub", "start")
    f.switch(360, 210)
    for x in (250, 360, 470):
        f.pc(x, 265)
    f.text(500, 262, "全端末のゲートウェイ", "sub", "start")
    f.text(500, 278, "= 192.168.10.1（仮想 IP）", "sub", "start")
    f.text(360, 300, "R1 が落ちると R2 が Active になる（端末の設定は変えなくてよい）", "sub")
    return figure(
        f, "6-2",
        "2台のルータで1つの仮想 IP を共有します。普段は Active の R1 が転送し、R2 は Hello で R1 の状態を見ながら待機しています。",
        "端末は仮想 IP をゲートウェイにしているので、Active が落ちても設定変更なしで Standby に切り替わる。preempt を有効にすると、優先度の高い R1 が復旧したときに Active に戻る。",
    )


def fig_nat() -> str:
    f = Fig("fig-7-2", 720, 316, "PAT（オーバーロード）の変換")
    f.zone(16, 28, 344, 152, "inside（10.0.0.0/24）")
    f.zone(360, 28, 344, 152, "outside", "zone zone-out")
    f.line(85, 65, 168, 96)
    f.line(85, 140, 168, 106)
    f.line(212, 101, 342, 101)
    f.line(378, 101, 476, 101)
    f.line(564, 101, 637, 101)
    f.text(330, 92, "Gi0/1 inside", "sub", "end")
    f.text(390, 92, "Gi0/0 outside", "sub", "start")
    f.label(70, 65, f.pc(70, 65), "10.0.0.11")
    f.label(70, 140, f.pc(70, 140), "10.0.0.12")
    f.label(190, 101, f.switch(190, 101), "SW")
    f.label(360, 101, f.router(360, 101), "R1", "外側 203.0.113.2")
    f.cloud(520, 101, "インターネット")
    f.label(650, 101, f.server(650, 101), "Web サーバ", "198.51.100.80")

    f.zone(40, 196, 640, 110, None, "legend")
    cols = (60, 280, 490)
    for x, h, s in zip(cols, ("Inside local", "Inside global", "Outside global"),
                       ("変換前の送信元", "変換後の送信元", "通信相手")):
        f.text(x, 218, h, "lbl", "start")
        f.text(x, 234, s, "sub", "start")
    f.links.append('<line x1="52" y1="244" x2="668" y2="244" class="rule"/>')
    for i, row in enumerate((("10.0.0.11:51000", "203.0.113.2:1024", "198.51.100.80:443"),
                             ("10.0.0.12:51000", "203.0.113.2:1025", "198.51.100.80:443"))):
        for x, s in zip(cols, row):
            f.text(x, 268 + i * 24, s, "mono" + (" mono-code" if x == 280 else ""), "start")
    return figure(
        f, "7-2",
        "本文の設定例（ACL 1 で 10.0.0.0/24 を許可、Gi0/0 で overload）での変換表。2台の PC が同じ外側アドレスを共有しています。",
        "inside local は変換前のプライベート IP、inside global は変換後のグローバル IP。PAT は送信元ポート番号で区別するので、多数の端末が1つのアドレスを共有できる。",
    )


def fig_acl() -> str:
    f = Fig("fig-8-1", 720, 304, "拡張 ACL の動き")
    f.line(92, 130, 168, 130)
    f.line(212, 130, 342, 130)
    f.line(378, 130, 618, 130)
    f.line(70, 82, 612, 82, "link flow-ok", arrow=True)
    f.text(400, 74, "HTTPS（tcp/443） → 最後の permit ip any any で許可", "sub", "middle")
    f.line(70, 186, 322, 186, "link flow-ng", arrow=True)
    f.text(338, 191, "✕", "ng-mark")
    f.text(92, 205, "SSH（tcp/22） → deny tcp 10.99.0.0 0.0.0.255 any eq 22 で拒否", "sub", "start")
    f.label(70, 130, f.pc(70, 130), "ゲスト端末", "10.99.0.0/24")
    f.label(190, 130, f.switch(190, 130), "SW")
    f.label(360, 130, f.router(360, 130), "R1")
    f.label(640, 130, f.server(640, 130), "サーバ", "10.10.0.10")
    f.pill(296, 108, "ACL in（Gi0/1）", "pill pill-accent")

    f.zone(40, 222, 640, 74, None, "legend")
    f.text(58, 244, "拡張 ACL → 送信元の近くに置く（宛先やポートまで見られるので、不要な通信を早く落とせる）", "sub", "start")
    f.text(58, 264, "標準 ACL → 宛先の近くに置く（送信元しか見ないので、送信元の近くだと他の通信まで止めてしまう）", "sub", "start")
    f.text(58, 284, "どの ACL も、最後に「暗黙の deny any」がある", "sub", "start")
    return figure(
        f, "8-1",
        "本文の設定例 BLOCK_SSH_FROM_GUEST を、R1 の Gi0/1 に in 方向で適用したときの動き。ゲストからの SSH だけを止め、それ以外は通します。",
        "ACL は上から順に照合し、最初に一致した行で許可・拒否が決まる。最後に暗黙の deny any があるので、通したい通信は明示的に permit する。",
    )


def fig_tcp() -> str:
    f = Fig("fig-3-1", 720, 306, "TCP と UDP の送り方の違い")
    for cx, title in ((180, "TCP（コネクション型）"), (540, "UDP（コネクションレス）")):
        f.zone(cx - 172, 8, 344, 290, None, "panel")
        f.text(cx, 32, title, "lbl")
    for c, s in ((90, 270), (450, 630)):
        seq_lane(f, c, 96, 262)
        seq_lane(f, s, 96, 262)
        f.label(c, 62, f.pc(c, 62), "クライアント")
        f.label(s, 62, f.server(s, 62), "サーバ")
    msg(f, 92, 268, 120, "SYN")
    msg(f, 268, 92, 158, "SYN / ACK")
    msg(f, 92, 268, 196, "ACK")
    msg(f, 92, 268, 238, "データ", "seq-data", "lbl lbl-accent")
    f.text(180, 286, "3ウェイハンドシェイクで接続してから送る", "sub")
    for y in (120, 158):
        msg(f, 452, 628, y, "データ", "seq-data", "lbl lbl-accent")
    f.line(452, 196, 560, 200, "link flow-ng", arrow=True)
    f.text(574, 205, "✕", "ng-mark")
    f.text(506, 190, "データ", "lbl")
    f.text(540, 236, "届かなくても再送しない", "sub")
    f.text(540, 286, "いきなり送る。確認応答も再送もない", "sub")
    return figure(
        f, "3-1",
        "TCP は最初に3回のやり取り（SYN → SYN/ACK → ACK）で接続を確立してから、データを送ります。UDP は確立なしで送り始め、届いたかどうかの確認もしません。",
        "TCP は確認応答・再送・順序制御で信頼性を確保する（そのぶんオーバーヘッドが大きい）。UDP は軽く速いが、信頼性が必要ならアプリ側で補う。",
    )


def fig_subnet() -> str:
    f = Fig("fig-3-2", 720, 270, "サブネット分割の例")
    x0, unit = 40, 2.5  # 1 アドレス = 2.5px
    f.front.append(f'<rect x="{x0}" y="34" width="640" height="30" rx="6" class="fld"/>')
    f.text(360, 54, "192.168.10.0/24（256 アドレス）", "lbl")
    for a in (0, 64, 128, 192, 256):
        f.text(x0 + a * unit, 80, f".{min(a, 255)}" if a < 256 else ".255", "sub", "middle" if 0 < a < 256 else ("start" if a == 0 else "end"))
    f.text(360, 102, "↓ /26 に分ける（ブロックサイズ 64）", "sub")
    for i in range(4):
        n = i * 64
        x = x0 + n * unit
        f.front.append(f'<rect x="{x + 2:g}" y="114" width="{64 * unit - 4:g}" height="30" rx="6" class="fld {"fld-tag" if i % 2 == 0 else "fld-alt"}"/>')
        f.text(x + 80, 134, f"192.168.10.{n}/26", "fld-txt" + (" fld-tag-txt" if i % 2 == 0 else ""))
        for j, (k, v) in enumerate((("ネットワーク", f".{n}"), ("ホスト", f".{n + 1} 〜 .{n + 62}"), ("ブロードキャスト", f".{n + 63}"))):
            y = 166 + j * 19
            f.text(x + 12, y, k, "sub", "start")
            f.text(x + 148, y, v, "mono mono-sm", "end")
    f.zone(40, 226, 640, 34, None, "legend")
    f.text(360, 248, "/26 = マスク 255.255.255.192　ホスト部 6 ビット → 2⁶ − 2 = 62 台", "sub")
    return figure(
        f, "3-2",
        "192.168.10.0/24 を /26 で4つに分けた例。どのサブネットも64アドレスずつで、先頭がネットワークアドレス、末尾がブロードキャストアドレスになります。",
        "ブロックサイズ（256 − マスクの最終オクテット）でネットワークアドレスの区切りがわかる。使えるホスト数は「2 の（ホスト部のビット数）乗 − 2」。",
    )


def fig_etherchannel() -> str:
    f = Fig("fig-4-2", 720, 244, "EtherChannel")
    f.back.append('<ellipse cx="360" cy="100" rx="130" ry="26" class="bundle"/>')
    f.line(172, 93, 548, 93)
    f.line(172, 107, 548, 107)
    f.pill(360, 62, "Port-channel1（論理リンク 1 本）", "pill pill-accent")
    f.text(186, 88, "Gi0/1", "sub", "start")
    f.text(186, 122, "Gi0/2", "sub", "start")
    f.text(534, 88, "Gi0/1", "sub", "end")
    f.text(534, 122, "Gi0/2", "sub", "end")
    f.label(150, 100, f.switch(150, 100), "SW1", "LACP active")
    f.label(570, 100, f.switch(570, 100), "SW2", "LACP active / passive")
    f.zone(40, 164, 640, 72, None, "legend")
    f.text(58, 186, "両端で揃える：速度・二重化、access / trunk と許可 VLAN", "sub", "start")
    f.text(58, 206, "LACP：active–active か active–passive なら束ねられる（passive 同士では束ならない）", "sub", "start")
    f.text(58, 226, "STP からは1本のリンクに見えるので、2本ともブロックされずに使える", "sub", "start")
    return figure(
        f, "4-2",
        "2本の物理リンクを Port-channel1 として1本にまとめた例。帯域が増え、1本が切れても通信は続きます。",
        "LACP は active が自分から交渉し、passive は相手を待つだけ。束ねる前に、両端の速度・二重化・トランク設定が一致しているかを確認する。",
    )


def fig_dhcp() -> str:
    f = Fig("fig-7-1", 720, 330, "DHCP の DORA とリレー")
    xs = (90, 360, 630)
    for x in xs:
        seq_lane(f, x, 104, 290)
    f.label(90, 60, f.pc(90, 60), "クライアント", "VLAN 10")
    f.label(360, 60, f.router(360, 60), "R1（リレー）", "ip helper-address 192.0.2.10")
    f.label(630, 60, f.server(630, 60), "DHCP サーバ", "192.0.2.10")
    steps = (("① Discover", 1), ("② Offer", -1), ("③ Request", 1), ("④ Ack", -1))
    for i, (name, d) in enumerate(steps):
        y = 124 + i * 44
        if d > 0:
            msg(f, 92, 358, y, name, drop=5)
            msg(f, 362, 628, y + 8, None, "seq-data", drop=5)
        else:
            msg(f, 628, 362, y, None, "seq-data", drop=5)
            msg(f, 358, 92, y + 8, name, drop=5)
    f.text(495, 120, "ユニキャストに変えて中継", "sub")
    f.text(225, 302, "Discover・Request はブロードキャスト", "sub")
    f.text(495, 302, "ユニキャスト", "sub")
    f.text(360, 322, "ルータはブロードキャストを転送しないので、別サブネットのサーバへはリレーが中継する", "sub")
    return figure(
        f, "7-1",
        "クライアントとは別のサブネットにある DHCP サーバから、アドレスを受け取るまでの流れ。R1 の ip helper-address がブロードキャストをサーバ宛てのユニキャストに変えて中継します。",
        "DORA（Discover → Offer → Request → Ack）の順番と、リレーが必要になる理由（ルータがブロードキャストを越えさせない）を説明できるようにする。",
    )


def fig_snooping() -> str:
    f = Fig("fig-8-2", 720, 322, "DHCP スヌーピング")
    f.line(145, 90, 338, 90)
    f.line(382, 90, 627, 90)
    f.line(360, 103, 360, 219)
    f.label(130, 90, f.pc(130, 90), "クライアント")
    f.label(360, 230, f.laptop(360, 230), "不正な DHCP サーバ")
    f.switch(360, 90)
    f.text(360, 62, "SW（DHCP snooping 有効）", "lbl")
    f.label(640, 90, f.server(640, 90), "正規の DHCP サーバ")
    f.pill(240, 90, "untrusted", "pill")
    f.pill(360, 168, "untrusted", "pill")
    f.pill(500, 90, "trusted", "pill pill-ok")
    f.line(560, 114, 400, 114, "link flow-ok", arrow=True)
    f.text(480, 134, "正規サーバの Offer → 通す", "sub")
    f.line(330, 214, 330, 128, "link flow-ng", arrow=True)
    f.text(330, 124, "✕", "ng-mark")
    f.text(316, 184, "不正な Offer → 破棄", "sub", "end")
    f.zone(40, 276, 640, 38, None, "legend")
    f.text(360, 299, "端末側のポートは untrusted のまま、正規サーバ側のアップリンクだけを trusted にする", "sub")
    return figure(
        f, "8-2",
        "DHCP スヌーピングを有効にしたスイッチは、untrusted ポートから来た DHCP サーバの応答（Offer・Ack）を破棄します。偽のゲートウェイや DNS を配る攻撃を防げます。",
        "信頼ポートの設定ミスが典型的なつまずき。アップリンクを trusted にし忘れると、正規の DHCP まで止まる。DAI はスヌーピングの記録（IP と MAC の対応）を使って不正な ARP を止める。",
    )


def fig_ipsec() -> str:
    f = Fig("fig-8-3", 720, 262, "サイト間 IPsec VPN")
    f.zone(16, 28, 224, 120, "本社（10.1.0.0/24）")
    f.zone(480, 28, 224, 120, "支店（10.2.0.0/24）")
    f.line(80, 100, 162, 100)
    f.line(198, 100, 312, 100)
    f.line(408, 100, 522, 100)
    f.line(558, 100, 640, 100)
    f.path("M180,80 C240,34 480,34 540,80", "link vpn")
    f.pill(360, 44, "IPsec トンネル（暗号化）", "pill pill-accent")
    f.label(64, 100, f.pc(64, 100), "PC", "10.1.0.10")
    f.label(180, 100, f.router(180, 100), "R1", "198.51.100.1")
    f.cloud(360, 100, "インターネット")
    f.label(540, 100, f.router(540, 100), "支店ルータ", "203.0.113.9")
    f.label(656, 100, f.pc(656, 100), "PC", "10.2.0.20")
    f.text(50, 178, "トンネルモードのパケット（R1 → 支店ルータの区間）", "sub", "start")
    x = 50
    for wdt, s, cls in ((230, "新しい IP ヘッダ（R1 → 支店ルータ）", "fld"), (50, "ESP", "fld fld-alt"),
                        (340, "元の IP ヘッダ（10.1.0.10 → 10.2.0.20）＋データ", "fld fld-tag")):
        f.front.append(f'<rect x="{x}" y="186" width="{wdt}" height="28" class="{cls}"/>')
        f.text(x + wdt / 2, 204, s, "fld-txt" + (" fld-tag-txt" if "tag" in cls else ""))
        x += wdt
    f.text(500, 232, "↑ 丸ごと暗号化される", "sub")
    f.text(360, 254, "暗号化と復号はトンネルの両端のルータが行うので、端末は VPN を意識しない", "sub")
    return figure(
        f, "8-3",
        "本社と支店をインターネット越しに常時つなぐサイト間 VPN。元のパケットを丸ごと暗号化し、ルータ同士のアドレスを付けた新しいヘッダで包んで送ります。",
        "サイト間 VPN は拠点間を常時接続し、リモートアクセス VPN は PC から必要なときに接続する。トンネルモードは元の IP ヘッダごと守り、トランスポートモードはデータ部分だけを守る。",
    )


def fig_sdn() -> str:
    f = Fig("fig-9-1", 720, 330, "SDN の3つの層")
    layers = ((18, "アプリケーション層", "監視・自動化・オーケストレーション"),
              (128, "コントロールプレーン", "コントローラ：経路やポリシーを決める頭脳"),
              (238, "データプレーン", "各機器：フレーム・パケットを転送する手足"))
    for y, name, desc in layers:
        f.zone(40, y, 640, 74, None, "legend")
        f.text(58, y + 24, name, "lbl", "start")
        f.text(58, y + 42, desc, "sub", "start")
    for i, s in enumerate(("監視アプリ", "自動化スクリプト", "オーケストレータ")):
        f.switch(400 + i * 104, 55, label_in=s, w=96, h=30)
    f.switch(560, 165, label_in="コントローラ", w=120, h=34)
    for i in range(4):
        f.switch(400 + i * 74, 275)
    for y1, y2, name, sub in ((92, 128, "Northbound API", "REST API・JSON"),
                              (202, 238, "Southbound API", "NETCONF・OpenFlow など")):
        f.line(320, y1 + 3, 320, y2 - 3, "link seq", arrow=True)
        f.line(320, y2 - 3, 320, y1 + 3, "link seq", arrow=True)
        f.text(334, (y1 + y2) / 2 - 1, name, "lbl", "start")
        f.text(334, (y1 + y2) / 2 + 13, sub, "sub", "start")
    return figure(
        f, "9-1",
        "コントローラ型（SDN）の構成。アプリはコントローラを Northbound API で呼び、コントローラは Southbound API で各機器に設定を配ります。",
        "制御（どう転送するかを決める）と転送（実際に送る）を分けるのが SDN の考え方。「誰が誰を API で呼ぶか」を、北（上のアプリ）と南（下の機器）で区別する。",
    )


# 図ごとに、どの章のどの見出しの直前に入れるか（ページ内の出現順に並べる）


PLACEMENTS = (
    ("01", '<h2 id="2"', fig_base),
    ("01", '<h2 id="3"', fig_tiers),
    ("03", '<h2 id="2-ipv4"', fig_tcp),
    ("03", '<h2 id="3-ipv6"', fig_subnet),
    ("04", '<h2 id="3-etherchannellacp"', fig_vlan),
    ("04", '<h2 id="4-rapid-pvst"', fig_etherchannel),
    ("04", '<h2 id="5"', fig_stp),
    ("05", '<h2 id="4-wlan-gui"', fig_wlc),
    ("06", '<h2 id="2"', fig_routing),
    ("06", '<h2 id="6"', fig_fhrp),
    ("07", '<h2 id="2-dns"', fig_dhcp),
    ("07", '<h2 id="4-ntp"', fig_nat),
    ("08", '<h2 id="5-2"', fig_acl),
    ("08", '<h2 id="6-ipsec-vpn"', fig_snooping),
    ("08", '<h2 id="7"', fig_ipsec),
    ("09", '<h2 id="4-rest-api-json"', fig_sdn),
)


if __name__ == "__main__":
    apply(ROOT / "chapters", PLACEMENTS)
