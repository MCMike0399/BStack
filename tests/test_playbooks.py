from pathlib import Path
import ast
import re
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/burbi-mode/SKILL.md"


class PlaybookFilesTest(unittest.TestCase):
    def test_router_links_to_each_playbook_once(self):
        router = SKILL.read_text().split("## Engineering rules", 1)[0]
        targets = re.findall(r"\]\((playbooks/[^)]+\.md)\)", router)
        files = [str(path.relative_to(SKILL.parent)) for path in SKILL.parent.glob("playbooks/*.md")]
        self.assertTrue(targets)
        self.assertCountEqual(targets, files)
        for target in targets:
            with self.subTest(playbook=target):
                content = (SKILL.parent / target).read_text()
                self.assertTrue(content.startswith("# "))
                self.assertIn("\n1. ", content)

    def test_every_skill_file_is_reachable_and_links_resolve(self):
        files = {path.resolve() for path in SKILL.parent.rglob("*.md")}
        reached, pending = set(), [SKILL.resolve()]
        while pending:
            source = pending.pop()
            if source in reached:
                continue
            reached.add(source)
            for target in re.findall(r"\]\(([^)#:]+\.md)(?:#[^)]*)?\)", source.read_text()):
                path = (source.parent / target).resolve()
                with self.subTest(source=source.name, link=target):
                    self.assertTrue(path.is_file())
                    self.assertTrue(path.is_relative_to(SKILL.parent.resolve()))
                if path in files:
                    pending.append(path)
        self.assertEqual(sorted(str(path) for path in files - reached), [])

    def test_files_stay_within_their_loading_budgets(self):
        # Burbi-mode loads SKILL.md whole on every invocation, and each route loads
        # one playbook plus the references whose condition applies. These caps are
        # ratchets, not measured thresholds: raise one only when the added text is
        # worth its cost on every task that loads the file. docs/rule-loading-research.md
        # measured the entry file's cost; docs/pstack-adoption.md and
        # docs/workflow-organization.md record the caps.
        self.assertLessEqual(len(SKILL.read_bytes()), 17_100)
        for folder, cap in (("playbooks", 3_500), ("references", 4_500), ("roles", 1_500)):
            for path in (SKILL.parent / folder).glob("*.md"):
                with self.subTest(path=path.name):
                    self.assertLessEqual(len(path.read_bytes()), cap)

    def test_link_labels_match_the_target_titles(self):
        for source in SKILL.parent.rglob("*.md"):
            for label, target in re.findall(r"\[([^\]]+)\]\(([^)#:]+\.md)\)", source.read_text()):
                title = (source.parent / target).read_text().splitlines()[0].removeprefix("# ")
                with self.subTest(source=source.name, link=target):
                    self.assertEqual(label, title)

    def test_router_names_every_reference_condition(self):
        section = SKILL.read_text().split("## Open a reference", 1)[1].split("\n## ", 1)[0]
        targets = re.findall(r"\]\((references/[^)]+\.md)\)", section)
        files = [str(path.relative_to(SKILL.parent)) for path in SKILL.parent.glob("references/*.md")]
        self.assertCountEqual(targets, files)

    def test_rule_and_step_citations_resolve(self):
        rules = SKILL.read_text().split("## Engineering rules", 1)[1]
        rule_count = len(re.findall(r"^\d+\. ", rules, re.M))
        for path in SKILL.parent.rglob("*.md"):
            text = path.read_text()
            for number in re.findall(r"\brules? (\d+)", text, re.I):
                with self.subTest(path=path.name, rule=number):
                    self.assertLessEqual(int(number), rule_count)
            if path == SKILL:
                continue
            steps = len(re.findall(r"^\d+\. ", text, re.M))
            for match in re.finditer(r"\bsteps? (\d+)(?:(?:,| and| to) (\d+))*", text):
                for number in re.findall(r"\d+", match.group(0)):
                    with self.subTest(path=path.name, step=number):
                        self.assertLessEqual(int(number), steps)

    def test_skill_text_is_portable_and_uses_one_vocabulary(self):
        core = (ROOT / "core/instructions.md").read_text().strip()
        self.assertIn(core, (SKILL.parent / "references/delegation.md").read_text())
        for path in SKILL.parent.rglob("*.md"):
            text = path.read_text().split("Illustration only.", 1)[0]
            if path == SKILL:
                text = text.removeprefix("---\n").partition("\n---\n")[2]
            for term in ("export_worker", "job-17", "BStack", "invoking agent", "task record"):
                with self.subTest(path=path.name, term=term):
                    self.assertNotIn(term, text)

    def test_project_verification_links_repeat_the_router_condition(self):
        condition = "a running app, device, or external dependency the usual checks do not exercise"
        self.assertIn(condition, SKILL.read_text())
        for path in SKILL.parent.rglob("*.md"):
            for line in path.read_text().splitlines():
                if path != SKILL and "project-verification.md)" in line:
                    with self.subTest(path=path.name):
                        self.assertIn(condition, line)

    def test_every_playbook_has_a_live_case(self):
        tree = ast.parse((ROOT / "tests/test_pi_playbooks.py").read_text())
        covered = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "Case" and len(node.args) > 1:
                value = ast.literal_eval(node.args[1])
                covered.update((value,) if isinstance(value, str) else value)
        self.assertEqual(covered, {path.stem for path in SKILL.parent.glob("playbooks/*.md")})

    def test_core_and_skill_keep_separate_invocation(self):
        core = (ROOT / "core/instructions.md").read_text()
        self.assertEqual(len(core.splitlines()), 1)
        self.assertTrue(core.strip())
        frontmatter, _, instructions = SKILL.read_text().removeprefix("---\n").partition("\n---\n")
        self.assertIn("disable-model-invocation: true", frontmatter.splitlines())
        rules = instructions.split("## Engineering rules", 1)[1]
        numbers = [int(number) for number in re.findall(r"^(\d+)\. ", rules, re.M)]
        self.assertTrue(numbers)
        self.assertEqual(numbers, list(range(1, len(numbers) + 1)))

    def test_fixture_reproduces_the_reported_failure(self):
        run = subprocess.run(
            [sys.executable, "checks/replay_export.py"],
            cwd=ROOT / "tests/fixtures/exports",
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(run.returncode, 1, run.stderr)
        self.assertEqual(run.stdout, "Observed ['job-17', 'job-17'], expected ['job-17']\n")


if __name__ == "__main__":
    unittest.main()
