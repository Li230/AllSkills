#!/usr/bin/env python3
"""前端静态扫描：按 rules.json 规则检测反模式，输出 findings JSON。

用法:
    python3 scan.py --dir <目录> [--tech react|vue|vanilla|all]
                    [--out findings.json]
    python3 scan.py --file <文件> [--tech react|vue|vanilla|all]

规则文件默认为同目录 rules.json，可用 --rules 覆盖。
跳过 node_modules/dist/.git/build/__pycache__/.next 等目录。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

RULES_DEFAULT = Path(__file__).resolve().parent / "rules.json"
SKIP_DIRS = {"node_modules", "dist", ".git", "build", "__pycache__", ".next"}
TEXT_EXTS = {".js", ".jsx", ".ts", ".tsx", ".vue", ".html", ".css"}


def load_rules(path: Path) -> dict:
    """加载规则集并校验基本结构。"""
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if "rules" not in data or not isinstance(data["rules"], list):
        raise ValueError(f"规则文件 {path} 缺少 rules 数组")
    return data


def detect_tech(path: Path) -> str:
    """推断技术栈：扩展名优先，.js 按内容嗅探 React 特征。"""
    suffix = path.suffix.lower()
    if suffix == ".vue":
        return "vue"
    if suffix in {".jsx", ".tsx"}:
        return "react"
    if suffix == ".js":
        try:
            head = path.read_text(encoding="utf-8", errors="replace")[:4000]
        except OSError:
            head = ""
        if "from 'react'" in head or 'from "react"' in head or "useState(" in head:
            return "react"
    return "vanilla"


def scan_text(text: str, rules: list[dict], tech: str) -> list[dict]:
    """对单文件文本跑所有规则，返回 findings 列表。

    规则命中条件：
    1. tech 匹配（rule.tech 为 all 或等于当前 tech）
    2. 任一 pattern 正则命中
    3. 若规则定义了 missing，文件文本不含其中任一项（配套缺失）
    """
    findings: list[dict] = []
    for rule in rules:
        if rule.get("tech") not in ("all", tech):
            continue
        matches: list[re.Match] = []
        for pat in rule.get("patterns", []):
            try:
                regex = re.compile(pat)
            except re.error:
                continue
            matches.extend(regex.finditer(text))
        if not matches:
            continue
        missing = rule.get("missing", [])
        if missing and any(re.search(m, text) for m in missing):
            continue
        for m in matches:
            line = text.count("\n", 0, m.start()) + 1
            start = max(0, m.start() - 40)
            end = min(len(text), m.end() + 40)
            findings.append(
                {
                    "rule_id": rule["id"],
                    "name": rule["name"],
                    "dimension": rule["dimension"],
                    "severity": rule["severity"],
                    "line": line,
                    "evidence": text[start:end].replace("\n", " ").strip(),
                    "fix_hint": rule.get("fix_hint", ""),
                }
            )
    return findings


def scan_file(path: Path, rules: list[dict], tech: str | None) -> list[dict]:
    """扫描单个文本文件。"""
    if path.suffix.lower() not in TEXT_EXTS:
        return []
    effective_tech = tech if tech and tech != "all" else detect_tech(path)
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    findings = scan_text(text, rules, effective_tech)
    for f in findings:
        f["file"] = str(path)
    return findings


def scan_dir(root: Path, rules: list[dict], tech: str | None) -> list[dict]:
    """递归扫描目录（跳过 SKIP_DIRS），返回汇总 findings。"""
    findings: list[dict] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        findings.extend(scan_file(path, rules, tech))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="前端静态扫描")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--dir", type=str, help="扫描目录")
    src.add_argument("--file", type=str, help="扫描单文件")
    parser.add_argument(
        "--tech", choices=["all", "react", "vue", "vanilla"], default="all"
    )
    parser.add_argument("--rules", type=str, default=str(RULES_DEFAULT))
    parser.add_argument("--out", type=str, help="findings JSON 输出路径")
    args = parser.parse_args(argv)

    rules = load_rules(Path(args.rules))["rules"]
    if args.dir:
        findings = scan_dir(Path(args.dir), rules, args.tech)
    else:
        findings = scan_file(Path(args.file), rules, args.tech)

    summary = {"total": len(findings), "findings": findings}
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"OK: {len(findings)} findings -> {out}")
    else:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
