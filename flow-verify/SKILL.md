---
description: 'opsx-flow Phase 5: 验证+换模型审查。结构验证（spec↔实现一致性）+ 换模型独立审查，防止自审走过场。触发词："验证"、"flow-verify"、"Phase
  5"、"审查"。'
name: flow-verify
---

# Flow-Verify — Phase 5: 验证与审查

## ⚠️ 进入前必做

```
read_file: skills/verification-before-completion/SKILL.md
read_file: openspec/changes/<change-name>/_checkpoint.md
```
确认 Phase 4 apply 已完成、所有任务 [x]。

## 目的

独立视角审查，防自审走过场。

## 执行步骤

### 1. 结构验证

对照 specs/ 检查实现是否一致：
- 每个 `### Requirement` 是否有对应代码/文件
- 每个 `#### Scenario` 的 WHEN/THEN 是否成立
- tasks.md 所有任务是否真的 [x]（抽查验证证据）

### 2. 换模型审查

> ⚠️ 自审不可信。必须换独立视角。

方式：
- `spawn_subagent`（fork=true）委托另一个 agent 做 code review
- 或 `chat_with_agent` 委托其他 agent
- 或用户切换模型后重新审查

审查重点：
- 改动是否与 proposal 一致
- 有无遗漏的边界情况
- 有无引入新问题

### 3. 审查意见处理

```
审查意见 → 分类：
  ├─ 必须修 → 回 Phase 4 补任务 → 修复 → 重验
  ├─ 建议改 → 记录，本次可选修
  └─ 误报 → 说明理由，标记驳回
```

### 4. 更新 _checkpoint.md

```markdown
## 当前状态
- Phase: 5 verify ✅

## 验证结果
- 结构验证: ✅/❌
- 换模型审查: ✅/❌（审查者: <agent-id/model>）
- 审查意见: N 条（必须修 X / 建议 Y / 误报 Z）

## 修复记录
<如有>

## 下一步
read_file: skills/flow-archive/SKILL.md
```

## 完成标准

- [ ] 结构验证通过（spec ↔ 实现一致）
- [ ] 换模型审查完成
- [ ] 必须修的意见已处理
- [ ] _checkpoint.md 已更新（指向 flow-archive）