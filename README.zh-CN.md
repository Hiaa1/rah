# Remote as Host (rah)

<p align="center">
  <img src="assets/rah-logo.svg" alt="Rah logo - local agent with files mounted from a remote host and commands routed to it" width="720">
</p>

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.2.0-blue)](rah)
[![Views](https://hits.sh/github.com/Hiaa1/rah.svg?label=views&color=0e75b6)](https://hits.sh/github.com/Hiaa1/rah/)
[![Claude Code](https://img.shields.io/badge/Claude_Code-compatible-7C3AED)](README.zh-CN.md#agent-支持)
[![Codex CLI](https://img.shields.io/badge/Codex_CLI-compatible-111827)](README.zh-CN.md#agent-支持)

[English](README.md)

Rah 让 Claude Code / Codex 像在远端机器上一样开发项目，但账号只登录在你指定的一台电脑上。

典型场景：

- A 电脑运行 Claude Code / Codex，并安装 `rah`。
- B 电脑或服务器保存真实项目、大数据集、模型权重和 GPU 环境。
- 你在 A 上正常使用 agent；文件来自 B，命令也在 B 上执行。

适合你如果：

- 不想把 Claude Code / Codex 登录态散落到多台电脑、不同网络或不同 VPN 出口。
- 想用本地 agent 操作远端工作站、服务器或实验机器。
- 不想复制大数据集、不想靠 git 同步开发状态。

Rah 做两件事：

- 把远端项目目录挂载成本地目录，例如 `~/mnt_rah/<project>`，你可以像编辑本地文件一样编辑远端代码。
- 自动把 agent 的 shell 命令转发到远端执行，例如测试、训练、调用 GPU、读取大数据集。

这些转发由 hook 自动完成，不靠提示词提醒 agent，所以 agent 不需要知道自己在“远程开发”。
**远端零安装**：只在 agent 所在机器安装 `rah`；远端只需要标准 SSH 和基本 shell 工具。

## 机器角色

- **agent host**：运行 Claude Code / Codex 和 `rah` 的机器。
- **remote host**：存放项目、数据、环境和 GPU，并真正执行命令的机器。

**Rah 安装在 agent host 上，不安装在 remote host 上。**

当前稳定支持的 agent host 是具备 sshfs/FUSE、`ssh` 和标准 shell 工具的 Linux 环境，主要是 Ubuntu、Debian、WSL2 或 Linux gateway。
原生 macOS / 原生 Windows 作为 agent host 还不是稳定目标；Windows 用户优先使用 WSL2，macOS 用户可以使用一台 Linux gateway。

remote host 不需要安装 `rah`。它只需要能 SSH 登录，并提供可访问的项目目录；Linux server、workstation，或开启 SSH 的 macOS 机器都可以作为 remote target。

## 可信 Agent 网关

如果你购买了 Claude Code 或 Codex 的个人 plan，又想在多台电脑上使用，频繁从不同设备、
网络或 VPN 出口登录同一账号可能增加风控风险。Rah 推荐把 agent 账号固定在一台可信的
agent host 上；其它电脑通过你自己的远程访问方式连接到这台 agent host，再由 Rah 操控真正的
remote host。这样账号登录态只留在一个地方，项目和命令执行仍然发生在正确的远端机器上。

<p align="center">
  <img src="assets/rah-seamless-dev.png" alt="Rah 让本地 coding agent 保持正常体验，同时由 hook 将命令路由到远端执行" width="900">
</p>

## 安装和使用

### 先确认环境

- 在运行 Claude Code / Codex 的这台机器上安装 `rah`。当前推荐 Ubuntu、Debian、WSL2 或 Linux gateway。
- 远端机器只需要开启 SSH，并且有你的项目目录；远端不需要安装 `rah`。
- 如果远端 SSH 不是默认 22 端口，后面 setup 时填 `--port` 即可。

### 选择一种安装方式

下面两种方式二选一，不需要都执行。

**方式一：终端一行安装（推荐）**

```bash
curl -fsSL https://raw.githubusercontent.com/Hiaa1/rah/main/install.sh | bash
```

安装后检查一下：

```bash
rah version
```

如果提示找不到 `rah`，重新打开终端，或者把 `~/.local/bin` 加到 `PATH`。

**方式二：让 Claude Code / Codex 帮你安装**

在 agent 会话里直接说：

> **“Install Rah from github.com/Hiaa1/rah and set it up for `you@host:~/project`.”**

agent 可以帮你下载和运行命令。如果遇到 `sudo`、SSH 密码或 `ssh-copy-id`，请按它给出的命令回到真实终端执行一次。

### 第一次连接远端项目

在真实终端里运行：

```bash
rah setup
```

它会依次询问：

- SSH 地址，例如 `you@devbox.example.com`
- SSH 端口，可以直接回车使用默认端口
- 远端项目目录，例如 `~/project`
- 本地挂载目录，可以直接回车使用默认 `~/mnt_rah/<project>`

如果你已经知道完整参数，也可以一行完成：

```bash
rah setup you@host:~/project
rah setup --port 2222 you@devbox.example.com:~/project
rah setup you@host:~/project ~/projects/project
```

> `rah setup` 可能需要安装本地依赖、授权 SSH key 或创建本地目录，这些步骤可能要求输入密码。请在真实终端运行它，不要在 agent 的无 TTY shell 里运行。

### 开始开发

setup 完成后，进入本地挂载目录：

```bash
cd ~/mnt_rah/project
rah verify
```

验证通过后，从这个目录启动 Claude Code / Codex。之后你照常让 agent 读写文件、运行测试或启动训练：

- agent 看到的是本地目录
- 文件实际来自远端项目
- shell 命令实际在远端执行

第一次安装 hook 后需要重启一次 agent。之后新增项目只需要再次运行 `rah setup` 或 `rah mount`，不需要重新配置 agent。完全移除可运行 `rah uninstall`。

## 命令

| 命令 | 用途 |
|---|---|
| `rah setup [--port PORT] [user@host:/path] [local-path] [-y]` | 引导式初始化：依赖、ssh key、agent hook、挂载 |
| `rah mount [--name N] [--port PORT] [--prelude CMD] user@host:/path [local-path]` | 把远端代码树挂到本地，默认 `~/mnt_rah/<project>` |
| `rah mount --same-path user@host:/abs/path` | 显式使用本地/远端完全同路径模式 |
| `rah remount [name\|path]` | 恢复失效或 stale mount，不传目标则恢复全部 |
| `rah unmount <name\|path>` | 卸载并关闭 ssh master 连接，保留配置 |
| `rah remove [--keep-local] [name\|path]` | 卸载、删除 rah 配置，并删除空的 mountpoint 目录；不传目标则使用当前 mount |
| `rah init <claude\|codex> [--remove]` | 安装或移除 agent hook 和 skill |
| `rah status` / `rah list` | 查看 mount / ssh / exec / agent hook 状态 |
| `rah verify [name\|path]` | 端到端检查 mount、ssh、hook |
| `rah doctor` | 检查依赖、PATH、mount 健康状态 |
| `rah self-update` | 更新到最新版本 |
| `rah uninstall [--purge]` | 移除 hook、skill 和 `rah` 二进制 |
| `rah run --cwd <dir> -- <cmd>` | 在远端执行命令，hook 内部使用 |
| `rah hook-log on\|off\|status\|clear` | 开启或查看 hook 诊断日志 |

## Mount 管理

用 `rah status` 或 `rah list` 查看所有受管理 mount，包括名称、远端路径、本地路径、mount 健康状态、ssh 连通性和执行面健康状态。

- `rah unmount <name|path>` 只断开 mount，保留配置，之后可以用 `rah remount <name|path>` 恢复。
- `rah remove [name|path]` 会断开 mount、删除 rah 配置，并且只在本地 mountpoint 为空时删除这个目录。
- `rah remove --keep-local [name|path]` 删除 rah 配置，但保留本地目录。

## 工作原理

<p align="center">
  <img src="assets/rah-workflow.png" alt="Rah 工作流：远端文件挂载到本地，命令再路由回远端执行" width="900">
</p>

```text
agent file tools -> local sshfs mount -> remote code tree
agent commands -> PreToolUse hook -> rah run -> ssh(ControlMaster) -> remote: cd + prelude + cmd
```

hook 按工作目录自门控：不在 rah 管理的 mount 内时，命令原样放行，所以全局安装也安全。命令以 base64 形式传到远端，避免 shell quoting 和注入问题；远端退出码会原样传播，agent 的运行和验证循环可以正常工作。在映射模式下，rah 会在远端执行前把本地 cwd 和命令里的本地绝对路径前缀翻译回远端项目路径。独立的 `cd` 会保留在本地，以维持 agent 持久 shell 的 cwd。

## 恢复

网络中断、远端重启或本机睡眠都可能让 sshfs mount 变成 **dead**。此时文件工具可能报 `Transport endpoint is not connected` 或卡住。因为执行面和文件面是分开的，**命令执行仍会继续工作**。恢复文件面：

- `rah remount` 会重新建立 ssh 和 sshfs，幂等，可在会话中途运行。
- hook 也会 **自愈**：工作时会节流探测 mount；如果发现 mount 已死，会后台触发 `rah remount`，通常能自动恢复。
- `rah status` 会报告 `mounted` / `DEAD` / `not mounted`，使用真实 liveness probe，而不是 stale 标记。

## Hook 诊断

如果 agent 在受管理 mount 内看起来仍然本地执行，开启 hook 日志并重试一条命令：

```bash
rah hook-log on
rah hook-log clear
```

然后在 agent 里运行可疑命令，查看 `~/.config/rah/hook.jsonl`。每条 JSONL 会记录 hook 是否触发、上报/实际 cwd、是否匹配 mount、route 还是 passthrough，以及发出的 decision。用 `rah hook-log off` 关闭。一次性调试也可以在启动 agent 时设置 `RAH_HOOK_LOG=1`，或把它设为日志路径。

## Agent 支持

| Agent | 状态 | `rah init` 安装的 hook |
|---|---|---|
| Claude Code v2.1.158+ | 已实测 | `rah hook --decision allow` |
| Codex CLI v0.137.0+ 交互式 TUI | 已实测 | `rah hook --decision allow --passthrough empty` |

Codex 在安装或更新后可能要求你 review hooks。对 rah hook 选择 **Trust all and continue** 后，从受管理 mount 发出的命令会路由到远端。`codex exec` 目前不是 rah 的目标路径；透明远端执行请使用交互式 CLI/TUI。

## 要求

- **支持的 agent host**：具备 sshfs/FUSE 支持的 Linux；主要目标是 Ubuntu、Debian、WSL2 或 Linux gateway。原生 macOS / 原生 Windows 作为 agent host 暂未稳定支持。
- **本地依赖包**：`bash`、`ssh`、`sshfs`（加 `fuse`/`fuse3`）、`jq`、`coreutils`（`base64`）、`util-linux`（`mountpoint`）；安装和自更新需要 `curl`。运行 `rah doctor` 检查。
- **SSH**：必须能 passwordless key-based ssh 到远端，`ssh <host> true` 不能要求输入密码。`rah setup` 会预检，并在缺失时提示 `ssh-copy-id`。
- **远端**：只需要标准 OpenSSH server、POSIX shell 和 `base64`。Linux server/workstation 或开启 SSH 的 macOS 都可以作为 remote target。

## 安全

`rah` 会把 agent 的命令执行路由到远端主机。Claude 和 Codex 当前都需要 `permissionDecision: "allow"` 才会应用 `updatedInput.command` 改写，所以 `rah init claude` 和 `rah init codex` 会安装 allow-mode hook。位于 rah 管理 mount 内的命令会在 cwd 门控后由 hook 批准；mount 外的命令保持原样放行（Claude 收到 `defer`，Codex 收到空 hook 响应）。需要排查时，可以用 `rah hook-log` 查看每次 hook 的路由决策。

## License

[MIT](LICENSE)
