#!/bin/bash

# EMOGUCHI 開発サーバー起動スクリプト

echo "🎭 EMOGUCHI 開発環境を起動中..."

# 既存のプロセスを停止
echo "🧹 既存のプロセスをクリーンアップ中..."
pkill -f "uvicorn.*main" 2>/dev/null || true
pkill -f "npm.*dev" 2>/dev/null || true
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true

# 少し待機
sleep 2

# バックエンドをデバッグモードで起動
echo "📡 バックエンドサーバーを起動中（デバッグログ有効）..."
cd backend

# バックエンドの起動確認
if [ ! -f "main.py" ]; then
    echo "❌ エラー: backend/main.py が見つかりません"
    exit 1
fi

# デバッグレベルでバックエンドを起動
python3 -m uvicorn main:socket_app --reload --host 0.0.0.0 --port 8000 --log-level info &
BACKEND_PID=$!

# バックエンドの起動を確認
echo "⏳ バックエンドの起動を確認中..."
for i in {1..10}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ バックエンドが正常に起動しました"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "❌ バックエンドの起動に失敗しました"
        kill $BACKEND_PID 2>/dev/null
        exit 1
    fi
    sleep 1
done

# フロントエンドを起動
echo "🌐 フロントエンドサーバーを起動中..."
cd ../frontend

# フロントエンドの起動確認
if [ ! -f "package.json" ]; then
    echo "❌ エラー: frontend/package.json が見つかりません"
    kill $BACKEND_PID
    exit 1
fi

npm run dev &
FRONTEND_PID=$!

# フロントエンドの起動を確認
echo "⏳ フロントエンドの起動を確認中..."
for i in {1..15}; do
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo "✅ フロントエンドが正常に起動しました"
        break
    fi
    if [ $i -eq 15 ]; then
        echo "⚠️  フロントエンドの起動確認がタイムアウトしました（通常は問題ありません）"
        break
    fi
    sleep 2
done

echo ""
echo "🎉 EMOGUCHI 開発環境が起動しました！"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌐 フロントエンド: http://localhost:3000"
echo "📡 バックエンド API: http://localhost:8000"
echo "🔍 バックエンド ヘルスチェック: http://localhost:8000/health"
echo "📊 バックエンドログ: このターミナルで確認可能"
echo "🌐 フロントエンドログ: ブラウザのDevTools > Console"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 トラブルシューティング:"
echo "   - バックエンドエラー: このターミナルのログを確認"
echo "   - フロントエンドエラー: ブラウザのConsoleを確認"
echo "   - ポート競合: スクリプトが自動的にクリーンアップします"
echo ""
echo "🛑 停止するには Ctrl+C を押してください"

# 終了シグナルをキャッチして両方のプロセスを停止
cleanup() {
    echo ""
    echo "🛑 サーバーを停止中..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    pkill -f "uvicorn.*main" 2>/dev/null || true
    pkill -f "npm.*dev" 2>/dev/null || true
    echo "✅ すべてのプロセスが停止されました"
    exit 0
}

trap cleanup INT TERM

# プロセスを待機
wait