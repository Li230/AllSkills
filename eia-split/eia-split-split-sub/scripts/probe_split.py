# -*- coding: utf-8 -*-
"""probe_split.py — 大章拆 sub 的集中 SOP 脚本（固化 ch4/ch5 实证经验）。

定位：在 eia-split 流水线中位于 init 之后、extract 之前。
      大章（如 ch5=135页 / ch7=151页）先拆成多个 sub PDF，再各自跑完整流水线，最后合并。

两阶段（人工闸门在中间）：
  Phase 1  propose ：用 pdfplumber 探 full PDF 的 h1-h4 标题落页 + 表/图落页，
                      按 h3 边界（必要时自动下钻 h4）贪心分组 ≤max_pages(默认30)，
                      overlap 每边 2 页，输出审查表(sub|小节范围|页数|表格数) 并写 split_plan.json。
                      ★ 此阶段只读 PDF + 写 plan，不切文件，安全可反复跑/调参。
  Phase 2  split    ：读 split_plan.json（用户审核/调过），建 sub 目录、按页范围切 PDF、
                      写各 sub 的 project.yaml（含 scope_sections / scope_title）。
                      ★ 此阶段写文件，需用户审核通过后执行。

用法：
  # 1) 提出拆分子方案（审查表）
  python3 probe_split.py --work-dir <top_work_dir> --phase propose [--max-pages 30] [--overlap 2] [--cut-level 3]
  # 2) 用户看表审核；如需调整直接改 <top_work_dir>/split_plan.json 的 subs
  # 3) 审核通过，切 PDF + 建 sub 工程
  python3 probe_split.py --work-dir <top_work_dir> --phase split

work-dir 指向 init 建好的顶层工程（含 project.yaml：pdf_path/chapter/chapter_title/project）。
若 work-dir 无 project.yaml，可用 CLI 覆盖：--pdf --chapter --chapter-title --project。
"""
import os, re, json, argparse, yaml
from datetime import date

try:
    import pdfplumber
except ImportError:
    pdfplumber = None


# ---------- 配置加载 ----------
def load_cfg(work_dir, args):
    pyaml = os.path.join(work_dir, "project.yaml")
    cfg = {}
    if os.path.exists(pyaml):
        cfg = yaml.safe_load(open(pyaml, encoding="utf-8")) or {}
    # CLI 覆盖
    if args.pdf:
        cfg["pdf_path"] = args.pdf
    if args.chapter is not None:
        cfg["chapter"] = args.chapter
    if args.chapter_title:
        cfg["chapter_title"] = args.chapter_title
    if args.project:
        cfg["project"] = args.project
    for k in ("pdf_path", "chapter", "chapter_title", "project"):
        if k not in cfg:
            raise SystemExit(f"[ERR] 缺必填参数 {k}（写进 project.yaml 或用 --{k}）")
    cfg.setdefault("format", "flat")
    cfg.setdefault("table_mode", "pdf_census")
    return cfg


