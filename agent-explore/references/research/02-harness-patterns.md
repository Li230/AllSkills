# 02 本项目 harness 模式（ask-harness / dsh 宿主）

> 一手来源：`ask-harness/README.md`（01–09 编号文档）、`apps/qa/agent/harness/`、
> `apps/qa/shared/harness/`、`apps/qa/agent/skills/`、
> `openspec/changes/archive/`（harness-* 七件套、scenario-a-d、qa-agent-orchestration 等真归档）
> + git 提交锚点（d8e0fb3/a225f79/d6f94bf/4deaf3c，见正文）。
> 检索时间：2026-09-12。

## 演进主线

从"6199 行 Python 瀑布（qwen 做槽位填空）"重构为"dsh（DeepSeek Harness）宿主 + MCP 工具 +
技能库"的真智能体。浏览器 SSE → FastAPI :8282（AGENT_ENGINE_ENABLED=1）→ dsh 宿主 :8712
（Node 子进程）→ 4 个 MCP 工具包（:8761/8762/8763/8765）+ 技能库 `apps/qa/agent/skills/*.md`。

## 可复用的 harness 设计模式（与白龙马能力地图同构对照）

| 模式 | 本项目实现 | 白龙马对照 | agent-explore 模型 |
|---|---|---|---|
| 宿主接缝层 | `harness/runtime.py`：子进程生命周期/会话映射/回合预算 | Electron + index.js 主循环 | 模型1 |
| 事件总线 | `shared/harness/events.py` 九事件（AI 问数） | SSE `/events` 事件流 | 模型5 |
| 思考流持久化 | events.jsonl 跨重启回放（git 提交 d8e0fb3；orchestrator/task_events.py） | 思考流面板 + `/turn-trace` | 模型5 |
| 超时/重试 guard | `shared/harness/guard.py` | llm.js"重试保护" | 模型6 |
| 上下文留存 | `harness/retention.py` | 动态上下文注入七类素材 | 模型3 |
| 技能库 | `apps/qa/agent/skills/*.md` 14 本技能书（15 个 md，MIGRATION.md 无 frontmatter 不计），frontmatter 触发词路由 | 工具按需注入 + 能力清单 | 模型4 |
| 澄清门 | skills/grill-me.md：五类 MUST 澄清（口径双关/同名实体/半径超上限/数据期外/主体缺位） | ——（白龙马未见显式澄清门） | 模型6 |
| 红线归代码 | git 提交 4deaf3c：执行阶段思考全程可见，红线归代码 | 沙箱/配对口令/仅本机 | 模型6 |

## 三层验收体系（设计探针的对齐目标）

1. 单测/集成闸门：`make gate`（711 通过）
2. 探针（harness 内部面）：`apps/qa/scripts/agent_probe.py` 14 条真模型回合
   （handshake/clarify/think-strip 等）
3. 浏览器真机 case：`apps/qa/scripts/browser_proof_grid_qa.py` 11 个（flow-eval/pool-eval/
   sticky-multiturn/token-stream 等，产物落 tmp_shots/）

另有业务编排场景 A–D（`apps/qa/scripts/run_scenario_{a,b,c,d}.py`）作为端到端样例。

## 技能书格式约定（本项目的"技能书宪法"）

- frontmatter 两字段：`name`（qa- 前缀）+ `description`（触发条件内嵌）
- 正文结构：何时触发 → 步骤 → 红线（MUST/MUST NOT 显式）
- 双向一致性契约（git 提交 a225f79；tests/test_skill_tool_alignment.py）：技能书声称的能力必须对应真实工具，工具能力必须被
  技能书覆盖——防技能库腐烂

## 对设计的约束（在本项目做 harness 设计时的硬边界）

- 回合预算与 guard 参数归宿主，技能书/模型层不得绕过
- 任何新的自主行为须同时给出：事件序列（九事件语义内）+ 外显出口 + 探针脚本
- 技能书新增须过一致性契约，域外技能不得入 `apps/qa/agent/skills/`
