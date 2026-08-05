# -*- coding: utf-8 -*-
"""eia-split-render: 参数化渲染脚本 (通用模板, 新项目直接复用)。
从 chapter.yaml 渲染 HTML (无 LLM): 表格数据从 all_tables_pdf.json(表普查产物)
按 table_id 确定性取数, 渲染为带完整数据的 <table>; 同时产出
output/chapter{N}_tables.json (每表 HTML 片段映射) 供 to-py 消费。
递归渲染 sub4/children 为 h4/h5...; 表格标题用 <p class="caption"> 不用 h4。

用法:
  python3 render.py --work-dir <dir>
项目专属 hainan_ch2 的 data/render.py 即基于此模板 (仅 WORK_DIR 硬编码为项目路径)。

经验/坑 (已固化):
  - 退化单行表(txt兜底常见整行挤一行): 整行作数据, 表头用通用列名, 避免空表。
  - 表尾粘连正文(txt 启发式抽表把下一行段落吸进末行): 在表普查侧按表头宽度截断,
    此处 render 不复核, 信任 all_tables_pdf.json 已干净。
  - 表格标题必须用 <p class="caption">, 不能用 h4 (h4 留给四级小节 2.x.x.x)。
"""
import argparse
import json
import os
import re
import yaml
from bs4 import BeautifulSoup

DEFAULT_WORK = os.getcwd()


def derive_tid(prompt):
    tid = prompt.get("table_id")
    if tid:
        return tid
    m = re.search(r'表\s*([\d.]+)-(\d+)', prompt.get("table_title", ""))
    return f"表{m.group(1)}-{m.group(2)}" if m else None


def build_table_html(fields, data, merge=False):
    header = "  <tr>" + "".join(f"<th>{f}</th>" for f in fields) + "</tr>"
    parts = []
    if merge and len(fields) >= 2 and data:
        i = 0
        while i < len(data):
            span = 1
            while i + span < len(data) and data[i + span][0] == data[i][0]:
                span += 1
            cells = f'  <tr><td rowspan="{span}">{data[i][0]}</td>'
            for j in range(1, len(fields)):
                val = data[i][j] if j < len(data[i]) else ""
                cells += f"<td>{val}</td>"
            cells += "</tr>"
            parts.append(cells)
            for k in range(1, span):
                cells = "  <tr>"
                for j in range(1, len(fields)):
                    val = data[i + k][j] if j < len(data[i + k]) else ""
                    cells += f"<td>{val}</td>"
                cells += "</tr>"
                parts.append(cells)
            i += span
    else:
        for row in data:
            parts.append("  <tr>" + "".join(
                f"<td>{row[j] if j < len(row) else ''}</td>" for j in range(len(fields))) + "</tr>")
    return (f'<table border="1" style="width:100%; border-collapse:collapse; font-size:12px;">\n'
            f'{header}\n' + "\n".join(parts) + "\n</table>")


def detect_image_ref(texts):
    """从段落文本检测首个图号(如 '图4.1-1')。"""
    pat = re.compile(r'图\s*(\d+\.\d+-\d+)')
    for t in texts:
        m = pat.search(t)
        if m:
            return f"图{m.group(1)}"
    return None


def build_image_titles(texts):
    """全章(clean.txt 全文/段落)扫描建立 图号 -> 图标题 映射。
    优先括号标题(图4.1-1（XXX）)；其次只认「行首以图号开头」的图标题行
    (图4.1-9马村港附近海域...)，排除'统计/显示/如下'等内联引用套话。"""
    titles = {}
    pat_paren = re.compile(r'图\s*(\d+\.\d+-\d+)\s*[（(]\s*([^）)]+?)\s*[）)]')
    pat_title = re.compile(r'图\s*(\d+\.\d+-\d+)\s*([^。\n；;（(]{2,30})')
    stop = ("统计", "显示", "如下", "见下", "如上", "详见", "所示")
    for t in texts:
        m = pat_paren.search(t)
        if m:
            titles[f"图{m.group(1)}"] = m.group(2).strip()
            continue
        if t.strip().startswith("图"):
            m = pat_title.search(t)
            if m:
                title = m.group(2).strip()
                if title[:2] not in stop and not title.startswith("）"):
                    titles.setdefault(f"图{m.group(1)}", title)
    return titles


