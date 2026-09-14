# rah user guide

[← Overview](../README.md) · [简体中文](guide.zh-CN.md)

Configuration, command routing, and recovery for an agent host connected to remote projects.

## Command reference

| Command | Purpose |
| :--- | :--- |
| `rah setup [target] [local-path]` | Guided setup for dependencies, SSH, hooks, and the first mount. |
| `rah mount [options] user@host:/path [local-path]` | Mount another remote project. |
| `rah status [--all\|--current] [name\|path]` | Check filesystem, SSH, execution, and integration status. `rah list` is an alias. |
| `rah verify [name\|path]` | Run a fuller check of the project, path mapping, and hooks. |
| `rah remount [--force] [name\|path ...]` | Recover selected mounts, or all mounts when no target is given. |
| `rah unmount <name\|path>` | Disconnect a mount while retaining its configuration. |
| `rah remove [--keep-local] [name\|path]` | Remove a mount's configuration; normally also remove its empty local directory. |
| `rah autostart on\|off\|status` | Manage recovery after boot or login. |
| `rah local [--cwd DIR] -- <command> [args...]` | Execute one command on the agent host. |
| `rah run --cwd <local-mount-path> -- <command...>` | Execute on the remote associated with the specified mount. |
| `rah init <claude\|codex> [--remove]` | Install or remove the routing hook and skill. |
| `rah local-allow list\|add\|remove <absolute-path>` | Manage local executable exceptions. |
| `rah hook-log on\|off\|status\|clear` | Manage logging of routing decisions. |
| `rah doctor` | Check local dependencies and managed mounts. |
| `rah version` | Print the version of the installed executable. |
| `rah self-update` | Update a downloaded installation. |
| `rah uninstall [--purge]` | Remove rah integration and the binary; optionally remove configuration. |

`rah hook` is the integration entry point used by the agents. It is not a command you normally need to invoke yourself.

## Installation and updates

Install rah on the machine running the agent. Local dependencies are:

- **Linux:** Bash, OpenSSH client, SSHFS, `jq`, `base64`, GNU `timeout`, util-linux tools, and FUSE utilities.
- **macOS:** Bash, OpenSSH client, SSHFS through macFUSE, `jq`, `base64`, and Perl. `timeout` or `gtimeout` is used when available.
- **Downloading updates:** `curl`.
- **Running the test suite:** Python 3, in addition to the relevant local tools.

The remote needs SSH with an SFTP subsystem, Bash, and `base64`. Confirm non-interactive access with `ssh -o BatchMode=yes <host> true`.

### Install from a checkout

```bash
git clone https://github.com/Hiaa1/rah.git
cd rah
bash install.sh
rah setup
```

You can inspect the installer before running it, or check out a chosen revision first. On macOS, setup can guide dependency installation through Homebrew, MacPorts, or the macFUSE/SSHFS installers. macFUSE may require approval in System Settings.

### Update a downloaded installation

```bash
rah self-update
rah version
```

The current updater downloads the script from `main`; it does not automatically install background updates or publish desktop notifications. `RAH_RAW_URL` can select a different source. Updating the executable alone does not apply every service or hook change.

### Update a Git checkout

When the installed executable points into a Git checkout, `rah self-update` refuses to overwrite tracked source. Review your working tree and update it through Git. A clean checkout following its upstream can use:

```bash
git status
git pull --ff-only
```

If you installed a separate copy using `install.sh`, reinstall that copy after updating the checkout. A symlink into the checkout uses the changed source directly.

### Apply integration and service changes

Refresh the integration for each agent you use:

```bash
rah init codex
# or: rah init claude
```

If autostart was enabled, regenerate its service configuration:

```bash
rah autostart on
rah autostart status
```

On Linux, existing SSHFS processes retain their old connection options until restarted. When you are ready for a brief filesystem reconnection, apply those options with `rah remount --force`. Reopen affected files if your editor retains stale handles.

## Remote environments

Use an explicit local path when multiple hosts have projects with the same basename:

```bash
rah setup gpu:~/project ~/mnt_rah/gpu-project
rah setup lab:~/project ~/mnt_rah/lab-project
```

Name a mount, choose a port, and activate a remote environment:

