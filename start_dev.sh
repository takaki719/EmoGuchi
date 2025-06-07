#!/bin/bash

# EMOGUCHI 開発サーバー起動スクリプト

echo "🎭 EMOGUCHI 開発環境を起動中..."

# バックエンドをバックグラウンドで起動
echo "📡 バックエンドサーバーを起動中..."
cd backend
python3 main.py &
BACKEND_PID=$!

# 少し待機
sleep 3

# フロントエンドを起動
echo "🌐 フロントエンドサーバーを起動中..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

echo "✅ サーバー起動完了！"
echo "🌐 フロントエンド: http://localhost:3000"
echo "📡 バックエンド: http://localhost:8000"
echo ""
echo "停止するには Ctrl+C を押してください"

# 終了シグナルをキャッチして両方のプロセスを停止
trap 'echo "🛑 サーバーを停止中..."; kill $BACKEND_PID $FRONTEND_PID; exit' INT

# プロセスを待機
wait