# EIA Split 流水线总览（环评章节拆分）

> **最新更新：2026-07-15**（基于 ch6 整章实战的完整能力清单与版本迭代，见下方「当前能力总览」一节）。旧版 ch2/ch4/ch5 沉淀保留在文末作历史参考。

---

## 当前能力总览（2026-07-15 更新）

### Skill 清单（9 个 + 本 README）
| Skill | 脚本 | 核心能力 |
|-------|------|---------|
| **eia-split-init** | （仅 SKILL.md） | 建目录 + 写 `project.yaml`；含**命名规范**（单章=`hainan_chN` 无后缀；拆 sub 独立+顶层合并禁 `_full_` 污染） |
| **eia-split-parse** | `parse.py` | PDF→clean.txt；识别 h1-h4 标题/表/图 → `structure.json`；**边界行不合并**（标题/表/图独立成行，防静默漏表/漏标题） |
| **eia-split-extract** | `table_census.py` `verify_census.py` `rebuild_tables.py` `extract.py` | 表普查（PDF优先/txt兜底）→ 强自检 → 错位表重建 → 生成 `chapter.yaml`（含 **h1全章引言** / **空壳h3** / **跨章引用只查本章前缀** / **完整 table_title**） |
| **eia-split-render** | `render.py` `checkpoint_tables.py` `fix_tables.py` | 确定性渲染 HTML（表100%来自JSON）；逐表强制检查点；**表劈裂修复**（extract_tables重抽+merge_cjk清洗） |
| **eia-split-verify** | `verify_render.py` | render 后质量闸门（多轮比对 render 表 vs PDF/txt） |
| **eia-split-to-py** | `gen_three_py.py` | 参数化生成三件套；无编号节点回退 section 标题；return `{ch:[funcs]},None` |
| **eia-split-generate** | `run_generate.py` `run_sub_pipeline.py` | 调 LongCat 跑 LLM 生成；**render_reviewed 闸门**；style 复用 render 版 |
| **eia-split-report** | `report_check.py` | **收尾校验**（render/LLM/PDF 三方比对：层级/表caption/标题/空段落/引言）；输出 report.json |
| **eia-split-split-sub** | `probe_split.py` | **大章拆 sub（init 后 / extract 前）**：pdfplumber 探落页 → 按 h3/h4 边界分组(≤30页,overlap2) → 打印审查表(sub\|小节范围\|页数\|表格数) → 用户审核后切 PDF + 建 sub 工程 |
| **eia-split-README** | （本文件） | 总览 |

### 能力矩阵
| 能力 | 状态 |
|------|------|
| PDF 结构解析（h1-h4/表/图） | ✅ parse.py，边界不合并 |
| 表作为数据资产（不靠 LLM） | ✅ 表普查→render确定性渲染→to-py只插片段→LLM只写叙述 |
| 表普查强自检 | ✅ verify_census（唯一性/连续性/列数/表头/空表） |
| 表错位重建 | ✅ rebuild_tables（clean.txt按标题+overrides） |
| 表劈裂修复（render阶段） | ✅ fix_tables（extract_tables重抽+merge_cjk） |
| 文本节点分离（标题/正文/引言） | ✅ extract 的 is_intro/is_section_header/跨章引用 |
| render 强制检查点 | ✅ checkpoint_tables（逐表列数/表头/caption） |
| verify 人工闸门（generate门控） | ✅ render_reviewed=false 拦截 |
| 收尾三方比对 | ✅ report_check（新增） |
| 命名同构（ch4风格） | ✅ 单章无 `_full_` 后缀 |
| shell python 化铁律 | ✅ 写入多 SKILL 注意事项 |

