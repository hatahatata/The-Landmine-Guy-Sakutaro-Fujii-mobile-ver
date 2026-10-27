# 公開URLで利用するためのデプロイ手順

この構成は Render でフロントエンドと FastAPI を公開します。設定は [render.yaml](./render.yaml) にまとめています。

## 事前準備

1. GitHub にこのリポジトリを push します。
2. Sony Prediction One の API キーを用意します。
3. Google ログインを使う場合は、Google OAuth のクライアントIDを用意します。
4. 既存ソースにAPIキーが含まれていた場合は、公開前にそのキーを無効化して再発行してください。

## Renderで公開する手順

1. Render に GitHub アカウントでログインします。
2. `New` → `Blueprint` を選び、このリポジトリを指定します。
3. `render.yaml` の内容を確認してデプロイします。
4. APIサービス `landmine-guy-api` の Environment に次を設定します。
   - `SONY_API_KEY`: Sony APIキー
   - `CORS_ORIGINS`: フロントエンドのURL（例: `https://landmine-guy-web.onrender.com`）
5. フロントエンドサービス `landmine-guy-web` の Environment に次を設定します。
   - `VITE_API_BASE_URL`: API URL（例: `https://landmine-guy-api.onrender.com`）
   - `VITE_GOOGLE_CLIENT_ID`: GoogleクライアントID（使用する場合）
6. 両サービスを再デプロイします。
7. `https://landmine-guy-api.onrender.com/health` を開き、`{"status":"ok"}` を確認します。
8. フロントエンドURLを開き、ルーム作成と別ブラウザからの参加を確認します。

## データ保存について

`render.yaml` では API に `/var/data` の Persistent Disk を接続し、`ROOMS_DB_PATH=/var/data/rooms.db` に設定しています。これにより SQLite のルーム情報は再起動・再デプロイ後も保持されます。

この構成では SQLite の都合上、APIサービスを複数インスタンスへスケールしません。複数インスタンスが必要になった場合は、ルームデータを共有PostgreSQLへ移行してください。

## ローカル開発

ローカルでは `.env.example` を `.env` にコピーし、`VITE_API_BASE_URL` と `CORS_ORIGINS` を localhost に設定します。APIは次で起動します。

```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

フロントエンドは次で起動します。

```bash
npm install
npm run dev
```
