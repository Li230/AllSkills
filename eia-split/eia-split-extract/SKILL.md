---
description: Use this skill when extracting EIA report content into structured YAML.
  Triggers include "提取环评内容", "eia-split-extract", "生成YAML草稿", "提取段落表格". Runs 表普查
  (PDF优先/txt兜底) to build the single table data source, extracts paragraph text, outputs chapter.yaml.
  Includes CP3 content coverage, CP4 table consistency, and 表普查 self-checks.
name: eia-split-extract
---

# EIA Split Extract — 环评章节内容提取

读取 structure.json 和清理后的 txt，运行**表普查**建立权威表数据源，按结构截取段落正文，生成 chapter.yaml 草稿。这是流水线的第三步，承接 eia-split-parse。

## 何时触发
- 用户说「提取环评内容」「eia-split-extract」「生成YAML草稿」
- eia-split-parse 完成后，用户要求继续

## 前置条件
- `structure.json` 存在且自检通过
- `chapter{N}-clean.txt` 存在
- `project.yaml` 含 `pdf_path`

## 工作流程

### Step 0: 📋 表普查（权威表清单 + 抽取，PDF优先 / txt兜底）
**表的"数据"在此阶段一次性确定**，后续 render 直接消费，LLM/to-py **不再抽取或编造表**。
1. **表号普查**：从 `chapter{N}-clean.txt` 抽**表标题行**（行首 `表X.Y-Z` 或 `表X.Y-Z 标题`），**排除内联引用**（"见表2.2-2"/"(表3-2-4)"不算表）。去重 → 权威表号集 `C`。
   ⚠️ **经验**：早期 grep 不区分"表标题行"与"内联引用"，把正文里的"见表X.Y-Z"也算成表号，虚增 `C` → 后续误报"缺号"。`table_census.py` 的 `is_caption_line()` 已固化此区分。
2. **PDF 原生抽取（优先）**：`pdfplumber` 按 caption 关联抽每页表格 → 干净 `cells`；无法关联到表号的（图内文字/跨页）按内容签名 `CONTENT_MAP` 归正到 `表X.Y-Z`（见 Step 4.6）。
3. **txt 兜底**：对 `C` 中 PDF 未抽到的表号，用 txt 启发式（`txt_fallback`）从 clean.txt 行范围抽字段+行，标 `source: txt`。
4. **未命名真实表归位**（关键，防数据沉默丢失）：PDF 抽到但 caption 未关联到表号的表会被自动命名为 `页{page}表{i}`（如 hainan 的 `页56表0`/`页63表0`/`表3-2`）。这些**是真实数据**，必须归位到 chapter.yaml 的表节点：
   - 按**章节位置**（表在 pdf/page 上的章节区间）匹配到最近的三级标题 → 写入该节的表 prompt；
   - 或人工在 `table_content_map.json` 给 `页*` 表补 `{正确表号: [签名子串]}` 让 `correct_by_content` 归正。
   - ⚠️ **经验**：hainan_ch2 初期这些表被 `^表\d` 过滤丢弃造成数据回退，后改为"保留所有 PDF 抽表"才修复。
5. **自检**：JSON 键集 ⊇ `C`（PDF/txt 兜底都覆盖）；`页*` 未命名表单独列清单交归位；缺号报警。
6. 写出 **`data/all_tables_pdf.json`**（唯一表数据源）：`{ "表X.Y-Z": {"title","fields","rows","source","page"} }`，未命名表用原键保留。

> 表普查脚本：`skills/eia-split-extract/scripts/table_census.py`（参数化 `--work-dir`）。项目实例见 `hainan_ch2/data/extract_all_tables_pdf.py`。

### 🔄 可重入性（重要，防"从init重跑"冲掉结构精修）
extract 重跑会从 PDF/txt 从头生成 chapter.yaml，**丢失手工结构精修**（sub4 四级节点、标题修正如"第二章"→"第2章"、figure 占位等）。规则：
- **表数据**：每次可安全重抽（覆盖 `all_tables_pdf.json`），不影响结构。
- **结构标注**（sub4/标题/figure）：要么把已验证的修正逻辑**写进抽取规则**（首选），要么支持**增量重抽**（只刷新表节点数据，保留结构标注）。绝不在"从init重跑"时盲目覆盖 chapter.yaml 结构层。