def render_para_node(prompt, chapter_data, section, is_first=False, level=None, image_titles=None):
    parts = []
    # 空壳 h3 节点(h3 下直接是 h4 子节, 无独立正文): 只发标题, 不发空 <p>, 但仍渲染 sub4
    if prompt.get("is_section_header"):
        num = prompt.get("num", "")
        lvl = level if level else (len(num.split('.')) if num else 3)
        if num:
            parts.append(f'<h{lvl}>{num} {prompt.get("title", "")}</h{lvl}>')
        for child in (prompt.get("sub4") or []):
            parts.append(render_para_node(child, chapter_data, section, is_first=False, level=lvl + 1,
                                          image_titles=image_titles))
        return "\n".join(parts)
    num = prompt.get("num", "")
    title = prompt.get("title", "")
    if is_first and prompt.get("has_h1"):
        parts.append(f'<h1>第{chapter_data["chapter"]}章 {chapter_data["chapter_title"]}</h1>')
    if is_first:
        # section 标题级别按 id 段数动态定级 (5.1→h2, 5.4.2→h3, 5.4.2.1→h4); 勿硬写h2
        _sid = section.get("id", "")
        _slevel = len(_sid.split('.')) if _sid else 2
        _slevel = max(2, min(_slevel, 6))
        parts.append(f'<h{_slevel}>{_sid} {section["title"]}</h{_slevel}>')
    if num or title:
        # 顶层标题级别由 num 组件数决定(4.3.1→h3, 4.3.2.1→h4); 无编号引段落(title 仅作 section 标题已由 is_first 发射)只渲染正文, 不发 hN
        if num:
            lvl = level if level else len(num.split('.'))
            parts.append(f'<h{lvl}>{num} {title}</h{lvl}>')
        elif title and not is_first:
            # 非首节点且有 title(极少见): 兜底发 h3 避免正文裸奔
            parts.append(f'<h3>{title}</h3>')
    # 无 num 且无 title 的纯引言段落: 仅正文(p), 标题由 section 标题承担
    for para in prompt.get("paragraphs", []):
        parts.append(f'<p style="text-indent:2em;">{para}</p>')
    if prompt.get("conclusion"):
        parts.append(f'<p style="text-indent:2em;"><span style="color:blue;">{prompt["conclusion"]}</span></p>')
    ref = prompt.get("image_ref")
    img = ref or detect_image_ref(prompt.get("paragraphs", []))
    ftitle = (image_titles or {}).get(img, "") if img else ""
    if img and not ftitle:
        # 仅内联引用且无独立图标题行时才渲染占位(无标题版);
        # 有独立图标题行时由 figure 节点统一渲染(避免重复)
        if img not in (image_titles or {}):
            parts.append('<div class="image-placeholder" style="border:1px dashed #999; padding:1em; '
                         'text-align:center; color:#666; margin:1em 0;">'
                         f'[图片占位：{img} — 请人工补充]</div>')
    for child in (prompt.get("sub4") or []):
        parts.append(render_para_node(child, chapter_data, section, is_first=False, level=lvl + 1,
                                      image_titles=image_titles))
    return "\n".join(parts)


def render_table(prompt, tables_pdf):
    tid = derive_tid(prompt)
    title = prompt.get("table_title", tid or "")
    entry = tables_pdf.get(tid) if tid else None
    # caption 补充完整标题: 若 table_title 仅表号(无标题文字), 用 all_tables_pdf.json 的 title 补全
    if entry and entry.get("title") and title.strip() == tid:
        title = tid + " " + entry["title"]
    caption = f'<p class="caption" style="text-align:center;">{title}</p>'
    if entry and entry.get("rows"):
        rows = entry["rows"]
        if entry.get("fields"):
            fields, data = entry["fields"], rows[1:]
        elif len(rows) >= 2:
            fields, data = rows[0], rows[1:]
        else:
            fields = [f"列{i+1}" for i in range(len(rows[0]))]
            data = rows
        return caption + "\n" + build_table_html(fields, data, prompt.get("merge_first_col", False))
    fields = prompt.get("fields") or [tid or "表"]
    n = len(fields)
    empty = (f'<table border="1" style="width:100%; border-collapse:collapse; font-size:12px;">\n'
             f'  <tr>' + "".join(f"<th>{f}</th>" for f in fields) + "</tr>\n"
             f'  <tr><td colspan="{n}">未提取，请人工补充</td></tr>\n</table>')
    return caption + "\n" + empty


def count_sub4(prompt):
    n = 0
    for c in (prompt.get("sub4") or []):
        n += 1 + count_sub4(c)
    return n


