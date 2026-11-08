---
name: agentic-coding
description: 智能体编程（agentic coding / coding agent）的任务委派、规格编写与结果验收规范。用于解释或辨析 agentic coding 概念、为编程智能体编写任务规格与机器可判定的验收标准、审查 AI 生成的 diff 或 PR、设计 agentic 开发工作流。This skill should be used when explaining agentic coding, drafting task specs with verifiable acceptance criteria for coding agents, reviewing AI-generated diffs, or designing agentic development workflows. 不适用于直接执行编码任务本身。
agent_created: true
---

# Agentic Coding

## 定位

把编码任务以「规格 → 委派 → 验证 → 审查」的闭环交给 agent。本文件只承载**路由、红线与输出契约**；概念、流程细节与清单由 `references/` 承载，此处不复制。

## 唯一事实源

| 主题 | 权威位置 | 其他文件的角色 |
| --- | --- | --- |
| 概念定义、核心循环、术语、固有局限 | `references/fundamentals.md` | 只引用，不另写一套循环模型或术语表 |
| 委派流程、七字段定义、检查点、失败模式、按栈验收命令 | `references/playbook.md` | 本文件只给动作红线与骨架，细节与理由以此为准 |
| 审查顺序、清单、风险分级、记录模板 | `references/review-checklist.md` | 审查按此执行并产出记录 |
| 任务卡模板 | `assets/task-spec.md` | 复制后填写，不手写临时格式 |
| 任务卡机械校验 | `scripts/check_spec.py` | 填完必须运行 |
| skill 自身一致性回归 | `scripts/selftest.py` | 改动本 skill 的文档或脚本后必须运行 |

术语与模型强制统一：**核心循环采用 `fundamentals.md` 第 3 节的六步模型**（Goal → Plan → Execution → Reflection/verification → Iteration → Output），不另称「四阶段」；**任务卡采用 `playbook.md` 第 2 节的七字段命名**（目标、范围、不做的事、上下文入口、验收标准、权限边界、停止条件），不另造别名。

## 按意图路由（含输出契约）

| 意图 | 读取位置 | 必须产出 |
| --- | --- | --- |
| 解释概念、培训、写技术材料 | `fundamentals.md` 第 1、3、4 节 | 结构化说明；指明「可验证反馈」是区分 agentic 与多轮聊天的硬指标 |
| 辨析术语（vibe coding / agentic AI / spec-driven） | `fundamentals.md` 第 7 节术语表 | 以该表为准的对照说明，不自造定义 |
| 委派编码任务 / 写任务卡 | `playbook.md` 第 1–3、6 节；复制 `assets/task-spec.md` | 填全七字段与附属区块的任务卡；验收标准写成「命令 + 期望输出」；运行 `check_spec.py` 直至 PASS |
| 审查 agent 产出的 diff / PR | `review-checklist.md` 全文 | 按第 1 节的 1–5 步逐项核对，产出第 5 节的**审查记录模板**，含结论（合并 / 打回 / 转人工）与规格偏差回写 |
| 设计工作流、选型、团队落地 | `playbook.md` 第 5、7 节 | 分阶段落地建议与度量口径 |
| 任务失败、返工、越界 | `playbook.md` 第 4 节 + `review-checklist.md`「打回信号」 | 失败模式归因与打回 / 转人工结论 |

**不适用**：直接实现功能、修复 bug、编写业务代码等任务本身——这些是委派的对象，不是本技能的触发条件。

## 红线（不可协商）

1. 委派前确认任务同时满足**可验证、边界清晰、可回滚**；任一不满足，先改造任务而不是委派。
2. 验收标准必须是机器可判定的命令 + 期望输出；出现「合理」「优雅」「尽量」等形容词即打回重写。
3. 含不可逆外部副作用（push、部署、发消息、付款、删数据、强制推送、生产变更）的任务**不整体委派**；确需涉及时只拆出调研 / 起草子步骤，且每个外部动作单独取得用户授权。
4. 结构性 / 跨模块改动后、安装依赖或改构建配置前、不可逆命令前、连续两轮验证失败后，必须暂停等待确认。
5. 同一失败重试上限 3 轮；超限即停止、回滚到最近干净状态、列出已尝试方案与剩余疑点，转人工。
6. 审查先读 diff 范围与验收证据，最后才读 agent 的说明文字；「测试通过」不等于「正确」。
7. 不得让同一个 agent 既写实现又写测试并自行宣布通过；关键路径需人给或独立设计的用例。
8. agent 产出不得绕开用户确认直接合并、推送或部署。

## 委派流程骨架

判定适配性 → 复制并填写任务卡（七字段）→ 按本栈选验收命令 → 运行 `check_spec.py` 校验 PASS → 设检查点 → 单任务单 diff 执行并在 3 轮内迭代 → 按 `review-checklist.md` 审查并产出记录 → 把规格偏差回写到模板或项目约定。

完整流程、字段释义、检查点设计、失败模式与缓解见 `playbook.md` 第 1–4 节，此处不复制。

## 资源

- `references/fundamentals.md` — 概念定义与传统辅助编码对比、六步核心循环、四个前提、术语辨析、工具形态与固有局限（**概念唯一事实源**）。
- `references/playbook.md` — 适配性判定、七字段释义、检查点、失败模式、上下文管理、按技术栈的验收命令、团队落地（**流程唯一事实源**）。
- `references/review-checklist.md` — 审查顺序、清单、风险分级、打回信号、审查记录模板（**审查唯一事实源**）。
- `assets/task-spec.md` — 可复制的任务卡模板。
- `scripts/check_spec.py` — 任务卡静态校验器，零依赖；填完任务卡必须运行。
- `scripts/selftest.py` — skill 自身一致性回归（引用、章节号、口径、评测格式、校验器正反行为），改动后运行。
- `evals/evals.json` — 正向 / 边界 / 压力评测用例。
