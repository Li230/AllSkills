# -*- coding: utf-8 -*-
"""fix_tables.py — render 阶段修复表数据(根上改 all_tables_pdf.json)。
用 pdfplumber extract_tables() 带列坐标重抽(列聚合准), 清洗单元格中文劈裂词,
写回 data/all_tables_pdf.json。render 随后重渲即得干净表。
仅处理指定表号(默认全部本章程表)。
用法: python3 fix_tables.py --work-dir <dir> [--tables 表6.2-1,表6.2-2]
"""
import os, re, json, argparse, yaml, shutil
import pdfplumber


def _is_cjk(ch):
    return bool(re.match(r'[\u4e00-\u9fff]', ch or ' '))


def _has_ascii_or_num(s):
    return bool(re.search(r'[A-Za-z0-9]', s))


def merge_cjk(s):
    if not s:
        return s
    for _ in range(4):
        parts = [p for p in s.split(" ") if p]
        out = []
        for p in parts:
            if (out and _is_cjk(out[-1][-1]) and _is_cjk(p[0])
                    and not _has_ascii_or_num(out[-1]) and not _has_ascii_or_num(p)):
                out[-1] = out[-1] + p
            else:
                out.append(p)
        new = " ".join(out)
        if new == s:
            break
        s = new
    return s


def clean_row(row):
    return [merge_cjk((c or "").replace("\n", " ")) for c in row]


def table_caption_page(pdf):
    """返回 {表号: (页码, 标题行top坐标)} — 扫每页 text 找 表X.Y-Z 标题行。"""
    cap = {}
    for pi in range(len(pdf.pages)):
        words = pdf.pages[pi].extract_words()
        txt = pdf.pages[pi].extract_text() or ""
        for line in txt.split("\n"):
            m = re.match(r'^表\s*(\d+\.\d+)-(\d+)', line.strip())
            if m:
                tid = f"表{m.group(1)}-{m.group(2)}"
                # 找该行对应 top: 取含表号词的 word 的 top
                top = None
                for w in words:
                    if w["text"].startswith("表"):
                        top = w["top"]
                        break
                cap.setdefault(tid, (pi, top))
    return cap


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-dir", required=True)
    ap.add_argument("--tables", default="")
    args = ap.parse_args()
    wd = os.path.abspath(args.work_dir)
    cfg = yaml.safe_load(open(os.path.join(wd, "project.yaml"), encoding="utf-8"))
    ch = cfg["chapter"]; ch_s = str(ch)
    data_dir = os.path.join(wd, "data")
    json_path = os.path.join(data_dir, "all_tables_pdf.json")
    data = json.load(open(json_path, encoding="utf-8"))
    # 目标表号
    if args.tables:
        targets = set(args.tables.split(","))
    else:
        targets = {k for k in data if k.startswith(f"表{ch_s}.")}
    pdf_path = cfg["pdf_path"]
    with pdfplumber.open(pdf_path) as pdf:
        caps = table_caption_page(pdf)
        for tid in sorted(targets):
            if tid not in caps:
                print(f"⚠️ {tid} 未在PDF找到标题行, 跳过")
                continue
            pi, cap_top = caps[tid]
            tbls = pdf.pages[pi].extract_tables()
            if not tbls:
                print(f"⚠️ {tid} 页 {pi+1} 无表格, 跳过")
                continue
            # 选 y 坐标最接近标题行的表(一页多表时不误选), 而非"该页最大表"
            def tbl_top(t):
                # extract_tables 不返坐标, 用该页 words 估算: 取首个非空单元格行对应 top
                for r in t:
                    for c in r:
                        if c:
                            for w in pdf.pages[pi].extract_words():
                                if c[:3] in w["text"] or w["text"][:3] in c:
                                    return w["top"]
                return 9999
            if cap_top is not None:
                tbl = min(tbls, key=lambda t: abs(tbl_top(t) - cap_top))
            else:
                tbl = max(tbls, key=lambda t: len(t[0]) if t else 0)
            cleaned = [clean_row(r) for r in tbl]
            old = data.get(tid, {})
            data[tid] = {
                "title": old.get("title", tid),
                "fields": cleaned[0] if cleaned else [],
                "rows": cleaned,
                "source": "extract_tables_fixed",
                "page": pi + 1,
            }
            print(f"✅ {tid}: {len(cleaned)}行 x {len(cleaned[0]) if cleaned else 0}列 (页{pi+1})")
    # 备份 + 写回
    shutil.copy2(json_path, json_path + ".bak")
    json.dump(data, open(json_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"写回 {json_path} (备份 .bak)")


if __name__ == "__main__":
    main()
