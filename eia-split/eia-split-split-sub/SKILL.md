---
description: Use this skill when a single EIA chapter PDF is too large to process in one
  pipeline pass (e.g. ch5=135pg / ch7=151pg) and must be split into multiple sub-projects
  before the standard eia-split pipeline. Triggers include "大章拆 sub", "eia-split-split-sub",
  "拆分子项目", "按 h3 拆分章节", "章节太大要分 sub". Produces a review table (sub | 小节范围 |
  页数 | 表格数), then after user approval splits the PDF into scoped sub-PDFs.
name: eia-split-split-sub
---

# EIA Split — 大章拆 sub（init 之后 / extract 之前）

当一个章节 PDF 过大（>~30–40 页，或表/节太多）无法一次性跑完流水线时，先把它拆成多个
**sub 子项目**，每个 sub 独立跑完整流水线（parse→extract→render→verify→to-py→generate），
最后在顶层合并。本 skill 把 **ch4/ch5 实证 + ch7 教训** 沉淀成集中、可执行的 SOP。

## 在流水线中的位置（核心约束）

```
init(顶层 hainan_chN) → 【eia-split-split-sub: propose 审查表 → 用户审核 → split 切PDF】
   → 每个 sub 各自： parse → extract(表普查) → render → checkpoint → verify(闸门) → [审核] → to-py → generate → report
   → 顶层合并（层级B：统一 code 三件套 + 一次 LLM）
```

> 🔴 **本 skill 位于 init 之后、extract 之前。** 它作用于 init 建好的**顶层 work_dir**
> （含 `project.yaml`：pdf_path / chapter / chapter_title / project）。拆出的每个 sub 自带
> 独立 `project.yaml`（含 `scope_sections` / `scope_title`），再各自走标准流水线。

## 何时触发

- 用户说「大章拆 sub」「拆分子项目」「章节太大要分 sub」「按 h3 拆分」
- 或章节 PDF 页数明显超过单 sub 上限（默认 30 页）

## 方法论（固化 ch4/ch5 实证 + ch7 反例）

| 原则 | 做法 | 反例（ch7 初版犯的错） |
|------|------|----------------------|
| **切分口 = 章节标题边界** | 只用 h2/h3/h4 天然标题作切分点；h3 是默认口，h2 可合并、h4 可下钻 | ❌ 按固定 30 页硬切中途段落，劈断 7.1.1/7.1.2 |
| **自动下钻** | 某段 >max_pages 且存在更细子标题 → 自动下钻到 h4 切分（如 7.1.1 拆 7.1.1.1–5） | ❌ 不探结构直接拍脑袋定切分 |
| **每 sub ≤ max_pages** | 默认 30 页；相邻段贪心合并填满 | — |
| **overlap 每边 2 页** | 防段落被切断；sub 的 PDF 页范围 = 职责节页 ±2 | ❌ 忘了 overlap 致边界段落残缺 |
| **scope_sections 零冗余** | 每个 sub 的 `project.yaml` 声明 `scope_sections`（本 sub 职责节）；parse/extract 据此裁剪 txt，邻居节冗余页被标题边界挡在门外 → 合并时直接拼，无需再裁 | ❌ 切分后不裁剪，合并出现重复 |
| **先探后定** | propose 用 pdfplumber 探真实落页，绝不靠记忆/假设 | ❌ ch7 初版假设"7.1.2 存在" → 探针证明根本无 7.1.2 |
| **标题含中文过滤** | 环评节标题必含中文；纯数字串（如坐标刻度"7.5 20 40 60…"）判为假阳性丢弃 | ❌ 误把刻度数字串当 7.5 节标题，还顶掉真标题 |

## 两阶段 + 人工闸门

```
Phase 1  propose ：只读 PDF，探 h1-h4 落页 + 表/图落页，分组，打印审查表，写 split_plan.json
                   ★ 安全，可反复跑/调参，不写任何文件（除 plan）
        ↓  【人工闸门：用户看表审核；可改 split_plan.json 的 subs 微调】
Phase 2  split    ：读 split_plan.json，建 sub 目录、按页范围切 PDF、写各 sub 的 project.yaml
                   ★ 写文件，须用户审核通过后执行
```

## 审查表格式（用户审核用）

`propose` 打印如下表格，列正是约定的 **sub / 小节范围 / 页数 / 表格数**：

```
sub   小节范围                  页数(含overlap)        表格数(估)
------------------------------------------------------------------------------
sub1   7.1.1.1–7.1.1.4       p1–26 (26页)         3
sub2   7.1.1.5               p23–41 (19页)        1
sub3   7.1.3–7.2.1.2         p38–66 (29页)        20
sub4   7.2.1.3–7.2.3         p63–96 (34页)        8          ⚠>max
...
```

