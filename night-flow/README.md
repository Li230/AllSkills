# night-flow 安装与触发适配指南（跨框架）

skill 本体只有 `SKILL.md`（Agent Skills 标准格式），任何支持该标准的框架都能装。
唯一的框架差异是**触发方式**——skill 被定时唤醒时收到的那条消息。

## 安装

把 `night-flow/` 整个目录拷到目标框架的技能目录：

| 框架 | 技能目录 |
|---|---|
| QwenPaw | `<WORKING_DIR>/workspaces/<agent_id>/skills/night-flow/` |
| Claude Code | `~/.claude/skills/night-flow/`（或项目 `.claude/skills/`） |
| OpenClaw | `~/.openclaw/workspace/skills/night-flow/` |

## 触发适配器（选一种）

### A. QwenPaw

```bash
qwenpaw cron create \
  --agent-id default --type agent --schedule-type cron \
  --name "night-flow" \
  --cron "*/20 23,0-5 * * *" \
  --channel qq --target-user "<用户ID>" --target-session "<会话ID>" \
  --text "执行 night-flow 技能：读取 skills/night-flow/state/ 状态文件，严格按 SKILL.md 每轮流程执行，自主决策，不要询问我。" \
  --silent
```

### B. OpenClaw / 心跳类框架

把心跳文件（HEARTBEAT.md）内容设为：

```
执行 night-flow 技能：读取 skills/night-flow/state/ 状态文件，
严格按 SKILL.md 每轮流程执行，自主决策，不要询问我。
```

心跳间隔设 20–30 分钟；SKILL.md 自带时段判断，非时段内心跳会自动空跑（可在心跳内容里加"非 23:00-6:00 则直接结束"减少开销）。

### C. Claude Code / 通用 CLI 框架

用系统 crontab + 无头调用：

```cron
*/20 23-23,0-5 * * * cd /path/to/project && claude -p "执行 night-flow 技能：读取 .claude/skills/night-flow/state/ 状态文件，严格按 SKILL.md 每轮流程执行，自主决策，不要询问我。" >> /tmp/night-flow.log 2>&1
```

其他支持 `SKILL.md` 的框架同理：**定时器只负责把上面那句唤醒词递给 agent，其余逻辑全在 skill 里**。

## 关键点

1. **唤醒词模板固定**，换框架只换"怎么定时递这句话"
2. **状态目录跟随 skill 走**，换框架时把 `state/` 一起拷走即可续上进度
3. 首次使用建议白天先跑一轮 `night-flow 开始. 目标: 测试` 验证状态文件读写正常
4. 轮询间隔 ≈ 单任务时长上限：任务多为 15 分钟 → 20 分钟间隔；任务多为 1 小时 → 间隔放宽到 60-70 分钟
