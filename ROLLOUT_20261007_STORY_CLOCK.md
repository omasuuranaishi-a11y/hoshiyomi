# Instagram定刻運用（2026-10-07開始）

承認済みの投稿時刻は日本時間04:00「今日の月と星」、05:00「12星座 きょうの運勢」、17:00「おますの占い大辞典」。

2026-10-06のGitHub scheduleは01:43予定が07:55に開始した。予約イベントへの依存を減らすため、Instagram Story Clockが稼働中のGitHubランナーから15分前に既存投稿ワークフローを直接dispatchする。投稿ジョブは4分前にRenderを起動し、指定時刻まで待機する。Instagram側の画像処理と公開には追加の数十秒がかかる。

- 時計は170分で終了し、GITHUB_TOKENのworkflow_dispatchで後続を起動する。各ジョブ上限は180分。cronは時計停止後の再起動用。
- 公開リポジトリの標準Ubuntuランナーを使用する。Render CronやローカルPCのタイマーは使用しない。
- 開始日は2026-10-07。時計は経過済み時刻の投稿を追加しない。
- 既存投稿ワークフローの直列化とGitHub永続投稿済み印を使い、force_repost=falseを固定する。
- すでに投稿済み、同じ時計リクエストが存在、投稿処理が実行中の場合は再送しない。APIの公開結果が不明な場合も再送しない。
- 投稿失敗後の復旧は、ログ・投稿済み印・利用可能なInstagram証拠で未投稿が明確な場合に限り、監視タスクから既存ワークフローを一度実行する。
- 時計の検証モードverifyは翌日3枠のプレビューだけを生成し、handoff-checkへの起動を確認する。Instagramへ投稿しない。

## 稼働確認と停止

gh run list --repo omasuuranaishi-a11y/hoshiyomi --workflow instagram-story-clock.yml
gh run view RUN_ID --repo omasuuranaishi-a11y/hoshiyomi --log

停止時はまず時計ワークフローをdisableし、その後、実行中・待機中の時計をcancelする。投稿も停止する依頼ならdaily-instagram-story.ymlをdisableし、待機中の投稿ジョブもcancelする。ユーザーの停止依頼なしに停止しない。

初回起動:
gh workflow run instagram-story-clock.yml --repo omasuuranaishi-a11y/hoshiyomi --ref main -f mode=live

新しい作業コピーは C:/Users/yoshi/Hoshiyomi_Instagram_live_20261006。旧コピーも保持している。制約下のGit確認は不完全だったが、実環境では旧コピーも正常と確認済み。

