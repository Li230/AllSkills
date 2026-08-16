# 主题地图（渐进生长）

用途：判断"这个概念依赖什么、学习者缺什么"。**不是教学大纲**——不按顺序硬教，只在用户遇到时按需讲解。每教一个新概念，把节点补进对应分区。

节点格式：`概念 | 一句话 | 前置依赖 | Python 锚点`

## pandas 基础

| 概念 | 一句话 | 前置依赖 | Python 锚点 |
|---|---|---|---|
| `read_csv` | 把 CSV 文件读成一张表（df） | 无 | `open()` 读文件 |
| df 是什么 | 一张有行有列的表格；列叫 Series | read_csv | 二维列表的"升级版" |
| `shape` / `columns` / `dtypes` / `head` | 看表的行数、列名、每列类型、前几行 | df 概念 | `len()`、`type()` |
| `df[列名]` | 取出表格的一列（Series） | df 概念 | 字典 `d[key]` |
| `df[[列1, 列2]]` | 同时取多列，返回小表 | `df[列名]` | 用列表当 key |
| 布尔筛选 `df[df[列] > x]` | 按条件挑出满足的行 | `df[列名]` | `if` 条件 + 列表推导 |
| `value_counts()` | 数每种值各出现多少次，降序 | df 概念 | 字典计数 + `sorted` |
| `isna()` / `sum()` | 标记空值 / 数空值个数 | df 概念 | `True` 当 1 加 |
| `mean()` / `describe()` | 均值 / 整体统计 | df 概念 | `sum(x)/len(x)` |
| `dropna()` | 丢掉含空值的行（返回新表，不改原表） | `isna()` | 列表 `remove`、字符串 `replace` |
| `fillna(v)` | 把空值填成 v | `isna()` | 字典 `get` 默认值 |
| `astype(类型)` | 转换列的类型 | df 概念 | `int(x)` / `str(x)` |
| `str.strip().lower()` | 去掉空格、统一小写（修类别不一致） | 取列 | 字符串方法 |
| `duplicated()` / `drop_duplicates()` | 找重复行 / 删重复行 | df 概念 | 集合去重 |

## numpy 基础

| 概念 | 一句话 | 前置依赖 | Python 锚点 |
|---|---|---|---|
| `np.array` | 把列表变成数组，能整体运算 | 无 | 列表 |
| `shape` / 索引 `a[i]` | 数组的形状 / 取元素 | np.array | `len()`、列表 `a[i]` |
| 切片 `a[1:3]` | 取一段元素 | np.array | 列表切片 |
| 向量化运算 `a + 1` | 不用 for 循环，一次算整列 | np.array | for 循环做同样的事做对比 |
| `np.where(条件, a, b)` | 按条件选 a 或 b | 向量化 | `if/else` |
| 广播（遇到再补） | 不同形状数组自动对齐运算 | 向量化 | - |

## sklearn 建模

| 概念 | 一句话 | 前置依赖 | Python 锚点 |
|---|---|---|---|
| `train_test_split` | 把数据切成训练/验证两份，防止偷看答案 | 布尔筛选 | 函数参数、多返回值 |
| X 和 y | X=特征表，y=答案列，模型用 X 学 y | df 概念 | 函数参数 |
| `fit(X, y)` | 让模型"学习"数据 | X/y 概念 | 对象的方法（OOP） |
| `predict(X)` | 用学好的模型对新数据预测 | fit | 方法调用 |
| `accuracy_score` / `confusion_matrix` | 预测得准不准 / 错在哪些类 | predict | 函数返回值 |
| `roc_auc_score` | 概率类指标（不平衡时用） | predict | - |
| `cross_val_score` | 切几份轮流训练验证，看稳定性 | fit/predict | for 循环 |

## 待补节点（遇到再补）

（这里留空；每教一个新概念，把节点从"待补"移进上面的分区）
