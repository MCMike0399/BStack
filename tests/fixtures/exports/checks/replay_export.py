from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory


worker = Path(__file__).resolve().parents[1] / "export_worker.py"
with TemporaryDirectory() as scratch:
    output = Path(scratch) / "exports.txt"
    for _ in range(2):
        subprocess.run([sys.executable, str(worker), "job-17", str(output)], check=True)
    actual = output.read_text().splitlines()
    expected = ["job-17"]
    print(f"Observed {actual!r}, expected {expected!r}")
    raise SystemExit(0 if actual == expected else 1)
