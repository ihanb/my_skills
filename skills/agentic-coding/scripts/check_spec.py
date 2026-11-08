#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""agentic-coding 任务卡静态校验器。

用法：
    python scripts/check_spec.py task.md
    python scripts/check_spec.py task.md --strict
    python scripts/check_spec.py task.md other.md --json

校验七字段齐全、占位符已替换、验收标准含可执行命令与期望输出、
权限边界保留非空禁止项、停止条件写明重试上限；对模糊形容词与
附属区块缺失告警。只做可机械判定的检查，人工判断项见
references/review-checklist.md。

退出码：0 = PASS，1 = 存在 ERROR（--strict 下 WARN 也算失败），2 = 参数 / 读取错误。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:  # Windows 终端编码保护
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

REQUIRED = ["目标", "范围", "不做的事", "上下文入口", "验收标准", "权限边界", "停止条件"]
OPTIONAL = ["检查点", "交付要求", "执行记录"]
VAGUE_WORDS = ("合理", "优雅", "尽量", "适当", "尽可能", "差不多", "看着办")
PLACEHOLDER = re.compile(r"\{\{.*?\}\}")
HEADING = re.compile(r"^##\s+(.+?)\s*$")


def strip_comments(text: str) -> str:
    """移除 HTML 注释（支持跨行块），保留注释外的同行内容。"""
    out: list[str] = []
    in_comment = False
    for line in text.splitlines():
        buf, rest = "", line
        while rest:
            if in_comment:
                if "-->" in rest:
                    rest = rest.split("-->", 1)[1]
                    in_comment = False
                else:
                    rest = ""
            elif "<!--" in rest:
                before, _, rest = rest.partition("<!--")
                buf += before
                in_comment = True
            else:
                buf += rest
                rest = ""
        if buf.strip():
            out.append(buf)
    return "\n".join(out)


def split_sections(text: str) -> dict[str, list[str]]:
    """按二级标题切分；一级标题与三级标题不参与。"""
    result: dict[str, list[str]] = {}
    current: str | None = None
    buf: list[str] = []
    for line in text.splitlines():
        m = HEADING.match(line)
        if m:
            if current is not None:
                result[current] = buf
            current, buf = m.group(1).strip(), []
        elif current is not None:
            buf.append(line)
    if current is not None:
        result[current] = buf
    return result


def meaningful(lines: list[str]) -> list[str]:
    """过滤空行、分隔线、纯列表符号等无信息行。"""
    out = []
    for line in lines:
        s = line.strip()
        if not s or s in ("---", "***", "___"):
            continue
        if re.fullmatch(r"[-*+>`\s]+", s):
            continue
        out.append(s)
    return out


def check(path: Path, strict: bool) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    text = strip_comments(path.read_text(encoding="utf-8-sig"))
    sec = split_sections(text)

    for name in REQUIRED:
        if name not in sec:
            errors.append(f"缺少必填字段「{name}」")
            continue
        lines = meaningful(sec[name])
        if not lines:
            errors.append(f"必填字段「{name}」为空")
            continue
        if any(PLACEHOLDER.search(l) for l in lines):
            errors.append(f"必填字段「{name}」仍有未替换的占位符")
        if any(w in l for l in lines for w in VAGUE_WORDS):
            warnings.append(f"字段「{name}」含模糊形容词，无法机器判定")

    if "验收标准" in sec:
        lines = meaningful(sec["验收标准"])
        cmds = [c for l in lines for c in re.findall(r"`([^`]+)`", l)
                if not PLACEHOLDER.search(c)]
        if not cmds:
            errors.append("验收标准缺少反引号包裹的可执行命令")
        if not any(("→" in l or "期望" in l or "通过" in l) for l in lines):
            warnings.append("验收标准未写明期望输出")

    if "权限边界" in sec:
        lines = meaningful(sec["权限边界"])
        has_ban = any(
            "禁止" in l and l.split("禁止", 1)[1].strip("：: -") for l in lines
        )
        if not has_ban:
            errors.append("权限边界缺少非空的「禁止」项")

    if "停止条件" in sec:
        lines = meaningful(sec["停止条件"])
        if not re.search(r"重试[^\n]*\d|\d+\s*轮|上限[^\n]*\d", "\n".join(lines)):
            errors.append("停止条件未写明重试上限（例如 3 轮）")

    for name in OPTIONAL:
        if name not in sec:
            warnings.append(f"缺少附属区块「{name}」（不计入七字段，但审查与复盘需要）")
        elif not meaningful(sec[name]):
            warnings.append(f"附属区块「{name}」为空（不计入七字段，但审查与复盘需要）")

    ok = not errors and (not strict or not warnings)
    return {
        "file": str(path),
        "ok": ok,
        "errors": errors,
        "warnings": warnings,
        "fields_found": [n for n in REQUIRED if n in sec],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="校验 agentic-coding 任务卡")
    ap.add_argument("files", nargs="+", help="任务卡 Markdown 路径")
    ap.add_argument("--strict", action="store_true", help="WARN 也视为失败")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()

    results: list[dict] = []
    io_error = False
    for f in args.files:
        p = Path(f)
        if not p.is_file():
            print(f"ERROR {p}: 文件不存在或不是普通文件", file=sys.stderr)
            io_error = True
            continue
        try:
            results.append(check(p, args.strict))
        except (OSError, UnicodeError) as e:
            print(f"ERROR {p}: 读取失败 {e}", file=sys.stderr)
            io_error = True

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for r in results:
            for e in r["errors"]:
                print(f"ERROR {r['file']}: {e}")
            for w in r["warnings"]:
                print(f"WARN  {r['file']}: {w}")
            status = "PASS" if r["ok"] else "FAIL"
            print(f"{status} {r['file']}  fields={len(r['fields_found'])}/7  "
                  f"errors={len(r['errors'])}  warnings={len(r['warnings'])}")

    if io_error and not results:
        return 2
    return 0 if all(r["ok"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
