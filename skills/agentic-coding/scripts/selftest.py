#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""agentic-coding skill 自身的一致性回归。

用法（在 skill 根目录执行）：
    python scripts/selftest.py

覆盖：脚本语法、评测格式、资源引用、**章节引用可达性**、frontmatter、
章节编号连续性、口径统一、概念去重，以及 check_spec.py 的正反行为。
测试样例写在临时目录，不改动 skill 内任何文件。

与「快照断言」不同：本回归不锁死评测条数或章节总数，只校验关系是否成立，
因此新增评测用例或章节不会误报，而引用指错章节会被拦截。

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
TASK_TEMPLATE = BASE / "assets/task-spec.md"
REVIEW_TEMPLATE = BASE / "assets/review-record.md"
SECTION_REF = re.compile(r"第\s*([0-9\s、,，–\-—~至]+?)节")
FILE_TOKEN = re.compile(r"(?:references|assets)/[A-Za-z0-9._-]+\.md")
HEADING_NUM = re.compile(r"^##\s+(\d+)\.\s*(.+)$", re.M)
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


def expand_refs(raw: str) -> set[int]:
    """把「1–3、6」展开成 {1,2,3,6}。"""
    nums: set[int] = set()
    spans = list(re.finditer(r"(\d+)\s*[–\-—~至]\s*(\d+)", raw))
    for m in spans:
        nums.update(range(int(m.group(1)), int(m.group(2)) + 1))
    rest = re.sub(r"\d+\s*[–\-—~至]\s*\d+", "", raw)
    nums.update(int(x) for x in re.findall(r"\d+", rest))
    return nums


def nearest_file(line: str, pos: int) -> str | None:
    """章节引用左侧最近的资源文件名；同行仅一个文件时兜底。"""
    before = list(FILE_TOKEN.finditer(line[:pos]))
    if before:
        return before[-1].group(0)
    all_hits = list(FILE_TOKEN.finditer(line))
    if len(all_hits) == 1:
        return all_hits[0].group(0)
    return None


def section_integrity() -> tuple[int, list[str], list[str]]:
    """校验所有「第 N 节」引用确实指向存在的章节，返回 (已校验引用数, 断链, 未归属)。"""
    documents = [BASE / "SKILL.md", BASE / "evals/evals.json",
                 *sorted((BASE / "assets").glob("*.md")),
                 *sorted((BASE / "references").glob("*.md"))]
    sections: dict[str, set[int]] = {}
    for f in (BASE / "references").glob("*.md"):
        sections[f"references/{f.name}"] = {
            int(n) for n, _ in HEADING_NUM.findall(f.read_text(encoding="utf-8"))
        }

    broken: list[str] = []
    unresolved: list[str] = []
    verified = 0
    for doc in documents:
        self_key = f"references/{doc.name}" if doc.parent.name == "references" else None
        for lineno, line in enumerate(doc.read_text(encoding="utf-8").splitlines(), 1):
            for m in SECTION_REF.finditer(line):
                nums = expand_refs(m.group(1))
                if not nums:
                    continue
                target = nearest_file(line, m.start()) or self_key
                if target is None:
                    unresolved.append(f"{doc.name}:{lineno} 第{m.group(1).strip()}节")
                    continue
                if target not in sections:
                    # 指向 assets/SKILL.md 等无编号章节的文件时，不做编号校验
                    continue
                for n in sorted(nums):
                    verified += 1
                    if n not in sections[target]:
                        broken.append(f"{doc.name}:{lineno} -> {target} 第 {n} 节不存在")
    return verified, broken, unresolved


GOOD_TASK = """# 任务卡

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
3. `npm test -- test_rate_limit_429` → 单 IP 第 6 次请求返回 429 的用例通过

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

GOOD_REVIEW = """# 审查记录

## 任务卡
TASK-123

## 改动范围
- src/middleware/rate_limit.ts
- tests/test_rate_limit.ts

## 验收命令与结果
- `npm run build` → 通过
- `npm test -- test_rate_limit` → 全部用例通过

## 发现的问题
- 无

## 结论
合并

## 风险级别
中

