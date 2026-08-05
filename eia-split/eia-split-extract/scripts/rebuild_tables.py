# -*- coding: utf-8 -*-
"""rebuild_tables.py — 从 clean.txt 按标题重建表(extract 错位时的治本工具)。

表普查(table_census.py)在源PDF表号错乱时产出不可信(ch5 sub4/5/6 实测 data/ 普查错位,
被迫从 clean.txt 逐张手工重建)。本工具把"重建"固化成标准路径, 避免每次临时写 build_tables.py:
  - 自动: 对权威表号集 C 中每表, 从 clean.txt 抽规则网格行(空白/多空格分列)
  - 手工: 读 data/table_overrides.json ({表号: rows}) 覆盖自动结果(复杂表/合并单元格/跨页)
  - 校验: 每张表列数一致
用法:
  python3 rebuild_tables.py --work-dir <dir>            # 预览(不写)
  python3 rebuild_tables.py --work-dir <dir> --apply   # 写回 data/all_tables_pdf.json(备份原)
注意: 仅重建 rows; 表标题行以 clean.txt 为准。自动抽失败的复杂表必须补 table_overrides.json。
"""
import os, re, json, argparse, yaml, shutil


def load_yaml(p):
    return yaml.safe_load(open(p, encoding="utf-8")) or {}


def is_caption_line(line):
    s = line.strip()
    if not re.match(r'^表\s*\d+\.\d+-\d+', s):
        return False
    rest = s[re.match(r'^表\s*\d+\.\d+-\d+', s).end():].strip()
    if rest.startswith(('（', '(')) and '表' in rest:
        return False
    return True


def grep_table_ids(txt_path):
    ids, seen = [], set()
    for line in open(txt_path, encoding="utf-8").read().split("\n"):
        if is_caption_line(line):
            m = re.search(r'表\s*(\d+\.\d+)-(\d+)', line)
            if m:
                tid = f"表{m.group(1)}-{m.group(2)}"
                if tid not in seen:
                    seen.add(tid)
                    ids.append(tid)
    return ids


def auto_extract(txt_path, tid):
    """从 clean.txt 抽表号 tid 后、直到下一个表号/章节头的行, 按空白分列。"""
    lines = open(txt_path, encoding="utf-8").read().split("\n")
    start = None
    for i, l in enumerate(lines):
        if is_caption_line(l):
            m = re.search(r'表\s*(\d+\.\d+)-(\d+)', l)
            if m and f"表{m.group(1)}-{m.group(2)}" == tid:
                start = i
                break
    if start is None:
        return None
    rows = []
    for line in lines[start + 1:]:
        if is_caption_line(line):
            break
        if re.match(r'^\s*\d+\.\d+(\.\d+)*\s', line):
            break
        cells = [c.strip() for c in re.split(r'\s{2,}|\s+', line.strip()) if c.strip()]
        if len(cells) >= 2:
            rows.append(cells)
    return rows or None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-dir", required=True)
    ap.add_argument("--apply", action="store_true", help="写回 data/all_tables_pdf.json(备份原)")
    args = ap.parse_args()
    wd = os.path.abspath(args.work_dir)
    cfg = load_yaml(os.path.join(wd, "project.yaml"))
    chapter = cfg.get("chapter") or "N"
    data_dir = os.path.join(wd, "data")
    txt_path = os.path.join(data_dir, f"chapter{chapter}-clean.txt")
    if not os.path.exists(txt_path):
        print("❌ 未找到", txt_path)
        return
    C = grep_table_ids(txt_path)
    ov_path = os.path.join(data_dir, "table_overrides.json")
    overrides = json.load(open(ov_path, encoding="utf-8")) if os.path.exists(ov_path) else {}
    result = {}
    skipped = []
    for tid in C:
        rows = overrides.get(tid) or auto_extract(txt_path, tid)
        if not rows:
            skipped.append(tid)
            continue
        result[tid] = {"title": tid, "fields": rows[0],
                       "rows": rows, "source": "override" if tid in overrides else "rebuild"}
    bad = [(t, sorted(set(len(r) for r in v["rows"] if isinstance(r, list))))
           for t, v in result.items()
           if len(set(len(r) for r in v["rows"] if isinstance(r, list))) > 1]
    if skipped:
        print(f"⚠️ 自动抽失败且无 override, 跳过 {len(skipped)} 张: {skipped}（需补 table_overrides.json）")
    if bad:
        print(f"⚠️ 列数不一致需 override 修正: {bad}")
    if not args.apply:
        print(f"=== 预览: 自动+override 共 {len(result)} 张表 ===")
        for tid, v in list(result.items())[:5]:
            print(f"  {tid}: {len(v['rows'])}行 宽{len(v['rows'][0]) if v['rows'] else 0} source={v['source']}")
        if len(result) > 5:
            print(f"  ... 共 {len(result)} 张")
        print("加 --apply 写回 data/all_tables_pdf.json")
        return
    json_path = os.path.join(data_dir, "all_tables_pdf.json")
    if os.path.exists(json_path):
        shutil.copy2(json_path, json_path + ".bak")
    json.dump(result, open(json_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"✅ 写回 {json_path} ({len(result)} 张表, 备份 .bak)")


if __name__ == "__main__":
    main()
