---
name: opsx-flow
description: "OpenSpec × Superpowers 整合工作流（编排器总览）。以 OpenSpec 流程为骨架（explore→new→proposal→plan→apply→verify→archive），每阶段拆为独立 skill，通过执行契约（_checkpoint.md）驱动状态流转。触发词：\"走流程\"、\"opsx-flow\"、\"开始一个变更\"、\"按框架做\"。"
---

# Opsx-Flow — 总览与调度

> v3.1 — 8 个模块收拢在 `opsx-flow/` 单文件夹（子目录分阶段），脚手架生成文件架构，执行契约驱动流转

## 设计哲学

```
OpenSpec  管 WHAT（做什么、记录什么）—— 骨架/档案
Superpowers 管 HOW（怎么做得好）—— 思考/质量
opsx-flow 管 WHEN（每个阶段调谁）—— 调度
_checkpoint.md 管 WHERE（当前在哪、下一步去哪）—— 状态机
```

## 六阶段 + 脚手架，8 个模块（都在本文件夹内）

| 阶段 | 模块文件 | 产出 | 必读前置 skill |
|---|---|---|---|
| 脚手架 | `new/SKILL.md` | 变更目录 + .openspec.yaml + _checkpoint.md | — |
| Phase 1 | `explore/SKILL.md` | 需求范围 + checkpoint 更新 | grill-me（内嵌） |
| Phase 2 | `proposal/SKILL.md` | proposal.md + specs/ | brainstorming |
| Phase 3 | `plan/SKILL.md` | design.md + tasks.md | — |
| Phase 4 | `apply/SKILL.md` | 完成的 tasks | 按任务类型调度 |
| Phase 5 | `verify/SKILL.md` | 验证报告 | verification-before-completion |
| Phase 6 | `archive/SKILL.md` | 归档 + STATUS 更新 | openspec-archive |

## ⚠️ 核心机制

### 1. 分阶段加载
每个阶段是独立模块文件，进入时 `read_file` 对应 `opsx-flow/<阶段>/SKILL.md`，指令在上下文最近位置。

### 2. 执行契约（_checkpoint.md）
每个变更目录下有 `_checkpoint.md`，记录当前 phase、产出物、下一步该读哪个模块。会话中断后读它恢复状态。

### 3. 强制 skill 调用
每个模块顶部 `⚠️ 进入前必做: read_file ...`，不读不继续。

## 流程流转

```
用户: "走流程"
  │
  ├─ read_file: skills/opsx-flow/new/SKILL.md → 创建变更目录 + _checkpoint.md
  │
  ├─ read_file: skills/opsx-flow/explore/SKILL.md → 质询 → 更新 checkpoint
  │
  ├─ read_file: skills/opsx-flow/proposal/SKILL.md → 必读 brainstorming → 写 proposal → 更新 checkpoint
  │
  ├─ read_file: skills/opsx-flow/plan/SKILL.md → 写 design + tasks → 更新 checkpoint
  │
  ├─ read_file: skills/opsx-flow/apply/SKILL.md → 按调度表执行 → 更新 checkpoint
  │
  ├─ read_file: skills/opsx-flow/verify/SKILL.md → 换模型审查 → 更新 checkpoint
  │
  └─ read_file: skills/opsx-flow/archive/SKILL.md → 归档 → 最终 checkpoint
```

## 调度表（Phase 4 apply 用）

| 任务类型 | 激活 skill | 质量闸门 |
|---|---|---|
| `file-op` | — | 验证命令通过 |
| `docs` | — | grep/ls 验证 |
| `git-op` | — | git status 验证 |
| `feature` | test-driven-development | TDD 红→绿→重构 |
| `bugfix` | systematic-debugging | 根因 + 测试通过 |
| `ui` | frontend-design | 构建/预览验证 |
| `python` | python-quality-guide + python-quality-gate | flake8+black+pytest 全绿 |
| `verify` | verification-before-completion | 命令输出证据 |

## 反模式

- ❌ 不读 skill 的 SKILL.md 直接执行
- ❌ 跳过必读前置 skill
- ❌ 不更新 _checkpoint.md 就进下一阶段
- ❌ Python 任务不跑 gate 就打勾
- ❌ 自审代替换模型审查

## 恢复机制

会话中断后：
```
read_file openspec/changes/<change-name>/_checkpoint.md
→ 读当前 phase → read_file skills/opsx-flow/<阶段>/SKILL.md → 继续
```
