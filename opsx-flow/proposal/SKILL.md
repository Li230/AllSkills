---
name: opsx-proposal
description: "opsx-flow Phase 2: 方案构建。必读 brainstorming skill 做设计思考，产出 proposal.md 和 specs/ delta。触发词：\"写方案\"、\"opsx-proposal\"、\"Phase 2\"。"
---

# Opsx-Proposal — Phase 2: 方案构建

## ⚠️ 进入前必做

```
read_file: skills/brainstorming/SKILL.md
read_file: openspec/changes/<change-name>/_checkpoint.md
```

> **不读 brainstorming 不能继续。** proposal 质量依赖设计思考方法论。

## 前置检查

确认 Phase 1 explore 已完成、需求范围已明确。

## 目的

写清楚"为什么做 + 做什么"，产出 `proposal.md` + `specs/`。

## 执行步骤

### 1. 读 brainstorming SKILL.md，按其方法论做设计思考

brainstorming 核心是：
- 探索用户真实意图（不是表面需求）
- 列出多个方案，权衡取舍
- 明确 What Changes / Impact

### 2. 写 proposal.md

路径：`openspec/changes/<change-name>/proposal.md`

必含 section：
```markdown
## Why          ← 为什么做（痛点/现状）
## What Changes ← 做什么（具体变更）
## Capabilities ← 新增/修改的能力
## Impact       ← 影响哪些文件/模块
```

### 3. 写 specs/ delta

路径：`openspec/changes/<change-name>/specs/<capability>/spec.md`

格式：
```markdown
## ADDED Requirements

### Requirement: <名称>
<SHALL/MUST 描述>

#### Scenario: <场景名>
- **WHEN** <条件>
- **THEN** <预期>
```

### 4. 更新 .openspec.yaml 的 capability 字段

### 5. 更新 _checkpoint.md

```markdown
## 当前状态
- Phase: 2 proposal ✅

## 产出物
- [x] proposal.md
- [x] specs/<capability>/spec.md

## 方案要点
<一句话总结>

## 下一步
read_file: skills/opsx-flow/plan/SKILL.md
```

## 完成标准

- [ ] brainstorming SKILL.md 已读
- [ ] proposal.md 已写（含 Why/What/Capabilities/Impact）
- [ ] specs/ delta 已写（如适用）
- [ ] _checkpoint.md 已更新（指向 opsx-plan）