```python
def grep_table_ids(txt_path):
    """从 clean.txt grep 表号候选, 去重 -> 权威表号集 C。"""
    text = open(txt_path, encoding="utf-8").read()
    cand = re.findall(r'表\s*(\d+\.\d+)-(\d+)', text)
    ids, seen = [], set()
    for a, b in cand:
        tid = f"表{a}-{b}"
        if tid not in seen:
            seen.add(tid); ids.append(tid)
    return ids

def txt_fallback(txt_path, tid):
    """PDF 抽不到时, 从 clean.txt 按表号行范围启发式抽行。返回 rows 或 None。"""
    lines = open(txt_path, encoding="utf-8").read().split("\n")
    start = next((i for i,l in enumerate(lines)
                  if l.strip().startswith(tid) or re.search(r'表\s*'+re.escape(tid[1:]), l)), None)
    if start is None:
        return None
    rows = []
    for line in lines[start+1:]:
        if re.match(r'^\s*表\s*\d', line) or re.match(r'^\s*\d+\.\d+(\.\d+)*\s+', line):
            break
        cells = [c.strip() for c in re.split(r'\s{2,}', line.strip()) if c.strip()]
        if len(cells) >= 2:
            rows.append(cells)
    return rows or None
```

### Step 1: 读取输入
```python
import json, yaml
config = yaml.safe_load(open(f"{work_dir}/project.yaml"))
structure = json.load(open(f"{work_dir}/data/structure.json"))
txt_lines = open(structure["txt_path"]).readlines()
```

### Step 2: 计算每个 prompt 的行号范围
遍历 structure 的三级标题和表格，计算内容 txt 行号范围（含二级标题边界事件，防越界）：
- 范围内无表格 → 1 paragraph prompt `{var}_text`
- 范围内有 1/2 个表格 → 拆 2/3 个 prompt（`{var}_text` + `{var}_tab1[_2]`）
- 范围内仅表格 → 1 table prompt `{var}_tab`
- 含更深标题（四级 2.x.x.x 等）→ 拆 `sub4`/`children` 嵌套节点（见 Step 2.5）

### Step 2.5: 🧱 深层标题（四级及以下）处理（防标题重复）
深层标题拆成父段落下的 `sub4`/`children` 嵌套节点，每个独立成 prompt；剔除标题前缀，body 不含重复标题文字。变量名含完整点号编号。

### Step 2.6: 🖼️ 图片占位节点（figure）
`parse` 阶段识别的「行首图号」figure 节点，在 extract 转为独立 prompt（`type: figure`），
含 `figure_id` / `figure_title`。render 据其渲染图片占位框（含图标题，提示原 PDF 图片未提取）。
**图片占位不依赖段落内联检测**（易重复/漏），统一由 figure 节点驱动，保证图号不重不漏。
（hainan_ch4 sub1 实证：9 个图全部带标题占位，无重复）

### Step 2.7: 🔪 scope 裁剪继承
若 `project.yaml` 含 `scope_sections`，extract 只处理 scope 内的 H3/H4/figure/表
（parse 已裁剪 txt，此处兜底再筛）。跨 scope 的邻居节标题/表自动排除，保证子任务产物零冗余。

### Step 3 / 3.5: 提取段落 + 清理
`extract_paragraphs`（断行合并）、`clean_page_number`（页码清理）、`merge_paragraphs`、`IMAGE_REF_PATTERN`、`FIGURE_CAPTION_PATTERN` 同原流程，确保无页码残留与段落碎裂。

### Step 4: 提取表格数据（仅元数据，内容已在表普查确定）
对每个 table prompt，仅记录 `table_title` 与 `txt_lines` 范围；**字段与行数据不在此抽**，直接引用 `all_tables_pdf.json`（按 `表X.Y-Z` 关联）。chapter.yaml 的 table 节点写入 `table_id: "表X.Y-Z"`，render 据此从 JSON 取完整 rows。

### Step 4.6: 🔗 表号关联校正（已在表普查内）
`extract_tables()` 抽到的表若 caption 是图内文字/跨页，会被自动命名为 `页{page}表{i}`。校正（抽取脚本末尾按内容特征归正）：
1. `CONTENT_MAP`：`正确表号 → 该表独有内容签名子串`（如 `{"表2.2-4":["船舶吨级","船长"]}`）。
2. 对所有 `页*` 表，拼单元格文本，命中某表号全部签名 → 重命名。
3. 仅 1 列长文本 → 判为段落误抽，删除。
4. 抽取后表号覆盖自检：JSON 键集 vs `C` 比对，缺号报警。

