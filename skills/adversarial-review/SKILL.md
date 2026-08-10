---
name: adversarial-review
description: Run independent, read-only adversarial reviews with Codex GPT, Claude Code Sonnet, and Cursor Agent Grok, then verify and synthesize their findings. Use when the user asks for a multi-model review, adversarial review, second opinions from GPT/Claude/Grok, pre-merge risk review, or competing critiques of code, a diff, a design, or an implementation plan.
---

# Adversarial Review

3つのモデルへ同じ対象を独立にレビューさせ、根拠を実物で再確認してから統合する。

## Run

1. レビュー対象、期待する動作、対象範囲を1つの依頼文にまとめる。指定がなければ現在の作業ツリーまたは差分を対象にする。
2. スキルのディレクトリから実行する。

```bash
python3 scripts/run_review.py --cwd "$PWD" '現在の変更をレビューする。要件: ...'
```

長い依頼は標準入力で渡す。

```bash
python3 scripts/run_review.py --cwd "$PWD" < /tmp/review-request.txt
```

スクリプトは3つのCLIを並列かつ読み取り専用で実行し、JSONを返す。

- Codex: CLIの既定モデル（モデルIDを固定しない）
- Claude Code: `sonnet`（CLIが最新Sonnetへ解決するエイリアス）
- Cursor Agent: `cursor-agent --list-models` にある最新Grokの最強・非Fastモデル

CLIや認証がないモデルは勝手に代替しない。失敗したモデル名と理由を報告する。

## Verify and synthesize

各出力を証拠候補として扱い、次の順で処理する。

1. 指摘されたファイル、行、実行経路を自分で確認する。
2. 再現条件または失敗経路を説明できない指摘を捨てる。
3. 同じ原因の指摘を統合する。モデル数を信頼度の代用にしない。
4. 重大度順に、場所、問題、影響、最小修正、確信度を示す。
5. 根拠が拮抗する不一致だけを「未解決の論点」として残す。

レビュー結果をそのまま転載しない。コード変更はユーザーが修正も依頼した場合だけ行う。

## Check

Cursor CLIの実際のモデル一覧で選択ロジックを検証する。モデル推論は実行しない。

```bash
python3 scripts/run_review.py --self-test
```
