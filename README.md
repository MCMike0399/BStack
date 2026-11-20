# BStack

Engineering guidance for coding agents, under design.

- [The core](core/instructions.md) is a one-line standing instruction for ordinary requests.
- [Burbi-mode](skills/burbi-mode/SKILL.md) is an opt-in skill for engineering work.

Development continues on `main`. Pi with DeepSeek V4.1 Flash is the first test environment.

## Try Burbi-mode in Pi

Run from the repository root with a configured DeepSeek connection.

```sh
pi --model deepseek/deepseek-flash \
  --append-system-prompt core/instructions.md \
  --skill skills/burbi-mode/SKILL.md
```

Start an engineering request with `/skill:burbi-mode`. Burbi-mode selects a playbook for the requested outcome and uses the project's guidance to find relevant docs and checks. The parent opens the shared [Architecture reference](skills/burbi-mode/references/architecture.md) when the work depends on an unresolved design decision. Ask ordinary questions as plain text.

## Test the playbooks

Run `python3 -B -m unittest discover -s tests` to check the skill and its links. With Pi and a DeepSeek connection configured, run `BSTACK_TEST_PI=1 python3 -B -m unittest discover -s tests -v` for live checks. These use disposable export-worker fixtures and check the selected playbook, the edits made, and the behavior of the resulting code.

## Try the subagent experiment

On macOS with Pi, DeepSeek, and `claude-auto` configured, run the Worker and Advisor pilot against disposable copies of the export fixture.

```sh
BSTACK_TEST_SUBAGENTS=1 python3 -B -m unittest discover -s tests -p test_subagents.py -v
```

The pilot runs one Pi Worker and reviews the resulting patch and a seeded regression in separate Fable sessions. The parent verifies the outputs before integrating the patch into its own fixture. [Subagent research](docs/subagents-research.md)
