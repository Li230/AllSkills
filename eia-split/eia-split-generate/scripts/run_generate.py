# -*- coding: utf-8 -*-
"""eia-split-generate 通用运行器: 调 LongCat 跑 generate_chapterN 出 LLM HTML。
表格/figure getter 直接返回 render 片段, 仅段落经 LLM。并发 Semaphore(10)。
全部参数从 --work-dir 的 project.yaml 自动推导 (PROJECT/CHAPTER), 不硬编码, 避免污染邻 sub。
环境变量: LONGCAK_API_KEY / LONGCAK_BASE_URL / LONGCAK_MODEL / LONGCAT_CONCURRENCY
LLM版 <style> 复用 render 版 (hainan_ch4 sub3 教训: 两版须一致)。
用法: python3 run_generate.py --work-dir <sub_dir>
"""
import os, sys, re, json, asyncio, time, argparse, yaml
import openai


def load_yaml(p):
    return yaml.safe_load(open(p, encoding="utf-8"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-dir", required=True)
    args = ap.parse_args()
    wd = os.path.abspath(args.work_dir)
    proj = load_yaml(os.path.join(wd, "project.yaml"))
    # 🔴 verify 闸门: render 人工审核通过(render_reviewed: true) 才能 generate
    if not proj.get("render_reviewed", False):
        print("❌ 未通过 render 人工审核：project.yaml 的 render_reviewed 不为 true。")
        print("   请先完成 eia-split-render → eia-split-verify → 人工审核，")
        print("   并将 project.yaml 的 render_reviewed 置为 true，再运行 generate。")
        return
    WORK_DIR = wd
    CODE_DIR = os.path.join(wd, "code")
    OUT_DIR = os.path.join(wd, "output")
    sys.path.insert(0, CODE_DIR)
    PROJECT = proj["project"]
    CHAPTER = int(proj["chapter"])
    CONTENT_MODULE = f"content_{PROJECT}_ch{CHAPTER}"

    API_KEY = os.environ.get("LONGCAK_API_KEY", "")
    BASE_URL = os.environ.get("LONGCAK_BASE_URL", "https://api.longcat.chat/openai")
    MODEL = os.environ.get("LONGCAK_MODEL", "LongCat-2.0")
    EXTRA = {"chat_template_kwargs": {"enable_thinking": False}}

    def _sync_call(prompt):
        client = openai.OpenAI(api_key=API_KEY, base_url=BASE_URL)
        r = client.chat.completions.create(
            model=MODEL, messages=[{"role": "user", "content": prompt}],
            max_tokens=3000, temperature=0.3, extra_body=EXTRA)
        return r.choices[0].message.content

    async def llm_handler(prompt_text: str) -> str:
        return await asyncio.to_thread(_sync_call, prompt_text)

    def _render_style():
        try:
            html = open(f"{OUT_DIR}/chapter{CHAPTER}.html", encoding="utf-8").read()
            m = re.search(r"<style>.*?</style>", html, re.S)
            if m:
                return m.group(0)
        except Exception:
            pass
        return '<style>body{font-family:"Microsoft YaHei","PingFang SC",sans-serif;max-width:960px;margin:auto;padding:1em;line-height:1.8;}</style>'

    if not API_KEY:
        print("❌ 未设置 LONGCAK_API_KEY 环境变量", flush=True)
        return
    mod = __import__(CONTENT_MODULE)
    print(f"模型: {MODEL}  端点: {BASE_URL}  思考: 关闭  并发: {os.environ.get('LONGCAT_CONCURRENCY','10')}  sub={PROJECT}", flush=True)
    t0 = time.time()
    # 兼容 chapter4 / chapter5 的 generate 函数名
    gen_fn = getattr(mod, f"generate_chapter{CHAPTER}", None)
    if not gen_fn:
        print(f"❌ {CONTENT_MODULE} 无 generate_chapter{CHAPTER}", flush=True)
        return
    results = asyncio.run(gen_fn(None, PROJECT, llm_handler))
    parts = []
    for r in results:
        if r.get("error"):
            print(f"  ❌ {r['name']}: {r['error'][:80]}", flush=True)
        else:
            parts.append(r.get("result") or "")
    full_html = "\n\n".join(parts)
    style = _render_style()
    html_doc = (f'<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n'
                f'<title>第{CHAPTER}章 {PROJECT}</title>\n{style}\n</head>\n<body>\n'
                + full_html + '\n</body>\n</html>')
    out_path = f"{OUT_DIR}/chapter{CHAPTER}_llm.html"
    open(out_path, "w", encoding="utf-8").write(html_doc)
    ok = sum(1 for r in results if not r.get("error"))
    fail = len(results) - ok
    print(f"\n✅ 完成: 成功 {ok}/{len(results)} (失败 {fail})  耗时 {time.time()-t0:.1f}s", flush=True)
    print(f"LLM HTML: {out_path} ({len(full_html)} 字节)", flush=True)

    def count(html, tag):
        return len(re.findall(rf"<{tag}[ >]", html))
    render_html = open(f"{OUT_DIR}/chapter{CHAPTER}.html", encoding="utf-8").read()
    print("\n=== LLM版 vs render版 层级 ===", flush=True)
    for tag in ["h1", "h2", "h3", "h4", "table"]:
        a, b = count(full_html, tag), count(render_html, tag)
        print(f"  {tag}: LLM={a} render={b} {'✓' if a == b else '⚠️不一致'}", flush=True)


if __name__ == "__main__":
    main()
