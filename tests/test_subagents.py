from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import difflib
import json
import os
import shutil
import subprocess
import sys
import unittest

from test_pi_playbooks import FIXTURE, ROOT, SKILL, project_files, tool_trace


ROLES = SKILL.parent / "roles"
SOURCE = "export_worker.py"
FILE_TOOLS = ["read", "grep", "find", "ls", "edit", "write"]
REQUIREMENT = (
    "A sequential retry with the same stable export ID must leave one row for that ID. "
    "Different IDs must still append in order, including to a file with existing rows. "
    "Keep the existing two-argument CLI and line-based output. "
    "IDs in scope are nonempty single-line strings such as job-17."
)
ADVISOR_SCHEMA = {
    "type": "object",
    "properties": {
        "snapshot": {"type": "string"},
        "status": {"type": "string", "enum": ["reviewed", "incomplete"]},
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "inputs": {"type": "array", "minItems": 1, "maxItems": 6, "items": {"type": "string"}},
                    "expected": {"type": "array", "items": {"type": "string"}},
                    "predicted": {"type": "array", "items": {"type": "string"}},
                    "impact": {"type": "string"},
                },
                "required": ["path", "inputs", "expected", "predicted", "impact"],
                "additionalProperties": False,
            },
        },
        "limitations": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["snapshot", "status", "findings", "limitations"],
    "additionalProperties": False,
}


def snapshot_id(base, candidate):
    return sha256(base + b"\0" + candidate).hexdigest()


def review_covers(report, base, candidate):
    return report["status"] == "reviewed" and report["snapshot"] == snapshot_id(base, candidate)


def json_events(output):
    return [json.loads(line) for line in output.splitlines() if line.startswith("{")]


def subpaths(paths):
    return " ".join(f"(subpath {json.dumps(str(path))})" for path in paths)


def worker_profile(pi, workspace, runtime, parent):
    home = Path.home().resolve()
    launcher_paths = (pi, pi.resolve(), home / ".pi/agent/install", home / ".local/share/pi-node")
    return (
        "(version 1) (allow default) (deny file-write*) "
        f"(allow file-write* (literal {json.dumps(str(workspace / SOURCE))}) {subpaths((runtime,))}) "
        f"(deny file-read-data {subpaths((home, parent))}) "
        f"(allow file-read-data {subpaths(launcher_paths)})"
    )


def worker_environment(runtime):
    key = subprocess.run(
        ["pi", "auth", "print-api-key", "--provider", "deepseek", "--model", "deepseek-flash"],
        capture_output=True, text=True, timeout=15, check=True,
    ).stdout.strip()
    if not key:
        raise RuntimeError("Pi returned no DeepSeek credential for the temporary profile")
    inherited = {"PATH", "HOME", "LANG", "LC_ALL", "XDG_DATA_HOME", "SSL_CERT_FILE", "SSL_CERT_DIR"}
    return {
        **{name: os.environ[name] for name in inherited if name in os.environ},
        "TMPDIR": str(runtime),
        "PI_CODING_AGENT_DIR": str(runtime / "pi"),
        "DEEPSEEK_API_KEY": key,
        "PYTHONDONTWRITEBYTECODE": "1",
    }


def run_worker(workspace, runtime, sandbox, environment, base):
    if (workspace / SOURCE).read_bytes() != base:
        raise ValueError("Worker workspace does not match the assigned base")
    for name, source in (
        ("core.md", ROOT / "core/instructions.md"),
        ("worker.md", ROLES / "worker.md"),
        ("bug-fix.md", SKILL.parent / "playbooks/bug-fix.md"),
    ):
        shutil.copyfile(source, runtime / name)
    rules = SKILL.read_text().split("## Engineering rules", 1)[1]
    (runtime / "engineering-rules.md").write_text(rules)
    command = [
        *sandbox, "pi", "--print", "--mode", "json", "--model", "deepseek/deepseek-flash", "--thinking", "low",
        "--offline", "--no-session", "--no-extensions", "--no-mcp", "--no-prompt-templates", "--no-themes",
        "--no-skills", "--no-context-files", "--no-approve", "--tools", ",".join(FILE_TOOLS),
    ]
    for name in ("core.md", "engineering-rules.md", "worker.md"):
        command.extend(("--append-system-prompt", str(runtime / name)))
    prompt = (
        f"Your assignment starts at snapshot {sha256(base).hexdigest()}. Fix duplicate output on retry. "
        f"{REQUIREMENT} Read AGENTS.md and the Bug fix playbook at {runtime / 'bug-fix.md'}. "
        f"Your writable scope is {SOURCE} in the assigned working copy. "
        "The acceptance check replays a duplicate ID and two distinct IDs through the CLI. "
        "The invoking agent runs that check after you return. Report any checks you could not run."
    )
    result = subprocess.run(
        [*command, "--", prompt], cwd=workspace, env=environment,
        capture_output=True, text=True, timeout=150,
    )
    if result.returncode:
        error = result.stderr.replace(environment["DEEPSEEK_API_KEY"], "[redacted]")
        raise RuntimeError(f"Pi exited {result.returncode}. {error.strip()}")
    return [event["message"] for event in json_events(result.stdout) if event.get("type") == "message_end"]


