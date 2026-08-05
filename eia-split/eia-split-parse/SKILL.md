---
description: Use this skill when parsing EIA report PDF structure. Triggers include
  "解析环评结构", "eia-split-parse", "解析章节结构", "提取PDF标题表格". Reads project.yaml, extracts
  PDF to txt, identifies chapter titles and table positions, outputs structure.json.
  Includes CP1 title completeness and CP2 table completeness self-checks.
name: eia-split-parse
---

# EIA Split Parse — 环评章节结构解析

读取 project.yaml，提取 PDF 文字，识别章节标题和表格位置，输出 structure.json。这是流水线的第二步，承接 eia-split-init。

## 何时触发

- 用户说「解析环评结构」「eia-split-parse」「解析章节结构」
- eia-split-init 完成后，用户要求继续

## 前置条件

- `project.yaml` 存在且 `status: initialized`
- PDF 文件存在

## 工作流程

### Step 1: 读取 project.yaml

```python
import yaml
config = yaml.safe_load(open(f"{work_dir}/project.yaml"))
pdf_path = config["pdf_path"]
chapter = config["chapter"]
work_dir = config["work_dir"]
```

### Step 2: PDF → txt 提取

使用 pdfplumber 提取文字（优先）或 pypdf（降级）：

```python
# 优先使用 pdfplumber
try:
    import pdfplumber
    text_parts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text_parts.append(page.extract_text() or "")
    txt = "\n".join(text_parts)
except ImportError:
    # 降级到 pypdf
    from pypdf import PdfReader
    reader = PdfReader(pdf_path)
    txt = "\n".join(page.extract_text() or "" for page in reader.pages)
```

将 txt 保存到 `{work_dir}/data/chapter{chapter}-raw.txt`。

### Step 3: txt 清理

对原始 txt 做机械清理（不改正文文字内容）：

1. **去除页码行**：纯数字行（1-3位数字）→ 删除
2. **去除页眉页脚**：匹配"环境影响报告书"等重复出现的行 → 删除
3. **合并断行**：一行末尾不是句号/问号/叹号/引号/冒号，且下一行以非数字非标点开头 → 合并为一行
4. **去除行内多余空格**：连续 2+ 个空格 → 1 个空格
5. **保留原始行号映射**：清理后的行号 → 原始行号的映射表，便于后续追溯

保存清理后的 txt 到 `{work_dir}/data/chapter{chapter}-clean.txt`。

### Step 4: 识别章节标题

用正则匹配标题层级（以第三章为例，chapter=3）：

```python
import re

# 一级标题: "3 规划一致性和协调性分析"
level1_pattern = re.compile(rf'^{chapter}\s+(.+)')

# 二级标题: "3.1 与上层规划及重要文件的一致性分析"
level2_pattern = re.compile(rf'^{chapter}\.(\d+)\s+(.+)')

# 三级标题: "3.1.1 中共中央、国务院关于..."
level3_pattern = re.compile(rf'^{chapter}\.(\d+)\.(\d+)\s+(.+)')

# 四级（及更深）标题: "3.1.1.1 子项名称"
# ⚠️ 环评报告常含 4 级甚至更深层小节（如港口规划"2.2.3.3 陆域布置规划"）。
#    必须识别为独立标题写入 structure.json（带 level 字段），禁止并入三级段落文本，
#    否则下游 extract 会把标题当正文、LLM 重复生成 → 标题重复 bug（hainan_ch2 实测）。
# ⚠️ 编号后**允许无空格**：源报告常把四级标题写为 "3.1.1.1子项名称"（编号顶头无空格，
#    如 hainan_ch4 sub3 的 "4.5.1.1保护区范围"）。正则须用 \s* 而非 \s+，否则该标题
#    被漏识别、退化成父段落正文首行 → 视觉缺失 h4 层级。实测：sub3 改 \s+→\s* 后
#    h4 计数 7→8，4.5.1.1 被正确识别。
level4_pattern = re.compile(rf'^{chapter}\.(\d+)\.(\d+)\.(\d+)\s*(.+)')
# 通用深层（N>=4）：章节可能更深的层级，按点号段数判定 level
leveln_pattern = re.compile(rf'^{chapter}(\.\d+)+?\s+(.+)')
```

