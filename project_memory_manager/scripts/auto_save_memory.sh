#!/bin/bash
# Project Memory Manager - 自动记忆保存与精炼
# 在每次回答后自动分析对话内容，判断重要性并分级存储

set -e

MEMORY_DIR="memory"
SESSION_LOG="$MEMORY_DIR/01_session_log.md"
KNOWLEDGE_BASE="$MEMORY_DIR/02_knowledge_base.md"
CORE_CONTEXT="$MEMORY_DIR/00_core_context.md"

# 从参数获取对话内容（支持多行）
DIALOGUE="${1:-}"

if [ -z "$DIALOGUE" ]; then
    echo "用法：$0 \"对话内容\""
    exit 1
fi

# 检查 memory 目录
if [ ! -d "$MEMORY_DIR" ]; then
    echo "⚠️ memory 目录不存在，正在初始化..."
    bash ~/.claude/skills/project_memory_manager/scripts/init_memory.sh
fi

TIMESTAMP=$(date -Iseconds)
DATE_SHORT=$(date +%Y-%m-%d)

# === 第一步：记忆精炼 - 判断内容重要性 ===

# 定义关键词模式（使用英文关键词，管道符前后不能有空格）
CORE_PATTERNS='decided|use|architecture|core|rule|must|forbid|standard|spec'
KNOWLEDGE_PATTERNS='verified|solution|code|snippet|business logic|bug fix|fixed|implemented|tested'
SESSION_PATTERNS='todo|later|temporary|idea|note|pending|TBD'

# 判断优先级（按优先级从高到低检查）
PRIORITY="session"
if echo "$DIALOGUE" | grep -qiE "$CORE_PATTERNS"; then
    PRIORITY="core"
elif echo "$DIALOGUE" | grep -qiE "$KNOWLEDGE_PATTERNS"; then
    PRIORITY="knowledge"
fi

# === 第二步：记忆更新 - 根据优先级存储 ===

case "$PRIORITY" in
    core)
        # 核心上下文变更 - 生成待确认文件
        echo "🔴 检测到核心上下文变更:"
        echo "   $DIALOGUE"

        # 将变更内容写入待确认文件
        PENDING_FILE="$MEMORY_DIR/.pending_core_update.md"
        cat > "$PENDING_FILE" << EOF
# 待确认的核心上下文更新

**检测时间**: $TIMESTAMP

**变更内容**:
$DIALOGUE

---
请用户确认后手动执行:
bash ~/.claude/skills/project_memory_manager/scripts/update_memory.sh update-core "新内容"
EOF
        echo "   已生成待确认文件：memory/.pending_core_update.md"
        echo "   请确认后手动执行 update-core 命令"
        ;;

    knowledge)
        # 知识库 - 自动添加
        echo "🟢 已添加到知识库："

        # 检查是否已存在相同日期的条目，避免重复
        if ! grep -q "### $DATE_SHORT" "$KNOWLEDGE_BASE" 2>/dev/null; then
            cat >> "$KNOWLEDGE_BASE" << EOF

---
### $DATE_SHORT
$DIALOGUE
EOF
        else
            # 已存在该日期的条目，追加内容
            echo "" >> "$KNOWLEDGE_BASE"
            echo "$DIALOGUE" >> "$KNOWLEDGE_BASE"
        fi

        echo "   内容：$DIALOGUE"
        ;;

    session)
        # 会话日志 - 自动添加
        echo "🔵 已添加到会话日志："

        cat >> "$SESSION_LOG" << EOF

### $TIMESTAMP
$DIALOGUE
EOF

        echo "   内容：$DIALOGUE"
        ;;
esac

# === 第三步：定期精炼 - 检查是否需要清理 ===

# 检查是否有已完成的待办事项（标记为 [x]）
if [ -f "$SESSION_LOG" ]; then
    COMPLETED=$(grep -c '\[x\]' "$SESSION_LOG" 2>/dev/null || echo "0")
    if [ "$COMPLETED" -gt 3 ]; then
        echo ""
        echo "📝 检测到 $COMPLETED 项已完成任务，建议清理会话日志"
        echo "   命令：bash ~/.claude/skills/project_memory_manager/scripts/update_memory.sh cleanup-session"
    fi
fi

# 检查知识库中的重复条目
if [ -f "$KNOWLEDGE_BASE" ]; then
    DUPE_COUNT=$(grep -c "^### " "$KNOWLEDGE_BASE" 2>/dev/null || echo "0")
    if [ "$DUPE_COUNT" -gt 10 ]; then
        echo ""
        echo "📝 知识库有 $DUPE_COUNT 个条目，建议定期合并重复内容"
    fi
fi

echo ""
echo "✓ 记忆自动保存完成 (优先级：$PRIORITY)"
