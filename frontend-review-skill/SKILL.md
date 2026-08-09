---
description: 对 AI 生成或交付的前端代码（React/Vue/原生 JS）做边界验收：检查内存泄漏、资源清理、安全、依赖健康、可访问性、性能、错误处理、竞态、响应式、代码质量，输出分级问题清单+修复代码+评分。触发词：验收前端、审查前端代码、检查内存泄漏、前端质量把关、review
  frontend code、帮我看看这段前端代码有没有问题。
name: frontend-review-skill
---

# 前端边界验收 (Frontend Boundary Review)

作为**验收角色**，对 AI 写的前端代码做系统化边界审查：不止看"功能对不对"，更看"长期运行会不会炸"——内存泄漏、资源泄漏、安全漏洞、可访问性缺失等。

## 何时使用

用户要求验收/审查前端代码时触发：
- 「验收这个前端」「审查 AI 写的页面」「帮我检查这段代码」
- 「看看有没有内存泄漏/安全问题」「页面越用越卡怎么办」
- 任何需要**质量把关**的前端交付场景

## 输入 / 输出

- **输入**：前端代码目录或文件（React/Vue/原生 JS）
- **输出**：markdown 验收报告——🔴 阻断 / 🟡 警告 / ⚪ 建议 三级问题清单 + 每项修复代码 + 总分

## 执行流程（总览）

1. **静态扫描**（自动化）：`run_tool_batch` 跑 `scan.py`，产出 findings JSON（证据：文件/行号/规则）
2. **agent 语义审查**（核心，不能省）：按下方 10 维度清单逐项核对——确认真伪、校正修复代码、补脚本漏掉的语义问题（业务逻辑、竞态、设计问题）
3. **输出验收报告**：固定模板 + 评分

---

## 执行

本 skill 附带 batch JSON 文件 `scripts/scan-batch.json`。

**严格按照以下格式调用 `run_tool_batch`，使用 `file_path` 加载文件执行。不要自行构造 `actions` 列表内联传入。**

`run_tool_batch` 的 `file_path` 需要**绝对路径**。你在读取本 SKILL.md 时看到的目录路径即为本 skill 的绝对目录，请用它拼接出完整的 `file_path`。

```
run_tool_batch(
  file_path="<本skill目录>/scripts/scan-batch.json",
  args={
    "code_dir": "/path/to/frontend/src",
    "tech": "all",
    "skill_dir": "<本skill目录>",
    "out_file": "/tmp/frontend_findings.json"
  }
)
```

### Batch 参数

* `code_dir`：待验收前端代码目录（绝对路径）。也可以指向单个文件所在目录；单文件场景可直接手动跑 `scan.py --file <路径>`。
* `tech`：技术栈过滤，`all` / `react` / `vue` / `vanilla`。默认 `all`（自动按扩展名判断）。明确知道是 React/Vue 项目时传对应值可减少误报。
* `skill_dir`：本 skill 的绝对目录（读取本 SKILL.md 时可见），用于定位 `scripts/scan.py`。
* `out_file`：findings JSON 输出路径（绝对路径），如 `/tmp/frontend_findings.json`。

调用 `run_tool_batch` 时必须传入上面所有参数。**不要传 `args={}`**。

### Batch 失败处理

如果 `run_tool_batch` 执行失败（返回 `ok: false` 或中途报错）：
1. 检查「Batch 参数」是否都传了实际值，修正后重试。
2. 仍失败则手动执行：`python3 <skill_dir>/scripts/scan.py --dir <code_dir> --tech <tech> --out <out_file>`，然后 `read_file <out_file>`。
3. 执行完毕后，提示用户：「本次 batch 执行遇到问题，已改为手动完成。是否需要我用 edit_file 调整和优化这个 skill 的 batch 脚本？」

---

## agent 语义审查：10 维度检查清单

对扫描 findings **逐条确认真伪**（正则可能误报，如"文件里有 clearInterval 但与 setInterval 无关"），再按以下清单**人工补漏**（脚本覆盖不了的语义问题）。

### 1. 内存与资源（核心 ⭐ 每项都查）
- [ ] 定时器：`setInterval/setTimeout` 有配套 `clear*` 吗？组件卸载时清了吗？
- [ ] 监听器：`addEventListener` 有 `removeEventListener` 吗？（React：useEffect cleanup；Vue：onUnmounted）
- [ ] 长连接：WebSocket/EventSource 关闭了吗？`onmessage/onerror` 处理器清了吗？
- [ ] `URL.createObjectURL` 有 `revokeObjectURL` 吗？
- [ ] 聊天/消息数组无限 push 吗？（AI 聊天组件高发，必须有截断上限）
- [ ] ⚠️ 仅 agent 审查项（脚本不可覆盖）：隐式全局变量？闭包捕获大对象？DOM 引用（$refs/querySelector 结果）释放了吗？
- [ ] React：卸载后 setState？`useEffect` 空依赖 + 闭包旧值（stale closure）？
- [ ] Vue：`$on` 有 `$off` 吗？大响应式对象用 `shallowRef/markRaw` 了吗？

