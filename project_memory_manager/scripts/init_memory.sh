#!/bin/bash
# Project Memory Manager - 记忆初始化脚本
# 用于在项目根目录创建 memory 文件夹和初始文件

set -e

MEMORY_DIR="memory"

# 检查是否已存在 memory 目录
if [ -d "$MEMORY_DIR" ]; then
    echo "✓ memory 目录已存在"
else
    echo "创建 memory 目录..."
    mkdir -p "$MEMORY_DIR"
    echo "✓ memory 目录创建成功"
fi

# 创建 00_core_context.md
if [ ! -f "$MEMORY_DIR/00_core_context.md" ]; then
    cat > "$MEMORY_DIR/00_core_context.md" << 'EOF'
---
type: core_context
priority: highest
last_updated: 2026-04-08T00:00:00Z
version: 1.0
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
    echo "✓ 创建 00_core_context.md"
else
    echo "✓ 00_core_context.md 已存在"
fi

# 创建 01_session_log.md
if [ ! -f "$MEMORY_DIR/01_session_log.md" ]; then
    cat > "$MEMORY_DIR/01_session_log.md" << 'EOF'
---
type: session_log
priority: high
session_start: 2026-04-08T00:00:00Z
---

# 会话日志

## 当前会话目标
[待填写]

## 待办事项
- [ ]

## 临时笔记
[待填写]
EOF
    echo "✓ 创建 01_session_log.md"
else
    echo "✓ 01_session_log.md 已存在"
fi

# 创建 02_knowledge_base.md
if [ ! -f "$MEMORY_DIR/02_knowledge_base.md" ]; then
    cat > "$MEMORY_DIR/02_knowledge_base.md" << 'EOF'
---
type: knowledge_base
priority: medium
last_updated: 2026-04-08T00:00:00Z
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
    echo "✓ 创建 02_knowledge_base.md"
else
    echo "✓ 02_knowledge_base.md 已存在"
fi

# 创建 MEMORY.md 索引文件
cat > "$MEMORY_DIR/MEMORY.md" << 'EOF'
# 项目记忆索引

| 文件 | 类型 | 优先级 | 说明 |
|------|------|--------|------|
| [00_core_context.md](00_core_context.md) | core_context | highest | 项目核心设定、技术栈、不可变规则 |
| [01_session_log.md](01_session_log.md) | session_log | high | 当前会话的临时重点、待办事项 |
| [02_knowledge_base.md](02_knowledge_base.md) | knowledge_base | medium | 已验证代码、业务逻辑、历史决策 |

---
*最后更新：2026-04-08*
EOF
echo "✓ 创建 MEMORY.md 索引文件"

echo ""
echo "项目记忆系统初始化完成！"
echo "使用方法："
echo "  1. 编辑 memory/00_core_context.md 填写项目核心信息"
echo "  2. 在会话开始前读取 memory/ 目录获取上下文"
echo "  3. 会话结束后更新 memory/01_session_log.md"
