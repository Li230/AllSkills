# Project Memory Manager - Hook 集成指南

## 概述

通过配置 Claude Code 的 hooks，可以实现记忆系统的自动化：
- **会话开始前**：自动加载项目记忆
- **会话结束后**：自动保存关键内容

## Hook 配置

### 1. 在项目中配置 hooks

在项目根目录创建 `.claude/settings.json`：

```json
{
  "hooks": {
    "SessionInit": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "bash -c 'if [ -d \"memory\" ]; then echo \"✓ 已加载项目记忆\"; else ~/.claude/skills/project_memory_manager/scripts/init_memory.sh; fi'"
      }]
    }],
    "UserPromptSubmit": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "bash -c 'if [ -f \"memory/01_session_log.md\" ]; then head -50 memory/01_session_log.md; fi'"
      }]
    }]
  }
}
```

### 2. 全局配置（可选）

在 `~/.claude/settings.json` 添加：

```json
{
  "skills": {
    "project_memory_manager": {
      "auto_init": true,
      "auto_save": true
    }
  }
}
```

## 使用方式

### 手动初始化项目记忆

```bash
# 在项目根目录运行
bash ~/.claude/skills/project_memory_manager/scripts/init_memory.sh
```

### 加载记忆

```bash
# 在会话中手动加载
bash ~/.claude/skills/project_memory_manager/scripts/load_memory.sh
```

### 更新记忆

```bash
# 添加会话内容
bash ~/.claude/skills/project_memory_manager/scripts/update_memory.sh add-session "讨论了用户认证模块的设计"

# 添加知识
bash ~/.claude/skills/project_memory_manager/scripts/update_memory.sh add-knowledge "使用 JWT 进行身份验证，token 过期时间设置为 24 小时"

# 标记任务完成
bash ~/.claude/skills/project_memory_manager/scripts/update_memory.sh complete-task "实现登录功能"

# 查看状态
bash ~/.claude/skills/project_memory_manager/scripts/update_memory.sh status
```

## 自动化工作流

### 会话前（自动）

1. 检查 `memory/` 目录是否存在
2. 如不存在，自动初始化
3. 读取 `00_core_context.md` 和 `01_session_log.md`
4. 将内容注入到系统提示词

### 会话后（建议手动触发）

1. 回顾本次对话的关键内容
2. 运行 `update_memory.sh` 保存重要信息
3. 清理过期的会话日志

## 最佳实践

### 1. 项目启动时

```bash
# 初始化记忆系统
bash ~/.claude/skills/project_memory_manager/scripts/init_memory.sh

# 编辑核心上下文
vim memory/00_core_context.md
```

### 2. 每次会话前

```bash
# 快速浏览记忆
cat memory/MEMORY.md
cat memory/01_session_log.md
```

### 3. 每次会话后

```bash
# 保存关键决策
bash ~/.claude/skills/project_memory_manager/scripts/update_memory.sh \
  add-knowledge "本次会话确定的 API 设计规范"

# 更新待办事项
bash ~/.claude/skills/project_memory_manager/scripts/update_memory.sh \
  complete-task "完成用户登录接口"
```

### 4. 定期维护

```bash
# 每周清理会话日志
bash ~/.claude/skills/project_memory_manager/scripts/update_memory.sh cleanup-session

# 查看记忆状态
bash ~/.claude/skills/project_memory_manager/scripts/update_memory.sh status
```

## 与其他技能配合

### selfImprove

当 `selfImprove` 技能记录到 `.learnings/` 目录后：
- 高优先级的学习 → 提升到 `memory/02_knowledge_base.md`
- 项目特定的约定 → 提升到 `memory/00_core_context.md`

### writing-plans

实现计划时：
- 读取 `memory/00_core_context.md` 了解项目约束
- 计划完成后更新 `memory/01_session_log.md`

## 故障排除

### 问题：hooks 不执行

**解决方案**：
1. 确认 `.claude/settings.json` 格式正确
2. 确认脚本有执行权限：`chmod +x scripts/*.sh`
3. 检查 Claude Code 版本是否支持 hooks

### 问题：记忆文件为空

**解决方案**：
1. 运行初始化脚本
2. 手动编辑文件添加初始内容

### 问题：记忆内容冲突

**解决方案**：
1. 以最新时间戳的版本为准
2. 合并冲突内容到知识库
3. 使用 git 管理记忆文件版本

## 记忆文件模板

### 00_core_context.md 快速填充

```markdown
---
type: core_context
priority: highest
last_updated: 2026-04-08T00:00:00Z
version: 1.0
---

# 核心项目上下文

## 项目概述
[项目名称] - [一句话描述项目目标]

## 技术栈
- **语言**: TypeScript 5.0, Python 3.11
- **框架**: React 18, Express 4.x
- **数据库**: PostgreSQL 15, Redis 7
- **部署**: Docker, Kubernetes, AWS

## 核心规则
1. 所有 API 必须有类型定义
2. 敏感配置必须通过环境变量注入
3. 数据库变更必须有迁移脚本

## 架构决策
| 决策 | 日期 | 原因 |
|------|------|------|
| 使用 ORPC 作为 RPC 框架 | 2026-04-01 | 类型安全，支持流式传输 |
```

### 01_session_log.md 快速填充

```markdown
---
type: session_log
priority: high
session_start: 2026-04-08T09:00:00Z
---

# 会话日志

## 当前目标
- [ ] 实现用户登录功能
- [ ] 编写单元测试

## 待办事项
| 事项 | 优先级 | 状态 | 备注 |
|------|--------|------|------|
| 登录接口 | P0 | pending | 需要 JWT 认证 |
| 单元测试 | P1 | pending | 覆盖率>80% |

## 临时笔记
- 用户反馈登录速度慢，需要优化
```

### 02_knowledge_base.md 快速填充

```markdown
---
type: knowledge_base
priority: medium
last_updated: 2026-04-08T00:00:00Z
---

# 知识库

## 已验证的代码片段

### JWT 认证中间件
```typescript
// 验证通过的代码
const jwtMiddleware = (req, res, next) => {
  const token = req.headers.authorization?.split(' ')[1];
  // ...
};
```

## 业务逻辑总结

### 用户认证流程
1. 用户提交凭据
2. 验证凭据
3. 生成 JWT token
4. 返回 token 和用户信息

## 历史决策记录
| 日期 | 决策 | 原因 | 状态 |
|------|------|------|------|
| 2026-04-08 | 使用 bcrypt 加密密码 | OWASP 推荐 | active |

## 常见问题解决方案

### 登录失败：token 过期
**原因**: JWT token 超过有效期
**解决方案**: 实现 refresh token 机制
```
