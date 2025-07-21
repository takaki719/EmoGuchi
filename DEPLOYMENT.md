# EMOGUCHI Deployment Guide

デプロイ構成：
- **Frontend**: Cloudflare Pages (Next.js 静的/ISR)
- **Backend**: Fly.io Machines (FastAPI + Socket.IO)
- **Database**: Neon Serverless PostgreSQL
- **Storage**: Cloudflare R2

## 1. Neon PostgreSQL Setup

```bash
# 1. Neon (https://neon.tech) でアカウント作成
# 2. 新しいプロジェクト作成
# 3. 接続文字列をコピー（DATABASE_URL）
```

## 2. Cloudflare R2 Setup

```bash
# 1. Cloudflare Dashboard → R2 Object Storage
# 2. バケット作成 (例: emoguchi-audio)
# 3. API Token作成 (R2 Edit権限)
# 4. 以下の値を取得:
#    - Account ID
#    - Access Key ID  
#    - Secret Access Key
#    - Endpoint URL: https://<account-id>.r2.cloudflarestorage.com
```

## 3. Backend Deployment (Fly.io)

```bash
# Fly.io CLI インストール
curl -L https://fly.io/install.sh | sh

# ログイン
flyctl auth login

# プロジェクトルートで初期化
flyctl apps create emoguchi-backend

# シークレット設定
flyctl secrets set DATABASE_URL="postgresql://..." \
  OPENAI_API_KEY="sk-..." \
  R2_ENDPOINT_URL="https://<account-id>.r2.cloudflarestorage.com" \
  R2_ACCOUNT_ID="your-account-id" \
  AWS_ACCESS_KEY_ID="your-r2-access-key" \
  AWS_SECRET_ACCESS_KEY="your-r2-secret-key" \
  S3_BUCKET="emoguchi-audio"

# デプロイ
flyctl deploy

# ログ確認
flyctl logs
```

## 4. Frontend Deployment (Cloudflare Pages)

```bash
# 1. GitHub リポジトリと連携
# 2. Cloudflare Pages でプロジェクト作成
# 3. ビルド設定:
#    - Build command: npm run build
#    - Output directory: out
#    - Root directory: frontend

# 4. 環境変数設定:
NEXT_PUBLIC_BACKEND_URL=https://emoguchi-backend.fly.dev
```

## 5. Database Migration

```bash
# Alembic マイグレーション実行（初回のみ）
flyctl ssh console
cd /app
alembic upgrade head
exit
```

## 6. スケーリング設定

```bash
# Scale-to-zero 設定確認
flyctl scale count 0 --region nrt

# オートスケール設定
flyctl autoscale set min=0 max=3
```

## 7. モニタリング

```bash
# アプリケーション状態確認
flyctl status

# メトリクス確認
flyctl metrics

# ログ監視
flyctl logs -f
```

## コスト最適化

- **Fly.io**: Scale-to-zero で使用時のみ課金
- **Neon**: Free tier で月5GB まで無料
- **Cloudflare R2**: 10GB ストレージ無料
- **Cloudflare Pages**: 無制限ビルド・デプロイ無料

## トラブルシューティング

### 1. Backend起動失敗
```bash
flyctl logs
# ML モデルのダウンロード確認
# 環境変数の設定確認
```

### 2. Frontend接続エラー
```bash
# CORS 設定確認
# Backend URL 確認
```

### 3. Audio upload失敗
```bash
# R2 設定確認
# ファイルサイズ制限確認
```