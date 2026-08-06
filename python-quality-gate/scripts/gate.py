#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Python 代码质量硬闸门：flake8 + black --check + pytest
用法: python3 gate.py --target <目录|文件> [--skip-tests]
返回码: 0 = 全绿, 1 = 有失败
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"


def run(cmd: list[str], label: str) -> tuple[bool, str]:
    """运行命令，返回 (是否通过, 摘要)"""
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        ok = proc.returncode == 0
        detail = proc.stdout.strip().splitlines()
        brief = (
            detail[0]
            if detail
            else proc.stderr.strip().splitlines()[-1] if proc.stderr else "?"
        )
        return ok, brief
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT (>120s)"
    except FileNotFoundError:
        return False, "工具未安装"


def collect_py_files(target: str) -> list[str]:
    """收集 target 下的 .py 文件列表（目录则递归）"""
    tp = Path(target)
    if tp.is_file():
        return [str(tp)] if tp.suffix == ".py" else []
    return [str(p) for p in tp.rglob("*.py")]


def main() -> int:
    ap = argparse.ArgumentParser(description="Python quality gate")
    ap.add_argument("--target", default=".", help="目录或 .py 文件")
    ap.add_argument("--skip-tests", action="store_true", help="跳过 pytest")
    args = ap.parse_args()

    target = str(Path(args.target).resolve())
    print(f"\n=== Python Quality Gate ===  target: {target}")
    t0 = time.time()
    results = []

    py_files = collect_py_files(target)
    if not py_files:
        print(f"{RED}❌ 未找到 .py 文件{RESET}")
        return 1

    # 1. flake8（max-line-length 对齐 black 的 88，避免 E501 误报）
    ok, brief = run(
        [sys.executable, "-m", "flake8", "--max-line-length=88", *py_files],
        "flake8",
    )
    results.append(("flake8", ok, brief))

    # 2. black --check（传文件列表，规避 black 目录扫描异常）
    ok, brief = run(
        [sys.executable, "-m", "black", "--check", *py_files],
        "black --check",
    )
    results.append(("black --check", ok, brief))

    # 3. pytest（存在 test 文件才跑）
    if not args.skip_tests:
        tp = Path(target)
        has_tests = (
            tp.is_dir()
            and bool(list(tp.rglob("test_*.py")) + list(tp.rglob("*_test.py")))
            or (tp.is_file() and tp.name.startswith("test_"))
        )
        if has_tests:
            ok, brief = run([sys.executable, "-m", "pytest", "-q", target], "pytest")
            results.append(("pytest", ok, brief))
        else:
            results.append(("pytest", True, "SKIP (无测试文件)"))
    else:
        results.append(("pytest", True, "SKIP (--skip-tests)"))

    # 汇总
    all_green = True
    for i, (name, ok, brief) in enumerate(results, 1):
        mark = f"{GREEN}PASS{RESET}" if ok else f"{RED}FAIL{RESET}"
        if not ok:
            all_green = False
        print(f"[{i}/3] {name:<14} {mark}  {brief[:100]}")

    elapsed = time.time() - t0
    if all_green:
        print(f"=== RESULT: {GREEN}✅ ALL GREEN{RESET} ({elapsed:.1f}s) ===")
        return 0
    print(f"=== RESULT: {RED}❌ FAILED{RESET} ({elapsed:.1f}s) — 修复后重跑 ===")
    return 1


if __name__ == "__main__":
    sys.exit(main())
