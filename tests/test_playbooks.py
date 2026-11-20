from pathlib import Path
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
