# -*- coding: utf-8 -*-
"""表普查 table_census.py — 环评章节权威表清单与内容抽取。

流程:
  1. PDF -> chapter{N}-clean.txt, grep 全部 '表X.Y-Z' 候选 -> 去重 -> 权威表号集 C
  2. pdfplumber 按 caption 关联抽每页表格 (优先) -> 干净 cells; 无法关联者按 CONTENT_MAP 归正
  3. 对 C 中 PDF 未抽到的表号 -> txt 启发式兜底 (从 clean.txt 行范围抽)
  4. 自检: JSON 键集 == C; 缺号/多号报警
输出 data/all_tables_pdf.json: { "表X.Y-Z": {"title","fields","rows","source","page"} }

用法:
  python3 table_census.py --work-dir <dir> [--pdf <path>] [--txt <path>]
项目级 CONTENT_MAP 可放 <work_dir>/data/table_content_map.json: {"表X.Y-Z": ["签名子串", ...]}
"""
import json
import os
import re
import argparse
import pdfplumber


def is_caption_line(line):
    """判断该行是否为表标题行(而非内联引用)。
    表标题行: 行首即 '表X.Y-Z' 后可接 中文标题 / 数字年份(表4.1-1 2022年…) / 空白。
    内联引用(不算表): '见表2.2-2' / '(表3-2-4)' / '...详见表2.6-5'。
    ← 经验1: 早期 grep 不区分, 把正文引用也算成表号, 虚增权威表集 C 导致误报缺号。
    ← 经验2(hainan_ch4 sub1): 表标题后常接年份数字(表4.1-1 2022年春季…),
      旧正则漏识 → 表号进不了权威集 C, 被误报为'多号'。现放宽为
      '表号后接 中文/数字/空白/标点' 即可, 仅排除 '详见/见表/如' 等内联引用前缀。"""
    s = line.strip()
    if not re.match(r'^表\s*\d+\.\d+-\d+', s):
        return False
    rest = s[re.match(r'^表\s*\d+\.\d+-\d+', s).end():].strip()
    # 内联引用: 表号前或紧跟 '详见/见表/如' 等(但仍需行首判定, 故这里只兜底排除空rest下接括号引用)
    if rest.startswith(('（', '(')) and '表' in rest:
        return False
    return True


def grep_table_ids(txt_path):
    """从 clean.txt 抽取**表标题行**的表号, 去重 -> 权威表号集 C。
    只取行首为 '表X.Y-Z' 的标题行, 排除内联引用(见表X.Y-Z), 避免虚增 C。"""
    text = open(txt_path, encoding="utf-8").read()
    ids, seen = [], set()
    for line in text.split("\n"):
        if is_caption_line(line):
            m = re.search(r'表\s*(\d+\.\d+)-(\d+)', line)
            if m:
                tid = f"表{m.group(1)}-{m.group(2)}"
                if tid not in seen:
                    seen.add(tid)
                    ids.append(tid)
    return ids


def load_content_map(work_dir):
    p = os.path.join(work_dir, "data", "table_content_map.json")
    if os.path.exists(p):
        return json.load(open(p, encoding="utf-8"))
    return {}


def norm_caption(line):
    m = re.search(r'表\s*([\d.]+)-(\d+)\s*([^\n（(]*)', line)
    if m:
        return f"表{m.group(1)}-{m.group(2)}", m.group(3).strip()
    return None, None


def extract_pdf(pdf_path):
    results = {}
    with pdfplumber.open(pdf_path) as pdf:
        for pi, page in enumerate(pdf.pages):
            txt = page.extract_text() or ""
            tables = page.extract_tables()
            caps = []
            for line in txt.split("\n"):
                tid, name = norm_caption(line)
                if tid:
                    caps.append((tid, name, txt.index(line)))
            for ti, tb in enumerate(tables):
                flat = " ".join(" ".join(c or "" for c in row) for row in tb)
                tb_first = (tb[0][0] or "")[:6] if tb and tb[0] else ""
                best = None
                for tid, name, idx in caps:
                    if tb_first and tb_first in txt[max(0, idx):idx + 400]:
                        best = (tid, name)
                        break
                if not best and caps:
                    best = caps[min(ti, len(caps) - 1)]
                tid = best[0] if best else f"页{pi + 1}表{ti}"
                name = best[1] if best else ""
                clean = [[(c or "").replace("\n", " ").strip() for c in row] for row in tb]
                clean = [r for r in clean if any(r)]
                if tid not in results:
                    results[tid] = {"title": name, "page": pi + 1, "rows": clean, "source": "pdf"}
                else:
                    results[tid]["rows"].extend(clean[1:] if len(clean) > 1 else clean)
    return results


def correct_by_content(results, content_map):
    """按内容签名把 页N表M 归正到 表X.Y-Z; 单列长文本判为段落误抽删除。"""
    for ak in [k for k in list(results) if k.startswith("页")]:
        rows = results[ak]["rows"]
        flat = " ".join(" ".join(str(c) for c in r) for r in rows)
        mapped = False
        for tid, sigs in content_map.items():
            if all(s in flat for s in sigs):
                results[tid] = results.pop(ak)
                results[tid]["source"] = "pdf"
                mapped = True
                break
        if not mapped:
            cols = max((len(r) for r in rows), default=0)
            if cols <= 1:
                del results[ak]  # 段落误抽


