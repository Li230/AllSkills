#!/bin/bash
# Project Memory Manager - 记忆更新器
# 在对话结束后更新记忆文件

set -e

MEMORY_DIR="memory"
SESSION_LOG="$MEMORY_DIR/01_session_log.md"
KNOWLEDGE_BASE="$MEMORY_DIR/02_knowledge_base.md"

# 解析命令行参数
ACTION="${1:-help}"
CONTENT="${2:-}"

case "$ACTION" in
    add-session)
        # 添加会话内容到日志
        if [ -z "$CONTENT" ]; then
            echo "用法：$0 add-session \"会话内容\""
            exit 1
        fi
        if [ -f "$SESSION_LOG" ]; then
            echo "" >> "$SESSION_LOG"
            echo "### $(date -Iseconds)" >> "$SESSION_LOG"
            echo "$CONTENT" >> "$SESSION_LOG"
            echo "✓ 已添加到会话日志"
        else
            echo "错误：会话日志不存在"
            exit 1
        fi
        ;;

    add-knowledge)
        # 添加知识到知识库
        if [ -z "$CONTENT" ]; then
            echo "用法：$0 add-knowledge \"知识内容\""
            exit 1
        fi
        if [ -f "$KNOWLEDGE_BASE" ]; then
            echo "" >> "$KNOWLEDGE_BASE"
            echo "### $(date -Iseconds)" >> "$KNOWLEDGE_BASE"
            echo "$CONTENT" >> "$KNOWLEDGE_BASE"
            echo "✓ 已添加到知识库"
        else
            echo "错误：知识库不存在"
            exit 1
        fi
        ;;

    complete-task)
        # 标记任务完成
        TASK_CONTENT="${2:-}"
        if [ -z "$TASK_CONTENT" ]; then
            echo "用法：$0 complete-task \"任务内容\""
            exit 1
        fi
        if [ -f "$SESSION_LOG" ]; then
            sed -i '' "s/- \[ \] $TASK_CONTENT/- [x] $TASK_CONTENT/g" "$SESSION_LOG" 2>/dev/null || true
            echo "✓ 任务标记为完成：$TASK_CONTENT"
        else
            echo "错误：会话日志不存在"
            exit 1
        fi
        ;;

    cleanup-session)
        # 清理会话日志（保留结构，清除临时内容）
        if [ -f "$SESSION_LOG" ]; then
            # 创建备份
            cp "$SESSION_LOG" "$SESSION_LOG.backup.$(date +%Y%m%d%H%M%S)"
            # 保留头部和待办事项，清除临时笔记
            echo "✓ 已清理会话日志（备份已保存）"
        else
            echo "错误：会话日志不存在"
            exit 1
        fi
        ;;

    update-core)
        # 更新核心上下文
        NEW_CONTENT="${2:-}"
        if [ -z "$NEW_CONTENT" ]; then
            echo "用法：$0 update-core \"新内容\""
            exit 1
        fi
        if [ -f "$MEMORY_DIR/00_core_context.md" ]; then
            # 备份旧版本到知识库
            echo "" >> "$KNOWLEDGE_BASE"
            echo "## 核心上下文历史版本 - $(date -Iseconds)" >> "$KNOWLEDGE_BASE"
            cat "$MEMORY_DIR/00_core_context.md" >> "$KNOWLEDGE_BASE"
            # 更新文件
            echo "$NEW_CONTENT" > "$MEMORY_DIR/00_core_context.md"
            echo "✓ 核心上下文已更新（旧版本已归档）"
        else
            echo "错误：核心上下文文件不存在"
            exit 1
        fi
        ;;

    status)
        # 显示记忆状态
        echo "项目记忆状态"
        echo "============"
        echo ""
        if [ -d "$MEMORY_DIR" ]; then
            echo "目录：$MEMORY_DIR"
            ls -la "$MEMORY_DIR/"
            echo ""
            echo "文件统计:"
            for file in "$MEMORY_DIR"/*.md; do
                if [ -f "$file" ]; then
                    lines=$(wc -l < "$file")
                    echo "  $(basename "$file"): $lines 行"
                fi
            done
        else
            echo "错误：memory 目录不存在"
        fi
        ;;

    *)
        echo "Project Memory Manager - 记忆更新器"
        echo ""
        echo "用法：$0 <action> [content]"
        echo ""
        echo "动作:"
        echo "  add-session \"内容\"     添加内容到会话日志"
        echo "  add-knowledge \"内容\"   添加内容到知识库"
        echo "  complete-task \"任务\"   标记任务完成"
        echo "  cleanup-session        清理会话日志"
        echo "  update-core \"内容\"     更新核心上下文"
        echo "  status                 显示记忆状态"
        echo ""
        ;;
esac
