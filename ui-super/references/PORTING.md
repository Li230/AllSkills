# 抄视觉不抄代码：移植手册

把 React + Tailwind + Radix 组件的观感移植到任意栈（典型：原生 HTML/CSS/JS 单文件应用）。

## 一、提取三清单

对着参考组件（浏览器 DevTools 检视 computed style 最准，截图兜底）逐层提取：

**tokens 层**
- 色板：背景/前景/主色/边框，记 hex 或 oklch；注意暗色模式是否成对
- 字体：family 栈、字号阶梯、行高、字重
- 间距：基准尺度（Tailwind 的 4px 网格 → 记成 CSS 变量 `--sp-1..n`）
- 圆角、阴影（多层阴影逐层记）、边框色与宽

**骨架层**
- 布局：flex 还是 grid、方向、gap、列宽配比（如 `grid-template-columns: 240px 1fr 320px`）
- 密度：控件 padding、行高、表格行距
- 断点：何时折行/收栏（Tailwind 的 md:lg: → 记实际像素）

**动效层**（最常漏抄）
- 过渡：属性 + 时长 + 缓动（如 `all .2s cubic-bezier(.4,0,.2,1)`）
- 态：hover / focus-visible / active / disabled 各是什么变化
- 入场：有无 fade/slide/stagger，时长与延迟

## 二、翻译对照表

| React 栈里的东西 | 原生栈的等价物 |
|---|---|
| Tailwind class（`bg-zinc-900 rounded-xl p-4`） | 语义 CSS 变量（`background: var(--bg); border-radius: var(--r-lg); padding: var(--sp-4)`） |
| `tailwind.config` theme.extend | `:root {}` 变量块 |
| Radix Dialog | 原生 `<dialog>` + `showModal()` |
| Radix Popover/Dropdown | `popover` 属性（较新浏览器）或最小 JS toggle + 外点关闭 |
| Radix Tabs | radio :checked 兄弟选择器或最小 JS |
| React state（开关/循环标记） | 一个 `dataset`/class 切换，几行原生 JS |
| framer-motion 入场动画 | CSS `@keyframes` + `animation-delay` 递增做 stagger |
| shadcn 变体（variant=destructive…） | 修饰 class（`.btn.danger`） |

原则：交互降级取**最小可行实现**，不为还原一个 hover 菜单手写 200 行 JS。

## 三、实施与验收

1. tokens 先行：先落 `:root` 变量块，再写结构，最后补动效
2. 布局防压碎：内容区设合理 `min-width`，窄屏横向滚动优于压碎；主文字 `white-space: nowrap` 防竖排
3. 验收两档宽度（1280 / 1920）+ 深浅色（若参考有）+ 全交互态过一遍（hover/focus/禁用）
4. 动效核对：录屏或连续截图对比参考的手感——时长差 100ms 就能看出来
5. 无 JS 错误、无 console 警告，页面功能回归通过后才算完成
