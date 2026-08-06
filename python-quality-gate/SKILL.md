---
name: python-quality-gate
description: Python 代码质量硬闸门（硬约束）。Python 任务完成前必须运行——自动执行 flake8（规范）+ black --check（格式）+ pytest（测试），三项全绿才允许宣称任务完成/打勾 tasks.md。触发词："跑闸门"、"质量检查"、"python-quality-gate"、"Python 任务完成前检查"。
---

# Python Quality Gate — Python 代码质量硬闸门

Python 任务完成前的**强制检查闸门**。配合软约束 `python-quality-guide` 使用。

## 何时使用

- 任何涉及 `.py` 文件的任务，**宣称完成前必跑**
- tasks.md 打勾 `[x]` 前
- 提交/合并前

## 运行方式

```bash
python3 skills/python-quality-gate/scripts/gate.py --target <目录或文件>
```

- `--target`：要检查的目录或 .py 文件（默认当前目录）
- `--skip-tests`：跳过 pytest（当任务不涉及逻辑时）
- 返回码：**0 = 全绿通过**，**1 = 有失败项**

## 检查项

| 检查 | 工具 | 不通过的含义 |
|---|---|---|
| 规范 | `flake8` | 有 PEP8 违规（行长/未用导入/裸 except 等） |
| 格式 | `black --check` | 格式不符合 black 标准 |
| 测试 | `pytest` | 有测试失败（仅当存在 test 文件时） |

## 判定规则

- 三项全 PASS → 允许打勾 ✅
- 任一 FAIL → **禁止宣称完成**，先修复再重跑

## 反模式（Red Flags）

- ❌ "格式小事，先提交" → 黑闸门必须过
- ❌ "测试以后再补" → 有逻辑就有测试
- ❌ 改 gate 脚本放水 → gate 是底线，改它=承认质量不重要
- ❌ 跳过 --skip-tests 而不说明理由

## 输出示例

```
=== Python Quality Gate ===
[1/3] flake8 ........... PASS (0 errors)
[2/3] black --check ... PASS (0 files would be reformatted)
[3/3] pytest .......... PASS (12 passed)
=== RESULT: ✅ ALL GREEN (0.8s) ===
```

## 注意事项

- 工具位置：pytest/black/flake8 在 venv 中，脚本自动用 `sys.executable -m` 调用，保证环境一致
- 大目录检查慢：可用 `--target 具体文件` 缩小范围
