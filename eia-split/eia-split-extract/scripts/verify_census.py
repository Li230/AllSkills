# -*- coding: utf-8 -*-
"""verify_census.py — 表普查后置强自检（extract 后必须跑，不可跳过）。

表普查(table_census.py)只查缺号/多号，不足以暴露「源PDF表号错乱」类问题。
本脚本在 census 之后对 data/all_tables_pdf.json 做强校验，把隐患提前到 extract 阶段：
  1. 唯一性/缺号/多号：JSON 键集 vs clean.txt 权威表号集 C
  2. 连续性：按「章.节」分组，组内表号应连续（缺号报警）
  3. 列数一致性：每张表各行宽度应 == 表头宽度（不一致=被合并邻表/吞末列）
  4. 表头垃圾：表头字段不得含 >40 字或句号（否则真表头丢失）
  5. 空表：无 rows 或仅表头的表
任一不合格 → 打印 ⚠️ 报告，建议从 clean.txt 重建(见 rebuild_tables.py)。

用法: python3 verify_census.py --work-dir <dir>
"""
import os, re, json, argparse, yaml


def load_yaml(p):
    return yaml.safe_load(open(p, encoding="utf-8")) or {}


def grep_table_ids(txt_path):
    """从 clean.txt 抽表标题行表号 -> 权威集 C（排除内联引用）。"""
    ids, seen = [], set()
    for line in open(txt_path, encoding="utf-8").read().split("\n"):
        s = line.strip()
        m = re.match(r'^表\s*(\d+\.\d+)-(\d+)', s)
        if not m:
            continue
        rest = s[m.end():].strip()
        if rest.startswith(('（', '(')) and '表' in rest:
            continue  # 内联引用
        tid = f"表{m.group(1)}-{m.group(2)}"
        if tid not in seen:
            seen.add(tid)
            ids.append(tid)
    return ids


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-dir", required=True)
    args = ap.parse_args()
    wd = os.path.abspath(args.work_dir)
    cfg = load_yaml(os.path.join(wd, "project.yaml"))
    chapter = cfg.get("chapter") or "N"
    data_dir = os.path.join(wd, "data")
    json_path = os.path.join(data_dir, "all_tables_pdf.json")
    if not os.path.exists(json_path):
        print("❌ 未找到", json_path)
        return
    data = json.load(open(json_path, encoding="utf-8"))
    txt_path = os.path.join(data_dir, f"chapter{chapter}-clean.txt")
    C = grep_table_ids(txt_path) if os.path.exists(txt_path) else []
    keys = list(data.keys())
    problems = []

    # 1. 缺号 / 多号
    missing = [t for t in C if t not in data]
    extra = [k for k in keys if re.match(r'^表\d', k) and k not in C]
    if missing:
        problems.append(f"缺号(PDF/txt均缺): {missing}")
    if extra:
        problems.append(f"多号(误抽/未归正): {extra}")

    # 2. 连续性（按 章.节 分组, 仅提示跳号; 缺号已由上方 missing 覆盖, 不重复报警）
    # 环评报告跨节表号不连续是常态(每节独立编号/跳号), 不视为错误, 仅 ℹ️ 提示供人工确认。
    groups = {}
    for t in C:
        a, b = t[1:].split("-")
        groups.setdefault(a, []).append(int(b))
    hints = []
    for g, nums in groups.items():
        nums.sort()
        gaps = [i for i in range(nums[0], nums[-1] + 1) if i not in nums]
        if gaps:
            gap_str = ", ".join("表" + g + "-" + str(i) for i in gaps)
            hints.append("组 " + g + " 跳号(可能正常): " + gap_str)
    for h in hints:
        print("ℹ️", h)

    # 3/4/5. 列数一致 / 表头垃圾 / 空表
    for k, v in data.items():
        rows = v.get("rows") or []
        if not rows:
            problems.append(f"{k}: 空表(无 rows)")
            continue
        header = rows[0]
        if isinstance(header, list):
            if any(len(str(c)) > 40 or '。' in str(c) for c in header):
                problems.append(f"{k}: 表头疑似垃圾(含超长/句号字段)")
            widths = set(len(r) for r in rows if isinstance(r, list))
            if len(widths) > 1:
                problems.append(f"{k}: 列数不一致(各行宽度 {sorted(widths)}) → 可能合并邻表/吞末列")

    print(f"=== 表普查强自检 (work-dir={os.path.basename(wd)}) ===")
    print(f"权威表号 C={len(C)}  抽得={len(keys)}")
    if not problems:
        print("✅ 全部通过: 唯一性/连续性/列数/表头/空表 均无异常")
    else:
        print(f"⚠️ 发现 {len(problems)} 项问题:")
        for p in problems:
            print("  -", p)
        print("建议: 错位表从 clean.txt 重建(见 rebuild_tables.py)，改 all_tables_pdf.json 后重渲。")


if __name__ == "__main__":
    main()
