# 06 时间线与参照系

> 一手来源：白龙马 README/影像（2026-09-12 检索）× 本项目 `openspec/changes/archive/` 目录
> （2026-09-12 列举）。

## 白龙马 / 小鱼AI 侧

- 2026-07-01：项目诞生（自述"7月1日诞生的，活了11天，还在长"；影像时版本 2.1.512）。
- 2026-09 上旬：产品影像显示已具备——认知界面（用户消息处理器/Tick 跑马灯/对话流）、
  实时热点地图平台（热榜聚合 + AI 技术审阅）、Brain UI 多面板、语音、局域网移动访问。
- 开源：github.com/xiaoyuanda666-ship-it/BaiLongma；官网 bailongma.top（搜索确认）；
  影像字幕另见 bailongma.ai 字样（未独立核实，以 .top 为准）。

## 本项目 harness 侧（openspec 归档变更 + git 提交序列，2026-09）

| 日期 | 归档变更 / git 提交 | 能力演进 |
|---|---|---|
| 2026-09-09 | qa-agent-orchestration | 编排基座 |
| 2026-09-12 | harness-p1-hardening / caliber-fixes / d10fix / deblock / debt / hostspawn / toolface | dsh 宿主七件套硬化 |
| 2026-09-12 | scenario-a/b/c/d-* | 业务编排场景 A–D 端到端 |
| 2026-09-12 | git d8e0fb3（task-events-persist） | 思考流持久化（events.jsonl 跨重启回放） |
| 2026-09-12 | git a225f79（skill-tool-alignment） | 技能-工具双向一致性契约 |
| 2026-09-12 | git d6f94bf（skill-pill） | 编排报告页技能加载可观测 |
| 2026-09-12 | git 4deaf3c（agentic-mode） | 执行阶段模型查证模式（思考全程可见，红线归代码） |
| 2026-09-12 | session-history-archive / snapshot-fidelity / trace-* / map-linkage | 会话与轨迹族 |

## 对照读法（时间线揭示的方向差）

- 白龙马 11 天长出"常驻 + 心跳 + 自主产出面板"；本项目同期把"单回合问答"做深
  （预算/guard/澄清/探针/一致性契约）。两者是同一图谱的两轴：**常驻自主度** × **单回合可信度**。
- agent-explore 的定位：让本项目在保持单回合可信度优势的前提下，设计常驻自主能力时
  有现成的决策先例库与产出物模板——不必从聊天程序范式重新摸索。