```bash
rah mount --name gpu-project --port 2222 \
  --prelude 'source .venv/bin/activate' \
  you@host:~/project ~/mnt_rah/gpu-project
```

`--prelude` runs in the remote project directory before each command. Keep it lightweight: status probes also check the configured execution environment. Commands use the remote shell environment; they do not inherit the agent host's virtual environment.

Use identical paths on both hosts only when your workflow requires them:

```bash
rah mount --same-path you@host:/home/you/project
```

Normally, rah maps the local mount prefix to the remote project path. It also translates matching local mount paths in routed command text. `rah verify` checks this mapping.

## SSH and private networks

Define stable aliases in `~/.ssh/config` on the agent host:

```sshconfig
Host gpu
    HostName gpu.example.com
    User you
    Port 2222
    IdentityFile ~/.ssh/id_ed25519
```

Then use `rah setup gpu:~/project`. Both file access and command routing inherit the alias's connection settings, including `ProxyJump` and `ProxyCommand`. If a machine changes address, update the alias after verifying its identity.

A host behind NAT needs a reachable SSH route. A private network such as Tailscale can supply that route; use its hostname in the SSH alias. Alternatively, create a reverse tunnel **on the remote host** to a reachable relay:

```bash
autossh -M 0 -N -R 2222:localhost:22 you@relay.example.com
```

On the agent host, reach the relay's forwarded loopback port through a jump connection:

```sshconfig
Host gpu-via-relay
    HostName 127.0.0.1
    Port 2222
    User you
    ProxyJump you@relay.example.com
```

Confirm `ssh gpu-via-relay true` works before using `rah setup gpu-via-relay:~/project`. rah inherits the route; it does not establish the private network or maintain the reverse tunnel itself.

## Local execution and other mounts

Suppose B and C are mounted on agent host A at `/mnt/b` and `/mnt/c`. While the agent works in `/mnt/b`, ordinary routed commands execute on B. A `/mnt/c` path in a command argument does not change its execution host.

```bash
# Execute on A, reading A's local file
rah local -- cat /home/you/notes.txt

# Execute on A, reading C through its SSHFS mount
rah local -- cat /mnt/c/file.txt

# Compare the two mounted files on A
rah local -- diff /mnt/b/config.yaml /mnt/c/config.yaml

# Execute on C, connecting directly from A
rah run --cwd /mnt/c -- cat file.txt
```

The hook leaves commands beginning with `rah` on A. B does not need SSH access to C. Put `rah local` at the start of the agent's tool command.

`rah local` preserves arguments, standard streams, and exit status. Its working directory stays local; relative paths inside `/mnt/b` still access B's mounted files. Use `--cwd` or absolute paths to select another directory. For a pipeline or redirection, pass the whole script to a local shell:

```bash
rah local --cwd /home/you -- bash -c 'cat notes.txt | head -n 20'
```

### Persistent executable exceptions

For a tool that should always run on the agent host, add its absolute executable path:

```bash
rah local-allow add /home/you/bin/local-helper.sh
rah local-allow list
rah local-allow remove /home/you/bin/local-helper.sh
```

The global file is `~/.config/rah/local-allow`, with one absolute path per line. A command must start with an entry and match a word boundary. `echo /home/you/bin/local-helper.sh` still routes remotely. Relative paths, bare command names, and patterns are rejected. Missing or malformed entries do not broaden local execution.

## Recovery and troubleshooting

`rah remount` skips healthy mounts. `--force` rebuilds them. The agent hook also schedules throttled background recovery without waiting for filesystem probes in the calling process.

### Linux services

`rah autostart on` installs a `rah-mount@.service` instance and a `rah-health@.timer` instance for each configured mount:

- SSHFS stays in the foreground so systemd owns its lifecycle.
- File and command traffic use separate SSH transports.
- Health checks perform a fresh filename lookup without writing a probe file.
- Each lookup has a 3-second timeout and a 1-second kill grace period.
- A failed check restarts that mount's service. The next check is scheduled 15 seconds after the previous one finishes.
- Service retries have a 30-second restart delay. Startup and shutdown also have deadlines.
- Both normal stop and failed-start cleanup detach leftover mounts; the service manager terminates the associated processes.