**误匹配排除规则**（关键！）：
- 标题行通常较短（<50字符），且后面紧跟正文
- "3.54 万平方公里" 这种数字开头正文行 → 排除（小数点后超过1位数字）
- "3.3-4）。其中..." 这种带标点的行 → 排除
- 验证方法：匹配到的行，检查是否在已知标题列表的上下文中出现（前后是否有其他标题）

对每个三级标题记录：
```json
{
  "num": "3.1.1",
  "level": 3,
  "title": "中共中央、国务院关于支持海南全面深化改革开放的指导意见",
  "line": 8,
  "section": "3.1",
  "section_title": "与上层规划及重要文件的一致性分析"
}
```

### Step 5: 识别表格位置

用正则匹配表格标题：

```python
# 表格标题: "表 3.2-1 马岛主要保护对象的保护目标"
table_pattern = re.compile(rf'表\s*{chapter}\.(\d+)-(\d+)\s+(.+)')
```

对每个表格记录：
```json
{
  "table_id": "3.2-1",
  "title": "马岛主要保护对象的保护目标",
  "line": 687,
  "end_line": 725,  // 下一个标题或表格之前的行
  "section": "3.2"
}
```

**表格结束行判定**：从表格标题行往下扫描，遇到以下情况之一视为表格结束：
- 下一行是新的三级标题（3.x.y）
- 下一行是新的表格标题（表X.Y-Z）
- 连续 2 个空行
- 段落文字（非表格数据行，通过"是否包含表格字段名"判断）

### Step 6: 输出 structure.json

```json
{
  "chapter": 3,
  "chapter_title": "规划一致性和协调性分析",
  "total_lines": 1417,
  "effective_lines": 1380,
  "titles": [
    {"num": "3.1", "level": 2, "title": "...", "line": 7},
    {"num": "3.1.1", "level": 3, "title": "...", "line": 8, "section": "3.1"},
    {"num": "3.1.1.1", "level": 4, "title": "...", "line": 12, "section": "3.1", "parent": "3.1.1"},
    ...
  ],
  "tables": [
    {"table_id": "3.2-1", "title": "...", "line": 687, "end_line": 725, "section": "3.2"},
    ...
  ],
  "txt_path": "{work_dir}/data/chapter3-clean.txt",
  "raw_txt_path": "{work_dir}/data/chapter3-raw.txt"
}
```

保存到 `{work_dir}/data/structure.json`。

### Step 7: 🤖 自检 CP1 — 三级标题完整性

**目的**：确保所有三级章节标题都被正确识别，无遗漏无多余。

```python
def check_title_completeness(structure, txt_path):
    txt_lines = open(txt_path).readlines()
    issues = []
    # 1. 正则提取所有可能的三级标题行
    all_matches = []
    for i, line in enumerate(txt_lines):
        line = line.strip()
        m3 = re.match(r'^(\d+\.\d+\.\d+)\s+(.+)', line)
        if m3 and is_valid_title(line, m3):
            all_matches.append((m3.group(1), i+1))
    # 2. 双向比对
    structure_nums = [t["num"] for t in structure["titles"] if t["level"] == 3]
    txt_nums = [m[0] for m in all_matches]
    missing = set(txt_nums) - set(structure_nums)
    extra = set(structure_nums) - set(txt_nums)
    if missing:
        issues.append(f"遗漏标题: {missing}")
    if extra:
        issues.append(f"多出标题: {extra}")
    # 3. 编号连续性检查
    for i in range(1, len(structure_nums)):
        prev = structure_nums[i-1].split('.')
        curr = structure_nums[i].split('.')
        if len(prev) == 3 and len(curr) == 3 and prev[0] == curr[0] and prev[1] == curr[1]:
            if int(curr[2]) != int(prev[2]) + 1:
                issues.append(f"编号不连续: {structure_nums[i-1]} → {structure_nums[i]}")
    return issues
```

**误匹配排除函数**：
```python
def is_valid_title(line, match):
    num = match.group(1)
    parts = num.split('.')
    for p in parts:
        if len(p) > 2:
            return False
    if line.rstrip().endswith(('。', '；', '，', '。', '.')):
        return False
    if len(line) > 60:
        return False
    return True
```

### Step 7b: 🤖 自检 CP1-二级 — 二级标题完整性

**目的**：确保 `section_titles`（如 3.1/3.2/3.3/3.4）全部被识别，**防止二级节在解析阶段静默丢失**（如之前的 3.4 节丢失 bug）。

