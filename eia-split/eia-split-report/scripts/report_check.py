# -*- coding: utf-8 -*-
"""report_check.py — eia 章节收尾校验(render/LLM/PDF 三方比对)。
校验: 层级一致 / 表完整(caption+数量) / 标题完整 / 内容覆盖。
输出 output/chapter{N}_report.json + 终端摘要。任一 FAIL 退出码非0。
用法: python3 report_check.py --work-dir <dir>
"""
import os, re, json, argparse, yaml


def load_yaml(p):
    return yaml.safe_load(open(p, encoding="utf-8"))


def count_tags(html, tag):
    return len(re.findall(rf"<{tag}[ >]", html))


def get_captions(html):
    return re.findall(r'<p class="caption"[^>]*>(表[\d.\-]+[^<]*)</p>', html)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-dir", required=True)
    args = ap.parse_args()
    wd = os.path.abspath(args.work_dir)
    cfg = load_yaml(os.path.join(wd, "project.yaml"))
    ch = cfg["chapter"]
    out = os.path.join(wd, "output")
    render = open(os.path.join(out, f"chapter{ch}.html"), encoding="utf-8").read()
    llm = open(os.path.join(out, f"chapter{ch}_llm.html"), encoding="utf-8").read()
    report = {"chapter": ch, "checks": []}

    def check(name, ok, detail=""):
        report["checks"].append({"name": name, "pass": bool(ok), "detail": detail})
        print(f"{'✅' if ok else '⚠️'} {name}" + (f": {detail}" if detail and not ok else ""))

    # 1. 层级一致
    tags = ["h1", "h2", "h3", "h4", "table"]
    levels_ok = all(count_tags(render, t) == count_tags(llm, t) for t in tags)
    detail = {t: [count_tags(render, t), count_tags(llm, t)] for t in tags}
    check("层级一致性(render==LLM)", levels_ok, str(detail))

    # 2. 表完整
    r_cap = get_captions(render)
    l_cap = get_captions(llm)
    only_num = sum(1 for c in l_cap if " " not in c.strip())
    caps_ok = len(r_cap) == len(l_cap) and only_num == 0
    check("表 caption 完整(LLM版)", caps_ok, f"render={len(r_cap)} llm={len(l_cap)} 仅表号数={only_num}")
    empty_tbl = len(re.findall(r"未提取，请人工补充", llm))
    check("无空表残留", empty_tbl == 0, f"空表数={empty_tbl}")

    # 3. 标题文本一致
    def titles(html, tag):
        return re.findall(rf"<{tag}>(.*?)</{tag}>", html, re.S)
    title_ok = all(titles(render, t) == titles(llm, t) for t in ["h2", "h3", "h4"])
    check("标题文本一致(render==LLM)", title_ok)

    # 4. 内容覆盖
    empty_p = len(re.findall(r"<p[^>]*>\s*</p>", llm))
    check("无空段落", empty_p == 0, f"空段落数={empty_p}")
    intro = re.search(r"</h1>\s*<p[^>]*>(.*?)</p>", llm, re.S)
    check("引言段存在", bool(intro) and intro.group(1).strip() != "", "")

    all_pass = all(c["pass"] for c in report["checks"])
    report["result"] = "PASS" if all_pass else "FAIL"
    json.dump(report, open(os.path.join(out, f"chapter{ch}_report.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(f"\n结论: {'✅ 全部通过' if all_pass else '⚠️ 存在失败项'} -> {os.path.join(out, f'chapter{ch}_report.json')}")
    if not all_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
