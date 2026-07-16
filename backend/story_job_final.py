from __future__ import annotations

import argparse
import json

from .story_automation_final import run_daily_story


def main() -> None:
    parser = argparse.ArgumentParser(description="おます Instagramストーリー完全自動化")
    parser.add_argument("--date", help="対象日（YYYY-MM-DD）。省略時は日本時間の今日。")
    parser.add_argument("--publish", action="store_true", help="Instagramへ実投稿する。")
    parser.add_argument("--offline", action="store_true", help="確認用の簡易文章を使う。")
    parser.add_argument("--force", action="store_true", help="同日の完了記録があっても再実行する。")
    args = parser.parse_args()
    result = run_daily_story(
        args.date,
        dry_run=not args.publish,
        offline=args.offline,
        force=args.force,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
