# Export benchmark

Run `python3 bench.py` for the default comparison. `python3 bench.py --help`
lists the replay controls.

The CLI replays a fixed timing trace and executes the corresponding mock
exporter. The receipt reports the elapsed time from the trace and the work
performed during replay. Use the counters to decide whether the runs are
comparable.
