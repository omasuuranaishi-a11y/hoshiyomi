# Instagramストーリー完全自動化 設定ガイド

## 完成している処理

毎朝、次の処理を人の操作なしで実行します。

1. Swiss Ephemerisで当日7:00（日本時間）の実天体位置を計算
2. 月のサイン、月相、月のサイン移動時刻、主要アスペクトを抽出
3. 月・太陽・水星・金星・火星を日運向けに優先
4. OpenAI APIで「おます」調の3枚分の文章を構造化生成
5. 1080×1920pxのJPEGを3枚生成
6. 公開HTTPS URLからMeta公式APIへ渡す
7. Instagramストーリーへ3枚を順番に投稿
8. 同日の二重投稿を防ぎ、途中失敗時は未投稿分から再開

Canvaは使いません。現在の生成り、くすみパープル、ゴールドの雰囲気をコードで再現するため、毎朝Canvaへ貼る作業がなくなります。

## 本番で使うファイル

- `backend/automation_main_final.py`: Web APIの起動先
- `backend/story_automation_final.py`: 全体の実行制御
- `backend/story_sky_daily.py`: 日運向け天体計算
- `backend/story_copy.py`: OpenAIによる文章生成
- `backend/story_renderer_final.py`: 3枚の画像生成
- `backend/instagram.py`: Meta公式APIへの投稿
- `requirements-instagram.txt`: Python依存関係
- `.github/workflows/daily-instagram-story.yml`: 毎朝7時の実行

`render-final.yaml`はRender設定の見本です。既存のHoshiyomiサービスへ重ねる場合は、Render画面で下記のBuild CommandとStart Commandを設定します。

## 1. Meta側の一度だけの設定

Meta for DevelopersでBusinessタイプのアプリを作り、Instagram投稿権限を付けます。

Instagram Loginを使う場合:

- 権限: `instagram_business_basic`
- 権限: `instagram_business_content_publish`
- APIホスト: `https://graph.instagram.com`

Facebookページ経由を使う場合:

- 権限: `pages_show_list`
- 権限: `instagram_basic`
- 権限: `instagram_content_publish`
- 権限: `pages_read_engagement`
- APIホスト: `https://graph.facebook.com`

自分のアカウントだけを運用する場合は、Metaのアプリへ自分のInstagramビジネスアカウントをテスターまたは管理対象として追加します。発行したトークンはGitHubへ書かず、RenderのSecret環境変数だけに保存してください。

長期運用では、Meta Business Managerのシステムユーザー経由で発行し、Token Debuggerで有効期限を確認する方法が安定します。期限付きトークンを使う場合は期限前に再認証が必要です。

公式資料:

- https://www.postman.com/meta/instagram/documentation/6yqw8pt/instagram-api
- https://www.postman.com/meta/instagram/request/23987686-f4b5a72d-a125-4080-8968-93de1a549e68
- https://www.postman.com/meta/instagram/request/23987686-299b176b-90aa-4d8a-b6cf-e6028fc69de5

## 2. OpenAI APIキー

OpenAI PlatformでAPIキーを1本作り、Renderの `OPENAI_API_KEY` に設定します。コードやGitHubへ貼り付けないでください。

文章はResponses APIのStructured Outputsを使用します。モデルは初期値を `gpt-5.6-luna` にしていますが、Renderの `OPENAI_MODEL` だけで変更できます。

公式資料:

- https://developers.openai.com/api/docs/guides/text
- https://developers.openai.com/api/docs/guides/structured-outputs
- https://developers.openai.com/api/docs/models

## 3. Render設定

既存サービスの設定を次の値へ変更します。

Build Command:

```text
pip install -r requirements-instagram.txt
```

Start Command:

```text
uvicorn backend.automation_main_final:app --host 0.0.0.0 --port $PORT
```

Renderの環境変数:

| 名前 | 値 |
|---|---|
| `OPENAI_API_KEY` | OpenAIのAPIキー |
| `OPENAI_MODEL` | `gpt-5.6-luna` |
| `INSTAGRAM_USER_ID` | InstagramプロアカウントID |
| `INSTAGRAM_ACCESS_TOKEN` | Metaのアクセストークン |
| `INSTAGRAM_API_VERSION` | `v25.0` |
| `INSTAGRAM_GRAPH_BASE_URL` | 選んだログイン方式のAPIホスト |
| `PUBLIC_BASE_URL` | Renderの公開URL。末尾スラッシュなし |
| `AUTOMATION_SECRET` | 32文字以上のランダム文字列 |
| `STORY_TIMEZONE` | `Asia/Tokyo` |
| `ALLOW_FALLBACK_COPY` | `false` |
| `ERROR_WEBHOOK_URL` | 任意。失敗通知先Webhook |

`ALLOW_FALLBACK_COPY=false` により、OpenAI APIが失敗した日は質の低い文章を勝手に投稿せず、投稿を停止します。

## 4. GitHub Actionsの毎朝7時設定

リポジトリの Settings → Secrets and variables → Actions に、次の2つを追加します。

| Secret | 値 |
|---|---|
| `AUTOMATION_URL` | `https://RenderのURL/api/automation/daily-story` |
| `AUTOMATION_SECRET` | Renderに設定したものと同じ文字列 |

`.github/workflows/daily-instagram-story.yml` は毎日22:00 UTC、つまり翌朝7:00 JSTに起動します。

## 5. 最初の安全確認

まず `dry_run=true` と `offline=true` で、Instagramへ投稿せず画像だけ生成します。

```bash
curl -X POST \
  -H "Authorization: Bearer あなたのAUTOMATION_SECRET" \
  "https://RenderのURL/api/automation/daily-story?dry_run=true&offline=true&force=true"
```

返ってきた `asset_urls` をブラウザで開き、3枚とも問題がないことを確認します。

OpenAIの文章を含む本番前確認では、`offline=true` だけを外します。初回の実投稿は、画像を確認した後に手動実行してください。

## 安全設計

- 実在する天体位置だけをAIへ渡します。
- 一般向け投稿なので、出生図や架空のハウスは使いません。
- AIには星座やアスペクトを勝手に補完させません。
- 断定、恐怖訴求、医療・金融助言を禁止しています。
- APIキーとMetaトークンは画像・ログ・レスポンスへ出しません。
- 同日の投稿記録がある場合は二重投稿しません。
- 3枚目で失敗した場合は、再実行時に3枚目から再開します。

## Instagram API上の制限

自動投稿画像へ通常の文字や装飾を焼き込むことはできます。Instagramネイティブの投票、質問、音楽、リンクなどの操作可能なスタンプはAPIでは追加できないため、必要な日はInstagramアプリで手動追加します。
