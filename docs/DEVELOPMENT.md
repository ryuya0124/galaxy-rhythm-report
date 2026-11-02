# 開発ガイド

## 必要なもの

- Node.js 22以上（CIは24）
- Python 3.12以上（追加パッケージ不要、CIは3.13）

## ビルドとローカル表示

```sh
npm ci
npm run build
npm run dev
```

ローカル表示は `http://127.0.0.1:8787/` です。`npm run build` は単一HTML、保存用MD・JSON、レスポンスヘッダーを `dist/` に生成します。

保存用HTMLはCSS・JS・データをすべて内包します。外部CDNやバックエンドへの接続はありません。

## 構成

| パス                         | 内容                                   |
| ---------------------------- | -------------------------------------- |
| `data/judgment-windows.json` | 公開版のアプリ・条件・判定値           |
| `templates/report.html`      | ページ構成                             |
| `templates/report.css`       | PC・スマホ用の表示                     |
| `templates/report.js`        | 検索・絞り込み・判定図・オフライン保存 |
| `scripts/build_report.py`    | HTML・MD・JSONの生成                   |
| `docs/JUDGMENT_WINDOWS.md`   | ビルド時に更新する一覧                 |
| `wrangler.jsonc`             | Cloudflare Workersの静的アセット設定   |

公開版は判定値・条件・バージョンを中心にしています。アプリ本体、逆コンパイル結果、端末ログ、認証情報は含みません。

## データや表示を変更するとき

値と条件はJSON、ゲームの表示順・略号と件数チェックはビルドスクリプト、ページ内の収録数と日付はHTMLテンプレートにあります。新しいゲームやバージョンを追加するときは、これらを合わせて更新してください。

`early_ms` と `late_ms` は非負の半幅です。各要素は同じ位置の `grades` に対応します。0や非単調な幅も意味を持つので、数値を並べ替えたり単調になるよう補正したりしないでください。

```sh
npm run check
npm run build
npx wrangler deploy --dry-run
```

変更後はスマホ幅での表示と横はみ出し、検索、条件切り替え、固定表なしの表示、ダウンロードを確認します。本文16〜17px、一覧の判定値21〜24pxを基準にしています。

## Cloudflare Workersへ公開

初回は自分のCloudflareアカウントで認証し、`wrangler.jsonc` のWorker名を自分の公開先に合わせてください。

```sh
npx wrangler login
npm run deploy
```

アップロードするのは `dist/` だけです。APIトークンやアカウントIDをソースへ書き込む必要はありません。GitHub Actionsはチェックとビルドを実行し、Cloudflareへの自動デプロイは行いません。

`html_handling: none` と `_redirects` の内部転送でトップページと `.html` の保存URLを両立しています。`_headers` のCSPはJSのSHA-256から生成されるため、JSを変えたときも必ず再ビルドしてください。
