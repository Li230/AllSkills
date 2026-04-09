---
name: project_memory_manager
description: 在每次回答前读取项目 memory 文件夹加载记忆，回答后维护和更新记忆内容，实现跨会话的核心信息保留
type: project
---

# Project Memory Manager - 项目记忆管理器

## 核心目标

1. **跨会话记忆保留** - 解决重开 Claude 时重要记忆丢失的问题
2. **记忆分级存储** - 不同重要等级的内容放在不同文档里
3. **自动维护精炼** - 每次对话后及时更新，删除过时内容
4. **项目上下文共享** - 为所有会话提供一致的项目背景信息

## 目录结构

```
project_root/
└── memory/
    ├── MEMORY.md           # 【索引文件】记忆目录索引，指向所有记忆文件
    ├── 00_core_context.md  # 【最高优先级】项目核心设定、技术栈、不可变的规则
    ├── 01_session_log.md   # 【当前会话】本次对话的临时重点、待办事项
    └── 02_knowledge_base.md # 【长期积累】已验证的代码片段、业务逻辑总结、历史决策记录
```

## 执行逻辑流程

### 触发方式

当用户输入 **"开启记忆管理"**、**"开始记忆管理"**、**"加载记忆"** 或 **"/project_memory_manager"** 时，执行以下流程。

### 阶段一：回答前 —— 记忆加载与唤醒

在生成任何回答之前，**自动执行**以下步骤：

#### 步骤 1：检查并初始化 memory 目录

```bash
# 检查 memory 文件夹是否存在，不存在则自动创建
if [ ! -d "memory" ]; then
    mkdir -p memory
    bash ~/.claude/skills/project_memory_manager/scripts/init_memory.sh
fi
```
last_updated: $(date -Iseconds)
---

# 核心项目上下文

## 项目概述
[待填写：项目的主要目标和范围]

## 技术栈
[待填写：使用的技术、框架、语言]

## 核心规则
[待填写：不可变更的项目规则和约束]

## 架构决策
[待填写：重要的架构决策和原因]
EOF
fi

if [ ! -f "memory/01_session_log.md" ]; then
    cat > memory/01_session_log.md << 'EOF'
---
type: session_log
priority: high
session_start: $(date -Iseconds)
---

# 会话日志

## 当前会话目标
[待填写]

## 待办事项
- [ ] 

## 临时笔记
[待填写]
EOF
fi

if [ ! -f "memory/02_knowledge_base.md" ]; then
    cat > memory/02_knowledge_base.md << 'EOF'
---
type: knowledge_base
priority: medium
last_updated: $(date -Iseconds)
---

# 知识库

## 已验证的代码片段
[待填写]

## 业务逻辑总结
[待填写]

## 历史决策记录
[待填写]

## 常见问题解决方案
[待填写]
EOF
fi

# 创建或更新索引文件
cat > memory/MEMORY.md << 'EOF'
# 项目记忆索引

| 文件 | 类型 | 优先级 | 说明 |
|------|------|--------|------|
| 00_core_context.md | core_context | highest | 项目核心设定、技术栈、不可变规则 |
| 01_session_log.md | session_log | high | 当前会话的临时重点、待办事项 |
| 02_knowledge_base.md | knowledge_base | medium | 已验证代码、业务逻辑、历史决策 |
EOF
```

#### 步骤 2：读取记忆上下文

读取三个核心文件的内容：

1. **00_core_context.md** - 获取项目的"长期记忆"
   - 项目使用什么技术栈（React 还是 Vue）
   - 数据库类型（SQL 还是 NoSQL）
   - 核心业务逻辑
   - 架构约束

2. **01_session_log.md** - 获取"短期记忆"
   - 刚才讨论的内容
   - 当前待办事项
   - 临时笔记

3. **02_knowledge_base.md** - 获取"积累知识"
   - 已验证的解决方案
   - 历史决策记录
   - 常见问题处理

#### 步骤 3：注入系统提示词

将读取到的内容作为系统级背景信息：

```
【项目记忆上下文】

## 核心上下文 (来自 00_core_context.md)
[文件内容]

## 会话日志 (来自 01_session_log.md)
[文件内容]

## 知识库 (来自 02_knowledge_base.md)
[文件内容]

---
请基于以上项目记忆来理解用户的最新指令。这些记忆包含了项目的核心设定、当前会话的重点和已积累的知识。
```

### 阶段二：回答后 —— 询问记忆更新

在生成完回答后，**输出询问提示**：

```
---
💡 是否需要进行记忆更新？
   输入 **"可以"**、**"好的"**、**"是"** 或类似确认词，自动执行记忆维护和精炼
```

#### 用户确认后自动执行

当用户输入 **"可以"**、**"好的"**、**"是"**、**"是的"**、**"ok"**、**"确认"** 等确认词时，自动执行以下步骤：

**步骤 1：分析对话内容并提取关键信息**

**步骤 2：判断重要性并分级存储**

| 内容类型 | 关键词 | 存储位置 |
|----------|--------|----------|
| 核心决策 | decided, architecture, core, rule, must, standard | 00_core_context.md |
| 已验证知识 | verified, solution, fixed, implemented, tested | 02_knowledge_base.md |
| 临时待办 | todo, later, temporary, note, pending | 01_session_log.md |

**步骤 3：执行记忆精炼**

- 检查已完成任务（[x] 标记），超过 3 项时自动清理会话日志
- 检查知识库重复条目，超过 10 条时提示合并

#### 手动调用方式

```bash
# 添加会话内容到日志
bash ~/.claude/skills/project_memory_manager/scripts/update_memory.sh add-session "内容"

