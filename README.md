# BStack

Engineering guidance for coding agents, under design.

- [The core](core/instructions.md) is a one-line standing instruction for ordinary requests.
- [Burbi-mode](skills/burbi-mode/SKILL.md) is an opt-in skill for engineering work.

Draft rules are reviewed through pull requests. Pi with DeepSeek V4.1 Flash is the first test environment.

## Try Burbi-mode in Pi

Run from the repository root with a configured DeepSeek connection.

```sh
pi --model deepseek/deepseek-flash \
  --append-system-prompt core/instructions.md \
  --skill skills/burbi-mode/SKILL.md
```

Start an engineering request with `/skill:burbi-mode`. Ask ordinary questions as plain text.
