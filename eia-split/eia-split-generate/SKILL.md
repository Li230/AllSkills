---
name: eia-split-generate
description: 调用LLM运行generate_chapter产出章节HTML。表格变量不走LLM——直接插入render产出的表HTML片段；仅段落/sub4调LLM。并发(Semaphore)提升吞吐。generate后做表完整性验证(对比PDF/txt)。
---

# EIA Split Generate — 调用 LLM 生成章节 HTML

读取 `eia-split-to-py` 三件套，用 LLM handler 运行 `generate_chapterN()`，把 prompt 结果拼接为章节 HTML。本步是 **LLM 生成路径**核心，但**表格不走 LLM**——直接插入 render 片段。

## 何时触发
- 「跑 LLM 生成」「生成章节HTML」「调模型出内容」
- `eia-split-to-py` 已完成（三件套 + `output/chapter{N}_tables.json` 就绪）

## 前置条件
- `code/` 下三件套存在
- `output/chapter{N}_tables.json`（render 表片段）就绪
- LLM 可达：LongCat（`LONGCAK_API_KEY` + `LongCat-2.0` + `enable_thinking:False`）或 qwen 等

## 通用脚本（推荐，新项目直接复用）
- `scripts/run_generate.py --work-dir <sub_dir>`：**参数化**，从 `project.yaml` 自动推导 `PROJECT`/`CHAPTER`/路径，**不硬编码 work-dir**（避免拷贝脚本污染邻 sub 的坑）。调 LongCat 出 `chapter{N}_llm.html`，内置层级自检。
- ⚠️ **拷贝脚本坑（hainan_ch5 sub2 实测）**：早期每个 sub 自带一份 `data/gen_chapter.py`，但 `WORK_DIR`/`PROJECT`/`CONTENT_MODULE` 硬编码成源 sub → 拷贝到新 sub 未改会**写到邻 sub 目录 + import 报错**。已修复为参数化通用版，新 sub **直接复用 `scripts/run_generate.py`**，勿再手改硬编码副本。

## 工作流程

### Step 1: 导入 content 模块
```python
import sys; sys.path.insert(0, f"{work_dir}/code")
import content_{base}_ch{N} as c
```

### Step 2: 构建 async llm_handler
LongCat 示例：`openai.OpenAI(...)` + `extra_body={'chat_template_kwargs':{'enable_thinking':False}}`，`max_tokens≈2000`、`temperature≈0.3`；用 `asyncio.to_thread` 包同步 SDK。

### Step 3: 并发运行 generate_chapterN（关键）
各 getter 无副作用纯函数、LLM 调用独立 → 可并发：
```python
async def generate_chapterN(xmxx_extract, content, llm_handler, concurrency=10):
    funcs = c.chapter_divide()[0][N]
    sem = asyncio.Semaphore(concurrency)
    async def run_one(i, h):
        async with sem:
            try:
                p = await h(xmxx_extract, content)
                if h.__name__.startswith("get_") and "tab" in h.__name__:
                    return {"index": i+1, "name": h.__name__, "prompt": p, "result": p}  # 表格: p 已是 render 片段
                r = await llm_handler(p)
                return {"index": i+1, "name": h.__name__, "prompt": p, "result": r}
            except Exception as e:
                return {"index": i+1, "name": h.__name__, "prompt": None, "result": None, "error": str(e)}
    return list(await asyncio.gather(*[run_one(i, h) for i, h in enumerate(funcs)]))
```
- `concurrency` 默认 **10**。实测 86 条串行~5min → 并发10~1min。

### Step 4: 拼接
```python
results = await generate_chapterN(None, project, llm_handler, concurrency=10)
html = "\n\n".join(r["result"] for r in results if not r.get("error"))
open(f"{work_dir}/output/chapter{N}_llm.html", "w").write(html)
# 表格变量 r["result"] 已是 render <table> 片段；text 变量是 LLM 输出
```

### Step 5: 验证（替代后处理保真）
因 render 已带数据、LLM 不碰表，无需重建表。改为完整性自检：
- **表数 == grep `表X.Y-Z` 去重数**（from txt）
- **每张表非空**（无 `<tr><td></td></tr>`）
- **表号齐全**（缺号报警）
PDF/txt 作验证参考（**非数据来源**）。

### Step 6: 交 eia-split-report

## 设计原则
1. 绝不在 HTML 产物上打补丁修结构 → 回 eia-split-extract/render 根上修。
2. **表格来自 render 片段（确定性）；LLM 只做叙述**。
3. 标题（含四级 `<h4>`）每个 prompt 只出现一次，body 不含标题前缀。
4. **⚠️ LLM 版 `<style>` 须与 render 版一致（hainan_ch4 sub3 实测）**：生成 `chapter{N}_llm.html` 的 `<head><style>` 块**直接复用 render 版 `chapter{N}.html` 的 `<style>` 字符串**，不要自行加/减 hN 规则。若 render 版是裸 `body{...}`（hN 靠浏览器默认渲染），LLM 版也须是同样的 `body{...}`；否则同一章 render/LLM 两版 h4 视觉层级不一致，用户核验会要求对齐。做法：generate 脚本读 `output/chapter{N}.html` 提取其 `<style>...</style>` 原样写进 LLM 版，或两者共用同一常量。

## 下一步
运行 **eia-split-report** 三方比对 + 结构回归

## 标准命令
```bash
python3 skills/eia-split-generate/scripts/run_generate.py --work-dir <work_dir>
```
> ⚠️ 闸门：project.yaml 的 `render_reviewed` 须为 true，否则拒绝运行（先完成 render+verify+人工审核）。
🔴 工程铁律：文件操作用 python，禁 shell cd 中文路径。

## 下一步
运行 **eia-split-report** 三方比对 + 结构回归

## 标准命令
```bash
python3 skills/eia-split-generate/scripts/run_generate.py --work-dir <work_dir>
```
> ⚠️ 闸门：project.yaml 的 `render_reviewed` 须为 true，否则拒绝运行（先完成 render+verify+人工审核）。
🔴 工程铁律：文件操作用 python，禁 shell cd 中文路径。
