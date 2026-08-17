---
description: 'opsx-flow Phase 3: 原子任务规划。产出 design.md（关键决策+风险）和 tasks.md（带类型标注的可验证原子任务）。触发词："拆任务"、"flow-plan"、"Phase
  3"。'
name: flow-plan
---

# Flow-Plan — Phase 3: 任务规划

## ⚠️ 进入前必做

```
read_file: openspec/changes/<change-name>/_checkpoint.md
```
确认 Phase 2 proposal 已完成。

## 目的

拆成可执行、可验证的原子任务。

## 执行步骤

### 1. 写 design.md

路径：`openspec/changes/<change-name>/design.md`

必含 section：
```markdown
## Context       ← 背景
## Goals / Non-Goals
## Decisions     ← 关键决策（带理由）
## Risks / Trade-offs
## Migration Plan ← 落地顺序
```

### 2. 写 tasks.md

路径：`openspec/changes/<change-name>/tasks.md`

**每个任务三条件：**

| 条件 | 说明 |
|---|---|
| 原子 | 一件事，不混合 |
| 可验证 | 有明确完成标准（命令输出/文件存在） |
| 带类型标注 | 决定 Phase 5 调哪个 skill |

格式：
```markdown
- [ ] **类型**: 描述
  - 验证：`<具体命令>`
```

类型取值：

| 类型 | Phase 5 调度 |
|---|---|
| `file-op` | 直接执行 |
| `docs` | 直接执行 |
| `git-op` | 直接执行 |
| `feature` | test-driven-development |
| `bugfix` | systematic-debugging |
| `ui` | frontend-design |
| `python` | python-quality-guide + gate |
| `verify` | verification-before-completion |

### 3. 更新 _checkpoint.md

```markdown
## 当前状态
- Phase: 3 plan ✅

## 产出物
- [x] design.md
- [x] tasks.md（N 个任务）

## 任务类型分布
- file-op: X
- docs: X
- ...

## 下一步
read_file: skills/flow-reflect/SKILL.md   # Phase 4 执行前反思闸门，先反思再执行
```

## 完成标准

- [ ] design.md 已写（含 Decisions + Risks）
- [ ] tasks.md 已写，每个任务有类型标注 + 验证条件
- [ ] _checkpoint.md 已更新（指向 flow-reflect）