"""Status latency and diagnostics with fake SSH; never contacts real hosts."""
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import time
import unittest

RAH = Path(__file__).resolve().parents[1] / 'rah'


class StatusTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='rah-status-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = self.root / 'config'
        self.config.mkdir()
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.env = dict(os.environ, HOME=str(self.root), RAH_CONFIG_DIR=str(self.config),
                        RAH_COLOR='never', TMPDIR=str(self.root),
                        PATH=f'{self.bin}:{os.environ["PATH"]}',
                        STATUS_CALLS=str(self.root / 'calls'))
        self.lib = self.root / 'lib.sh'
        self.lib.write_text(RAH.read_text().rsplit('main "$@"', 1)[0])
        ssh = self.bin / 'ssh'
        ssh.write_text(f'#!{sys.executable}\n' + '''
import json,os,signal,subprocess,sys,time
args=sys.argv[1:]
with open(os.environ['STATUS_CALLS'], 'a') as f:
 f.write(json.dumps(args)+'\\n')
assert '-M' not in args and '-O' not in args
assert 'BatchMode=yes' in args and 'ControlMaster=no' in args
assert 'ControlPath=none' in args and 'ControlPersist=no' in args
host=args[-2]
if host == 'offline': sys.exit(255)
if host == 'blackhole':
 signal.signal(signal.SIGTERM, signal.SIG_IGN)
 time.sleep(30)
else:
 sys.exit(subprocess.call(['bash','-c',args[-1]]))
''')
        ssh.chmod(0o755)
        systemctl = self.bin / 'systemctl'
        systemctl.write_text('#!/bin/bash\nexit 1\n')
        systemctl.chmod(0o755)

    def config_mount(self, name, host='ok', remote=None, prelude=''):
        mp = self.root / name
        mp.mkdir()
        path = self.config / f'{name}.env'
        path.write_text(f'host={host}\nmountpoint={mp}\nremote_path={remote or mp}\n'
                        f'prelude={prelude}\ncontrol_socket={self.root}/unused-socket\n')
        return path

    def run_status(self, *args, timeout=10):
        start = time.monotonic()
        result = subprocess.run(['bash', str(RAH), 'status', '--no-agents', *args],
                                env=self.env, cwd=self.root, text=True,
                                capture_output=True, timeout=timeout)
        elapsed = time.monotonic() - start
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(list(self.root.glob('rah-status.*')), 'temporary results leaked')
        return result, elapsed

    def calls(self):
        return [json.loads(line) for line in (self.root / 'calls').read_text().splitlines()]

    def test_unreachable_ssh_is_not_retried_for_execution(self):
        self.config_mount('demo', 'offline')
        r, elapsed = self.run_status()
        self.assertLess(elapsed, 2)
        self.assertIn('[FAILED]', r.stdout)
        self.assertIn('[not checked] SSH unavailable', r.stdout)
        self.assertEqual(len(self.calls()), 1)
        self.assertFalse((self.root / 'unused-socket.lock').exists())

    def test_multiple_hung_hosts_share_one_timeout_window(self):
        for name in ['a', 'b', 'c', 'd']:
            self.config_mount(name, 'blackhole')
        r, elapsed = self.run_status(timeout=8)
        self.assertGreater(elapsed, 3)
        self.assertLess(elapsed, 6, r.stdout)
        self.assertEqual(r.stdout.count('[TIMEOUT] exceeded 3s'), 4)
        self.assertEqual(len(self.calls()), 4)

    def test_bad_remote_directory_does_not_mean_ssh_failed(self):
        self.config_mount('demo', remote=self.root / 'missing')
        r, _ = self.run_status()
        self.assertIn('ssh:        [reachable]', r.stdout)
        self.assertIn('exec:       [FAILED]', r.stdout)

    def test_prelude_failure_is_an_execution_failure(self):
        self.config_mount('demo', prelude='false')
        r, _ = self.run_status()
        self.assertIn('ssh:        [reachable]', r.stdout)
        self.assertIn('exec:       [FAILED]', r.stdout)

    def test_prelude_timeout_reports_connected_ssh(self):
        self.config_mount('demo', prelude='sleep 30')
        r, elapsed = self.run_status(timeout=6)
        self.assertLess(elapsed, 5)
        self.assertIn('ssh:        [reachable]', r.stdout)
        self.assertIn('exec:       [TIMEOUT]', r.stdout)

    def test_healthy_unmounted_project_and_quoted_paths(self):
        self.config_mount("a project's directory", prelude='export STATUS_TEST=works')
        r, _ = self.run_status()
        self.assertIn('[not mounted]', r.stdout)
        self.assertIn('exec:       [remote ok]', r.stdout)
        self.assertEqual(len(self.calls()), 1)

    def test_selected_mount_does_not_probe_unrelated_host(self):
        self.config_mount('healthy')
        self.config_mount('unrelated', 'blackhole')
        r, elapsed = self.run_status('healthy')
        self.assertLess(elapsed, 2)
        self.assertNotIn('unrelated\n', r.stdout)
        self.assertEqual(len(self.calls()), 1)

    def test_systemd_snapshot_is_one_bounded_query(self):
        self.config_mount('demo')
        script = '''
source "$1"
_systemd_mount_unit_name() { echo rah-mount@demo.service; }
_timeout() {
  echo "$*" >> "$RAH_CONFIG_DIR/systemctl-calls"
  cat <<'SNAPSHOT'
Id=rah-mount@demo.service
UnitFileState=enabled
ActiveState=active

ActiveState=active
Id=rah-health@demo.timer
UnitFileState=enabled
SNAPSHOT
}
_autostart_status_systemd
'''
        r = subprocess.run(['bash', '-c', script, 'bash', str(self.lib)],
                           env=self.env, capture_output=True, text=True, timeout=3)
        self.assertEqual(r.returncode, 0, r.stderr)
        calls = (self.config / 'systemctl-calls').read_text().splitlines()
        self.assertEqual(len(calls), 1)
        self.assertTrue(calls[0].startswith('3 systemctl --user show '))
        self.assertIn('1/1 enabled, 1 active', r.stdout)
        self.assertIn('1/1 timers active', r.stdout)

    def test_unresponsive_systemd_does_not_add_a_second_timeout_window(self):
        self.config_mount('demo', 'blackhole')
        (self.bin / 'systemctl').write_text('#!/bin/bash\ntrap "" TERM\nexec sleep 30\n')
        r, elapsed = self.run_status(timeout=8)
        self.assertLess(elapsed, 6)
        self.assertIn('systemd query failed or exceeded 3s', r.stdout)
        self.assertIn('[TIMEOUT] exceeded 3s', r.stdout)


if __name__ == '__main__':
    unittest.main()