### 标准命令流（新项目直接复用，全参数化）
```bash
# 1. 初始化
#    (手写 project.yaml 或用 init SKILL 指引; work_dir 建 data/code/output)
# 2. 解析
python3 skills/eia-split-parse/scripts/parse.py --work-dir <work_dir>
# 3. 提取(表普查 + 强自检 + 生成 chapter.yaml)
python3 skills/eia-split-extract/scripts/table_census.py --work-dir <work_dir> --pdf <pdf_path>
python3 skills/eia-split-extract/scripts/verify_census.py --work-dir <work_dir>
python3 skills/eia-split-extract/scripts/extract.py --work-dir <work_dir>
# 4. 渲染 + 检查点 + [表劈裂修复]
python3 skills/eia-split-render/scripts/render.py --work-dir <work_dir>
python3 skills/eia-split-render/scripts/checkpoint_tables.py --work-dir <work_dir>
python3 skills/eia-split-render/scripts/fix_tables.py --work-dir <work_dir> [--tables 表6.2-1,表6.2-2]
# 5. 人工审核 render HTML -> 置 render_reviewed=true
# 6. to-py + generate(LongCat)
python3 skills/eia-split-to-py/scripts/gen_three_py.py --work-dir <work_dir>
python3 skills/eia-split-generate/scripts/run_generate.py --work-dir <work_dir>
# 7. 收尾校验
python3 skills/eia-split-report/scripts/report_check.py --work-dir <work_dir>
```

### 大章路径（需拆 sub，如 ch5=135pg / ch7=151pg）

单章 ≤30 页走上面标准流即可；**大章先拆 sub**，流程为：

```
init(顶层 hainan_chN) → eia-split-split-sub(propose 审查表 → 审核 → split 切PDF)
   → 每个 sub： parse → extract → render → checkpoint → verify → [审核] → to-py → generate → report
   → 顶层合并（层级B）
```

集中 SOP 见 **eia-split-split-sub** skill（探落页 → 按 h3/h4 边界分组 ≤30页 overlap2 → 审查表 → 审核后切 PDF）。
**🔴 顺序铁律**：split-sub 必须在 init 之后、各 sub 的 extract 之前；禁止不探结构就按固定页数硬切。

### 版本迭代时间线
- **基线（ch2/ch4/ch5）**：extract/render/to-py/generate 基础流程；表是数据资产原则；checkpoint_tables、render 动态级别
- **迭代1（ch5复盘）**：新建 verify_census / rebuild_tables；run_generate 加 render_reviewed 闸门；init 命名规范；gen_three_py 去 ch5 特例；parse 边界合并 bug 修
- **迭代2（ch6实战）**：parse 标题/正文/引言分离（h1~h2引言丢失修复）；extract is_intro/is_section_header/跨章引用/完整table_title；render h1注入/caption双保险/compute_expected；checkpoint_tables 路径修复；fix_tables 新建
- **迭代3（ch6全优）**：eia-split-report 新建闭环；SKILL.md 补 CLI 命令；fix_tables 表定位增强（按标题top坐标选最近表）；verify_census 连续性误报修复；shell python 化铁律扩写
- **迭代4（2026-07-15 晚）**：① 新建 **eia-split-split-sub** skill（大章拆 sub：pdfplumber 探落页→按 h3/h4 边界分组≤30页 overlap2→审查表→审核后切 PDF）；② **ch4/ch5 优化全部回流 skill**：parse.py 加 scope 三层裁剪 + `is_valid_title` 强校验 + `in_range` 守卫 + 表 `end_line` + 图 `section`；extract.py 加 `extract_paragraphs` 段落精修（句末合并+清页码）+ figure 节点 + scope 防御过滤；跨章引用校验保留。验证：ch5 整章 scope(5.1-5.2) 正确裁出、深 h3 scope(5.2.1) 祖先保留零泄漏、ch6 无 scope 无回归。

### 已知遗留 / 待观察
- `eia-split-verify/verify_render.py` 与 render 内置 checkpoint 功能重叠，未统一
- `run_sub_pipeline.py`（子项目流水线）存在但未在 ch6 验证（ch6 整章一次性）
- 表内部"单元格内多指标挤一行"（如表6.3-1 的"1、xxx 2、xxx"）保留原样，未做 `<br>` 分段（内容完整无丢失，视觉可优化）

---