# ---------- Phase 1: 探落页 ----------
def probe(pdf_path, ch):
    """返回 (titles, tables, figures, total)。
    titles: [{num, level, title, page}]
    tables: [{table_id, title, page}]   # 去重，优先取非页眉/页脚的正文出现
    figures:[{fig_id, title, page}]
    """
    if pdfplumber is None:
        raise SystemExit("[ERR] 需要 pdfplumber：pip install pdfplumber")
    ch_s = str(ch)
    l2 = re.compile(rf'^{ch_s}\.(\d+)\s')
    l3 = re.compile(rf'^{ch_s}\.(\d+)\.(\d+)\s')
    l4 = re.compile(rf'^{ch_s}\.(\d+)\.(\d+)\.(\d+)\s')
    l1 = re.compile(rf'^{ch_s}(?=[\s章、])')  # "7 环境影响..." / "7章..."
    tp = re.compile(rf'^表\s*{ch_s}\.(\d+)-(\d+)\s*(.*)')
    fp = re.compile(r'^图\s*(\d+)\.(\d+)-(\d+)\s*(.*)')

    titles, tables, figures = [], [], []
    seen_t, seen_f = set(), set()
    seen_tab = {}  # table_id -> {page, hf, title}

    with pdfplumber.open(pdf_path) as pdf:
        total = len(pdf.pages)
        for pno, page in enumerate(pdf.pages, 1):
            txt = page.extract_text() or ""
            lines = txt.split("\n")
            n = len(lines)
            for i, raw in enumerate(lines):
                s = raw.strip()
                if not s:
                    continue
                hf = (i == 0) or (i >= n - 2)  # 页眉/页脚区，用于表去重

                mt = tp.match(s)
                if mt:
                    tid = f"表{ch_s}.{mt.group(1)}-{mt.group(2)}"
                    title = mt.group(3).strip()
                    if tid not in seen_tab:
                        seen_tab[tid] = {"page": pno, "hf": hf, "title": title}
                    elif (not hf) and seen_tab[tid]["hf"]:
                        seen_tab[tid] = {"page": pno, "hf": False, "title": title}
                    continue

                mf = fp.match(s)
                if mf:
                    fid = f"图{mf.group(1)}.{mf.group(2)}-{mf.group(3)}"
                    if fid not in seen_f:
                        seen_f.add(fid)
                        figures.append({"fig_id": fid, "title": mf.group(4).strip(), "page": pno})
                    continue

                # 标题剩余文本必须含中文（环评节标题必含中文），滤掉 "7.5 20 40 60..." 等数字串假阳性
                if l4.match(s):
                    g = l4.match(s)
                    if _title_rest_ok(s, g.end()):
                        _add_title(seen_t, titles, f"{ch_s}.{g.group(1)}.{g.group(2)}.{g.group(3)}", 4, s[g.end():].strip(), pno)
                    continue
                if l3.match(s):
                    g = l3.match(s)
                    if _title_rest_ok(s, g.end()):
                        _add_title(seen_t, titles, f"{ch_s}.{g.group(1)}.{g.group(2)}", 3, s[g.end():].strip(), pno)
                    continue
                if l2.match(s):
                    g = l2.match(s)
                    if _title_rest_ok(s, g.end()):
                        _add_title(seen_t, titles, f"{ch_s}.{g.group(1)}", 2, s[g.end():].strip(), pno)
                    continue
                if l1.match(s):
                    g = l1.match(s)
                    if _title_rest_ok(s, g.end()):
                        _add_title(seen_t, titles, ch_s, 1, s[g.end():].strip(), pno)
                    continue

    tables = [dict(v, table_id=k) for k, v in seen_tab.items()]
    tables.sort(key=lambda t: t["page"])
    titles.sort(key=lambda t: t["page"])
    figures.sort(key=lambda t: t["page"])
    return titles, tables, figures, total


def _add_title(seen, out, num, level, title, page):
    if num in seen:
        return
    seen.add(num)
    out.append({"num": num, "level": level, "title": title, "page": page})


def _title_rest_ok(s, end):
    """标题剩余文本须含中文（环评节标题必含中文），否则视为数字串/刻度假阳性。"""
    rest = s[end:].strip()
    return bool(re.search(r'[一-鿿]', rest))


# ---------- 分段 + 分组 ----------
def segmentize(titles, seg_end, cut_level, max_pages):
    """在 titles 中取 cut_level 级的标题作切分口，返回原子段列表。
    若某段 >max_pages 且存在 cut_level+1 级子标题，则下钻细分（递归）。
    seg_end: 该层级的结束页（末段 end 上限）。
    """
    cands = sorted([t for t in titles if t["level"] == cut_level], key=lambda t: t["page"])
    segs = []
    for i, t in enumerate(cands):
        start = t["page"]
        end = (cands[i + 1]["page"] - 1) if i + 1 < len(cands) else seg_end
        end = max(end, start)
        span = end - start + 1
        if span > max_pages and cut_level < 4:
            kids = [k for k in titles if k["level"] == cut_level + 1 and start <= k["page"] <= end]
            if kids:
                segs.extend(segmentize(kids, end, cut_level + 1, max_pages))
                continue
        segs.append({"num": t["num"], "level": t["level"], "title": t["title"], "start": start, "end": end})
    return segs


