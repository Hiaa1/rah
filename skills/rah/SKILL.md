---
name: rah
description: Remote as Host — manage the sshfs mount and remote execution for this machine. Use when the user asks to mount/unmount a remote project, check mount or ssh health (rah status), or set up "remote as host" for a coding agent. Note that command execution in a rah-managed directory is ALREADY auto-routed to the remote by a hook — you do not need to add ssh yourself.
---

# rah — Remote as Host

`rah` lets this host act as a remote dev box: files are edited through a same-path
sshfs mount, while command execution is transparently routed to the remote over ssh
by a `PreToolUse` hook. **You do not need to prefix commands with `ssh` or do anything
special — when the working directory is a rah-managed mount, your normal Bash commands
already run on the remote (with its GPU, datasets, and environment).**

## When to use this skill

Only for **control-plane** actions. Execution routing is automatic; never wrap commands
in ssh manually.

## Commands

- `rah status` — list managed mounts; show whether each is mounted and its ssh master is alive.
- `rah mount [--name N] [--prelude 'CMD'] user@host:/abs/path` — mount a remote code tree at the
  identical absolute path. `--prelude` is a shell snippet run before each remote command
  (e.g. `source .venv/bin/activate`) to fix the remote environment.
- `rah unmount <name>` — unmount and drop the ssh master connection.
- `rah init <claude|codex>` — install the routing hook and this skill for an agent.

## Notes

- Only the **code tree** is mounted; datasets/outputs stay on the remote and are reached
  natively when commands execute there. Don't try to read large datasets through the mount.
- If a command must inspect remote outputs/logs, just run `cat`/`ls`/`tail` normally — it
  executes on the remote.
- `cd` within the mount works locally and is preserved across commands; everything else runs remote.
