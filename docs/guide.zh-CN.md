# rah 使用指南

[← 项目首页](../README.zh-CN.md) · [English](guide.md)

在 agent 主机与远端项目之间配置文件访问、命令路由和故障恢复。

## 命令参考

| 命令 | 用途 |
| :--- | :--- |
| `rah setup [target] [local-path]` | 通过向导配置依赖、SSH、hook 和首次挂载。 |
| `rah mount [options] user@host:/path [local-path]` | 挂载另一个远端项目。 |
| `rah status [--all\|--current] [name\|path]` | 检查文件系统、SSH、执行与集成状态；`rah list` 是其别名。 |
| `rah verify [name\|path]` | 完整检查项目、路径映射和 hook。 |
| `rah remount [--force] [name\|path ...]` | 恢复指定挂载；未指定目标时处理所有挂载。 |
| `rah unmount <name\|path>` | 断开挂载，保留配置。 |
| `rah remove [--keep-local] [name\|path]` | 移除挂载配置，默认还会删除空的本地挂载目录。 |
| `rah autostart on\|off\|status` | 管理开机或登录后的自动恢复。 |
| `rah local [--cwd DIR] -- <command> [args...]` | 在 agent 本机执行一条命令。 |
| `rah run --cwd <local-mount-path> -- <command...>` | 在指定挂载对应的远端执行命令。 |
| `rah init <claude\|codex> [--remove]` | 安装或移除路由 hook 和技能说明。 |
| `rah local-allow list\|add\|remove <absolute-path>` | 管理本机可执行文件例外。 |
| `rah hook-log on\|off\|status\|clear` | 管理路由决策日志。 |
| `rah doctor` | 检查本地依赖和受管理的挂载。 |
| `rah version` | 查看当前安装的程序版本。 |
| `rah self-update` | 更新下载方式安装的程序。 |
| `rah uninstall [--purge]` | 移除集成和程序，可选清除配置。 |

`rah hook` 是 agent 使用的集成入口，通常不需要手动调用。

## 安装与更新

rah 安装在运行 agent 的机器上。本地依赖如下：

- **Linux：** Bash、OpenSSH 客户端、SSHFS、`jq`、`base64`、GNU `timeout`、util-linux 和 FUSE 工具。
- **macOS：** Bash、OpenSSH 客户端、基于 macFUSE 的 SSHFS、`jq`、`base64` 和 Perl；存在 `timeout` 或 `gtimeout` 时会优先使用。
- **下载更新：** `curl`。
- **运行测试：** Python 3，以及相关本机工具。

远端需要启用 SFTP 子系统的 SSH、Bash 和 `base64`。可以通过 `ssh -o BatchMode=yes <host> true` 确认非交互式访问正常。

### 从仓库安装

```bash
git clone https://github.com/Hiaa1/rah.git
cd rah
bash install.sh
rah setup
```

可以在执行前阅读安装脚本，也可以先切换到指定修订。macOS 上的向导支持通过 Homebrew、MacPorts 或 macFUSE/SSHFS 安装程序准备依赖；macFUSE 可能需要在系统设置中授权。

### 更新下载版

```bash
rah self-update
rah version
```

当前更新器从 `main` 下载脚本，不会自动在后台安装新版本或发送桌面通知。`RAH_RAW_URL` 可以指定其他来源。只更新程序文件，并不意味着所有服务和 hook 变更都已生效。

### 更新 Git 仓库版

如果已安装的程序指向 Git 仓库，`rah self-update` 会拒绝覆盖受版本控制的源码。请检查工作区，通过 Git 更新。对于跟踪上游且工作区干净的仓库，可以执行：

```bash
git status
git pull --ff-only
```

如果之前通过 `install.sh` 安装了独立副本，更新仓库后需要重新安装该副本；指向仓库的符号链接则会直接使用修改后的源码。

### 让集成和服务变更生效

刷新你使用的 agent 集成：

```bash
rah init codex
# 或者：rah init claude
```

如果之前启用了自动恢复，重新生成服务配置：

```bash
rah autostart on
rah autostart status
```

Linux 上正在运行的 SSHFS 进程会保留旧连接选项，直到重启。准备好接受短暂的文件系统重连时，运行 `rah remount --force` 应用新选项；编辑器保留旧句柄时，需要重新打开相关文件。

## 远端环境

多台主机上的项目同名时，请指定不同的本地挂载路径：

```bash
rah setup gpu:~/project ~/mnt_rah/gpu-project
rah setup lab:~/project ~/mnt_rah/lab-project
```

为挂载命名、指定端口并激活远端环境：

