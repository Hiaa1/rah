"""Failure-path regression tests, isolated from real mounts and user services."""
import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import time
import unittest

RAH = Path(__file__).resolve().parents[1] / 'rah'


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='rah-recovery-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.lib = self.root / 'lib.sh'
        self.lib.write_text(RAH.read_text().rsplit('main "$@"', 1)[0])
        self.config = self.root / 'config'
        self.config.mkdir()
        (self.config / 'demo.env').write_text('mountpoint=/fake/mount\nhost=unused\n')
        self.env = dict(os.environ, RAH_CONFIG_DIR=str(self.config),
                        XDG_CONFIG_HOME=str(self.root), RAH_BIN_DIR=str(RAH.parent))

    def bash(self, script, timeout=10):
        return subprocess.run(['bash', '-c', 'source "$1"\n' + script,
                               'bash', str(self.lib)], env=self.env,
                              text=True, capture_output=True, timeout=timeout)

    def test_mount_table_does_not_touch_mount(self):
        r = self.bash('stat() { exit 90; }; mountpoint() { exit 91; }; '
                      '_is_mountpoint /; ! _is_mountpoint /nonexistent-rah-path')
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_missing_mount_is_unmounted_without_stat(self):
        r = self.bash('_is_mountpoint() { return 1; }; '
                      '_timeout() { exit 92; }; _mount_state /missing')
        self.assertEqual(r.stdout.strip(), 'unmounted')

    def test_probe_bypasses_root_cache_and_accepts_only_enoent(self):
        for error, expected in [('No such file or directory', 'mounted'),
                                ('Transport endpoint is not connected', 'dead'),
                                ('Permission denied', 'dead')]:
            with self.subTest(error=error):
                r = self.bash('''
_is_mountpoint() { return 0; }
_timeout() {
  [ "$3" != /fake/mount ] || return 0
  case "$3" in /fake/mount/.rah-health-*) ;; *) exit 93 ;; esac
  echo "stat: $ERROR" >&2; return 1
}
ERROR=''' + shlex.quote(error) + '\n_mount_state /fake/mount')
                self.assertEqual(r.stdout.strip(), expected, r.stderr)

    def test_timeout_kills_term_ignoring_process(self):
        start = time.monotonic()
        r = self.bash("_timeout 1 bash -c 'trap \"\" TERM; exec sleep 30'", timeout=5)
        self.assertNotEqual(r.returncode, 0)
        self.assertLess(time.monotonic() - start, 4)

    def test_watchdog_only_restarts_unhealthy_active_service(self):
        for active, health, restart in [('active', 'dead', True),
                                        ('active', 'unmounted', True),
                                        ('active', 'mounted', False),
                                        ('inactive', 'dead', False),
                                        ('activating', 'dead', False)]:
            with self.subTest(active=active, health=health):
                r = self.bash('''
_systemd_mount_unit_name() { echo rah-mount@demo.service; }
systemctl() {
  if [ "$2" = show ]; then echo ''' + active + '''; else echo "ACTION:$*"; fi
}
_mount_state() { echo ''' + health + '''; }
cmd_systemd_health demo
''')
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual('try-restart' in r.stdout, restart)
                if restart:
                    self.assertIn('--no-block try-restart rah-mount@demo.service', r.stdout)

    def test_watchdog_respects_stop_during_probe(self):
        r = self.bash('''
_systemd_mount_unit_name() { echo rah-mount@demo.service; }
systemctl() {
  if [ "$2" = show ]; then
    if [ -f "$RAH_CONFIG_DIR/stopped" ]; then echo inactive; else echo active; fi
  else echo UNEXPECTED; fi
}
_mount_state() { touch "$RAH_CONFIG_DIR/stopped"; echo dead; }
cmd_systemd_health demo
''')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn('UNEXPECTED', r.stdout)

    def test_failed_start_cleanup_never_probes_filesystem(self):
        r = self.bash('''
_mount_state() { exit 94; }
_mount_alive() { exit 95; }
_is_mountpoint() { return 0; }
_unmount_fuse() { echo "detach:$1"; }
cmd_systemd_unmount demo
''')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('detach:/fake/mount', r.stdout)

    def test_service_mount_does_not_need_execution_master(self):
        fake = self.root / 'sshfs'
        fake.write_text('#!/bin/bash\nprintf "%s\\n" "$@"\n')
        fake.chmod(0o755)
        common = '''
_sshfs_bin() { echo ''' + shlex.quote(str(fake)) + '''; }
_ensure_master() { echo UNEXPECTED_MASTER >&2; return 1; }
_is_mountpoint() { return 1; }
_timeout() { shift; if [ "$1" = ssh ]; then echo Linux; else "$@"; fi; }
'''
        for foreground in (0, 1):
            r = self.bash(common + f'_do_mount unused /remote /fake/mount socket "" {foreground}')
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn('ControlPath=none', r.stdout)
            self.assertNotIn('UNEXPECTED_MASTER', r.stderr)
            self.assertEqual('reconnect,' in r.stdout, foreground == 0)
            self.assertEqual('\n-f\n' in '\n' + r.stdout, foreground == 1)

    def test_generated_units_have_failure_cleanup_and_independent_timer(self):
        r = self.bash('_ensure_path() { :; }; _write_systemd_autostart')
        self.assertEqual(r.returncode, 0, r.stderr)
        unit_dir = self.root / 'systemd/user'
        mount = (unit_dir / 'rah-mount@.service').read_text()
        self.assertIn('ExecStopPost=', mount)
        self.assertIn('Restart=always', mount)
        self.assertIn('StartLimitIntervalSec=0', mount)
        self.assertIn('WorkingDirectory=/', mount)
        self.assertIn(str(self.config), mount)
        timer = (unit_dir / 'rah-health@.timer').read_text()
        self.assertIn('OnUnitInactiveSec=15s', timer)
        health = (unit_dir / 'rah-health@.service').read_text()
        self.assertIn('TimeoutStartSec=12s', health)

    def test_hook_does_not_probe_mount_in_foreground(self):
        r = self.bash('''
_mount_state() { sleep 5; echo dead; }
_self_path() { echo /bin/true; }
cmd_hook --decision allow --passthrough empty <<'JSON'
''' + json.dumps({'tool_name': 'command_execution', 'cwd': '/fake/mount',
                  'tool_input': {'command': 'echo hi'}}) + '\nJSON\n', timeout=2)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('rah run --cwd', r.stdout)

    def test_mount_preparation_fails_closed_when_directory_scan_fails(self):
        mp = self.root / 'mount'
        mp.mkdir()
        r = self.bash('''
_is_mountpoint() { return 1; }
_timeout() { shift; if [ "$1" = find ]; then return 124; fi; "$@"; }
_prepare_mountpoint ''' + shlex.quote(str(mp)))
        self.assertNotEqual(r.returncode, 0)

    def test_missing_service_config_stops_retrying(self):
        r = self.bash('cmd_systemd_mount removed')
        self.assertEqual(r.returncode, 78)

    def test_concurrent_remounts_are_serialized(self):
        r = self.bash('''
_mount_state() { if [ -f "$RAH_CONFIG_DIR/live" ]; then echo mounted; else echo unmounted; fi; }
_systemd_mount_service_enabled() { return 1; }
_prepare_mountpoint() { echo /fake/mount; }
_do_mount() { echo mount >> "$RAH_CONFIG_DIR/attempts"; sleep 0.2; touch "$RAH_CONFIG_DIR/live"; }
_wait_for_mount() { return 0; }
_remount_one demo 0 &
_remount_one demo 0 &
wait
wc -l < "$RAH_CONFIG_DIR/attempts"
''')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip().splitlines()[-1], '1')

    def test_force_remount_clears_dead_mount_before_preparing(self):
        r = self.bash('''
_mount_state() { echo dead; }
_systemd_mount_service_enabled() { return 1; }
_unmount_fuse() { touch "$RAH_CONFIG_DIR/detached"; }
_prepare_mountpoint() { [ -f "$RAH_CONFIG_DIR/detached" ] || return 1; echo /fake/mount; }
_do_mount() { echo recovered; }
_wait_for_mount() { return 0; }
_remount_one demo 1
''')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('recovered', r.stdout)

    def test_health_timer_is_disabled_with_autostart(self):
        r = self.bash('''
_systemd_user_ready() { return 0; }
_systemd_mount_unit_name() { echo rah-mount@demo.service; }
systemctl() { echo "$*" >> "$RAH_CONFIG_DIR/calls"; }
_systemd_disable_mount_service demo
cat "$RAH_CONFIG_DIR/calls"
''')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('disable --now rah-health@demo.timer', r.stdout)
        self.assertIn('disable rah-mount@demo.service', r.stdout)


if __name__ == '__main__':
    unittest.main()