# 添加知识到知识库
bash ~/.claude/skills/project_memory_manager/scripts/update_memory.sh add-knowledge "内容"

# 标记任务完成
bash ~/.claude/skills/project_memory_manager/scripts/update_memory.sh complete-task "任务名"

# 清理会话日志
bash ~/.claude/skills/project_memory_manager/scripts/update_memory.sh cleanup-session

# 查看记忆状态
bash ~/.claude/skills/project_memory_manager/scripts/update_memory.sh status
```

## 记忆更新触发器

### 自动记录场景

| 场景 | 记录位置 | 触发条件 |
|------|----------|----------|
| 用户确认新决策 | 02_knowledge_base.md | "决定使用 X 方案" |
| 发现并修复 bug | 02_knowledge_base.md | bug 修复完成 |
| 新增待办事项 | 01_session_log.md | "稍后需要做 X" |
| 修改核心架构 | 00_core_context.md | 架构决策变更 |
| 会话结束总结 | 02_knowledge_base.md | 会话自然结束 |

### 清理触发器

| 场景 | 清理动作 |
|------|----------|
| 任务标记为完成 | 24 小时后从 session_log 清理 |
| 会话重新开始 | 清空旧的 session_log |
| 核心上下文更新 | 保留旧版本到 knowledge_base |

## 记忆格式规范

### 00_core_context.md 格式

```markdown
---
type: core_context
priority: highest
last_updated: 2026-04-08T12:00:00Z
version: 1.0
---

# 核心项目上下文

## 项目概述
[项目的名称、目标、范围]

## 技术栈
- **语言**: [例如：TypeScript 5.0]
- **框架**: [例如：React 18, Express]
- **数据库**: [例如：PostgreSQL 15]
- **部署**: [例如：Docker, AWS]

## 核心规则
1. [不可变更的规则 1]
2. [不可变更的规则 2]

## 架构决策
| 决策 | 日期 | 原因 |
|------|------|------|
| [决策内容] | [日期] | [原因] |

## 目录结构
[关键目录说明]
```

### 01_session_log.md 格式

```markdown
---
type: session_log
priority: high
session_start: 2026-04-08T12:00:00Z
session_id: [会话 ID]
---

# 会话日志

## 当前目标
- [ ] [目标 1]
- [ ] [目标 2]

## 对话摘要
### [时间段/话题]
- [关键讨论点]
- [达成的共识]

## 待办事项
| 事项 | 优先级 | 状态 | 备注 |
|------|--------|------|------|
| [事项] | P0/P1/P2 | pending/done | [备注] |

## 临时笔记
[随手的笔记、想法]
```

### 02_knowledge_base.md 格式

```markdown
---
type: knowledge_base
priority: medium
last_updated: 2026-04-08T12:00:00Z
---

# 知识库

## 已验证的代码片段
### [代码片段名称]
```[语言]
[代码]
```
**用途**: [说明]
**验证日期**: [日期]

## 业务逻辑总结
### [业务模块名称]
[业务逻辑描述]

## 历史决策记录
| 日期 | 决策 | 原因 | 状态 |
|------|------|------|------|
| [日期] | [决策] | [原因] | active/archived |

## 常见问题解决方案
### [问题描述]
**原因**: [原因分析]
**解决方案**: [解决步骤]
```

## 与其他技能的集成

### 与 selfImprove 技能配合

- **selfImprove** 负责记录学习、错误、修正
- **project_memory_manager** 负责将重要的学习提升到项目记忆

当 selfImprove 记录的条目具有高优先级且广泛适用时，应提升到 `02_knowledge_base.md` 或 `00_core_context.md`。

### 与 writing-plans 技能配合

- 实现计划应读取 `00_core_context.md` 了解项目约束
- 计划完成后更新 `01_session_log.md` 记录进度

## 最佳实践

1. **立即更新** - 对话结束后立即更新记忆，保持上下文新鲜
2. **精炼优先** - 宁缺毋滥，只保留真正有价值的信息
3. **定期清理** - 每次会话开始时清理过期的 session_log
4. **版本追踪** - 核心上下文更新时保留版本历史
5. **链接相关** - 使用 See Also 链接相关的记忆条目

## 命令快速参考

```bash
# 初始化记忆目录
mkdir -p memory

# 查看记忆状态
ls -la memory/

# 快速查看核心上下文
cat memory/00_core_context.md

# 快速查看会话日志
cat memory/01_session_log.md

# 快速查看知识库
cat memory/02_knowledge_base.md
```

## 故障排除

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 记忆文件为空 | 尚未初始化 | 运行初始化脚本创建默认模板 |
| 记忆内容冲突 | 多会话并发 | 以最新时间戳为准，合并冲突 |
| 记忆过于冗长 | 缺乏精炼 | 运行清理逻辑，删除过期内容 |
| 找不到记忆文件 | 目录错误 | 确认当前工作目录是项目根目录 |
