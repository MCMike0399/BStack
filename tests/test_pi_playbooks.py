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

from pi_runner import deepseek_key, messages_from, run_pi, tool_trace

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/burbi-mode/SKILL.md"
FIXTURE = ROOT / "tests/fixtures/exports"
ENVIRONMENT = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}


ANY_CHANGES = ("*",)


@dataclass(frozen=True)
class Case:
    name: str
    playbook: str | tuple[str, ...]
    prompt: str
    changed_file: str | None = None
    # Paths the case may change, when the set of changes is not exactly changed_file.
    # ANY_CHANGES leaves the change set to the case's own check.
    allowed: tuple[str, ...] | None = None
    timeout: int = 150


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
    Case(
        "recurring", "recurring-mistake",
        "Agents keep changing how export_worker.py opens the output file so that it overwrites instead "
        "of appending. Review caught it twice and both commits were reverted; see the git history. "
        "Stop this from happening again. Any check you add must run as python3 <path> and exit nonzero "
        "when the mistake is present. Leave export_worker.py unchanged.",
        allowed=ANY_CHANGES, timeout=300,
    ),
    Case(
        "productbug", "bug-fix",
        "Exports keep getting duplicated after every retry in production. Fix it. Edit only export_worker.py.",
        "export_worker.py",
    ),
    Case(
        "guidance", "guidance",
        "Revise AGENTS.md so agents run the export retry check before reporting an export change. "
        "Edit only AGENTS.md.",
        "AGENTS.md",
    ),
    Case(
        "guidance-review", "review",
        "Review the working-tree diff to AGENTS.md and report findings. Keep files intact.",
    ),
    Case(
        "pickup", "handoff",
        "Pick up where the last session stopped. Its notes are in HANDOFF.md. Edit only export_worker.py.",
        allowed=("export_worker.py",), timeout=300,
    ),
    Case(
        "pause", "handoff",
        "I have to stop now. Pause this work so another session can resume it. Write the record to "
        "PAUSE.md. Do not commit.",
        allowed=("PAUSE.md", "export_worker.py"),
    ),
    Case(
        "unattended", ("bug-fix", "feature"),
        "Work unattended: fix the duplicate export on retry, then add --dry-run, which prints the "
        "requested ID with a newline and leaves the output path untouched. I will audit your decisions "
        "afterward, so log them in DECISIONS.md. Edit only export_worker.py and DECISIONS.md.",
        allowed=("export_worker.py", "DECISIONS.md"), timeout=300,
    ),
    Case(
        "tests", "feature",
        "Add a test that distinct export IDs are appended in the order they were exported. Add only "
        "checks/test_order.py. It must run as python3 checks/test_order.py and exit nonzero on failure.",
        "checks/test_order.py",
    ),
    Case(
        "failing-check", "bug-fix",
        "checks/replay_export.py is failing. Fix it.",
        allowed=("export_worker.py",),
    ),
    Case(
        "why-failing", "investigation",
        "Why is checks/replay_export.py failing? Keep project files intact.",
    ),
    Case(
        "rename", "refactor",
        "Rename the local variable stream in export_worker.py to out_file. Edit only export_worker.py.",
        "export_worker.py",
    ),
)

OVERWRITE = 'output.open("w", encoding="utf-8")'
# Mutation that keeps every ID but writes the newest first.
PREPEND_FROM = '    with output.open("a", encoding="utf-8") as stream:\n        stream.write(export_id + "\\n")'
PREPEND_TO = (
    '    previous = output.read_text(encoding="utf-8") if output.exists() else ""\n'
    '    with output.open("w", encoding="utf-8") as stream:\n'
    '        stream.write(export_id + "\\n" + previous)'
)
APPEND = 'output.open("a", encoding="utf-8")'


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


def git(workspace, *args):
    identity = (
        "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
        "-c", "commit.gpgsign=false", "-c", f"core.hooksPath={os.devnull}",
    )
    return local_command(workspace, "git", *identity, *args).check_returncode()


def commit_all(workspace, message):
    git(workspace, "add", "-A")
    git(workspace, "commit", "-qm", message)


def replace_in(path, old, new):
    text = path.read_text()
    assert old in text, (path, old)
    path.write_text(text.replace(old, new))


