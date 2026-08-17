# AllSkills - Claude Code 技能包

这是一个完整的 Claude Code 技能集合，包含 40+ 个预配置的技能，用于提升 AI 辅助编程的效率和质量。

## 快速安装

### 方法一：克隆仓库（推荐）

```bash
# 1. 克隆技能包到本地
git clone https://github.com/Li230/AllSkills.git ~/.claude/skills-backup

# 2. 备份现有技能（如果有）
if [ -d ~/.claude/skills ]; then
    mv ~/.claude/skills ~/.claude/skills.old
fi

# 3. 创建符号链接或复制
ln -s ~/.claude/skills-backup ~/.claude/skills
# 或者复制：cp -r ~/.claude/skills-backup ~/.claude/skills
```

### 方法二：直接复制

```bash
# 克隆后直接复制
git clone https://github.com/Li230/AllSkills.git /tmp/AllSkills
cp -r /tmp/AllSkills/* ~/.claude/skills/
```

## 技能列表

### 核心流程技能

| 技能 | 用途 |
|------|------|
| `using-superpowers` | 技能系统入口，每次对话自动检查 |
| `brainstorming` | 编写代码前的苏格拉底式设计 refine |
| `writing-plans` | 详细的实现计划拆解 |
| `executing-plans` | 批量执行计划，带人工检查点 |
| `using-git-worktrees` | 创建隔离的 Git 工作区 |

### 开发流程技能

| 技能 | 用途 |
|------|------|
| `test-driven-development` | TDD 红 - 绿 - 重构循环 |
| `systematic-debugging` | 四阶段系统性调试 |
| `verification-before-completion` | 完成前验证 |
| `subagent-driven-development` | 多子代理并行开发 |
| `dispatching-parallel-agents` | 并行子代理调度 |

### 代码评审技能

| 技能 | 用途 |
|------|------|
| `requesting-code-review` | 代码评审请求 |
| `receiving-code-review` | 接收评审反馈 |
| `finishing-a-development-branch` | 完成开发分支 |
| `frontend-review-skill` | 前端边界验收（内存/资源/安全 10 维度，分级报告+修复代码+评分） |

### 文件操作技能

| 技能 | 用途 |
|------|------|
| `docx` | Word 文档操作 (.docx) |
| `xlsx` | 电子表格操作 (.xlsx/.csv) |
| `pdf` | PDF 文件操作 |
| `pptx` | PowerPoint 演示文稿操作 |

### 元技能

| 技能 | 用途 |
|------|------|
| `selfImprove` | 捕获学习、错误、修正 |
| `project_memory_manager` | 跨会话记忆管理 |
| `writing-skills` | 创建新技能的方法论 |

### 设计技能

| 技能 | 用途 |
|------|------|
| `frontend-design` | 高质量前端界面设计（独特、生产级 UI） |
| `superdesign` | 在 Superdesign 画布上设计/重设计前端 UI、复刻现有界面、提取设计系统、构建可复用组件、制作海报/营销图 |

### EIA 环评拆分流水线（eia-split/）

环评报告章节拆分完整流水线：init → split-sub → parse → extract → render → to-py → generate → verify → report

| 技能 | 用途 |
|------|------|
| `eia-split-init` | 初始化环评章节划分工作流 |
| `eia-split-split-sub` | 大章拆分子项目 |
| `eia-split-parse` | 解析环评 PDF 结构 |
| `eia-split-extract` | 提取环评内容到结构化 YAML（表普查） |
| `eia-split-render` | Jinja2 渲染 HTML（表格确定性渲染，不调 LLM） |
| `eia-split-to-py` | 生成 prompts/getter/content 三件套 |
| `eia-split-generate` | 调用 LLM 生成章节 HTML（表走 render 片段） |
| `eia-split-verify` | render 后质量闸门（表格与 PDF/txt 比对至零误差） |
| `eia-split-report` | 收尾校验（三方结构回归 + 一致性比对） |

### OpenSpec 工作流（openspec/）

基于 OpenSpec CLI 的完整变更管理流程：install → init → onboard → new → explore → continue → ff → config → schema → apply → verify → sync → archive → bulk-archive → update

| 技能 | 用途 |
|------|------|
| `openspec-install` | 全局安装 OpenSpec CLI |
| `openspec-initial` | 在项目中初始化 OpenSpec |
| `openspec-onboard` | 引导式完整工作流入门 |
| `openspec-new` | 新建 OpenSpec change |
| `openspec-explore` | 需求探索与问题澄清 |
| `openspec-continue` | 按依赖链继续创建 artifact |
| `openspec-ff` | 快速生成全部规划 artifacts |
| `openspec-config` | 配置项目与全局设置 |
| `openspec-schema` | 自定义工作流 schema |
| `openspec-apply` | 按 tasks 实现 change |
| `openspec-verify` | 验证实现一致性 |
| `openspec-sync` | delta specs 同步进主 specs |
| `openspec-archive` | 归档已完成的 change |
| `openspec-bulk-archive` | 批量归档多个 changes |
| `openspec-update` | 升级 CLI 后重新生成指令 |

### Flow 工作流（flow-/）

opsx-flow 的 6 阶段子技能（explore → proposal → plan → apply → verify → archive），由 `opsx-flow` 总览调度：

