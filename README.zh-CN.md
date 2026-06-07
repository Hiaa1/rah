# Remote as Host (rah)

<p align="center">
  <img src="assets/rah-logo.svg" alt="Rah logo - local agent with files mounted from a remote host and commands routed to it" width="720">
</p>

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.2.0-blue)](rah)
[![Bash](https://img.shields.io/badge/Bash-single_file-4EAA25?logo=gnubash&logoColor=white)](rah)
[![Claude Code](https://img.shields.io/badge/Claude_Code-verified-7C3AED)](README.zh-CN.md#agent-支持)
[![Codex CLI](https://img.shields.io/badge/Codex_CLI-verified-111827)](README.zh-CN.md#agent-支持)

[English](README.md)

让你的本地机器像远端开发机一样服务 coding agent（Claude Code、Codex）。
agent 仍然运行在本地；真正的项目、代码、重数据集和 GPU 都留在远端。
`rah` 给 agent 提供两个被强制执行的平面：

- **文件面**：通过 **sshfs mount** 编辑远端代码树。默认挂到本机 `~/mnt_rah/<project>`，也可以指定任意空的本地目录。数据集不会被挂载，仍留在远端，避免一次误搜索把大量数据拖到本地。
- **执行面**：通过 `PreToolUse` **hook** 把 agent 的 shell 命令透明改写到远端 ssh 执行。这个路由是确定性的，不靠提示词提醒模型。agent 的行为就像它真的在远端机器上一样。

路由是 hook 强制的不变量，不是 prompt 里的请求，所以模型不会“忘记”在远端运行。
**远端零安装**：只在本机安装 `rah`；远端只需要标准的 `sshd`、`bash` 和 `base64`。

## 项目边界

`rah` 有意聚焦在 Linux-based agent gateway 这一种模型上：

- **agent host** 是一台 Linux 环境，能够运行 Claude Code / Codex、`sshfs`/FUSE、`ssh` 和标准 shell 工具。Ubuntu、Debian 和 WSL2 是主要目标。
- **remote host** 只需要 OpenSSH server 和 POSIX shell；远端不需要安装 `rah`。
- 不同 Linux 发行版的差异主要在安装依赖：Ubuntu/Debian/WSL2 可以走 `apt-get` 引导安装，其它 Linux 发行版需要用自己的包管理器安装等价依赖。

原生 macOS 和原生 Windows 不在当前项目范围内。如果个人设备是 macOS 或 Windows，请使用 Linux gateway 机器或 WSL2。

## 可信 Agent 网关

`rah` 也支持一种更安全的 coding agent 账号模型：只在一台可信机器上登录 Claude Code / Codex，
个人电脑通过你自己的远程访问方式连到这台机器；再由这台机器通过 `rah` 去操控任意 server 或 workstation。

这样可以避免把 agent 登录态、浏览器会话、API token 和账号风险散落到多台个人设备上，尤其是多台设备使用不同 VPN 出口或网络位置时。
agent 账号只留在一个地方；真正的项目执行仍然发生在正确的远端机器上。

<p align="center">
  <img src="assets/rah-seamless-dev.png" alt="Rah 让本地 coding agent 保持正常体验，同时由 hook 将命令路由到远端执行" width="900">
</p>

## 安装

```bash
# 一行安装，重复运行可升级
curl -fsSL https://raw.githubusercontent.com/Hiaa1/rah/main/install.sh | bash
```

想先读代码再运行，也可以 clone 后安装这个单文件脚本：

```bash
git clone https://github.com/Hiaa1/rah && cd rah && ./install.sh
```

`rah` 是一个自包含 Bash 脚本，方便审计，也可以直接 `scp` 到其它机器。

### 平台说明

支持的运行环境是具备 sshfs/FUSE 和必要命令行工具的 Linux。在 Ubuntu、Debian 和 WSL2 上，
`rah setup` 可以询问后通过 `sudo apt-get` 自动安装缺失的本地包。其它 Linux 发行版请先用自己的包管理器安装等价依赖，再运行 setup。

### 或者直接让 agent 安装

在任意 Claude Code / Codex 会话里，一句话就够：

> **“Install rah from github.com/Hiaa1/rah and set it up for `you@host:~/project`.”**

agent 会按这个 README 操作：检查 passwordless ssh，如果缺失会引导你运行 `ssh-copy-id`
（只需要那一次输入远端密码），安装 rah，并运行 `rah setup`。你只需要提供远端地址、完成一次 ssh 授权，并在第一次安装 hook 后重启 agent。

## 快速开始

一条命令进入引导式 setup。它会询问 ssh target、可选端口、远端项目路径、本地挂载目录，然后检查依赖、配置已安装的 agent、挂载，并打印实际执行的完整命令：

```bash
rah setup
```

脚本化或重复部署时，也可以显式传完整参数：

```bash
rah setup you@host:~/project
rah setup --port 27867 you@10.19.125.121:~/project
```

> **请在真实终端里运行 `rah setup`，不要在 coding agent 里运行。** 它会通过 `[Y/n]` 提示处理缺失前置条件：安装依赖（`sudo apt`）、生成并授权 ssh key（`ssh-copy-id`），或者在你指定的本地挂载目录需要 root 时创建目录（`sudo`）。这些步骤需要 TTY 来读取密码，而 coding agent 的 shell，包括 Claude Code 的 `!`，没有 TTY，所以会失败。加 `-y` 可以默认确认。无 TTY 运行时，`rah setup` 会检测到并打印需要人手执行的下一步，而不是卡住。

默认本地挂载目录是 `~/mnt_rah/<project>`。如果想挂到自己指定的位置，直接把本地目录作为第二个参数：

```bash
rah setup you@host:~/project ~/Fyx/project
```

如果确实需要本地和远端绝对路径完全一致，可以显式使用 `--same-path`。

第一次部署在终端完成；之后日常使用都在 agent 里完成，agent 不需要 TTY 或 `sudo`。

然后从 mountpoint 内启动 agent。它的文件工具访问挂载目录；它的命令在远端执行。hook 只需要安装一次（第一次需要重启 agent）；之后新挂载项目会立即生效，不需要重启。完全移除可运行：`rah uninstall`。

把项目交给 agent 前，先做一次验收：

```bash
cd ~/mnt_rah/project
rah verify
```

偏好显式步骤的话：`rah doctor` -> `rah init claude`（或 `codex`）-> `rah mount user@host:~/project ~/Fyx/project`。

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

- **支持的本地系统**：具备 sshfs/FUSE 支持的 Linux；主要目标是 Ubuntu、Debian 和 WSL2。当前不支持原生 macOS 和原生 Windows。
- **本地依赖包**：`bash`、`ssh`、`sshfs`（加 `fuse`/`fuse3`）、`jq`、`coreutils`（`base64`）、`util-linux`（`mountpoint`）；安装和自更新需要 `curl`。运行 `rah doctor` 检查。
- **SSH**：必须能 passwordless key-based ssh 到远端，`ssh <host> true` 不能要求输入密码。`rah setup` 会预检，并在缺失时提示 `ssh-copy-id`。
- **远端**：只需要标准 OpenSSH server 和 POSIX shell。

## 安全

`rah` 会把 agent 的命令执行路由到远端主机。Claude 和 Codex 当前都需要 `permissionDecision: "allow"` 才会应用 `updatedInput.command` 改写，所以 `rah init claude` 和 `rah init codex` 会安装 allow-mode hook。位于 rah 管理 mount 内的命令会在 cwd 门控后由 hook 批准；mount 外的命令保持原样放行（Claude 收到 `defer`，Codex 收到空 hook 响应）。整个工具是一个可读 Bash 文件；安装前建议审阅。

## License

[MIT](LICENSE)
