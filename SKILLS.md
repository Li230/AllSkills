# Skills

## Installed Skills

### Superpowers (from obra/superpowers)
- [using-superpowers](using-superpowers/SKILL.md) - Superpowers 技能系统介绍
- [brainstorming](brainstorming/SKILL.md) - 编写代码前的苏格拉底式设计 refine
- [using-git-worktrees](using-git-worktrees/SKILL.md) - 创建隔离的 Git 工作区
- [writing-plans](writing-plans/SKILL.md) - 详细的实现计划拆解
- [executing-plans](executing-plans/SKILL.md) - 批量执行计划，带人工检查点
- [subagent-driven-development](subagent-driven-development/SKILL.md) - 多子代理并行开发
- [test-driven-development](test-driven-development/SKILL.md) - TDD 红 - 绿 - 重构循环
- [systematic-debugging](systematic-debugging/SKILL.md) - 四阶段系统性调试
- [verification-before-completion](verification-before-completion/SKILL.md) - 完成前验证
- [requesting-code-review](requesting-code-review/SKILL.md) - 代码评审请求
- [receiving-code-review](receiving-code-review/SKILL.md) - 接收评审反馈
- [finishing-a-development-branch](finishing-a-development-branch/SKILL.md) - 完成开发分支
- [dispatching-parallel-agents](dispatching-parallel-agents/SKILL.md) - 并行子代理调度
- [writing-skills](writing-skills/SKILL.md) - 创建新技能的方法论

### File Operations
- [docx](docx/SKILL.md) - 创建、读取、编辑或操作 Word 文档（.docx 文件）
- [xlsx](xlsx/SKILL.md) - 打开、读取、编辑或创建电子表格（.xlsx、.xlsm、.csv、.tsv）
- [pdf](pdf/SKILL.md) - 读取、提取、合并、拆分、添加水印或创建 PDF 文件
- [pptx](pptx/SKILL.md) - 创建、读取、编辑或修改 PowerPoint 演示文稿（.pptx 文件）

### Design
- [frontend-design](frontend-design/SKILL.md) - 创建独特、生产级的前端界面，具有高设计质量

### Meta Skills
- [selfImprove](selfImprove/SKILL.md) - 捕获学习、错误和修正，实现持续改进
- [project_memory_manager](project_memory_manager/SKILL.md) - 跨会话记忆管理，读取/维护项目记忆

### File Operations
- [docx](docx/SKILL.md) - 创建、读取、编辑或操作 Word 文档（.docx 文件）
- [xlsx](xlsx/SKILL.md) - 打开、读取、编辑或创建电子表格（.xlsx、.xlsm、.csv、.tsv）
- [pdf](pdf/SKILL.md) - 读取、提取、合并、拆分、添加水印或创建 PDF 文件
- [pptx](pptx/SKILL.md) - 创建、读取、编辑或修改 PowerPoint 演示文稿（.pptx 文件）

### EIA 环评拆分流水线
- [eia-split-init](eia-split/eia-split-init/SKILL.md) - 初始化环评章节划分工作流（工作目录 + project.yaml）
- [eia-split-split-sub](eia-split/eia-split-split-sub/SKILL.md) - 大章拆分子项目（ch5=135pg 等超大章节）
- [eia-split-parse](eia-split/eia-split-parse/SKILL.md) - 解析环评 PDF 结构（章节标题 + 表格位置 → structure.json）
- [eia-split-extract](eia-split/eia-split-extract/SKILL.md) - 提取环评内容到结构化 YAML（表普查 + 段落正文）
- [eia-split-render](eia-split/eia-split-render/SKILL.md) - Jinja2 渲染 HTML（表格确定性渲染，不调用 LLM）
- [eia-split-to-py](eia-split/eia-split-to-py/SKILL.md) - 生成 prompts/getter/content 三件套（表格免 LLM）
- [eia-split-generate](eia-split/eia-split-generate/SKILL.md) - 调用 LLM 生成章节 HTML（表走 render 片段，仅段落调 LLM）
- [eia-split-verify](eia-split/eia-split-verify/SKILL.md) - render 后质量闸门（表格与 PDF/txt 多轮比对至零误差）
- [eia-split-report](eia-split/eia-split-report/SKILL.md) - 收尾校验（render/LLM/PDF-txt 三方结构回归 + 一致性比对）