def run_advisor(workspace, base, candidate):
    delta = "".join(difflib.unified_diff(
        base.decode().splitlines(keepends=True), candidate.decode().splitlines(keepends=True),
        fromfile=f"base/{SOURCE}", tofile=f"candidate/{SOURCE}",
    ))
    prompt = (
        f"Review snapshot {snapshot_id(base, candidate)} against this request. {REQUIREMENT}\n\n"
        "For a concrete sequential regression, give the ordered IDs as inputs, expected output rows, "
        "and the rows you predict from this code. Work from the supplied evidence and flag any limitations. "
        "Report reviewed when you covered this request against the supplied snapshot.\n\n"
        f"Diff\n{delta}\nFull candidate {SOURCE}\n{candidate.decode()}"
    )
    result = subprocess.run(
        [
            "claude-auto", "-p", "--bare", "--strict-mcp-config", "--tools", "", "--no-session-persistence",
            "--model", "claude-fable-5-2", "--effort", "medium", "--output-format", "stream-json", "--verbose",
            "--append-system-prompt", (ROLES / "advisor.md").read_text(),
            "--json-schema", json.dumps(ADVISOR_SCHEMA),
        ],
        cwd=workspace, input=prompt, capture_output=True, text=True, timeout=140,
    )
    if result.returncode:
        raise RuntimeError(f"Fable exited {result.returncode}. {result.stderr.strip()}")
    events = json_events(result.stdout)
    setup = next(event for event in events if event.get("type") == "system" and event.get("subtype") == "init")
    answer = next(event for event in events if event.get("type") == "result")
    return setup, answer


def run_fixture(workspace, scratch, *args):
    profile = (
        "(version 1) (allow default) (deny file-write*) (deny network*) "
        f"(allow file-write* {subpaths((scratch,))}) "
        f"(deny file-read-data {subpaths((Path.home().resolve(),))}) "
        f"(allow file-read-data {subpaths((Path(sys.base_prefix).resolve(),))})"
    )
    return subprocess.run(
        ["sandbox-exec", "-p", profile, sys.executable, "-B", *args], cwd=workspace,
        env={"TMPDIR": str(scratch)}, capture_output=True, text=True, timeout=20,
    )


def observed_rows(workspace, ids):
    with TemporaryDirectory(prefix="bstack-replay-") as scratch:
        scratch = Path(scratch).resolve()
        output = scratch / "exports.txt"
        for export_id in ids:
            run_fixture(workspace, scratch, SOURCE, "--", export_id, str(output)).check_returncode()
        return output.read_text().splitlines()


def documented_replay(workspace):
    with TemporaryDirectory(prefix="bstack-replay-") as scratch:
        return run_fixture(workspace, Path(scratch).resolve(), "checks/replay_export.py")


class RoleFilesTest(unittest.TestCase):
    def test_roles_are_available_to_the_runner(self):
        for role in ("worker", "advisor"):
            self.assertTrue((ROLES / f"{role}.md").read_text().startswith(f"# {role.title()}\n"))

    def test_review_coverage_requires_completion_and_exact_snapshot(self):
        base, candidate = b"base", b"candidate"
        report = {"status": "reviewed", "snapshot": snapshot_id(base, candidate)}
        self.assertTrue(review_covers(report, base, candidate))
        self.assertFalse(review_covers(report, b"other base", candidate))
        self.assertFalse(review_covers(report, base, b"new candidate"))
        self.assertFalse(review_covers({**report, "status": "incomplete"}, base, candidate))

    def test_worker_rejects_base_mismatch_before_dispatch(self):
        with TemporaryDirectory(prefix="bstack-base-") as scratch:
            workspace = Path(scratch)
            (workspace / SOURCE).write_bytes(b"unexpected state")
            with self.assertRaisesRegex(ValueError, "does not match the assigned base"):
                run_worker(workspace, workspace, [], {}, b"assigned base")
            self.assertEqual(project_files(workspace), {SOURCE: b"unexpected state"})


