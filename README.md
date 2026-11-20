# BStack

Engineering guidance for coding agents, under design. The aim is engineer-grade output on everyday software work, on any model: turn recurring corrections into design, type, lint, and test checks before prose, and verify on real artifacts.

- [The core](core/instructions.md) is a one-line standing instruction for ordinary requests.
- [Burbi-mode](skills/burbi-mode/SKILL.md) is the entry point for engineering work, invoked explicitly. It loads whole on each invocation and opens one playbook and only the references whose condition applies, so its size is budgeted by a test.

Development continues on `main`. Pi with DeepSeek V4.1 Flash is the first test environment because it follows wording literally.

## Try Burbi-mode in Pi

Run from the repository root with a configured DeepSeek connection. Check
`~/.pi/agent/AGENTS.md` or the corresponding file under your
`PI_CODING_AGENT_DIR` if you use a custom profile. If that profile already
loads the BStack core, use the command below.

```sh
pi --model deepseek/deepseek-flash \
  --skill skills/burbi-mode/SKILL.md
```

For a Pi profile without the core, append it for this invocation.

```sh
pi --model deepseek/deepseek-flash \
  --append-system-prompt core/instructions.md \
  --skill skills/burbi-mode/SKILL.md
```

Start an engineering request with `/skill:burbi-mode`. Burbi-mode selects a playbook for the requested outcome, opens a reference such as [Architecture](skills/burbi-mode/references/architecture.md) only when its condition applies, and uses the project's guidance to find relevant docs and checks. Ask ordinary questions as plain text.

## Test the playbooks

Run `python3 -B -m unittest discover -s tests` to check the skill and its links.
If Pi is on PATH, this also exercises the README invocations in isolated
profiles using a loopback provider with no DeepSeek credentials. The loader
check has been exercised with Pi 1.5.0. With Pi and a DeepSeek
connection configured, run `BSTACK_TEST_PI=1 python3 -B -m unittest discover -s tests -v`
for live checks. These use disposable export-worker fixtures and check the
selected playbook, the edits made, and the behavior of the resulting code.

## Compare guidance with an eval

Run the [export timing eval](docs/eval-export-timing.md) to compare how two
guidance configurations investigate the same benchmark claim.

## Try the subagent experiment

On macOS with Pi, DeepSeek, and `claude-auto` configured, run the Worker and Advisor pilot against disposable copies of the export fixture.

```sh
BSTACK_TEST_SUBAGENTS=1 python3 -B -m unittest discover -s tests -p test_subagents.py -v
```

The pilot runs one Pi Worker and reviews the resulting patch and a seeded regression in separate Fable sessions. The parent verifies the outputs before integrating the patch into its own fixture. [Subagent research](docs/subagents-research.md)
