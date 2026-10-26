"""Local execution and hook routing checks without SSH or real mounts.

Run with: python3 -m unittest discover -s tests
"""

import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest


RAH = Path(__file__).resolve().parents[1] / "rah"


class LocalExecutionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="rah-local-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.mount = self.root / "mount b"
        self.mount.mkdir()
        self.config = self.root / "config"
        self.config.mkdir()
        (self.config / "b.env").write_text(
            f"mountpoint={self.mount}\nremote_path=/remote/project\n"
            "host=unused.invalid\n"
        )
        # Suppress opportunistic remount probes in this isolated hook fixture.
        (self.config / ".heal.b").touch()
        self.env = dict(os.environ, RAH_CONFIG_DIR=str(self.config), RAH_HOOK_LOG="0")

    def run_rah(self, *args, input=None):
        return subprocess.run(
            ["bash", str(RAH), *args], cwd=self.mount, env=self.env,
            input=input, text=True, capture_output=True,
        )

    def test_preserves_arguments_without_shell_evaluation(self):
        args = ["with spaces", "", "'quoted'", "$(echo wrong)", "*", "a;b"]
        result = self.run_rah(
            "local", "--", sys.executable, "-c",
            "import json,sys; print(json.dumps(sys.argv[1:]))", *args,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), args)

    def test_preserves_stdin_stderr_and_exit_status(self):
        result = self.run_rah(
            "local", "--", "bash", "-c",
            "cat; printf problem >&2; exit 37", input="local input\n",
        )
        self.assertEqual(result.stdout, "local input\n")
        self.assertEqual(result.stderr, "problem")
        self.assertEqual(result.returncode, 37)

    def test_working_directory_and_reading_another_mount(self):
        result = self.run_rah("local", "--", "pwd")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), str(self.mount))
        other = self.root / "mount c"
        other.mkdir()
        (other / "file.txt").write_text("content from C\n")
        result = self.run_rah("local", "--cwd", str(other), "--", "cat", "file.txt")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "content from C\n")

    def test_invalid_invocations_do_not_execute(self):
        for args in [(), ("--",), ("--cwd",), ("--cwd", ""), ("--unknown",)]:
            with self.subTest(args=args):
                self.assertNotEqual(self.run_rah("local", *args).returncode, 0)
        result = self.run_rah(
            "local", "--cwd", str(self.root / "missing"), "--", "printf", "wrong",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def hook(self, command):
        return self.run_rah(
            "hook", "--decision", "allow", "--passthrough", "empty",
            input=json.dumps({"tool_name": "command_execution", "cwd": str(self.mount),
                              "tool_input": {"command": command}}),
        )

    def test_hook_escape_and_default_routing(self):
        local_command = f"{shlex.quote(str(RAH))} local -- printf local-ok"
        for command in [local_command, "rah local -- cat /mnt/c/file.txt",
                        "rah run --cwd /mnt/c -- cat file.txt"]:
            with self.subTest(command=command):
                result = self.hook(command)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, "")
        result = subprocess.run(
            ["bash", "-c", local_command], cwd=self.mount, env=self.env,
            text=True, capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "local-ok")
        result = self.hook("cat /mnt/c/file.txt")
        self.assertEqual(result.returncode, 0, result.stderr)
        rewritten = json.loads(result.stdout)["hookSpecificOutput"]["updatedInput"]["command"]
        self.assertTrue(rewritten.startswith("rah run --cwd "))
        self.assertIn(shlex.quote(str(self.mount)), rewritten)
        self.assertFalse((self.config / "local-allow").exists())

    def rewritten(self, command):
        result = self.hook(command)
        self.assertEqual(result.returncode, 0, result.stderr)
        if not result.stdout:
            return None
        return json.loads(result.stdout)["hookSpecificOutput"]["updatedInput"]["command"]

    def test_local_cmds_route_by_program_word(self):
        self.assertTrue(self.rewritten("gh pr list").startswith("rah run --cwd "))
        self.assertEqual(self.run_rah("local-cmds", "--global", "set", "gh", "codex", "tool.sh").returncode, 0)
        for command in ["gh pr list", "GH_PAGER=cat gh pr view 3", "env gh auth status",
                        "/usr/bin/gh repo view", 'codex exec "review this"',
                        '"/opt/my tools/codex" exec x', "'/plugins/1.2/tool.sh' q",
                        "X=1 /plugins/1.3/tool.sh q"]:
            with self.subTest(command=command):
                self.assertIsNone(self.rewritten(command))
        self.assertTrue(self.rewritten("git status").startswith("rah run --cwd "))
        self.assertEqual(self.run_rah("local-cmds", "set", "git").returncode, 0)
        self.assertIsNone(self.rewritten("git status"))
        self.assertTrue(self.rewritten("gh pr list").startswith("rah run --cwd "))
        self.assertEqual(self.run_rah("local-cmds", "set").returncode, 0)
        self.assertTrue(self.rewritten("git status").startswith("rah run --cwd "))
        self.assertEqual(self.run_rah("local-cmds", "reset").returncode, 0)
        self.assertIsNone(self.rewritten("gh pr list"))
        self.assertEqual(self.run_rah("local-cmds", "--global", "reset").returncode, 0)
        self.assertTrue(self.rewritten("gh pr list").startswith("rah run --cwd "))

    def test_local_command_later_in_remote_line_is_refused(self):
        self.assertEqual(self.run_rah("local-cmds", "--global", "set", "gh").returncode, 0)
        for command in ["git push && gh pr create", "ls; rah local -- hostname",
                        "make |\nrah local -- cat x"]:
            with self.subTest(command=command):
                rewritten = self.rewritten(command)
                result = subprocess.run(["bash", "-c", rewritten], text=True,
                                        capture_output=True)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertIn("first word", result.stderr)
        for command in ['echo "a b" | grep gh', "cd sub && make"]:
            with self.subTest(command=command):
                self.assertTrue(self.rewritten(command).startswith("rah run --cwd "))

    def test_session_context_describes_routing(self):
        self.assertEqual(self.run_rah("local-cmds", "--global", "set", "gh").returncode, 0)
        result = self.run_rah("session-context", input=json.dumps({"cwd": str(self.mount)}))
        self.assertEqual(result.returncode, 0, result.stderr)
        context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertIn(f"{self.mount} is an SSHFS mount of unused.invalid:/remote/project", context)
        self.assertIn("first word is one of: gh", context)
        result = self.run_rah("session-context", input=json.dumps({"cwd": str(self.root)}))
        self.assertEqual((result.returncode, result.stdout), (0, ""))

    def test_hook_rewrite_keeps_other_tool_input_fields(self):
        tool_input = {"command": "tail -f log", "description": "watch log",
                      "timeout_ms": 60000, "run_in_background": True}
        result = self.run_rah(
            "hook", "--decision", "allow",
            input=json.dumps({"tool_name": "Monitor", "cwd": str(self.mount),
                              "tool_input": tool_input}),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        updated = json.loads(result.stdout)["hookSpecificOutput"]["updatedInput"]
        self.assertTrue(updated.pop("command").startswith("rah run --cwd "))
        tool_input.pop("command")
        self.assertEqual(updated, tool_input)


if __name__ == "__main__":
    unittest.main()
