# 各CLIの SKILLS 設定分析

本ドキュメントは、Codex / Claude Code / Cursor / Grok / Droid / Anti-Gravity CLI のスキル設定を実際のファイルシステムと CLI の非対話実行から調査した結果です。

## 調査環境

- macOS
- ユーザーホーム: `/Users/tomozo`
- 調査日: 2026-06-20

## 分析サマリ

| CLI | スキル格納パス | ファイル形式 | frontmatter | 補足リソース | 備考 |
|---|---|---|---|---|---|
| **Codex** | `~/.codex/skills/<skill>/SKILL.md` | Markdown + YAML frontmatter | `name`, `description`, 任意 `metadata` | `scripts/`, `references/`, `assets/`, `agents/openai.yaml` | システムスキルは `.system/` 配下 |
| **Claude Code** | `~/.claude/skills/<skill>/SKILL.md` | Markdown + YAML frontmatter | `name`, `description`, 任意 `metadata` | `scripts/`, `references/` | シンプルな1ディレクトリ構成 |
| **Cursor** | `~/.cursor/skills/<skill>/SKILL.md` | Markdown + YAML frontmatter | `name`, `description` | `scripts/`, `references/`, `assets/` | `~/.cursor/skills-cursor/` はCursor管理の組み込みスキル用 |
| **Grok** | `~/.grok/skills/<skill>/SKILL.md` | Markdown + YAML frontmatter | `name`, `description`, 任意 `metadata.short-description` | `scripts/`, `references/` | bundled skills も同じ形式 |
| **Droid** | `~/.factory/skills/<skill>/SKILL.md` | Markdown + YAML frontmatter | `name`, `description` | `scripts/`, `references/` | **skills** は `.factory/skills/` 配下（`.factory/droids/` は droid サブエージェント用） |
| **Anti-Gravity CLI** | `~/.gemini/config/plugins/<plugin>/skills/<skill>/SKILL.md`（runtime） | Markdown + YAML frontmatter | `name`, `description` | `plugin.json` でグルーピング | import 後は `~/.gemini/config/plugins/` が実際の読み込み元 |

## 非対話実行による検証

`shared-hello` スキルを `skills/shared-hello/SKILL.md` として追加し、各 CLI のスキル一覧に表示されることを確認しました。

| CLI | 検証コマンド | 結果 |
|---|---|---|
| **Codex** | `codex-ollama -d debug prompt-input "..."` | ✅ `shared-hello` が Available skills に表示 |
| **Droid** | `droid exec --settings <ollama> --auto low "List your available skills, including shared-hello."` | ✅ `shared-hello` が skills 一覧に表示 |
| **Grok** | `grok-ollama --no-subagents -p "List your available skills, including shared-hello."` | ✅ `shared-hello` が skills 一覧に表示（`grok-build` モデル 404 は secondary fork model 起因で非致命的） |
| **Anti-Gravity CLI** | `agy plugin install ~/.gemini/antigravity-cli/plugins/agent-skills` 後、`agy -p "..."` | ✅ `shared-hello` が利用可能スキルに表示 |
| **Claude Code** | `claude -p "..." --bare` | ❌ `Not logged in · Please run /login` のため未検証。ファイルシステム上の symlink は正しく配置済み |

## 詳細

### 1. Codex

- **場所**: `~/.codex/skills/`
- **形式**: サブディレクトリ名がスキル名。必ず `SKILL.md` を含む。
- **frontmatter例**:
  ```yaml
  ---
  name: skill-creator
  description: Guide for creating effective skills.
  metadata:
    short-description: Create or update a skill
  ---
  ```
- **追加メタデータ**:
  - `agents/openai.yaml` — スキル一覧に表示するアイコン・説明等のUIメタデータ
  - `scripts/` — 実行可能なスクリプト
  - `references/` — 必要に応じて読み込む補足ドキュメント
  - `assets/` — 画像やテンプレート
- **非対話検証**: `codex debug prompt-input` はローカルで実行でき、developer メッセージ内の `<skills_instructions>` に `shared-hello` が含まれることを確認。

### 2. Claude Code

- **場所**: `~/.claude/skills/`
- **形式**: サブディレクトリ + `SKILL.md`。シンプル。
- **frontmatter例**:
  ```yaml
  ---
  name: docs-search
  description: |
    ライブラリやフレームワークの公式ドキュメントを検索するスキル。
  ---
  ```
