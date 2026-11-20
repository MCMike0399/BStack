from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
import ast
import json
import os
import re
import shutil
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/burbi-mode/SKILL.md"
FIXTURE = ROOT / "tests/fixtures/exports"
ENVIRONMENT = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}


@dataclass(frozen=True)
class Case:
    name: str
    playbook: str
    prompt: str
    changed_file: str | None = None


CASES = (
    Case(
        "diagnosis", "investigation",
        "Why does the export worker duplicate a line on retry? Diagnose it now. "
        "We will fix it later. Keep project files intact.",
    ),
    Case(
        "retry", "bug-fix",
        "Fix duplicate exports after a worker retry. Edit only export_worker.py. Verify the fix locally.",
        "export_worker.py",
    ),
    Case(
        "proposal", "bug-fix",
        "Use the Bug fix playbook to diagnose this duplicate export issue and propose the fix. "
        "For now, leave the project files intact.",
    ),
    Case(
        "preview", "feature",
        "Add --dry-run to the export CLI. It must print the requested ID with a newline and leave "
        "the output path untouched. Regular invocations still append. Edit only export_worker.py "
        "and verify both modes.",
        "export_worker.py",
    ),
    Case(
        "feature-plan", "feature",
        "Plan how to add an optional preview flag to the export CLI. Give one acceptance example. "
        "I only want the implementation plan today. Leave project files intact.",
    ),
    Case(
        "parser", "refactor",
        "Extract the CLI argument parsing into a function named parse_args. Keep the current CLI "
        "behavior, including argument errors and the on-disk output. Edit only export_worker.py.",
        "export_worker.py",
    ),
    Case(
        "refactor-plan", "refactor",
        "Use the Refactor playbook to propose extracting CLI argument parsing from export_worker.py. "
        "Explain how to prove the CLI stays the same. Do not edit any files yet.",
    ),
    Case(
        "transition", "migration",
        "Plan the migration from newline exports to JSON records while a legacy worker still writes "
        "for 48 hours. Describe the phases, how to verify them, and when to retire the old format. "
        "Planning only, keep files intact.",
    ),
    Case(
        "converter", "migration",
        "Implement the local conversion from newline exports to a JSON array of objects with an id "
        "string. Add only migrate_exports.py. Run it as python3 migrate_exports.py SOURCE DEST. "
        "Keep the source and existing destination records intact, append unseen nonempty IDs in "
        "source order, and make reruns safe after a partial conversion. Verify it on disposable inputs.",
        "migrate_exports.py",
    ),
    Case(
        "timing", "performance",
        "Measure the export CLI using the project's documented timing command. Give the baseline "
        "and spread for that workload. Keep project files intact.",
    ),
    Case(
        "design", "prototype",
        "Sketch two ways for someone to preview their export from the CLI and compare both on one "
        "concrete example. Recommend a direction. This is a disposable design exercise, keep "
        "project files intact.",
    ),
    Case(
        "diff", "review",
        "Review the working tree diff against HEAD for export behavior regressions. Report findings "
        "and their evidence. Keep the reviewed files intact.",
    ),
    Case(
        "check", "verification",
        "Run the documented export retry check and tell me whether it passes. Keep project files intact.",
    ),
)


def local_command(workspace, *args):
    return subprocess.run(args, cwd=workspace, env=ENVIRONMENT, capture_output=True, text=True, timeout=20)


def project_files(workspace):
    return {
        path.relative_to(workspace).as_posix(): path.read_bytes()
        for path in workspace.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(workspace).parts and path.suffix != ".pyc"
    }


def git_state(workspace):
    if not (workspace / ".git").is_dir():
        return None
    commands = (("rev-parse", "HEAD"), ("symbolic-ref", "--quiet", "HEAD"), ("ls-files", "--stage"), ("stash", "list"))
    return tuple(local_command(workspace, "git", *args).stdout for args in commands)