## 规格偏差回写
否
"""


def static_checks() -> None:
    for p in BASE.rglob("*.py"):
        try:
            ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
            ck(f"语法 {p.name}", True)
        except SyntaxError as e:
            ck(f"语法 {p.name}", False, str(e))

    evals = json.loads((BASE / "evals/evals.json").read_text(encoding="utf-8"))
    items = evals["evals"]
    ids = [e["id"] for e in items]
    ck("evals.json 归属且非空", evals["skill_name"] == "agentic-coding" and len(items) >= 1)
    ck("evals 用例键一致", all(
        set(e) == {"id", "name", "prompt", "expected_behavior", "pressure"} for e in items))
    ck("evals id 唯一且递增", len(set(ids)) == len(ids) and ids == sorted(ids))
    ck("evals 内容非空", all(len(e["prompt"]) >= 10 and len(e["expected_behavior"]) >= 20
                       for e in items))

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

    # 章节引用可达性：本轮核心新增项
    verified, broken, unresolved = section_integrity()
    ck("章节引用可达", not broken, "; ".join(broken))
    ck("章节引用校验未空转", verified >= 20, f"verified={verified}")
    ck("章节引用均可归属", not unresolved, "; ".join(unresolved[:6]))

    skill = (BASE / "SKILL.md").read_text(encoding="utf-8-sig")
    fm = re.search(r"^---\s*\n(.*?)\n---\s*\n", skill, re.S | re.M)
    ck("frontmatter 三字段", bool(fm) and all(
        k in fm.group(1) for k in ("name:", "description:", "agent_created: true")))
    ck("description 中文负向排除", "不适用于直接执行编码任务本身" in skill)
    ck("description 英文负向排除", "Not for performing the coding task itself" in skill)
    ck("脚本定位说明存在", "<SKILL_ROOT>" in skill and "## 脚本定位" in skill)

    old = ["## 核心心智模型", "## 反模式", "## 关键原则", "## Overview",
           "交付单位从", "验证是闭环的硬指标", "基础功（判断输出对错",
           "人工检查点不是倒退", "明确不做的事", "停止条件与重试上限"]
    stale = [m for m in old if m in skill]
    ck("旧概念章节与旧口径已移除", not stale, "; ".join(stale))

    ms = sentences(skill)
    copies = {f.name: len(ms & sentences(f.read_text(encoding="utf-8")))
              for f in sorted((BASE / "references").glob("*.md"))}
    ck("SKILL.md 无整句复制", all(v == 0 for v in copies.values()), str(copies))

    # 章节编号只要求「从 1 连续」，不锁死总数
    for f in sorted((BASE / "references").glob("*.md")):
        nums = [int(n) for n, _ in HEADING_NUM.findall(f.read_text(encoding="utf-8"))]
        ck(f"{f.name} 章节编号连续", nums == list(range(1, len(nums) + 1)), str(nums))

    fund = (BASE / "references/fundamentals.md").read_text(encoding="utf-8")
    play = (BASE / "references/playbook.md").read_text(encoding="utf-8")
    rev = (BASE / "references/review-checklist.md").read_text(encoding="utf-8")
    spec = (BASE / "assets/task-spec.md").read_text(encoding="utf-8")
    record = REVIEW_TEMPLATE.read_text(encoding="utf-8")
    ck("口径统一：六步模型", "六步模型" in fund and "六步模型" in skill)
    ck("口径统一：七字段命名", "## 不做的事" in spec and "## 停止条件" in spec)
    ck("口径统一：检查点边界已澄清", "不构成对上述类别的整体放行" in play)
    ck("时效内容有复核提示", "时效性快照" in fund)
    ck("审查记录七项齐全", all(f"## {n}" in record for n in
                        ("任务卡", "改动范围", "验收命令与结果", "发现的问题",
                         "结论", "风险级别", "规格偏差回写")))
    ck("审查格式指向唯一模板", "assets/review-record.md" in rev and "```" not in rev)
    ck("输出契约绑定两类校验", "--kind review" in skill and "--kind review" in play
       and "--kind review" in rev)
    ck("红线覆盖落盘产出", "必须落盘的产出物" in skill)


def checker_checks() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="agentic-coding-selftest-"))

    def write(name: str, text: str) -> Path:
        p = tmp / name
        p.write_text(text, encoding="utf-8")
        return p

    def run(*a):
        return subprocess.run([sys.executable, "-B", str(CLI), *map(str, a)],
                              capture_output=True, text=True)

    # ---- 任务卡 ----
    good = write("good.md", GOOD_TASK)
    ck("填好的任务卡 PASS", run(good).returncode == 0)
    ck("--strict 下任务卡仍 PASS", run(good, "--strict").returncode == 0)
    r = run(TASK_TEMPLATE)
    ck("未填任务卡模板被拦截", r.returncode == 1 and "未替换的占位符" in r.stdout, r.stdout)
    r = run(good, "--json")
    try:
        out = json.loads(r.stdout)
        ok = r.returncode == 0 and out[0]["ok"] and out[0]["kind"] == "task" \
             and out[0]["fields_total"] == 7
    except (ValueError, IndexError, KeyError):
        ok = False
    ck("--json 输出合法且带 kind", ok, r.stdout)
    r = run(write("missing.md", GOOD_TASK.replace(
        "## 不做的事\n- 不改其他路由\n- 不引入新依赖\n\n", "")))
    ck("任务卡缺字段被拦截", r.returncode == 1 and "缺少必填字段「不做的事」" in r.stdout, r.stdout)
    r = run(write("vague.md", GOOD_TASK.replace(
        "1. `npm run build` → 退出码 0\n2. `npm test -- test_rate_limit` → 全部用例通过\n"
        "3. `npm test -- test_rate_limit_429` → 单 IP 第 6 次请求返回 429 的用例通过",
        "1. 代码写得优雅、性能尽量好")))
    ck("模糊词 ERROR 且缺命令 ERROR", r.returncode == 1
       and "含模糊形容词" in r.stdout and "缺少反引号" in r.stdout, r.stdout)
    r = run(write("noban.md", GOOD_TASK.replace("- 禁止：git push、部署、访问外部网络\n", "")))
    ck("任务卡缺禁止项被拦截", r.returncode == 1 and "禁止" in r.stdout, r.stdout)
    r = run(write("noretry.md", GOOD_TASK.replace("- 同一失败重试上限：3 轮", "- 看情况停止")))
    ck("任务卡缺重试上限被拦截", r.returncode == 1 and "重试上限" in r.stdout, r.stdout)
    warn = write("warn.md", GOOD_TASK.replace("- 遗留疑点：无\n", ""))
    r = run(warn)
    ck("附属区块为空仅告警", r.returncode == 0 and "附属区块「执行记录」" in r.stdout, r.stdout)
    ck("--strict 使告警变失败", run(warn, "--strict").returncode == 1)

    # ---- 本轮新增：校验精度回归 ----
    r = run(write("split.md", GOOD_TASK.replace(
        "1. `npm run build` → 退出码 0\n2. `npm test -- test_rate_limit` → 全部用例通过",
        "1. `npm run build`\n2. 期望输出写在这里，与命令不同行")))
    ck("命令与期望分离被拦截", r.returncode == 1 and "同一行" in r.stdout, r.stdout)
    r = run(write("banNone.md", GOOD_TASK.replace(
        "- 禁止：git push、部署、访问外部网络", "- 禁止：无")))
    ck("禁止项写「无」被拦截", r.returncode == 1 and "禁止" in r.stdout, r.stdout)
    r = run(write("vagueElsewhere.md", GOOD_TASK.replace("- 不改其他路由", "- 不引入不合理的依赖")))
    ck("非验收字段不再误报模糊词", r.returncode == 0 and "含模糊形容词" not in r.stdout, r.stdout)
    r = run(write("mixedVague.md", GOOD_TASK.replace(
        "3. `npm test -- test_rate_limit_429` → 单 IP 第 6 次请求返回 429 的用例通过",
        "3. 边界行为：响应尽量快，看着办")))
    ck("保留命令也不能混入形容词", r.returncode == 1 and "含模糊形容词" in r.stdout, r.stdout)
    r = run(write("textOnly.md", GOOD_TASK.replace(
        "3. `npm test -- test_rate_limit_429` → 单 IP 第 6 次请求返回 429 的用例通过",
        "3. 边界行为：单 IP 第 6 次请求返回 429")))
    ck("纯文字验收条目被拦截", r.returncode == 1 and "缺少反引号" in r.stdout, r.stdout)

    # ---- 审查记录 ----
    review = write("review.md", GOOD_REVIEW)
    r = run(review, "--kind", "review")
    ck("填好的审查记录 PASS", r.returncode == 0, r.stdout)
    ck("审查记录 --strict 仍 PASS", run(review, "--kind", "review", "--strict").returncode == 0)
    r = run(REVIEW_TEMPLATE, "--kind", "review")
    ck("未填审查记录模板被拦截", r.returncode == 1 and "未替换的占位符" in r.stdout, r.stdout)
    r = run(review, "--kind", "review", "--json")
    try:
        out = json.loads(r.stdout)
        ok = out[0]["ok"] and out[0]["kind"] == "review" and out[0]["fields_total"] == 7
    except (ValueError, IndexError, KeyError):
        ok = False
    ck("审查记录 --json 带 kind 与 7 项", ok, r.stdout)
    r = run(write("reviewMissing.md", GOOD_REVIEW.replace(
        "## 规格偏差回写\n否\n", "")), "--kind", "review")
    ck("审查记录缺项被拦截", r.returncode == 1 and "缺少必填字段「规格偏差回写」" in r.stdout,
       r.stdout)
    r = run(write("reviewVerdict.md", GOOD_REVIEW.replace("## 结论\n合并", "## 结论\n看着办")),
            "--kind", "review")
    ck("非法结论被拦截", r.returncode == 1 and "结论必须是" in r.stdout, r.stdout)
    r = run(write("reviewRisk.md", GOOD_REVIEW.replace("## 风险级别\n中", "## 风险级别\n未知")),
            "--kind", "review")
    ck("非法风险级别被拦截", r.returncode == 1 and "风险级别必须是" in r.stdout, r.stdout)
    ck("任务卡不会被 review 规则误判", run(good, "--kind", "review").returncode == 1)

    # ---- 通用行为 ----
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
