# -*- coding: utf-8 -*-
"""eia-split-to-py 通用生成器: 依据 sub 的 chapter.yaml 生成三件套 .py 到 code/。
表格 getter 返回 render 预渲染片段(code/chapter{N}_tables.json); 仅段落经 LLM。
用法: python3 gen_three_py.py --work-dir <sub_dir>
"""
import os, re, json, argparse, yaml


def load_yaml(p):
    return yaml.safe_load(open(p, encoding="utf-8"))


def tbl_id_from_title(title):
    m = re.search(r'表\s*([\d.]+)-(\d+)', title or "")
    return m.group(1) + "-" + m.group(2) if m else None


def build_prompt(num, title, lvl, has_h1, has_h2, sec_id, sec_title, body, conclusion, chapter, chapter_title):
    ref = body if body else ""
    reqs = []
    n = 1
    if has_h1:
        reqs.append(f'{n}. 必须包含章节 h1 标题: "\\n\\n<h1>第{chapter}章 {chapter_title}</h1>\\n\\n"')
        n += 1
    if has_h2:
        # section 标题级别按 sec_id 段数动态定 (5.1→h2, 5.4.2→h3, 5.4.2.1→h4), 勿硬 h2
        _slvl = len(sec_id.split('.')) if sec_id else 2
        _slvl = max(2, min(_slvl, 6))
        reqs.append(f'{n}. 必须包含章节 h{_slvl} 标题: "\\n\\n<h{_slvl}>{sec_id} {sec_title}</h{_slvl}>\\n\\n"')
        n += 1
    # num/title 可能为 None (如无编号的引导段落, 由 section 标题承载) -> 用空串避免 TypeError
    _num = num or ""
    _title = title or ""
    if _num or _title:
        reqs.append(f'{n}. 必须包含章节 h{lvl} 标题: "\\n\\n<h{lvl}>{_num} {_title}</h{lvl}>\\n\\n"')
        n += 1
        if body:
            reqs.append(f'{n}. {lvl} 标题下包含以下正文内容（可适当润色，保持事实与数据与参考一致）: \\n\\n{body}\\n\\n')
        else:
            reqs.append(f'{n}. 即使无独立正文，也必须单独、原样保留 <h{lvl}>{_num} {_title}</h{lvl}> 标题行，不得省略。')
        n += 1
    else:
        # 无编号段落: 仅生成正文, 不重复标题 (标题由 render 的 section 标题承担)
        if body:
            reqs.append(f'{n}. 本段无独立编号标题，直接生成以下正文内容（可适当润色，保持事实与数据一致）: \\n\\n{body}\\n\\n')
            n += 1
    reqs.append(f'{n}. 正文用 <p style="text-indent:2em;">正文</p> 包裹；结论性内容用 <span style="color:blue;">结论</span>。每个标题只出现一次，body 不含"编号 标题"前缀。')
    reqs_text = "\n".join(reqs)
    example = f'<h{lvl}>{_num} {_title}</h{lvl}>\n<p style="text-indent:2em;">（此处为生成的正文，保持与参考内容一致的事实与数据）</p>' if (_num or _title) else '<p style="text-indent:2em;">（此处为生成的正文）</p>'
    if conclusion:
        example += f'\n<span style="color:blue;">{conclusion}</span>'
    tpl = ('你是一个word内容生成专家，请根据我给你的参考内容一步一步思考生成 __NUM__ __TITLE__ 的内容。\n'
           '我给你的参考内容是：【__REF__】\n'
           '要求：\n__REQS__\n'
           '下面是一个输出参考示例:"""\n__EXAMPLE__\n"""')
    return (tpl.replace("__NUM__", _num).replace("__TITLE__", _title)
             .replace("__REF__", ref).replace("__REQS__", reqs_text)
             .replace("__EXAMPLE__", example))


