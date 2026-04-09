#!/bin/bash
# Project Memory Manager - 自动记忆维护和精炼
# 在用户确认后自动执行记忆分析和存储

set -e

MEMORY_DIR="memory"
SESSION_LOG="$MEMORY_DIR/01_session_log.md"
KNOWLEDGE_BASE="$MEMORY_DIR/02_knowledge_base.md"
CORE_CONTEXT="$MEMORY_DIR/00_core_context.md"

# 从参数获取对话总结
DIALOGUE="${1:-}"

if [ -z "$DIALOGUE" ]; then
    echo "用法：$0 \"对话总结\""
    exit 1
fi

# 检查 memory 目录
if [ ! -d "$MEMORY_DIR" ]; then
    echo "⚠️ memory 目录不存在，正在初始化..."
    mkdir -p "$MEMORY_DIR"
    bash ~/.claude/skills/project_memory_manager/scripts/init_memory.sh
fi

TIMESTAMP=$(date -Iseconds)
DATE_SHORT=$(date +%Y-%m-%d)

# === 第一步：记忆精炼 - 判断内容重要性 ===

# 定义关键词模式（英文关键词，不区分大小写）
CORE_PATTERNS='decided|use|architecture|core|rule|must|forbid|standard|spec|design|pattern'
KNOWLEDGE_PATTERNS='verified|solution|code|fixed|implemented|tested|working|bug|fix|feature'
SESSION_PATTERNS='todo|later|temporary|idea|note|pending|TBD|remind'

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

        PENDING_FILE="$MEMORY_DIR/.pending_core_update.md"
        cat > "$PENDING_FILE" << EOF
# 待确认的核心上下文更新

**检测时间**: $TIMESTAMP

**变更内容**:
$DIALOGUE

---
请手动执行：
bash ~/.claude/skills/project_memory_manager/scripts/update_memory.sh update-core "新内容"
EOF
        echo "   已生成待确认文件：memory/.pending_core_update.md"
        ;;

    knowledge)
        # 知识库 - 自动添加
        echo "🟢 已添加到知识库："

        if ! grep -q "### $DATE_SHORT" "$KNOWLEDGE_BASE" 2>/dev/null; then
            cat >> "$KNOWLEDGE_BASE" << EOF

---
### $DATE_SHORT
$DIALOGUE
EOF
        else
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

# 检查已完成任务
if [ -f "$SESSION_LOG" ]; then
    COMPLETED=$(grep -c '\[x\]' "$SESSION_LOG" 2>/dev/null || echo "0")
    if [ "$COMPLETED" -gt 3 ]; then
        echo ""
        echo "📝 检测到 $COMPLETED 项已完成任务，建议清理会话日志"
        echo "   命令：bash ~/.claude/skills/project_memory_manager/scripts/update_memory.sh cleanup-session"
    fi
fi

# 检查知识库重复条目
if [ -f "$KNOWLEDGE_BASE" ]; then
    DUPE_COUNT=$(grep -c "^### " "$KNOWLEDGE_BASE" 2>/dev/null || echo "0")
    if [ "$DUPE_COUNT" -gt 10 ]; then
        echo ""
        echo "📝 知识库有 $DUPE_COUNT 个条目，建议定期合并重复内容"
    fi
fi

echo ""
echo "✓ 记忆自动维护完成 (优先级：$PRIORITY)"