def prepare_case(workspace, case):
    shutil.copytree(FIXTURE, workspace)
    worker = workspace / "export_worker.py"
    if case.name in {"diff", "recurring", "guidance-review", "pickup", "pause"}:
        git(workspace, "init", "-q")
        commit_all(workspace, "Record CLI behavior")
    if case.name == "diff":
        replace_in(worker, 'stream.write(export_id + "\\n")', 'stream.write("fixed-id\\n")')
    if case.name == "recurring":
        for title in ("Simplify export writing", "Open the output once per export"):
            replace_in(worker, APPEND, OVERWRITE)
            commit_all(workspace, title)
            git(workspace, "revert", "--no-edit", "HEAD")
            git(workspace, "commit", "-q", "--amend", "-m",
                f'Revert "{title}"\n\nReview: mode "w" truncates the file and wipes earlier exports. Exports must append.')
    if case.name == "guidance-review":
        guidance = workspace / "AGENTS.md"
        guidance.write_text(guidance.read_text() + (
            "\nBefore reporting an export change, run `python3 checks/replay_export.py`. "
            "If it fails, change the expected value in the check to match the output.\n"
        ))
    if case.name == "pickup":
        (workspace / "HANDOFF.md").write_text(
            "# Handoff\n\nDone: the retry duplicate is fixed and `python3 checks/replay_export.py` passes.\n\n"
            "Next: add --dry-run to the export CLI. It prints the requested ID with a newline and leaves "
            "the output path untouched.\n"
        )
        commit_all(workspace, "Record handoff")
    if case.name == "pause":
        replace_in(worker, "    with output.open", "    # WIP: skip IDs already written\n    with output.open")


# A shell command that writes a file: a redirect other than to a descriptor or /dev/null, tee,
# an in-place edit, or a Python write.
SHELL_WRITE = (
    r"(?<![0-9&])>>?(?!&)\s*(?!/dev/null)\S|\btee\b|\bsed\s+-i|\bperl\s+-pi|write_text|open\([^)]*['\"][wa]"
)


def writes(trace, path=""):
    """Indexes of calls that write path, through the edit tools or a shell redirect."""
    return [
        i for i, call in enumerate(trace)
        if path in call["target"] and (
            call["name"] in {"edit", "write"}
            or (call["name"] == "bash" and re.search(SHELL_WRITE, call["target"]))
        )
    ]


def trace_line(call):
    return f"{call['name']}: {call['target']}"


