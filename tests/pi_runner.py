import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "core/instructions.md"
SKILL = ROOT / "skills/burbi-mode/SKILL.md"
MODEL = "deepseek/deepseek-flash"
THINKING = "low"
FILE_TOOLS = ("read", "bash", "edit", "write", "grep", "find", "ls")


def deepseek_key():
    response = subprocess.run(
        ["pi", "auth", "print-api-key", "--provider", "deepseek", "--model", "deepseek-flash"],
        capture_output=True, text=True, timeout=15,
    )
    key = response.stdout.strip()
    if response.returncode or not key:
        raise RuntimeError("Pi did not resolve a DeepSeek API key")
    return key


def run_pi(workspace, runtime, key, prompt, *, skill=SKILL, core=CORE, tools=FILE_TOOLS, prefix=(), tool_env=None, timeout=150):
    profile = runtime / "pi"
    profile.mkdir()
    scratch = shlex.quote(str(runtime))
    (profile / "settings.json").write_text(json.dumps({
        "shellCommandPrefix": f"unset DEEPSEEK_API_KEY\nexport HOME={scratch} TMPDIR={scratch}",
    }))
    inherited = ("PATH", "HOME", "LANG", "LC_ALL", "XDG_DATA_HOME", "SSL_CERT_FILE", "SSL_CERT_DIR")
    environment = {
        **{name: os.environ[name] for name in inherited if name in os.environ},
        "TMPDIR": str(runtime),
        "PI_CODING_AGENT_DIR": str(profile),
        "DEEPSEEK_API_KEY": key,
        "PYTHONDONTWRITEBYTECODE": "1",
        **(tool_env or {}),
    }
    command = [
        *prefix, "pi", "--print", "--mode", "json", "--model", MODEL, "--thinking", THINKING,
        "--offline", "--no-session", "--no-extensions", "--no-mcp", "--no-prompt-templates",
        "--no-themes", "--no-skills", "--no-approve",
    ]
    command.extend(("--tools", ",".join(tools)) if tools else ("--no-tools",))
    if core is not None:
        command.extend(("--append-system-prompt", str(core)))
    if skill is not None:
        command.extend(("--skill", str(skill)))
        prompt = f"/skill:burbi-mode {prompt}"
    run = subprocess.run(
        [*command, "--", prompt], cwd=workspace, env=environment, capture_output=True, text=True, timeout=timeout,
    )
    if run.returncode:
        raise RuntimeError(f"Pi exited {run.returncode}. {run.stderr.strip().replace(key, '[redacted]')}")
    return [json.loads(line) for line in run.stdout.replace(key, "[redacted]").splitlines() if line.startswith("{")]


def messages_from(events):
    return [event["message"] for event in events if event.get("type") == "message_end"]


def message_text(message):
    content = message["content"]
    if isinstance(content, str):
        return content
    return "\n".join(block["text"] for block in content if block.get("type") == "text")


def tool_trace(messages):
    calls = {}
    for message in messages:
        if message.get("role") == "assistant":
            for block in message.get("content", []):
                if block.get("type") == "toolCall":
                    args = block.get("arguments", {})
                    calls[block["id"]] = {
                        "name": block["name"], "target": args.get("path") or args.get("command") or "",
                        "result": "", "error": None,
                    }
        if message.get("role") == "toolResult" and message.get("toolCallId") in calls:
            call = calls[message["toolCallId"]]
            call["error"] = message.get("isError")
            call["result"] = message_text(message)
    return list(calls.values())


def read_only_prefix(workspace, runtime, snapshots):
    sandbox = shutil.which("sandbox-exec")
    if not sandbox:
        return ()
    home = Path.home().resolve()
    pi = Path(shutil.which("pi"))
    node = shutil.which("node")
    readable = [pi, pi.resolve(), home / ".pi/agent/install", home / ".local/share/pi-node",
                workspace, runtime, snapshots]
    if node:
        readable.append(Path(node).resolve())
    allowed = " ".join(f"(subpath {json.dumps(str(path))})" for path in readable)
    profile = (
        f"(version 1) (allow default) (deny file-write*) "
        f"(allow file-write* (literal \"/dev/null\") (subpath {json.dumps(str(runtime))})) "
        f"(deny file-read-data (subpath {json.dumps(str(home))})) "
        f"(allow file-read-data {allowed})"
    )
    return (sandbox, "-p", profile)
