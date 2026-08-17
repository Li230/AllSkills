---
description: 'opsx-flow Phase 4: 执行+调度。按 tasks.md 的类型标注调度对应 skill 执行，质量闸门兜底，每 3-5
  任务更新执行契约。触发词："执行"、"flow-apply"、"Phase 4"。'
name: flow-apply
---

# Flow-Apply — Phase 4: 执行与调度

## ⚠️ 进入前必做

```
read_file: openspec/changes/<change-name>/_checkpoint.md
read_file: openspec/changes/<change-name>/_reflection.md
```
确认 Phase 3 plan 已完成、tasks.md 已写，且 **_reflection.md 裁决含 GO 且无未决「先澄清/先验证」**（未经 Phase 3.5 反思闸门不得进入执行）。若 _reflection.md 缺失，或裁决仅含「先澄清/先验证」未含 GO，先回到 flow-reflect 处理完毕再执行。

## 目的

按调度表执行任务，质量约束兜底。

## 执行循环

```
对 tasks.md 中每个未完成 [ ] 任务：
  ├─ 1. 读任务 → 判断类型（从 **类型** 标注）
  ├─ 2. 按类型读对应 skill 的 SKILL.md（见下方调度表）
  ├─ 3. 执行（写代码/文档/配置/文件操作）
  ├─ 4. 跑验证命令（任务里的"验证："行）
  ├─ 5. 验证通过 → tasks.md 打勾 [x]
  ├─ 6. 验证失败 → read_file skills/systematic-debugging/SKILL.md → 修复 → 重验
  └─ 7. 每 3-5 个任务更新一次 _checkpoint.md
```

## 按类型调度

| 类型 | 执行前必读 | 质量闸门 |
|---|---|---|
| `file-op` | — | 验证命令通过 |
| `docs` | — | grep/ls 验证 |
| `git-op` | — | git status 验证 |
| `feature` | `skills/test-driven-development/SKILL.md` | TDD 红→绿→重构 |
| `bugfix` | `skills/systematic-debugging/SKILL.md` | 根因 + 测试通过 |
| `ui` | `skills/frontend-design/SKILL.md` | 构建/预览验证 |
| `python` | `skills/python-quality-guide/SKILL.md` | `python-quality-gate`（flake8+black+pytest）全绿 |
| `verify` | `skills/verification-before-completion/SKILL.md` | 命令输出证据 |

> ⚠️ **python 类型任务**：完成前必须跑 gate，三项全绿才能打勾。禁止跳过。

> ⚠️ **任何任务**：打勾前必须给出**命令输出证据**。禁止空口"已完成"。

## 进度更新

每 3-5 个任务（或每完成一组），更新 _checkpoint.md：

```markdown
## 当前状态
- Phase: 4 apply 🔄
- 完成任务: X/N

## 已完成
- [x] 1.1 ...
- [x] 1.2 ...

## 下一步任务
- [ ] 2.1 ...

## 全部完成后
read_file: skills/flow-verify/SKILL.md
```

## 完成标准

- [ ] tasks.md 所有任务 [x]
- [ ] 每个任务有验证证据
- [ ] python 任务跑过 gate
- [ ] _checkpoint.md 标记 Phase 4 完成（指向 flow-verify）