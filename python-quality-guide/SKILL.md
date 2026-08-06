---
name: python-quality-guide
description: Python 高质量编程方法论（软约束）。当任务涉及编写/修改 .py 文件时使用——引导 agent 遵循 PEP8、类型注解、SOLID、可测试性等最佳实践。触发词："写 Python"、"Python 代码规范"、"高质量 Python"、"python-quality-guide"。
---

# Python Quality Guide — Python 高质量编程规范

写 Python 代码前的"软约束"方法论。配合硬闸门 `python-quality-gate`（flake8/black/pytest 检查）使用：**本 skill 教你怎么写好，gate 强制你写好**。

## 何时使用

- 任何新增/修改 `.py` 文件的任务
- 代码审查前自查
- 不确定怎么写更 Pythonic 时

## 核心原则（按重要性排序）

### 1. 可读性优先（代码是写给人看的）
- 命名达意：变量/函数/类名说清楚"是什么/做什么"
  - ✅ `total_pages`, `fetch_report()`, `DustSite`
  - ❌ `tp`, `get_stuff()`, `ds`
- 函数保持短小（一般 < 30 行），长了就拆
- 注释解释"为什么"，不解释"是什么"（代码本身应自解释）

### 2. 类型注解（可维护性的基石）
- 所有**公开函数**必须有参数和返回类型注解
- 使用 `typing` 模块：`Optional`, `List`, `Dict`, `Any`（万不得已才用 Any）
- 配合 mypy 可做静态检查

```python
def parse_table(tid: str, rows: list[list[str]]) -> dict[str, str]:
    """解析表格数据。"""
    ...
```

### 3. 可测试性（写代码时想着测试）
- 优先纯函数：同样输入 → 同样输出，无副作用
- 减少全局状态依赖
- 一个函数一个职责（单一职责原则）
- 依赖注入而非硬编码全局（依赖倒置）

### 4. PEP8 风格（硬闸门 flake8 会查）
- 缩进 4 空格，行长 ≤ 88（black 默认）
- 命名：`snake_case`（函数/变量）、`PascalCase`（类）、`UPPER_CASE`（常量）
- 导入顺序：标准库 → 第三方 → 本地（每组分隔）
- 两个空行分隔顶层定义，一个空行分隔方法

### 5. 异常处理（不吞异常）
- 捕获具体异常类型，不裸 `except:`
- 不静默吞异常（至少 log）
- 自定义异常继承 `Exception`
- 用 `raise ... from e` 保留上下文

```python
# ✅
try:
    data = json.loads(text)
except json.JSONDecodeError as e:
    raise ValueError(f"JSON 解析失败: {text[:50]}") from e
```

### 6. 现代 Python 习惯（3.10+）
- f-string 优先：`f"{name}: {value}"`（不用 % 或 .format）
- 路径用 `pathlib.Path`（不用 os.path 拼字符串）
- 文件读写用 `with` 上下文管理器
- 类型用内置泛型：`list[str]` 而非 `List[str]`（3.9+）

### 7. 不过度设计
- YAGNI：不需要的功能不提前做
- DRY：重复即重构，但不要为了消除重复引入过度抽象
- 简单 > 巧妙（Clarity over cleverness）

## 反模式清单（Red Flags）

| 反模式 | 问题 | 应该 |
|---|---|---|
| `except: pass` | 吞掉所有错误 | 捕获具体类型 + 日志 |
| 函数超长（>50 行） | 难读难测 | 拆成小函数 |
| 魔法数字/字符串 | 不可维护 | 定义常量/枚举 |
| 可变默认参数 `def f(x=[])` | 共享状态 bug | 用 `None` + 内部创建 |
| 手写字符串拼路径 | Windows/特殊字符问题 | `pathlib.Path` |
| 无类型注解的公开 API | 调用方无提示 | 补注解 |
| 复制粘贴代码 | 修一处漏三处 | 抽公共函数 |

## 完成标准（软约束自检清单）

- [ ] 命名达意、函数短小
- [ ] 公开函数有类型注解
- [ ] 逻辑可测试（纯函数优先）
- [ ] 无裸 except、无静默吞异常
- [ ] 用 f-string / pathlib / with
- [ ] 无魔法数字
- [ ] 无重复代码
- [ ] **已跑硬闸门**：`python-quality-gate`（flake8 + black + pytest 全绿）

## 下一步

写完代码 → 运行硬闸门：
```bash
python3 skills/python-quality-gate/scripts/gate.py --target <目录或文件>
```
全绿后才能宣称任务完成。