| 技能 | 用途 |
|------|------|
| `flow-new` | 创建变更脚手架（openspec/changes/<name>/ + 执行契约） |
| `flow-explore` | Phase 1 需求探索与质询（苏格拉底式提问挖透边界） |
| `flow-proposal` | Phase 2 方案构建（产出 proposal.md + specs delta） |
| `flow-plan` | Phase 3 原子任务规划（design.md + tasks.md） |
| `flow-apply` | Phase 4 执行+调度（按 tasks 调度 skill，质量闸门兜底） |
| `flow-verify` | Phase 5 验证 + 换模型独立审查，防自审走过场 |
| `flow-archive` | Phase 6 归档收尾（更新 STATUS/记忆/最终 checkpoint） |

## 技能使用方法

在 Claude Code 中，使用 `Skill` 工具调用技能：

```
/技能名称
```

例如：
- `/brainstorming` - 开始设计讨论
- `/test-driven-development` - 启动 TDD 流程
- `/project_memory_manager` - 加载项目记忆

## 技能优先级

1. **用户明确指令** (CLAUDE.md 等) — 最高优先级
2. **Superpowers 技能** — 覆盖默认系统行为
3. **默认系统提示** — 最低优先级

**关键规则**：如果有 1% 的可能性某个技能适用，必须调用该技能。

## 目录结构

```
skills/
├── SKILLS.md                       # 技能索引文件
├── README.md                       # 本说明
├── brainstorming/                  # 设计 refine
├── dispatching-parallel-agents/    # 并行代理调度
├── docx/                           # Word 文档操作
├── ds-competition/                 # 数据科学竞赛工作流
├── eia-split/                      # 环评拆分流水线（9 子技能）
├── executing-plans/                # 计划执行
├── finishing-a-development-branch/ # 分支完成
├── flow-apply/                     # Flow Phase 4 执行调度
├── flow-archive/                   # Flow Phase 6 归档
├── flow-explore/                   # Flow Phase 1 需求探索
├── flow-new/                       # Flow 变更脚手架
├── flow-plan/                      # Flow Phase 3 任务规划
├── flow-proposal/                  # Flow Phase 2 方案构建
├── flow-verify/                    # Flow Phase 5 验证审查
├── frontend-design/                # 前端设计
├── frontend-review-skill/          # 前端边界验收
├── openspec/                       # OpenSpec 工作流（14 子技能）
├── opsx-flow/                      # OpenSpec×Superpowers 编排器
├── pdf/                            # PDF 操作
├── pptx/                           # PowerPoint 操作
├── project_memory_manager/         # 记忆管理
├── py-study/                       # Python 数据科学教学
├── python-quality-gate/            # Python 质量硬闸门
├── python-quality-guide/           # Python 质量方法论
├── receiving-code-review/          # 接收评审
├── requesting-code-review/         # 请求评审
├── selfImprove/                    # 自我改进
├── study_master/                   # AI 学习助手
├── subagent-driven-development/    # 子代理开发
├── superdesign/                    # Superdesign 画布 UI 设计
├── systematic-debugging/           # 系统调试
├── tabular-ml-prep/                # 表格 ML 预处理
├── test-driven-development/        # TDD
├── using-git-worktrees/            # Git 工作区
├── using-superpowers/              # 技能系统入口
├── verification-before-completion/ # 完成验证
├── writing-plans/                  # 编写计划
├── writing-skills/                 # 编写技能
└── xlsx/                           # Excel 操作
```

## 更新技能

```bash
cd ~/.claude/skills
git pull origin main
```

## 贡献

欢迎提交 Issue 和 Pull Request 来改进这些技能！

## 许可证

MIT License - 见 LICENSE 文件

## 相关链接

- [Claude Code 官方文档](https://claude.ai/code)
- [GitHub 仓库](https://github.com/Li230/AllSkills)
### 学习技能

| 技能 | 用途 |
|------|------|
| `study_master` | AI 学习助手：AI 导师教学 + Zettelkasten 知识串联 + 学习日志管理（学习/复习/串联触发） |

### 数据科学技能

| 技能 | 用途 |
|------|------|
| `ds-competition` | 数据科学竞赛端到端工作流（Kaggle/天池：验证设计、GBM 基线、调优、集成、提交校验） |
| `tabular-ml-prep` | 表格/结构化数据 ML 预处理（12 步验证驱动的 EDA/清洗/特征工程） |
| `py-study` | Python 数据科学小老师（从零讲 pandas/numpy/sklearn，分层教学 + 练习检查） |

### 自建工作流与质量约束

| 技能 | 用途 |
|------|------|
| `opsx-flow` | OpenSpec × Superpowers 整合编排器（六阶段工作流 + 调度表 + 质量闸门，触发词："走流程"） |
| `python-quality-guide` | Python 高质量编程方法论（软约束） |
| `python-quality-gate` | Python 代码质量硬闸门（flake8 + black + pytest 全绿才放行） |

> **opsx-flow v3.0**: 已拆分为 8 个独立 skill（opsx-flow / opsx-new / opsx-explore / opsx-proposal / opsx-plan / opsx-apply / opsx-verify / opsx-archive），详见上方 SKILLS.md。