```bash
rah mount --name gpu-project --port 2222 \
  --prelude 'source .venv/bin/activate' \
  you@host:~/project ~/mnt_rah/gpu-project
```

`--prelude` 在每条命令前、远端项目目录中执行。请保持轻量，因为状态探测也会检查这套执行环境。命令使用远端 shell 环境，不会继承 agent 本机的虚拟环境。

确实需要两端使用相同绝对路径时，可以使用：

```bash
rah mount --same-path you@host:/home/you/project
```

通常情况下，rah 将本地挂载前缀映射回远端项目路径，并转换路由命令文本中匹配的本地挂载路径。`rah verify` 会检查这套映射。

## SSH 与私网连接

在 agent 主机的 `~/.ssh/config` 中定义稳定的 alias：

```sshconfig
Host gpu
    HostName gpu.example.com
    User you
    Port 2222
    IdentityFile ~/.ssh/id_ed25519
```

随后使用 `rah setup gpu:~/project`。文件访问和命令路由都会继承 alias 的连接设置，包括 `ProxyJump` 和 `ProxyCommand`。主机地址改变时，核实其身份后更新 alias。

NAT 后的主机需要先具备可达的 SSH 路径。Tailscale 等私网连接可以提供该路径，将对应主机名写入 SSH alias 即可。也可以**在远端主机上**建立到可达中继机的反向隧道：

```bash
autossh -M 0 -N -R 2222:localhost:22 you@relay.example.com
```

在 agent 主机上，通过跳板连接访问中继机的本地转发端口：

```sshconfig
Host gpu-via-relay
    HostName 127.0.0.1
    Port 2222
    User you
    ProxyJump you@relay.example.com
```

确认 `ssh gpu-via-relay true` 正常后，再运行 `rah setup gpu-via-relay:~/project`。rah 使用已有连接路径，不负责建立私网或维护反向隧道。

## 本机执行与跨挂载访问

假设 B、C 分别挂载到 agent 主机 A 的 `/mnt/b`、`/mnt/c`。agent 在 `/mnt/b` 工作时，普通路由命令在 B 上执行；命令参数中出现 `/mnt/c` 不会改变执行主机。

```bash
# 在 A 执行，读取 A 的本地文件
rah local -- cat /home/you/notes.txt

# 在 A 执行，通过 SSHFS 读取 C 的文件
rah local -- cat /mnt/c/file.txt

# 在 A 比较两个挂载中的文件
rah local -- diff /mnt/b/config.yaml /mnt/c/config.yaml

# 从 A 直接连接 C，在 C 执行命令
rah run --cwd /mnt/c -- cat file.txt
```

Hook 将以 `rah` 开头的命令留在 A 执行，无需 B 能通过 SSH 连接 C。请让 `rah local` 位于 agent 工具命令的开头。

`rah local` 保留参数、标准输入输出和退出码，工作目录也保留在本机。处于 `/mnt/b` 时，相对路径仍访问 B 的挂载文件；用 `--cwd` 或绝对路径选择其他目录。管道和重定向应整体交给本地 shell：

```bash
rah local --cwd /home/you -- bash -c 'cat notes.txt | head -n 20'
```

### 持续在本机执行的工具

将始终需要在 agent 本机运行的工具加入白名单：

```bash
rah local-allow add /home/you/bin/local-helper.sh
rah local-allow list
rah local-allow remove /home/you/bin/local-helper.sh
```

全局文件位于 `~/.config/rah/local-allow`，每行一条绝对路径。命令必须以条目开头，并在词边界结束匹配。`echo /home/you/bin/local-helper.sh` 仍会转发到远端。相对路径、裸命令名和模式匹配会被拒绝；条目缺失或非法不会扩大本地执行范围。

## 恢复与排障

`rah remount` 会跳过健康挂载，`--force` 则会重建它们。Agent hook 还会节流调度后台恢复，调用进程不会同步等待文件系统探测。

### Linux 服务

`rah autostart on` 为每个已配置挂载安装一个 `rah-mount@.service` 实例和一个 `rah-health@.timer` 实例：

- SSHFS 在前台运行，由 systemd 管理进程生命周期。
- 文件与命令流量使用独立 SSH 连接。
- 健康检查查找新的文件名，不向远端写入探测文件。
- 每次查找限时 3 秒，另留 1 秒强杀宽限期。
- 检查失败只重启对应挂载；上一次检查结束 15 秒后进行下一次检查。
- 服务重试之间等待 30 秒，启动和停止也有超时。
- 正常停止和启动失败时都会清理残留挂载，相关进程由服务管理器终止。

