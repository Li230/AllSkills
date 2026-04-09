#!/bin/bash
# Project Memory Manager - 记忆加载器
# 在每次回答前读取记忆文件并输出为系统提示词

set -e

MEMORY_DIR="memory"

# 检查 memory 目录是否存在
if [ ! -d "$MEMORY_DIR" ]; then
    echo "错误：memory 目录不存在"
    echo "请先运行：bash ~/.claude/skills/project_memory_manager/scripts/init_memory.sh"
    exit 1
fi

echo "【项目记忆上下文】"
echo "=================="
echo ""

# 读取核心上下文
if [ -f "$MEMORY_DIR/00_core_context.md" ]; then
    echo "## 核心上下文 (来自 00_core_context.md)"
    echo "----------------------------------------"
    cat "$MEMORY_DIR/00_core_context.md"
    echo ""
else
    echo "## 核心上下文"
    echo "警告：00_core_context.md 不存在"
    echo ""
fi

# 读取会话日志
if [ -f "$MEMORY_DIR/01_session_log.md" ]; then
    echo "## 会话日志 (来自 01_session_log.md)"
    echo "------------------------------------"
    cat "$MEMORY_DIR/01_session_log.md"
    echo ""
else
    echo "## 会话日志"
    echo "警告：01_session_log.md 不存在"
    echo ""
fi

# 读取知识库
if [ -f "$MEMORY_DIR/02_knowledge_base.md" ]; then
    echo "## 知识库 (来自 02_knowledge_base.md)"
    echo "------------------------------------"
    cat "$MEMORY_DIR/02_knowledge_base.md"
    echo ""
else
    echo "## 知识库"
    echo "警告：02_knowledge_base.md 不存在"
    echo ""
fi

echo "=================="
echo "请基于以上项目记忆来理解用户的最新指令。"