### Step 5: 生成变量名
`{project}_ch{chapter}_{section}_{type}`（表格 `{prefix}_{num}_tab`）。

### Step 6: 组装 chapter.yaml
```yaml
sections:
  - prompts:
      - var: hainan_ch2_2_1_tab
        type: table
        table_id: "表2.1-1"          # render 据此从 all_tables_pdf.json 取完整 rows
        table_title: "表2.1-1 马村港区码头生产性泊位现状情况表"
        txt_lines: [15, 26]
      - var: hainan_ch2_2_1_1_text   # 段落/sub4 同前
```
保存到 `{work_dir}/data/chapter.yaml`。

### Step 7/8: 自检 CP3 / CP4
- **CP3 内容覆盖**：每段正文可追溯 txt；txt 无遗漏实质行。
- **CP4 表一致性**：chapter.yaml 表号集 == `all_tables_pdf.json` 键集 == 表普查 `C`；字段/行数以 JSON 为准（不再比对 txt 启发式碎片）。

### Step 9: 更新 project.yaml
```yaml
status: extracted
table_mode: pdf_census   # 表数据来自 all_tables_pdf.json (PDF优先/txt兜底)
```

### Step 10: 输出
告知：表普查表数、CP3/CP4 结果、下一步「执行 eia-split-render」。

## 产物
| 文件 | 说明 |
|------|------|
| `data/chapter.yaml` | 结构化内容（表仅存 `table_id`，内容在 JSON） |
| `data/all_tables_pdf.json` | **唯一表数据源**（PDF优先/txt兜底，含 `source` 标记） |

## 自检清单
| 检查点 | 说明 | 失败处理 |
|--------|------|---------|
| 表普查自检 | JSON 键集 == txt 表号去重集 `C`；缺号报警 | 回抽/补 txt 兜底 |
| CP3 内容覆盖 | 段落可追溯 txt | 重截行号 |
| CP4 表一致性 | 表号/字段/行数 = JSON | 重抽 |

### 🔴 extract 后置强自检（必做，不可跳过）
`table_census.py` 只查缺号/多号，不足以暴露「源PDF表号错乱」(ch5 sub4/5/6 实测 data/ 普查不可信)。extract 完成后**必须**跑：
```bash
python3 skills/eia-split-extract/scripts/verify_census.py --work-dir <work_dir>
```
任一 ⚠️ 问题（缺号/不连续/列数不一致/表头垃圾/空表）→ 用 `rebuild_tables.py` 从 clean.txt 按标题重建错位表（读 `data/table_overrides.json` 手工精校复杂表），改 `all_tables_pdf.json` 后重渲。

### 🔴 文本节点分离（标题/正文/引言）—— 最易静默丢内容，必须审计
**根因（hainan_ch6 实测）**：旧 extract 用 `for h2 in h2_list` 循环，只抓「h2 行之后」内容。
h1（章标题）到第一个 h2 之间的**全章导语区间**不属于任何 h2 section、又非表/图 → **无节点承载、静默丢弃**。
ch4/ch5 该区间本就空（或仅页码），bug 潜伏；ch6 有全章导语（"总体来看…"）才暴露。
**同类易漏点**（均已修，extract.py/render.py 已固化）：
1. **h1~h2 引言丢失** → extract 循环 h2 前先抓 `h1行→首个h2行` 区间，生成 `is_intro` section 承载；render 对 intro 只渲染正文 p、不发射 h1/h2（h1 由框架 `<h1>第N章</h1>` 无条件注入）。
2. **h2 紧邻 h3 时引言被吃** → 取引言区间用 `extract_para_lines(h2l, lead_end-1)`；clean_text 标题行（章/节/子节号、表、图开头）**永不合并不被并入**（前后都防）。
3. **h1 框架标题丢失** → render 无条件注入 `<h1>第{ch}章 {title}</h1>`，不依赖 has_h1 节点标志。
4. **空壳 h3 节点**（h3 下直接是 h4 子节、无独立正文）→ 标 `is_section_header`，render 只发 `<h3>` + 递归 sub4，不发空 `<p>`。
5. **交叉引用错乱**（正文 `表5.3-2` 为上章残留）→ extract 末尾扫正文引用的表号，不在本章表清单则报警（源报告笔误，不自动改，交人工确认）。
6. **compute_expected 误算**：intro section（lv=1）不能计入 h4；h1 固定=1；section 级只计 lv2/3/≥4。

