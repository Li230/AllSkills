---
description: Use this skill when initializing an EIA (environmental impact assessment)
  report chapter splitting workflow. Triggers include "初始化环评划分", "eia-split-init",
  "开始环评分割", "环评prompt划分初始化". Creates work directory, writes project.yaml metadata,
  prepares for the 5 subsequent skills (parse→extract→render→verify→report).
name: eia-split-init
---

# EIA Split Init — 环评章节划分初始化

初始化环评报告章节划分工作流。创建工作目录、写入项目元信息，为后续 skill 提供基础。完整流水线有两条路径：
- **确定性路径**：parse → extract → render → verify → report（不调用 LLM，适合结构预览/校验）
- **LLM 生成路径**：parse → extract → to-py → generate（eia-split-generate，跑 LLM）→ report（校验）

两条路径共用 parse/extract；render 与 to-py+generate 二选一产出 HTML，最终都经 report 校验（含重复标题/完整性检查）。

## 何时触发

- 用户说「初始化环评划分」「开始环评分割」「eia-split-init」
- 用户提供 PDF 路径和章节号，要求开始处理

## 前置条件

- 用户提供：项目名（如 hainan）、PDF 文件路径、章节号（如 3）
- PDF 文件真实存在

## 工作流程

### Step 1: 确认输入参数

向用户确认三个必填参数：

| 参数 | 说明 | 示例 |
|------|------|------|
| `project` | 项目简称（英文，用于目录名和变量名前缀） | `hainan` |
| `pdf_path` | PDF 文件绝对路径 | `/Users/.../第三章-规划协调性分析.pdf` |
| `chapter` | 章节号（整数） | `3` |

可选参数：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `chapter_title` | 从 PDF 推断 | 章节标题 |
| `format` | `flat` | HTML 格式：`flat`=纯段落+独立表格，`wrapped`=外层大表格 |

### Step 1.5: 🔴 命名规范（避免后期 `_full_` 后缀整理）
- **单章不拆 sub**（如 ch6 仅 9 页）：`project` 直接取 `hainan_chN`（N=章节号）。生成三件套天然为 `content_hainan_chN_chN.py` / `get_hainan_chN_chN_prompts.py` / `hainan_chN_chN_prompts.py` —— **与 ch4 完全同构，无 `_full_` 后缀**，省去后期整理。
- **拆 sub**（大章如 ch5）：各 sub 用独立目录 `hainan_chN/subK/`，`project=hainan_chN_subK`；合并产物放 `hainan_chN/`（顶层），`project=hainan_chN`（同构命名）。**禁止用 `_full_` 后缀污染模块名**（ch5 教训：full 工作区命名带 `_full_` 导致三件套后期手动改名）。
- 表号空间：extract 阶段按章节顺序全局规划连续表号，避免 sub 合并时表号冲突需后期重排。

### Step 2: 创建工作目录

```
{base_dir}/{project}/
├── data/          # 存放 PDF、txt、中间产物
├── code/          # 存放生成的代码（如需要）
└── output/        # 存放最终 HTML
```

`base_dir` 默认为 PDF 所在目录的父目录。如果 PDF 在 `/Users/x/公司/环评生成/海南省/data/第三章.pdf`，则 `base_dir` = `/Users/x/公司/环评生成`，工作目录 = `/Users/x/公司/环评生成/hainan/`。

但如果 `{base_dir}/{project}/` 已存在（如海南项目已存在），则复用现有目录。

### Step 3: 写入 project.yaml

在工作目录下创建 `project.yaml`：

```yaml
project: hainan
pdf_path: /Users/.../第三章-规划协调性分析.pdf
chapter: 3
chapter_title: 规划一致性和协调性分析
format: flat
table_mode: fields_only   # fields_only=只提字段名数据行留空 / full=完整提取
render_reviewed: false    # render 后用户人工审阅完置 true，report 阶段跳过重复抽查
work_dir: /Users/.../hainan/
status: initialized
created_at: 2026-07-09
pipeline:
  - init: done
  - parse: pending
  - extract: pending
  - render: pending
  - verify: pending
  - report: pending
```

### Step 4: 自检 — 目录结构完整性

执行以下检查：

```bash
# 1. 确认 PDF 文件存在
test -f "{pdf_path}" && echo "PDF exists" || echo "PDF NOT FOUND"

# 2. 确认工作目录已创建
test -d "{work_dir}/data" && test -d "{work_dir}/output" && echo "Dirs OK"

# 3. 确认 project.yaml 已写入且可解析
python3 -c "import yaml; yaml.safe_load(open('{work_dir}/project.yaml'))" && echo "YAML OK"
```

三项全部通过 → 自检 PASS。

### Step 5: 输出结果

告知用户：
- 工作目录路径
- project.yaml 路径
- 自检结果
- 下一步指引：「请执行 `eia-split-parse` 进行结构解析」

## 产物

| 文件 | 说明 |
|------|------|
| `{work_dir}/project.yaml` | 项目元信息，后续所有 skill 的入口 |
| `{work_dir}/data/` | 数据目录 |
| `{work_dir}/output/` | 输出目录 |

## 下一步

使用 **eia-split-parse** 进行 PDF 结构解析。标准命令（参数化，新项目直接复用）：
```bash
python3 skills/eia-split-parse/scripts/parse.py --work-dir <work_dir>
```
> 注：parse/extract/render 脚本均参数化（从 `project.yaml` 自动推导），勿手改硬编码副本。文件操作一律用 python，禁 shell `cd` 含中文路径。

## 注意事项

- 如果 `{project}/` 目录已存在且包含之前的数据，提示用户是否覆盖或继续。
- `format: flat` 对应海南港模式（纯段落+独立表格），`format: wrapped` 对应烟台港模式（外层大表格包裹）。当前版本优先支持 `flat`。
- PDF 路径必须用绝对路径，避免后续 skill 执行时路径解析问题。