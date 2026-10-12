# 01 白龙马产品拆解（Bailongma / 小鱼AI）

> 一手来源：github.com/xiaoyuanda666-ship-it/BaiLongma README（2026-09-12 拉取，11.3KB）；
> 官网 bailongma.top；产品视频截图（抖音"鱼老板讲私域"，2026-09-12，三张）。
> 局限声明：未读其源码，以下为官方文档与影像层面的拆解。

## 产品一句话

跑在用户电脑上的桌面常驻智能体：主循环驱动，有消息优先处理，空闲按节奏自主干活，
状态实时推送到 Brain UI。

## 能力地图（来自官方 README：主要能力节 + 常用 API 表 + 运行方式节）

| 能力域 | 内容 | agent-explore 对应模型 |
|---|---|---|
| 主循环 | 用户消息/后台消息/提醒/任务续跑/空闲心跳 五类驱动源 | 模型1 主循环优先 |
| 记忆系统 | SQLite 持久化对话/记忆/行动日志/提醒/线程状态 + 全文检索、语义补充、去重合并 | 模型3 上下文编排 |
| 动态上下文注入 | 每轮前自动选：相关记忆/最近对话/用户画像/工具结果/UI 信号/预取内容/运行状态 | 模型3 |
| 工具系统 | 按需注入：通信/文件系统/Shell/网页读取/搜索/媒体/记忆管理/UI 卡片/任务/提醒/本地 Agent 委托/系统操作 | 模型4 能力即技能书 |
| Brain UI | 聊天/思考流/记忆图/焦点线程/热点面板/文档面板/语音控制/ACUI 卡片渲染 + `/turn-trace` 回合轨迹 | 模型5 状态外显 |
| 心跳配置 | `/settings/heartbeat` 读写心跳开关与默认间隔 | 模型2 心跳即存在 |
| 安全 | 敏感设置默认仅本机、局域网配对口令（URL fragment 传递后即移除）、沙箱工作区、单实例 | 模型6 有界自主 |
| 本地资源感知 | 启动收集系统/桌面/已装软件/本地 Agent/SSH/Git/地理天气/热点 | 模型3（预取内容） |

## 视频影像佐证的交互方向

- **认知界面（Cognitive Surface）**：左侧"用户消息处理器"（消息计数、Constraint/Memory/Knowledge
  计数、SEEN MESSAGE RECEIVED、capability_demo 卡片、工具调用链接），中部对话流，右侧
  "自主行为机制 Tick"跑马灯（HEARTBEAT TICK 与"思考完成"交替滚动、精确到秒）。
- **实时热点地图平台**：3D 地球 + 热榜矩阵（微博/抖音/知乎等 + AI 技术审阅 87%），是"空闲时
  自主干活"的产出外显——心跳的产物被产品化为独立面板。
- **自我介绍即能力清单**：小鱼AI 自述"五大核心能力：网络搜索、文件读写、命令执行、桌面交互、
  本地记忆"——产品把能力边界写进人格开场白（与技能书 description 触发词同构）。

## 工程结构参考

Electron 壳 + 本地 HTTP（:3721）+ LLM 调用层（llm.js 流式/工具调用/重试保护）+ SQLite +
memory/（识别/注入/线程/焦点/召回/整理）+ capabilities/（工具 schema/执行器/沙箱/工具市场）+
social/（Discord/微信桥接，外部消息进同一主循环按渠道路由）。

## 值得抄的产品决策

1. 心跳做成**可配置产品参数**（开关+间隔），不是隐藏的系统行为。
2. 回合轨迹（turn-trace）做成一等页面——排查与信任共用同一出口。
3. 外部渠道消息进同一主循环——多入口单循环，不在渠道层分叉逻辑。

## 官网哲学与源码证据（v2 联网轮3 增补，2026-09-12）

官网 bailongma.top（快照摘要）官方命名与措辞：

- 定位 "LOCAL INTELLIGENCE SYSTEM"，界面哲学 **"让每一次思考，都清晰可见"**（Live Cognition：
  记忆/对话/心跳/行动日志合于一个认知界面）→ 模型5 的官方表述。
- **CONSCIOUS HEARTBEAT "让意识，持续在线"**，语义三段：**TICK 周期唤醒**（不依赖用户消息触发）→
  **REFLECT 主动思考**（检查环境与未竟任务）→ **CONTINUE 延续行动**（把计划推进到下一步）→
  模型2 的官方语义，比 README 更进一步：心跳不只是"活着"，是"意识循环"。
- **"可见且可控"（SIGNAL / OBSERVABLE）**："将运行状态转化为清晰信号，始终保有观察和调整的能力"
  → 模型6 可控侧的官方表述。
- MONITOR 面板官方描述"热点主动浮现"——空闲自主产出获得一级界面（影像佐证的产品化结论获官方确认）。
- 语音定位"把指令送入同一条智能体运行流"→ 决策 D5 单循环归一的又一官方佐证。

源码证据（GitHub src/，只读 config 与测试清单，未通读主循环）：

- **心跳默认 20 分钟**：`src/config.js:1017` `tickInterval: 20 * 60 * 1000 // default idle heartbeat: 20 minutes`；
  `getHeartbeatConfig/setHeartbeatConfig`（:1472-1502）证实开关+间隔为可配置状态（README API 表互证）。
- **测试文件清单即设计先例**：`test-heartbeat-output-contract.js`（心跳输出契约——心跳必须产出什么）、
  `test-heartbeat-delivery-instructions.js`（心跳投递指令）、`test-tick-policy.js`（tick 策略）、
  `test-consciousness-loop.js`（意识循环）、`test-noise-eviction.js`（**噪音驱逐**——打扰感治理的工程化）、
  `test-action-contract.js`（73KB 行动契约）、`test-self-evolution.js`（自我进化）、
  `typhoon-alert-monitor.js` + `test-typhoon-alert-monitor.js`（主动监控真实实例）、
  `awakening.js`（8KB 唤醒模块）、`hotspots.js`（20KB 热点）、`ticker.js`。
  → 启示：心跳/自主行为在白龙马内部是**契约化**的（输出契约+投递契约+策略+驱逐），不是裸循环。