### OpenSpec 工作流
- [openspec-install](openspec/openspec-install/SKILL.md) - 全局安装 OpenSpec CLI（npm/pnpm/yarn/bun/nix）
- [openspec-initial](openspec/openspec-initial/SKILL.md) - 在项目中初始化 OpenSpec（openspec init）
- [openspec-onboard](openspec/openspec-onboard/SKILL.md) - 引导式完整 OpenSpec 工作流入门
- [openspec-new](openspec/openspec-new/SKILL.md) - 新建 OpenSpec change（/opsx:new）
- [openspec-explore](openspec/openspec-explore/SKILL.md) - 需求探索与问题澄清（/opsx:explore）
- [openspec-continue](openspec/openspec-continue/SKILL.md) - 按依赖链继续创建 artifact（/opsx:continue）
- [openspec-ff](openspec/openspec-ff/SKILL.md) - 快速生成全部规划 artifacts（/opsx:ff）
- [openspec-config](openspec/openspec-config/SKILL.md) - 配置 OpenSpec 项目与全局设置
- [openspec-schema](openspec/openspec-schema/SKILL.md) - 自定义工作流 schema（fork/validate/which）
- [openspec-apply](openspec/openspec-apply/SKILL.md) - 按 tasks 实现 change（/opsx:apply）
- [openspec-verify](openspec/openspec-verify/SKILL.md) - 验证实现与 artifacts 一致性（/opsx:verify）
- [openspec-sync](openspec/openspec-sync/SKILL.md) - 将 delta specs 同步进主 specs（/opsx:sync）
- [openspec-archive](openspec/openspec-archive/SKILL.md) - 归档已完成的 change（/opsx:archive）
- [openspec-bulk-archive](openspec/openspec-bulk-archive/SKILL.md) - 批量归档多个 changes（/opsx:bulk-archive）
- [openspec-update](openspec/openspec-update/SKILL.md) - 升级 CLI 后重新生成 AI 工具指令
### 学习技能
- [study_master](study_master/SKILL.md) - 综合 AI 学习助手（AI 导师教学 + Zettelkasten 知识串联 + 学习日志管理）
### 自建工作流与质量约束（opsx-flow 系列，8 个独立 skill）
- [opsx-flow](opsx-flow/SKILL.md) - 编排器总览（六阶段 + 调度表 + 恢复机制）
- [flow-new](flow-new/SKILL.md) - 变更脚手架（生成变更目录 + .openspec.yaml + _checkpoint.md 执行契约）
- [flow-explore](flow-explore/SKILL.md) - Phase 1 需求探索与质询（grill-me）
- [flow-proposal](flow-proposal/SKILL.md) - Phase 2 方案构建（必读 brainstorming + spec self-review）
- [flow-plan](flow-plan/SKILL.md) - Phase 3 原子任务规划（design.md + tasks.md）
- [flow-apply](flow-apply/SKILL.md) - Phase 4 执行与调度（按任务类型调对应 skill）
- [flow-verify](flow-verify/SKILL.md) - Phase 5 验证与换模型审查
- [flow-archive](flow-archive/SKILL.md) - Phase 6 归档收尾（archive/ + STATUS.md 更新）
- [python-quality-guide](python-quality-guide/SKILL.md) - Python 高质量编程方法论（软约束：PEP8/类型注解/SOLID/可测试性）
- [python-quality-gate](python-quality-gate/SKILL.md) - Python 代码质量硬闸门（硬约束：flake8 + black --check + pytest，全绿才放行）
### 前端验收
- [frontend-review-skill](frontend-review-skill/SKILL.md) - 前端边界验收（AI 写的前端代码：内存/资源/安全/可访问性/性能 10 维度审查，输出分级报告+修复代码+评分）
