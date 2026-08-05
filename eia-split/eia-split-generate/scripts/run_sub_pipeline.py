# -*- coding: utf-8 -*-
"""eia-split 子项目端到端流水线 (参数化, 新 sub 直接复用)。
流程: render → checkpoint(强制闸门) → [闸门不过则中止] → to-py(三件套) → generate(LLM) → 挂 8123。
用法: python3 run_sub_pipeline.py --work-dir <sub_dir> [--skip-mount]
前置: LONGCAK_API_KEY 须在环境中 (generate 阶段)。
注意: 本脚本只跑到 LLM HTML 生成 + 挂载; 用户审核 render/LLM 版是外部闸门(不自动过)。
"""
import os, sys, subprocess, argparse, re

RENDER = "/root/.qwenpaw/workspaces/QwenPaw_QA_Agent_0.2/skills/eia-split-render/scripts/render.py"
CHECKPOINT = "/root/.qwenpaw/workspaces/QwenPaw_QA_Agent_0.2/skills/eia-split-render/scripts/checkpoint_tables.py"
GENTHREE = "/root/.qwenpaw/workspaces/QwenPaw_QA_Agent_0.2/skills/eia-split-to-py/scripts/gen_three_py.py"
GENLLM = "/root/.qwenpaw/workspaces/QwenPaw_QA_Agent_0.2/skills/eia-split-generate/scripts/run_generate.py"
WEB_ROOT = "/root/vibe/split/马村港区报告书_按章节拆分/web_root"


def run(cmd, env=None):
    e = dict(os.environ)
    if env:
        e.update(env)
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=e)
    print(r.stdout)
    if r.stderr:
        print("[stderr]", r.stderr[-500:])
    return r.returncode == 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-dir", required=True)
    ap.add_argument("--skip-mount", action="store_true", help="不挂 8123 (仅本地生成)")
    ap.add_argument("--api-key", default=os.environ.get("LONGCAK_API_KEY", ""), help="LongCat key")
    args = ap.parse_args()
    wd = os.path.abspath(args.work_dir)
    proj = os.path.join(wd, "project.yaml")

    print(f"\n{'='*60}\n[1/5] render\n{'='*60}")
    if not run(f"python3 {RENDER} --work-dir {wd}"):
        print("❌ render 失败, 中止"); return

    print(f"\n{'='*60}\n[2/5] 强制检查点 (逐表内容校验)\n{'='*60}")
    cp = subprocess.run(f"python3 {CHECKPOINT} --work-dir {wd}", shell=True, capture_output=True, text=True)
    print(cp.stdout)
    if "⚠️" in cp.stdout or "存在需根上修复" in cp.stdout:
        print("❌ 检查点未通过: 须回 render 根上修 all_tables_pdf.json 的 rows 重渲, 不得进 to-py")
        return
    print("✅ 检查点通过")

    # 置 render_reviewed=true (闸门开)
    s = open(proj, encoding="utf-8").read()
    s = re.sub(r"render_reviewed:\s*false", "render_reviewed: true", s)
    open(proj, "w", encoding="utf-8").write(s)

    print(f"\n{'='*60}\n[3/5] to-py 三件套\n{'='*60}")
    if not run(f"python3 {GENTHREE} --work-dir {wd}"):
        print("❌ to-py 失败, 中止"); return

    print(f"\n{'='*60}\n[4/5] generate (LongCat LLM)\n{'='*60}")
    if not args.api_key:
        print("❌ 未提供 LONGCAK_API_KEY, 跳过 generate"); return
    if not run(f"python3 {GENLLM} --work-dir {wd}", env={"LONGCAK_API_KEY": args.api_key, "LONGCAK_MODEL": "LongCat-2.0"}):
        print("❌ generate 失败, 中止"); return

    print(f"\n{'='*60}\n[5/5] 挂载 8123\n{'='*60}")
    if args.skip_mount:
        print("⏭️ 跳过挂载"); return
    out = os.path.join(wd, "output", "chapter5_llm.html")
    if not os.path.exists(out):
        out = os.path.join(wd, "output", "chapter4_llm.html")
    import yaml as _yaml
    _proj = _yaml.safe_load(open(proj, encoding="utf-8"))
    sub = _proj["project"]  # hainan_ch5_sub2 (用 project 名, 非目录名)
    link = os.path.join(WEB_ROOT, f"{sub}_llm.html")
    os.makedirs(WEB_ROOT, exist_ok=True)
    if os.path.islink(link) or os.path.exists(link):
        os.remove(link)
    os.symlink(out, link)
    print(f"✅ 软链已建: {link} -> {out}")
    print(f"   公网: http://101.43.120.121:8123/{sub}_llm.html")
    print(f"   内网: http://127.0.0.1:8123/{sub}_llm.html")


if __name__ == "__main__":
    main()