`rah unmount <name>` stops its service. The health timer and hook do not restart that explicitly stopped service. `rah remount <name>` starts it again; enabled services also return when the user manager starts at login or boot. `rah autostart off` disables autostart without itself unmounting your projects.

```bash
rah autostart status
systemctl --user list-timers 'rah-health@*'
journalctl --user -u 'rah-mount@*' -u 'rah-health@*'
```

For recovery before the first login after a reboot, systemd user lingering must be enabled; `rah autostart on` reports the relevant command when needed. Services also need usable SSH credentials outside the interactive login session.

### macOS persistence

A LaunchAgent periodically runs `rah remount --best-effort`. Its default interval is 300 seconds; set `RAH_AUTOSTART_INTERVAL` when installing the agent to change it. SSHFS retains its own `reconnect` option on manual/macOS mounts.

### Read the status correctly

`rah status` checks up to eight mounts per batch. Filesystem checks, SSH checks, and the system service summary run concurrently. Each SSH connection has a 3-second total deadline plus a 1-second kill grace period. Status does not create or repair SSH masters.

| Result | Meaning / next step |
| :--- | :--- |
| `mounted` | The mount exists and its filesystem probe responded. |
| `DEAD` | The filesystem probe failed or did not respond. Run `rah remount <name>`. |
| `not mounted` | There is no mount at the configured path. |
| SSH `TIMEOUT` | The probe exceeded its budget; this is not proof the host is permanently offline. |
| Exec `not checked` | SSH was unavailable, so execution was not tested again. |
| SSH reachable, exec failed | Check the remote path and `--prelude`; use `rah verify <name>`. |

For a slow connection or full path-and-hook diagnostics, use `rah verify <name>`. More than eight unresponsive mounts require multiple bounded batches; the 3-second SSH deadline is per probe, not a deadline for the entire command.

### VS Code or file tools stop responding

Keep the editor server, shell startup, rah executable, and rah configuration on local disk. Mount the project directory, rather than putting the host's control tools inside a remote filesystem.

Run `rah remount <name>` from a local terminal. After recovery, reopen affected files or reload the VS Code window. Merely detaching a FUSE mount does not release I/O already blocked in a failed SSHFS process; the process must also terminate. The [SSHFS documentation](https://github.com/libfuse/sshfs/blob/master/sshfs.rst) explains this behavior and the risk to interrupted writes.

### Commands appear to execute on the wrong host

```bash
rah hook-log on
rah hook-log clear
# Reproduce one agent command, then inspect:
cat ~/.config/rah/hook.jsonl
rah hook-log off
```

Hook logs can contain command text. Remove sensitive arguments before sharing them. Check the selected working directory, refresh the relevant integration with `rah init`, and restart the agent.

## Execution and trust

rah routes commands based on the working directory of an agent tool call. The installed hook uses `permissionDecision: "allow"` so the supported integrations apply the command rewrite. Within a managed mount, this approves and routes the command after checking the directory boundary. Outside managed mounts, commands pass through; explicit local execution and executable exceptions are handled separately.

Install the integration only on an agent host you trust. Instructions in a remote repository can affect what the agent executes there. Keep SSH access scoped to the intended hosts and accounts, and review the installed hooks.

The project configuration lives in `~/.config/rah/*.env` by default. `RAH_CONFIG_DIR` overrides that location. Configurations record the host, remote path, mountpoint, control socket, optional port, and prelude. Agent integration files live under `~/.claude` and `~/.codex`.

## Maintaining the documentation

`RAH_VERSION` in [`rah`](../rah) is the version source. The README badges use a [Shields dynamic regex badge](https://shields.io/badges/dynamic-regex-badge) to read that field from the published `main` branch. Do not copy the number into README prose or a static version badge.

The badge requests a 300-second cache lifetime; Shields and GitHub may cache it longer. Unpublished local changes are not visible to the badge. Use `rah version` for the installed version.

Keep [the English overview](../README.md) and [the Chinese overview](../README.zh-CN.md) aligned when user-visible behavior changes, and update the matching guide sections. Document implemented behavior; proposed update notifications or automatic upgrades should not be presented as available features.
