---
name: eia-split-report
description: eia 章节流水线收尾校验。对 render 版 / LLM 版 / PDF-txt 三方做结构回归与一致性比对，输出验证报告，确认章节产物可用。generate 之后必须跑。
---

# EIA Split Report — 收尾校验与结构回归

在 generate 产出 `chapter{N}_llm.html` 后，做最后一道质量闸门：三方比对 + 结构回归。本步不调用 LLM，纯静态校验。

## 何时触发
- 「出报告」「校验章节」「report 阶段」
- `eia-split-generate` 已完成（`chapter{N}_llm.html` 存在）

## 前置
- `output/chapter{N}.html`（render 版，含完整表数据）
- `output/chapter{N}_llm.html`（LLM 版，叙述生成）
- `data/chapter{N}-clean.txt`（PDF 文本参考）
- `data/all_tables_pdf.json`（权威表数据源）

## 校验项

### 1. 层级一致性（render vs LLM）
h1/h2/h3/h4/table 数量两版必须相等。不一致 → LLM 版漏发/多发表/标题。

### 2. 表完整性（LLM 版）
- 表数 == render 版表数 == `all_tables_pdf.json` 键数
- 每张表 caption 完整（含表号+标题文字，非仅表号）
- 表数 == 正文引用的本章表号（去重）— 用 `verify_census` 同源逻辑
- 无空表（`<td>未提取</td>` 不应出现在最终产物）

### 3. 标题完整性
- LLM 版 h2/h3/h4 标题文本 == render 版（逐层比对）
- 无重复标题（同编号出现两次）
- 无缺失标题（render 有 LLM 无）

### 4. 内容覆盖（抽样）
- 每段 LLM 叙述非空（非 `<p></p>`）
- 引言段（h1 后首段）存在且非空

### 5. 跨章引用（非报错，仅提示）
- 正文引用了其他章表号（如 表5.3-2）属正常上溯，不计入缺失

## 通用脚本
`scripts/report_check.py --work-dir <dir>`：
- 自动读上述文件，跑 1-4 项
- 输出 `output/chapter{N}_report.json` + 终端摘要
- 任一 FAIL → 返回非 0 退出码（可接入 CI）

## 输出
- 终端：✅/⚠️ 逐项结论
- `output/chapter{N}_report.json`：结构化结果

## 下一步
全部 PASS → 章节 done，可部署检验或进入下一章。
