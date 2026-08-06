---
description: 'opsx-flow Phase 6: 归档收尾。变更移至 archive/、更新 STATUS.md、更新记忆、产出最终 checkpoint。触发词："归档"、"flow-archive"、"Phase
  6"、"收尾"。'
name: flow-archive
---

# Flow-Archive — Phase 6: 归档

## ⚠️ 进入前必做

```
read_file: openspec/changes/<change-name>/_checkpoint.md
```
确认 Phase 5 verify 已完成、验证通过。

## 目的

变更入档，主规格保持最新。

## 执行步骤

### 1. 归档变更

```bash
mv openspec/changes/<change-name> openspec/changes/archive/$(date +%Y-%m-%d)-<change-name>
```

保留 `_checkpoint.md` 作为归档记录。

### 2. 更新 STATUS.md（如存在）

更新 section：
- §0 一句话现状（新归档的变更）
- §1 演进时间线（加一行）
- §3 能力图谱（新增 capability 状态）
- §7 任务状态总览（标记已归档）

### 3. 更新记忆

如果有经验教训：
- `memory/YYYY-MM-DD.md` — 原始记录
- `MEMORY.md` — 长期记忆（如有必要）

### 4. 产出最终 checkpoint

```markdown
## 当前状态
- Phase: 6 archive ✅
- 变更名: <change-name>
- 归档路径: openspec/changes/archive/<date>-<change-name>/

## 产出物总览
- [x] proposal.md
- [x] specs/
- [x] design.md
- [x] tasks.md（全部 [x]）
- [x] _checkpoint.md（6 phase 全完成）

## STATUS.md 已更新: ✅/不适用
## 记忆已更新: ✅/不适用
```

## 完成标准

- [ ] 变更已移至 archive/
- [ ] STATUS.md 已更新（如适用）
- [ ] 记忆已更新（如有经验教训）
- [ ] 最终 _checkpoint.md 已产出