def walk(section_prompts, sec_id, sec_title, chapter, chapter_title, prefix, specs, counters):
    for idx, node in enumerate(section_prompts):
        if not isinstance(node, dict):
            continue
        t = node.get("type")
        if t == "paragraph":
            num = node.get("num") or ""
            title = node.get("title") or ""
            # 节点无编号时, 回退用 section 标题 (LLM 版也需 emit h4/h3, 而非仅靠 render 承担)
            # 仅对本章首个节点生效, 避免重复发射; 按 sec_id 段数动态定级 (5.4.2.2->h4)
            if not num and sec_id and idx == 0:
                num = sec_id
                title = sec_title
            lvl = len(num.split('.')) if num else 3
            body = "\n".join(node.get("paragraphs") or [])
            # var 必须是合法 Python 标识符: 点号/连字符等替换为下划线; 优先用 node.var 但须清洗
            _raw_var = node.get("var") or f"{prefix}_{num}_text" if num else f"{prefix}_{len(specs)}_text"
            var = re.sub(r"[^0-9a-zA-Z_]", "_", _raw_var)
            if not var[0].isalpha() and var[0] != "_":
                var = "_" + var
            specs.append(("text", "get_" + var, {
                "var": var, "num": num, "title": title, "lvl": lvl,
                "has_h1": node.get("has_h1", False), "has_h2": node.get("has_h2", False),
                "sec_id": sec_id, "sec_title": sec_title, "body": body,
                "conclusion": node.get("conclusion") or ""}))
            # 递归 sub4
            if node.get("sub4"):
                walk(node["sub4"], sec_id, sec_title, chapter, chapter_title, prefix, specs, counters)
        elif t == "table":
            tid = tbl_id_from_title(node.get("table_title"))
            counters["tbl"] += 1
            specs.append(("table", f"get_{prefix}_tab_{counters['tbl']}", {"tbl_id": tid}))
        elif t == "figure":
            counters["fig"] += 1
            specs.append(("figure", f"get_{prefix}_figure_{counters['fig']}", {"title": node.get("title") or ""}))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-dir", required=True)
    args = ap.parse_args()
    wd = os.path.abspath(args.work_dir)
    data_dir = os.path.join(wd, "data")
    code_dir = os.path.join(wd, "code")
    os.makedirs(code_dir, exist_ok=True)

    proj = load_yaml(os.path.join(wd, "project.yaml"))
    prefix = proj["project"]
    chapter = proj["chapter"]
    chapter_title = proj["chapter_title"]
    cy = load_yaml(os.path.join(data_dir, "chapter.yaml"))

    specs = []
    counters = {"tbl": 0, "fig": 0}
    for sec in cy.get("sections", []):
        walk(sec.get("prompts", []), sec.get("id"), sec.get("title"), chapter, chapter_title, prefix, specs, counters)

    # ---- prompts 模块 ----
    p_lines = [f"# {prefix} — 第{chapter}章 prompts（LLM 版自动生成）\n"]
    for kind, name, meta in specs:
        if kind == "text":
            prompt = build_prompt(meta["num"], meta["title"], meta["lvl"], meta["has_h1"],
                                  meta["has_h2"], meta["sec_id"], meta["sec_title"],
                                  meta["body"], meta["conclusion"], chapter, chapter_title)
            p_lines.append(f"{meta['var']} = {json.dumps(prompt, ensure_ascii=False)}\n")

    # ---- getter 模块 ----
    g_lines = [f"# {prefix} — 第{chapter}章 getter（LLM 版自动生成）",
               f"# 表格 getter 直接返回 render 预渲染片段(code/chapter{chapter}_tables.json); 不经 LLM。",
               f"from {prefix}_ch{chapter}_prompts import *",
               "import json, os\n",
               f'_RENDER_TABLES = json.load(open(os.path.join(os.path.dirname(__file__), "chapter{chapter}_tables.json"), encoding="utf-8"))\n',
               'def _render_table(tbl_id):\n',
               '    return _RENDER_TABLES.get("表" + tbl_id,\n',
               '        \'<p class="caption">表\' + tbl_id + \'</p><table border="1"><tr><td>未提取，请人工补充</td></tr></table>\')\n']
    for kind, name, meta in specs:
        if kind == "text":
            g_lines.append(f"async def {name}(xmxx_extract=None, content=None):\n")
            g_lines.append(f'    """{meta["num"]} {meta["title"]}"""\n')
            g_lines.append(f"    return {meta['var']}\n")
        elif kind == "table":
            tid = meta["tbl_id"]
            g_lines.append(f"async def {name}(xmxx_extract=None, content=None):\n")
            g_lines.append(f'    """表{tid} — 直接返回 render 预渲染片段"""\n')
            g_lines.append(f'    return _render_table("{tid}")\n')
        elif kind == "figure":
            title = meta["title"]
            g_lines.append(f"async def {name}(xmxx_extract=None, content=None):\n")
            g_lines.append(f'    """图占位: {title}"""\n')
            g_lines.append(f'    return \'<div class="image-placeholder" style="border:1px dashed #999; padding:1em; text-align:center; color:#666; margin:1em 0;">[图片占位：{title} — 请人工补充]</div>\'\n')

    # ---- content 模块 ----
    c_lines = [f"# {prefix} — 第{chapter}章 content 调度（LLM 版自动生成）",
               f"from get_{prefix}_ch{chapter}_prompts import *\n",
               "import os, asyncio\n",
               f"def chapter_divide():\n",
               f'    """返回第{chapter}章 getter 函数有序列表"""\n',
               f"    funcs = [\n"]
    for kind, name, meta in specs:
        c_lines.append(f"        {name},\n")
    c_lines.append("    ]\n")
    c_lines.append(f"    return {{{chapter}: funcs}}, None\n\n")
    c_lines.append(f"async def generate_chapter{chapter}(xmxx_extract, content, llm_handler):\n")
    c_lines.append(f'    """按序执行全部 prompt，调用 LLM 生成。表格/figure 节点直接返回预渲染片段，不经 LLM。"""\n')
    c_lines.append(f"    chapter_funcs, _ = chapter_divide()\n")
    c_lines.append(f"    funcs = chapter_funcs[{chapter}]\n")
    c_lines.append(f"    _sem = asyncio.Semaphore(int(os.environ.get('LONGCAT_CONCURRENCY', '10')))\n")
    c_lines.append(f"    async def _run_one(handler):\n")
    c_lines.append(f"        name = handler.__name__\n")
    c_lines.append(f"        async with _sem:\n")
    c_lines.append(f"            try:\n")
    c_lines.append(f"                prompt_text = await handler(xmxx_extract, content)\n")
    c_lines.append(f'                if "_tab" in name or "figure" in name:\n')
    c_lines.append(f'                    return {{"index": 0, "name": name, "prompt": prompt_text, "result": prompt_text}}\n')
    c_lines.append(f"                result_text = await llm_handler(prompt_text)\n")
    c_lines.append(f'                return {{"index": 0, "name": name, "prompt": prompt_text, "result": result_text}}\n')
    c_lines.append(f"            except Exception as e:\n")
    c_lines.append(f'                return {{"index": 0, "name": name, "prompt": None, "result": None, "error": str(e)}}\n')
    c_lines.append(f"    results = list(await asyncio.gather(*[_run_one(h) for h in funcs]))\n")
    c_lines.append(f"    for _i, _r in enumerate(results):\n")
    c_lines.append(f"        _r['index'] = _i + 1\n")
    c_lines.append(f"    return results\n\n")
    c_lines.append(f'if __name__ == "__main__":\n')
    c_lines.append(f"    funcs, _ = chapter_divide()\n")
    c_lines.append(f'    print(f"第{chapter}章 getter 数: {{len(funcs)}}")\n')

    out_prompts = os.path.join(code_dir, f"{prefix}_ch{chapter}_prompts.py")
    out_getter = os.path.join(code_dir, f"get_{prefix}_ch{chapter}_prompts.py")
    out_content = os.path.join(code_dir, f"content_{prefix}_ch{chapter}.py")
    open(out_prompts, "w", encoding="utf-8").write("\n".join(p_lines))
    open(out_getter, "w", encoding="utf-8").write("\n".join(g_lines))
    open(out_content, "w", encoding="utf-8").write("\n".join(c_lines))
    print(f"✅ 三件套已生成: {len(specs)} 个 getter")
    print(f"   {out_prompts}")
    print(f"   {out_getter}")
    print(f"   {out_content}")


if __name__ == "__main__":
    main()
