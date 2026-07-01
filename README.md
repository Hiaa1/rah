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

Do you need to develop your code on stupid cluster sever? Do you want to share your coding plan with others? Do you want to develop on different servers but don't want to configure coding agent for every server and have risk of leaking your account?                 **THIS** is what you want - **Rah**!

Rah lets Claude Code / Codex develop as if it were on a remote machine, while the agent account
stays logged in on one machine you choose.

**Invisible to the agent.** Claude Code / Codex sees a local folder and a normal shell: `cat`,
`pytest`, `python train.py`, and `nvidia-smi` work as usual. Rah handles the file mount and command
routing at the tool layer, so files come from the remote and commands execute there without prompt
overhead or relying on the model to remember SSH.

## Usage Scenarios

### 1. Personal Computer To Remote Workstation

For users who want to use a personal Mac/Ubuntu machine while doing the real work on a remote
workstation, server, or lab machine.

- **Machine A**: your local Mac/Ubuntu/WSL2/Linux gateway. It runs Claude Code / Codex and installs
  `rah`.
- **Machine B**: the remote development host. It stores the code, datasets, model weights, and GPU
  environment, and only needs SSH enabled.
- On machine A, use `rah` to mount machine B's project, for example under `~/mnt_rah/<project>`.
- On machine A, enter that mounted directory and start Claude Code / Codex. The agent reads and
  writes B's files, and commands execute on B.

### 2. Shared Agent Host For Multiple Users

For teams or labs that want to keep Claude Code / Codex sessions centralized on one trusted host.

- **A1, A2, A3...**: each person's own computer. It only needs SSH access to the shared agent host.
- **Machine B**: the shared agent host. It installs Claude Code / Codex and `rah`, and acts as the
  common development entry point.
- **C1, C2, C3...**: each person's own code host, workstation, or server, storing their project,
  data, and environment.
- Each user SSHes from their own computer to B, then uses `rah` to mount their Cj project into a
  personal working directory on B.
- Each user starts Claude Code / Codex from their own directory on B. Files come from their own Cj,
  and commands execute on their own Cj.

## Supported Now / TODO

- [x] **Recommended mode: shared Linux agent host.** Install Claude Code / Codex and `rah` on one
  Linux machine B. Other computers A1/A2/A3... SSH into B; B mounts each user's remote workspace Cj
  into a personal working directory. Cj can be Linux/macOS, or Windows/WSL2 if it provides
  SSH/SFTP plus a Unix-like shell environment.
- [x] **Personal mode: Linux/macOS agent host + remote Linux dev box.** Install Claude Code / Codex
  and `rah` on your own Linux or macOS work machine, mount the remote Linux workstation/GPU server,
  then start the agent from the mounted directory.
- [x] **macOS as the agent host.** Rah can run on macOS through macFUSE + SSHFS; the installer
  points to Homebrew, MacPorts, or manual install paths.
