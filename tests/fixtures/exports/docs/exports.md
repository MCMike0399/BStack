# Export worker

The CLI in `export_worker.py` receives an export ID and an output path. Distinct IDs append in order. A retry uses the same stable ID and should leave exactly one line for that ID.

Use `python3 checks/replay_export.py` to exercise a retry through the CLI on disposable output. It exits successfully if the output has one line. Use `python3 checks/time_export.py` to measure three runs of the sequential CLI workload, including process startup.