- **追加メタデータ**: `scripts/` や `references/` を同梱可能。`agents/openai.yaml` は不要。
- **非対話検証**: `claude -p` は Anthropic 認証が必要。本環境では未ログインのため実行できず。help 出力では `--disable-slash-commands` オプションがあり、skills は `/skill-name` で解決されることが確認済み。

### 3. Cursor

- **場所**: `~/.cursor/skills/`
- **形式**: サブディレクトリ + `SKILL.md`。Cursor IDEとCursor CLIの個人スキル共通パス。
- **注意**: `~/.cursor/skills-cursor/` はCursorが管理する組み込みスキル用のため、同期先にはしない。

### 4. Grok

- **場所**: `~/.grok/skills/`（ユーザースキル）, `~/.grok/bundled/skills/`（同梱スキル）
- **形式**: サブディレクトリ + `SKILL.md`。
- **frontmatter例**:
  ```yaml
  ---
  name: create-skill
  description: >
    Interactively create a new Grok skill.
  metadata:
    short-description: "Create a new Grok skill"
  ---
  ```
- **備考**: `grok` CLI は存在し、`grok-ollama` ランチャー経由で `~/.grok/skills/` のスキルが読み込まれる。`fork_secondary_model = "grok-build"` の設定は、Ollama Cloud 上に同名モデルが存在しない場合 404 を出すが、メインの応答には影響しない。`--no-subagents` を付けるとフォーク試行を抑制できる。

### 5. Droid

- **場所**: `~/.factory/skills/`
- **形式**: サブディレクトリ + `SKILL.md`。
- **frontmatter例**:
  ```yaml
  ---
  name: shared-hello
  description: A minimal cross-CLI skill example.
  ---
  ```
- **重要な区別**:
  - `.factory/droids/` にあるフラットな `.md` ファイルは **droid サブエージェント定義**（mission 内で `Task` ツールで呼び出す）。
  - `.factory/skills/` にある `SKILL.md` ディレクトリは **skills** として `droid exec` セッションに読み込まれる。
- **展開上の注意**:
  - `skills/<skill>/` を `~/.factory/skills/<skill>/` へ個別にシンボリックリンクする。
  - `~/.factory/droids/<skill>.md` へのコピーは不要。

### 6. Anti-Gravity CLI

- **source プラグイン**: `~/.gemini/antigravity-cli/plugins/agent-skills/skills/<skill>/SKILL.md`
- **runtime プラグイン**: `~/.gemini/config/plugins/agent-skills/skills/<skill>/SKILL.md`（import 後に実際に読まれる）
- **形式**: plugin 配下にスキルディレクトリを配置。plugin には `plugin.json` が必要。
- **frontmatter例**:
  ```yaml
  ---
  name: code-review
  description: Reviews the code changes on your current branch
  ---
  ```
- **展開上の注意**:
  - `skills/<skill>/` を `~/.gemini/antigravity-cli/plugins/agent-skills/skills/<skill>/` へ個別にシンボリックリンクする。
  - plugin ルートに `plugin.json`（最低限 `{ "name": "agent-skills" }`）を実ファイルとして置く。
  - 初回は `agy plugin install ~/.gemini/antigravity-cli/plugins/agent-skills` を実行し、`~/.gemini/config/plugins/` へインポートする。
  - その後、source と runtime の両方を symlink で同期すれば、`agy plugin install` の再実行なしでマスター更新が反映される。

## 共通化のための結論

1. **共通分母は `SKILL.md` + YAML frontmatter（`name`, `description`）**。これは Codex / Claude / Cursor / Grok / Droid / Anti-Gravity でほぼ同じ。
2. **Droid もディレクトリ形式の skills をサポート**する。`.factory/droids/` は別物（droid サブエージェント）なので、`.factory/skills/` へ symlink する。
3. **Codex の `agents/openai.yaml` や Anti-Gravity の `plugin.json`** は、他のCLIでは無視されるため、同じスキルディレクトリ内に共存させても問題ない。
4. **Anti-Gravity CLI は source と runtime の2箇所**にスキルディレクトリが存在する。`agy plugin install` で runtime へコピーされた後、両方を symlink でマスターに繋ぐ。
5. したがって、**`agent-skills/skills/<skill>/SKILL.md` をマスター**とし、各CLIの skills ディレクトリへ各スキルディレクトリを **個別にシンボリックリンク** するのが最も安全な共通化戦略。
