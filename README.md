# Agent Skills（マスターリポジトリ）

このディレクトリは、Codex・Claude Code・Grok・Droid・Anti-Gravity CLI など複数のAIコーディングCLIで共通して使えるスキルの**唯一の情報源（Single Source of Truth）**です。

## コンセプト

- 各CLI専用のスキルディレクトリ（`~/.codex/skills` など）を個別に管理する代わりに、ここにスキルを1つ追加すれば、同期スクリプトで各CLIに展開できます。
- スキルの中身は各CLI共通の `SKILL.md` を中心に、必要に応じて `scripts/`・`references/`・`assets/` を同梱します。
- CLI固有のメタデータ（Codex の `agents/openai.yaml` など）は、同じスキルディレクトリ内に置きます。他のCLIは読み飛ばします。

## ディレクトリ構成

```
agent-skills/
├── README.md
├── docs/
│   └── cli-skills-analysis.md   # 各CLIのスキル設定分析
├── scripts/
│   └── sync.py                  # マスター → 各CLI 同期スクリプト
└── skills/
    └── <skill-name>/
        ├── SKILL.md             # 必須。YAML frontmatter + Markdown
        ├── agents/
        │   └── openai.yaml      # Codex 用 UI メタデータ（任意）
        ├── scripts/             # 実行スクリプト（任意）
        ├── references/          # 補足資料（任意）
        └── assets/              # 画像・テンプレート等（任意）
```

## 使い方

1. 新しいスキルを `skills/<skill-name>/SKILL.md` として作成する。
2. 下記を実行して各CLIへ反映する（デフォルトは dry-run）。

```bash
# 1. dry-run で確認
python3 scripts/sync.py

# 2. 問題なければ反映
python3 scripts/sync.py --apply
```

3. Anti-Gravity CLI を初めて使う場合は、さらに以下を実行して runtime へインポートする。

```bash
agy plugin install ~/.gemini/antigravity-cli/plugins/agent-skills
```

## 同期内容の検証

`SKILL.md` や symlink が壊れていないか、展開後に検証できます。

```bash
# 既存の target について、空でないことを確認
python3 scripts/sync.py --verify

# すべてのCLI target が存在することも要求（まだインストールしていないCLIがある場合はFAILします）
python3 scripts/sync.py --verify-strict
```

検証では以下を確認します。

- マスター側の `skills/<skill>/SKILL.md` が空（または空白のみ）でないこと
- 各CLIの `SKILL.md` が存在し、空（または空白のみ）でないこと
- target が symlink の場合、リンク先が壊れていないこと

## 対応CLIと展開先

| CLI | 展開方法 | 展開先（macOS環境） |
|---|---|---|
| Codex | `skills/<skill>` を個別 symlink | `~/.codex/skills/<skill>` |
| Claude Code | `skills/<skill>` を個別 symlink | `~/.claude/skills/<skill>` |
| Grok | `skills/<skill>` を個別 symlink | `~/.grok/skills/<skill>` |
| Droid | `skills/<skill>` を個別 symlink | `~/.factory/skills/<skill>` |
| Anti-Gravity CLI | `skills/<skill>` を plugin source / runtime 両方へ個別 symlink | `~/.gemini/antigravity-cli/plugins/agent-skills/skills/<skill>` と `~/.gemini/config/plugins/agent-skills/skills/<skill>` |

## 注意事項

- 原則として各スキルディレクトリを個別にシンボリックリンクするため、既存のCLI固有スキル（Codex の `.system/` など）はそのまま保持されます。
- 既存の同名スキルがある場合、デフォルトでは上書きしません。上書きする場合は `--force` を付けてください。
- マスター側の `skills/<skill>/` を編集すると、リンク先の Codex / Claude / Grok / Droid / Anti-Gravity CLI source に即時反映されます。
- Anti-Gravity CLI は `agy plugin install` 時に runtime ディレクトリへコピーされます。`scripts/sync.py` は source と runtime の両方を symlink で維持するため、マスター更新が即座に反映されます。
- Droid の `.factory/droids/` にある `.md` ファイルは「droid サブエージェント定義」であり、skills とは別物です。skills は `.factory/skills/` へ展開します。

## 詳細な分析

- `docs/cli-skills-analysis.md` — 各CLIのスキル検索パス・ファイル形式・frontmatter・検証結果をまとめています。
