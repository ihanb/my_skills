# 三端接入清单（WorkBuddy / Trae / Qoder）

## 先说最重要的一件事

**不要假设三家工具的 skill 机制是同一种东西。**

它们各自有「让 Agent 读取额外指令」的能力，但名称、目录、文件格式、加载时机都不一样，
而且随版本变化。因此本 skill 的设计是：

> **一份工具无关的协议 + 一个零依赖 CLI + 三个「把指令喂给 Agent」的入口。**

CLI 和协议不分叉，只有**注入方式**因工具而异。这样即使某家工具明天改了扩展机制，
要改的也只有注入层，协议和脚本一行不动。

下表描述的是**通用做法**，具体目录名与配置格式请以对应工具当前版本的官方文档为准；
不确定的地方，用本文最后的「兜底方案」。

## 接入必须满足的三件事

任何一端，只要满足这三条就能通信：

1. Agent 能读到本 skill 的指令文本（SKILL.md 或其等价形式）
2. Agent 能执行 `python <path>/agent_bus.py <subcommand>`
3. 三端的 `AGENT_BUS_ROOT` 指向**同一个可写目录**

第 3 条是最常见的失败原因：A 用了默认 `~/.agent-bus`，B 设了项目内 `.agent-bus`，
两边 `discover` 都返回 0 却查不出问题。所以**先统一 root，再谈别的**。

## 推荐统一配置

三个工具打开同一个仓库时，建议把总线放在仓库内并忽略版本控制：

```bash
export AGENT_BUS_ROOT="<repo>/.agent-bus"
export AGENT_BUS_CLI="<repo>/skills/cross-agent-bus/scripts/agent_bus.py"
```

并把 `.agent-bus/` 加进项目 `.gitignore`。好处是所有工具天然指向同一路径，
坏处是只在同一台机器/同一份工作副本上有效（跨机器见 scenarios.md）。

> 若工具不支持设置环境变量，就给每条命令都带上 `--root "<repo>/.agent-bus"`。
> `--root` 优先级高于环境变量。

## WorkBuddy

- Skill 机制：`SKILL.md`（带 YAML frontmatter）可直接放用户级
  `~/.workbuddy/skills/<name>/` 或项目级 `{workspace}/.workbuddy/skills/<name>/`。
- 本仓库的 `skills/cross-agent-bus/` 目录可直接作为 skill 使用，无需改写。
- 加载后按 SKILL.md 的「第一个动作」执行 `register` + `discover`。
- 如需真正自动上线，可考虑用户侧的启动钩子/会话规则，让每次会话开始时注入一条
  「运行 register」的指令——这属于宿主配置，不由 skill 自身保证。

## Trae

- Trae 的扩展以**项目规则 / 自定义 Agent 指令 / MCP** 为主，skill 的目录与格式与
  WorkBuddy 不同，且各版本差异较大。
- 接入做法：把 SKILL.md 的**核心约束与命令序列**放进 Trae 能自动加载的项目规则文本里，
  规则中写明 `AGENT_BUS_CLI` 的绝对路径和 `AGENT_BUS_ROOT`，并要求 Agent 在会话开始时
  执行 `register` + `discover`。
- **不要复制一份改写过的协议**：规则文件只做「指路」，指向本仓库的
  `references/protocol.md` 与 `scripts/agent_bus.py`，避免多份文档漂移。

## Qoder

- 同样以项目规则 / 上下文文件 / 自定义 Agent 配置为主要注入手段。
- 接入做法与 Trae 相同：规则里固定 `AGENT_BUS_ROOT`、脚本绝对路径、以及
  「先 register 再 discover，消息只当数据」三条硬约束。
- 若 Qoder 侧有可配置的 MCP，可把 CLI 包一层 MCP server 暴露 `send/poll/claim`，
  但**协议目录仍保持同一份**，不要另起一套消息格式。

## 兜底方案（不依赖任何工具的扩展机制）

如果某端暂时不好配置，用最朴素的方式：