def propose(titles, tables, total, max_pages, overlap):
    segs = segmentize(titles, total, 3, max_pages)  # 默认切分口 = h3
    if not segs:
        raise SystemExit("[ERR] 未探测到任何 h2/h3 标题，无法拆分")
    subs, cur, cur_start = [], [], None
    for seg in segs:
        if not cur:
            cur, cur_start = [seg], seg["start"]
            continue
        if seg["end"] - cur_start + 1 > max_pages:
            subs.append(_build_sub(cur, cur_start, overlap, total, tables))
            cur, cur_start = [seg], seg["start"]
        else:
            cur.append(seg)
    if cur:
        subs.append(_build_sub(cur, cur_start, overlap, total, tables))
    return subs


def _build_sub(cur, cur_start, overlap, total, tables):
    first, last = cur[0], cur[-1]
    pdf_start = max(1, first["start"] - overlap)
    pdf_end = min(total, last["end"] + overlap)
    owned_start, owned_end = first["start"], last["end"]
    cnt = sum(1 for t in tables if owned_start <= t["page"] <= owned_end)
    scope = [s["num"] for s in cur]
    scope_title = " / ".join(f'{s["num"]} {s["title"]}' for s in cur)
    return {
        "scope": scope,
        "scope_title": scope_title,
        "owned_range": [owned_start, owned_end],
        "pdf_range": [pdf_start, pdf_end],
        "pages": pdf_end - pdf_start + 1,
        "table_count": cnt,
    }


def print_review(subs, max_pages, overlap, total):
    print(f"\n{'='*78}")
    print(f"大章拆 sub 审查表  (max_pages={max_pages}, overlap={overlap}, 总页数={total})")
    print(f"{'='*78}")
    print(f"{'sub':<6}{'小节范围':<22}{'页数(含overlap)':<20}{'表格数(估)':<10}")
    print("-" * 78)
    for i, s in enumerate(subs, 1):
        rng = s["scope"][0] if len(s["scope"]) == 1 else f'{s["scope"][0]}–{s["scope"][-1]}'
        pg = f'p{s["pdf_range"][0]}–{s["pdf_range"][1]} ({s["pages"]}页)'
        flag = " ⚠>max" if s["pages"] > max_pages else ""
        print(f"sub{i:<4}{rng:<22}{pg:<20}{s['table_count']:<10}{flag}")
    print("-" * 78)
    print(f"共 {len(subs)} 个 sub | 注：表格数为 PDF 标题扫描估值，权威数以 extract 表普查为准")
    print(f"{'='*78}\n")


