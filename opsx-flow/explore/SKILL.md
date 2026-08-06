---
name: opsx-explore
description: "opsx-flow Phase 1: 需求探索与质询。通过 grill-me 苏格拉底式提问挖透需求边界，产出需求范围说明并更新执行契约。触发词：\"探索需求\"、\"opsx-explore\"、\"Phase 1\"。"
---

# Opsx-Explore — Phase 1: 需求探索

## ⚠️ 进入前必做

```
read_file: openspec/changes/<change-name>/_checkpoint.md
```
确认 Phase 0 脚手架已完成。

## 目的

写 proposal 前把需求挖透，避免"proposal 写歪全盘皆输"。

## 执行步骤

### 1. 读上下文

- 项目背景、相关 specs、用户原始诉求
- `read_file openspec/STATUS.md`（如存在）
- 浏览相关代码入口

### 2. Grill-me 质询

> 如有 grill-me skill，先 `read_file skills/grill-me/SKILL.md`。否则用以下内嵌清单。

**至少覆盖四个维度，逐一向用户提问：**

- **需求边界**：做什么？不做什么？明确排除什么？
- **用户/场景**：谁用？什么场景？失败的代价是什么？
- **约束**：性能/安全/兼容性有哪些硬约束？
- **验收标准**：怎么算完成？什么证据算通过？

> ⚠️ 不要自己脑补答案。必须问用户，拿到明确回复。

### 3. 记录需求范围

把用户回答整理成需求范围说明（scope）。

### 4. 更新 _checkpoint.md

```markdown
# Execution Contract: <change-name>

## 当前状态
- Phase: 1 explore ✅
- 变更名: <change-name>

## 需求范围
<整理后的 scope>

## 验收标准
<用户确认的标准>

## 下一步
read_file: skills/opsx-flow/proposal/SKILL.md
```

## 完成标准

- [ ] 项目上下文已读
- [ ] 四维度质询已问用户并拿到回复
- [ ] 需求范围说明已整理
- [ ] _checkpoint.md 已更新（指向 opsx-proposal）
