---
name: eia_split_to_py
description: 根据chapter.yaml生成prompts、getter、content三件套。表格不从LLM生成——getter直接返回render产出的表HTML片段(output/chapter{N}_tables.json)，LLM只生成段落/sub4叙述文本。表格数据来源=render片段；PDF/txt仅作验证。
---

## 功能
从 `data/chapter.yaml` 生成多层结构 `.py`（支持任意标题深度 h1/h2/h3/h4…），对齐 `code/`。**表格免 LLM**：表内容来自 render 已渲染片段；LLM 仅生成叙述。

## 触发
「生成三个py」「拆三层文件」「导出py」或流水线第⑦步 `eia-split-to-py`。

## 前置
- `data/chapter.yaml` 通过验证
- `output/chapter{N}_tables.json`（render 产出的表片段映射）就绪
- `project.yaml`（project, chapter_title）
- ⚠️ **硬依赖**：`render_reviewed == true`（`eia-split-verify` 零误差 + 用户审核通过）。生成器/运行器前置检查此标志，否则**中止**并提示先跑 verify + 审核。表格 getter 读 `output/chapter{N}_tables.json`，若该文件缺失或表号未覆盖 → getter **优雅降级**（返回"未提取，请人工补充"占位），不得 KeyError 崩。
- 🔴 **强制检查点（render 后 Must）**：层级计数 PASS ≠ 内容正确。to-py 之前必须已跑过 `eia-split-render/scripts/checkpoint_tables.py`，确认**每张表列数一致、表头非垃圾、非空、caption 匹配**。任一不合格说明 `all_tables_pdf.json` 的 `rows` 在 extract/表普查阶段有误（邻表/续表误合并、表头被正文替换、行截断），须**回 render 阶段根上修 JSON 重渲**，绝不可带病进 to-py（LLM 不碰表，脏表会原样进最终 HTML）。

## 产出
| 文件 | 层 | 说明 |
|------|----|------|
| `{base}_ch{N}_prompts.py` | 模板 | 段落/小节 LLM 指令；表格为"插入已渲染表"指令 |
| `get_{base}_ch{N}_prompts.py` | 数据 | 段落 getter 返回 prompt；**表格 getter 返回 render 表片段（不调 LLM）** |
| `content_{base}_ch{N}.py` | 调度 | 拼接，表格直接插入 render 片段 |

## 通用脚本（推荐，新项目直接复用）
- `scripts/gen_three_py.py --work-dir <sub_dir>`：**参数化**，从 `project.yaml` 自动推导 `project`/`chapter`/前缀，**不硬编码**。读 chapter.yaml 生成 3 件套到 `code/`。
- ⚠️ **表 getter 命名须含 `_tab`、图 getter 须含 `figure`**：generate 运行器靠 `"_tab" in name or "figure" in name` 判断"跳过 LLM 直接返 render 片段"——命名不一致会把表/图误送 LLM（hainan_ch5 sub1 初版踩过）。生成器已固化此命名。
- ⚠️ **段落正文在 `node['paragraphs']`（非 `content`）**：ch5 的 chapter.yaml 段落 `content` 字段为空，正文在 `paragraphs` 列表——生成器取 `paragraphs` 而非 `content`（否则 LLM prompt 无参考文本）。

## 步骤
1. **确定参数**：从 `project.yaml` 读 `project`/`chapter`，动态推导前缀 `{project}_ch{chapter}_`（勿硬编码 `_ch3_`/`third_gh`）。
2. **生成文件**：`python3 gen_three_py.py --work-dir {work_dir}`，读 chapter.yaml 生成标准格式。
3. **验证**：导入 content，检查 `chapter_divide()` 数量；抽查 getter——**表格 getter 返回的是 render `<table>` 字符串而非 LLM 调用**。

## Prompt 格式标准（用户确认）
- **段落/小节 prompt（任意层级）**：节点按 `level` 渲染标题 `<h3>`/`<h4>`/`<h5>`；正文 `<p style="text-indent:2em;">`；结论 `<span style="color:blue;">`；`【】` 参考占位；输出示例完整。每标题仅一次，body 不含"编号 标题"前缀。
- **表格 prompt（非 LLM）**：指令为"在 `table_id` 位置插入 `output/chapter{N}_tables.json[table_id]` 的 HTML 片段"；**不要求 LLM 输出 `<table>`**。表格内协调性结论等沿用 JSON 数据（render 已标蓝）。

## 设计原则
1. **表格数据来源 = render 表片段**（确定性），LLM 不生成表、不碰 PDF/txt 取数。
2. **PDF/txt 仅验证**：generate 后用 grep 表号 + JSON 比对做完整性自检（表数/表号/空表），不作为数据来源。
3. 段落正文逐段列出；输出示例完整呈现。
4. 变量命名对齐：`{prefix}_{num_点号转下划线}_text` / 表格 `{prefix}_{num}_tab`（getter 返回片段）。
5. **递归 `sub4`/`children`**：逐条生成独立 prompt 与 getter，标题层级对应 `<h{n}>`。
6. **结构性问题根上修**：层级/重复类改 chapter.yaml + 生成器重跑，禁 HTML 补丁（`fix_h4_*`/`dedup_*` 反模式）。

