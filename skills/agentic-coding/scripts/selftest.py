#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""agentic-coding skill 自身的一致性回归。

用法：
    python scripts/selftest.py

覆盖：脚本语法、评测格式、资源引用、frontmatter、章节编号、口径统一、
概念去重、以及 check_spec.py 的正反行为。测试样例写在临时目录，
不改动 skill 内任何文件。

退出码：0 = 全部通过，1 = 存在失败项。
"""
from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

BASE = Path(__file__).resolve().parent.parent
CLI = BASE / "scripts/check_spec.py"
TEMPLATE = BASE / "assets/task-spec.md"
passed: list[str] = []
failed: list[str] = []


def ck(name: str, ok: bool, detail: str = "") -> None:
    (passed if ok else failed).append(name + (f"  [{detail}]" if not ok and detail else ""))


def sentences(text: str) -> set[str]:
    s = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    return {
        p.strip() for p in re.split(r"[。！？\n]", s)
        if len(p.strip()) >= 14 and not p.strip().startswith("|")
    }


GOOD = """# 任务卡

## 目标
为 /api/login 增加基于 IP 的限流并补齐测试。

## 范围
- src/middleware/rate_limit.ts
- tests/test_rate_limit.ts

## 不做的事
- 不改其他路由
- 不引入新依赖

## 上下文入口
- 参考实现：src/middleware/auth.ts
- 构建 / 测试命令：npm test -- --runInBand
- 约定文件：CLAUDE.md

## 验收标准
1. `npm run build` → 退出码 0
2. `npm test -- test_rate_limit` → 全部用例通过
3. 边界行为：单 IP 60 秒内第 6 次请求返回 429

## 权限边界
- 允许：只读、本地文件写入、本地构建与测试命令
- 禁止：git push、部署、访问外部网络
- 需要单独确认的动作：无

## 停止条件
- 同一失败重试上限：3 轮
- 超时 / token 预算：30 分钟
- 超限行为：停止、回滚到最近干净状态、列出已尝试方案与剩余疑点，转人工

---

## 检查点
- 结构性 / 跨模块改动后暂停确认

## 交付要求
- 单个可独立回滚的 diff / PR

