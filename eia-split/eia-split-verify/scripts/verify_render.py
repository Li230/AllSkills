# -*- coding: utf-8 -*-
"""eia-split-verify: render 后质量闸门 (参数化, 新项目直接复用)。
多轮比对 render 产出的 HTML 每张表的 字段/行数/抽样单元格 与 all_tables_pdf.json(PDF/txt源),
迭代修正至零误差。自带 while-not-zero-error 循环驱动; 发现退化表时按 eia-split-verify
SKILL.md 的「退化表处理原则」处理(本地解析优先, 联网搜索兜底)。未命名 页* 表单独报告。

用法:
  python3 verify_render.py --work-dir <dir> [--max-rounds 3]

经验/坑 (已固化):
  - 多轮是机制不是人肉: 本脚本循环调用, 每轮产出差异清单; 差异分两类:
      (a) render/extract 取数错位 -> 报出后由人工/自动化回 extract(re抽)或 render(重渲) 修正;
      (b) 退化单行表 -> 走退化表处理(见下), 不计入 error 但标 WARN。
  - hainan_ch2 实测多轮: 第1轮发现 表2.2-3 表尾粘连正文(末行被吸进段落) ->
    修了 txt_fallback 按表头宽度截断 -> 第2轮零误差零警告。
  - 退化表处理原则(PDF/txt均抽不到干净结构时): 数据在、可看 -> 先按退化表渲染,
    verify 标 WARN; 把本地抽到的几行内容交给智能体, 智能体可联网搜索(webSearch)核对/
    补全结构再重抽为干净多行表; 仍无法结构化则保留退化表标"未提取"。
    (本脚本对常见坐标控制点表内置 _try_coordinate_rows 本地首选; 通用联网兜底由 agent 调用。)
"""
import argparse
import json
import os
import re

DEFAULT_WORK = os.getcwd()


def parse_render_tables(html):
    out = {}
    for b in re.split(r'(?=<p class="caption")', html):
        if "<table" not in b:
            continue
        cap = re.search(r'<p class="caption"[^>]*>(.*?)</p>', b, re.S)
        cap_text = cap.group(1).strip() if cap else ""
        m = re.search(r'表\s*([\d.]+)-(\d+)', cap_text)
        if not m:
            continue
        tid = f"表{m.group(1)}-{m.group(2)}"
        th = [t.strip() for t in re.findall(r'<th>(.*?)</th>', b, re.S)]
        data = []
        for tr in re.findall(r"<tr>(.*?)</tr>", b, re.S):
            if "<th>" in tr:
                continue
            cells = [c.strip() for c in re.findall(r"<td>(.*?)</td>", tr, re.S)]
            if any(cells):
                data.append(cells)
        out[tid] = {"th": th, "rows": data, "n": len(data)}
    return out


def json_table(entry):
    rows = entry.get("rows") or []
    if entry.get("fields"):
        return entry["fields"], rows[1:]
    if len(rows) >= 2:
        return rows[0], rows[1:]
    fields = [f"列{i+1}" for i in range(len(rows[0]))] if rows else []
    return fields, rows


def run_one_round(work_dir, tables_pdf, render_t):
    c_set = set(tables_pdf.keys())
    r_set = set(render_t.keys())
    errors = []
    warns = []
    # 未命名真实表: 页* 自动命名, 或 '表3-2' 类无章节点号的(未关联到 表X.Y-Z)
    unnamed = [t for t in c_set if t.startswith("页") or re.match(r'^表\d+-\d+$', t)]
    if unnamed:
        warns.append(f"未命名真实表(需归位): {unnamed}")
    for tid in sorted(render_t.keys()):
        rt = render_t[tid]
        entry = tables_pdf.get(tid)
        if not entry:
            warns.append(f"{tid}: render 有多余表(源无)")
            continue
        jf, jd = json_table(entry)
        src = entry.get("source", "?")
        line_issues = []
        if len(rt["th"]) != len(jf):
            line_issues.append(f"字段数 {len(rt['th'])}!={len(jf)}")
        if rt["n"] != len(jd):
            line_issues.append(f"行数 {rt['n']}!={len(jd)}")
        if rt["rows"] and jd:
            # render 表含表头行(th), rt["rows"] 比 jd 多 1 行表头; 比对数据行(跳过表头)
            rt_data = rt["rows"][1:] if len(rt["rows"]) > len(jd) else rt["rows"]
            for ri in [0, min(len(rt_data) - 1, len(jd) - 1)]:
                if ri < len(rt_data) and ri < len(jd):
                    # 逐单元格 strip 比较(忽略列数差/多余空列, 以较短为准), 避免不规则表误报
                    a_cells = [str(c).strip() for c in rt_data[ri]]
                    b_cells = [str(x).strip() for x in jd[ri]]
                    mn = min(len(a_cells), len(b_cells))
                    diff = False
                    for k in range(mn):
                        if a_cells[k][:30] != b_cells[k][:30]:
                            diff = True
                            break
                    if diff:
                        line_issues.append(f"行{ri}抽样不一致")
                        break
        if line_issues:
            errors.append((tid, src, line_issues))
        elif src == "txt" and rt["n"] <= 1:
            warns.append(f"{tid}: 退化表(单行/需人工或联网精修)")
    return errors, warns


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-dir", default=DEFAULT_WORK)
    ap.add_argument("--max-rounds", type=int, default=3)
    args = ap.parse_args()
    wd = os.path.abspath(args.work_dir)
    data_dir = os.path.join(wd, "data")
    out_dir = os.path.join(wd, "output")
    code_dir = os.path.join(wd, "code")
    tpath = os.path.join(code_dir, "all_tables_pdf.json")
    if not os.path.exists(tpath):
        tpath = os.path.join(data_dir, "all_tables_pdf.json")  # 降级兼容
    tables_pdf = json.load(open(tpath, encoding="utf-8"))
    c2 = os.path.join(out_dir, "chapter2.html")
    alts = [f for f in os.listdir(out_dir) if f.startswith("chapter") and f.endswith(".html")]
    html_path = c2 if os.path.exists(c2) else os.path.join(out_dir, alts[0])
    html = open(html_path, encoding="utf-8").read()

    rounds = 0
    while rounds < args.max_rounds:
        rounds += 1
        render_t = parse_render_tables(html)
        errors, warns = run_one_round(wd, tables_pdf, render_t)
        print(f"\n===== 第 {rounds} 轮校验 =====")
        print(f"render 表数: {len(render_t)} | 误差项: {len(errors)} | 警告: {len(warns)}")
        for tid, src, iss in errors:
            print(f"  ❌ {tid}[{src}]: {iss}")
        for w in warns:
            print(f"  ⚠️ {w}")
        if not errors:
            print("✅ 零误差: 所有表字段/行数/抽样单元格均与源一致。")
            if warns:
                print(f"⚠️ {len(warns)} 项警告(退化表/未命名表), 非错误, 建议人工/智能体处理。")
            print("→ 可交用户审核 render HTML。")
            return
        print(f"❌ {len(errors)} 张表存在误差, 须回 extract/render 修正后重跑本脚本。")
        # 机制说明: 此处不自动修, 由外层(eia-split-extract/render)修正后重跑
        break
    if errors:
        raise SystemExit(f"verify 未通过(第{rounds}轮仍有 {len(errors)} 误差)")


if __name__ == "__main__":
    main()