把环评报告 PDF 按章节拆成结构化 HTML。核心架构决策（2026-07-13 hainan_ch2 实证）：

> **表是数据资产，不是 LLM 生成物。**
> 表在 `extract`（表普查）阶段一次性从 PDF/txt 抽全 → `render` 确定性渲染成带数据的 `<table>` → `verify` 多轮校验零误差 → 用户审核 → `to-py`/`generate` 只让 LLM 写**叙述文本**，表直接插入 render 预渲染片段。
> 这样彻底消除"LLM 生成表"带来的空表/失样式/段落化问题。

## 流水线（两段，五 skill + 表普查脚本）
```
init → parse → extract(表普查) → render → **checkpoint(强制逐表内容校验)** → verify(闸门) → [用户审核] → to-py → generate → report
        (共用)   (PDF/txt抽表)  (完整表HTML+片段)  (🔴列数/表头/空表)   (多轮零误差)            (LLM只写叙述, 表插片段)
```

> 🔴 **强制检查点（任何子项目不可跳过）**：`render` 输出后、`verify`/审核前，必须跑 `eia-split-render/scripts/checkpoint_tables.py --work-dir <sub_dir>`。
> 层级计数 PASS（h1/h2/h3/h4/table 数量一致）**绝不等于内容正确**——PDF 提取常把邻表/续表误合并进同一 key（如 sub2 表5.4-2 被并入 8 列趋势子表、表5.3-3 表头整行被正文替换），render 按首行宽度截断会**静默吞掉末列数据**。
> 检查点逐表校验：**① 每行列数==表头列数 ② 表头非正文垃圾 ③ 非空无缺失 ④ caption 表号匹配**。任一不合格 → **回 render 根上修 `all_tables_pdf.json` 的 `rows` 重渲**，绝不可带病进 to-py（LLM 不碰表，脏表原样进最终 HTML）。注意区分真错误与提取空格假阳性（字段内空格不算垃圾）。

| skill | 职责 | 脚本（参数化，新项目复用） | 关键经验 |
|-------|------|--------------------------|---------|
| eia-split-init | 建目录/写 project.yaml | — | 复用目录不删 data/；`render_reviewed` 闸门标志 |
| eia-split-parse | PDF→txt + 结构/标题/表格定位 | — | CP1/CP1-二级/CP2 自检；识别四级(及更深)标题为独立 level，禁并入段落 |
| eia-split-extract | **表普查**（PDF优先+txt兜底）+ 内容提取 | `scripts/table_census.py` | ① 表号只取**标题行**排除内联引用；② `CONTENT_MAP` 按内容签名归正 `页*` 表；③ 未命名 `页*` 表须按章节**归位**防丢失；④ **可重入**：重抽表数据可，重跑不得冲掉 sub4/标题精修 |
| eia-split-render | 从 JSON 按 `table_id` 渲染**完整数据表** + 产出片段映射 | `scripts/render.py` | 表格标题用 `<p class="caption">` 非 h4；退化单行表整行作数据；空表降级"未提取" |
| eia-split-verify | render 后质量闸门：多轮比对 render 表 vs JSON 源，**零误差**才交用户 | `scripts/verify_render.py`（自带 while 循环） | 多轮是机制不是人肉；退化表→智能体可联网搜索重建；未命名表单独 WARN |
| eia-split-to-py | 生成三件套；**表 getter 返回 render 片段(不经 LLM)** | — | 硬依赖 `render_reviewed==true`；getter 缺失表号优雅降级 |
| eia-split-generate | 跑 LLM 出章节 HTML；**表格变量跳 LLM 直接插片段** | — | 并发 gather+Semaphore(10)；LLM 只做叙述 |
| eia-split-report | 最终三方比对+结构回归 | — | 表来自 render，本步只确认表未被 LLM 改动 |

