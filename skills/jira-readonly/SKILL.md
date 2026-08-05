---
name: jira-readonly
description: Retrieve individual Jira issues and search issues with JQL through Jira Cloud REST API using an Atlassian API token, without creating, updating, transitioning, or deleting data. Use when the user asks to look up a Jira ticket, provides a Jira issue URL or key, or requests a read-only Jira search.
---

# Jira Readonly

Jira Cloud REST APIから課題を読み取り専用で取得する。

## Prerequisites

以下を環境変数に設定する。

- `JIRA_BASE_URL`: 例 `https://jocy.atlassian.net`
- `JIRA_EMAIL`: Atlassianアカウントのメールアドレス
- `JIRA_API_TOKEN`: Atlassianアカウントで作成したAPIトークン

認証情報を出力、保存、応答へ転載しない。

## Get an issue

Jira URLまたは課題キーからキーを特定し、次を実行する。

```bash
scripts/get-issue.sh "$JIRA_BASE_URL" "$JIRA_EMAIL" "$JIRA_API_TOKEN" GWXF-1441
```

回答では少なくとも課題キー、要約、ステータス、説明、担当者、Jiraリンクを整理する。取得できない項目は推測しない。

## Search issues

```bash
scripts/search-issues.sh "$JIRA_BASE_URL" "$JIRA_EMAIL" "$JIRA_API_TOKEN" 'project = GWXF ORDER BY created DESC' 20
```

続きが必要な場合は、レスポンスの `nextPageToken` を第6引数に渡す。

```bash
scripts/search-issues.sh "$JIRA_BASE_URL" "$JIRA_EMAIL" "$JIRA_API_TOKEN" 'project = GWXF ORDER BY created DESC' 20 "$NEXT_PAGE_TOKEN"
```

## Read-only boundary

- `GET /rest/api/3/issue/{issueIdOrKey}` と `GET /rest/api/3/search/jql` だけを使う。
- 作成、更新、コメント、トランジション、削除を行わない。
- 401はメールアドレスまたはトークン、403は権限、404は課題キーまたは閲覧権限を確認する。
- Jira取得に失敗した場合、別の情報源へフォールバックせず失敗理由を報告する。
