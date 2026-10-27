# RenderにFastAPIバックエンドを公開する手順

このリポジトリでは、フロントエンドを既存のCloudflare Pagesで公開し、FastAPIバックエンドだけをRenderで公開します。

## 事前準備

- GitHubにこのリポジトリをpushできる状態にする
- Sony Prediction OneのAPIキーを用意する
- Cloudflare Pagesで現在公開しているフロントエンドのOriginを確認する

Originは、ブラウザでフロントエンドを開いたときの次の部分です。

```text
https://実際のCloudflare公開ドメイン
```

パス（`/login` など）や末尾のスラッシュは含めません。実際のドメインは推測せず、Cloudflare Pagesの画面またはブラウザのアドレスバーで確認してください。

## Renderでバックエンドを作成する

1. RenderにGitHubアカウントでログインします。
2. `New` → `Blueprint` を選択します。
3. このリポジトリを選択し、リポジトリ内の `render.yaml` を読み込みます。
4. FastAPIサービスの内容を確認して作成します。

このBlueprintでは、FastAPIサービスだけが作成されます。フロントエンドは既存のCloudflare Pagesを使うため、Render上にStatic Siteは作成しません。

APIサービスのEnvironmentに、次の値を設定します。

```text
SONY_API_KEY=Sony Prediction OneのAPIキー
CORS_ORIGINS=Cloudflareで確認した実際の公開Origin
```

`SONY_API_KEY` はRenderのEnvironmentにだけ設定してください。ソースコード、GitHub、Cloudflare Pagesの環境変数には設定しません。

## Renderの実際のURLを確認する

1. Render DashboardでFastAPIサービスを開きます。
2. サービス画面に表示される公開URLをコピーします。
3. URLは推測せず、Renderが表示した値を使用します。

コピーしたURLの末尾に `/health` を付けてブラウザで開きます。

```text
https://Renderが表示した実際のバックエンドURL/health
```

次のレスポンスが表示されれば、バックエンドは起動しています。

```json
{"status":"ok"}
```

## Cloudflare Pagesからバックエンドへ接続する

Cloudflare Pagesの対象プロジェクトで、Environment variablesに次の変数を追加します。

```text
VITE_API_BASE_URL=Renderが表示した実際のバックエンドURL
```

`/health` は付けません。RenderのURLそのものを設定します。

また、Render APIサービスの `CORS_ORIGINS` には、Cloudflare Pagesで確認した実際のOriginを設定します。Cloudflareで複数の公開Originを使う場合は、カンマ区切りで設定できます。

```text
https://実際のCloudflare公開ドメイン,https://別の実際の公開Origin
```

環境変数を変更しただけでは、すでに生成されたフロントエンドには反映されません。Cloudflare Pagesで新しいデプロイを開始するか、GitHub連携の再ビルドを実行してください。デプロイ完了後、スマートフォンでCloudflareの公開URLを開いて確認します。

## 確認項目

- Renderの `/health` が `{"status":"ok"}` を返す
- Cloudflare Pagesのビルド環境変数 `VITE_API_BASE_URL` がRenderの実URLになっている
- Render APIサービスの `CORS_ORIGINS` がCloudflareの実際のOriginになっている
- Cloudflare Pagesを環境変数変更後に再ビルド・再デプロイした
- スマートフォンからルーム作成、ルーム参加、診断を確認する

## ローカル開発

ローカルでは、`.env.example` を参考に `.env` を用意します。ローカルのAPI URLは次のまま使用できます。

```text
VITE_API_BASE_URL=http://127.0.0.1:8000
```

バックエンドは次で起動します。

```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

フロントエンドは別のターミナルで起動します。

```bash
npm install
npm run dev
```

## データ保存について

RenderのAPIサービスにはPersistent Diskを接続し、SQLiteの保存先を `/var/data/rooms.db` にしています。SQLiteを使用しているため、APIサービスを複数インスタンスへ拡張する構成にはしていません。将来複数インスタンスが必要になった場合は、共有データベースへの移行が必要です。