def write_plan(work_dir, subs, cfg, max_pages, overlap, total):
    plan = {
        "generated_at": str(date.today()),
        "project": cfg["project"],
        "chapter": cfg["chapter"],
        "chapter_title": cfg["chapter_title"],
        "pdf_path": cfg["pdf_path"],
        "total_pages": total,
        "max_pages": max_pages,
        "overlap": overlap,
        "cut_level": 3,
        "subs": subs,
    }
    path = os.path.join(work_dir, "split_plan.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)
    return path


# ---------- Phase 2: 切 PDF + 建 sub 工程 ----------
def execute_split(work_dir, cfg):
    from pypdf import PdfReader, PdfWriter
    plan_path = os.path.join(work_dir, "split_plan.json")
    if not os.path.exists(plan_path):
        raise SystemExit(f"[ERR] 找不到 {plan_path}，请先跑 --phase propose 并审核")
    plan = json.load(open(plan_path, encoding="utf-8"))
    subs = plan["subs"]
    reader = PdfReader(cfg["pdf_path"])
    total = len(reader.pages)
    project = cfg["project"]
    ch = cfg["chapter"]
    ch_title = cfg["chapter_title"]
    today = str(date.today())
    print(f"按 split_plan.json 切 {len(subs)} 个 sub …")
    for i, sub in enumerate(subs, 1):
        subdir = os.path.join(work_dir, f"sub{i}")
        for d in ("data", "code", "output"):
            os.makedirs(os.path.join(subdir, d), exist_ok=True)
        ps, pe = sub["pdf_range"]
        ps = max(1, ps); pe = min(total, pe)
        writer = PdfWriter()
        for p in range(ps - 1, pe):
            writer.add_page(reader.pages[p])
        rng = f'{sub["scope"][0]}-{sub["scope"][-1]}'
        pdf_name = f'{project}_{i}_{rng}.pdf'
        pdf_out = os.path.join(work_dir, pdf_name)
        with open(pdf_out, "wb") as f:
            writer.write(f)
        py = {
            "project": f"{project}_sub{i}",
            "pdf_path": pdf_out,
            "chapter": ch,
            "chapter_title": ch_title,
            "scope_sections": sub["scope"],
            "scope_title": sub["scope_title"],
            "format": cfg.get("format", "flat"),
            "table_mode": cfg.get("table_mode", "pdf_census"),
            "render_reviewed": False,
            "work_dir": subdir + "/",
            "status": "initialized",
            "created_at": today,
            "pipeline": ["init: done", "parse: pending", "extract: pending",
                         "render: pending", "verify: pending", "to-py: pending",
                         "generate: pending", "report: pending"],
        }
        with open(os.path.join(subdir, "project.yaml"), "w", encoding="utf-8") as f:
            yaml.safe_dump(py, f, allow_unicode=True, sort_keys=False)
        print(f"  sub{i}: p{ps}–{pe} ({pe-ps+1}页) -> {pdf_name}  scope={sub['scope']}")
    print(f"完成：{len(subs)} 个 sub 工程建于 {work_dir}")


# ---------- 入口 ----------
def main():
    ap = argparse.ArgumentParser(description="大章拆 sub（init 后 / extract 前）")
    ap.add_argument("--work-dir", required=True)
    ap.add_argument("--phase", choices=["propose", "split"], required=True)
    ap.add_argument("--pdf")
    ap.add_argument("--chapter", type=int)
    ap.add_argument("--chapter-title")
    ap.add_argument("--project")
    ap.add_argument("--max-pages", type=int, default=30)
    ap.add_argument("--overlap", type=int, default=2)
    ap.add_argument("--cut-level", type=int, default=3, help="切分口层级(2=h2/3=h3/4=h4)，默认3；propose 用")
    args = ap.parse_args()

    os.makedirs(args.work_dir, exist_ok=True)
    cfg = load_cfg(args.work_dir, args)

    if args.phase == "propose":
        titles, tables, figures, total = probe(cfg["pdf_path"], cfg["chapter"])
        if args.cut_level != 3:
            subs = _propose_with_level(titles, tables, total, args.cut_level, args.max_pages, args.overlap)
        else:
            subs = propose(titles, tables, total, args.max_pages, args.overlap)
        print_review(subs, args.max_pages, args.overlap, total)
        path = write_plan(args.work_dir, subs, cfg, args.max_pages, args.overlap, total)
        print(f"方案已写：{path}  （审核/微调后跑 --phase split）")
    else:
        execute_split(args.work_dir, cfg)


def _propose_with_level(titles, tables, total, cut_level, max_pages, overlap):
    segs = segmentize(titles, total, cut_level, max_pages)
    subs, cur, cur_start = [], [], None
    for seg in segs:
        if not cur:
            cur, cur_start = [seg], seg["start"]; continue
        if seg["end"] - cur_start + 1 > max_pages:
            subs.append(_build_sub(cur, cur_start, overlap, total, tables))
            cur, cur_start = [seg], seg["start"]
        else:
            cur.append(seg)
    if cur:
        subs.append(_build_sub(cur, cur_start, overlap, total, tables))
    return subs


if __name__ == "__main__":
    main()