def compute_expected(ch):
    h2 = h3 = h4 = 0
    # section 标题级别按 id 段数定 (5.1→h2, 5.4.2→h3, 5.4.2.1→h4); 子项目按切分口层级
    for s in ch["sections"]:
        if s.get("is_intro"):
            continue  # 全章引言段不发射独立标题, 标题由章节框架承担
        _sid = s.get("id", "")
        _lv = len(_sid.split('.')) if _sid else 2
        if _lv == 2:
            h2 += 1
        elif _lv == 3:
            h3 += 1
        elif _lv >= 4:
            h4 += 1
        # _lv==1 (章号, 仅 intro) 跳过
    for s in ch["sections"]:
        for p in s["prompts"]:
            if p["type"] == "paragraph" and p.get("num"):
                comps = len(p["num"].split('.'))
                if comps == 3:
                    h3 += 1
                elif comps >= 4:
                    h4 += 1
            # 仍支持旧式嵌套 sub4 (sub1 等)
            h4 += count_sub4(p)
    tables = sum(1 for s in ch["sections"] for p in s["prompts"] if p["type"] == "table")
    # 每章必有 1 个 h1 框架标题(render 无条件注入)
    h1 = 1
    return {"h1": h1, "h2": h2, "h3": h3, "h4": h4, "tables": tables}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-dir", default=DEFAULT_WORK)
    args = ap.parse_args()
    wd = os.path.abspath(args.work_dir)
    data_dir = os.path.join(wd, "data")
    out_dir = os.path.join(wd, "output")
    os.makedirs(out_dir, exist_ok=True)

    ch = yaml.safe_load(open(os.path.join(data_dir, "chapter.yaml"), encoding="utf-8"))
    # 表数据放在 code/ (与 to-py 同目录, 自包含)
    code_dir = os.path.join(wd, "code")
    tables_path = os.path.join(code_dir, "all_tables_pdf.json")
    if not os.path.exists(tables_path):
        tables_path = os.path.join(data_dir, "all_tables_pdf.json")  # 降级兼容
    tables_pdf = json.load(open(tables_path, encoding="utf-8"))

    parts = []
    table_map = {}
    # 图标题可能落在表行范围内被 extract 吞掉, 故直接扫 clean.txt 全文建立映射
    clean_path = os.path.join(data_dir, f"chapter{ch['chapter']}-clean.txt")
    if os.path.exists(clean_path):
        raw_lines = open(clean_path, encoding="utf-8").read().split("\n")
        image_titles = build_image_titles(raw_lines)
    else:
        all_paras = [p for s in ch["sections"] for pr in s["prompts"] for p in pr.get("paragraphs", [])]
        image_titles = build_image_titles(all_paras)
    for section in ch["sections"]:
        is_intro = section.get("is_intro", False)
        for idx, prompt in enumerate(section["prompts"]):
            if prompt["type"] == "paragraph":
                # 全章引言(section.is_intro): 只渲染正文 p, 不发射 h1/h2 标题(标题由章节框架承担)
                _is_first = (idx == 0) and not is_intro
                parts.append(render_para_node(prompt, ch, section, is_first=_is_first,
                                              image_titles=image_titles))
            elif prompt["type"] == "figure":
                cap = (f'{prompt["figure_id"]} {prompt.get("figure_title", "")}'.strip())
                parts.append('<div class="image-placeholder" style="border:1px dashed #999; padding:1em; '
                             'text-align:center; color:#666; margin:1em 0;">'
                             f'[图片占位：{cap} — 请人工补充]</div>')
            elif prompt["type"] == "table":
                if idx == 0:
                    _sid = section.get("id", "")
                    _slevel = len(_sid.split('.')) if _sid else 2
                    _slevel = max(2, min(_slevel, 6))
                    parts.append(f'<h{_slevel}>{_sid} {section["title"]}</h{_slevel}>')
                html = render_table(prompt, tables_pdf)
                parts.append(html)
                tid = derive_tid(prompt)
                if tid:
                    table_map[tid] = html

    ch_no = ch["chapter"]
    body = "\n\n".join(parts)
    h1_tag = f'<h1>第{ch_no}章 {ch["chapter_title"]}</h1>'
    html_doc = ('<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n'
                '<meta charset="utf-8">\n'
                f'<title>第{ch_no}章 {ch["chapter_title"]}</title>\n'
                '<style>body{font-family:"Microsoft YaHei","PingFang SC",sans-serif;'
                'max-width:960px;margin:auto;padding:1em;line-height:1.8;</style>\n'
                '</head>\n<body>\n' + h1_tag + "\n\n" + body + '\n</body>\n</html>')
    open(os.path.join(out_dir, f"chapter{ch_no}.html"), "w", encoding="utf-8").write(html_doc)
    # 片段映射写到 code/ (to-py getter 从 code/ 读)
    json.dump(table_map, open(os.path.join(code_dir, f"chapter{ch_no}_tables.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    exp = compute_expected(ch)
    soup = BeautifulSoup(h1_tag + "\n\n" + "\n".join(parts), "html.parser")
    got = {t: len(soup.find_all(t)) for t in ["h1", "h2", "h3", "h4"]}
    got["tables"] = len(soup.find_all("table"))
    ok = all(got[t] == exp[t] for t in exp)
    print(f"✅ render 完成: HTML + chapter{ch_no}_tables.json (表 {len(table_map)} 张)")
    print(f"   层级 expected={exp} got={got} -> {'PASS' if ok else 'FAIL'}")
    if not ok:
        raise SystemExit("层级不符, 检查 chapter.yaml / all_tables_pdf.json")


if __name__ == "__main__":
    main()
