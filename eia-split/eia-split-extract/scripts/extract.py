# -*- coding: utf-8 -*-
"""extract.py — 环评章节内容提取(参数化)。基于 structure.json + clean.txt 生成 chapter.yaml。
表数据已在 all_tables_pdf.json(表普查), 此处只引用 table_id。段落按标题行范围抽取(跳过标题行本身)。

【段落精修】(固化 ch5): extract_paragraphs 按句末标点(。！？")合并 + clean_page_number 清嵌入页码,
  取代简单拼接, 提升喂给 LLM 的文本质量。
【figure 节点】(固化 ch5): 图作为独立 prompt 节点(type=figure), 由 render 兜底、generate 跳过 LLM。
【scope 防御过滤】(固化 ch4/ch5): 若 project.yaml 含 scope_sections(且 parse 已裁 structure), 再保险只留
  scope 树内 section, 保证零冗余。
【跨章引用校验】(ch6): 正文引用的【本章前缀】表号须在本章表清单内, 跨章引用(如上溯第5章)正常不报。

用法: python3 extract.py --work-dir <dir>
"""
import os, re, json, argparse, yaml


def load_yaml(p):
    return yaml.safe_load(open(p, encoding="utf-8"))


def clean_page_number(line):
    line = re.sub(r"^\s*\d{1,3}(?=[一-龥])", "", line)
    line = re.sub(r"([一-龥])\d{1,3}\s*$", r"\1", line)
    return line.strip()


def extract_paragraphs(lines, start, end):
    """取 lines[start-1:end] 段落, 清嵌入页码, 按句末标点合并成句; 返回段落列表。"""
    if end < start:
        return []
    raw = [clean_page_number(l) for l in lines[start - 1:end]]
    raw = [r for r in raw if r]
    if not raw:
        return []
    paras, cur = [], ""
    for line in raw:
        if cur and not cur.endswith(("。", "！", "？", "”")):
            cur += line
        else:
            if cur:
                paras.append(cur)
            cur = line
    if cur:
        paras.append(cur)
    merged = []
    for p in paras:
        if merged and len(p) <= 4 and not p.endswith("。"):
            merged[-1] += p
        else:
            merged.append(p)
    return merged


def mk_para(prefix, num, title, sec_id, has_h2, a, b, paras):
    text = "\n".join(paras) if isinstance(paras, list) else paras
    paras = paras if isinstance(paras, list) else [paras]
    return {"var": f"{prefix}_{num.replace('.', '_') if num else sec_id}_text", "num": num, "title": title,
            "type": "paragraph", "section": sec_id, "has_h1": False, "has_h2": has_h2,
            "is_leaf": False, "txt_lines": [a + 1, b], "paragraphs": paras, "conclusion": None, "image_ref": None}


def mk_tbl(prefix, sec_id, tbl):
    # table_title 存完整(表号+标题文字), 从 structure 的 table.title 取, 不从 JSON 漏存
    full_title = "表" + tbl["table_id"] + ((" " + tbl["title"]) if tbl.get("title") else "")
    return {"var": f"{prefix}_{sec_id.replace('.', '_')}_{tbl['table_id'].replace('.', '_')}_tab",
            "num": None, "title": tbl["title"], "type": "table", "section": sec_id,
            "has_h2": False, "txt_lines": [tbl["line"], tbl.get("end_line", tbl["line"])],
            "table_title": full_title, "fields": [], "rows": [], "merge_first_col": False}


def mk_fig(prefix, sec_id, t):
    fid = t.get("fig_id") or t.get("num")
    return {"var": f"{prefix}_figure_{fid.replace('.', '_').replace('-', '_')}",
            "num": fid, "title": t.get("title", ""), "type": "figure", "section": sec_id,
            "has_h2": False, "txt_lines": [t["line"], t["line"]], "figure_id": fid,
            "figure_title": t.get("title", ""), "paragraphs": [], "conclusion": None, "image_ref": fid}


