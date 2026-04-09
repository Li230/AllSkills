# Project Memory Manager - 快速开始指南

## 🚀 安装完成！

`project_memory_manager` 技能已成功安装到：
```
/Users/macbookair/.claude/skills/project_memory_manager/
```

## 📁 技能结构

```
project_memory_manager/
├── SKILL.md                      # 主技能文档
├── scripts/
│   ├── init_memory.sh            # 初始化脚本
│   ├── load_memory.sh            # 加载记忆脚本
│   └── update_memory.sh          # 更新记忆脚本
└── references/
    ├── hooks-integration.md      # Hooks 集成指南
    └── memory-classification.md  # 记忆分级标准
```

## 🎯 核心功能

### 1. 记忆分级存储

| 文件 | 优先级 | 内容 | 更新频率 |
|------|--------|------|----------|
| `00_core_context.md` | highest | 项目核心设定、技术栈、不可变规则 | 低 |
| `01_session_log.md` | high | 当前会话的临时重点、待办事项 | 高 |
| `02_knowledge_base.md` | medium | 已验证代码、业务逻辑、历史决策 | 中 |

### 2. 执行流程

**回答前**：
1. 检查 `memory/` 目录是否存在
2. 如不存在，自动初始化
3. 读取三个记忆文件
4. 将内容注入到系统提示词

**回答后**：
1. 分析对话内容
2. 判断重要性并分级
3. 更新对应的记忆文件
4. 清理过期的临时内容

## 💡 使用方式

### 方式一：手动命令（推荐新手）

```bash
# 1. 初始化（仅首次）
bash ~/.claude/skills/project_memory_manager/scripts/init_memory.sh

# 2. 加载记忆（每次会话前）
bash ~/.claude/skills/project_memory_manager/scripts/load_memory.sh

# 3. 更新记忆（会话结束后）
bash ~/.claude/skills/project_memory_manager/scripts/update_memory.sh add-knowledge "学到的内容"
```

### 方式二：Skills 命令

```bash
# 在 Claude Code 中使用
/project_memory_manager
```

### 方式三：Hooks 自动（高级）

配置 `.claude/settings.json` 实现自动加载和保存（详见 `references/hooks-integration.md`）

## 📝 快速开始

### 第一步：初始化项目记忆

```bash
cd /path/to/your/project
bash ~/.claude/skills/project_memory_manager/scripts/init_memory.sh
```

### 第二步：填写核心上下文

编辑 `memory/00_core_context.md`：

```markdown
---
type: core_context
priority: highest
last_updated: 2026-04-08T00:00:00Z
version: 1.0
---

# 核心项目上下文

## 项目概述
[项目名称] - [一句话描述]

## 技术栈
- **语言**: TypeScript 5.0
- **框架**: React 18
- **数据库**: PostgreSQL 15

## 核心规则
1. 所有 API 必须有类型定义
2. 敏感配置必须外部化
```

### 第三步：开始对话

在对话前运行：
```bash
bash ~/.claude/skills/project_memory_manager/scripts/load_memory.sh
```

### 第四步：保存记忆

对话结束后：
```bash
# 添加决策到知识库
bash ~/.claude/skills/project_memory_manager/scripts/update_memory.sh \
  add-knowledge "使用 JWT 进行身份认证，token 过期时间 24 小时"

# 标记任务完成
bash ~/.claude/skills/project_memory_manager/scripts/update_memory.sh \
  complete-task "实现登录功能"
```

## 🔧 命令参考

### init_memory.sh
创建 memory 目录和初始文件

### load_memory.sh
读取并输出所有记忆文件内容

### update_memory.sh

| 命令 | 说明 |
|------|------|
| `add-session "内容"` | 添加内容到会话日志 |
| `add-knowledge "内容"` | 添加内容到知识库 |
| `complete-task "任务"` | 标记任务完成 |
| `cleanup-session` | 清理会话日志 |
| `update-core "内容"` | 更新核心上下文 |
| `status` | 显示记忆状态 |

## 📚 参考资料

- [Hooks 集成指南](references/hooks-integration.md) - 配置自动化工作流
- [记忆分级标准](references/memory-classification.md) - 判断内容存储位置

## ⚠️ 注意事项

1. **每个项目独立的 memory 目录** - 在项目根目录运行初始化脚本
2. **定期清理** - 避免记忆文件过于冗长
3. **不要包含敏感信息** - 密码、API Key 等不要存入记忆文件
4. **版本控制** - 考虑将 memory 目录加入 .gitignore 或版本控制

## 🆘 故障排除

**Q: 找不到脚本**
```bash
# 确认技能已安装
ls -la ~/.claude/skills/project_memory_manager/scripts/
```

**Q: 脚本没有执行权限**
```bash
chmod +x ~/.claude/skills/project_memory_manager/scripts/*.sh
```

**Q: 记忆文件为空**
运行初始化脚本重新创建文件

## 📞 反馈与支持

遇到问题或有改进建议，请查看：
- 主技能文档：`SKILL.md`
- 参考文档：`references/` 目录

---
*最后更新：2026-04-08*
