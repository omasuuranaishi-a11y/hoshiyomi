"""Exercise the actual publishing shell against a local HTTP stub only."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest


ROOT = Path(__file__).resolve().parents[1]
GIT_BASH = Path(r"C:\Program Files\Git\bin\bash.exe")
BASH = str(GIT_BASH) if GIT_BASH.is_file() else shutil.which("bash")


def publishing_script():
    workflow = (ROOT / ".github/workflows/daily-instagram-story.yml").read_text(encoding="utf-8")
    section = workflow.split("      - name: Generate and publish one story", 1)[1]
    block = section.split("        run: |\n", 1)[1].split("\n      - name:", 1)[0]
    return "\n".join(line[10:] if line.startswith("          ") else line
                     for line in block.splitlines())


@unittest.skipUnless(BASH, "Bash is required to test the GitHub publishing shell")
class WorkflowRuntimeTests(unittest.TestCase):
    def run_stub(self, *, preview, get_statuses=(200,), post_statuses=(200,)):
        seen = {"GET": 0, "POST": 0}
        class Handler(BaseHTTPRequestHandler):
            def reply(self, method, statuses):
                index = seen[method]
                seen[method] += 1
                status = statuses[min(index, len(statuses) - 1)]
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                body = {"status": "dry_run" if preview else "published"} if status == 200 else {"error": "temporary"}
                self.wfile.write(json.dumps(body).encode())
            def do_GET(self):
                self.reply("GET", get_statuses)
            def do_POST(self):
                self.reply("POST", post_statuses)
            def log_message(self, *args):
                pass
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory(prefix="story-workflow-test-") as tmp:
                env = {**os.environ, "PATH": str(Path(sys.executable).parent) + os.pathsep + os.environ.get("PATH", ""),
                       "TZ": "Asia/Tokyo", "AUTOMATION_URL": f"http://127.0.0.1:{server.server_port}/api/automation/daily-story",
                       "AUTOMATION_SECRET": "test-only-token", "SLOT": "morning", "TARGET_DATE": "2026-10-08",
                       "PUBLISH_EPOCH": "0", "DRY_RUN": "true" if preview else "false", "FORCE_REPOST": "false",
                       "MARK_PUBLISHED_ONLY": "false", "NO_PROXY": "127.0.0.1", "no_proxy": "127.0.0.1"}
                # GitHub's default Bash runner exits on the first failed command.
                result = subprocess.run([BASH, "-e", "-c", publishing_script()], cwd=tmp, env=env,
                                        timeout=45, capture_output=True, encoding="utf-8")
                response_file = Path(tmp) / "story-response.json"
                body = response_file.read_text() if response_file.exists() else None
                marker = (Path(tmp) / ".story-published/2026-10-08-morning.done").exists()
                return result, seen, body, marker
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_preview_retries_502_and_response_file_contains_one_json(self):
        result, seen, body, marker = self.run_stub(preview=True, post_statuses=(502, 200))
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(seen, {"GET": 1, "POST": 2})
        self.assertEqual(json.loads(body), {"status": "dry_run"})
        self.assertFalse(marker)

    def test_publishing_post_is_not_retried_when_result_is_unknown(self):
        result, seen, _, marker = self.run_stub(preview=False, post_statuses=(502, 200))
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(seen, {"GET": 1, "POST": 1})
        self.assertFalse(marker)

    def test_readiness_failure_stops_before_publishing_post(self):
        result, seen, _, marker = self.run_stub(preview=False, get_statuses=(503,))
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(seen, {"GET": 3, "POST": 0})
        self.assertIn("no publish request was sent", result.stdout)
        self.assertFalse(marker)


if __name__ == "__main__":
    unittest.main()