## 执行记录
- 遗留疑点：无
"""


def static_checks() -> None:
    for p in BASE.rglob("*.py"):
        try:
            ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
            ck(f"语法 {p.name}", True)
        except SyntaxError as e:
            ck(f"语法 {p.name}", False, str(e))

    evals = json.loads((BASE / "evals/evals.json").read_text(encoding="utf-8"))
    ck("evals.json 归属与条数", evals["skill_name"] == "agentic-coding" and len(evals["evals"]) == 8)
    ck("evals 用例键一致", all(
        set(e) == {"id", "name", "prompt", "expected_behavior", "pressure"} for e in evals["evals"]))
    ck("evals id 连续", [e["id"] for e in evals["evals"]] == list(range(1, 9)))

    missing: list[str] = []
    for f in BASE.rglob("*.md"):
        t = f.read_text(encoding="utf-8")
        for rel in re.findall(r"`((?:references|assets|scripts|evals)/[^`]+?)`", t):
            if not (BASE / rel.split()[0]).exists():
                missing.append(f"{f.name} -> {rel}")
        for target in re.findall(r"\]\(([^)]+)\)", t):
            if target.startswith(("http", "#")):
                continue
            if not (f.parent / target.split("#")[0]).exists():
                missing.append(f"{f.name} -> {target}")
    ck("资源引用全部存在", not missing, "; ".join(missing))

    skill = (BASE / "SKILL.md").read_text(encoding="utf-8-sig")
    fm = re.search(r"^---\s*\n(.*?)\n---\s*\n", skill, re.S | re.M)
    ck("frontmatter 三字段", bool(fm) and all(
        k in fm.group(1) for k in ("name:", "description:", "agent_created: true")))
    ck("description 含负向排除", "不适用于直接执行编码任务本身" in skill)

    old = ["## 核心心智模型", "## 反模式", "## 关键原则", "## Overview",
           "交付单位从", "验证是闭环的硬指标", "基础功（判断输出对错",
           "人工检查点不是倒退", "明确不做的事", "停止条件与重试上限"]
    stale = [m for m in old if m in skill]
    ck("旧概念章节与旧口径已移除", not stale, "; ".join(stale))

    ms = sentences(skill)
    copies = {f.name: len(ms & sentences(f.read_text(encoding="utf-8")))
              for f in sorted((BASE / "references").glob("*.md"))}
    ck("SKILL.md 无整句复制", all(v == 0 for v in copies.values()), str(copies))

    fund = (BASE / "references/fundamentals.md").read_text(encoding="utf-8")
    play = (BASE / "references/playbook.md").read_text(encoding="utf-8")
    rev = (BASE / "references/review-checklist.md").read_text(encoding="utf-8")
    spec = (BASE / "assets/task-spec.md").read_text(encoding="utf-8")
    ck("fundamentals 8 节编号", re.findall(r"^## (\d+)\.", fund, re.M) == [str(i) for i in range(1, 9)])
    ck("playbook 7 节编号", re.findall(r"^## (\d+)\.", play, re.M) == [str(i) for i in range(1, 8)])
    ck("review-checklist 5 节编号", re.findall(r"^## (\d+)\.", rev, re.M) == [str(i) for i in range(1, 6)])
    ck("口径统一：六步模型", "六步模型" in fund and "六步模型" in skill)
    ck("口径统一：七字段命名", "## 不做的事" in spec and "## 停止条件" in spec)
    ck("口径统一：检查点边界已澄清", "不构成对上述类别的整体放行" in play)
    ck("时效内容有复核提示", "时效性快照" in fund)
    ck("输出契约绑定审查记录", "产出第 5 节的审查记录" in rev)


def checker_checks() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="agentic-coding-selftest-"))

    def write(name: str, text: str) -> Path:
        p = tmp / name
        p.write_text(text, encoding="utf-8")
        return p

    def run(*a):
        return subprocess.run([sys.executable, "-B", str(CLI), *map(str, a)],
                              capture_output=True, text=True)

    good = write("good.md", GOOD)
    r = run(good)
    ck("填好的任务卡 PASS", r.returncode == 0, r.stdout + r.stderr)
    ck("--strict 下仍 PASS", run(good, "--strict").returncode == 0)
    r = run(TEMPLATE)
    ck("未填模板被拦截", r.returncode == 1 and "未替换的占位符" in r.stdout, r.stdout)
    r = run(good, "--json")
    try:
        out = json.loads(r.stdout)
        ok = r.returncode == 0 and out[0]["ok"] and len(out[0]["fields_found"]) == 7
    except (ValueError, IndexError, KeyError):
        ok = False
    ck("--json 输出合法", ok, r.stdout)
    r = run(write("missing.md", GOOD.replace("## 不做的事\n- 不改其他路由\n- 不引入新依赖\n\n", "")))
    ck("缺字段被拦截", r.returncode == 1 and "缺少必填字段「不做的事」" in r.stdout, r.stdout)
    vague = write("vague.md", GOOD.replace(
        "1. `npm run build` → 退出码 0\n2. `npm test -- test_rate_limit` → 全部用例通过",
        "1. 代码写得优雅、性能尽量好"))
    r = run(vague)
    ck("模糊词告警且缺命令报错", r.returncode == 1 and "含模糊形容词" in r.stdout
       and "缺少反引号" in r.stdout, r.stdout)
    r = run(write("noban.md", GOOD.replace("- 禁止：git push、部署、访问外部网络\n", "")))
    ck("缺禁止项被拦截", r.returncode == 1 and "禁止" in r.stdout, r.stdout)
    r = run(write("noretry.md", GOOD.replace("- 同一失败重试上限：3 轮", "- 看情况停止")))
    ck("缺重试上限被拦截", r.returncode == 1 and "重试上限" in r.stdout, r.stdout)
    warn = write("warn.md", GOOD.replace("- 遗留疑点：无\n", ""))
    r = run(warn)
    ck("附属区块为空仅告警", r.returncode == 0 and "附属区块「执行记录」" in r.stdout, r.stdout)
    ck("--strict 使告警变失败", run(warn, "--strict").returncode == 1)
    ck("文件不存在返回 2", run(tmp / "nope.md").returncode == 2)
    r = run("--strict", good, warn)
    ck("多文件 + --strict 组合", r.returncode == 1
       and r.stdout.count("PASS") == 1 and r.stdout.count("FAIL") == 1, r.stdout)


def main() -> int:
    static_checks()
    checker_checks()
    print(f"PASS: {len(passed)} checks, FAIL: {len(failed)}")
    for name in passed:
        print("  -", name)
    for name in failed:
        print("  x", name)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
