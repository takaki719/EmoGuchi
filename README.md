# 🎭 EMOGUCHI - 音声演技 × 感情推定ゲーム

リアルタイム音声演技と感情推定を楽しむパーティゲームです。

開始画面
<img width="1463" alt="image" src="https://github.com/user-attachments/assets/0b627c1d-87b8-429d-979a-a8f216777006" />  
ゲーム画面(スピーカー)
<img width="931" alt="image" src="https://github.com/user-attachments/assets/eaa9a60e-f9c6-429d-82d8-3ab6293814da" />  
ゲーム画面(リスナー)  
<img width="918" alt="image" src="https://github.com/user-attachments/assets/691536fc-dc1a-444a-9fe4-0bcd32735eec" />  


## 🎮 ゲーム概要

プレイヤーは順番にスピーカーとなり、指定されたセリフを感情を込めて読み上げます。他のプレイヤーはその感情を推測して投票し、スコアを競います。

### ゲームモード
- **基本モード**: 8種類の基本感情（喜び、怒り、悲しみ、驚き、期待、嫌悪、恐れ、信頼）
- **応用モード**: 24種類の複合感情（楽観、愛、絶望、羨望など） 
### ゲームフロー

1. **ルーム作成/参加**: プレイヤーがルームを作成または参加
2. **ラウンド開始**: ホストがラウンドを開始
3. **セリフ生成**: LLM が感情とセリフを生成
4. **演技フェーズ**: スピーカーがセリフを感情込みで読み上げ
5. **投票フェーズ**: リスナーが感情を推測して投票
6. **結果発表**: 正解と得点を表示
  
### 点数形式  
  
- **スピーカー**: 正解したリスナー数 × 1pt
- **リスナー**: 正解で +1pt

## 🛠️ 技術スタック

### Backend
- **FastAPI** - REST API & WebSocket サーバー
- **Socket.IO** - リアルタイム通信
- **Pydantic** - データバリデーション
- **OpenAI API** - セリフ生成

### Frontend
- **Next.js 14** - React フレームワーク
- **TypeScript** - 型安全性
- **Tailwind CSS** - スタイリング
- **Zustand** - 状態管理
- **Socket.IO Client** - リアルタイム通信

## 🚀 開発環境セットアップ

### 必要環境
- Docker & Docker Compose
- Node.js 18+ (ローカル開発の場合)
- Python 3.11+ (ローカル開発の場合)

### Docker を使用した起動

1. リポジトリをクローン
```bash
git clone <repository-url>
cd emoguchi
```

2. 環境変数ファイルを作成
```bash
cp .env.example .env
# .env ファイルを編集して OpenAI API キーを設定
```

3. Docker Compose で起動
```bash
docker-compose up --build
```

4. ブラウザでアクセス
- フロントエンド: http://localhost:3000
- バックエンド API: http://localhost:8000
- API ドキュメント: http://localhost:8000/docs

### ローカル開発

#### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:socket_app --reload --host 0.0.0.0 --port 8000
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

## 開発コマンド

### Backend
- `uvicorn main:socket_app --reload` - 開発サーバー起動
- `python -m pytest` - テスト実行 (実装時)

### Frontend
- `npm run dev` - 開発サーバー起動
- `npm run build` - プロダクションビルド
- `npm run lint` - ESLint 実行
- `npm run type-check` - TypeScript 型チェック

## 🏗️ アーキテクチャ

### API エンドポイント
- `POST /api/v1/rooms` - ルーム作成
- `GET /api/v1/rooms/{room_id}` - ルーム状態取得
- `DELETE /api/v1/rooms/{room_id}` - ルーム削除 (ホストのみ)
- `POST /api/v1/rooms/{room_id}/prefetch` - セリフ事前生成
- `GET /api/v1/debug/rooms` - 全ルーム一覧 (デバッグ用)

### WebSocket イベント
- `join_room` - ルーム参加
- `start_round` - ラウンド開始
- `submit_vote` - 投票送信
- `round_result` - 結果発表

## 設定

### 環境変数
- `OPENAI_API_KEY`: OpenAI API キー (セリフ生成用)
- `DEBUG_API_TOKEN`: デバッグAPI用トークン
- `NEXT_PUBLIC_API_URL`: フロントエンドからのAPI URL

### ゲーム設定
- 最大プレイヤー数: 8名
- 投票タイムアウト: 30秒

## デプロイ🚀 

### フロントエンド
```bash
cd frontend
npm run build
# Vercel にデプロイ
```

### バックエンド
```bash
cd backend
# (Railway/Render/Fly.io等) を使用してデプロイ
```
