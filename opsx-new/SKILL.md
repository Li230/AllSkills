---
name: opsx-new
description: "创建 opsx-flow 变更脚手架。生成 openspec/changes/<name>/ 目录结构 + .openspec.yaml + _checkpoint.md（执行契约）。触发词：\"新建变更\"、\"opsx-new\"、\"/opsx:new\"、\"开始走流程\"。"
---

# Opsx-New — 变更脚手架

## 目的

创建变更目录结构 + 执行契约，为后续 6 个阶段准备容器。

## 何时使用

- 用户说"走流程"、"开始一个变更"、"新建变更"
- opsx-flow 总览 skill 调度到此

## 执行步骤

### 1. 确认变更名

向用户确认变更名（kebab-case），如 `project-restructure`、`add-dark-mode`。

### 2. 创建目录结构

```
openspec/changes/<change-name>/
├── .openspec.yaml          ← 变更元数据
├── _checkpoint.md          ← 执行契约（状态机）
├── specs/                  ← Phase 2 产出（delta specs）
│   └── <capability>/
└── (后续阶段产出 proposal.md / design.md / tasks.md)
```

### 3. 写 .openspec.yaml

```yaml
# OpenSpec change metadata
change: <change-name>
capability: []           # Phase 2 填充
status: in-progress
created: <YYYY-MM-DD>
```

### 4. 写 _checkpoint.md（执行契约）

```markdown
# Execution Contract: <change-name>

## 当前状态
- Phase: 0 scaffold ✅
- 变更名: <change-name>
- 创建时间: <YYYY-MM-DD>

## 产出物
- [x] .openspec.yaml
- [x] _checkpoint.md

## 下一步
read_file: skills/opsx-explore/SKILL.md
```

### 5. 确认并告知用户

```
✅ 变更 <change-name> 脚手架已创建
📂 openspec/changes/<change-name>/
下一步: Phase 1 Explore（需求质询）
```

## 完成标准

- [ ] 变更名已确认
- [ ] 目录已创建
- [ ] .openspec.yaml 已写
- [ ] _checkpoint.md 已写（指向 opsx-explore）
