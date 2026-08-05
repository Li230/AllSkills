---
name: eia_split_render
description: 读取chapter.yaml，用Jinja2渲染HTML。表格数据从all_tables_pdf.json（表普查产物）按table_id确定性渲染为带完整数据的<table>，并产出每表HTML片段映射供to-py消费。不调用LLM。
---

## 功能
将 chapter.yaml 按模板渲染为独立 HTML。**表格内容从 `all_tables_pdf.json`（表普查产物）按 `table_id` 确定性取数**，渲染为带完整数据的 `<table>`——render 产出的 HTML 即"完整版"（含全部表格数据与叙述占位）。严格不调用 LLM。

## 使用场景
- 「渲染环评HTML」「生成HTML」
- eia-split-extract 完成（status: extracted，`all_tables_pdf.json` 就绪）

## 运行（参数化脚本，新项目直接复用）
```bash
python3 skills/eia-split-render/scripts/render.py --work-dir <work_dir>
```
产 `output/chapter{N}.html`（完整版）+ `code/chapter{N}_tables.json`（每表 HTML 片段映射，供 to-py 消费）。
⚠️ **表数据位置约定**：表普查产物 `all_tables_pdf.json` 与 render 片段 `chapter{N}_tables.json` **都放在 `code/`**（与 to-py 三件套同目录，自包含）。`render.py`/`verify_render.py` 默认从 `code/` 读，缺失时降级读 `data/`。
> 项目实例 `hainan_ch2/data/render.py` 即此脚本的项目化副本（仅 `WORK_DIR` 硬编码）。

## 经验（已固化，render 阶段避坑）
- **HTML 骨架必须含 `<meta charset="utf-8">`**：否则浏览器用错误编码渲染 → 简体中文乱码。render 输出已包裹 `<!DOCTYPE>/<head><meta charset>`（hainan_ch4 sub1 修复）。
- **表格标题用 `<p class="caption">` 不用 `<h4>`**：`h4` 留给四级小节 `2.x.x.x`，混用会层级错位。
- **图片占位（figure）**：缺失图片渲染为虚线框 `[图片占位：图X.X-X 图标题 — 请人工补充]`。
  **图标题从 clean.txt 全文扫「行首图号」行建立映射**（不靠段落内联检测，避免重复/漏）。
  格式：`图号 — 标题，请人工补充`；无标题时 `图号 — 请人工补充`。
- **退化单行表**（txt 兜底常见整行挤一行，如坐标控制点）→ 整行作数据、表头用通用 `列N`，避免空表；若需结构化（多行控制点），由表普查侧 `_try_coordinate_rows` 拆分（见 extract skill 退化表原则）。
- **表尾粘连正文**：txt 启发式抽表易把下一行段落吸进末行 → 在表普查 `txt_fallback` 按表头宽度截断，render 信任 JSON 已干净。
- **空表降级**：JSON 无数据的表渲染为表头 + 一行"未提取，请人工补充"，不静默跳过。
- **子片段无 h1 是正常**：大章拆子项目时，render 的 h1 应为 0（整章 h1 合并时再加）；`compute_expected` 硬编码 h1=1 的 FAIL 仅对整个整章项目成立，子项目可忽略该告警。
- **🔴 section 标题级别动态化（hainan_ch5 sub3 实测）**：section 标题的 `<hN>` 级别**不能硬编码 h2**。当子项目按 H4 天然切分（如 sub3 = `5.4.2.1`），section id 是 4 段 → 应渲染 `<h4>`；按 H3 切（如 sub2=`5.4.1`）→ `<h3>`；按 H2 切（如 sub1=`5.1`）→ `<h2>`。render 按 `len(section['id'].split('.'))` 定级（2→h2, 3→h3, ≥4→h4），`compute_expected` 的 h2/h3/h4 也按 section id 层级分类计数（旧版 `h2=len(sections)` 假设所有 section 都是 h2，对 H4 切分的 sub3 错判为 h2）。**已修复 render.py**（line 106/220 动态定级 + compute_expected 分层计数），sub1/sub2/sub3 重渲均 PASS 向后兼容。

## 前置
- `chapter.yaml`（表节点含 `table_id`）
- `data/all_tables_pdf.json`（表普查产物，唯一表数据源）

## 工作流
1. **读取** YAML + `all_tables_pdf.json`
2. **加载** Jinja2 模板：
   - 段落首行缩进、结论句标注
   - **表格按 `table_id` 从 JSON 取 `fields`+`rows` 渲染完整 `<table>`**（border 样式、干净 `<th>`、真实 `<td>` 行）
   - 图片占位（含 `image_ref`/`figure`）以虚线框标记
   - **递归渲染嵌套小节**：`sub4`/`children` 渲染为 `<h4>`（四级）、`<h5>`… 保留父子顺序
