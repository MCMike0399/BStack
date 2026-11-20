from eval_export_timing import FIXTURE, fixture_receipts, observed_replays
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


class ExportTimingReceiptTest(unittest.TestCase):
    def test_records_fresh_replay_when_stdout_is_redirected(self):
        receipts = fixture_receipts(FIXTURE)
        fresh = {"fresh": True, "rows": receipts["fresh"]}
        with TemporaryDirectory() as scratch:
            journal = Path(scratch) / "replays.jsonl"
            self.assertEqual(observed_replays(journal), [])
            environment = {**os.environ, "BSTACK_EXPORT_TRIAL_RECEIPTS": str(journal)}
            subprocess.run(
                [sys.executable, "bench.py"], cwd=FIXTURE, env=environment,
                stdout=subprocess.DEVNULL, check=True, timeout=10,
            )
            self.assertEqual(observed_replays(journal), [{"fresh": False, "rows": receipts["default"]}])
            self.assertNotIn(fresh, observed_replays(journal))
            with subprocess.Popen(
                [sys.executable, "bench.py", "--fresh"], cwd=FIXTURE, env=environment, stdout=subprocess.PIPE,
            ) as replay:
                summary = subprocess.run(
                    [sys.executable, "-c", "import sys; print(sum(1 for _ in sys.stdin))"],
                    stdin=replay.stdout, capture_output=True, text=True, check=True, timeout=10,
                )
                self.assertEqual(summary.stdout.strip(), "10")
                self.assertEqual(replay.wait(timeout=10), 0)
            self.assertIn(fresh, observed_replays(journal))
