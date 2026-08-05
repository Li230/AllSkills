# -*- coding: utf-8 -*-
"""parse.py — 环评章节结构解析(参数化, 通用)。
PDF->raw.txt->clean.txt, 识别 h1-h4 标题/表/图, 输出 structure.json + 摘要。
表号/四级标题允许无空格写法(^表\\s*6.\\d+-\\d+ / ^6.\\d+.\\d+.\\d+\\s*)。

【scope 裁剪】(大章拆 sub: 固化 ch4/ch5 项目副本)
  若 project.yaml 含 scope_sections, 按"自身+全部祖先+后裔"三层判定裁剪 clean.txt 与
  structure.json, 保证子任务 txt 零冗余(邻居节内容被标题边界挡在门外)。无 scope 则全章解析。

【标题鲁棒性】(固化 ch5)
  is_valid_title: 拒假阳性(结尾标点 />60字 / 纯数字cap如"5 10.00" / 多点点号"5.4.2.1 5.4.2.2")
  in_range: 编号各段<=30 守卫

【表/图跨度】(固化 ch5)
  表记 end_line(下一标记前一行); 图记 section(h2 父), 供 extract 定位。

用法: python3 parse.py --work-dir <dir>
"""
import os, re, json, argparse, yaml
try:
    import pdfplumber
except ImportError:
    from pypdf import PdfReader


def load_yaml(p):
    return yaml.safe_load(open(p, encoding="utf-8"))


def extract_pdf(pdf_path):
    parts = []
    if 'pdfplumber' in globals():
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                parts.append(page.extract_text() or "")
    else:
        r = PdfReader(pdf_path)
        for page in r.pages:
            parts.append(page.extract_text() or "")
    return "\n".join(parts)


def clean_text(txt):
    out = []
    prev_boundary = False
    for line in txt.split("\n"):
        s = line.strip()
        if not s:
            continue
        if re.match(r'^\d{1,3}$', s):
            continue  # 页码
        # 边界行: 标题(章/节/子节号) / 表 / 图 开头 -> 独立成行, 不向前/向后合并
        is_boundary = bool(re.match(r'^\d+\.\d+', s) or re.match(r'^\d+\s', s)
                           or s.startswith('表') or s.startswith('图'))
        if is_boundary:
            out.append(s)  # 标题/表/图永远独立成行
            prev_boundary = True
            continue
        # 上一行是边界行(如标题) -> 本行是正文, 绝不并入标题行
        if out and not prev_boundary and out[-1][-1] not in '。；，、）)":：' and not s[0] in '0123456789（([':
            out[-1] = out[-1] + s
        else:
            out.append(s)
        prev_boundary = False
    return [re.sub(r'  +', ' ', l) for l in out]


# ---------- 标题鲁棒性(ch5) ----------
def is_valid_title(line, num):
    for p in num.split("."):
        if len(p) > 2:
            return False
    if line.rstrip().endswith(("。", "；", "，", ".", "．")):
        return False
    if len(line) > 60:
        return False
    cap = line.split(None, 1)[1] if " " in line else ""
    if re.search(r"\d+\.\d+(\s+\d+\.\d+){1,}", cap):
        return False
    if cap and cap[0].isdigit() and not re.search(r'[一-鿿]', cap):
        return False
    return True


def in_range(num):
    parts = num.split(".")[1:]
    return all(p.isdigit() and 1 <= int(p) <= 30 for p in parts)


