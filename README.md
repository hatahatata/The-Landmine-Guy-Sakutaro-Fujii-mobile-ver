# 🎓 成績ランクAI診断アプリ

既存の Python 製アプリを、UI を刷新した Svelte + TypeScript の Web アプリとして再構成したプロジェクトです。

## 目的

- 既存の `app.py` の入力項目・初期値・API 入力列名・診断ロジックを維持
- UI をモダンなダッシュボード風に刷新
- API キーをブラウザへ露出せず、Python バックエンド側で保持して予測 API にアクセス

## 主要機能

- 10 項目の学生ライフスタイル入力
- 4 段階の成績ランク診断
- 4 つのランク別予測確率表示
- 通信エラー時の表示
- ダッシュボード風のレイアウト

## 技術スタック

- Svelte 5
- TypeScript
- Vite
- Python 3.14
- FastAPI
- Sony Prediction One API

## 実行手順

### 1. フロントエンド依存をインストール

```bash
npm install
```

### 2. バックエンド依存をインストール

```bash
python -m pip install -r requirements.txt
```

### 3. バックエンドを起動

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. フロントエンドを起動

```bash
npm run dev
```

ブラウザで `http://127.0.0.1:5173` にアクセスします。

スマートフォンからアクセスする場合は、PC と同じ Wi-Fi に接続し、PC の IP アドレスを使って `http://<PCのIPアドレス>:5173` を開きます。ルーム API は既定で、開いているページと同じホストのポート `8000` に接続します。API が別のホストにある場合は、フロントエンドの `.env` に `VITE_API_BASE_URL=http://<APIのホスト>:8000` を設定してください。

## API 連携について

- 既存の Sony Prediction One API を利用
- API キーはフロントエンドではなく Python バックエンド側に保持
- 送信する列名は以下を維持
  - `StudyHours`
  - `Attendance`
  - `Resources`
  - `Motivation`
  - `Internet`
  - `Gender`
  - `Age`
  - `Discussions`
  - `AssignmentCompletion`
  - `EduTech`

## 既存アプリとの整合性

- タイトルと説明は既存の意味を維持
- 入力項目、初期値、選択肢、範囲は維持
- 予測 API の呼び出し形式とレスポンス処理を既存実装に合わせている
- 診断結果メッセージと確率の表現は既存の内容を保持
