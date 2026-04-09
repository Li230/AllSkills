#!/bin/bash
# Project Memory Manager - 回答后提示
# 在每次回答后询问用户是否保存关键点

set -e

MEMORY_DIR="memory"

# 检查 memory 目录是否存在，不存在则初始化
if [ ! -d "$MEMORY_DIR" ]; then
    mkdir -p "$MEMORY_DIR"
    bash ~/.claude/skills/project_memory_manager/scripts/init_memory.sh
fi

# 输出提示
echo ""
echo "---"
echo "💡 是否需要进行记忆更新？"
echo "   输入 **"可以"**、**"好的"**、**"是"** 或类似确认词，自动执行记忆维护和精炼"
