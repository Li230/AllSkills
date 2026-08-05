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
