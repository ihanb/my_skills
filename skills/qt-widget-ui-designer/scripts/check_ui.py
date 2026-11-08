#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""qt-widget-ui-designer 静态校验器（Step 6 / Step 8 使用）。

用法：
    python scripts/check_ui.py prototype.html ui/
    python scripts/check_ui.py ui/status_card.cpp          # 只扫 C++
    python scripts/check_ui.py prototype.html --strict     # WARN 也视为失败

参数可混合传 HTML 文件、C++ 文件、目录；目录会递归收集 .html/.htm 与 .h/.cpp 等源码。
脚本只做**可机械判定**的检查，人工判断项仍按 references/quality-checklist.md 逐项自查。

输出：ERROR 必须清零才能进入下一步；WARN 需人工确认。
退出码：0 = 无 ERROR（--strict 下无 WARN），1 = 有 ERROR，2 = 参数/读取错误。
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

try:  # Windows 终端编码保护
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

HTML_EXT = {".html", ".htm"}
CPP_EXT = {".h", ".hpp", ".hh", ".hxx", ".cpp", ".cc", ".cxx", ".c++"}
PALETTE_FILES = ("theme_manager", "palette", "colors")

# (正则, 代码, 级别, 说明)
HTML_RULES = [
    (r"box-shadow\s*:", "HTML_SHADOW", "ERROR", "QSS 不支持阴影；用纯色/边框表达层次，或走 Step 7.3 的 Qt 侧增强"),
    (r"text-shadow\s*:", "HTML_TEXT_SHADOW", "ERROR", "QSS 不支持 text-shadow"),
    (r"backdrop-filter\s*:", "HTML_BACKDROP_FILTER", "ERROR", "QSS 不支持 backdrop-filter"),
    (r"(?<![\w-])filter\s*:", "HTML_FILTER", "ERROR", "QSS 不支持 filter"),
    (r"\bopacity\s*:", "HTML_OPACITY", "ERROR", "QSS 不支持 opacity；透明度需自定义绘制"),
    (r"\btransform\s*:", "HTML_TRANSFORM", "ERROR", "QSS 不支持 transform"),
    (r"\btransition\s*:|\banimation\s*:", "HTML_ANIMATION", "ERROR", "原型禁用 CSS 动画/过渡；Qt 用 QPropertyAnimation"),
    (r"clip-path\s*:", "HTML_CLIP_PATH", "ERROR", "QSS 不支持 clip-path"),
    (r"border-image\s*:", "HTML_BORDER_IMAGE", "ERROR", "QSS border-image 语法不同，易出错"),
    (r"(?:linear|radial)-gradient\s*\(", "HTML_GRADIENT", "ERROR", "禁用渐变；用纯色替代"),
    (r"position\s*:\s*(?:absolute|fixed)", "HTML_ABSOLUTE", "ERROR", "禁用绝对/固定定位；用 flex/grid"),
    (r"\bfloat\s*:", "HTML_FLOAT", "ERROR", "禁用 float；用 flex/grid"),
    (r"z-index\s*:", "HTML_Z_INDEX", "ERROR", "禁用层叠；控件层级由布局顺序决定"),
    (r"::(?:before|after)\b", "HTML_PSEUDO_ELEMENT", "ERROR", "QSS 没有 ::before/::after 伪元素"),
    (r"@font-face|fonts\.googleapis\.com", "HTML_WEBFONT", "ERROR", "禁用 Web 字体；用系统字体"),
    (r"<svg\b", "HTML_SVG_ICON", "WARN", "原型用 Unicode/文字占位；Qt 侧仍可用 QIcon('*.svg') 资源"),
    (r"data:image/svg\+xml", "HTML_SVG_DATAURI", "ERROR", "QSS data URI SVG 仅全局主题 indicator 可用"),
    (r"\b\d+(?:\.\d+)?(?:em|rem|vw|vh)\b", "HTML_RELATIVE_UNIT", "WARN", "Qt 布局基于像素，间距统一用 px"),
]

