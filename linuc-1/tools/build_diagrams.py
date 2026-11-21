#!/usr/bin/env python3
"""LinuC-1 の章ページに概念図（インライン SVG）を差し込む。

使い方:  python3 linuc-1/tools/build_diagrams.py
章 HTML を Markdown から作り直したあとも、このスクリプトを実行すれば図が戻る。
描画の共通部品はリポジトリ直下の tools/netfig.py にある。
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parent / "tools"))
from netfig import Fig, figure, msg, seq_lane, apply  # noqa: E402


def chain_arrows(f: Fig, xs, y, half_w, kind="seq"):
    for a, b in zip(xs, xs[1:]):
        f.arrow(a + half_w + 2, y, b - half_w - 2, y, kind)


# ---------------------------------------------------------------- 02 起動
def fig_boot() -> str:
    f = Fig("fig-2-1", 720, 262, "Linux の起動の流れ")
    steps = (("UEFI / BIOS", "ハードを検査し", "ブートローダを探す"),
             ("GRUB", "カーネルと", "initramfs を読み込む"),
             ("カーネル", "ハードを初期化し", "ルート FS をマウント"),
             ("systemd（PID 1）", "target に従って", "サービスを起動"),
             ("ログイン", "multi-user.target", "graphical.target"))
    stops = (("ブートメニュー", "No bootable device"), ("grub> の画面", "GRUB rescue"),
             ("kernel panic", "カーネルが停止"), ("emergency シェル", "rescue.target"),
             ("ログイン画面", "起動完了"))
    xs = [72 + i * 144 for i in range(5)]
    for i, (x, (t, a, b)) in enumerate(zip(xs, steps)):
        f.front.append(f'<rect x="{x - 62}" y="41" width="124" height="78" rx="8" '
                       f'class="{"box-soft" if i == 3 else "dev"}"/>')
        f.text(x, 64, t, "lbl")
        f.text(x, 84, a, "sub")
        f.text(x, 99, b, "sub")
        s1, s2 = stops[i]
        f.box(x, 186, 124, 44, s1, s2, "box-ok" if i == 4 else "box-gray", "lbl-sm")
        f.line(x, 146, x, 163, "link lane")
    chain_arrows(f, xs, 80, 62)
    f.text(12, 138, "止まったときに見える画面", "zone-lbl", "start")
    f.text(360, 248, "起動しないときは、どの画面で止まったかで、原因のある段階を絞り込む", "sub")
    return figure(
        f, "2-1",
        "電源を入れてからログインできるまでの4段階。各段階が次の段階のプログラムを読み込んで、処理を引き継ぎます。",
        "ブートローダ（GRUB）がカーネルと initramfs を読み込み、カーネルが最初に起動するプロセスが systemd（PID 1）。起動後の状態は target（multi-user.target など）で決まる。",
    )


# ---------------------------------------------------------------- 03 リダイレクト
def fig_streams() -> str:
    f = Fig("fig-3-1", 720, 282, "標準入出力とリダイレクト・パイプ")
    f.box(360, 100, 150, 64, "コマンド", "（プロセス）", "box-soft")
    f.box(95, 100, 130, 50, "キーボード", "< ファイル で差し替え")
    f.box(625, 52, 130, 46, "画面", "> ファイル（上書き）")
    f.box(625, 150, 130, 46, "画面", "2> ファイル")
    f.arrow(162, 100, 283, 100)
    f.text(222, 90, "0  stdin（標準入力）", "lbl-sm")
    f.arrow(437, 88, 558, 58, "seq-data")
    f.text(486, 62, "1  stdout", "lbl-sm")
    f.arrow(437, 112, 558, 144, "flow-ng")
    f.text(486, 146, "2  stderr", "lbl-sm")
    f.text(40, 214, "例：command 2>&1 | grep error", "zone-lbl", "start")
    f.box(110, 246, 120, 36, "command", None, "dev", "mono-b")
    f.arrow(172, 246, 316, 246, "seq-data")
    f.text(244, 236, "1 と 2 をまとめて |", "sub")
    f.box(380, 246, 124, 36, "grep error", None, "dev", "mono-b")
    f.arrow(444, 246, 546, 246)
    f.text(495, 236, "1 stdout", "sub")
    f.box(610, 246, 120, 36, "画面")
    return figure(
        f, "3-1",
        "どのコマンドにも、入力1本（0番）と出力2本（1番：通常の出力、2番：エラー）があります。リダイレクトはその行き先をファイルに変え、パイプは出力を次のコマンドの入力につなぎます。",
        "2>&1 は「2番（エラー）を1番と同じ行き先へ」という意味。パイプ（|）が運ぶのは1番だけなので、エラーも grep したいときは 2>&1 を先に書く。",
    )


# ---------------------------------------------------------------- 04 FHS・権限・リンク
def fig_fhs() -> str:
    f = Fig("fig-4-1", 720, 272, "FHS の主なディレクトリ")
    f.box(360, 34, 64, 30, "/", None, "box-soft", "mono-b")
    kids = (("/etc", "設定"), ("/var", "可変データ"), ("/home", "ユーザー"), ("/usr", "プログラム"),
            ("/tmp", "一時ファイル"), ("/proc", "プロセス情報"), ("/sys", "デバイス情報"))
    xs = [72 + i * 96 for i in range(7)]
    f.line(360, 49, 360, 68)
    f.line(72, 68, 648, 68)
    for x, (name, desc) in zip(xs, kids):
        f.line(x, 68, x, 89)
        f.box(x, 110, 86, 42, name, desc, "box-dash" if name in ("/proc", "/sys") else "dev", "mono-b")
    grand = (("/etc/ssh/", "SSH の設定"), ("/var/log/", "ログ"), ("/home/alice/", "alice の家"), ("/usr/bin/", "コマンド本体"))
    for x, (name, desc) in zip(xs, grand):
        f.line(x, 131, x, 174)
        f.box(x, 195, 92, 42, name, desc, "box-gray", "mono-sm-b")
    f.text(360, 258, "点線の /proc と /sys はディスク上に実体がなく、カーネルが見せている仮想ファイルシステム", "sub")
    return figure(
        f, "4-1",
        "FHS（Filesystem Hierarchy Standard）で決まっている主なディレクトリ。すべて / から始まる1本の木になっています。",
        "「設定は /etc、ログは /var/log、一時ファイルは /tmp」のように、何を置く場所かを説明できるようにする。/proc と /sys は実行中のカーネルの情報を見る窓口。",
    )


def fig_perm() -> str:
    f = Fig("fig-4-2", 720, 262, "パーミッションの読み方")
    x0, w = 140, 44
    for i, ch in enumerate("-rwxr-x---"):
        cls = "fld" if i == 0 or i >= 7 else ("fld fld-tag" if i <= 3 else "fld fld-alt")
        f.front.append(f'<rect x="{x0 + i * w}" y="34" width="{w}" height="42" class="{cls}"/>')
        f.text(x0 + i * w + w / 2, 62, ch, "perm" + (" fld-tag-txt" if 1 <= i <= 3 else ""))
    groups = ((0, 0, "種別"), (1, 3, "所有者（u）"), (4, 6, "グループ（g）"), (7, 9, "その他（o）"))
    nums = (None, "4+2+1 = 7", "4+0+1 = 5", "0+0+0 = 0")
    for (s, e, name), n in zip(groups, nums):
        a, b = x0 + s * w + 4, x0 + (e + 1) * w - 4
        f.path(f"M{a},84v6H{b}v-6", "link bracket")
        cx = (a + b) / 2
        f.text(cx, 108, name, "lbl-sm")
        if n:
            f.text(cx, 132, n, "mono mono-code")
    f.text(360, 172, "→ 数値で書くと 750（chmod 750 ファイル名）", "lbl lbl-accent")
    f.zone(80, 192, 560, 62, None, "legend")
    for i, s in enumerate(("r = 4　読む（ディレクトリなら一覧を見る）",
                           "w = 2　書く（ディレクトリなら作成・削除・名前の変更）",
                           "x = 1　実行する（ディレクトリなら cd で中に入る）")):
        f.text(100, 211 + i * 17, s, "sub", "start")
    return figure(
        f, "4-2",
        "ls -l の左端10文字の読み方。最初の1文字が種別（- 通常ファイル、d ディレクトリ、l シンボリックリンク）で、残りの9文字が3人分の権限です。",
        "r=4・w=2・x=1 を足した数を3人分並べたものが数値モード。644（rw-r--r--）、755（rwxr-xr-x）、600（rw-------）はよく出る。",
    )


def fig_links() -> str:
    f = Fig("fig-4-3", 720, 296, "ハードリンクとシンボリックリンク")
    f.text(120, 24, "名前（ディレクトリのエントリ）", "zone-lbl")
    f.text(380, 24, "i ノード", "zone-lbl")
    f.text(600, 24, "データ", "zone-lbl")
    f.box(120, 62, 130, 40, "symlink.txt", "シンボリックリンク", "dev", "mono-b")
    f.box(380, 62, 130, 40, "inode 5678")
    f.box(600, 62, 150, 40, "中身 = パス名", "\"original.txt\"")
    f.arrow(187, 62, 313, 62)
    f.arrow(447, 62, 523, 62)
    f.path("M600,84V112H120V128", "link vpn", arrow=False)
    f.arrow(120, 124, 120, 133, "seq-data")
    f.text(360, 106, "名前をたどって original.txt を開く", "sub")
    f.box(120, 154, 130, 40, "original.txt", "元のファイル", "dev", "mono-b")
    f.box(120, 214, 130, 40, "hardlink.txt", "ハードリンク", "dev", "mono-b")
    f.box(380, 184, 130, 44, "inode 1234", "リンク数 2", "box-soft")
    f.box(600, 184, 150, 44, "データ本体", "（ファイルの中身）")
    f.arrow(187, 156, 313, 178, "seq-data")
    f.arrow(187, 212, 313, 190, "seq-data")
    f.arrow(447, 184, 523, 184)
    f.zone(40, 242, 640, 46, None, "legend")
    f.text(58, 261, "original.txt を消すと… ハードリンク：hardlink.txt からまだ読める（リンク数が 1 減るだけ）", "sub", "start")
    f.text(58, 279, "シンボリックリンク：たどる先の名前がなくなり、壊れたリンクになる", "sub", "start")
    return figure(
        f, "4-3",
        "ハードリンクは同じ i ノード（ファイルの実体）に付けた別の名前。シンボリックリンクは、別のファイル名（パス）を中身として持つ小さなファイルです。",
        "ls -i で i ノード番号が同じならハードリンク。ハードリンクは同じファイルシステム内でしか作れないが、シンボリックリンクは別のファイルシステムやディレクトリも指せる。",
    )


# ---------------------------------------------------------------- 06 プロセス
def fig_ptree() -> str:
    f = Fig("fig-6-1", 720, 256, "プロセスの親子関係")
    f.text(24, 24, "→ は「親が子を起動した」関係", "sub", "start")
    chain = (("systemd", "PID 1"), ("sshd", "PID 812"), ("sshd: alice", "PID 2051"),
             ("bash", "PID 2052"), ("top", "PID 2101"))
    xs = [74 + i * 140 for i in range(5)]
    for i, (x, (n, p)) in enumerate(zip(xs, chain)):
        f.box(x, 70, 118, 44, n, p, "box-soft" if i == 0 else "dev", "mono-b")
    chain_arrows(f, xs, 70, 59)
    f.path("M74,92V170H150", "link seq", arrow=True)
    f.box(214, 170, 118, 44, "nginx: master", "PID 700", "dev", "mono-sm-b")
    f.box(374, 146, 118, 40, "nginx: worker", "PID 701", "dev", "mono-sm-b")
    f.box(374, 196, 118, 40, "nginx: worker", "PID 702", "dev", "mono-sm-b")
    f.arrow(275, 162, 312, 150)
    f.arrow(275, 178, 312, 192)
    f.text(494, 112, "↑ ssh でログインした人の操作（sshd → bash → top）", "sub")
    f.text(360, 246, "PPID（親の PID）をたどると、最後は PID 1 の systemd に行き着く。親子関係は pstree -p で見られる", "sub")
    return figure(
        f, "6-1",
        "ssh でログインして top を動かしているときのプロセスの木。どのプロセスも、ほかのプロセス（親）から起動されています。",
        "ps -ef の PPID 列が親の PID。親が子より先に終わると、子は systemd（PID 1）に引き取られる。終わったのに親に回収されない子はゾンビ（状態 Z）になる。",
    )


def fig_signals() -> str:
    f = Fig("fig-6-2", 720, 262, "主なシグナル")
    rows = ((60, "kill -15 PID", "SIGTERM：終了のお願い", "box-ok", "flow-ok", "後片付けをしてから終了する"),
            (130, "kill -9 PID", "SIGKILL：強制終了", "box-ng", "flow-ng", "その場で止まる（後片付けなし）"),
            (200, "kill -1 PID", "SIGHUP：再読み込みの合図", "box-soft", "seq-data", "設定を読み直す（多くのデーモン）"))
    for y, cmd, sig, bcls, kind, result in rows:
        f.box(140, y, 220, 46, cmd, sig, bcls, "mono-b")
        f.arrow(252, y, 318, y, kind)
        f.box(380, y, 110, 40, "プロセス")
        f.arrow(437, y, 488, y)
        f.text(498, y + 4, result, "lbl-sm", "start")
    f.text(360, 250, "まず SIGTERM。応答しないときだけ SIGKILL（プロセス側で捕まえて無視することができない）", "sub")
    return figure(
        f, "6-2",
        "kill コマンドは、プロセスに「シグナル」という合図を送ります。番号を省略した kill PID は SIGTERM（15）です。",
        "-9（SIGKILL）を常用しない。一時ファイルの削除や子プロセスの整理などの後片付けが飛ばされ、データが壊れることがある。",
    )


# ---------------------------------------------------------------- 07 パッケージ
def fig_pkg() -> str:
    f = Fig("fig-7-1", 720, 268, "パッケージ管理の高水準と低水準")
    f.box(190, 48, 250, 48, "高水準：apt / dnf", "依存関係を調べてまとめて入れる", "box-soft")
    f.box(580, 48, 200, 48, "リポジトリ", "パッケージと索引の置き場")
    f.arrow(317, 40, 478, 40)
    f.text(397, 30, "① 索引を見て依存関係を調べる", "sub")
    f.arrow(478, 58, 317, 58, "seq-data")
    f.text(397, 78, "② まとめてダウンロード", "sub")
    for x, w, s in ((80, 120, "nginx.deb"), (220, 134, "nginx-common.deb"), (360, 120, "libssl3.deb")):
        f.box(x, 128, w, 30, s, None, "box-gray", "mono-sm-b")
    f.text(432, 132, "依存するパッケージも一緒に", "sub", "start")
    f.arrow(190, 74, 190, 111)
    f.arrow(190, 145, 190, 182)
    f.box(190, 208, 250, 48, "低水準：dpkg / rpm", "パッケージを1つずつ展開・登録")
    f.box(580, 208, 200, 48, "システムへ配置", "/usr/bin・/etc など")
    f.arrow(317, 208, 478, 208)
    f.text(397, 198, "③ 展開して登録", "sub")
    f.text(360, 258, "Debian 系：apt → dpkg（.deb）　RPM 系：dnf / yum → rpm（.rpm）", "sub")
    return figure(
        f, "7-1",
        "apt install nginx を実行したときの流れ（Debian 系の例）。高水準のコマンドが依存関係を解決し、実際の展開は低水準のコマンドが行います。",
        "高水準（apt・dnf）は依存関係を解決してリポジトリから入れる。低水準（dpkg・rpm）は手元のパッケージファイルを1つずつ扱い、依存関係は解決しない。",
    )


# ---------------------------------------------------------------- 08 ストレージ
def fig_lvm() -> str:
    f = Fig("fig-8-1", 720, 318, "ストレージの層と LVM")
    rows = ((42, "マウントポイント", "mount・/etc/fstab"), (92, "ファイルシステム", "mkfs.ext4"),
            (142, "LV（論理ボリューム）", "lvcreate"), (192, "VG（ボリュームグループ）", "vgcreate"),
            (242, "PV（物理ボリューム）", "pvcreate"), (292, "パーティション", "gdisk・parted"))
    for y, name, cmd in rows:
        f.text(24, y - 2, name, "lbl-sm", "start")
        f.text(24, y + 13, cmd, "mono mono-sm mono-muted", "start")
    for x in (300, 560):
        f.line(x, 276, x, 258)
        f.line(x, 226, x, 208)
    for x in (320, 537):
        f.line(x, 176, x, 158)
        f.line(x, 126, x, 108)
        f.line(x, 76, x, 58)
    f.box(300, 292, 220, 32, "/dev/sdb1", None, "dev", "mono-b")
    f.box(560, 292, 220, 32, "/dev/sdc1", None, "dev", "mono-b")
    f.box(300, 242, 220, 32, "PV /dev/sdb1", None, "box-gray", "mono-b")
    f.box(560, 242, 220, 32, "PV /dev/sdc1", None, "box-gray", "mono-b")
    f.box(430, 192, 480, 32, "vgdata（PV をまとめた容量のプール）", None, "box-soft")
    f.box(320, 142, 260, 32, "lvapp（20G）", None, "dev", "mono-b")
    f.box(537, 142, 150, 32, "lvlog（10G）", None, "dev", "mono-b")
    f.box(646, 142, 48, 32, "空き", None, "box-dash", "sub")
    f.box(320, 92, 260, 32, "ext4")
    f.box(537, 92, 150, 32, "xfs")
    f.box(320, 42, 260, 32, "/app", None, "box-gray", "mono-b")
    f.box(537, 42, 150, 32, "/var/log/app", None, "box-gray", "mono-b")
    return figure(
        f, "8-1",
        "2本のディスクを LVM でまとめ、必要な大きさの LV を切り出して使う例。下から順にコマンドで作っていきます。",
        "PV（物理ボリューム）を束ねて VG（プール）にし、そこから LV（論理ボリューム）を切り出す。VG に空きがあれば lvextend で LV をあとから広げられる。",
    )


# ---------------------------------------------------------------- 09 SSH
def fig_ssh() -> str:
    f = Fig("fig-9-1", 720, 300, "SSH の公開鍵認証")
    cx, sx = 230, 490
    seq_lane(f, cx, 88, 238)
    seq_lane(f, sx, 88, 238)
    f.laptop(cx, 40)
    f.server(sx, 42)
    f.text(cx, 76, "クライアント", "lbl")
    f.text(sx, 76, "サーバ（sshd）", "lbl")
    msg(f, cx + 2, sx - 2, 104, "事前に ssh-copy-id で公開鍵を登録", "seq-data", "lbl-sm")
    msg(f, sx - 2, cx + 2, 144, "① ホスト鍵を見せる（known_hosts と照合）", "seq", "lbl-sm")
    msg(f, sx - 2, cx + 2, 184, "② 合図（チャレンジ）を送る", "seq", "lbl-sm")
    msg(f, cx + 2, sx - 2, 224, "③ 秘密鍵で署名して返す", "seq", "lbl-sm")
    f.text(360, 258, "④ サーバが公開鍵で署名を確かめる → ログイン成功", "lbl lbl-accent")
    f.box(100, 130, 160, 44, "~/.ssh/id_ed25519", "秘密鍵（外に出さない）", "box-soft", "mono-sm-b")
    f.box(100, 190, 160, 44, "~/.ssh/known_hosts", "接続先ホストの記録", "dev", "mono-sm-b")
    f.box(620, 130, 170, 44, "~/.ssh/authorized_keys", "許可する公開鍵", "box-soft", "mono-sm-b")
    f.box(620, 190, 170, 44, "/etc/ssh/sshd_config", "PasswordAuthentication no", "dev", "mono-sm-b")
    f.text(360, 290, "秘密鍵そのものはネットワークに流れない。パスワード認証を止めると、総当たり攻撃が効かなくなる", "sub")
    return figure(
        f, "9-1",
        "鍵認証でログインするまでの流れ。サーバには公開鍵だけを置き、クライアントは秘密鍵で「本人である証明」を作って送ります。",
        "秘密鍵はクライアント（~/.ssh/id_ed25519）、公開鍵はサーバの ~/.ssh/authorized_keys。known_hosts は接続先サーバのホスト鍵の記録で、なりすまし検知に使う。",
    )


# ---------------------------------------------------------------- 10 ネットワーク
def fig_resolve() -> str:
    f = Fig("fig-10-1", 720, 252, "名前解決の順番")
    f.box(88, 120, 140, 50, "アプリ", "ping・curl・getent")
    f.box(292, 120, 176, 50, "/etc/nsswitch.conf", "hosts: files dns", "box-soft", "mono-sm-b")
    f.box(512, 60, 180, 50, "/etc/hosts", "① files：手元の対応表", "dev", "mono-b")
    f.box(512, 180, 180, 50, "/etc/resolv.conf", "② dns：問い合わせ先", "dev", "mono-b")
    f.box(666, 180, 76, 50, "DNS", "サーバ")
    f.arrow(160, 120, 202, 120)
    f.arrow(382, 108, 420, 72)
    f.arrow(382, 132, 420, 168)
    f.arrow(604, 180, 626, 180)
    f.text(392, 80, "まず", "sub", "end")
    f.text(392, 168, "なければ", "sub", "end")
    f.text(360, 240, "/etc/hosts に書いた内容は DNS より先に使われる（手元で上書きできる）", "sub")
    return figure(
        f, "10-1",
        "ホスト名を IP アドレスに変える順番。/etc/nsswitch.conf の hosts 行に書かれた順（files → dns）で調べます。",
        "getent hosts 名前 は nsswitch.conf の順番どおりに引くので、アプリと同じ結果を確認できる。「名前が解けない」と「名前は解けるが届かない」を分けて考える。",
    )


def fig_triage() -> str:
    f = Fig("fig-10-2", 720, 214, "つながらないときの確認順")
    steps = (("リンク", "ip link", "L1・L2"), ("アドレス", "ip addr", "L3"), ("経路", "ip route", "L3"),
             ("疎通", "ping GW", "L3"), ("名前解決", "getent hosts", "DNS"), ("待ち受け・FW", "ss -tlnp", "L4・アプリ"))
    xs = [65 + i * 118 for i in range(6)]
    for i, (x, (t, c, layer)) in enumerate(zip(xs, steps)):
        f.front.append(f'<rect x="{x - 53}" y="48" width="106" height="80" rx="8" class="dev"/>')
        f.badge(x, 48, str(i + 1))
        f.text(x, 84, t, "lbl")
        f.text(x, 106, c, "mono mono-sm")
        f.text(x, 148, layer, "sub")
    chain_arrows(f, xs, 88, 53)
    f.arrow(40, 172, 680, 172, "seq-data")
    f.text(360, 198, "下の層から順に確かめ、失敗した段で原因を探す", "sub")
    return figure(
        f, "10-2",
        "通信できないときの切り分けの順番。物理的なつながりから始めて、アプリの待ち受けまで1段ずつ上がっていきます。",
        "上の段だけ見ても原因はわからない。たとえば DNS を疑う前に、ゲートウェイへの ping が通るかを確かめる。",
    )


# ---------------------------------------------------------------- 11 ログ
def fig_logs() -> str:
    f = Fig("fig-11-1", 720, 262, "ログの流れ")
    f.box(90, 70, 130, 46, "サービス", "nginx・sshd など")
    f.box(90, 150, 130, 46, "カーネル", "dmesg の内容")
    f.box(290, 110, 150, 50, "systemd-journald", "ログを集める", "box-soft", "mono-sm-b")
    f.box(290, 212, 170, 46, "/var/log/journal/", "journalctl で読む", "dev", "mono-sm-b")
    f.box(470, 110, 110, 46, "rsyslog", "振り分けて書く", "dev", "mono-b")
    f.box(640, 58, 140, 46, "/var/log/syslog", "messages など", "dev", "mono-sm-b")
    f.box(640, 138, 140, 36, "logrotate", None, "box-gray", "mono-b")
    f.text(640, 170, "ローテ・圧縮・削除", "sub")
    f.box(640, 226, 140, 46, "ログサーバ", "中央集約（転送）")
    f.arrow(157, 74, 213, 102)
    f.arrow(157, 146, 213, 118)
    f.arrow(290, 136, 290, 187)
    f.arrow(367, 110, 413, 110)
    f.arrow(527, 100, 568, 66)
    f.arrow(527, 120, 568, 218)
    f.arrow(640, 119, 640, 83, "seq-data")
    return figure(
        f, "11-1",
        "ログが書き出されるまでの流れ。journald が集めたログを、rsyslog がファイルやほかのサーバへ振り分けます。",
        "journalctl は journald が保存したログを読む。/var/log/journal/ がない環境では再起動で消える。ファイルのログは logrotate が定期的に整理して、ディスクがいっぱいになるのを防ぐ。",
    )


# ---------------------------------------------------------------- 13 仮想化
def fig_hv() -> str:
    f = Fig("fig-13-1", 720, 292, "ハイパーバイザー型とホスト型")
    f.text(180, 28, "ハイパーバイザー型", "lbl")
    f.text(180, 46, "ハードの上で直接動く（KVM・Xen）", "sub")
    f.text(540, 28, "ホスト型", "lbl")
    f.text(540, 46, "普段の OS の上で動く（VirtualBox）", "sub")
    f.box(180, 250, 300, 34, "ハードウェア", None, "box-gray")
    f.box(180, 210, 300, 34, "ハイパーバイザー", None, "box-soft")
    for x in (106, 254):
        f.box(x, 130, 145, 84, "ゲスト OS", "＋ アプリ")
    f.box(540, 250, 300, 34, "ハードウェア", None, "box-gray")
    f.box(540, 210, 300, 34, "ホスト OS（Windows・macOS など）")
    f.box(540, 170, 300, 34, "仮想化ソフト", None, "box-soft")
    for x in (466, 614):
        f.box(x, 110, 145, 64, "ゲスト OS", "＋ アプリ")
    f.text(360, 284, "CPU の仮想化支援（Intel VT-x / AMD-V）があると速い。lscpu で確認できる", "sub")
    return figure(
        f, "13-1",
        "仮想マシンを動かす2つの方式。ホスト型は間にホスト OS が入るぶん手軽ですが、そのぶん遅くなりがちです。",
        "KVM は Linux カーネル自体をハイパーバイザーにする仕組み。今の OS が仮想マシンやコンテナの中かどうかは systemd-detect-virt で確認できる。",
    )


def fig_vm_ct() -> str:
    f = Fig("fig-13-2", 720, 300, "仮想マシンとコンテナの違い")
    f.text(180, 28, "仮想マシン", "lbl")
    f.text(180, 46, "VM ごとにカーネルを持つ", "sub")
    f.text(540, 28, "コンテナ", "lbl")
    f.text(540, 46, "ホストのカーネルを1つ共有する", "sub")
    f.box(180, 270, 300, 30, "ハードウェア", None, "box-gray")
    f.box(180, 234, 300, 30, "ハイパーバイザー")
    for x in (106, 254):
        f.back.append(f'<rect x="{x - 72.5}" y="110" width="145" height="101" rx="9" class="frame"/>')
        f.box(x, 132, 129, 26, "アプリ")
        f.box(x, 162, 129, 26, "ライブラリ")
        f.box(x, 192, 129, 26, "ゲスト OS・カーネル", None, "box-soft", "lbl-sm")
    f.box(540, 270, 300, 30, "ハードウェア", None, "box-gray")
    f.box(540, 234, 300, 30, "ホスト OS（カーネル）", None, "box-soft")
    f.box(540, 198, 300, 30, "コンテナエンジン（Docker など）")
    for x in (442, 540, 638):
        f.back.append(f'<rect x="{x - 48}" y="116" width="96" height="62" rx="9" class="frame"/>')
        f.box(x, 133, 84, 24, "アプリ")
        f.box(x, 161, 84, 24, "ライブラリ")
    return figure(
        f, "13-2",
        "色の付いた箱がカーネル。仮想マシンは OS ごと動かすので重く、コンテナはホストのカーネルを共有するので軽く起動が速い、という違いが生まれます。",
        "コンテナは「軽い VM」ではなく、隔離されたプロセスとファイルシステムの層。カーネルを共有するので、ホストと違う種類の OS カーネルは動かせない。",
    )


# 図ごとに、どの章のどの見出しの直前に入れるか（ページ内の出現順に並べる）
PLACEMENTS = (
    ("02", '<h2 id="2-grub"', fig_boot),
    ("03", '<h2 id="4"', fig_streams),
    ("04", '<h2 id="2-ls-l"', fig_fhs),
    ("04", '<h2 id="3"', fig_perm),
    ("04", '<h2 id="5-find"', fig_links),
    ("06", '<h2 id="2"', fig_ptree),
    ("06", '<h2 id="4-nice-renice"', fig_signals),
    ("07", '<h2 id="2-debian-apt-dpkg"', fig_pkg),
    ("08", '<h2 id="6-i"', fig_lvm),
    ("09", '<h2 id="5"', fig_ssh),
    ("10", '<h2 id="5-firewalld-ufw"', fig_resolve),
    ("10", '<h2 id="7"', fig_triage),
    ("11", '<h2 id="5"', fig_logs),
    ("13", '<h2 id="3"', fig_hv),
    ("13", '<h2 id="4-kvm-virsh"', fig_vm_ct),
)


if __name__ == "__main__":
    apply(ROOT / "chapters", PLACEMENTS)