`rah unmount <name>` 会停止对应服务，巡检定时器和 hook 不会重新拉起主动停止的服务。`rah remount <name>` 可以恢复它；已启用的服务也会随登录或开机时启动的用户管理器恢复。`rah autostart off` 关闭自动启动，本身不会卸载项目。

```bash
rah autostart status
systemctl --user list-timers 'rah-health@*'
journalctl --user -u 'rah-mount@*' -u 'rah-health@*'
```

如果需要重启后、首次登录前就恢复挂载，需要启用 systemd 用户 lingering；必要时 `rah autostart on` 会给出对应命令。服务也需要在交互式登录会话之外可用的 SSH 凭据。

### macOS 自动恢复

LaunchAgent 周期性执行 `rah remount --best-effort`，默认间隔 300 秒；安装该服务时可通过 `RAH_AUTOSTART_INTERVAL` 调整。手动挂载和 macOS 挂载保留 SSHFS 自身的 `reconnect` 选项。

### 正确理解状态

`rah status` 每批最多检查 8 个挂载，文件系统、SSH 和系统服务汇总同时探测。每次 SSH 连接总限时 3 秒，另留 1 秒强杀宽限期。状态查询不会创建或修复 SSH master。

| 结果 | 含义 / 下一步 |
| :--- | :--- |
| `mounted` | 挂载存在，文件系统探测已响应。 |
| `DEAD` | 文件系统探测失败或未响应，运行 `rah remount <name>`。 |
| `not mounted` | 配置路径上没有挂载。 |
| SSH `TIMEOUT` | 探测超出时间预算，不代表主机永久离线。 |
| Exec `not checked` | SSH 不可用，未重复检查命令执行。 |
| SSH 正常、exec 失败 | 检查远端目录和 `--prelude`，运行 `rah verify <name>`。 |

对于较慢连接或完整的路径与 hook 诊断，使用 `rah verify <name>`。超过 8 个无响应挂载需要分批检查；3 秒 SSH 超时针对单个探测，不是整个命令的总期限。

### VS Code 或文件工具不响应

将编辑器服务、shell 启动配置、rah 程序和 rah 配置保留在本地磁盘。挂载项目目录，避免把主机控制工具放进远端文件系统。

从本地终端运行 `rah remount <name>`。恢复后重新打开受影响的文件，或重新加载 VS Code 窗口。仅分离 FUSE 挂载不能释放已经阻塞在故障 SSHFS 进程中的 I/O，还需要终止对应进程。[SSHFS 官方文档](https://github.com/libfuse/sshfs/blob/master/sshfs.rst)解释了这一行为及其对中断写入的影响。

### 命令似乎在错误的主机上执行

```bash
rah hook-log on
rah hook-log clear
# 复现一条 agent 命令，然后查看日志：
cat ~/.config/rah/hook.jsonl
rah hook-log off
```

Hook 日志可能包含命令文本，分享前请移除敏感参数。检查选中的工作目录，通过 `rah init` 刷新对应集成，再重启 agent。

## 执行与信任

rah 根据 agent 工具调用的工作目录路由命令。安装的 hook 使用 `permissionDecision: "allow"`，以使受支持的集成应用命令改写。在受管理挂载中，hook 检查目录边界后批准并路由命令。挂载之外的命令保持透传；显式本机执行和可执行文件例外另行处理。

只在你信任的 agent 主机上安装这套集成。远端仓库中的指令可能影响 agent 在该主机执行的操作。请将 SSH 权限限制在预期主机和账号范围内，并检查安装的 hook。

项目配置默认位于 `~/.config/rah/*.env`，可通过 `RAH_CONFIG_DIR` 覆盖。配置记录主机、远端路径、挂载目录、控制套接字、可选端口和 prelude；agent 集成文件位于 `~/.claude`、`~/.codex`。

## 文档维护

版本以 [`rah`](../rah) 中的 `RAH_VERSION` 为准。README 徽章通过 [Shields 动态正则徽章](https://shields.io/badges/dynamic-regex-badge)读取已发布到 `main` 分支的该字段，请不要在 README 正文或静态版本徽章中再维护一份版本数字。

徽章请求 300 秒缓存，但 Shields 和 GitHub 可能缓存更久；尚未推送的本地修改不会出现在徽章中。本机安装版本以 `rah version` 为准。

用户可见行为改变时，同步更新[英文首页](../README.md)、[中文首页](../README.zh-CN.md)以及对应指南章节。文档描述已经实现的行为，不将讨论中的更新提醒或自动升级写成已提供的功能。
