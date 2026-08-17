---
description: 'opsx-flow Phase 4: 执行前反思闸门。计划明确后、执行前，强制书面自问两个问题（需求哪里不明确 / 对哪里没把握），对拿不准的事实先联网核实（WebSearch），产出 _reflection.md 并给出 GO / 先澄清 / 先验证 裁决（澄清与验证可并存），重大疑点回退，禁止带病前进。触发词："反思"、"flow-reflect"、"执行前反思"、"Phase 4"。'
name: flow-reflect
---

# Flow-Reflect — Phase 4: 执行前反思闸门

## ⚠️ 进入前必做

```
read_file: openspec/changes/<change-name>/_checkpoint.md
```
确认 Phase 3 plan 已完成（design.md + tasks.md 已写）。

## 目的

在「计划清晰」与「动手执行」之间，强制一次**书面反思**——把隐藏的需求疑点与信心缺口摊在桌面上，避免带病前进。

> 设计来源：Definition of Ready（需求清晰度闸门）、Pre-mortem 事前析误（风险预判）、Riskiest Assumption Test（最危险假设先验证）、NASA 飞行就绪评审的 go/no-go（硬裁决）、Anthropic think 工具（Agent 原生暂停）。

## 两个自问（强制书面回答）

### Q1 · 需求哪里不明确？（清晰度闸门）
- 逐任务自检：描述清晰、无歧义吗？（Backbrief 自检：我能用自己的话重述这条任务的目标吗？）
- 验收标准可验证吗？依赖解除了吗？技术路线可行吗？（Definition of Ready 四栏）
- **对拿不准的事实/技术点，先联网核实（WebSearch）**：如 API 行为、库版本差异、文档说法，把核实结论写进 _reflection.md，再判断是否「说不清」。
- 有任何一个「说不清」或「核实后仍不确定」的，就是 Q1 疑点。

### Q2 · 对哪里没把握？（风险/信心闸门）
- 想象「执行完发现搞砸了」，最可能因为当时忽略了什么？（Pre-mortem 事前析误）
- **先联网核实（WebSearch）**：查相关已知坑、社区最佳实践、官方文档，补全证据后再打分。
- 给每条没把握打（致命度 × 证据度），**低证据 + 高致命**的先做最小验证（Riskiest Assumption Test）：

| 没把握的点 | 致命度(高/中/低) | 证据度(高/中/低) | 最便宜的 de-risk 动作 |
|---|---|---|---|
| 例：第三方 API 限流未知 | 高 | 低 | 先写 10 行脚本压测 5 次 |

## 执行步骤

```
1. 读 _checkpoint.md、design.md、tasks.md
2. 写 openspec/changes/<name>/_reflection.md（模板见下）
3. 给裁决（可多选；GO 为放行，先澄清/先验证 可单独或同时出现）：
   ├─ GO          → 仅当无未决澄清/验证时，更新 _checkpoint.md 指向 flow-apply，进入 Phase 5
   ├─ 先澄清       → 回 flow-explore 向用户确认 Q1 卡点，澄清后重走 plan（可与先验证并存）
   └─ 先验证       → 在 tasks.md 顶部插一个 spike 任务（类型 verify/file-op），验证通过再全量执行（可与先澄清并存）
4. 重大疑点一律回退，禁止带病前进（NASA 评审精神：异议必须被听见、被记录）
```

## _reflection.md 模板

```markdown
# 执行前反思 — <change-name>

## Q1 需求疑点（Backbrief / Definition of Ready 自检 + 联网核实）
- [ ] 任务「X.Y」描述模糊：__会影响__，卡在__，需[问用户 / 自定]
- [ ] 联网核实（WebSearch）：__查了__，结论__，仍不确定的是__
- （若无疑点：所有任务描述清晰、验收可验证、依赖已解 ✅）

## Q2 信心缺口（Pre-mortem / Riskiest Assumption Test 打分 + 联网核实）
| 没把握的点 | 致命度 | 证据度 | 联网核实结论 | 最便宜的 de-risk 动作 |
|---|---|---|---|---|
| （逐条列出） | | | | |

## 裁决（go/no-go，可多选）
- [ ] GO → 进入 flow-apply（仅当无未决澄清/验证）
- [ ] 先澄清 → 回 flow-explore 向用户确认 Q1 卡点（可与先验证并存）
- [ ] 先验证 → 在 tasks.md 顶部插 spike 任务，验证后再全量执行（可与先澄清并存）

> 重大疑点一律回退，禁止带病前进。
```

## 更新 _checkpoint.md

```markdown
## 当前状态
- Phase: 3.5 reflect ✅

## 产出物
- [x] _reflection.md（裁决: GO / 先澄清 / 先验证）

## 下一步
read_file: skills/flow-apply/SKILL.md   # 仅当裁决含 GO 且无未决的「先澄清/先验证」
```

## 完成标准

- [ ] _reflection.md 已写
- [ ] Q1、Q2 都有书面回答（无疑点须显式写「无」）
- [ ] 拿不准的事实/技术点已做联网核实（WebSearch）并记录结论
- [ ] 裁决明确（GO 互斥；先澄清/先验证 可单独或并存）
- [ ] 若为「先澄清」已回 flow-explore；若为「先验证」已在 tasks.md 插入 spike
- [ ] _checkpoint.md 已更新（裁决含 GO 且无未决澄清/验证时指向 flow-apply）
