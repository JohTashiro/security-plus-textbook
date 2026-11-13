# データ ID 方針

進捗・ブックマーク・知識マップ・小テスト連携のため、用語は **全体で一意な ID** で管理する。

## 命名規則

| 対象 | 表示 | 識別子 / ファイル | 例 |
|---|---|---|---|
| Domain | `A` | フォルダ `a/` | Domain A |
| Chapter | `A-1` | `a-1.html` / `slug: a-1` | A-1 |
| Term | （日本語名） | `{chapter_slug}-{key}` | `a-1-technical` |

- `key` … 章内の短い英小文字スラッグ（`technical`, `gap-analysis`）
- `id` … **全体一意**。必ず `{chapter_slug}-{key}`
- 公式試験番号（`1.1` など）は `chapter.official` と表示チップのみ。ID には使わない

## JSON フィールド

```json
{
  "id": "a-1-technical",
  "key": "technical",
  "ja": "技術的コントロール",
  "en": "Technical",
  "one_liner": "**技術・ソフト**で守る対策",
  "examples": ["暗号化"]
}
```

小テスト `a-quizzes.json` の各問題は `"term": "a-1-technical"` のように **term.id を参照**する。

## ビルド時チェック

`python build_study.py` が次を検証し、違反で失敗する。

- chapter id / slug / term id の形式
- term id == `{chapter_slug}-{key}`
- term id・chapter id の重複なし
- クイズが章内の全 term をカバーし、未知 ID を参照していない

## Domain 追加時

1. `data/b.json` / `data/b-quizzes.json` を追加（term id は `b-1-...`、`"domain": "B"`）
2. `python build_study.py` を実行（両ファイルがそろった Domain は自動で公開扱いになり、`b/` に出力される）
3. term id はドメインをまたいでも重複不可（ビルドで検査）