```python
def check_section_completeness(level2, lines, chapter):
    issues = []
    all_sec_nums = set()
    for raw in lines:
        line = raw.strip()
        m = re.match(rf'^{chapter}\.(\d+)\s+(.+)', line)
        if m:
            num = f"{chapter}.{m.group(1)}"
            if is_valid_section(num):   # 1<=x<=15，排除 3.54 等误匹配
                all_sec_nums.add(num)
    located = set(s["num"] for s in level2)
    missing = all_sec_nums - located
    if missing:
        issues.append(f"遗漏二级标题: {sorted(missing)}")
    extra = located - all_sec_nums
    if extra:
        issues.append(f"多余二级标题: {sorted(extra)}")
    return issues

def is_valid_section(num_str):
    parts = num_str.split('.')
    if len(parts) != 2:
        return False
    try:
        x = int(parts[1])
    except ValueError:
        return False
    return 1 <= x <= 15
```

### Step 7c: 🤖 自检 CP1-四级 — 四级（及更深）标题完整性

**目的**：确保四级（及更深）小节标题被识别，防止像"2.2.3.3 陆域布置规划"这类深层标题在解析阶段静默丢失（曾导致下游 LLM 把标题当正文、重复生成）。

```python
def check_sublevel_completeness(chapter, lines):
    issues = []
    pat4 = re.compile(rf'^{chapter}\.(\d+\.\d+\.\d+)\s*(.+)')
    txt_full = set()
    for raw in lines:
        m = pat4.match(raw.strip())
        if m and is_valid_title(raw.strip(), m):
            txt_full.add(m.group(1))
    located = set(t["num"] for t in structure["titles"] if t.get("level", 0) >= 4)
    missing = txt_full - located
    if missing:
        issues.append(f"遗漏四级(及更深)标题: {sorted(missing)}")
    return issues
```

> ⚠️ 章节可能含 4 级甚至更深层小节。parse 阶段必须把它们作为独立 `level>=4` 标题写入 structure.json，绝不能并入三级段落文本。

### Step 7d: 🖼️ 图标题节点（figure）识别

**目的**：环评报告图片（图X.X-X）在 PDF 提取时未被抽取为图，需在 HTML 渲染出**图片占位提示**（含图标题）。在 parse 阶段把「行首以图号开头」的行识别为独立 figure 节点，供 render 插占位。

```python
figures = []
for idx, line in enumerate(cleaned, 1):
    s = line.strip()
    mf = re.match(r"^图\s*(\d+)\.(\d+)-(\d+)\s*(.*)$", s)
    if mf:
        figures.append({"fig_id": f"图{mf.group(1)}.{mf.group(2)}-{mf.group(3)}",
                        "title": mf.group(4).strip(), "line": idx, "level": 5, "figure": True})
```

> 经验：图标题行常紧贴表格行，若表 `end_line` 计算吞掉图行，图占位会丢失 → 表 end_line 判定须把图行（`图\s*\d+\.\d+-\d+`）作为边界标记之一（与 H2/H3/表同级）。（hainan_ch4 sub1 实证）

### Step 7e: 🔪 子任务 scope 裁剪（大章拆子项目时，保证 txt 零冗余）

**场景**：整章过大需拆成多个子项目（如 ch4 拆 3 段：4.1-4.2 / 4.3-4.4 / 4.5-4.6）。为防段落被切断，子 PDF 切分时**每边多切 2 页（overlap）**；但 overlap 会让子 PDF 含邻居节内容。解决：**用 h 标题作为硬边界裁剪 txt**——

1. `project.yaml` 写 `scope_sections: ["4.1","4.2"]`（本子任务职责节）。
2. parse 先全量提取 + 识别全部标题/表（含 overlap 冗余页）。
3. 按 scope 的**首个 H2 行号**起、到**下一个非 scope H2 之前**止，裁剪 txt 行范围；标题/表也只保留 `scope_sections` 内的。
4. 下游 extract/render 只处理裁剪后 txt → **HTML 天然无重复**，合并时直接拼 3 段即可。

```python
scope_set = set(cfg.get("scope_sections", []))
def top_section(num): return ".".join(num.split(".")[:2])
scope_h2 = [h for h in h2 if h["num"] in scope_set]
first_line = scope_h2[0]["line"]
nxt = [h["line"] for h in h2 if h["num"] not in scope_set and h["line"] > first_line]
end_line = (nxt[0] - 1) if nxt else len(cleaned)
crop = cleaned[first_line - 1:end_line]
# 标题/表/图: 只留 top_section in scope_set 者
```

