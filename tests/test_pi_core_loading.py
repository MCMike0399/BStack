from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
from tempfile import TemporaryDirectory
from threading import Thread
import unittest

from pi_runner import message_text


ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "core/instructions.md"
PI = shutil.which("pi")
PROJECT_MARKER = "BStack loader fixture project instructions."


class CaptureProvider(BaseHTTPRequestHandler):
    def do_POST(self):
        request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        self.server.requests.append((self.path, request))
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        for delta, finish in (({"role": "assistant", "content": "Stub reply."}, None), ({}, "stop")):
            packet = {
                "id": "fixture", "object": "chat.completion.chunk", "created": 1, "model": "capture",
                "choices": [{"index": 0, "delta": delta, "finish_reason": finish}],
            }
            self.wfile.write(("data: " + json.dumps(packet) + "\n\n").encode())
        self.wfile.write(b"data: [DONE]\n\n")

    def log_message(self, *args):
        pass


@unittest.skipUnless(PI, "Pi CLI is needed for the offline provider capture")
class PiCoreLoadingTest(unittest.TestCase):
    def test_readme_invocations_send_one_copy(self):
        section = (ROOT / "README.md").read_text().split("## Try Burbi-mode in Pi\n", 1)[1].split("\n## ", 1)[0]
        commands = [
            shlex.split(block.replace("\\\n", ""))
            for block in re.findall(r"```sh\n(.*?)```", section, re.DOTALL)
        ]
        self.assertEqual(len(commands), 2, "Expected installed and standalone Pi examples")
        installed, standalone = commands
        with ThreadingHTTPServer(("127.0.0.1", 0), CaptureProvider) as server:
            server.requests = []
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                for name, command, link, custom_profile, expected in (
                    ("installed", installed, True, False, 1),
                    ("installed custom profile", installed, True, True, 1),
                    ("standalone", standalone, False, False, 1),
                    ("duplicate control", standalone, True, False, 2),
                    ("missing control", installed, False, False, 0),
                ):
                    with self.subTest(name=name):
                        self.assertEqual(self.capture(server, command, link, custom_profile), expected)
            finally:
                server.shutdown()
                thread.join()

    def capture(self, server, command, link, custom_profile):
        self.assertEqual(command[0], "pi")
        self.assertEqual(command[command.index("--model") + 1], "deepseek/deepseek-flash")
        command = command[1:]
        command[command.index("--model") + 1] = "bstack-fixture/capture"
        with TemporaryDirectory(prefix="bstack-loader-") as scratch:
            home = Path(scratch)
            workspace = home / "project"
            agent = home / "custom" if custom_profile else home / ".pi/agent"
            agent.mkdir(parents=True)
            (workspace / "core").mkdir(parents=True)
            shutil.copyfile(CORE, workspace / "core/instructions.md")
            shutil.copytree(ROOT / "skills/burbi-mode", workspace / "skills/burbi-mode")
            (workspace / "AGENTS.md").write_text(PROJECT_MARKER)
            if link:
                (agent / "AGENTS.md").symlink_to(workspace / "core/instructions.md")
            (agent / "models.json").write_text(json.dumps({
                "providers": {"bstack-fixture": {
                    "baseUrl": f"http://127.0.0.1:{server.server_port}/v1",
                    "api": "openai-completions",
                    "apiKey": "fixture",
                    "models": [{"id": "capture", "name": "Loopback capture"}],
                }},
            }))
            data_home = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
            bundled_node = data_home / "pi-node/current/bin"
            environment = {
                "PATH": os.pathsep.join((str(bundled_node), os.environ["PATH"])),
                "HOME": scratch, "TMPDIR": scratch,
            }
            if custom_profile:
                environment["PI_CODING_AGENT_DIR"] = str(agent)
            server.requests.clear()
            result = subprocess.run(
                [PI, *command, "--print", "--offline", "--no-session", "--no-extensions", "--no-mcp",
                 "--no-skills", "--no-prompt-templates", "--no-themes", "--tools", "read", "--thinking", "off",
                 "--", "/skill:burbi-mode Loopback probe."],
                cwd=workspace, env=environment, text=True, capture_output=True, timeout=20,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Stub reply.", result.stdout)
        self.assertEqual(len(server.requests), 1)
        endpoint, request = server.requests[0]
        self.assertEqual(endpoint, "/v1/chat/completions")
        self.assertEqual(request["model"], "capture")
        system = "\n".join(message_text(message) for message in request["messages"] if message["role"] == "system")
        user = "\n".join(message_text(message) for message in request["messages"] if message["role"] == "user")
        self.assertIn(PROJECT_MARKER, system)
        self.assertIn("## Choose a playbook", user)
        return system.count(CORE.read_text().strip())