def _trim_glued(cell):
    """去掉单元格尾部粘连的中文正文(数字/单位后跟中文时截断)。
    例 '656海峡危险品...' -> '656'; 坐标 '109°56′52″' 保留。"""
    m = re.match(r'^([\d\.\-]+[\d\.\°′″%万/\s]*)', cell)
    if m and len(m.group(1)) < len(cell):
        rest = cell[len(m.group(1)):]
        if rest and '\u4e00' <= rest[0] <= '\u9fff':
            return m.group(1).strip()
    return cell


def txt_fallback(txt_path, tid):
    """PDF 抽不到时, 从 clean.txt 按表号行范围启发式抽行。返回 rows 或 None。
    注意: clean.txt 中表值常为单空格分隔, 故用 \\s+ 切分; 要求 >=2 单元格且
    (含数字 或 为表后首行即表头) 以排除纯正文行。表尾粘连正文(如末行数值后跟段落)
    按表头宽度截断并清理单元格尾部中文, 避免污染表格。"""
    lines = open(txt_path, encoding="utf-8").read().split("\n")
    start = None
    for i, line in enumerate(lines):
        if line.strip().startswith(tid) or re.search(r'表\s*' + re.escape(tid[1:]), line):
            start = i
            break
    if start is None:
        return None
    rows = []
    header_len = None
    for j, line in enumerate(lines[start + 1:]):
        if re.match(r'^\s*表\s*\d', line) or re.match(r'^\s*\d+\.\d+(\.\d+)*\s+', line):
            break
        cells = [c.strip() for c in re.split(r'\s+', line.strip()) if c.strip()]
        if len(cells) >= 2 and (any(ch.isdigit() for ch in line) or j == 0):
            if header_len is None:
                header_len = len(cells)
            if header_len and len(cells) > header_len:
                cells = cells[:header_len]
            cells = [_trim_glued(c) for c in cells]
            rows.append(cells)
    if not rows:
        return None
    # 退化单行表: 若含 S1/S2... 控制点标记, 拆成 [控制点,北纬,东经] 多行
    if len(rows) == 1:
        coord = _try_coordinate_rows(" ".join(rows[0]))
        if coord:
            return coord
    return rows


def _try_coordinate_rows(text):
    """单行坐标控制点表(如 'S1 109°.. 19°.. S8 110°.. 20°..S2 ...') 拆成多行 [控制点,北纬,东经]。"""
    pts = re.findall(r'S(\d+)\s*([\d°′″.]+)\s+([\d°′″.]+)', text)
    if len(pts) >= 3:
        return [["S" + n, lat, lon] for n, lat, lon in pts]
    return None


def census(work_dir, pdf_path, txt_path, content_map):
    C = grep_table_ids(txt_path)
    pdf_res = extract_pdf(pdf_path)
    correct_by_content(pdf_res, content_map)
    # txt 兜底
    for tid in C:
        if tid not in pdf_res:
            rows = txt_fallback(txt_path, tid)
            if rows:
                pdf_res[tid] = {"title": tid, "page": None, "rows": rows, "source": "txt"}
    missing = [t for t in C if t not in pdf_res]
    # 保留所有 PDF 抽表(含未归正 页*), 不丢数据; 再叠加 txt 兜底
    out = dict(pdf_res)
    for tid in C:
        if tid not in out:
            rows = txt_fallback(txt_path, tid)
            if rows:
                out[tid] = {"title": tid, "page": None, "rows": rows, "source": "txt"}
    missing = [t for t in C if t not in out]
    extra = [k for k in out if re.match(r'^表\d', k) and k not in C]
    return out, C, missing, extra


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-dir", required=True)
    ap.add_argument("--pdf", default=None)
    ap.add_argument("--txt", default=None)
    args = ap.parse_args()
    cfg = {}
    py = os.path.join(args.work_dir, "project.yaml")
    if os.path.exists(py):
        import yaml
        cfg = yaml.safe_load(open(py, encoding="utf-8")) or {}
    base = cfg.get("base") or os.path.basename(args.work_dir)
    chapter = cfg.get("chapter") or "N"
    pdf_path = args.pdf or cfg.get("pdf_path")
    txt_path = args.txt or os.path.join(args.work_dir, "data", f"chapter{chapter}-clean.txt")
    if not pdf_path or not os.path.exists(pdf_path):
        raise SystemExit(f"PDF 未找到: {pdf_path}")
    if not os.path.exists(txt_path):
        raise SystemExit(f"txt 未找到: {txt_path}")
    content_map = load_content_map(args.work_dir)
    out, C, missing, extra = census(args.work_dir, pdf_path, txt_path, content_map)
    os.makedirs(os.path.join(args.work_dir, "data"), exist_ok=True)
    with open(os.path.join(args.work_dir, "data", "all_tables_pdf.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"表普查完成: 权威表号 {len(C)} 个; 抽得 {len(out)} 个")
    print(f"  缺号(PDF/txt均缺): {missing}")
    print(f"  多号(误抽): {extra}")
    print(f"  输出: data/all_tables_pdf.json")


if __name__ == "__main__":
    main()