def prepare_case(workspace, case):
    shutil.copytree(FIXTURE, workspace)
    if case.name == "diff":
        for args in (
            ("init", "-q"),
            ("add", "AGENTS.md", "docs", "checks", "export_worker.py"),
            (
                "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                "-c", "commit.gpgsign=false", "-c", f"core.hooksPath={os.devnull}",
                "commit", "-qm", "Record CLI behavior",
            ),
        ):
            local_command(workspace, "git", *args).check_returncode()
        worker = workspace / "export_worker.py"
        worker.write_text(
            worker.read_text().replace('stream.write(export_id + "\\n")', 'stream.write("fixed-id\\n")')
        )


def run_pi(workspace, prompt):
    command = [
        "pi", "--print", "--mode", "json", "--model", "deepseek/deepseek-flash", "--thinking", "low",
        "--offline", "--no-session", "--no-extensions", "--no-mcp", "--no-prompt-templates",
        "--no-themes", "--no-skills", "--tools", "read,bash,edit,write,grep,find,ls",
        "--skill", str(SKILL), "--append-system-prompt", str(ROOT / "core/instructions.md"),
        "--", f"/skill:burbi-mode {prompt}",
    ]
    run = subprocess.run(command, cwd=workspace, env=ENVIRONMENT, capture_output=True, text=True, timeout=150)
    if run.returncode:
        raise RuntimeError(f"Pi exited {run.returncode}. {run.stderr.strip()}")
    messages = []
    for line in run.stdout.splitlines():
        if line.startswith("{"):
            event = json.loads(line)
            if event.get("type") == "message_end":
                messages.append(event["message"])
    return messages


def tool_trace(messages):
    calls = {}
    for message in messages:
        if message.get("role") == "assistant":
            for block in message.get("content", []):
                if block.get("type") == "toolCall":
                    args = block.get("arguments", {})
                    calls[block["id"]] = {
                        "name": block["name"],
                        "target": args.get("path") or args.get("command") or "",
                        "result": "",
                        "error": None,
                    }
        if message.get("role") == "toolResult" and message.get("toolCallId") in calls:
            call = calls[message["toolCallId"]]
            call["error"] = message.get("isError")
            call["result"] = "\n".join(item["text"] for item in message["content"] if item.get("type") == "text")
    return list(calls.values())


def trace_line(call):
    return f"{call['name']}: {call['target']}"


