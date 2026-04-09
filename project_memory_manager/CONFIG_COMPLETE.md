# Project Memory Manager - 配置完成

## ✅ 已完成的配置

### 1. Hooks 自动触发配置

文件位置：`/Users/macbookair/.claude/settings.json`

配置内容：
```json
{
  "hooks": {
    "UserPromptSubmit": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "bash -c 'if [ -d memory ]; then if [ -f memory/01_session_log.md ]; then echo \"\\n📚 已加载项目记忆:\" && cat memory/01_session_log.md 2>/dev/null | head -40; echo \"\"; echo \"---\"; fi; else echo \"\\n⚠️ memory 目录不存在，运行初始化...\" && bash ~/.claude/skills/project_memory_manager/scripts/init_memory.sh; fi'"
      }]
    }]
  }
}
```

### 2. memory 目录结构

```
/Users/macbookair/memory/
├── 00_core_context.md   # 核心项目上下文
├── 01_session_log.md    # 会话日志
├── 02_knowledge_base.md # 知识库
└── MEMORY.md            # 索引文件
```

---

## 🚀 使用方式

### 自动触发（已配置）

**每次你提问前**，系统会自动：
1. 检查 `memory/` 目录是否存在
2. 如不存在，自动运行初始化脚本
3. 读取并显示 `01_session_log.md` 的内容（前 40 行）
4. 将记忆内容注入到对话上下文中

### 手动命令

```bash
# 初始化记忆目录（首次使用）
bash ~/.claude/skills/project_memory_manager/scripts/init_memory.sh

# 手动加载记忆
bash ~/.claude/skills/project_memory_manager/scripts/load_memory.sh

# 添加内容到会话日志
bash ~/.claude/skills/project_memory_manager/scripts/update_memory.sh add-session "讨论了用户认证模块"

# 添加知识到知识库
bash ~/.claude/skills/project_memory_manager/scripts/update_memory.sh add-knowledge "使用 JWT 进行身份认证"

# 标记任务完成
bash ~/.claude/skills/project_memory_manager/scripts/update_memory.sh complete-task "实现登录功能"

# 查看记忆状态
bash ~/.claude/skills/project_memory_manager/scripts/update_memory.sh status

# 会话后提示
bash ~/.claude/skills/project_memory_manager/scripts/after_response.sh
```

---

## 📝 工作流程

### 首次使用

1. **Hooks 自动初始化** - 第一次提问时自动创建 memory 目录
2. **编辑核心上下文** - 填写 `memory/00_core_context.md` 中的项目信息
3. **开始对话** - 正常提问，系统会自动加载记忆

### 日常使用

```
┌─────────────────────────────────────────────────────────┐
│  1. 用户提问                                             │
│         ↓                                                │
│  2. Hooks 触发 → 自动加载 memory/ 内容                   │
│         ↓                                                │
│  3. Claude 基于记忆上下文回答问题                        │
│         ↓                                                │
│  4. 用户手动保存关键点（可选）                           │
│         update_memory.sh add-knowledge "..."             │
└─────────────────────────────────────────────────────────┘
```

### 记忆保存时机

**建议手动保存的场景**：
- 确认了重要的技术决策
- 发现了关键 bug 的解决方案
- 用户说"这个很重要，记下来"
- 完成了某个待办事项

**不需要保存的场景**：
- 临时的尝试和探索
- 错误的假设和方向
- 琐碎的对话细节

---

## 🔧 在其他项目中使用

如果你在其他项目目录工作，需要：

### 步骤 1：在项目目录创建配置

```bash
cd /path/to/new/project
mkdir -p .claude
cat > .claude/settings.json << 'EOF'
{
  "hooks": {
    "UserPromptSubmit": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "bash -c 'if [ -d memory ]; then if [ -f memory/01_session_log.md ]; then echo \"\\n📚 已加载项目记忆:\" && head -40 memory/01_session_log.md; fi; else echo \"\\n⚠️ memory 目录不存在\" && bash ~/.claude/skills/project_memory_manager/scripts/init_memory.sh; fi'"
      }]
    }]
  }
}
EOF
```

### 步骤 2：初始化记忆目录

```bash
bash ~/.claude/skills/project_memory_manager/scripts/init_memory.sh
```

### 步骤 3：填写核心上下文

编辑 `memory/00_core_context.md`，填入该项目的核心信息

---

## ⚠️ 注意事项

1. **Hooks 仅在 Claude Code CLI 中有效** - 桌面版和网页版不支持
2. **每个项目独立的 memory 目录** - 切换项目时需要重新初始化
3. **定期清理** - 避免会话日志过于冗长
4. **不要包含敏感信息** - 密码、API Key 等不要存入记忆文件

---

## 📚 参考文档

- 主技能文档：`~/.claude/skills/project_memory_manager/SKILL.md`
- 快速开始：`~/.claude/skills/project_memory_manager/QUICKSTART.md`
- Hooks 集成：`~/.claude/skills/project_memory_manager/references/hooks-integration.md`
- 记忆分级：`~/.claude/skills/project_memory_manager/references/memory-classification.md`

---

*配置完成时间：2026-04-08*
