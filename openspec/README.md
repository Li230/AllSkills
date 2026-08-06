# OpenSpec 工作流技能包（openspec/）

基于 **OpenSpec CLI**（AI-native spec-driven development）的完整变更管理技能集合，覆盖一个变更从**诞生到归档**的全生命周期。

## 这是什么

OpenSpec 是一套"**先写规格，再写代码**"的变更管理框架。本文件夹把 OpenSpec 的每个环节封装成独立 skill，让 AI agent 在正确的时机执行正确的操作。

**核心思想**：
- 每个变更（change）都有完整档案：proposal → specs → design → tasks
- 变更期间写 **delta specs**，归档时合入**主 specs**（主规格永远最新）
- 全程可验证：`openspec validate` / `openspec change verify`

## 技能清单（15 个）

| 阶段 | 技能 | 用途 |
|------|------|------|
| **安装** | `openspec-install` | 全局安装 OpenSpec CLI（npm/pnpm/yarn/bun/nix） |
| **初始化** | `openspec-initial` | 在项目中初始化 OpenSpec（`openspec init`） |
| **入门** | `openspec-onboard` | 引导式完整工作流入门（新手教程） |
| **建变更** | `openspec-new` | 新建 OpenSpec change（`/opsx:new`） |
| **探索** | `openspec-explore` | 需求探索与问题澄清（`/opsx:explore`） |
| **写档案** | `openspec-continue` | 按依赖链逐个创建 artifact（`/opsx:continue`） |
| **快进** | `openspec-ff` | 一次性生成全部规划 artifacts（`/opsx:ff`） |
| **配置** | `openspec-config` | 配置项目与全局设置 |
| **自定义** | `openspec-schema` | 自定义工作流 schema（fork/validate/which） |
| **实现** | `openspec-apply` | 按 tasks 实现变更（`/opsx:apply`） |
| **验证** | `openspec-verify` | 验证实现与 artifacts 一致性（`/opsx:verify`） |
| **同步** | `openspec-sync` | 将 delta specs 同步进主 specs（`/opsx:sync`） |
| **归档** | `openspec-archive` | 归档已完成变更（`/opsx:archive`） |
| **批量归档** | `openspec-bulk-archive` | 批量归档多个变更（`/opsx:bulk-archive`） |
| **升级** | `openspec-update` | 升级 CLI 后重新生成 AI 工具指令 |

## 标准流程

```
openspec-install → openspec-initial → openspec-onboard（可选）
→ openspec-new → openspec-explore（可选）→ openspec-continue / openspec-ff
→ openspec-apply → openspec-verify → openspec-sync（可选）→ openspec-archive / openspec-bulk-archive
```

## 快速开始

```bash
# 1. 安装 CLI
npm install -g @fission-ai/openspec   # 或按 openspec-install 的说明

# 2. 初始化项目（在项目根目录）
openspec init

# 3. 开始一个变更
openspec change new <change-name>
# 或使用 skill 引导：说「/opsx:new <名称>」

# 4. 按依赖链写 artifacts
/opsx:continue    # 逐个写 proposal → specs → design → tasks
/opsx:ff          # 或一次性全部生成

# 5. 实现 + 验证 + 归档
/opsx:apply       # 按 tasks 实现
/opsx:verify      # 验证一致性
/opsx:archive     # 归档合入主 specs
```

## 与 opsx-flow 整合

本套 skill 是 **opsx-flow**（OpenSpec × Superpowers 整合编排器）的骨架层：

- `opsx-flow` 负责**编排**：六阶段流程（explore → proposal → plan → apply → verify → archive）
- 本文件夹的 skill 负责**执行**：每阶段对应的 OpenSpec 操作
- 代码质量约束（TDD / Python 闸门 / 审查）由 superpowers 家族 skill 补充

```
用户说「走流程」→ opsx-flow 编排
  ├─ Phase 1 explore → grill-me 质询
  ├─ Phase 2 proposal → openspec-new（本包）
  ├─ Phase 3 plan → tasks.md（原子任务+类型标注）
  ├─ Phase 4 apply → openspec-apply（本包）+ 质量闸门
  ├─ Phase 5 verify → openspec-verify（本包）+ 换模型审查
  └─ Phase 6 archive → openspec-archive（本包）
```

## 设计原则

1. **Spec before code**：先写规格再写代码
2. **变更可追溯**：每个 change 有完整档案，归档后主 specs 保持最新
3. **验证闭环**：apply 后必须 verify，确认实现与文档一致
4. **根上修**：结构性问题回 artifacts 改，不在代码产物上打补丁

## 参考

- [OpenSpec 官方文档](https://github.com/Fission-AI/OpenSpec)
- [OpenSpec Commands](https://github.com/Fission-AI/OpenSpec/blob/main/docs/commands.md)
