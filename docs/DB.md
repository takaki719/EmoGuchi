# 📦 データベース設計まとめ（2025年6月版）

## ✅ セッションベース識別について

このアプリではユーザー登録を行わず、各ユーザーを `localStorage` に保存された UUID で一意に識別します。これにより、ユーザー管理テーブルは不要になり、匿名性を保ちつつユーザーを区別できます。

---

## ✅ 1. modes（モード）

| カラム名        | 型    | 説明              |
| ----------- | ---- | --------------- |
| id          | UUID | モードID (PK)      |
| name        | TEXT | モード名（例: normal） |
| description | TEXT | モードの説明（感情や答え方）  |

### 📘 補足: advanced モード（プルチックの感情の輪モード）

* `name`: `advanced`
* `description`: プルチックの感情の輪を提示し、選択肢なしでリスナーが自由に感情を選択して当てる形式。
* UI上で視覚的な感情選択ホイールを提供。
* 選択された感情は `emotion_votes.selected_emotion_id` に登録。

---

## ✅ 2. emotion\_types（感情タイプ）

| カラム名 | 型    | 説明            |
| ---- | ---- | ------------- |
| id   | UUID | 感情ID (PK)     |
| name | TEXT | 感情名（例: 喜び、怒り） |

※ プルチックの感情の輪に対応する感情（例: 喜び、恐怖、信頼、驚き 等）を登録しておく。

---

## ✅ 3. chat\_sessions（1プレイ全体をまとめる単位）

| カラム名        | 型         | 説明            |
| ----------- | --------- | ------------- |
| id          | UUID      | セッションID (PK)  |
| session\_id | UUID      | ブラウザごとの一意識別子  |
| mode\_id    | UUID      | modes.id 外部キー |
| created\_at | TIMESTAMP | セッション開始日時     |

---

## ✅ 4. rounds（ラウンド：1セリフ・1スピーカー単位）

| カラム名              | 型         | 説明                       |
| ----------------- | --------- | ------------------------ |
| id                | UUID      | ラウンドID (PK)              |
| session\_id       | UUID      | 発話者セッションID               |
| chat\_session\_id | UUID      | chat\_sessions.id 外部キー   |
| prompt\_text      | TEXT      | GPTで生成した or 選ばれたセリフ      |
| emotion\_id       | UUID      | 正解の感情（emotion\_types.id） |
| created\_at       | TIMESTAMP | ラウンド開始時刻                 |

---

## ✅ 5. recordings（録音された音声）

| カラム名         | 型         | 説明                  |
| ------------ | --------- | ------------------- |
| id           | UUID      | 録音ID (PK)           |
| round\_id    | UUID      | rounds.id 外部キー      |
| audio\_url   | TEXT      | 音声ファイルの保存URL        |
| duration     | FLOAT     | 音声長（秒）              |
| session\_id  | UUID      | 録音者のセッションID         |
| prompt\_hint | TEXT      | 音声変換をする場合のプロンプト（予備） |
| created\_at  | TIMESTAMP | 録音日時                |

---

## ✅ 6. emotion\_votes（感情当て投票）

| カラム名                  | 型         | 説明                         |
| --------------------- | --------- | -------------------------- |
| id                    | UUID      | 投票ID (PK)                  |
| round\_id             | UUID      | rounds.id 外部キー             |
| session\_id           | UUID      | 投票者のセッションID                |
| selected\_emotion\_id | UUID      | 選択された感情（emotion\_types.id） |
| is\_correct           | BOOLEAN   | 正解と一致したか（バックエンドで自動評価）      |
| created\_at           | TIMESTAMP | 投票時刻                       |

---

## ✅ 7. scores（得点履歴）

| カラム名        | 型         | 説明             |
| ----------- | --------- | -------------- |
| id          | UUID      | スコアID (PK)     |
| session\_id | UUID      | 一意ユーザー識別子      |
| round\_id   | UUID      | rounds.id 外部キー |
| points      | INT       | 得点             |
| created\_at | TIMESTAMP | 記録時刻           |

---

## 📊 正答率の計算

### 🍻 リスナー正答率（セッションID別）

```sql
SELECT
  session_id,
  COUNT(*) AS total_votes,
  SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) AS correct_votes,
  ROUND(SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) * 1.0 / COUNT(*), 2) AS accuracy
FROM emotion_votes
GROUP BY session_id;
```

### 🚩 スピーカー正答率（セッションID別）

```sql
SELECT
  r.session_id AS speaker_session_id,
  COUNT(v.id) AS total_votes_received,
  SUM(CASE WHEN v.selected_emotion_id = r.emotion_id THEN 1 ELSE 0 END) AS correct_votes_received,
  ROUND(SUM(CASE WHEN v.selected_emotion_id = r.emotion_id THEN 1 ELSE 0 END) * 1.0 / COUNT(v.id), 2) AS speaker_accuracy
FROM rounds r
JOIN emotion_votes v ON r.id = v.round_id
GROUP BY r.session_id;
```

---

## ✅ この設計の特徴

| 機能            | 対応状況                                 |
| ------------- | ------------------------------------ |
| モード切替・柔軟性     | ✅ `modes` の単純管理で十分対応（advanced モード含む） |
| 音声録音・再生       | ✅ `recordings` テーブルで保存・配信            |
| 感情ラベル管理       | ✅ `emotion_types` で拡張可能（プルチック感情対応）   |
| 投票・正誤記録       | ✅ `emotion_votes` にて一括管理             |
| リスナー・スピーカー正答率 | ✅ 集計SQLにて自動算出可能                      |
| 得点制           | ✅ `scores` テーブルで任意実装可能               |