def build(work_dir):
    cfg = load_yaml(os.path.join(work_dir, "project.yaml"))
    ch = cfg["chapter"]; prefix = cfg["project"]
    data_dir = os.path.join(work_dir, "data")
    structure = json.load(open(os.path.join(data_dir, "structure.json"), encoding="utf-8"))
    lines = open(structure["txt_path"], encoding="utf-8").read().split("\n")
    titles = sorted(structure["titles"], key=lambda t: t["line"])
    tables = structure.get("tables", [])
    figures = structure.get("figures", [])
    h1 = next((t for t in titles if t["level"] == 1), None)
    h2_list = [t for t in titles if t["level"] == 2]
    sections = []

    # 全章引言: h1 行之后 到 第一个 h2 之前 (PDF 中 h1 与 h2 间的段落, 如 ch6 的"总体来看...")
    if h1:
        first_h2_line = h2_list[0]["line"] if h2_list else len(lines) + 1
        intro = extract_paragraphs(lines, h1["line"], first_h2_line - 1)
        if intro:
            sections.append({
                "id": h1["num"], "title": h1["title"], "is_intro": True,
                "prompts": [{
                    "var": f"{prefix}_{h1['num']}_intro_text", "num": None, "title": None,
                    "type": "paragraph", "section": h1["num"], "has_h1": False, "has_h2": False,
                    "is_leaf": False, "txt_lines": [h1["line"] + 1, first_h2_line],
                    "paragraphs": intro, "conclusion": None, "image_ref": None}]})

    for h2 in h2_list:
        sec_id = h2["num"]; h2l = h2["line"]
        nxt = next((t["line"] for t in h2_list if t["line"] > h2l), len(lines) + 1)
        sec_titles = [t for t in titles if h2l < t["line"] < nxt and t["level"] >= 3]
        sec_tables = [t for t in tables if h2l < t["line"] < nxt]
        sec_figs = [t for t in figures if h2l < t["line"] < nxt]
        events = []
        for t in sec_titles:
            events.append((t["line"], "t", t))
        for t in sec_tables:
            events.append((t["line"], "tbl", t))
        for t in sec_figs:
            events.append((t["line"], "fig", t))
        events.sort()
        prompts = []
        lead_end = events[0][0] if events else nxt
        # h2 引言: h2 行之后 到 首个 h3/表/图 之前
        lead = extract_paragraphs(lines, h2l, lead_end - 1)
        if lead:
            prompts.append(mk_para(prefix, None, h2["title"], sec_id, True, h2l, lead_end - 1, lead))
        h3_list = [t for t in sec_titles if t["level"] == 3]
        if not h3_list:
            for (ln, k, nd) in events:
                if k == "tbl":
                    prompts.append(mk_tbl(prefix, sec_id, nd))
                elif k == "fig":
                    prompts.append(mk_fig(prefix, sec_id, nd))
        else:
            for hi, h3 in enumerate(h3_list):
                h3l = h3["line"]
                h3_end = next((t["line"] for t in h3_list if t["line"] > h3l), nxt)
                h4_list = [t for t in sec_titles if t["level"] >= 4 and h3l < t["line"] < h3_end]
                h3_lead_end = h4_list[0]["line"] if h4_list else h3_end
                h3_lead = extract_paragraphs(lines, h3l - 1, h3_lead_end - 1)
                node = mk_para(prefix, h3["num"], h3["title"], sec_id, hi == 0, h3l - 1, h3_lead_end - 1, h3_lead)
                # h3 下直接是 h4 子节且无独立正文 -> 空壳节点: 标记 is_section_header, render 只发<h3>不发空<p>
                if h4_list and not h3_lead:
                    node["is_section_header"] = True
                if h4_list:
                    sub4 = []
                    for h4 in h4_list:
                        h4_end = next((t["line"] for t in h4_list if t["line"] > h4["line"]), h3_end)
                        h4_txt = extract_paragraphs(lines, h4["line"], h4_end - 1)
                        sub4.append(mk_para(prefix, h4["num"], h4["title"], h4["num"], False, h4["line"] - 1, h4_end - 1, h4_txt))
                    node["sub4"] = sub4
                prompts.append(node)
                for t in sec_tables:
                    if h3l < t["line"] < h3_end:
                        prompts.append(mk_tbl(prefix, sec_id, t))
                for t in sec_figs:
                    if h3l < t["line"] < h3_end:
                        prompts.append(mk_fig(prefix, sec_id, t))
        sections.append({"id": sec_id, "title": h2["title"], "prompts": prompts})

    # 交叉引用校验: 正文里引用的【本章前缀】表号必须在本章表清单内, 否则报警。
    # 跨章引用(如第6章引用 表5.3-2)是正常上溯, 不报警。
    valid_ids = {t["table_id"] for t in tables}
    ch_prefix = f"{ch}."
    for s in sections:
        for p in s["prompts"]:
            if p["type"] == "paragraph":
                for ref in re.findall(r"表\s*(\d+\.\d+-\d+)", p.get("text", "")):
                    if ref.startswith(ch_prefix) and ref not in valid_ids:
                        print(f"  ⚠ 跨章引用缺失: {ref} 不在本章表清单(可能属邻 sub, 合并时需对齐)")

    # scope 防御过滤(parse 已裁 structure, 此处再保险)
    scope = cfg.get("scope_sections") or []
    if scope:
        scope_set = set(scope)
        allowed = set(scope_set)
        for _sc in scope_set:
            _ps = _sc.split(".")
            for k in range(1, len(_ps)):
                allowed.add(".".join(_ps[:k]))
        sections = [s for s in sections if s["id"] in allowed]

    chapter = {
        "chapter": cfg["chapter"], "chapter_title": cfg["chapter_title"],
        "project": prefix, "format": cfg.get("format", "flat"),
        "scope_sections": scope, "sections": sections,
    }
    yaml.safe_dump(chapter, open(os.path.join(data_dir, "chapter.yaml"), "w", encoding="utf-8"),
                   allow_unicode=True, sort_keys=False)

    n_h = sum(1 for s in sections for p in s["prompts"] if p["type"] == "paragraph" and p.get("num"))
    n_tab = sum(1 for s in sections for p in s["prompts"] if p["type"] == "table")
    n_fig = sum(1 for s in sections for p in s["prompts"] if p["type"] == "figure")
    n_intro = sum(1 for s in sections for p in s["prompts"] if p.get("is_intro") or p.get("has_h2"))
    print(f"✅ extract 完成: sections={len(sections)} H段落={n_h} 表={n_tab} 图={n_fig} (含intro/h2lead={n_intro})")
    for s in sections:
        print(f"  {s['id']}: {len(s['prompts'])} prompts")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-dir", required=True)
    build(ap.parse_args().work_dir)