## 注意事项
- 写入仅限 `code/`
- 表格 getter 读 `output/chapter{N}_tables.json`（render 产物）；失败回退读 `all_tables_pdf.json` 现渲
- 段落若含 `image_ref`，prompt 与产物插占位提醒（"原PDF图片未提取，请人工补充"），与 render 占位框一致
- 段落正文含标题残基用 `filter_title_residue()` 清理
- **后处理保真步骤可移除**（render 已带数据、LLM 不碰表）；保留可选空表自检
- **⚠️ table_id 取数反例（hainan_ch4 sub1）**：`chapter.yaml` 的 table 节点可能 `table_id=None`（仅 `table_title` 带"表X.Y-Z"），getter 若只从 `table_id` 提表号会得到空串 → 表降级占位（`<p class="caption">表</p><table>未提取</table>`）。**修复**：getter 从 `table_title`（`表4.1-1 ...`）正则提取 `\d+\.\d+-\d+` 作 tbl_id。`render.py` 的 `chapter{N}_tables.json` key 是 `"表X.Y-Z"`，`_render_table(tbl_id)` 拼 `"表"+tbl_id` 命中。generate 自检 `table=N` 会误判通过（降级表也算 `<table`），必须在 report 阶段用 `表X.Y-Z` caption 真实匹配校验表数。
- **⚠️ sub4 四级小节必须递归展开（hainan_ch2 回灌教训）**：若 `chapter.yaml` 段落节点含 `sub4` 嵌套列表（25 个四级节点），三件套生成器**必须递归展开 sub4**——每个 sub4 节点生成独立 prompt（`<h4>` 标题）+ getter，并纳入 `content` 的 getter 序列。否则 LLM 版 h4=0（render 有但 LLM 漏），导致层级不一致。通用 `to_py` 模板应内置 `build_sub4_prompt` + sub4 getter 递归。
- **⚠️ figure 节点注入（hainan_ch2 回灌）**：老章节 chapter.yaml 可能无 figure 节点（图只在段落内联引用），render 升级后支持 figure 占位但需节点驱动。回灌时用脚本扫 clean.txt 行首图号行（支持一行多图如"图2.6-1...图2.6-2"），按 clean.txt 真实 H2 行号归 section，注入 figure 节点；重渲即出虚线框占位。注入前先清空旧 figure 防叠加。
- **⚠️ 标题级别动态化（hainan_ch4 sub2/sub3 + hainan_ch5 sub3）**：① 段落 prompt 的 `<h{n}>` 级别**不能硬编码 h3**。须按 `lvl = len(num.split('.'))` 判定：`4.3.1`→h3、`4.3.2.1`→h4、`4.5.7.2`→h4。② **section 标题同样动态化**：子项目按 H4 切分（如 sub3=`5.4.2.1`）时 section 是 h4 级，render 已按 `len(section['id'].split('.'))` 渲染 `<h4>`；to-py 生成器对 section 首项若生成 prompt，其标题级别也须对齐（sub3 首个 paragraph 无 num/title，由 render 的 section 标题承担，生成器无需额外 h2）。若段落 prompt 硬编码 `<h3>` 而实际是 h4 → LLM 版层级与 render 不一致。生成器须用 `<h{lvl}>`。
- **⚠️ 空体标题必须显式保留（hainan_ch4 sub2）**：容器型 H3/H4（如 4.4.3 区域大气环境现状，正文在其下级小节）常无独立正文 → LLM 偶会跳过该标题导致层级缺漏。prompt 须加指令"即使无独立正文也必须保留 `<hN>编号 标题</hN>`"。否则 LLM 版 h3/h4 计数少于 render。
- **⚠️ 同级相邻 h4 易被 LLM 吞掉中间项（hainan_ch4 sub3 实测）**：4.5.7.1/2/3 三个相邻四级标题，LLM 生成时偶会把中间的 `4.5.7.2 圆尾鲎和中国鲎` 整个标题行吞掉（内容混进 4.5.7.1/4.5.7.3）。修复：对 `lvl>=4` 的节点（无论有无正文）prompt 强制加指令"必须**单独、原样**输出 `<h4>编号 标题</h4>`，不得与相邻同级标题合并或省略"。重生成三件套+重跑 LLM 后 h4 计数 7→8 与 render 对齐。
- **⚠️ 同源样式一致（hainan_ch4 sub3）**：to-py 生成的 `<hN>` 标签本身正确（由 `len(num.split('.'))` 定级），但 LLM 版 HTML 的 `<style>` 须与 render 版**完全一致**（例如都仅 `body{...}`、无额外 hN 规则，或都含同套 hN 规则）。若 render 版裸默认 h4、LLM 版却加了 h4 绿色规则，两者视觉不一致 → 用户核验会要求对齐。generate 脚本的 LLM 版 `<style>` 块应直接复用 render 版的 `<style>` 字符串。

## 下一步
eia-split-generate 调 LLM 产 HTML（表插 render 片段）→ eia-split-report 校验

## 标准命令
```bash
python3 skills/eia-split-to-py/scripts/gen_three_py.py --work-dir <work_dir>
```
🔴 工程铁律：文件操作用 python，禁 shell cd 中文路径。