- **小节范围**：本 sub 覆盖的节号（单节写自身；多节写 `首–尾`）。跨 h2 合并时会显式写出（如 `7.1.3–7.2.1.2`），便于识别。
- **页数(含overlap)**：实际切出的 PDF 页范围与页数。⚠>max 表示超过 `--max-pages`（通常因 overlap 叠加在大节上；结构无法再细分时由用户定夺接受或调整）。
- **表格数(估)**：PDF 标题扫描估值（去重、优先取正文出现）。**权威数以 extract 表普查为准**，此处仅作拆分合理性参考。

## 标准命令

```bash
# 前置：init 已建好顶层 work_dir（含 project.yaml）
# 1) 提出拆分子方案（审查表）—— 反复跑直到满意
python3 skills/eia-split-split-sub/scripts/probe_split.py \
  --work-dir <top_work_dir> --phase propose \
  [--max-pages 30] [--overlap 2] [--cut-level 3]
#   列含义见上；方案写入 <top_work_dir>/split_plan.json
# 2) 用户审核审查表；如需调整，直接编辑 split_plan.json 的 subs（改 pdf_range / scope / 合并拆分）
# 3) 审核通过，切 PDF + 建 sub 工程（写文件）
python3 skills/eia-split-split-sub/scripts/probe_split.py \
  --work-dir <top_work_dir> --phase split
#   产物：<top_work_dir>/subK/{data,code,output}/ + subK/project.yaml
#         <top_work_dir>/hainan_chN_K_范围.pdf  （物理 sub PDF，命名对齐 ch5）
# 4) 每个 sub 走标准流水线（parse→extract→...→generate→report）
# 5) 顶层合并（层级B：统一 code 三件套 + 一次 LLM，参考 eia-split-README「合并阶段标准做法」）
```

CLI 参数：
- `--work-dir`：顶层工程目录（读 `project.yaml`；无则用下方覆盖）
- `--phase`：`propose` | `split`
- `--max-pages`：单 sub 页数上限（默认 30）
- `--overlap`：每边重叠页数（默认 2）
- `--cut-level`：切分口层级，`2`=h2 / `3`=h3(默认) / `4`=h4（propose 用；默认 h3 并对超大段自动下钻 h4）
- 覆盖：`--pdf` `--chapter` `--chapter-title` `--project`（work-dir 无 project.yaml 时用）

## 产物

| 文件 | 说明 |
|------|------|
| `<top_work_dir>/split_plan.json` | propose 输出：完整拆分子方案（subs / max_pages / overlap / 总页数），split 阶段读取 |
| `<top_work_dir>/hainan_chN_K_范围.pdf` | 切出的物理 sub PDF（命名 `hainan_chN_{K}_{首节}-{尾节}.pdf`，对齐 ch5 `hainan_ch5_1_5.1-5.2.pdf`） |
| `<top_work_dir>/subK/project.yaml` | 各 sub 工程元信息，`scope_sections` / `scope_title` 已填，可直接进 parse |

## 已知约束 / 待增强

- **表格数为估值**：来自 PDF 标题扫描，可能受页眉重复表标题干扰；以 extract 表普查为权威。
- **scope 裁剪（已固化 ✅ 2026-07-15）**：`eia-split-parse/scripts/parse.py` 与
  `eia-split-extract/scripts/extract.py` 现已读 `scope_sections`，按"自身+全部祖先+后裔"三层判定
  裁剪 clean.txt / structure.json / chapter.yaml，保证子任务 txt 零冗余（overlap 邻居被标题边界挡在门外）。
  同步进 skill 的还有：parse 的 `is_valid_title` 强校验（拒数字串假阳性）、`in_range` 编号守卫、
  表 `end_line`、图 `section`；extract 的 `extract_paragraphs` 段落精修（句末合并+清页码）、figure 节点。
  （原 ch4/ch5 项目副本的 scope 逻辑已回流，不再需要项目副本。）
- **⚠>max 处理**：结构无法再细分（无 h5）却仍超上限时，由用户决定接受或人工调整 split_plan.json。
- **标题探测依赖格式**：依赖"章号开头 + 中文标题"的排版；极特殊编号（如 7.6.3.2 缺失）可能漏探，
  可在 propose 后人工核对 split_plan.json 的 scope 覆盖。

## 下步

拆分并建好 sub 工程后，对每个 `subK` 依次执行：
`eia-split-parse` → `eia-split-extract` → `eia-split-render`（+checkpoint 强制逐表校验）
→ `eia-split-verify`（闸门）→ 用户审核 render → `eia-split-to-py` → `eia-split-generate`
→ `eia-split-report`。全部 sub 完成后，顶层按层级 B 合并。
