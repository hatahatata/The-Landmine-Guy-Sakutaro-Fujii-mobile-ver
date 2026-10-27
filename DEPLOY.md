# Render に FastAPI バックエンドを公開する手順

このリポジトリでは、フロントエンドを既存の Cloudflare Pages で公開し、FastAPI バックエンドだけを Render の無料 Web Service で公開します。

## 無料プランの制約

- `render.yaml` は `plan: free` を使用します。
- Persistent Disk や有料データベースは使用しません。
- ルーム情報は SQLite に一時保存します。Render の無料サービスではファイルシステムの永続保存が保証されないため、再起動、再デプロイ、インスタンス交換などで `/tmp/rooms.db` が消える可能性があります。
- データが消えても、アプリケーションは空の SQLite データベースを作成して起動できます。新しいルームは作成できますが、消失前のルーム ID・招待コードは利用できず、既存ルームへの参加や診断の継続には新しいルームの作成が必要です。
- ルーム情報のバックアップ、永続保存、複数インスタンス間での共有はこの無料構成では実現できません。
- Render の無料サービスはスリープすることがあるため、スマートフォンから最初のアクセス時に起動待ちが発生する場合があります。

## 事前準備

1. GitHub にこのリポジトリを push できる状態にします。
2. Sony Prediction One の API キーを準備します。
3. Cloudflare Pages で現在公開しているフロントエンドの実際の Origin を確認します。

Origin は通常、ブラウザで Cloudflare Pages を開いたときの URL のうち、パスを除いた部分です。例:

```text
https://example.pages.dev
```

## Render でバックエンドを作成する

1. Render に GitHub アカウントでログインします。
2. `New` → `Blueprint` を選択します。
3. このリポジトリを選択し、リポジトリ内の `render.yaml` を読み込みます。
4. FastAPI Web Service の内容を確認して作成します。

この Blueprint では FastAPI Web Service だけが作成されます。既存の Cloudflare Pages 用 Static Site や、有料データベースは作成しません。

## Render の環境変数

Render Dashboard の対象サービスの Environment に次を設定します。

```text
SONY_API_KEY=Sony Prediction One の API キー
CORS_ORIGINS=https://実際のCloudflare PagesのOrigin
```

`SONY_API_KEY` は Render の Environment にだけ設定してください。ソースコード、GitHub、Cloudflare Pages の環境変数、フロントエンドのコードには設定しません。

`CORS_ORIGINS` に複数の Origin を許可する場合は、カンマ区切りで指定できます。

```text
https://example.pages.dev,https://another.example.com
```

SQLite の保存先は `render.yaml` で `/tmp/rooms.db` に設定済みです。これは無料サービス上の一時ファイルであり、永続保存先ではありません。

## Render の URL を確認する

1. Render Dashboard で FastAPI サービスを開きます。
2. Render が表示するサービス URL をコピーします。URL は推測しません。
3. URL の末尾に `/health` を付けてブラウザで開きます。

```text
https://Renderが表示した実際のバックエンドURL/health
```

次のレスポンスが表示されればバックエンドは起動しています。

```json
{"status":"ok"}
```

起動コマンドは次の設定を維持しています。

```text
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

`$PORT` は Render が設定する値を使用し、ヘルスチェックは `/health` です。

## Cloudflare Pages と接続する

Cloudflare Pages の対象プロジェクトの Environment variables に次を設定します。

```text
VITE_API_BASE_URL=Renderが表示した実際のバックエンドURL
```

`/health` や `/` は付けず、Render の URL そのものを設定します。設定変更後は Cloudflare Pages で再ビルド・再デプロイします。

同時に、Render の `CORS_ORIGINS` には Cloudflare Pages の実際の Origin を設定します。両者は次の関係になります。

```text
Cloudflare Pages: VITE_API_BASE_URL = Render の API URL
Render:           CORS_ORIGINS       = Cloudflare Pages の Origin
```

## 動作確認

- Render の `/health` が `{"status":"ok"}` を返す
- Cloudflare Pages のビルド環境変数 `VITE_API_BASE_URL` が Render の実 URL になっている
- Render の `CORS_ORIGINS` が Cloudflare Pages の実際の Origin になっている
- スマートフォンからルームを作成できる
- 別のスマートフォンまたはブラウザから招待コードで参加できる
- 診断を実行できる

無料プランで DB ファイルが消えた場合は、既存ルームへのアクセスが `404 Room not found` になります。その場合は新しいルームを作成してください。バックエンドの `/health` や新規ルーム作成自体は継続して利用できます。

## ローカル開発

`.env.example` を参考に `.env` を作成します。ローカルのフロントエンドは次の API URL を使用します。

```text
VITE_API_BASE_URL=http://127.0.0.1:8000
```

バックエンド:

```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

フロントエンド:

```bash
npm install
npm run dev
```

ローカルでは `ROOMS_DB_PATH=backend/rooms.db` を使用できます。`backend/rooms.db` は `.gitignore` で管理対象外です。