## 可参考实例（hainan_ch2，项目专属代码不进 skill，思路进 skill）
- 表普查实例：`hainan_ch2/data/extract_all_tables_pdf.py` + `data/table_content_map.json`（签名归正 表2.2-4/2.3-7/2.4-13）
- render 实例：`hainan_ch2/data/render.py`（即 `render.py` 模板项目化）
- verify 实例：`hainan_ch2/data/verify_render.py`
- **多轮实证**：表2.2-3 表尾粘连正文 → 修 `txt_fallback` 截断 → 第2轮零误差；表2.4-11 坐标行 → `_try_coordinate_rows` 拆 S1–S14 控制点
- **最终产物**：86/86 LLM 成功，LLM版 vs render版 层级全一致（h1=1/h2=6/h3=26/h4=25/table=34），34 表 0 空表

## 新项目怎么用
1. `eia-split-init`（指定 project/pdf_path/chapter）
2. 依次 `parse` → `extract`（跑 `table_census.py`，按章节调整 `table_content_map.json`）→ `render`（跑 `render.py`）
3. `verify`（跑 `verify_render.py`，多轮至零误差）→ **用户审核 render HTML**
4. `to-py` → `generate` → `report`

> 所有 skill SKILL.md 内含"经验/坑"段与可参考代码；项目专属硬编码脚本属于项目，新项目按模板重新生成适配版。

## 大章拆子项目（hainan_ch4 实证，2026-07-13）

> 🔧 **已集中固化**：下面的方法论（按标题边界切 / overlap / scope 零冗余 / 合并层级）已自动化进
> **eia-split-split-sub** skill（pdfplumber 探落页 + 按 h3/h4 分组 + 审查表 + 审核后切 PDF）。
> 新项目直接跑该 skill，勿再手动 `/tmp/probe_*.py` 或拍脑袋定切分（ch7 初版硬切中途段落即踩坑）。

整章过大（如 ch4 = 90 页、60+ 表）时拆成多个子项目并行/串行处理，最终合并。

### 拆分原则
1. **按 H2 归组**：先罗列全章 h1–h4，按内容独立度切 3 组（如 4.1-4.2 / 4.3-4.4 / 4.5-4.6）。
   明确每组**覆盖哪些 h 标题**（scope），杜绝歧义。
2. **PDF 切分时每边多切 2 页（overlap）**：保证段落不被切断（如 4.2 结尾跨页段落完整）。
3. **txt 用 h 标题零冗余**：子 PDF 含邻居节冗余页，但 parse 阶段按 `scope_sections` 的首 H2→下个非 scope H2 之间**裁剪 txt**，
   重叠页的邻居节内容被 h 标题边界挡在门外 → **每个子任务 txt 零冗余**。合并时直接拼 3 段，无需再裁。
4. 每子项目独立跑完整流水线（init→parse→extract→render→verify→[审核]→to-py→generate→report）。
5. 合并：顶部加 h1「第N章 标题」+ 锚点导航，下方按 h2 顺序拼接各子项目 HTML。

### 项目级脚本 vs skill 模板
- `parse`/`extract` 的 **scope 裁剪 + figure 节点 + 标题鲁棒性 + 段落精修 已全部回流进 skill**（2026-07-15 晚，固化 ch4/ch5 项目副本）。
  `eia-split-parse/scripts/parse.py` 读 `scope_sections` 按"自身+祖先+后裔"裁剪 clean.txt/structure.json；`eia-split-extract/scripts/extract.py` 同步裁剪 chapter.yaml。
  **不再需要项目副本**——新项目直接 `init → split-sub → 每 sub parse/extract` 即零冗余。
- `render`/`verify`/`table_census` 已升级为通用模板（见下方"本次 skill 升级"），新子项目直接 `python3 skills/.../xxx.py --work-dir`。

