# Remote as Host (rah)

Make a host machine act as a remote dev box for coding agents (Claude Code, Codex).
The agents run on the host; the real project — code, heavy datasets, GPU — lives on a
remote. `rah` gives the agent two enforced planes:

- **Files** are edited through a **same-path sshfs mount** of the remote code tree, so the
  agent's native Read/Edit/Grep tools just work. Datasets are *not* mounted (they stay
  remote), so a stray search can't drag gigabytes over the network.
- **Execution** is transparently routed to the remote over ssh by a `PreToolUse` **hook**
  that rewrites every Bash command — deterministically, with no instructions to the model.
  The agent feels like it is on the remote machine.

The routing is an *invariant enforced by a hook*, not a request in a prompt: the model
cannot forget to run on the remote.

## Quickstart

```bash
./install.sh                                              # put `rah` on PATH

rah mount --prelude 'source .venv/bin/activate' \
    user@hia-host:/home/hia/proj/.../explore_scannet      # mount the code tree (same path)

rah init claude                                           # install hook + skill for Claude Code
rah init codex                                            # install hook + skill for Codex

rah status                                                # check mount + ssh health
```

Then launch your agent from inside the mountpoint. Its file tools hit the mount; its Bash
runs on the remote. Nothing else to configure.

## Commands

| Command | Purpose |
|---|---|
| `rah mount [--name N] [--prelude CMD] user@host:/abs/path` | mount remote code tree at the identical path |
| `rah unmount <name>` | unmount + drop the ssh master |
| `rah run --cwd <dir> -- <cmd>` | execute a command on the remote (used by the hook) |
| `rah hook` | PreToolUse rewrite, reads the event JSON on stdin |
| `rah init <claude\|codex>` | install the hook + skill for an agent |
| `rah status` | mount / ssh-master health |

## How it works

```
agent file tools ──► same-path sshfs mount ──► remote code tree
agent Bash ──► PreToolUse hook ──► rah run ──► ssh(ControlMaster) ──► remote: cd + prelude + cmd
```

The hook self-gates by working directory: outside a rah-managed mount it passes commands
through unchanged, so it is safe even if installed globally. Commands are carried to the
remote base64-encoded (no quoting/injection issues), and the remote exit code is propagated
so the agent's run/verify loop works normally.