@unittest.skipUnless(os.environ.get("BSTACK_TEST_PI") == "1", "set BSTACK_TEST_PI=1 for live Pi runs")
class PiPlaybookTest(unittest.TestCase):
    def test_routes_and_observable_results(self):
        key = deepseek_key()
        with TemporaryDirectory(prefix="exports-") as scratch:
            root = Path(scratch)
            for index, case in enumerate(CASES):
                prepare_case(root / str(index), case)

            def execute(item):
                index, case = item
                workspace = root / str(index)
                before = project_files(workspace)
                before_git = git_state(workspace)
                with TemporaryDirectory(prefix="pi-", dir=root) as runtime:
                    messages = messages_from(run_pi(workspace, Path(runtime), key, case.prompt, timeout=case.timeout))
                after = project_files(workspace)
                changes = {path for path in before.keys() | after.keys() if before.get(path) != after.get(path)}
                return workspace, case, messages, changes, git_state(workspace) == before_git

            # Each case is an independent DeepSeek session, so run them all at once by default.
            workers = int(os.environ.get("BSTACK_PI_WORKERS", len(CASES)))
            with ThreadPoolExecutor(max_workers=workers) as pool:
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
        playbooks = (case.playbook,) if isinstance(case.playbook, str) else case.playbook
        opened = next(i for i, call in enumerate(trace) if "/playbooks/" in call["target"])
        # The skill asks for the playbook first. Flash sometimes reads project context or a named
        # record first; allow a few read-only calls, but no edits before the playbook.
        self.assertLessEqual(opened, 3, trace_line(trace[0]))
        if opened:
            print(f"{case.name}: {opened} read-only call(s) before the playbook", flush=True)
        self.assertFalse(writes(trace[:opened]), trace_line(trace[0]))
        self.assertTrue(any(f"/playbooks/{name}.md" in trace[opened]["target"] for name in playbooks), trace_line(trace[opened]))
        self.assertIn("\n1. ", trace[opened]["result"], trace_line(trace[opened]))
        if case.allowed is None:
            self.assertEqual(changes, {case.changed_file} if case.changed_file else set())
        elif case.allowed != ANY_CHANGES:
            self.assertLessEqual(changes, set(case.allowed))
        self.assertTrue(same_git_state, "Pi changed the checkout, index, or stash")

        if case.name == "retry":
            self.assertFalse(any("/references/project-verification.md" in call["target"] for call in trace))
        if case.name in {"productbug", "failing-check"}:
            local_command(workspace, sys.executable, "checks/replay_export.py").check_returncode()
        if case.name == "recurring":
            self.check_recurring(workspace, changes)
        answer = " ".join(block["text"] for block in assistant["content"] if block.get("type") == "text")
        if case.name == "guidance":
            original = set((FIXTURE / "AGENTS.md").read_text().splitlines())
            added = "\n".join(line for line in (workspace / "AGENTS.md").read_text().splitlines() if line not in original)
            self.assertRegex(added, r"(?i)replay_export|retry check")
        if case.name == "guidance-review":
            self.assertTrue(any(re.search(r"\bgit\s+(diff|show)\b", call["target"]) for call in trace))
            self.assertRegex(answer, r"(?i)expected value|edit(ing)? the check|weaken")
        if case.name == "pickup":
            self.check_pickup(workspace, trace, answer)
        if case.name == "pause":
            self.check_pause(workspace, trace)
        if case.name == "unattended":
            self.check_unattended(workspace, trace)
        if case.name == "tests":
            self.check_order_test(workspace)
        if case.name == "rename":
            self.assertFalse(any("/references/" in call["target"] for call in trace))
            code = (workspace / "export_worker.py").read_text()
            self.assertIn("out_file", code)
            self.assertNotRegex(code, r"\bstream\b")
            self.check_same_cli(workspace)
            print(f"rename: {len(trace)} tool calls", flush=True)
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
        print(f"{case.name}: {case.playbook}; unrelated topic referenced={unrelated}; {answer[:200]}", flush=True)

    def check_preview(self, workspace):
        output = workspace / "preview.txt"
        run = local_command(workspace, sys.executable, "export_worker.py", "job-17", str(output), "--dry-run")
        self.assertEqual((run.returncode, run.stdout), (0, "job-17\n"), run.stderr)
        self.assertFalse(output.exists())
        local_command(workspace, sys.executable, "export_worker.py", "job-17", str(output)).check_returncode()
        self.assertEqual(output.read_text(), "job-17\n")

    def check_recurring(self, workspace, changes):
        self.assertTrue(changes)
        # Step 4: no instruction for a class a check enforces, and existing checks stay as they are.
        self.assertFalse(changes & {"export_worker.py", "checks/replay_export.py", "AGENTS.md"}, changes)
        added = sorted(path for path in changes if path.endswith(".py") and not (FIXTURE / path).exists())
        rejecting = []
        with TemporaryDirectory() as scratch:
            past = Path(scratch) / "past"
            shutil.copytree(workspace, past)
            replace_in(past / "export_worker.py", APPEND, OVERWRITE)
            for path in added:
                current = local_command(workspace, sys.executable, path)
                mistaken = local_command(past, sys.executable, path)
                if current.returncode == 0 and mistaken.returncode != 0:
                    rejecting.append(path)
        self.assertTrue(rejecting, f"no new check passes now and rejects mode 'w': {added}")

    def check_pickup(self, workspace, trace, answer):
        # The record claims the replay check passes; it fails. The agent must rerun it before
        # building on that claim, report the discrepancy, and continue with another playbook.
        replay = [i for i, call in enumerate(trace) if call["name"] == "bash" and "Observed ['job-17'" in call["result"]]
        self.assertTrue(replay)
        edits = writes(trace)
        if edits:
            self.assertLess(replay[0], edits[0])
        self.assertTrue(any(
            "/playbooks/" in call["target"] and "/playbooks/handoff.md" not in call["target"] for call in trace[1:]
        ))
        self.assertRegex(answer, r"(?i)replay|duplicate")
        self.check_preview(workspace)

    def check_pause(self, workspace, trace):
        # A pause records the checkpoint and starts no new step.
        self.assertFalse(any(
            "/playbooks/" in call["target"] and "/playbooks/handoff.md" not in call["target"] for call in trace
        ))
        record = (workspace / "PAUSE.md").read_text()
        head = local_command(workspace, "git", "rev-parse", "HEAD").stdout.strip()
        self.assertIn(head[:7], record)
        if "WIP" in (workspace / "export_worker.py").read_text():
            self.assertIn("export_worker.py", record)

    def check_unattended(self, workspace, trace):
        reference = [i for i, call in enumerate(trace) if "/references/long-running-work.md" in call["target"]]
        log = writes(trace, "DECISIONS.md")
        worker = writes(trace, "export_worker.py")
        self.assertTrue(reference and log and worker)
        self.assertLess(reference[0], worker[0])
        self.assertLess(log[0], worker[0])
        self.assertTrue((workspace / "DECISIONS.md").read_text().strip())
        local_command(workspace, sys.executable, "checks/replay_export.py").check_returncode()
        self.check_preview(workspace)

    def check_order_test(self, workspace):
        local_command(workspace, sys.executable, "checks/test_order.py").check_returncode()
        with TemporaryDirectory() as scratch:
            broken = Path(scratch) / "broken"
            shutil.copytree(workspace, broken)
            replace_in(broken / "export_worker.py", 'stream.write(export_id + "\\n")', 'stream.write("fixed-id\\n")')
            self.assertNotEqual(local_command(broken, sys.executable, "checks/test_order.py").returncode, 0)
        with TemporaryDirectory() as scratch:
            reversed_order = Path(scratch) / "reversed"
            shutil.copytree(workspace, reversed_order)
            replace_in(reversed_order / "export_worker.py", PREPEND_FROM, PREPEND_TO)
            self.assertNotEqual(local_command(reversed_order, sys.executable, "checks/test_order.py").returncode, 0)

    def check_same_cli(self, workspace):
        outputs = []
        for root in (FIXTURE, workspace):
            with TemporaryDirectory() as scratch:
                output = Path(scratch) / "exports.txt"
                for export_id in ("job-1", "job-2"):
                    local_command(root, sys.executable, "export_worker.py", export_id, str(output)).check_returncode()
                outputs.append(output.read_text())
        self.assertEqual(outputs[0], outputs[1])

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