@unittest.skipUnless(os.environ.get("BSTACK_TEST_SUBAGENTS") == "1", "set BSTACK_TEST_SUBAGENTS=1 for the live role experiment")
class SubagentExperimentTest(unittest.TestCase):
    def test_worker_and_advisor_handoff(self):
        self.assertEqual(sys.platform, "darwin", "the live worker sandbox uses macOS sandbox-exec")
        with TemporaryDirectory(prefix="bstack-subagents-") as scratch:
            root = Path(scratch).resolve()
            parent, worker, seeded, runtime, advisor = (
                root / name for name in ("parent", "worker", "seeded", "runtime", "advisor")
            )
            for workspace in (parent, worker, seeded):
                shutil.copytree(FIXTURE, workspace)
            runtime.mkdir()
            advisor.mkdir()
            (parent / "local-note.txt").write_text("Parent's unfinished work\n")
            initial_parent = project_files(parent)
            initial_worker = project_files(worker)
            base = initial_worker[SOURCE]
            cases = ("job-17", "job-17", "job-19", "job-17")
            expected = ["job-17", "job-19"]
            self.assertEqual(observed_rows(parent, cases), list(cases))

            pi = Path(shutil.which("pi"))
            sandbox = ["sandbox-exec", "-p", worker_profile(pi, worker, runtime, parent)]
            environment = worker_environment(runtime)
            self.check_worker_boundary(sandbox, environment, parent / "local-note.txt", worker)
            messages = run_worker(worker, runtime, sandbox, environment, base)
            last = [message for message in messages if message.get("role") == "assistant"][-1]
            self.assertEqual((last.get("provider"), last.get("model")), ("deepseek", "deepseek-flash"))
            self.assertEqual(last.get("stopReason"), "stop", last.get("errorMessage"))
            trace = tool_trace(messages)
            self.assertTrue({call["name"] for call in trace} <= set(FILE_TOOLS))
            self.assertTrue(any(
                call["name"] == "read" and call["target"].endswith("bug-fix.md")
                and call["error"] is False and "# Bug fix" in call["result"]
                for call in trace
            ))
            changed = project_files(worker)
            self.assertEqual({path for path in initial_worker.keys() | changed.keys() if initial_worker.get(path) != changed.get(path)}, {SOURCE})
            candidate = changed[SOURCE]
            self.assertEqual(project_files(parent), initial_parent)
            self.assertEqual(observed_rows(worker, cases), expected)
            documented_replay(worker).check_returncode()
            print("Worker: parent workspace intact; retry and distinct IDs verified on the patch.", flush=True)

            broken = base.replace(
                b'    with output.open("a", encoding="utf-8") as stream:',
                b'    if output.exists() and output.read_text(encoding="utf-8").strip():\n'
                b'        return\n    with output.open("a", encoding="utf-8") as stream:',
            )
            self.assertNotEqual(broken, base)
            (seeded / SOURCE).write_bytes(broken)
            self.assertEqual(observed_rows(seeded, cases), ["job-17"])
            advisor_before = project_files(advisor)
            with ThreadPoolExecutor(max_workers=2) as pool:
                worker_review = pool.submit(run_advisor, advisor, base, candidate)
                seeded_review = pool.submit(run_advisor, advisor, base, broken)
                reviewed = self.check_advisor(*worker_review.result(), base, candidate)
                findings = self.check_advisor(*seeded_review.result(), base, broken)["findings"]
            self.assertEqual(project_files(advisor), advisor_before)
            self.assertEqual(project_files(parent), initial_parent)
            self.assertEqual(project_files(worker), changed)
            for finding in reviewed["findings"]:
                actual = observed_rows(worker, finding["inputs"])
                self.assertEqual(actual, list(dict.fromkeys(finding["inputs"])), finding)
            confirmed = [finding for finding in findings if self.reproduces(seeded, finding)]
            self.assertTrue(confirmed, findings)
            self.assertFalse(review_covers(reviewed, base, broken))
            print(f"Advisor: no workspace tools; seeded finding independently reproduced for {confirmed[0]['inputs']}.", flush=True)

            (parent / SOURCE).write_bytes(candidate)
            self.assertEqual(project_files(parent), {**initial_parent, SOURCE: candidate})
            self.assertEqual(observed_rows(parent, cases), expected)
            documented_replay(parent).check_returncode()
            print("Parent: integrated only the verified artifact and reran the checks.", flush=True)

    def check_worker_boundary(self, sandbox, environment, sentinel, workspace):
        probe = "from pathlib import Path; import sys; Path(sys.argv[1])"
        for target, operation in (
            (sentinel, "read_text()"),
            (sentinel, "write_text('changed')"),
            (workspace / "checks/replay_export.py", "write_text('changed')"),
        ):
            before = target.read_bytes()
            result = subprocess.run(
                [*sandbox, sys.executable, "-B", "-c", f"{probe}.{operation}", str(target)],
                cwd=workspace, env=environment, capture_output=True, text=True, timeout=15,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("PermissionError", result.stderr)
            self.assertEqual(target.read_bytes(), before)

    def check_advisor(self, setup, answer, base, candidate):
        self.assertFalse(set(setup["tools"]) - {"StructuredOutput"}, setup["tools"])
        self.assertFalse(answer["is_error"], answer.get("result"))
        self.assertEqual(set(answer["modelUsage"]), {"claude-fable-5-2"})
        report = answer["structured_output"]
        self.assertTrue(review_covers(report, base, candidate), report)
        return report

    def reproduces(self, workspace, finding):
        self.assertIn(finding["path"], (SOURCE, f"candidate/{SOURCE}"))
        inputs = finding["inputs"]
        expected = list(dict.fromkeys(inputs))
        actual = observed_rows(workspace, inputs)
        return finding["expected"] == expected and finding["predicted"] == actual and expected != actual


if __name__ == "__main__":
    unittest.main()