def parse(work_dir):
    cfg = load_yaml(os.path.join(work_dir, "project.yaml"))
    ch = cfg["chapter"]; ch_s = str(ch)
    txt = extract_pdf(cfg["pdf_path"])
    data_dir = os.path.join(work_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    open(os.path.join(data_dir, f"chapter{ch}-raw.txt"), "w", encoding="utf-8").write(txt)
    cleaned = clean_text(txt)
    clean_path = os.path.join(data_dir, f"chapter{ch}-clean.txt")

    h1, h2, h3, h4, tables, figures = [], [], [], [], [], []
    l2 = re.compile(rf'^{ch_s}\.(\d+)\s*(.+)')
    l3 = re.compile(rf'^{ch_s}\.(\d+)\.(\d+)\s*(.+)')
    l4 = re.compile(rf'^{ch_s}\.(\d+)\.(\d+)\.(\d+)\s*(.+)')
    tp = re.compile(rf'^表\s*{ch_s}\.(\d+)-(\d+)\s*(.+)')  # \s* 允许无空格
    fp = re.compile(r'^图\s*(\d+)\.(\d+)-(\d+)\s*(.*)$')
    for i, line in enumerate(cleaned, 1):
        s = line.strip()
        mf = fp.match(s)
        if mf:
            figures.append({"fig_id": f"图{mf.group(1)}.{mf.group(2)}-{mf.group(3)}",
                            "title": mf.group(4).strip(), "line": i, "level": 5, "figure": True})
            continue
        mt = tp.match(s)
        if mt and is_valid_title(s, f"{ch_s}.{mt.group(1)}.{mt.group(2)}"):
            tables.append({"table_id": f"{ch_s}.{mt.group(1)}-{mt.group(2)}",
                           "title": mt.group(3).strip(), "line": i, "end_line": i,
                           "section": f"{ch_s}.{mt.group(1)}"})
            continue
        m4 = l4.match(s)
        if m4 and is_valid_title(s, f"{ch_s}.{m4.group(1)}.{m4.group(2)}.{m4.group(3)}") and in_range(f"{ch_s}.{m4.group(1)}.{m4.group(2)}.{m4.group(3)}"):
            h4.append({"num": f"{ch_s}.{m4.group(1)}.{m4.group(2)}.{m4.group(3)}", "level": 4,
                       "title": m4.group(4).strip(), "line": i,
                       "section": f"{ch_s}.{m4.group(1)}.{m4.group(2)}", "parent": f"{ch_s}.{m4.group(1)}.{m4.group(2)}"})
            continue
        m3 = l3.match(s)
        if m3 and is_valid_title(s, f"{ch_s}.{m3.group(1)}.{m3.group(2)}") and in_range(f"{ch_s}.{m3.group(1)}.{m3.group(2)}"):
            h3.append({"num": f"{ch_s}.{m3.group(1)}.{m3.group(2)}", "level": 3,
                       "title": m3.group(3).strip(), "line": i, "section": f"{ch_s}.{m3.group(1)}"})
            continue
        m2 = l2.match(s)
        if m2 and is_valid_title(s, f"{ch_s}.{m2.group(1)}") and in_range(f"{ch_s}.{m2.group(1)}"):
            h2.append({"num": f"{ch_s}.{m2.group(1)}", "level": 2,
                       "title": m2.group(2).strip(), "line": i})
            continue
        m1 = re.match(rf'^{ch_s}\s+(.+)', s)
        if m1 and is_valid_title(s, ch_s):
            h1.append({"num": ch_s, "level": 1, "title": m1.group(1).strip(), "line": i})

    # 表 end_line = 下一个标记(表/H1/H2/H3/H4/图行)前一行
    fig_lines = [i + 1 for i, l in enumerate(cleaned) if re.search(r"图\s*\d+\.\d+-\d+", l)]
    markers = sorted([(t["line"], 0) for t in tables] +
                     [(x["line"], 1) for x in h1 + h2 + h3 + h4] +
                     [(f, 2) for f in fig_lines])
    for t in tables:
        nxt = [m[0] for m in markers if m[0] > t["line"]]
        t["end_line"] = (nxt[0] - 1) if nxt else len(cleaned)

    # 图 section = 其前的 h2 父
    h2_by_line = {t["line"]: t["num"] for t in h2}
    h2_lines_sorted = sorted(h2_by_line.keys())
    for f in figures:
        parent_line = max([ln for ln in h2_lines_sorted if ln <= f["line"]], default=None)
        f["section"] = h2_by_line[parent_line] if parent_line else None

    # ---------- scope 裁剪(ch4/ch5) ----------
    titles = h1 + h2 + h3 + h4
    scope = cfg.get("scope_sections") or []
    if scope:
        scope_set = set(scope)
        allowed = set(scope_set)
        for _sc in scope_set:                       # 全部祖先(不只直接父), 深 scope 也能保留 h2 包装
            _ps = _sc.split(".")
            for k in range(1, len(_ps)):
                allowed.add(".".join(_ps[:k]))

        def belongs(num):
            if num in allowed:
                return True
            for _sc in scope_set:
                if num.startswith(_sc + "."):
                    return True
            return False

        def section_belongs(section):
            if not section:
                return False
            if section in allowed:
                return True
            for _sc in scope_set:
                if _sc == section or _sc.startswith(section + "."):
                    return True
            return False

        all_titles = h1 + h2 + h3 + h4
        in_titles = [t for t in all_titles if belongs(t["num"])]
        if not in_titles:
            raise SystemExit(f"[ERR] scope {scope} 未匹配到任何标题")
        first_line = min(t["line"] for t in in_titles)
        last_line = max(t["line"] for t in in_titles)
        nxt_ns = [t["line"] for t in all_titles if not belongs(t["num"]) and t["line"] > last_line]
        end_full = (min(nxt_ns) - 1) if nxt_ns else len(cleaned)
        shift = first_line - 1
        crop_lines = cleaned[first_line - 1:end_full]
        total = len(crop_lines)

        def renum(n):
            return max(1, n - shift)

        titles = [{"num": t["num"], "title": t["title"], "line": renum(t["line"]),
                   "level": t["level"],
                   "section": t.get("section"), "parent": t.get("parent")}
                  for t in all_titles if belongs(t["num"])]
        tables = [{"table_id": t["table_id"], "title": t["title"], "line": renum(t["line"]),
                   "end_line": min(renum(t["end_line"]), total), "section": t["section"]}
                  for t in tables if section_belongs(t["section"])]
        figures = [{"fig_id": t["fig_id"], "title": t["title"], "line": renum(t["line"]),
                    "level": 5, "figure": True, "section": t.get("section")}
                   for t in figures if section_belongs(t.get("section"))]
        cleaned = crop_lines
        print(f"  [scope 裁剪] {scope} -> 行 {first_line}-{end_full}, 保留 h1={sum(1 for t in titles if t['level']==1)} h2={sum(1 for t in titles if t['level']==2)} h3={sum(1 for t in titles if t['level']==3)} h4={sum(1 for t in titles if t['level']==4)} 表={len(tables)} 图={len(figures)}")

    # 写回 clean.txt(裁剪后) 与 structure.json
    open(clean_path, "w", encoding="utf-8").write("\n".join(cleaned))
    structure = {"chapter": ch, "chapter_title": cfg.get("chapter_title"),
                 "scope_sections": scope,
                 "total_lines": len(cleaned), "titles": titles, "tables": tables, "figures": figures,
                 "txt_path": clean_path, "raw_txt_path": os.path.join(data_dir, f"chapter{ch}-raw.txt")}
    json.dump(structure, open(os.path.join(data_dir, "structure.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    n1 = sum(1 for t in titles if t["level"] == 1)
    n2 = sum(1 for t in titles if t["level"] == 2)
    n3 = sum(1 for t in titles if t["level"] == 3)
    n4 = sum(1 for t in titles if t["level"] == 4)
    print(f"✅ parse 完成: h1={n1} h2={n2} h3={n3} h4={n4} 表={len(tables)} 图={len(figures)}")
    print("表号:", [t["table_id"] for t in tables])
    print("标题:", [(t["num"], t["level"]) for t in titles])
    cfg["status"] = "parsed"
    yaml.safe_dump(cfg, open(os.path.join(work_dir, "project.yaml"), "w", encoding="utf-8"), allow_unicode=True, sort_keys=False)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-dir", required=True)
    parse(ap.parse_args().work_dir)
