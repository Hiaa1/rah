# Remote as Host (rah)

<p align="center">
  <img src="assets/rah-logo.svg" alt="Rah logo - a local coding agent connected to a remote host through file and command lanes" width="720">
</p>

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.4.1-blue.svg)](rah)
[![Claude Code](https://img.shields.io/badge/Claude_Code-compatible-7C3AED)](#agent-support--agent-支持)
[![Codex CLI](https://img.shields.io/badge/Codex_CLI-compatible-111827)](#agent-support--agent-支持)

> **Develop where the compute lives. Keep your agent where you trust it.**
>
> **让代码和算力留在远端，让 agent 留在你信任的机器上。**

**One agent host. Many shared compute hosts.** Configure Claude Code or Codex once on your own machine, then use Rah to reach any number of SSH-accessible GPU servers, CPU boxes, lab workstations, or data machines. The shared servers stay agent-free: no repeated agent setup, no account login on every machine, and no Rah installation on the remote side.

**一台 agent 主机，多台共享计算服务器。** 只在自己的电脑上配置一次 Claude Code 或 Codex，之后就可以通过 Rah 连接任意 SSH 服务器：GPU 服务器、CPU 机器、实验室工作站或数据主机。共享服务器无需安装 agent，不需要在每台机器上重复配置或登录账号，远端也不需要安装 Rah。

Rah lets Claude Code and Codex work on a remote project as if it were a local folder. Files are mounted through SSHFS; normal shell commands are routed through SSH. Your editor, agent, datasets, GPU environment, and long-running jobs can each stay where they belong.

Rah 让 Claude Code 和 Codex 像操作本地目录一样操作远端项目：文件通过 SSHFS 挂载，普通 shell 命令通过 SSH 转发。编辑器、agent、数据集、GPU 环境和长时间任务，都可以留在最合适的机器上。

<p align="center">
  <img src="assets/rah-seamless-dev.png" alt="Rah routes local coding agent commands and files to a remote development host" width="900">
</p>

## The problem Rah solves / Rah 解决的问题

Your laptop may be the best place to run an agent: it has your login session, your editor, and the workflow you already trust. But the real project may live on a GPU server, a lab workstation, a cluster login node, or a machine behind a private network. Copying repositories, datasets, virtual environments, and outputs back and forth quickly becomes the work.

你的笔记本可能最适合运行 agent：登录态、编辑器和工作流都已经准备好了。但真正的项目往往在 GPU 服务器、实验室工作站、集群登录节点，或者一台藏在私网后的机器上。反复同步代码、数据集、虚拟环境和输出文件，很快就会变成新的负担。

Rah keeps the agent on the machine you choose, while making the remote project feel local. You do not need to teach the model to remember SSH, prefix every command, or copy large data just to run a test.

Rah 把 agent 留在你指定的机器上，同时让远端项目拥有接近本地开发的体验。你不需要反复提醒模型使用 SSH，也不需要给每条命令加前缀，更不用为了跑一次测试就搬运大型数据集。

The important distinction is that Rah turns shared servers into execution targets, not additional agent hosts. You keep one familiar agent environment and one trusted login session, while each server contributes the compute, data, or network access it already has.

关键区别在于：Rah 把共享服务器变成执行目标，而不是更多的 agent 主机。你只维护一套熟悉的 agent 环境和一个可信的登录态，每台服务器只提供它原本就拥有的算力、数据或网络访问能力。

## Real-world scenarios / 具体应用场景

### 1. One agent, many shared compute servers / 一台 agent，多台共享计算服务器

This is the core Rah workflow. You have one personal laptop or workstation with Claude Code or Codex, but several shared machines: a GPU server for training, a CPU server for tests, a storage host with large datasets, and perhaps a lab workstation reachable only through an internal network. You do not want to install an agent on every shared machine, consume another login, modify a shared environment, or ask administrators to maintain another tool.

这就是 Rah 最核心的使用方式：你有一台配置了 Claude Code 或 Codex 的个人电脑，但同时拥有多台共享机器——一台用于训练的 GPU 服务器、一台用于测试的 CPU 服务器、一台存放大型数据集的存储主机，以及一台只能通过内网访问的实验室工作站。你不希望在每台共享机器上安装 agent、重复登录、污染公共环境，也不希望让管理员额外维护一套工具。

Install the agent and Rah once on your own host. Give each server a clear SSH alias, then mount whichever project you need:

只在自己的主机上安装一次 agent 和 Rah，为每台服务器配置清晰的 SSH alias，然后按需挂载项目：

```bash
rah setup gpu-train:~/projects/model
rah setup cpu-test:~/projects/model
rah setup lab-workstation:~/projects/model
```

The agent configuration stays local and shared servers remain clean. Switch the working directory to switch compute; the same normal commands—`pytest`, `python train.py`, `nvidia-smi`, and dataset inspection—run on the selected remote host.

agent 配置始终留在本地，所有共享服务器保持干净。切换工作目录就能切换算力；`pytest`、`python train.py`、`nvidia-smi` 和数据集检查等普通命令，都会在当前选中的远端主机执行。

### 2. Laptop + remote GPU workstation / 笔记本 + 远程 GPU 工作站

Keep Claude Code or Codex on your Mac or Linux laptop. Mount the project from a remote GPU box, ask the agent to edit code and run tests, and let `nvidia-smi`, training jobs, datasets, and model weights stay on the GPU box. Only the code tree is mounted; the heavy data never has to cross the network.

把 Claude Code 或 Codex 留在你的 Mac/Linux 笔记本上，把远程 GPU 机器上的项目挂载进来。让 agent 修改代码、运行测试，`nvidia-smi`、训练任务、数据集和模型权重都在 GPU 机器上执行。Rah 只挂载代码树，大型数据不需要跨网络搬运。

### 3. Home lab or office machine behind NAT / NAT 后的家庭实验室或办公主机

Your workstation does not need a public IP. Give it reachability with Tailscale or a reverse SSH tunnel, expose that route as an SSH config alias, and point Rah at the alias. The same alias is inherited by both the file and command planes.

你的工作站不需要公网 IP。可以用 Tailscale 或反向 SSH 隧道提供可达性，再把连接写成 SSH config alias，最后让 Rah 使用这个 alias。文件挂载和命令执行会共同继承这套 SSH 配置。

### 4. A trusted agent gateway for a team or lab / 团队或实验室的可信 agent 网关

Run the agent on one trusted Linux host and let approved users reach that host through your existing access channel. Each user can mount their own remote project into an isolated working directory. The agent session stays centralized, while code, credentials, data, and compute remain on the correct remote host.

让 agent 运行在一台可信的 Linux 主机上，用户通过现有的访问方式进入这台主机，再把各自的远端项目挂载到隔离的工作目录中。agent 会话集中管理，而代码、凭据、数据和算力仍然留在各自的远端机器上。

This is an operational pattern for trusted environments, not a way to bypass provider policies or share credentials carelessly. Read the security notes before using it with other people or untrusted repositories.

这是一种适用于可信环境的运维模式，不是绕过服务商政策或随意共享凭据的方法。和他人使用、或在不可信仓库中使用前，请先阅读安全说明。

### 5. Multiple remote projects without multiple agent setups / 多个远程项目，一个 agent 环境

Mount several projects under one agent host, switch directories, and use `rah status`, `rah remount`, and optional autostart to keep the working set healthy across network drops, laptop sleep, and reboots.

在同一台 agent 主机上挂载多个项目，切换目录即可切换远端环境；配合 `rah status`、`rah remount` 和可选的自动恢复，可以应对网络中断、笔记本睡眠和重启后的恢复问题。

## How it works / 工作原理

Rah deliberately separates the file plane from the execution plane:

Rah 有意把文件面和执行面分开：

| Plane / 平面 | English | 中文 |
|---|---|---|
| File plane / 文件面 | SSHFS mounts the remote code tree into a local directory. | SSHFS 把远端代码树挂载到本地目录。 |
| Execution plane / 执行面 | An agent hook rewrites Bash commands to `rah run`; Rah sends them over SSH and preserves the exit code. | agent hook 把 Bash 命令改写为 `rah run`；Rah 通过 SSH 发送命令并保留退出码。 |
| Working directory / 工作目录 | The local mount path maps back to the remote project path before execution. | 执行前会把本地挂载路径映射回远端项目路径。 |
| Recovery / 恢复 | `rah remount` and optional system services restore a dead or unmounted file plane. | `rah remount` 和可选的系统服务负责恢复失效或未挂载的文件面。 |

```text
agent file tools ──► local SSHFS mount ──► remote code tree
agent commands ────► PreToolUse hook ────► rah run ──► SSH ──► remote shell
```

The agent sees a local directory and a normal shell. Commands run on the remote host with its environment, GPU, datasets, and credentials; the remote host does not need Rah installed.

agent 看到的是本地目录和普通 shell。命令会在远端主机的环境中执行，可以直接使用远端 GPU、数据集和凭据；远端主机不需要安装 Rah。

Rah is not a general-purpose file synchronization service. It is a remote development bridge: mount the code you edit, and keep datasets, outputs, caches, and model weights native to the machine that executes the workload.

Rah 不是通用文件同步服务，而是远程开发桥接工具：挂载你需要编辑的代码，让数据集、输出、缓存和模型权重留在真正执行任务的机器上。

## Quick start / 快速开始

### 1. Install / 安装

Install Rah on the machine that runs Claude Code or Codex. The remote host only needs SSH access, a POSIX-like shell, and `base64`.

把 Rah 安装在运行 Claude Code 或 Codex 的机器上。远端只需要 SSH、类 Unix shell 和 `base64`。

```bash
curl -fsSL https://raw.githubusercontent.com/Hiaa1/rah/main/install.sh | bash
rah version
```

For a production environment, inspect or pin the installer source instead of blindly executing an unpinned remote script.

在生产环境中，建议先检查或固定安装脚本版本，不要无条件执行未固定版本的远程脚本。

### 2. Set up your first project / 配置第一个项目

Run setup in a real terminal. It may need to install local dependencies, authorize an SSH key, create a mount directory, or ask for macFUSE permissions on macOS.

请在真实终端运行 setup。它可能需要安装本地依赖、授权 SSH key、创建挂载目录，或者在 macOS 上请求 macFUSE 权限。

```bash
rah setup you@host:~/project

# Non-default SSH port / 非默认 SSH 端口
rah setup --port 2222 you@host:~/project

# Explicit local mount path / 指定本地挂载目录
rah setup you@host:~/project ~/projects/project
```

The interactive form is also available:

也可以直接使用交互式向导：

```bash
rah setup
```

It asks for the SSH target, port, remote project path, and local mount path. It wires hooks for any installed Claude Code or Codex configuration it finds, then mounts the project.

向导会询问 SSH 目标、端口、远端项目路径和本地挂载路径；随后为检测到的 Claude Code 或 Codex 配置安装 hook，并挂载项目。

### 3. Start the agent / 启动 agent

```bash
cd ~/mnt_rah/project
rah verify
codex       # or: claude
```

From this directory, use the agent normally. Ask it to edit files, run tests, inspect remote datasets, or launch a GPU job. The file edits land on the remote project, and the commands execute on the remote host.

进入这个目录后就可以正常使用 agent：让它修改文件、运行测试、读取远端数据集或启动 GPU 任务。文件修改会落到远端项目，命令也会在远端主机执行。

If Rah is not automatically wired during setup, run one of these commands and restart the agent once:

如果 setup 没有自动安装 hook，可以执行下面的命令之一，然后重启 agent 一次：

```bash
rah init claude
rah init codex
```

Once the hook is installed, adding another shared server does not require another agent setup or another agent login. Configure the SSH alias and run `rah setup` for the new project; the same local Claude Code or Codex session can use it immediately.

hook 安装好之后，新增共享服务器不需要重新配置 agent，也不需要再次登录 agent。只需配置 SSH alias，再为新项目运行 `rah setup`；同一个本地 Claude Code 或 Codex 会话即可直接使用它。

## Supported environments / 支持的环境

- **Agent host / agent 主机:** Linux or macOS with SSHFS/FUSE support. Ubuntu, Debian, WSL2, and macOS are the primary targets.
- **Remote host / 远端主机:** Linux or macOS with OpenSSH, a POSIX-like shell, and `base64`. A Windows/WSL2 remote is experimental unless it provides the same environment.
- **SSH:** Passwordless key-based access is required. `ssh <host> true` must succeed without a password prompt.
- **Native Windows agent host / 原生 Windows agent 主机:** Not supported today; use WSL2 or SSH into a Linux agent host.
- **Codex execution mode / Codex 执行模式:** Interactive CLI/TUI is the supported path; `codex exec` is not the target path today.

本地 agent 主机需要 Linux 或 macOS，并支持 SSHFS/FUSE；主要目标是 Ubuntu、Debian、WSL2 和 macOS。远端主要支持 Linux/macOS，实验性支持提供类 Unix shell 的 Windows/WSL2。SSH 必须可以免密码执行，原生 Windows agent 主机目前不在支持范围内；Codex 目前支持交互式 CLI/TUI，不以 `codex exec` 为目标路径。

### Local dependencies / 本地依赖

On Linux, Rah expects `bash`, `ssh`, `sshfs`, `jq`, `base64`, `timeout`, `mountpoint`, and FUSE tools. On macOS, it expects `bash`, `ssh`, `sshfs` through macFUSE, `jq`, `base64`, and `perl`. `curl` is needed for installation and self-update.

Linux 本地需要 `bash`、`ssh`、`sshfs`、`jq`、`base64`、`timeout`、`mountpoint` 和 FUSE 工具。macOS 本地需要 `bash`、`ssh`、通过 macFUSE 提供的 `sshfs`、`jq`、`base64` 和 `perl`。安装和自更新需要 `curl`。

Run `rah doctor` to inspect the local environment. On macOS, Rah can guide you through Homebrew, MacPorts, or manual macFUSE/SSHFS installation.

运行 `rah doctor` 可以检查本地环境。macOS 上 Rah 会提示使用 Homebrew、MacPorts 或手动安装 macFUSE/SSHFS。

On macOS, the first mount may require approving the macFUSE system extension in System Settings. If `rah` is installed but your shell cannot find it, reopen the terminal or add `~/.local/bin` to `PATH`.

在 macOS 上，第一次挂载可能需要在系统设置中允许 macFUSE 系统扩展。如果已经安装 Rah 但 shell 找不到命令，请重新打开终端，或把 `~/.local/bin` 加入 `PATH`。

## Commands / 命令

### Everyday commands / 日常命令

| Command | Purpose / 用途 |
|---|---|
| `rah setup [target] [local-path]` | Guided first-time setup: dependencies, SSH, agent hook, and mount. / 首次向导：依赖、SSH、agent hook 和挂载。 |
| `rah mount user@host:/path [local-path]` | Add a remote project mount. / 增加一个远端项目挂载。 |
| `rah status [--current]` | Show mount, SSH, execution, autostart, and agent-hook health. / 查看挂载、SSH、执行面、自动恢复和 agent hook 状态。 |
| `rah verify [name\|path]` | Run an end-to-end project and hook check. / 执行端到端项目和 hook 检查。 |
| `rah remount [--force] [name\|path]` | Recover dead or unmounted projects. / 恢复失效或未挂载的项目。 |
| `rah unmount <name\|path>` | Disconnect the mount but keep its configuration. / 断开挂载但保留配置。 |
| `rah remove [--keep-local] [name\|path]` | Remove the mount configuration and optionally the empty local directory. / 删除挂载配置，并可删除空的本地目录。 |
| `rah doctor` | Check local dependencies and managed mounts. / 检查本地依赖和受管理的挂载。 |
| `rah init <claude\|codex>` | Install or remove the agent hook and Rah skill. / 安装或移除 agent hook 和 Rah skill。 |

### Lifecycle and diagnostics / 生命周期与诊断

| Command | Purpose / 用途 |
|---|---|
| `rah autostart on\|off\|status` | Restore managed mounts after login or reboot. / 在登录或重启后恢复受管理的挂载。 |
| `rah hook-log on\|off\|status\|clear` | Inspect hook routing decisions. / 查看 hook 的路由决策。 |
| `rah self-update` | Fetch the latest Rah script. / 获取最新 Rah 脚本。 |
| `rah uninstall [--purge]` | Remove Rah hooks, skills, binary, and optionally configuration. / 移除 Rah hook、skill、程序和可选的配置。 |

`rah run` and `rah hook` are plumbing commands used by the agent integration. They are useful for debugging and automation, but normal users should not need to prefix their commands with either one.

`rah run` 和 `rah hook` 是 agent 集成使用的底层命令，适合调试和自动化；日常使用时不需要手动给命令加这两个前缀。

### Advanced mount options / 高级挂载选项

```bash
# Name a mount, select a port, and prepare the remote environment
# 指定挂载名、端口，并在每条远端命令前准备环境
rah mount --name gpu-project --port 2222 --prelude 'source .venv/bin/activate' \
  you@host:~/project ~/mnt_rah/gpu-project

# Use the same absolute path on both hosts when you intentionally need it
# 如果确实需要两端使用同一个绝对路径
rah mount --same-path you@host:/home/you/project

# Inspect all mounts or only the current project
# 查看全部挂载或当前项目
rah status --all
rah status --current

# Remove a hook without removing the rest of the agent configuration
# 只移除 Rah hook，不删除 agent 的其他配置
rah init claude --remove
```

Use `--prelude` for lightweight environment setup such as activating a virtual environment. Keep datasets and outputs outside the mounted code tree whenever possible.

可以用 `--prelude` 做轻量的环境准备，例如激活虚拟环境。数据集和输出文件应尽量放在挂载代码树之外。

## Remote behind NAT / 远端位于 NAT 后

Rah needs a reachable SSH destination. If the remote cannot accept inbound SSH, solve reachability below Rah and then use an SSH config alias. Both SSH command execution and SSHFS mounting inherit `HostName`, `Port`, `ProxyJump`, and `ProxyCommand` from that alias.

Rah 需要一个可达的 SSH 目标。如果远端无法接收入站 SSH，应先在 Rah 下面一层解决网络可达性，再使用 SSH config alias。命令执行和 SSHFS 挂载都会继承 alias 中的 `HostName`、`Port`、`ProxyJump` 和 `ProxyCommand`。

### Tailscale / Tailscale

Tailscale is the recommended option when both machines are behind NAT:

当两台机器都位于 NAT 后时，推荐使用 Tailscale：

1. Install Tailscale on both machines and join the same tailnet. / 在两台机器上安装 Tailscale 并加入同一个 tailnet。
2. Add an alias on the agent host: / 在 agent 主机上添加 alias：

   ```sshconfig
   Host gpu-home
       HostName gpu-home.tailXXXX.ts.net
       User you
   ```

3. Use the alias with Rah: / 使用 alias 配置 Rah：

   ```bash
   rah setup gpu-home:/home/you/project
   ```

### Reverse SSH tunnel / 反向 SSH 隧道

If you have a public relay, keep a reverse tunnel from the remote host to the relay and expose the forwarded route as an SSH alias:

如果你有公网中继机，可以让远端维持到中继机的反向隧道，再把转发路径配置成 SSH alias：

```bash
autossh -M 0 -N -R 2222:localhost:22 you@relay.example.com
```

Rah does not need a NAT-specific flag. It only needs the alias to work with both `ssh` and `sshfs`.

Rah 不需要额外的 NAT 参数，只要这个 alias 同时能被 `ssh` 和 `sshfs` 使用即可。

## Recovery and autostart / 恢复与自动启动

A network drop, remote reboot, or laptop sleep can leave an SSHFS mount in a dead state. File tools may report `Transport endpoint is not connected` or hang, while the separate SSH execution plane can still work.

网络中断、远端重启或笔记本睡眠可能让 SSHFS 挂载进入 dead 状态。文件工具可能报 `Transport endpoint is not connected` 或卡住，但独立的 SSH 执行面仍可能继续工作。

```bash
rah status
rah remount
```

`rah remount` is idempotent and can be run from inside an agent session because it executes on the local control plane. The hook also performs throttled background recovery checks while you work.

`rah remount` 具有幂等性，即使在 agent 会话中也可以执行，因为它运行在本地控制面。工作过程中 hook 还会节流地进行后台恢复检查。

Enable optional persistence when mounts should return after login or reboot:

如果希望登录或重启后自动恢复挂载，可以启用可选的持久化：

```bash
rah autostart on
rah autostart status
```

Linux uses `systemd --user`; macOS uses a LaunchAgent. Disable it with `rah autostart off`.

Linux 使用 `systemd --user`，macOS 使用 LaunchAgent。可以用 `rah autostart off` 关闭。

## Hook diagnostics / Hook 诊断

If a command appears to run locally from inside a managed mount, enable the hook log and retry one command:

如果 agent 在受管理挂载内看起来仍然在本地执行，可以开启 hook 日志并重试一条命令：

```bash
rah hook-log on
rah hook-log clear
```

Inspect `~/.config/rah/hook.jsonl`, then disable logging:

查看 `~/.config/rah/hook.jsonl`，完成后关闭日志：

```bash
rah hook-log off
```

The log can contain command text. Do not leave it enabled around secrets, tokens, or sensitive arguments.

日志可能包含命令文本。涉及 secret、token 或敏感参数时，不要长时间开启日志。

## Agent support / Agent 支持

| Agent | Current target / 当前目标 | Hook installed by `rah init` |
|---|---|---|
| Claude Code | v2.1.158+ | `rah hook --decision allow` |
| Codex CLI | v0.137.0+ interactive TUI | `rah hook --decision allow --passthrough empty` |

Codex may ask you to review hooks after installation or update. Review the command and choose the trust option only when you understand and accept that commands inside Rah-managed mounts will be routed to the remote host.

Codex 安装或更新后可能要求 review hook。只有在理解并接受“Rah 管理挂载内的命令会被转发到远端”这一行为后，才应选择信任选项。

## Security / 安全

Rah changes where agent commands execute. The installed hooks use `permissionDecision: "allow"` because the supported agent integrations require an allow decision for command rewrites to take effect. Inside a Rah-managed mount, the hook approves and routes the command after checking the working-directory boundary; outside a managed mount, commands pass through unchanged.

Rah 会改变 agent 命令的实际执行位置。由于当前 agent 集成要求 `allow` 决策才能应用命令改写，Rah 安装的 hook 会使用 `permissionDecision: "allow"`。在 Rah 管理的挂载内，hook 检查工作目录边界后批准并转发命令；在挂载外，命令保持原样放行。

Only install Rah hooks on an agent host you trust. Treat a managed remote project as a command-execution boundary: prompt injection or malicious project instructions can cause the agent to execute commands on that remote host. Keep SSH permissions narrow, review hooks after installation, and use `rah hook-log` only when needed.

只在你信任的 agent 主机上安装 Rah hook。请把受管理的远程项目视为一个命令执行边界：提示注入或恶意项目指令可能诱导 agent 在远端执行命令。请收紧 SSH 权限，安装后 review hook，并只在需要时开启 `rah hook-log`。

## Limitations / 当前限制

- Native Windows as the agent host is not supported. Use WSL2 or a Linux agent host. / 不支持原生 Windows 作为 agent 主机，请使用 WSL2 或 Linux agent 主机。
- SSHFS is designed for source trees, not large datasets or high-throughput storage. / SSHFS 适合代码树，不适合作为大型数据集或高吞吐存储层。
- The remote host must provide a compatible shell and `base64`; a normal Windows command environment is not a stable target. / 远端需要兼容的 shell 和 `base64`，普通 Windows 命令环境不是稳定目标。
- `codex exec` is not the supported transparent-routing path today. / 当前不支持通过 `codex exec` 实现透明远端执行。

## License / 许可证

[MIT](LICENSE)