@unittest.skipUnless(os.environ.get("BSTACK_TEST_PI") == "1", "set BSTACK_TEST_PI=1 for live Pi runs")
class PiPlaybookTest(unittest.TestCase):
    def test_routes_and_observable_results(self):
        with TemporaryDirectory(prefix="exports-") as scratch:
            root = Path(scratch)
            for index, case in enumerate(CASES):
                prepare_case(root / str(index), case)

            def execute(item):
                index, case = item
                workspace = root / str(index)
                before = project_files(workspace)
                before_git = git_state(workspace)
                messages = run_pi(workspace, case.prompt)
                after = project_files(workspace)
                changes = {path for path in before.keys() | after.keys() if before.get(path) != after.get(path)}
                return workspace, case, messages, changes, git_state(workspace) == before_git

            with ThreadPoolExecutor(max_workers=3) as pool:
                runs = [pool.submit(execute, item) for item in enumerate(CASES)]
                for case, run in zip(CASES, runs):
                    with self.subTest(case=case.name):
                        self.check_case(*run.result())

    def check_case(self, workspace, case, messages, changes, same_git_state):
        assistant = [message for message in messages if message.get("role") == "assistant"][-1]
        self.assertEqual((assistant.get("provider"), assistant.get("model")), ("deepseek", "deepseek-flash"))
        self.assertEqual(assistant.get("stopReason"), "stop", assistant.get("errorMessage"))
        trace = tool_trace(messages)
        self.assertTrue(trace)
        self.assertFalse(trace[0]["error"], trace_line(trace[0]))
        self.assertIn(f"/playbooks/{case.playbook}.md", trace[0]["target"], trace_line(trace[0]))
        self.assertIn("\n1. ", trace[0]["result"], trace_line(trace[0]))
        self.assertEqual(changes, {case.changed_file} if case.changed_file else set())
        self.assertTrue(same_git_state, "Pi changed the checkout, index, or stash")

        if case.name == "retry":
            red = next(i for i, call in enumerate(trace) if "Observed ['job-17', 'job-17'], expected ['job-17']" in call["result"])
            green = next(i for i, call in enumerate(trace) if "Observed ['job-17'], expected ['job-17']" in call["result"])
            self.assertLess(red, green)
            edits = [i for i, call in enumerate(trace) if call["name"] in {"edit", "write"}]
            if edits:
                self.assertLess(red, edits[0])
                self.assertLess(edits[-1], green)
            local_command(workspace, sys.executable, "checks/replay_export.py").check_returncode()
        if case.name == "preview":
            self.check_preview(workspace)
        if case.name == "parser":
            self.check_refactor(workspace)
        if case.name == "converter":
            self.check_converter(workspace)
        if case.name == "timing":
            self.assertTrue(any("checks/time_export.py" in call["target"] and "Run 3:" in call["result"] for call in trace))
        if case.name == "diff":
            self.assertTrue(any(re.search(r"\bgit\s+(diff|show)\b", call["target"]) for call in trace))
        if case.name == "check":
            self.assertTrue(any("checks/replay_export.py" in call["target"] and "['job-17', 'job-17']" in call["result"] for call in trace))
        unrelated = any("docs/billing.md" in call["target"] for call in trace)
        answer = " ".join(block["text"] for block in assistant["content"] if block.get("type") == "text")
        print(f"{case.name}: {case.playbook}; unrelated topic referenced={unrelated}; {answer[:200]}", flush=True)

    def check_preview(self, workspace):
        output = workspace / "preview.txt"
        run = local_command(workspace, sys.executable, "export_worker.py", "job-17", str(output), "--dry-run")
        self.assertEqual((run.returncode, run.stdout), (0, "job-17\n"), run.stderr)
        self.assertFalse(output.exists())
        local_command(workspace, sys.executable, "export_worker.py", "job-17", str(output)).check_returncode()
        self.assertEqual(output.read_text(), "job-17\n")

    def check_refactor(self, workspace):
        code = ast.parse((workspace / "export_worker.py").read_text())
        self.assertTrue(any(isinstance(node, ast.FunctionDef) and node.name == "parse_args" for node in code.body))
        original = local_command(FIXTURE, sys.executable, "export_worker.py")
        revised = local_command(workspace, sys.executable, "export_worker.py")
        self.assertEqual((revised.returncode, revised.stdout, revised.stderr), (original.returncode, original.stdout, original.stderr))
        old_replay = local_command(FIXTURE, sys.executable, "checks/replay_export.py")
        new_replay = local_command(workspace, sys.executable, "checks/replay_export.py")
        self.assertEqual((new_replay.returncode, new_replay.stdout), (old_replay.returncode, old_replay.stdout))

    def check_converter(self, workspace):
        source = workspace / "existing.txt"
        destination = workspace / "exports.json"
        old_data = "job-1\njob-17\n\njob-17\njob-19\n"
        source.write_text(old_data)
        previous = {"id": "job-1", "keep": True}
        destination.write_text(json.dumps([previous]))
        for _ in range(2):
            local_command(workspace, sys.executable, "migrate_exports.py", str(source), str(destination)).check_returncode()
            self.assertEqual(json.loads(destination.read_text()), [previous, {"id": "job-17"}, {"id": "job-19"}])
            self.assertEqual(source.read_text(), old_data)


if __name__ == "__main__":
    unittest.main()
