# Remote as Host (rah)

<p align="center">
  <img src="assets/rah-logo.svg" alt="Rah logo - local agent with files mounted from a remote host and commands routed to it" width="720">
</p>

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.2.0-blue)](rah)
[![Views](https://hits.sh/github.com/Hiaa1/rah.svg?label=views&color=0e75b6)](https://hits.sh/github.com/Hiaa1/rah/)
[![Claude Code](https://img.shields.io/badge/Claude_Code-compatible-7C3AED)](README.md#agent-support)
[![Codex CLI](https://img.shields.io/badge/Codex_CLI-compatible-111827)](README.md#agent-support)

[简体中文](README.zh-CN.md)

Make your local machine act as a remote dev box for coding agents (Claude Code, Codex).
The agent runs locally; your real project — code, heavy datasets, GPU — stays on a remote.
`rah` gives the agent two enforced planes:

- **Files** are edited through an **sshfs mount** of the remote code tree. By default, rah
  mounts projects under `~/mnt_rah/<project>`; you can also choose any empty local directory.
  Datasets are *not* mounted (they stay remote), so a stray search can't drag gigabytes over
  the network.
- **Execution** is transparently routed to the remote over ssh by a `PreToolUse` **hook**
  that rewrites the agent's shell commands — deterministically, with no instructions to the
  model. The agent behaves as if it were on the remote machine.

Routing is an *invariant enforced by a hook*, not a request in a prompt — the model cannot
forget to run on the remote. **Zero remote footprint:** only your machine installs `rah`; the
remote needs nothing but a stock `sshd`, `bash`, and `base64`.

## Project scope

`rah` is intentionally scoped to a Linux-based agent gateway model:

- The **agent host** is a Linux environment that can run Claude Code / Codex, `sshfs`/FUSE,
  `ssh`, and standard shell tools. Ubuntu, Debian, and WSL2 are the primary targets.
- The **remote host** only needs OpenSSH server plus a POSIX shell; no `rah` install is required
  there.
- Installation differs by Linux distribution: Ubuntu/Debian/WSL2 can use the guided `apt-get`
  path, while other Linux distributions need equivalent packages from their own package manager.

Native macOS and native Windows are outside the current scope. Use a Linux gateway machine or WSL2
when your personal device is macOS or Windows.

## Trusted agent gateway

`rah` also supports a safer account model for coding agents: keep Claude Code / Codex logged in on
one trusted machine, then reach that machine from your laptop or desktop over your own remote-access
channel. From there, `rah` controls any server or workstation over ssh.

This avoids spreading agent logins, browser sessions, API tokens, and account risk across multiple
personal devices with different VPN exits or network locations. The agent account lives in one
place; remote project execution still happens on the right server.

If you pay for a Claude Code or Codex plan and want to use it from multiple computers, frequently
logging the same account in from different devices, networks, or VPN exits can increase account
risk, including security review or lockout. A steadier pattern is to choose one trusted computer as
the **agent host**: only that A machine stays logged in to Claude Code / Codex. A separate B
machine or server holds the real project, large datasets, model weights, and outputs. With `rah`,
the agent on A edits B's project as if it were local, while commands really execute on B, where the
GPU, datasets, and tuned environment already live.

<p align="center">
  <img src="assets/rah-seamless-dev.png" alt="Rah makes local coding agents work normally while hooks route commands to a remote host" width="900">
</p>

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

### Platform notes

The supported runtime is Linux with sshfs/FUSE and the required command-line tools. On Ubuntu,
Debian, and WSL2, `rah setup` can offer to install missing local packages with `sudo apt-get`.
On other Linux distributions, install the equivalent packages yourself before running setup.

### Or just ask your agent

In any Claude Code / Codex session, one sentence is enough — no pre-install needed:

> **"Install rah from github.com/Hiaa1/rah and set it up for `you@host:~/project`."**

The agent follows this README: it checks passwordless ssh (and walks you through `ssh-copy-id` if
it's missing — you enter the remote password that one time), installs rah, and runs `rah setup`.
You're asked only for the remote, that one ssh authorization, and a single restart the first time.

## Quickstart

One command starts the guided setup. It asks for your ssh target, optional port, remote project
path, and local mount directory, then checks dependencies, wires your installed agents, mounts,
and prints the exact command it is executing:

```bash
rah setup
```

For scripts or repeatable setup, pass everything explicitly:

```bash
rah setup you@host:~/project
rah setup --port 2222 you@devbox.example.com:~/project
```

> **Run `rah setup` in a real terminal — not inside the coding agent.** It walks you through any
> missing prerequisite behind a `[Y/n]` prompt: installing dependencies (`sudo apt`), generating
> and authorizing your ssh key (`ssh-copy-id`), or creating a custom local mount directory if it
> needs `sudo`. Those steps need a TTY to read a password, and a coding agent's shell — including
> Claude Code's `!` — has **no TTY**, so they fail there. Add `-y` to assume yes. (Run headless,
> `rah setup` detects the missing terminal and prints the one human step instead of hanging.)

By default, the local mount lands at `~/mnt_rah/<project>`. To choose your own local directory,
pass it explicitly:

```bash
rah setup you@host:~/project ~/projects/project
```

For strict identical local/remote paths, opt in with `--same-path`.

Deploy once in a terminal; after that, day-to-day use is all through the agent (it never needs a
TTY or `sudo`).

Then launch your agent from inside the mountpoint. Its file tools hit the mount; its commands
run on the remote. The hook is installed once (restart the agent that first time); after that,
mounting a new project activates routing immediately — no restart. To remove everything: `rah uninstall`.

Check the setup before handing it to an agent:

```bash
cd ~/mnt_rah/project
rah verify
```

Prefer the explicit steps? `rah doctor` -> `rah init claude` (or `codex`) ->
`rah mount user@host:~/project ~/projects/project`.

## Commands

| Command | Purpose |
|---|---|
| `rah setup [--port PORT] [user@host:/path] [local-path] [-y]` | guided onboarding: deps, ssh key, agent hooks, mount |
| `rah mount [--name N] [--port PORT] [--prelude CMD] user@host:/path [local-path]` | mount a remote code tree locally; defaults to `~/mnt_rah/<project>` |
| `rah mount --same-path user@host:/abs/path` | opt into identical local/remote path mode |
| `rah remount [name\|path]` | recover a dead/stale mount (all if no target) |
| `rah unmount <name\|path>` | unmount + drop the ssh master, keep config |
| `rah remove [--keep-local] [name\|path]` | unmount, remove rah config, rmdir empty mountpoint; current mount if omitted |
| `rah init <claude\|codex> [--remove]` | install/remove the hook + skill for an agent |
| `rah status` / `rah list` | mount / ssh / exec / agent-hook health |
| `rah verify [name\|path]` | end-to-end mount/ssh/hook check |
| `rah doctor` | check dependencies, PATH, mount health |
| `rah self-update` | update to the latest version |
| `rah uninstall [--purge]` | remove hooks, skill, and the `rah` binary |
| `rah run --cwd <dir> -- <cmd>` | run a command on the remote (used by the hook) |
| `rah hook-log on\|off\|status\|clear` | enable/inspect hook diagnostics |

## Mount management

Use `rah status` or `rah list` to see every managed mount, including its name, remote path,
local path, mount health, ssh reachability, and exec-plane health.

- `rah unmount <name|path>` disconnects the mount but keeps the config, so `rah remount <name|path>` can recover it later.
- `rah remove [name|path]` disconnects it, removes the rah config, and removes the local mountpoint only if the directory is empty.
- `rah remove --keep-local [name|path]` removes rah's config while leaving the local directory in place.

## How it works

<p align="center">
  <img src="assets/rah-workflow.png" alt="Rah workflow showing remote files mounted locally and commands routed back to the remote host" width="900">
</p>

```
agent file tools ──► local sshfs mount ──► remote code tree
agent commands ──► PreToolUse hook ──► rah run ──► ssh(ControlMaster) ──► remote: cd + prelude + cmd
```

The hook self-gates by working directory: outside a rah-managed mount it passes commands
through unchanged, so it is safe even if other projects share the same agent. Commands are
carried to the remote base64-encoded (no quoting/injection issues), and the remote exit code is
propagated so the agent's run/verify loop works normally. In mapped mode, rah translates the
local cwd and local absolute path prefixes back to the remote project path before execution.
Standalone `cd` stays local so the shell's working directory is preserved across commands.

## Recovery

A network drop, remote reboot, or laptop sleep can leave the sshfs mount **dead** — file tools
then report `Transport endpoint is not connected` or hang. Because exec and files are separate
channels, **command execution keeps working** while the mount is down. To recover the file plane:

- `rah remount` re-establishes ssh + sshfs (idempotent; runs locally even mid-session).
- The hook also **self-heals**: while you're working it probes the mount (throttled, non-blocking)
  and fires a background `rah remount` if it finds it dead — so it usually recovers on its own.
- `rah status` reports `mounted` / `DEAD` / `not mounted` (a real liveness probe, not a stale flag).

## Hook diagnostics

If an agent appears to run locally from inside a managed mount, enable the hook log and retry one
command:

```bash
rah hook-log on
rah hook-log clear
```

Then run the suspect command in the agent and inspect `~/.config/rah/hook.jsonl`. Each JSONL entry
records whether the hook fired, the reported/effective cwd, mount match, route vs passthrough, and
the emitted decision. Disable it with `rah hook-log off`. For one-off debugging without changing the
flag file, launch the agent with `RAH_HOOK_LOG=1` or set it to a log path.

## Agent support

| Agent | Status | Hook installed by `rah init` |
|---|---|---|
| Claude Code v2.1.158+ | tested | `rah hook --decision allow` |
| Codex CLI v0.137.0+ interactive TUI | tested | `rah hook --decision allow --passthrough empty` |

Codex may ask you to review hooks after install or update. Choose **Trust all and continue** for the
rah hook, then commands launched from a managed mount route to the remote. `codex exec` is not the
target path for rah today; use the interactive CLI/TUI for transparent remote execution.

## Requirements

- **Supported local OS:** Linux with sshfs/FUSE support; primary target is Ubuntu, Debian, and WSL2.
  Native macOS and native Windows are not supported.
- **Local packages:** `bash`, `ssh`, `sshfs` (+ `fuse`/`fuse3`), `jq`, `coreutils` (`base64`),
  `util-linux` (`mountpoint`); `curl` for install/self-update. Run `rah doctor` to check.
- **SSH:** passwordless key-based ssh to the remote — `ssh <host> true` must succeed without a
  prompt. `rah setup` preflights this and points you to `ssh-copy-id` if it's missing.
- **Remote:** nothing beyond a standard OpenSSH server and a POSIX shell.

## Security

`rah` reroutes the agent's command execution to a remote host over ssh. Claude and Codex currently
require `permissionDecision: "allow"` for `updatedInput.command` rewrites to take effect, so
`rah init claude` and `rah init codex` install allow-mode hooks. Commands inside a rah-managed mount
are approved by the hook after cwd gating; outside a managed mount they pass through unchanged
(Claude receives `defer`, while Codex receives an empty hook response). The whole tool is one
readable Bash file; review it before install.

## License

[MIT](LICENSE)
