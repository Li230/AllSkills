---
name: eia-split-verify
description: render 后、to-py 前的质量闸门。多轮比对 render 产出的 HTML 每张表的字段/行数/抽样单元格值 与 PDF(all_tables_pdf.json) + txt 源，迭代修正至零误差，再交用户审核 render HTML。是"to-py 表格只信 render"的前提。
---

# EIA Split Verify — render 后质量闸门（多轮表数据校验）

在 render 产出完整 HTML 后、to-py 消费前，对**表格数据**做多轮交叉验证：render HTML 表 ↔ PDF 抽取(JSON) ↔ txt 源，确保零误差。未达标不交由 to-py，避免错误表数据被"固化"进最终 HTML。

## 何时触发
- 「校验render」「render验证」「表数据核对」
- eia-split-render 完成（`output/chapter{N}.html` + `chapter{N}_tables.json` 就绪）

## 前置条件
- `output/chapter{N}.html`（render 完整版）
- `code/all_tables_pdf.json`（PDF 抽取，权威数据；与 to-py 同处 `code/`）
- `data/chapter{N}-clean.txt`（txt 源）
- `data/structure.json`

## 运行（参数化脚本，自带多轮循环，新项目直接复用）
```bash
python3 skills/eia-split-verify/scripts/verify_render.py --work-dir <work_dir> [--max-rounds 3]
```
脚本循环校验：每轮产差异清单，差异分两类——
- **(a) 取数错位**（字段/行数/抽样不一致）→ 回 eia-split-extract（重抽）或 eia-split-render（重渲）修正，再重跑本脚本；
- **(b) 退化单行表**（`source: txt` 且 ≤1 行）→ 不计入 error，标 WARN，走下方退化表处理。

## 工作流（多轮迭代，直至零误差）

### Round 逻辑（脚本即此实现）
1. **抽取 render HTML 表**：解析 `output/chapter{N}.html` 所有 `<table>`（按 `<p class="caption">` 表号定位），得 `{表号: {fields, rows}}`。
2. **比对 PDF(JSON)**：对每表，比对 `fields`、行数、抽样单元格（首行/末行/含关键数值行）与 `all_tables_pdf.json[表号]`。差异 → 记录。
3. **比对 txt 源**：对 PDF 缺失（`source: txt`）的表，比对 render 表与 `chapter{N}-clean.txt` 对应行范围；差异 → 记录。
4. **未命名表归位检查**：JSON 中 `页*`/`表3-2` 类未关联表号者 → 单独列 WARN，须回 extract 归位（见 eia-split-extract skill）。
5. **判定**：零 error → 通过，输出 `verify_render_report.md`；有 error → 报清单，回修后重跑。

### 经验（hainan_ch2 实证多轮）
- 第1轮发现 **表2.2-3 行3 抽样不一致** → 根因是 txt 兜底把下一行段落吸进末行 → 修 `txt_fallback` 按表头宽度截断 + `_trim_glued` 清尾部中文 → 第2轮**零误差零警告**。
- 多轮必须是**机制不是人肉**：脚本自带 `while-not-zero-error` 循环驱动，避免手动跑几轮的遗漏。

## 审核闸门（程序化强制）
verify 零误差后，**必须交用户审核 `output/chapter{N}.html` 并置 `project.yaml: render_reviewed=true`**，`eia-split-to-py` 前置检查该标志，否则中止并提示先审核。这样"to-py 表格只信 render"才有闸门保障。

### 用户审核 gate
零误差后，**暂停交用户审核 `output/chapter{N}.html`**（yaml 得到的 html）。用户确认无误 → 放行 to-py；用户指出问题 → 回修对应阶段。

## 检查维度
| 维度 | 说明 |
|------|------|
| 表号齐全 | render 表号集 == 表普查 `C`（txt 去重） |
| 字段一致 | `<th>` 与 JSON/txt 表头一致 |
| 行数一致 | 数据行数 == JSON/txt |
| 单元格值 | 抽样关键数值单元格一致 |
| 空表 | 无空 `<tr><td></td></tr>` |

## 注意事项
- 本步只验证 render 表数据，不改叙述（叙述由 LLM 在 to-py 生成）
- 多轮迭代：每轮修正后必须重 render 再验，直至零误差
- 不修改产物内容的"打补丁"——差异须回 extract/render 根上修
- **HTML 文件名自适应**：脚本自动找 `output/chapter*.html`（不硬编码 chapter2.html）。
  旧版 fallback 条件写反会崩溃，已修复（hainan_ch4 sub1）。
- **子项目可零误差**：子片段无 h1 不影响表校验；只要表字段/行数/抽样与 `all_tables_pdf.json` 一致即通过。
- **⚠️ 不规则表列数差误报（hainan_ch4 sub2 表4.4-3）**：PDF 抽的表某些行 6 列、某些 7 列，render 的 `build_table_html` 按 max 列数补空 `''` 渲染 → render 表比 JSON 源多一列空单元格。verify 原整行 `join` 比对因子项长度/尾随空格触发"行N抽样不一致"误报。修复：`run_one_round` 抽样比对改为**逐单元格 strip 比较、以较短列数为准、忽略多余空列**（hainan_ch4 sub2 实证零误差）。

## 退化表处理原则（PDF/txt 均抽不到干净结构时）
当某表 PDF 原生抽取失败、txt 兜底也只能得到**单行退化表**（如坐标控制点挤在 txt 一行 `S1 109°.. 19°.. S8 ...`）时：
- **数据在、可看**，先按退化表渲染（不丢数据），verify 标 `⚠️ 退化表` 交用户/智能体。
- **智能体重建**：把本地抽到的这几行内容交给智能体，智能体**可联网搜索（webSearch）**核对表结构/补全字段，再重抽为干净多行表。
- 仍无法结构化（如完全无本地内容且无公开来源）→ 保留退化表并标"未提取，请人工补充"。
- 此原则写入 `eia-split-extract/scripts/table_census.py` 的 `_try_coordinate_rows` 等退化表专用解析作为本地首选；联网搜索作为通用兜底。

## 下一步
用户审核通过后 → **eia-split-to-py**（表格只插 render 认证片段）