3. **抽不到的表**：JSON 中 `source: txt` 或缺席 → 渲染表头 + 一行「未提取，请人工补充」（保留表号，便于 verify/用户发现）
4. **渲染** → 写 `output/chapter{N}.html`
5. **产出表片段映射**：`output/chapter{N}_tables.json` = `{ "表X.Y-Z": "<table>...</table>" }`，供 eia-split-to-py 的 getter 直接消费（LLM 不碰表）
6. **验证** (lxml/BeautifulSoup)：标签闭合修复（≤3 轮）；h1/h2/h3/**h4（及更深）**/table 数量与 YAML 期望一致；**每张表非空（无空 `<tr><td></td></tr>`）**
   - **🔴 强制检查点（MUST，render 后必须执行，不得跳过）**：层级计数 PASS **不等于**内容正确。必须额外对**每张表**做内容级校验（脚本示例见下方"强制检查点脚本"）：
     1. **列数一致**：表的每一行 `<td>` 数必须等于表头 `<th>` 数。不一致即在 PDF 提取时被错误合并了邻表/续表（如 sub2 的 表5.4-2 被并入 8 列趋势子表、表5.3-3 表头整行被正文替换）→ **render 按首行宽度截断会吞掉末列数据**。
     2. **表头非垃圾**：表头 `<th>` 不得含句号/超长正文（>40字），否则真表头丢失（如 表5.3-3 表头整格是"储煤棚管理不当…"正文）。
     3. **非空、无缺失行**：表不得为空或缺失数据行。
     4. **caption 匹配**：`<p class="caption">表X.Y-Z …</p>` 的表号须与 `all_tables_pdf.json` 的 key 一一对应，无 `表` 裸标题、无未知 key。
     - 任一不合格 → **根上修复 `all_tables_pdf.json` 的 `rows`（改 JSON 后重渲）**；严禁在 HTML 上打补丁。
     - ⚠️ **假阳性识别**：PDF 提取常在字段内插空格（如"油品类 别"/"罐区防火堤容 积"），表头字段本身合法 → 不算垃圾，勿误修。判断标准是"是否真实字段"而非"有无空格"。
   - **强制检查点脚本**（项目内复用，参数化 work-dir）：扫描 `output/chapter{N}.html` 每张带 caption 表块，输出 `列数/异常行/表头垃圾/空单元格`，结论 ✅/⚠️。sub1/sub2 已落地为 `/tmp/checkpoint_subN.py`，须固化为 skill 自带脚本 `skills/eia-split-render/scripts/checkpoint_tables.py`。
7. **格式自检**：缩进、表格边框、结论句颜色
8. 输出 `render_report.json`，更新 `project.yaml` → `status: rendered`

### 🔴 render 阶段表修复（表数据质量差时必做）
表普查(`table_census.py`)用 `extract_text` 逐行抽表，对**无边框/字符劈裂**的环评表会出错：列聚合错乱、中文两字词被空格劈裂（"土 地资源"）、表头字段粘连。
修复工具 `scripts/fix_tables.py`（render 阶段，根上改 `all_tables_pdf.json`）：
```bash
python3 skills/eia-split-render/scripts/fix_tables.py --work-dir <dir> [--tables 表6.2-1,表6.2-2]
```
机制：① 用 pdfplumber `extract_tables()` **带列坐标重抽**（列聚合准）；② 单元格清洗 `merge_cjk()` —— 相邻皆中文(无英文数字)的词合并（"土 地资源"→"土地资源"、"海洋生态环境"→合并），**英文/数字间隔保留**（"BOD 5"/"SO 2"不合并）；③ 写回 `all_tables_pdf.json`（自动 `.bak` 备份）。随后 render 重渲即得干净表。
⚠️ 空单元格多（如 104/140）通常是**符号矩阵**（●/○/■/□ 表影响程度），本就该空，非缺陷；checkpoint 仅报警"列数不一致/表头垃圾/空表"，空单元格不误报。
ℹ️ 适用场景：ch6 实测 5 张表全用此修复（原 extract_text 抽的 表6.2-3 被劈裂成"土 地资源"、表6.2-1/6.2-2 空单元格超多），重抽后全部正确。

## 注意事项
- 严禁 LLM；表数据 100% 来自 JSON
- 空段落报警；表为空（无 JSON 数据）报警并标「未提取」
- **表格标题用 `<p class="caption">` 不用 h4**；h4 留给四级小节
- 章节可含四级及以下，须递归 `sub4`/`children`，否则层级错乱

## 下一步
**eia-split-verify**（render 后质量闸门：多轮比对 render HTML 表 vs PDF/txt，零误差后交用户审核）→ 再 eia-split-to-py

## 标准命令（参数化，新项目直接复用）
```bash
# 1. 渲染(确定性, 不调 LLM) -> output/chapter{N}.html + code/chapter{N}_tables.json
python3 skills/eia-split-render/scripts/render.py --work-dir <work_dir>
# 2. 强制检查点(逐表列数/表头/空值/caption)
python3 skills/eia-split-render/scripts/checkpoint_tables.py --work-dir <work_dir>
# 3. [表数据质量差时] 带列坐标重抽 + 单元格劈裂清洗
python3 skills/eia-split-render/scripts/fix_tables.py --work-dir <work_dir> [--tables 表6.2-1,表6.2-2]
```
> render 已固化: h1 无条件注入 / is_section_header(空壳h3只发标题) / compute_expected(h1固定=1,intro跳过) / caption 双保险(仅表号时从JSON补标题) / 表修复 fix_tables。
