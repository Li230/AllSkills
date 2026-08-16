# pandas / numpy 高频误区库

用途：讲解到相关语法时**主动预警**；找错练习从这里选题（先语法级，后语义级）。级别只用于练习排序，不是重要性排序。

| 误区 | 错在哪 | 正确做法 | 级别 |
|---|---|---|---|
| 以为 `dropna()` 会改原表 | dropna 默认返回新表，原 df 不变 | `df = df.dropna()`，或显式赋值回原变量 | 语义 |
| 行筛选与列筛选混用 | `df["age"] > 18` 得到的是布尔 Series，不是筛选后的表 | 行筛选要包一层：`df[df["age"] > 18]` | 语义 |
| 用 `and` / `or` 连接两个条件 | Series 不能直接 `and`（Python 会报 ValueError） | 用 `&` / `|`，且每个条件加括号：`(df["a"]>1) & (df["b"]<2)` | 语法 |
| 视图 vs 拷贝（SettingWithCopyWarning） | 链式取列后赋值可能改不到原表，或触发警告 | 用 `.loc` 显式赋值；需要独立数据用 `.copy()` | 语义 |
| 链式赋值 `df[df["a"]>1]["b"]=0` | 可能改的是副本，静默失败 | `df.loc[df["a"]>1, "b"] = 0` | 语义 |
| `value_counts()` 看不到 NaN | 默认 `dropna=True`，缺失值被忽略 | `value_counts(dropna=False)` | 语义 |
| 列名带空格/特殊字符还用 `df.列名` | 点语法只适用于合法标识符，其余直接报错 | 一律用 `df["列名"]` | 语法 |
| `pandas.std()` 和 `numpy.std()` 默认不同 | pandas 默认 ddof=1（样本），numpy 默认 ddof=0（总体） | 需要一致时显式传 `ddof` | 语义 |
| 数值列带逗号/单位被读成 object 还直接算 | pandas 无法自动转数值 | `pd.to_numeric(s, errors="coerce")`，并检查被转成 NaN 的数量 | 语法 |
| 以为必须用 `inplace=True` | 现代 pandas 不推荐 inplace，容易忘赋回 | 直接赋值回原变量更清晰 | 语义 |
