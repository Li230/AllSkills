# 记忆管理 - 快速使用指南

## 使用方式

### 1. 开启记忆管理

当你说以下任一词汇时，我会自动加载或创建记忆文件：
- **"开启记忆管理"**
- **"开始记忆管理"**
- **"加载记忆"**
- **"用记忆管理"**

**自动执行**：
- 检查 `memory/` 目录是否存在
- 如不存在，自动创建并初始化
- 读取三个记忆文件内容
- 将记忆注入到回答上下文中

### 2. 回答后询问

每次回答结束后，会显示提示：
```
---
💡 是否需要进行记忆更新？
   输入 **"可以"**、**"好的"**、**"是"** 或类似确认词，自动执行记忆维护和精炼
```

### 3. 确认执行记忆维护

当你输入以下任一确认词时，自动执行记忆维护：
- **"可以"**
- **"好的"**
- **"是"** / **"是的"**
- **"ok"**
- **"确认"**

**自动执行**：
- 分析对话内容，提取关键信息
- 判断重要性并分级存储（core/knowledge/session）
- 检查是否需要清理（>3 项完成时提示）
- 检查知识库重复条目（>10 条时提示）

---

## 手动命令

```bash
# 初始化记忆目录（首次使用）
bash ~/.claude/skills/project_memory_manager/scripts/init_memory.sh

# 加载记忆
bash ~/.claude/skills/project_memory_manager/scripts/load_memory.sh

# 自动维护记忆（用户确认后）
bash ~/.claude/skills/project_memory_manager/scripts/auto_maintain_memory.sh "对话总结"

# 添加会话内容
bash ~/.claude/skills/project_memory_manager/scripts/update_memory.sh add-session "内容"

# 添加知识
bash ~/.claude/skills/project_memory_manager/scripts/update_memory.sh add-knowledge "内容"

# 标记任务完成
bash ~/.claude/skills/project_memory_manager/scripts/update_memory.sh complete-task "任务名"

# 查看记忆状态
bash ~/.claude/skills/project_memory_manager/scripts/update_memory.sh status
```

---

## 记忆文件说明

| 文件 | 用途 | 保留策略 |
|------|------|----------|
| 00_core_context.md | 项目核心设定、技术栈 | 长期保留 |
| 01_session_log.md | 当前会话的临时重点 | 会话结束后清理 |
| 02_knowledge_base.md | 已验证代码、业务逻辑 | 长期保留 |

---

## 记忆分级规则

| 优先级 | 关键词 | 存储位置 |
|--------|--------|----------|
| **core** | decided, architecture, core, rule, must | 00_core_context.md（待确认） |
| **knowledge** | verified, solution, fixed, implemented | 02_knowledge_base.md（自动） |
| **session** | todo, later, temporary, note, pending | 01_session_log.md（自动） |

---

*最后更新：2026-04-08*