## 本次 skill 升级（hainan_ch4 sub1 试点沉淀，2026-07-13）
| 文件 | 修复/增强 | 触发问题 |
|------|----------|---------|
| `extract/scripts/table_census.py` | `is_caption_line` 放宽为"表号后接 中文/数字/空白/标点"，排除内联引用 | 表标题后接年份(`表4.1-1 2022年…`)被漏识 → 权威集 C=0、表号误报"多号" |
| `render/scripts/render.py` | ① 输出包裹 `<!DOCTYPE>/<head><meta charset="utf-8">` ② 图占位靠 **figure 节点**（非段落内联检测，去重）③ 图标题扫 clean.txt 全文建立映射 | 浏览器中文乱码；图占位缺/重复 |
| `verify/scripts/verify_render.py` | HTML 文件名自适应（自动找 `chapter*.html`，不再硬编码 chapter2.html） | 子项目 chapter4.html 崩溃 |
| `parse` SKILL.md | 新增 Step 7d figure 节点、Step 7e scope 裁剪 | 大章拆子项目的方法论 |
| `extract` SKILL.md | 新增 Step 2.6 figure 节点、Step 2.7 scope 继承 | — |
| `render` SKILL.md | 经验段补 charset/图占位/子片段无 h1 | — |
| `verify` SKILL.md | 注意事项补文件名自适应/子项目零误差 | — |

> 子项目 render 的 `h1=0` 是预期的（整章 h1 合并时加），`compute_expected` 的 h1 FAIL 告警可忽略。

### 合并阶段标准做法（hainan_ch4 实证，2026-07-13 末）

子项目各自独立生成后，合并成整章。两种合并层级：

#### 层级 A：HTML 拼接（快速，无需统一 code）
- 各子项目已生成 render/LLM 版 HTML（各自 h2 起、h1=0）。
- 合并脚本读各 `subN/output/chapter{N}.html`（render）或 `chapter{N}_llm.html`（LLM），提取 `<body>` 内容，**剥离子段自带 h1**（子项目独立生成时常带 h1 章标题，否则合并后 h1 重复），拼接 + 顶部统一加 h1「第N章 标题」。
- 注意：子项目 LLM 版的 `<style>` 须与 render 版一致（或统一复用一份），否则两版视觉不一致。
- 优点：简单；缺点：合并产物是 HTML，无统一三件套，重跑需回各子项目。

#### 层级 B：统一 code 三件套 + 一次 LLM 生成（推荐，自包含）
- **生成合并三件套**：写一个合并生成器（如 `gen_merged_three_py.py`），读各 `subN/data/chapter.yaml`，合并成一套不带 `subN` 前缀的三件套（`{project}_ch{N}_*`），放在**合并版 `code/`**。
- **表格信息集中在合并版 `code/`**（关键）：
  - 把各 `subN/code/chapter4_tables.json`（render 表片段）合并成一份 `code/chapter4_tables.json`（按 `表X.Y-Z` key 合并）。
  - 同时合并 `all_tables_pdf.json`（表源）到 `code/all_tables_pdf.json`。
  - **getter 直接读同目录 `code/chapter4_tables.json`**，不再跨目录路由 `../subN/code/...`（合并 code 自包含，可独立重跑）。
- **用 LongCat 跑合并 `generate_chapterN()`** 一次生成整章 LLM HTML（如 145 个 getter 并发跑，非拼出来）。
- 优点：一份逻辑统一代码、重跑方便、表数据集中；缺点：需写合并生成器（可沉淀为 skill 参数化脚本）。

#### 表字段修复经验（合并前后都可能踩）
- **症状**：表的列数 ≠ 字段数，部分列头为空（源 PDF 抽取时合并单元格/跨页导致空补位）。
- **根因**：环评表常是**嵌套/合并表头**——第0行是分组类（如"调查时段""有效波高范围""栖息密度"跨多列），真正列名在第1数据行。PDF 抽取把分组行当表头、真实列名留空。
- **修复（根上改 `all_tables_pdf.json`，非 HTML 补丁）**：
  1. 浏览表标题 + 数据行，由 AI（QwenPaw QA Agent）基于内容推断每列真实字段名。
  2. 展平为**单一表头行**：空列用真实列名填（如 `栖息密度-环节动物`/`栖息密度-软体动物`，而非留空）。
  3. 若源 JSON 缺数据行（仅表头），用户直接提供数据则整表重建 `rows`（表头+数据行），标 `source="user_provided"`。
  4. 改 `all_tables_pdf.json` 的 `rows[0]`（表头）→ 重渲子项目（刷新 `chapter4_tables.json`）→ 重跑合并生成器 + 合并 LLM。
