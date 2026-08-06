---
name: opsx-flow
description: OpenSpec × Superpowers 整合工作流（编排器）。以 OpenSpec 流程为骨架（explore→proposal→plan→apply→verify→archive），嵌入 superpowers/agent-skills 思考方法论与质量约束，通过调度表盘活现有 skill。触发词："走流程"、"opsx-flow"、"开始一个变更"、"按框架做"。
---

# Opsx-Flow — OpenSpec × Superpowers 整合工作流

**编排器 skill**：不重复造轮子，而是调度现有 skill，把"变更管理"（OpenSpec）和"代码质量"（superpowers/agent-skills）焊在一起。

## 设计哲学

```
OpenSpec 管 WHAT（做什么、记录什么）—— 骨架/档案
Superpowers 管 HOW（怎么做得好）—— 思考/质量
本 skill 管 WHEN（每个阶段调谁）—— 调度
```

## 完整流程（六阶段）

```
explore → proposal → plan → apply → verify → archive
```

### Phase 1: explore（需求扩充 + 质询）
**目的**：写 proposal 前把需求挖透，避免"proposal 写歪全盘皆输"。

1. 读上下文：项目背景、相关 specs、用户原始诉求
2. **grill-me 质询**：苏格拉底式提问，至少覆盖：
   - 需求边界（做什么/不做什么）
   - 用户/场景（谁用、失败代价）
   - 约束（性能/安全/兼容）
   - 验收标准（怎么算完成）
3. 记录 grill 问答 → 需求范围界定（scope）
4. 产出：需求范围说明

### Phase 2: proposal（构建方案）
**目的**：写清楚"为什么做 + 做什么"。

1. 调 `brainstorming`（superpowers）：对方案做设计思考
2. 参考 agent-skills 的 /spec 原则：**Spec before code**
3. 产出：`proposal.md`（含需求范围、目标、非目标、验收标准）

### Phase 3: plan（原子任务规划）
**目的**：拆成可执行、可验证的原子任务。

1. 每个任务必须：**原子**（一件事）、**可验证**（有完成标准）、**带类型标注**（供调度）
2. 标注任务类型（重要！决定 apply 阶段用哪个 skill）
3. 产出：`design.md` + `tasks.md`（任务格式：`[ ] 类型: 描述`）

### Phase 4: apply（执行 + 调度）
**目的**：按调度表执行任务，质量约束兜底。

```
循环每个未完成任务：
  ├─ 读任务 → 判断类型（从标注/涉及文件）
  ├─ 调对应 skill（见调度表）
  ├─ 执行（写代码/文档/配置）
  ├─ 完成前验证（verification-before-completion 或硬闸门）
  ├─ 全绿 → tasks.md 打勾 [x]
  └─ 有错 → systematic-debugging → 修复 → 重验
```

### Phase 5: verify（验证 + 换模型审查）
**目的**：独立视角审查，防自审走过场。

1. `openspec-verify`：实现 vs specs 一致性（结构）
2. **换模型审查**：切换另一个基座模型做 code review（视角独立）
3. 审查意见 → 修复 → 复审

### Phase 6: archive（归档）
**目的**：变更入档，主规格保持最新。

1. `openspec-archive`：delta specs 合入主 specs
2. 更新记忆/MOC（如有）

## 调度表（核心，可扩展）

| 任务类型 | 激活 skill | 来源 | 状态 |
|---|---|---|---|
| 新功能 | `test-driven-development` | superpowers | ✅ 已装 |
| 修 bug | `systematic-debugging` | superpowers | ✅ 已装 |
| UI 页面 | `frontend-design` | 已装 | ✅ 已装 |
| 需求/方案讨论 | `brainstorming` | superpowers | ✅ 已装 |
| 完成前验证 | `verification-before-completion` | superpowers | ✅ 已装 |
| **Python 代码** | `python-quality-guide`（软）+ `python-quality-gate`（硬） | 自建 | ✅ 已装 |
| 变更审查 | `requesting-code-review`（换模型） | superpowers | ❌ 待装 |
| 交付收尾 | `finishing-a-development-branch` | superpowers | ❌ 待装 |

**扩展方法**：新 skill 装好后，在调度表加一行即可。

## 质量闸门（apply 阶段强制）

- **Python 任务**：`python-quality-gate`（flake8 + black + pytest）全绿才打勾
- **其他代码任务**：`verification-before-completion`（跑测试/构建出证据）
- **任何任务**：宣称完成前必须给出**命令输出证据**，禁止空口"已完成"

## 反模式（Red Flags）

- ❌ 跳过 explore 直接写 proposal（需求没挖透）
- ❌ 任务不带类型标注（apply 无法调度）
- ❌ Python 任务不跑 gate 就打勾
- ❌ 自审代替换模型审查
- ❌ 发现设计错只改代码不回写 specs（归档失真）

## 使用示例

```
用户: "走流程，把 traffic 的报警导出功能做了"
Agent: opsx-flow 启动
  ├─ Phase 1: grill-me（导出格式? 权限? 谁用? 失败代价?）→ 范围
  ├─ Phase 2: brainstorming → proposal.md
  ├─ Phase 3: 拆任务（含类型标注）→ tasks.md
  ├─ Phase 4: apply（功能→TDD，UI→frontend-design，完成→验证）
  ├─ Phase 5: openspec-verify + 换模型审查
  └─ Phase 6: archive + 更新记忆
```

## 前置条件

- 项目已初始化 OpenSpec（`openspec init`，见 openspec-initial）
- 调度表涉及的 skill 已安装