- [x] **Remote behind NAT / no public IP.** Reach a remote that cannot accept inbound SSH by
  giving it reachability one layer below rah (Tailscale or a reverse SSH tunnel) and using an
  `~/.ssh/config` alias as the rah target. See [Remote Behind NAT](#remote-behind-nat-no-public-ip).
- [ ] **Native Windows as the agent host.** Not supported yet; Windows users should prefer WSL2 or
  SSH into a Linux agent host.
- [ ] **Native Windows as the remote host.** Only experimental when SSH/SFTP and a Unix-like
  shell/base64 environment are available; a normal Windows shell is not a stable target today.

Use Rah if you want to:

- avoid spreading Claude Code / Codex sessions across multiple computers, networks, or VPN exits
- control a remote workstation, server, or lab machine from your local agent
- avoid copying datasets or using git as a development sync mechanism

Rah does two things:

- Mounts the remote project as a local folder, for example `~/mnt_rah/<project>`, so you can edit
  remote code like local files.
- Automatically sends the agent's shell commands to the remote machine, so tests, training jobs,
  GPU calls, and dataset access run where the project really lives.

The routing is handled by hooks, not by prompt reminders, so the agent does not need to know it is
doing remote development. **Zero remote install:** install `rah` only on the agent machine; the
remote only needs SSH and basic shell tools.

## Machine Roles

- **agent host**: the machine that runs Claude Code / Codex and `rah`.
- **remote host**: the machine that stores the project, data, environment, and GPU, and actually
  runs commands.

**Install Rah on the agent host, not on the remote host.**

The supported agent host target today is a Unix-like environment with sshfs/FUSE, `ssh`, and
standard shell tools: Ubuntu, Debian, WSL2, and macOS. Native Windows as the agent host is outside
the current scope; Windows users should prefer WSL2.

The remote host does not need `rah`. It only needs SSH access and a project directory. A Linux
server/workstation, or an SSH-enabled macOS machine, can be a remote target.

## Trusted agent gateway

If you pay for a Claude Code or Codex plan and want to use it from multiple computers, frequently
logging the same account in from different devices, networks, or VPN exits can increase account
risk, including security review or lockout. Rah's recommended pattern is to keep the agent account
on one trusted agent host. Other computers reach that host through your own remote-access channel,
and Rah controls the real remote host from there. The account session stays in one place, while
project files and command execution still happen on the right remote machine.

<p align="center">
  <img src="assets/rah-seamless-dev.png" alt="Rah makes local coding agents work normally while hooks route commands to a remote host" width="900">
</p>

## Install And Use

### Check Your Environment

- Install `rah` on the machine that runs Claude Code / Codex. Ubuntu, Debian, WSL2, macOS, or a
  Linux gateway are the recommended environments today.
- The remote machine only needs SSH enabled and a project directory. It does not need `rah`.
- If your remote SSH uses a non-default port, pass `--port` during setup.

### Pick One Install Option

Choose one of the two options below. You do not need to run both.

**Option 1: one-line terminal install (recommended)**

```bash
curl -fsSL https://raw.githubusercontent.com/Hiaa1/rah/main/install.sh | bash
```

Check that it works:

```bash
rah version
```

If your shell cannot find `rah`, reopen the terminal or add `~/.local/bin` to `PATH`.

On macOS, if SSHFS is missing, the installer points you to the right path for your machine:
Homebrew, MacPorts, or manual macFUSE + SSHFS installers. macFUSE may require approval in System
Settings before the first mount works. To force a path, set `RAH_MACOS_SSHFS_INSTALLER=brew`,
`macports`, or `manual`.

If macFUSE shows a **System Extension Blocked** prompt on the first mount, choose **Open System
Settings**, allow the macFUSE system extension in Privacy & Security, then try the mount again:

<p align="center">
  <img src="assets/mac-deploy-fuse.png" alt="macOS macFUSE System Extension Blocked permission prompt" width="620">
</p>

**Option 2: ask Claude Code / Codex to install it**

In an agent session, say:

> **"Install Rah from github.com/Hiaa1/rah and set it up for `you@host:~/project`."**

The agent can download rah and prepare the commands. If it needs `sudo`, an SSH password,
`ssh-copy-id`, or macFUSE/SSHFS install steps, run the command it prints in a real terminal once.

### Connect Your First Remote Project

Run this in a real terminal:

```bash
rah setup
```

It asks for:

- SSH target, for example `you@devbox.example.com`
- SSH port, or press Enter for the default
- Remote project directory, for example `~/project`
- Local mount directory, or press Enter for the default `~/mnt_rah/<project>`

If you already know the values, you can do it in one line:

```bash
rah setup you@host:~/project
rah setup --port 2222 you@devbox.example.com:~/project
rah setup you@host:~/project ~/projects/project
```

> `rah setup` may install local dependencies (`apt`, Homebrew, MacPorts, or manual macFUSE/SSHFS
> steps), authorize your SSH key, or create a local directory. Those steps can ask for a password,
> so run setup in a real terminal, not inside an agent shell without a TTY.

### Start Developing

After setup, enter the local mount:

```bash
cd ~/mnt_rah/project
rah verify
```

When verification passes, start Claude Code / Codex from this directory. Use the agent normally:

- the agent sees a local folder
- files actually come from the remote project
- shell commands actually execute on the remote

Restart the agent once after the first hook install. After that, new projects only need another
`rah setup` or `rah mount`; the agent does not need to be configured again. To remove everything,
run `rah uninstall`.

## Remote Behind NAT (No Public IP)

Rah needs an SSH destination it can reach: exec runs `ssh <host>`, files come over
`sshfs <host>:<path>`. If the remote sits behind NAT/CGNAT with no public IP, it cannot
accept inbound SSH and both planes fail. NAT traversal is solved one layer **below** rah:
give the remote a reachable address, expose it as an `~/.ssh/config` alias, then point
`rah setup` at that alias. Rah needs no special flags — `ssh` and `sshfs` inherit the
alias's `HostName`, `Port`, `ProxyJump`, and `ProxyCommand`.

### Option 1 — Tailscale (recommended)

Works even when both ends are behind NAT (hole-punching with a DERP relay fallback); no
public IP or VPS required.

1. Install Tailscale on both machines and bring them onto the same tailnet:
   ```bash
   tailscale up        # run on the remote and on the agent machine
   tailscale status    # find the remote's MagicDNS name, e.g. gpu-home.tailXXXX.ts.net
   ```
2. Add an alias to `~/.ssh/config` on the agent machine:
   ```
   Host gpu-home
       HostName gpu-home.tailXXXX.ts.net
       User you
   ```
3. Use the alias as the rah target:
   ```bash
   rah setup gpu-home:/home/you/project
   ```

### Option 2 — Reverse SSH tunnel (self-hosted)

Use this if you prefer not to depend on a third-party overlay and have a public relay
(a cheap VPS, or any always-on machine with a public IP).

1. On the remote, keep a reverse tunnel up to the relay (supervise it with `autossh`, a
   systemd unit, or `tmux`):
   ```bash
   autossh -M 0 -N -R 2222:localhost:22 you@relay.example.com
   ```
2. On the agent machine, reach the remote through the relay-forwarded port:
   ```
   Host gpu-home
       HostName localhost
       Port 2222
       ProxyJump you@relay.example.com
       User you
   ```
3. Use the alias as the rah target:
   ```bash
   rah setup gpu-home:/home/you/project
   ```

Port and proxy settings live in `~/.ssh/config`; rah only uses the alias, and both the
command-execution and the sshfs mount inherit it. If `rah setup`/`rah mount` reports an
SSH preflight failure, rah prints these same options as a hint.

## Commands

| Command | Purpose |
|---|---|
| `rah setup [--port PORT] [user@host:/path] [local-path] [-y]` | guided onboarding: deps, ssh key, agent hooks, mount |
| `rah mount [--name N] [--port PORT] [--prelude CMD] user@host:/path [local-path]` | mount a remote code tree locally; defaults to `~/mnt_rah/<project>` |
| `rah mount --same-path user@host:/abs/path` | opt into identical local/remote path mode |
| `rah remount [--force] [name\|path]` | recover dead/stale/unmounted mounts; all if no target; healthy mounts are skipped unless forced |
| `rah unmount <name\|path>` | unmount + drop the ssh master, keep config |
| `rah remove [--keep-local] [name\|path]` | unmount, remove rah config, rmdir empty mountpoint; current mount if omitted |
| `rah autostart on\|off\|status` | restore managed mounts after reboot/login with a user-level service |
| `rah init <claude\|codex> [--remove]` | install/remove the hook + skill for an agent |
| `rah status [--all\|--current] [name\|path]` / `rah list` | global mount / ssh / exec / autostart / agent-hook health |
| `rah verify [name\|path]` | end-to-end mount/ssh/hook check |
| `rah doctor` | check dependencies, PATH, mount health |
| `rah self-update` | update to the latest version |
| `rah uninstall [--purge]` | remove hooks, skill, and the `rah` binary |
| `rah run --cwd <dir> -- <cmd>` | run a command on the remote (used by the hook) |
| `rah hook-log on\|off\|status\|clear` | enable/inspect hook diagnostics |

## Mount management

Use `rah status` or `rah list` to see every managed mount from `~/.config/rah`, including its
name, remote path, local path, mount health, ssh reachability, and exec-plane health. Use
`rah status --current` when you only want the mount that contains the current directory.

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
- `rah autostart on` installs a per-user boot/login job to run safe `rah remount` retries
  automatically after reboot. Linux uses `systemd --user`; macOS uses a LaunchAgent.
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

- **Supported agent host:** Linux or macOS with sshfs/FUSE support; primary targets are Ubuntu,
  Debian, WSL2, and macOS. Native Windows is not supported.
- **Linux local packages:** `bash`, `ssh`, `sshfs` (+ `fuse`/`fuse3`), `jq`, `coreutils`
  (`base64`, `timeout`), `util-linux` (`mountpoint`); `curl` for install/self-update.
- **macOS local packages:** `bash`, `ssh`, `sshfs` through macFUSE, `jq`, `base64`, and `perl`;
  `curl` for install/self-update. For SSHFS/macFUSE, use Homebrew
  (`brew install --cask sshfs-mac`), MacPorts (`sudo port install sshfs`), or the official
  macFUSE + SSHFS installer packages. `rah` can find SSHFS in the usual Homebrew/MacPorts
  locations even if it is not on PATH. Run `rah doctor` to check.
- **SSH:** passwordless key-based ssh to the remote — `ssh <host> true` must succeed without a
  prompt. `rah setup` preflights this and can authorize your key with `ssh-copy-id` or an
  ssh-based fallback.
- **Remote:** a standard OpenSSH server, POSIX shell, and `base64`. A Linux server/workstation or an
  SSH-enabled macOS machine can be a remote target.

## Security

`rah` reroutes the agent's command execution to a remote host over ssh. Claude and Codex currently
require `permissionDecision: "allow"` for `updatedInput.command` rewrites to take effect, so
`rah init claude` and `rah init codex` install allow-mode hooks. Commands inside a rah-managed mount
are approved by the hook after cwd gating; outside a managed mount they pass through unchanged
(Claude receives `defer`, while Codex receives an empty hook response). Use `rah hook-log` when you
need to inspect routing decisions.

## License

[MIT](LICENSE)