- **⚠️ 同步纪律**：修表后必须**同时重跑 render 合并版（merge 脚本）和 LLM 合并版（run_merged_llm）**，否则两版表头不一致（hainan_ch4 实测漏跑 render 合并导致旧空列头残留）。
- **已修复实例**（hainan_ch4）：表4.1-1/4.1-2（站点名提为列名）、4.1-7（浪高级展平）、4.5-10（栖息密度/湿重各分组）、4.5-12（年份/变化/分级）、4.5-15（多样性指数7列）、4.5-16（用户补数据+9列底质覆盖）。

#### 三段合并后结构示例（hainan_ch4）
```
hainan_ch4/
├── code/                    # 合并版(自包含)
│   ├── {project}_ch4_prompts.py / get_..._prompts.py / content_..._ch4.py
│   ├── chapter4_tables.json            # 合并 render 表片段
│   └── all_tables_pdf.json             # 合并表源
├── output/
│   ├── chapter4_llm_merged_unified.html   # 8123 /  (LongCat 跑合并三件套)
│   ├── chapter4_llm_merged.html           # HTML 拼接版(层级A)
│   └── chapter4_render_merged.html        # render 合并版
├── gen_merged_three_py.py / run_merged_llm.py
└── sub1/ sub2/ sub3/         # 子项目(各自 code/output 保留)
```

## 二次强化（hainan_ch5 sub1/sub2 实证，2026-07-14）

sub1/sub2 跑通后，回看踩坑把通用脚本与强制检查点打磨固化：

| 优化点 | 问题 | 修复(已固化到 skill) |
|--------|------|---------------------|
| 🔴 强制检查点脚本化 | 层级 PASS≠内容正确；PDF 提取常把邻表/续表误合并进同 key，render 按首行宽度截断静默吞末列 | `render/scripts/checkpoint_tables.py --work-dir` 逐表校验(列数一致/表头非垃圾/非空/caption匹配)；流水线内置闸门，不过不进 to-py |
| 🐛 拷贝脚本硬编码污染邻 sub | sub2 的 `gen_chapter.py` 把 WORK_DIR/PROJECT 写死成 sub1 → 写到邻 sub + import 报错 | `generate/scripts/run_generate.py` + `to-py/scripts/gen_three_py.py` 全参数化，从 project.yaml 自动推导，禁硬编码 |
| ⚠️ checkpoint 假阳性 | 字段内空格("油品类 别")被误判为垃圾表头 | 判定只认正文标点(。，；)或单格>40字，空格分隔合法字段不算垃圾 |
| 📋 缺端到端串联 | 每 sub 手动 cp/改值/置标志/跑5步易漏 | `generate/scripts/run_sub_pipeline.py --work-dir` 串 render→checkpoint闸门→to-py→generate→挂8123；闸门不过即中止 |
| 📝 表 getter 命名纪律 | 命名不含 `_tab`/`figure` 会把表/图误送 LLM | 生成器固化 `_tab`/`figure` 后缀；generate 运行器据此跳过 LLM |

> 经验:**项目代码(硬编码脚本)归项目，通用模板沉淀进 skill**。sub1/sub2 的 `data/gen_three_py.py`/`gen_chapter.py` 属项目副本；新 sub 直接复用 skill 的 `scripts/` 参数化版，勿再手改硬编码。
> **段落正文在 `node['paragraphs']`(非 `content`)**：ch5 chapter.yaml 段落 `content` 为空，生成器取 `paragraphs`。
> **源文档表号同名冲突**(如 5.4.2 节两张表都叫"表5.4-2")：extract 全局重排解结构层，但 render 的 `all_tables_pdf.json` 仍按原号塞 → 每 sub 需手工修(截断/重建)。未来应在表普查对齐阶段自动把续表重排为独立号(如 `5.4-2a`)，而非留到 render 后补。
