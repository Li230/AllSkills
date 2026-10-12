---
name: ui-super
description: 从 21st.dev（最大 React UI 组件注册表）等顶级组件库提取视觉 DNA 并移植到任意技术栈，包括原生 HTML/CSS/JS。触发词："ui-super"、"参考 21st.dev"、"21st 风格"、"抄视觉"、"去组件库找参考"、"组件库风格移植"。当用户想给现有页面找一流组件库的视觉参考、把 React/Tailwind 组件的观感移植到非 React 项目、或在 superdesign 出稿前先建立视觉情报与设计 tokens 时使用。
---

ui-super = **视觉情报 + 移植**。与 superdesign 技能分工明确：superdesign 管无限画布上的设计出稿与迭代流程；ui-super 管"去哪找参考、怎么抄得像、怎么落地不背依赖"。两者可串行：先用 ui-super 提取视觉 DNA，再交给 superdesign 按此出稿。

---

# 核心原则：抄视觉，不抄代码

21st.dev 的组件全部是 React + Tailwind CSS + Radix UI（shadcn 规范）。除非目标项目本身就是这个栈且已用 shadcn CLI，否则：

- **不复制组件源码，不引入 React / Tailwind / Radix 依赖**——为一个按钮拖入整条 React 工具链是本末倒置
- 抄的是三层视觉 DNA：**tokens**（色板/字号/间距/圆角/阴影）、**骨架**（布局结构/断点/密度）、**动效**（时长/缓动/触发方式）
- 每层怎么提、怎么翻译进目标栈，见 [PORTING.md](references/PORTING.md)

# 流程

## 1. 锁定目标

先弄清三件事，缺一先问用户：目标页面（现有页面给截图/URL，新页面要描述）、目标技术栈（决定第 4 步走 a 还是 b）、风格偏好（暗色/亮色、密度、气质关键词）。

## 2. 21st.dev 选参考

按 [21STDEV.md](references/21STDEV.md) 的类目入口和聚合库风格速查找 2-3 个参考组件。要点：

- 用类目检索（如 inputs 949+、sign-in 103+、AI chat）而不是漫无目的逛
- 聚合库气质差异大：Aceternity 偏炫酷动效、shadcn 偏克制工程风、Magic UI 偏营销视觉——按产品气质选
- **每日只有 2 次免费复制**，把额度留给最核心的 1-2 个组件取其 tokens；其余靠浏览器截图 + 检视（DevTools 看 computed style）提取
- AI chat / 思考流 / 流式输出类组件对智能体产品前端最有参考价值

## 3. 提取视觉 DNA

对每个参考产出一个三清单（模板见 PORTING.md）：

```
tokens: 色板(hex/oklch) / 字号阶梯 / 间距尺度 / 圆角 / 阴影 / 边框
骨架: 布局结构(flex/grid) / 列宽配比 / 断点行为 / 密度(行高padding)
动效: 过渡属性+时长+缓动 / hover·focus·active 态 / 入场动画
```

## 4. 落地（按目标栈二选一）

- **a. 直接改代码**（原生/任意栈）——按 PORTING.md 翻译手册实施：Tailwind class → 语义 CSS 变量、Radix 交互 → 原生 `dialog`/`details`/popover 降级、React 状态 → 最小原生 JS。改完跑一遍页面确认无 JS 错误、无布局压碎（至少验 1280px 与 1920px 两档宽度）
- **b. 喂给 superdesign**（用户明确要画布出稿时）——把三清单整理成 design tokens 交给 superdesign 技能作为其 design-system 输入，走 superdesign 自己的 SOP

## 5. 视觉验收

并排对比参考截图与实现截图，列偏差清单（色值/间距/动效手感），逐项迭代到"肉眼无明显差异"。动效手感（时长与缓动）是最常被漏抄的一层，单独核对。

# 边界

- 21st.dev 免费额度为每日 2 次组件复制，浏览与检索不限；不要反复尝试绕过额度
- 非 React 项目不要用 21st MCP 安装组件（它是 shadcn registry 格式）；MCP 只适合 React 栈项目
- 版权：视觉风格与设计模式可借鉴；若整段复制组件源码到商业项目，需遵循原组件的许可条款
