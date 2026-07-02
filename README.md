# あなただけの今日の星よみ

LINE公式アカウントのリッチメニューから開ける、LIFF対応の星よみWebアプリです。外部AIサービスや星よみ処理キーは使わず、アプリ内の計算と文章生成だけで結果を作ります。

## ファイル構成

- `frontend/index.html`: 入力画面と結果画面
- `backend/main.py`: 画面配信と星よみ処理
- `backend/engine.py`: 星まわりの計算ロジック
- `backend/translator.py`: 結果文の生成
- `requirements.txt`: Render/Railwayが使うPythonライブラリ
- `render.yaml`: Render用の設定
- `Procfile`: Railway用の起動設定

## 1. ZIPをGitHubにアップロードする

1. GitHubで新しいリポジトリを作ります。
2. `Hoshiyomi`フォルダを開き、中のファイルをすべて選びます。
3. GitHubの「Add file」からアップロードします。
4. `Commit changes`を押します。

`Hoshiyomi`フォルダそのものを丸ごと入れるのではなく、フォルダの中身をアップロードしてください。

## 2. Renderでデプロイする

1. Renderで「New」から「Blueprint」を選びます。
2. GitHubのリポジトリを選びます。
3. `render.yaml`が読まれたら、そのまま作成します。
4. 初回だけ環境変数 `LIFF_ID` に `temp` と入れておきます。
5. デプロイが終わると、`https://...onrender.com` のURLが発行されます。

## 3. Railwayでデプロイする場合

1. Railwayで「New Project」を作ります。
2. GitHubリポジトリを選びます。
3. 自動で `Procfile` が使われます。
4. 環境変数に `LIFF_ID=temp` を入れます。
5. 発行されたHTTPS URLを控えます。

## 4. LINE Developersでチャネルを作る

1. LINE Developersを開きます。
2. プロバイダーを作成します。
3. 「LINEログイン」チャネルを作成します。
4. チャネルを「開発中」から「公開済み」に切り替えます。

LIFFはMessaging 星よみ処理チャネルではなく、LINEログインチャネル側で作ります。

## 5. LIFFアプリを作る

1. LINEログインチャネルの「LIFF」タブを開きます。
2. 「追加」を押します。
3. Endpoint URLにRenderまたはRailwayのHTTPS URLを入れます。
4. Sizeは `Full` を選びます。
5. 作成後に表示されるLIFF IDをコピーします。

Endpoint URLの例:

```text
https://your-app.onrender.com
```

## 6. LIFF IDをRenderに設定する

1. RenderまたはRailwayの環境変数を開きます。
2. `LIFF_ID` の値を、コピーしたLIFF IDに変更します。
3. もう一度デプロイします。

LIFF URLは次の形になります。

```text
https://liff.line.me/あなたのLIFF_ID
```

## 7. LINE公式アカウントのリッチメニューに設定する

1. LINE Official Account Managerを開きます。
2. リッチメニューを作成します。
3. タップ領域のアクションを「リンク」にします。
4. URLに `https://liff.line.me/あなたのLIFF_ID` を入れます。
5. 保存して公開します。

## 8. 動作確認

1. 自分のLINEで公式アカウントを開きます。
2. リッチメニューをタップします。
3. LINE内でアプリが開くことを確認します。
4. 生年月日を入れて「今日の星をよむ」を押します。
5. 結果文と「現在の星の動き」が表示されれば完了です。

Renderの無料プランでは、久しぶりのアクセス時に起動まで少し待つことがあります。