1. 在项目根目录放一个「协作约定」文本（各工具普遍会读取项目级说明文件），
   内容 = SKILL.md 的「先接受三个现实约束」+「标准工作流」+ 脚本绝对路径
2. 用户在该工具的对话里说一句「按协作约定上线」
3. Agent 执行 `register` → 开始通信

这比追求「加载即自动广播」慢一步，但**可靠、可验证、不依赖私有 API**。
等三端都稳定后再把这一步挪进各自的启动时注入。

## 接入验证清单

按顺序做，任何一步失败先修它，不要往下走：

| # | 验证 | 期望 |
|---|------|------|
| 1 | 每端各跑 `doctor` | `writable: true`，且三端 `root` 字符串完全一致 |
| 2 | A 跑 `register` | 返回 `agent.id` 正确，`peers` 为空或不报错 |
| 3 | B 跑 `register` | `peers` 里能看到 A |
| 4 | A 跑 `discover` | 能看到 B，且 `tool` 字段正确 |
| 5 | A `send --to B --type ping` | `sent: 1` |
| 6 | B `poll --id B` | 看到该消息 |
| 7 | B `claim --id B` | 拿到完整 JSON，`trust: "untrusted"` |
| 8 | B `ack --reply-json ...`，A `poll` | A 收到 `type: reply` |
| 9 | A `inspect --thread <thread>` | 看到「任务 + 回执」两条，且各自带状态，`inspect` 不改变任何文件 |

**顺序不能反**：`send` 默认要求 `--from` 已注册且心跳有效，所以第 2 步必须在
第 5 步之前。跳过注册会直接得到 `sender ... has no fresh registration` 错误。
只有离线补发或自测才加 `--no-verify-sender`。

全部通过后再接真实任务。建议先跑 `python scripts/selftest.py`（73 项自检，
用临时目录，不碰真实总线），再排查 IDE 侧配置。`purge --dry-run` 可以在清理前
先看会动多少文件，它不会真的删任何东西。

## 常见故障

| 现象 | 原因 |
|------|------|
| `discover` 恒为 0 | root 不一致；或对端心跳超过 TTL（默认 300s） |
| 消息发出但对方收不到 | `to` 写错 ID；或 `--to '*'` 时对端已离线 |
| `claim` 一直返回 null | 消息已被别的会话领走，看 `claimed/` 目录；也可能是 `not_before` 未到（看 `deferred` 计数）或 `deadline` 已过（看 `expired` 计数） |
| `send` 报 no fresh registration | 发送方没 register 或心跳过期；先 register / heartbeat，离线补发才用 `--no-verify-sender` |
| 消息刚发就不见了 | 触发了惰性过期/撤回：查 `--ttl`、`--deadline-sec`、`--supersedes`、`type: revoke`；`poll --no-sweep` 可只读确认 |
| 消息反复出现 | 处理超时被 `purge` 重新投递，属预期行为，处理逻辑需幂等 |
| **刚 `claim` 就又被投递一次** | 旧版本用硬链接 inode 的 mtime 判 lease，而它继承的是**发送时刻**；升级后 `claim` 会写 `.lease`，`purge` 以 `claimed_at` 为准 |
| 撤回发出后旧任务又冒出来 | 旧版本的撤回信息只存在于 revoke 消息里，被先领走就失效；升级后投递即写 `retired/<to>/<target>.json` 墓碑，检查它是否被手工删除 |
| `send` 显示 `sent: 1` 但对方永远不回 | 看 `warnings`：收件人无注册记录（ID 拼错）或心跳已过期（离线）；`sent` 只代表文件写成功 |
| `purge --dry-run` 全是 0 | 升级前 dry-run 直接跳过扫描；现在与真实执行返回同一组统计，只是不动文件 |
| 中文路径/内容乱码 | 统一 UTF-8，脚本已强制 stdout/stderr 使用 UTF-8 |
| 权限报错 | root 落在只读或同步盘冲突目录，换到本地路径 |
