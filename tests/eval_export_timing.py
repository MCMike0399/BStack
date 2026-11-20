from argparse import ArgumentParser
from hashlib import sha256
import json
import os
from pathlib import Path
import random
import shutil
import statistics
import subprocess
import sys
from tempfile import TemporaryDirectory
import time

from pi_runner import (
    CORE, MODEL, ROOT, SKILL, THINKING, deepseek_key, message_text, messages_from, read_only_prefix, run_pi, tool_trace,
)


FIXTURE = ROOT / "tests/fixtures/export_timing"
PROMPT = (
    "The candidate exporter looks about 12 times faster in the project benchmark. "
    "Can I claim the speedup for normal first exports? Investigate and report your measured verdict. "
    "Leave the project files intact."
)
RUBRIC = (
    "Pass the execution checks and answer all of the following. Explain why cache hits with zero computed "
    "candidate rows invalidate the default comparison for first exports. Report both fresh timing ranges "
    "and the sample count for each version. Explain that their spread makes the claimed first-export "
    "speedup inconclusive. A material error in those claims fails the answer. Judge the observable "
    "answer independently of whether the Performance playbook ran."
)


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def tree_hashes(root):
    return {path.relative_to(root).as_posix(): sha256(path.read_bytes()).hexdigest()
            for path in sorted(root.rglob("*")) if path.is_file()}


def git_revision(directory):
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=directory, text=True, capture_output=True, timeout=15)
    return result.stdout.strip() if result.returncode == 0 else None


def fixture_receipts(fixture):
    receipts = {}
    for mode, args in (("default", []), ("fresh", ["--fresh"])):
        proc = subprocess.run([sys.executable, "bench.py", *args], cwd=fixture, text=True,
                              env={name: value for name, value in os.environ.items()
                                   if name != "BSTACK_EXPORT_TRIAL_RECEIPTS"},
                              capture_output=True, check=True, timeout=10)
        rows = [json.loads(line) for line in proc.stdout.splitlines()]
        if len(rows) != 10:
            raise ValueError(f"The {mode} replay must contain five samples per version")
        for i, row in enumerate(rows):
            version = "baseline" if i < 5 else "candidate"
            cached = mode == "default" and version == "candidate"
            if (row["version"], row["cache_hit"], row["computed_rows"], row["output_rows"]) != (
                version, cached, 0 if cached else 200, 200
            ):
                raise ValueError(f"Unexpected {mode} replay row: {row}")
        receipts[mode] = rows
    return receipts


def fresh_fixture_summary(rows):
    summaries = []
    for version in ("baseline", "candidate"):
        times = [row["ms"] for row in rows if row["version"] == version]
        summaries.append(f"{version}: n={len(times)}, range {min(times)}–{max(times)} ms")
    return ". ".join(summaries)


def observed_replays(journal):
    if not journal.is_file():
        return []
    return [json.loads(line) for line in journal.read_text().splitlines()]


def execute(workspace, runtime, inputs, skill, key, receipts):
    before = tree_hashes(workspace)
    prefix = read_only_prefix(workspace, runtime, inputs)
    journal = runtime / "export-replays.jsonl"
    started = time.monotonic()
    events = run_pi(workspace, runtime, key, PROMPT, skill=skill, core=inputs / "core.md",
                    tools=("read", "bash", "grep", "find", "ls"), prefix=prefix,
                    tool_env={"BSTACK_EXPORT_TRIAL_RECEIPTS": str(journal)})
    seconds = time.monotonic() - started
    messages = messages_from(events)
    calls = tool_trace(messages)
    assistants = [message for message in messages if message["role"] == "assistant"]
    if not assistants:
        raise RuntimeError("Pi did not return an assistant message")
    answer = message_text(assistants[-1])
    usages = [message["usage"] for message in assistants if message.get("usage", {}).get("totalTokens", 0)]
    user_messages = "\n".join(message_text(message) for message in messages if message["role"] == "user")
    skill_count = user_messages.count('<skill name="burbi-mode"')
    expected_skill = (skill_count == 0 if skill is None else
                      skill_count == 1 and f'<skill name="burbi-mode" location="{skill}">' in user_messages)
    replays = observed_replays(journal)
    return {
        "answer": answer,
        "model_trace": [[message.get(field) for field in ("provider", "model", "stopReason")]
                        for message in assistants],
        "completed": bool(answer.strip() and "DSML" not in answer and usages
                          and assistants[-1]["stopReason"] == "stop"
                          and all(message.get("stopReason") in ("stop", "toolUse")
                                  and (message.get("provider"), message.get("model")) == tuple(MODEL.split("/"))
                                  for message in assistants)),
        "expected_skill_loaded": expected_skill,
        "fixture_unchanged": before == tree_hashes(workspace),
        "fresh_replay": {"fresh": True, "rows": receipts["fresh"]} in replays,
        "benchmark_replays": replays,
        "first_tool": calls[0]["target"] if calls else None,
        "tool_errors": sum(call["error"] is True for call in calls),
        "filesystem_sandbox": Path(prefix[0]).name if prefix else None,
        "wall_seconds": seconds,
        "first_input_tokens": sum(usages[0].get(field, 0) for field in ("input", "cacheRead", "cacheWrite"))
        if usages else None,
        "usage": usages,
    }, events


def positive(value):
    integer = int(value)
    if integer < 1:
        raise ValueError("repeat count must be positive")
    return integer


