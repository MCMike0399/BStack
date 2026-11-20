from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from time import perf_counter


worker = Path(__file__).resolve().parents[1] / "export_worker.py"
with TemporaryDirectory() as scratch:
    for run in range(3):
        output = Path(scratch) / f"exports-{run}.txt"
        started = perf_counter()
        for index in range(6):
            subprocess.run([sys.executable, str(worker), f"job-{index}", str(output)], check=True)
        duration = perf_counter() - started
        assert output.read_text().splitlines() == [f"job-{index}" for index in range(6)]
        print(f"Run {run + 1}: {duration:.4f}s for 6 exports")
