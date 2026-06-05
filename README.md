# Remote as Host (rah)

Make your local machine act as a remote dev box for coding agents (Claude Code, Codex).
The agent runs locally; your real project — code, heavy datasets, GPU — stays on a remote.
`rah` gives the agent two enforced planes:

- **Files** are edited through a **same-path sshfs mount** of the remote code tree, so the
  agent's native read/edit/grep tools just work. Datasets are *not* mounted (they stay
  remote), so a stray search can't drag gigabytes over the network.
- **Execution** is transparently routed to the remote over ssh by a `PreToolUse` **hook**
  that rewrites the agent's shell commands — deterministically, with no instructions to the
  model. The agent behaves as if it were on the remote machine.

Routing is an *invariant enforced by a hook*, not a request in a prompt — the model cannot
forget to run on the remote. **Zero remote footprint:** only your machine installs `rah`; the
remote needs nothing but a stock `sshd`, `bash`, and `base64`.

## Install

```bash
# one line (re-run to upgrade)
curl -fsSL https://raw.githubusercontent.com/Hiaa1/rah/main/install.sh | bash
```

Prefer to read before you run? Clone and install the single file:

```bash
git clone https://github.com/Hiaa1/rah && cd rah && ./install.sh
```

`rah` is a single self-contained Bash script — auditable in one file, and `scp`-able to any host.

### Or just ask your agent

In any Claude Code / Codex session, one sentence is enough — no pre-install needed:

> **"Install rah from github.com/Hiaa1/rah and set it up for `you@host:/abs/path`."**

The agent follows this README: it checks passwordless ssh (and walks you through `ssh-copy-id` if
it's missing — you enter the remote password that one time), installs rah, and runs `rah setup`.
You're asked only for the remote, that one ssh authorization, and a single restart the first time.

## Quickstart

One command checks dependencies, wires your installed agents, and mounts:

```bash
rah setup you@host:/abs/path/to/project
```

Then launch your agent from inside the mountpoint. Its file tools hit the mount; its commands
run on the remote. The hook is installed once (restart the agent that first time); after that,
mounting a new project activates routing immediately — no restart. To remove everything: `rah uninstall`.

Prefer the explicit steps? `rah doctor` → `rah init claude` (or `codex`) → `rah mount user@host:/abs/path`.

## Commands

| Command | Purpose |
|---|---|
| `rah setup [user@host:/abs/path] [--prelude CMD]` | one-command guided onboarding (doctor + init + mount) |
| `rah mount [--name N] [--prelude CMD] user@host:/abs/path` | mount a remote code tree at the identical path |
| `rah remount [name]` | recover a dead/stale mount (all if no name) |
| `rah unmount <name>` | unmount + drop the ssh master |
| `rah init <claude\|codex> [--remove]` | install/remove the hook + skill for an agent |
| `rah status` | mount / ssh-master health |
| `rah doctor` | check dependencies, PATH, mount health |
| `rah self-update` | update to the latest version |
| `rah uninstall [--purge]` | remove hooks, skill, and the `rah` binary |
| `rah run --cwd <dir> -- <cmd>` | run a command on the remote (used by the hook) |

## How it works

```
agent file tools ──► same-path sshfs mount ──► remote code tree
agent commands ──► PreToolUse hook ──► rah run ──► ssh(ControlMaster) ──► remote: cd + prelude + cmd
```

The hook self-gates by working directory: outside a rah-managed mount it passes commands
through unchanged, so it is safe even if other projects share the same agent. Commands are
carried to the remote base64-encoded (no quoting/injection issues), and the remote exit code is
propagated so the agent's run/verify loop works normally. Standalone `cd` stays local so the
shell's working directory is preserved across commands.

## Recovery

A network drop, remote reboot, or laptop sleep can leave the sshfs mount **dead** — file tools
then report `Transport endpoint is not connected` or hang. Because exec and files are separate
channels, **command execution keeps working** while the mount is down. To recover the file plane:

- `rah remount` re-establishes ssh + sshfs (idempotent; runs locally even mid-session).
- The hook also **self-heals**: while you're working it probes the mount (throttled, non-blocking)
  and fires a background `rah remount` if it finds it dead — so it usually recovers on its own.
- `rah status` reports `mounted` / `DEAD` / `not mounted` (a real liveness probe, not a stale flag).

## Requirements

- **Local:** `bash`, `ssh`, `sshfs` (+ `fuse`/`fuse3`), `jq`, `coreutils` (`base64`),
  `util-linux` (`mountpoint`); `curl` for install/self-update. Run `rah doctor` to check.
- **SSH:** passwordless key-based ssh to the remote — `ssh <host> true` must succeed without a
  prompt. `rah setup` preflights this and points you to `ssh-copy-id` if it's missing.
- **Remote:** nothing beyond a standard OpenSSH server and a POSIX shell.

## Security

`rah` reroutes the agent's command execution to a remote host over ssh. By default the hook
returns `permissionDecision: "defer"`, so it **respects your agent's normal approval flow**
rather than auto-approving commands. Run fully autonomously only if you opt in
(`rah hook --decision allow`). The whole tool is one readable Bash file; review it before install.

## License

[MIT](LICENSE)
