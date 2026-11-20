# Export timing eval

Use this eval to compare how two Burbi-mode revisions handle a misleading
benchmark claim. The fixture replays synthetic timings. It measures the
agent’s decision and reporting, with no claim about exporter performance.

## Run

From BStack, use Pi with a configured official DeepSeek connection. The
runner uses fresh profiles with DeepSeek Flash, low effort, the same core,
the same prompt and the same benchmark fixture in every run.

```sh
python3 -B tests/eval_export_timing.py --output /tmp/bstack-export-eval
```

The output directory must be new. The default comparison is core only against
the current Burbi-mode skill. Pass `--baseline-skill /path/to/old/SKILL.md` and
`--candidate-skill /path/to/new/SKILL.md` to compare two skill revisions. Supply
the complete Burbi-mode directory in each case so its relative playbook and
reference links work. Use `--repeats` to change the number of matched pairs.
`--seed` fixes trial order within pairs. Each pair runs both arms once.

The runner verifies both fixture modes itself before launching Pi. Pi then
investigates a fresh fixture copy in every trial. On macOS, the read-only
trial uses `sandbox-exec` where available. The runner captures the tool trace
and a separate journal from the benchmark CLI so piping or redirecting stdout
does not hide a run. It checks fixture integrity and removes disposable
workspaces. Each run records its sandbox mode. Use trusted skill directories
in this local harness. Pi retains the provider key in its process
environment. The ordinary Bash tool unsets the key before running commands.
The optional sandbox constrains filesystem access.

## Score and decide

1. Read `answers.md` before opening the arm mapping in `manifest.json`. Score
   each labeled answer against the included rubric. Answers may mention the
   playbook and reveal the arm, so treat this as masking rather than full
   blinding.
2. Require a completed trial, expected skill delivery, stable fixture file
   paths and contents, and a successful fresh replay through the documented
   CLI. The command is available in `run-*-events.json` and the replay rows
   are in `run-*.json`. The journal proves the CLI ran. Use the answer and
   tool output to check how the agent used the evidence. Apply the rubric in
   the receipt. In particular, the overlapping ranges support an
   inconclusive verdict on first-export speedup. An answer that rejects 12×
   and still claims a measured 4% first-export speedup fails that criterion.
   A valid session without a fresh CLI replay fails the task. A session
   failure, delivery mismatch or fixture mutation produces a nonzero runner
   exit. The CLI leaves substantive grades to the scorer.
3. Join the scores to the arm mapping. Prefer a candidate only if the
   observable outcomes support the intended change. If the outcome gain is
   inconsistent, keep the current guidance. Use `summary.json` for the
   number of completed runs and the median and spread of first-input tokens
   and elapsed time. Per-run usage includes cache counts. First-input tokens
   measure context, and overlapping wall-time ranges leave speed differences
   inconclusive. Compare arms under the same sandbox conditions.

The receipt contains the exact prompt and rubric, input copies and hashes,
the source Git revisions when available, and the model, effort and tool
traces. Use the recorded hashes to identify the exact inputs when the source
checkout has uncommitted changes. To compare skill snapshots again, pass the saved
`inputs/baseline/SKILL.md` and `inputs/candidate/SKILL.md` paths that exist.
Omit the baseline option to rerun a core-only arm. Replay into a fresh output
directory and score the new answers.
