import argparse
import json
import os
import sys


def replay(fresh):
    traces = {
        "baseline": [94, 105, 120, 133, 145],
        "candidate": [91, 101, 113, 128, 141] if fresh else [9, 11, 10, 12, 10],
    }
    for version, times in traces.items():
        for elapsed in times:
            cache_hit = version == "candidate" and not fresh
            cached_rows = list(range(200)) if cache_hit else []
            computed = [] if cache_hit else list(range(200))
            yield {
                "version": version, "ms": elapsed, "computed_rows": len(computed),
                "output_rows": len(cached_rows or computed), "cache_hit": cache_hit,
            }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--fresh", action="store_true", help="replay cache-empty timings for both versions")
    fresh = parser.parse_args().fresh
    rows = list(replay(fresh))
    for row in rows:
        print(json.dumps(row))
    if receipt := os.environ.get("BSTACK_EXPORT_TRIAL_RECEIPTS"):
        sys.stdout.flush()
        with open(receipt, "a") as journal:
            print(json.dumps({"fresh": fresh, "rows": rows}), file=journal)