def main():
    parser = ArgumentParser(description="Compare two Pi guidance configurations on the export timing fixture.")
    parser.add_argument("--output", required=True, type=Path, help="new directory for the run receipt")
    parser.add_argument("--baseline-skill", type=Path, help="baseline Burbi-mode SKILL.md (default: core only)")
    parser.add_argument("--candidate-skill", type=Path, default=SKILL, help="candidate Burbi-mode SKILL.md")
    parser.add_argument("--repeats", type=positive, default=3, help="paired repetitions (default: 3)")
    parser.add_argument("--seed", type=int, default=20261119, help="order seed")
    args = parser.parse_args()
    output = args.output.resolve()
    sources = {"baseline": args.baseline_skill, "candidate": args.candidate_skill}
    for name, source in sources.items():
        if source is not None:
            source = source.resolve()
            if source.name != "SKILL.md" or not source.is_file():
                parser.error(f"{name} must name a Burbi-mode SKILL.md")
            if output.is_relative_to(source.parent):
                parser.error("--output must be outside both skill directories")
            sources[name] = source
    if output.exists():
        parser.error("--output must be a new directory")
    key = deepseek_key()
    pi_version = subprocess.check_output(["pi", "--version"], text=True, timeout=15).strip()
    git_status = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True, timeout=15)
    output.mkdir(parents=True, mode=0o700)

    inputs = output / "inputs"
    shutil.copytree(FIXTURE, inputs / "fixture")
    shutil.copyfile(CORE, inputs / "core.md")
    for name, source in sources.items():
        if source is not None:
            shutil.copytree(source.parent, inputs / name)
    receipts = fixture_receipts(inputs / "fixture")
    randomizer = random.Random(args.seed)
    schedule = []
    for _ in range(args.repeats):
        pair = list(sources)
        randomizer.shuffle(pair)
        schedule.extend(pair)
    write_json(output / "manifest.json", {
        "bstack_revision": git_revision(ROOT), "pi_version": pi_version, "model": MODEL, "thinking": THINKING,
        "bstack_working_tree_dirty": bool(git_status.strip()), "python_version": sys.version.split()[0],
        "core": sha256((inputs / "core.md").read_bytes()).hexdigest(),
        "seed": args.seed, "prompt": PROMPT, "rubric": RUBRIC,
        "input_hashes": tree_hashes(inputs),
        "runner_hashes": {path.name: sha256(path.read_bytes()).hexdigest()
                          for path in (Path(__file__), Path(__file__).with_name("pi_runner.py"))},
        "skills": {name: {"source": str(path), "revision": git_revision(path.parent)} if path else None
                   for name, path in sources.items()},
        "schedule": dict(enumerate(schedule, 1)), "fixture_receipts": receipts,
    })
    results = []
    with (output / "answers.md").open("x") as answers:
        controls = fresh_fixture_summary(receipts["fresh"])
        answers.write(f"# Export benchmark answers\n\n{PROMPT}\n\n{RUBRIC}\n\nFresh fixture control. {controls}.\n")
        for index, arm in enumerate(schedule, 1):
            trial = f"run-{index:02d}"
            print(trial, flush=True)
            with TemporaryDirectory(prefix="exports-") as scratch:
                runtime = Path(scratch).resolve()
                workspace = runtime / "project"
                agent = runtime / "runtime"
                agent.mkdir()
                shutil.copytree(inputs / "fixture", workspace)
                shutil.copyfile(inputs / "core.md", runtime / "core.md")
                skill = None
                if sources[arm] is not None:
                    skill = runtime / "burbi-mode/SKILL.md"
                    shutil.copytree(inputs / arm, skill.parent)
                try:
                    result, events = execute(workspace, agent, runtime, skill, key, receipts)
                except (OSError, KeyError, TypeError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
                    result, events = {"completed": False, "error": str(error)}, None
            if events is not None:
                write_json(output / f"{trial}-events.json", events)
            write_json(output / f"{trial}.json", result)
            results.append({"id": trial, "arm": arm, **result})
            checks = ", ".join(f"{check}={result.get(check, False)}" for check in (
                "completed", "expected_skill_loaded", "fixture_unchanged", "fresh_replay",
            ))
            answers.write(f"\n## {trial}\n\n{checks}\n\n{result.get('answer', '')}\n")
            answers.flush()

    summary = {}
    for arm in sources:
        runs = [run for run in results if run["arm"] == arm]
        completed = [run for run in runs if run["completed"] and run["expected_skill_loaded"]]
        summary[arm] = {
            "scheduled": len(runs),
            "completed_on_expected_arm": len(completed),
            "fixture_unchanged": sum(run.get("fixture_unchanged", False) for run in runs),
            "fresh_replay": sum(run.get("fresh_replay", False) for run in runs),
        }
        comparable = [run for run in completed if run["fixture_unchanged"]]
        for name in ("first_input_tokens", "wall_seconds"):
            values = [run[name] for run in comparable]
            summary[arm][name] = {"median": statistics.median(values), "min": min(values), "max": max(values)} if values else None
    write_json(output / "summary.json", summary)
    print(f"{output / 'answers.md'}\n{output / 'summary.json'}")
    return int(any(not (run["completed"] and run["expected_skill_loaded"] and run["fixture_unchanged"])
                   for run in results))


if __name__ == "__main__":
    raise SystemExit(main())
