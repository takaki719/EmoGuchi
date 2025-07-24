# Database Migration Guide

## PostgreSQL (Neon) 用マイグレーション設定

### 1. 環境変数設定

本番環境でマイグレーションを実行する場合：

```bash
# .env ファイルまたは環境変数で設定
DATABASE_TYPE=postgresql
POSTGRES_HOST=ep-noisy-glitter-a1bm1cc1-pooler.ap-southeast-1.aws.neon.tech
POSTGRES_PORT=5432
POSTGRES_DB=neondb
POSTGRES_USER=neondb_owner
POSTGRES_PASSWORD=npg_OH5fYbW9KVnS
```

### 2. マイグレーション実行コマンド

```bash
# 新しいマイグレーションを作成
alembic revision --autogenerate -m "description of changes"

# マイグレーションを実行
alembic upgrade head

# マイグレーション履歴を確認
alembic history

# 現在のリビジョンを確認
alembic current
```

### 3. PostgreSQL特有の機能

現在の設定に含まれている PostgreSQL 最適化：

- `compare_type=True`: カラム型の変更を検出
- `compare_server_default=True`: デフォルト値の変更を検出
- `include_object`: 不要なテーブル（alembic_version等）を除外

### 4. Fly.io デプロイ時のマイグレーション

Fly.io での自動マイグレーション実行のため、`fly.toml` に以下を追加可能：

```toml
[deploy]
  release_command = "alembic upgrade head"
```

### 5. トラブルシューティング

- **接続エラー**: SSL設定を確認（Neonでは `sslmode=require` が必要）
- **権限エラー**: データベースユーザーの権限を確認
- **マイグレーション競合**: `alembic merge` でマージリビジョンを作成

### 6. セキュリティ注意事項

- 本番パスワードをリポジトリにコミットしない
- Fly.io secrets を使用してデータベース認証情報を管理
- 開発環境では SQLite を使用（DATABASE_TYPE=sqlite）