### 2. 安全
- [ ] `v-html`/`dangerouslySetInnerHTML`/`innerHTML` + 用户输入 → XSS
- [ ] 硬编码密钥（apiKey/secret/token 字面量）
- [ ] `eval`/`new Function`/URL 拼接未编码
- [ ] 第三方脚本无 SRI；用户输入未校验直接渲染
- [ ] 请求路径/参数是否可能被注入（SSRF/路径遍历）

### 3. 依赖健康
- [ ] import 的包**真实存在**吗？（AI 幻觉包名高发——`npm view <包名>` 验证）
- [ ] 版本过旧/过时 API？（componentWillMount、createRef、Vue.extend）
- [ ] 重复功能库；无 tree-shaking；bundle 过大

### 4. 可访问性（WCAG 2.2）
- [ ] img 有 alt 吗？按钮有可见文本/aria-label 吗？
- [ ] 可见文本与 aria-label 一致吗？（SC 2.5.3 名称标签——AI 高频翻车点）
- [ ] 选项卡/手风琴有键盘导航 + ARIA 角色吗？
- [ ] 焦点管理：弹窗关闭后焦点回到触发元素？
- [ ] 颜色对比度、语义标签（div 滥用）

### 5. 性能
- [ ] 大列表虚拟滚动？图片懒加载 + 尺寸？
- [ ] 重渲染：React memo/依赖数组；Vue 计算属性/`v-memo`
- [ ] 请求瀑布流（循环 await）？独立请求并行了吗？
- [ ] bundle 有 code splitting 吗？

### 6. 错误处理
- [ ] fetch/then 有 catch 吗？catch 是空块吞错吗？（⚠️ 扫描对任意 `.then` 无 catch 报 block；非 fetch 的 Promise 场景 agent 可降级为 warn 并在报告注明）
- [ ] 有 loading/empty/error 三态吗？（AI 生成 UI 常见只做 happy path）
- [ ] HTTP 错误状态码有处理吗？

### 7. 状态与竞态
- [ ] 异步请求乱序（快速切换时旧响应覆盖新结果）？有竞态控制吗？
- [ ] 异步回调里用了旧 state/旧 props（stale closure）？
- [ ] 全局 state 滥用？直接修改 props/store 吗？

### 8. 响应式与兼容
- [ ] 固定 px 宽高？无媒体查询？移动端溢出？
- [ ] 过时 API/无 polyfill/浏览器兼容问题？

### 9. 代码质量
- [ ] 魔法数字、`any` 滥用、重复代码、`console.log` 残留、死代码

### 10. 逻辑与业务边界（脚本难覆盖，重点人工查）
- [ ] **金额/折扣/权限/状态机**等关键业务逻辑正确吗？（AI 逻辑问题 +75%，曾有折扣码错误致全站价格归零的 600 万美元事故）
- [ ] 异步时序假设（"先执行完再…"有保证吗？）
- [ ] 业务上下文正确吗？（数据格式/单位/边界值）

---

## 输出验收报告

ALWAYS use this template:

```markdown
# 前端边界验收报告

> 验收对象：<目录/文件> ｜ 日期：<YYYY-MM-DD> ｜ 扫描规则：<规则数> 条

## 📊 总评：<XX>/100（🔴 <n> · 🟡 <m> · ⚪ <k>）｜ 结论：<✅ 通过 / ❌ 不通过>

## 🔴 阻断问题（必须修）
| # | 维度 | 位置 | 问题 | 证据 | 修复代码 |
|---|------|------|------|------|---------|
| 1 | 内存与资源 | src/App.jsx:12 | useEffect 定时器未清理 | `setInterval(...)` 无 cleanup | `useEffect(() => { const t = setInterval(...); return () => clearInterval(t); }, [])` |

## 🟡 警告问题（应修）
| # | 维度 | 位置 | 问题 | 修复建议 |
|---|------|------|------|---------|

## ⚪ 建议问题（可修）
| # | 维度 | 位置 | 问题 | 修复建议 |
|---|------|------|------|---------|

## ✅ 通过项
- <维度/检查项通过情况>

## 📌 修复优先级
1. 先修 🔴（阻断上线）…
```

### 评分规则
```
总分 = 100 − 10×🔴数 − 3×🟡数 − 1×⚪数（下限 0）
结论：🔴=0 且总分 ≥ 60 → ✅ 通过；否则 ❌ 不通过
```

---

## 注意事项

- **findings 只是证据，agent 是最终裁决**：确认真伪（正则误报如"文件有 clearInterval 但与 setInterval 无关"）、校正修复代码、补脚本漏掉的语义问题（尤其维度 10 业务逻辑）。
- findings 超过 ~40 条时 `read_file` 可能截断——先 `python3 -c "import json;d=json.load(open('<out_file>'));print(len(d['findings']))"` 看总数，再按 severity 分块读取。
- 修复代码一律标注「建议修复」，agent 需结合上下文校正（不能照抄 fix_hint）。
- 扫描跳过 `node_modules/dist/.git` 等目录。
- 规则可扩展：编辑 `scripts/rules.json` 增删规则（pattern 为正则，missing 为配套缺失检查），改后跑 `python3 -m pytest scripts/test_scan.py` 确认不回归。
- 单文件快速扫描：`python3 <skill_dir>/scripts/scan.py --file <文件> --tech <tech>`
- 验收粒度：AI 写完一页/一组件就验，别等整个项目写完（问题越早发现修复成本越低）。