**审计方法（必做）**：对 `structure.json` + `chapter.yaml` + `clean.txt` 三方交叉比对，自动扫：空正文节点 / 正文混编号标题 / 标题字段过长含句号 / structure 标题 vs extract 节点一致性 / 交叉引用表号存在性。发现异常即回 extract/render 根上修。

### 🔴 工程提示（避坑）
文件操作（复制/改名/字符串替换）一律用 **python**（`shutil`/`copy`/`字符串替换`），**禁止 shell `cd` 含中文路径**（变量展开会致 `$BASE` 为空、cd 报 `too many arguments`）。多行 shell 命令 + 中文 + `echo` 易解析混乱，统一走 python 脚本。

## 下一步
**eia-split-render**（从 JSON 渲染完整表）→ 随后 **eia-split-verify** 多轮校验。

## 标准命令（参数化，新项目直接复用）
```bash
# 1. 表普查(权威表数据源)
python3 skills/eia-split-extract/scripts/table_census.py --work-dir <work_dir> --pdf <pdf_path>
# 2. 强自检(必跑, 不可跳过)
python3 skills/eia-split-extract/scripts/verify_census.py --work-dir <work_dir>
# 3. 生成 chapter.yaml(段落/标题/表节点)
python3 skills/eia-split-extract/scripts/extract.py --work-dir <work_dir>
# 4. [可选] 表数据错位时从 clean.txt 重建
python3 skills/eia-split-extract/scripts/rebuild_tables.py --work-dir <work_dir> --apply
```
> extract 已固化: h1~h2 全章引言(is_intro) / h2 紧邻 h3 引言 / 空壳 h3(is_section_header) / 跨章引用校验(只查本章前缀) / 完整 table_title。

## 注意事项
- **表是数据不是 LLM 产物**：extract 用表普查一次性抽全，render 确定性渲染，to-py 不再让 LLM 生成表（避免空表/失样式/段落化那类堆叠问题）。
- 段落提取准确依赖 txt 清理质量；表格最大难点，靠表普查 + 后续 verify 兜底。
- 二级标题边界：`build_prompts` 须把二级标题行号作边界事件，防越界（CP8 检出）。
- `merge_first_col: true` 表示首列连续相同值需 rowspan（自动检测连续 3+ 行相同）。
- **⚠️ 嵌套/合并表头导致空列头（hainan_ch4 实测，必记）**：环评表常是**两层表头**——第0行是分组类（如"调查时段""有效波高范围""栖息密度(ind/m2)""评估要素"）跨多列，真实列名在第1数据行（如站点名、浪高级、环节/节肢/软体动物、年份）。PDF 抽取时把分组行当 `rows[0]` 表头，真实列名位留空 → **列数≠字段数、空列头**。
  - **修复（根上改 `all_tables_pdf.json` 的 `rows[0]`，非 HTML 补丁）**：浏览表标题+数据行，由 AI（QwenPaw QA Agent）推断每列真实字段名，展平为单一表头行（空列用真实列名填，如 `栖息密度-环节动物`/`栖息密度-软体动物`/`湿重生物量-环节动物`）。
  - 若源 JSON 仅表头无数据行（PDF 原抽取缺失），用户直接提供数据则整表重建 `rows = [表头] + 数据行`，标 `source="user_provided"`。
  - **列数对齐校验**：写回前 assert `len(rows[0]) == len(数据行列数)`，否则中止人工核对（如 4.1-7 原9列，展平为 `波向+7个浪高级+合计`=9列，勿把"有效波高范围"单列致列数错）。
  - **同步纪律**：改 `all_tables_pdf.json` 后必须重渲（刷新 `chapter4_tables.json`）→ 重跑合并生成器 + 合并 LLM；**render 合并版与 LLM 合并版都要重跑**，否则两版表头不一致。
  - 已修复实例：表4.1-1/4.1-2（站点名提列）、4.1-7（浪高级展平）、4.5-10（栖息密度/湿重分组）、4.5-12（年份/变化/分级）、4.5-15（多样性指数7列）、4.5-16（用户补数据+9列底质覆盖）。
