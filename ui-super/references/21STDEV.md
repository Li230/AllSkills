# 21st.dev 情报档案

三轮联网搜索沉淀（2026-09 核实）。写 skill 时以此为事实底座，数值可能随时间变化，关键决策（如付费）前可让 agent 复核官网。

## 是什么

- 目前最大的 React UI 组件注册表，自称"设计工程师的 npm"；YC 孵化，360 万+ 开发者，客户含 Google、Meta、NVIDIA、Shopify
- 定位演进："UI building blocks for the agentic internet"——越来越面向 AI/智能体应用的 UI 构建

## 目录构成

| 资源 | 入口 | 说明 |
|---|---|---|
| 社区组件 | 21st.dev/community/components | 2000+ 营销区块（动画 Hero/渐变背景/页脚）+ 2100+ UI 组件（按钮/AI 聊天/卡片/导航/登录） |
| 类目检索 | 同上 | 按类目聚合，如 inputs 949+、sign-in 103+ |
| 组件库聚合 | 21st.dev/community/libraries | 139+ 库、700+ 设计工程师作品 |
| 完整模板 | 官网 templates 区 | 多页生产级应用模板，部分付费 |

## 聚合库风格速查（选参考用）

- **shadcn/ui** —— 克制工程风，最接近"默认该长什么样"的基准
- **Aceternity UI** —— 炫酷动效、shader/3D，适合营销首页
- **Magic UI** —— 营销视觉组件（动画、渐变、效果字）
- **Origin UI / ReUI / Kokonut UI / Geist** —— 表单与基础件为主，密度和气质各异

## 技术栈与安装

- 全部 React + Tailwind CSS + Radix UI，以 shadcn registry 格式发布
- React 栈项目可 shadcn CLI 安装；组件页自带 AI prompt，可粘贴进 Cursor/Claude Code/v0 让 AI 重建进代码库

## MCP

- 原 Magic MCP（@21st-dev/magic）已被**统一 21st MCP** 取代，经 21st CLI 安装（21st.dev/mcp）
- 能力：搜目录 / 装组件 / 生成 UI（21st AI 多变体）/ 发布，终端或任意 MCP client
- 适用 Cursor、Windsurf、Cline、Claude 等 MCP client
- **仅对 React 栈项目有意义**；非 React 项目勿装

## 收费

- 浏览、检索免费；**每日 2 次免费组件复制**
- 订阅制解锁无限复制 + 付费模板；21st AI 按月度积分另计
