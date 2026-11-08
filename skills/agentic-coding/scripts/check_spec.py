#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""agentic-coding 任务卡 / 审查记录静态校验器。

用法（在 skill 根目录执行，或用脚本绝对路径）：
    python scripts/check_spec.py task.md
    python scripts/check_spec.py task.md --strict
    python scripts/check_spec.py review.md --kind review
    python scripts/check_spec.py task.md other.md --json

任务卡（--kind task，默认）校验七字段齐全、占位符已替换、
验收标准每条都是「命令 + 同行期望输出」、禁止项与重试上限非空；
审查记录（--kind review）校验七项齐全、结论与风险级别取值合法。
只做可机械判定的检查，人工判断项见 references/review-checklist.md。

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

TASK_REQUIRED = ["目标", "范围", "不做的事", "上下文入口", "验收标准", "权限边界", "停止条件"]
TASK_OPTIONAL = ["检查点", "交付要求", "执行记录"]
REVIEW_REQUIRED = ["任务卡", "改动范围", "验收命令与结果", "发现的问题", "结论", "风险级别", "规格偏差回写"]
REVIEW_CONCLUSIONS = ("合并", "打回", "转人工")
REVIEW_RISKS = ("低", "中", "高")
VAGUE_WORDS = ("合理", "优雅", "尽量", "适当", "尽可能", "差不多", "看着办", "符合预期", "无明显问题")
EMPTY_VALUES = {"", "无", "none", "n/a", "null", "暂无", "-", "—", "/", "待填"}
EXPECTED_MARKERS = ("→", "期望", "通过", "退出码", "返回码", "全绿", "失败", "无报错")
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


def value_of(lines: list[str], key: str) -> str:
    """取「key：value」形式的冒号后内容，兼容全角 / 半角冒号。"""
    for l in lines:
        if key in l:
            m = re.split(r"[：:]", l, maxsplit=1)
            if len(m) == 2:
                return m[1].strip()
    return ""


def is_empty_value(v: str) -> bool:
    return v.strip(" 。.、,，;；()（）").lower() in EMPTY_VALUES


def check_common(sec: dict[str, list[str]], required: list[str],
                 errors: list[str], warnings: list[str]) -> None:
    """两类产出物共用的必填字段检查。"""
    for name in required:
        if name not in sec:
            errors.append(f"缺少必填字段「{name}」")
            continue
        lines = meaningful(sec[name])
        if not lines:
            errors.append(f"必填字段「{name}」为空")
            continue
        if any(PLACEHOLDER.search(l) for l in lines):
            errors.append(f"必填字段「{name}」仍有未替换的占位符")
        if "目标" == name and any(w in l for l in lines for w in VAGUE_WORDS):
            warnings.append("字段「目标」含模糊形容词，无法机器判定")


def check_task(sec: dict[str, list[str]], errors: list[str], warnings: list[str]) -> None:
    check_common(sec, TASK_REQUIRED, errors, warnings)

    if "验收标准" in sec:
        lines = meaningful(sec["验收标准"])
        vague = [w for l in lines for w in VAGUE_WORDS if w in l]
        if vague:
            errors.append(f"验收标准含模糊形容词（{ '、'.join(sorted(set(vague))) }），无法机器判定")
        for l in lines:
            cmds = [c for c in re.findall(r"`([^`]+)`", l) if not PLACEHOLDER.search(c)]
            if not cmds:
                errors.append(f"验收标准条目缺少反引号包裹的可执行命令：{l[:40]}")
            elif not any(k in l for k in EXPECTED_MARKERS):
                errors.append("验收标准的命令未写明期望输出（必须与命令写在同一行）")

    if "权限边界" in sec:
        lines = meaningful(sec["权限边界"])
        bans = [l.split("禁止", 1)[1].strip("：: -—*")
                for l in lines if "禁止" in l]
        if not any(b and not is_empty_value(b) and not PLACEHOLDER.search(b) for b in bans):
            errors.append("权限边界缺少非空且有实质内容的「禁止」项")

    if "停止条件" in sec:
        lines = meaningful(sec["停止条件"])
        if not re.search(r"重试[^\n]*\d|\d+\s*轮|上限[^\n]*\d", "\n".join(lines)):
            errors.append("停止条件未写明重试上限（例如 3 轮）")

    for name in TASK_OPTIONAL:
        if name not in sec:
            warnings.append(f"缺少附属区块「{name}」（不计入七字段，但审查与复盘需要）")
        elif not meaningful(sec[name]):
            warnings.append(f"附属区块「{name}」为空（不计入七字段，但审查与复盘需要）")


def check_review(sec: dict[str, list[str]], errors: list[str], warnings: list[str]) -> None:
    check_common(sec, REVIEW_REQUIRED, errors, warnings)

    if "结论" in sec:
        text = "\n".join(meaningful(sec["结论"]))
        if not any(c in text for c in REVIEW_CONCLUSIONS):
            errors.append(f"结论必须是 {' / '.join(REVIEW_CONCLUSIONS)} 之一")

    if "风险级别" in sec:
        text = "\n".join(meaningful(sec["风险级别"]))
        if not any(re.search(rf"(?:^|[^一-龥]){r}(?:[^一-龥]|$)", text) for r in REVIEW_RISKS):
            errors.append(f"风险级别必须是 {' / '.join(REVIEW_RISKS)} 之一，并据此决定审查强度")

    for name in ("任务卡", "改动范围", "验收命令与结果", "发现的问题", "规格偏差回写"):
        if name not in sec:
            continue
        lines = meaningful(sec[name])
        if not lines:
            continue  # check_common 已报错
        joined = "\n".join(lines)
        if name in ("任务卡", "改动范围", "验收命令与结果") and is_empty_value(value_of(lines, name) or joined):
            errors.append(f"「{name}」不能填「无」，必须写出实际内容或明确「未执行 / 未附」")


def check(path: Path, strict: bool, kind: str) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    text = strip_comments(path.read_text(encoding="utf-8-sig"))
    sec = split_sections(text)
    if kind == "task":
        check_task(sec, errors, warnings)
        required = TASK_REQUIRED
    else:
        check_review(sec, errors, warnings)
        required = REVIEW_REQUIRED

    ok = not errors and (not strict or not warnings)
    return {
        "file": str(path),
        "kind": kind,
        "ok": ok,
        "errors": errors,
        "warnings": warnings,
        "fields_found": [n for n in required if n in sec],
        "fields_total": len(required),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="校验 agentic-coding 任务卡 / 审查记录")
    ap.add_argument("files", nargs="+", help="Markdown 产出物路径")
    ap.add_argument("--kind", choices=("task", "review"), default="task",
                    help="产出物类型，默认 task（任务卡）")
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
            results.append(check(p, args.strict, args.kind))
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
            print(f"{status} {r['file']}  kind={r['kind']}  "
                  f"fields={len(r['fields_found'])}/{r['fields_total']}  "
                  f"errors={len(r['errors'])}  warnings={len(r['warnings'])}")

    if io_error:
        return 2
    return 0 if results and all(r["ok"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