# QSS ID 选择器是 #name，只匹配后面跟 3/6/8 位 hex 且不是标识符的写法
HEX_RE = re.compile(r"(?<![&\w])#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
FUNC_RE = re.compile(r"^\s*(?:[\w:<>*&~]+\s+)*?([A-Za-z_~][\w:]*(?:::\w+)?)\s*\(")


@dataclass
class Finding:
    level: str
    path: str
    line: int
    code: str
    message: str

    def __str__(self) -> str:
        return f"{self.level:<5} {self.path}:{self.line} {self.code}: {self.message}"


def collect(paths: list[str]) -> tuple[list[Path], list[Path]]:
    htmls, cpps = [], []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            for f in sorted(p.rglob("*")):
                if f.suffix.lower() in HTML_EXT:
                    htmls.append(f)
                elif f.suffix.lower() in CPP_EXT:
                    cpps.append(f)
        elif p.is_file():
            suf = p.suffix.lower()
            if suf in HTML_EXT:
                htmls.append(p)
            elif suf in CPP_EXT:
                cpps.append(p)
            else:
                print(f"WARN  跳过不支持的文件类型: {p}", file=sys.stderr)
        else:
            print(f"ERROR 路径不存在: {p}", file=sys.stderr)
    return htmls, cpps


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def is_comment(line: str) -> bool:
    s = line.strip()
    return s.startswith(("//", "/*", "*", "<!--", "#"))


def add(findings: list[Finding], level: str, path: Path, lineno: int, code: str, msg: str) -> None:
    findings.append(Finding(level, str(path), lineno, code, msg))


def check_html(path: Path, findings: list[Finding]) -> None:
    for lineno, line in enumerate(read_lines(path), 1):
        if is_comment(line):
            continue
        for pattern, code, level, msg in HTML_RULES:
            if re.search(pattern, line):
                add(findings, level, path, lineno, code, msg)
        # :root 里的变量定义是合法的色板导出；其余位置硬编码 hex 提示人工确认
        is_var_def = re.search(r"--[\w-]+\s*:", line) is not None
        if not is_var_def and re.search(r":\s*[^;]*", line) and HEX_RE.search(line):
            add(findings, "WARN", path, lineno, "HTML_HARDCODE_COLOR",
                "非 :root 位置出现字面量色值；应引用 var(--key) 且与 ThemeManager 一致")


def check_cpp(path: Path, findings: list[Finding]) -> None:
    lines = read_lines(path)
    palette_file = any(tag in path.stem.lower() for tag in PALETTE_FILES)
    current_func = "<global>"
    all_text = "\n".join(lines)
    has_wa_hover = "WA_Hover" in all_text
    has_hover_rule = ":hover" in all_text
    has_attr_selector = re.search(r"\[[A-Za-z_][\w-]*\s*=\s*\\?[\"']", all_text) is not None
    has_prop_decl = ("Q_PROPERTY" in all_text) or ("setProperty(" in all_text)

    for lineno, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("//") or stripped.startswith("*"):
            continue
        m = FUNC_RE.match(line)
        # 只把「函数定义行」当作作用域边界：以 { 结尾，或 ) 后跟 const/override/noexcept。
        # 否则 setStyleSheet(...) 这类调用行会被误判成函数定义。
        looks_like_def = stripped.endswith("{") or re.search(
            r"\)\s*(?:const|override|noexcept)\b", line) is not None
        if (m and looks_like_def
                and not stripped.startswith(("if", "for", "while", "return", "connect", "setStyleSheet"))):
            current_func = m.group(1)

        if not palette_file and HEX_RE.search(line):
            add(findings, "ERROR", path, lineno, "CPP_HARDCODE_COLOR",
                "硬编码色值；改用 ThemeManager::ThemeColor(key).name()")

        if re.search(r"q(?:linear|radial)gradient", line, re.I):
            add(findings, "ERROR", path, lineno, "CPP_QSS_GRADIENT",
                "QSS 渐变性能差且语法不同；用纯色 + setProperty 切换")
        if re.search(r"\b(?:SLOT|SIGNAL)\s*\(", line):
            add(findings, "ERROR", path, lineno, "CPP_OLD_CONNECT",
                "使用新式 connect 语法，不用 SLOT/SIGNAL 宏")
        if re.search(r"setFixedWidth\s*\(", line):
            add(findings, "ERROR", path, lineno, "CPP_FIXED_WIDTH",
                "容器禁用 setFixedWidth()；用 minimumSize + sizePolicy + stretch")
        if re.search(r"setFixedHeight\s*\(", line):
            add(findings, "WARN", path, lineno, "CPP_FIXED_HEIGHT",
                "卡片/列表项固定高度是允许的；若用于内容区则改用 setMinimumHeight()")
        if re.search(r"data:image/svg\+xml", line, re.I):
            add(findings, "ERROR", path, lineno, "CPP_SVG_DATAURI",
                "运行时动态 setStyleSheet() 禁用 SVG data URI（QIcon 加载 .svg 资源不受此限）")

        if "setStyleSheet(" in line:
            short_func = current_func.split("::")[-1]
            runtime_like = re.match(r"(?:Update|Set|Refresh|On|Handle|slot)", short_func) is not None
            in_loop = any(re.search(r"\b(?:for|while)\s*\(", l) for l in lines[max(0, lineno - 3):lineno - 1])
            if runtime_like or in_loop:
                add(findings, "ERROR", path, lineno, "CPP_RUNTIME_STYLESHEET",
                    f"在 {current_func}() / 循环中调用 setStyleSheet()；改用 setProperty + polish/unpolish")
            elif not current_func.endswith(("setupUi", "ApplyStylesheet")) and current_func != "<global>":
                add(findings, "WARN", path, lineno, "CPP_STYLESHEET_SCOPE",
                    f"setStyleSheet() 出现在 {current_func}()；确认是否在 setupUi() 之外的运行时路径")
            if has_hover_rule and not has_wa_hover:
                add(findings, "WARN", path, lineno, "CPP_MISSING_WA_HOVER",
                    "样式表含 :hover，自定义 QWidget 需 setAttribute(Qt::WA_Hover)")
            if has_attr_selector and not has_prop_decl:
                add(findings, "WARN", path, lineno, "CPP_MISSING_Q_PROPERTY",
                    "QSS 属性选择器需要 Q_PROPERTY 声明或已 setProperty 注册")


def main() -> int:
    parser = argparse.ArgumentParser(description="Qt Widget UI 静态校验（Step 6 / Step 8）")
    parser.add_argument("paths", nargs="+", help="HTML 原型 / C++ 源码文件或目录，可混合")
    parser.add_argument("--strict", action="store_true", help="WARN 也视为失败")
    args = parser.parse_args()

    htmls, cpps = collect(args.paths)
    if not htmls and not cpps:
        print("ERROR 没有找到任何 .html/.htm 或 C++ 源码文件", file=sys.stderr)
        return 2

    findings: list[Finding] = []
    for p in htmls:
        check_html(p, findings)
    for p in cpps:
        check_cpp(p, findings)

    for f in findings:
        print(f)
    errors = sum(f.level == "ERROR" for f in findings)
    warns = sum(f.level == "WARN" for f in findings)
    print(f"---\nfiles: {len(htmls) + len(cpps)} (html {len(htmls)} / cpp {len(cpps)}), "
          f"errors: {errors}, warnings: {warns}")
    if errors:
        print("结论：ERROR 未清零，按 quality-checklist.md 修复后再进入下一步。")
        return 1
    if args.strict and warns:
        print("结论：--strict 模式下存在未确认的 WARN。")
        return 1
    print("结论：静态检查通过；继续按 quality-checklist.md 完成人工自查。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