> 经验（hainan_ch4 sub1）：overlap 保证 4.2 结尾段落完整不切断；scope 裁剪用 `4.3 区域资源概况` 作边界，把 overlap 进来的 4.3 页剔除 → txt 零冗余。
> 注意：这是相对 ch2（整章）的新增强，建议写成参数化脚本，新项目复用。

### Step 8: 🤖 自检 CP2 — 表格完整性

**目的**：确保所有表格都被定位，无遗漏。

```python
def check_table_completeness(structure, txt_path):
    txt = open(txt_path).read()
    issues = []
    
    # 1. 正则扫描 txt 中所有"表X.Y-Z"模式
    all_tables = re.findall(rf'表\s*{chapter}\.\d+-\d+', txt)
    all_table_ids = set(t.replace(' ', '').replace('表', '') for t in all_tables)
    
    # 2. 与 structure 中的表格比对
    structure_ids = set(t["table_id"] for t in structure["tables"])
    
    missing = all_table_ids - structure_ids
    if missing:
        issues.append(f"遗漏表格: {missing}")
    
    # 3. 检查每个表格的 end_line 是否合理
    for table in structure["tables"]:
        if table["end_line"] <= table["line"]:
            issues.append(f"表格 {table['table_id']} 结束行 <= 起始行")
    
    return issues
```

### Step 9: 更新 project.yaml

```yaml
status: parsed
pipeline:
  - init: done
  - parse: done
  - extract: pending
  ...
```

### Step 10: 输出结果

告知用户：
- txt 提取结果（总行数、有效行数）
- 识别到的标题数（二级 N 个、三级 N 个）
- 识别到的表格数（N 个）
- 自检 CP1/CP2 结果
- 下一步指引：「请执行 `eia-split-extract` 进行内容提取」

## 产物

| 文件 | 说明 |
|------|------|
| `{work_dir}/data/chapter{N}-raw.txt` | PDF 原始提取文字 |
| `{work_dir}/data/chapter{N}-clean.txt` | 清理后文字 |
| `{work_dir}/data/structure.json` | 章节结构+表格位置 |

## 自检清单

| 检查点 | 检查内容 | 失败处理 |
|--------|---------|---------|
| CP1 三级标题完整性 | 三级标题无遗漏无多余，编号连续 | 调整正则/排除规则，重新解析 |
| CP1-二级 二级标题完整性 | section_titles 无遗漏无多余（防 3.4 静默丢失） | 调整 is_valid_section，重新解析 |
| CP2 表格完整性 | 所有"表X.Y-Z"都被定位 | 补充遗漏表格，重新生成 structure.json |

自检失败时自动修复（最多 3 轮），仍失败则输出问题清单让用户决策。

## 下一步

使用 **eia-split-extract** 进行内容提取。

## 注意事项

- PDF 提取质量取决于 PDF 本身。如果 txt 提取结果大量乱码，提示用户可能需要 OCR。
- 🔴 **工程铁律（避坑）**：文件操作（复制/改名/字符串替换/读 json）一律用 **python**（`shutil`/`json`/`字符串替换`），**禁止 shell `cd` 含中文路径**（变量展开会致 `$BASE` 为空、cd 报 `too many arguments`）；多行 shell 命令 + 中文 + `echo` 易解析混乱，统一走 python 脚本。
- 表号/四级标题允许无空格写法（`表6.2-3` / `4.5.1.1保护区范围`），正则须用 `\s*`。
- txt 清理只做机械操作（去空格、去页码、合并断行），**不改正文文字**。
- 误匹配排除是 CP1 的核心难点。常见误匹配：正文中的数字编号（如"3.54万平方公里"）、带编号的列表项。通过行长、标点、数字位数三重过滤排除。
- 如果 pdfplumber 未安装，降级到 pypdf，但表格结构信息会更少。
- **⚠️ 四级标题无空格写法**（hainan_ch4 sub3 实测）：源报告四级标题可写为 `4.5.1.1保护区范围`（编号后无空格），四级正则须用 `\s*` 允许无空格，否则漏识成父段落正文。自检 CP1-四级 同样用 `\s*` 才能命中。
- **表号无空格写法**（hainan_ch4 sub3 实测）：`表4.5-1自然保护区...` 表号后无空格，表检测正则 `\s+`→`\s*` 同理。详见 eia-split-extract 注意事项。