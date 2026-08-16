# 集成（Ensembling）参考

目录：
1. 何时做集成
2. 平均 / 加权 / 排名平均
3. 种子袋装
4. Stacking
5. 防坑

## 1. 何时做集成

当多个模型 OOF 指标接近且预测相关性不高时，集成通常比单独调参收益大。前提：
- 已有 2+ 个合格的基线（不同算法：LightGBM/XGBoost/CatBoost；或不同特征集）；
- 模型间 OOF 预测相关系数 < 0.95（用 `np.corrcoef` 检查两两相关）；
- 每个成员都已在固定折上验证过，不要为了集成引入未经验证的弱模型。

## 2. 平均 / 加权 / 排名平均

先收集每个模型的 OOF 与测试预测，再选权重：

```python
import numpy as np
from scipy.stats import rankdata

# 概率平均（二分类常用；相关模型多时比算术平均更稳）
blend = np.sqrt(np.mean(np.array([p1, p2, p3]) ** 2, axis=0))

# 排名平均：把每个模型的预测转成排名再平均（对量纲/分布敏感度低）
rank_blend = np.mean([rankdata(p) for p in [p1, p2, p3]], axis=0)

# 按 OOF 指标加权（指标越高权重越大，如 w = oof_score）
w = np.array([0.943, 0.941, 0.938])
weighted = (w[:, None] * np.array([p1, p2, p3])).sum(axis=0) / w.sum()
```

权重只用 **OOF** 定；绝不用 LB 反复调权重。

## 3. 种子袋装（Seed Bagging）

同一模型、同一特征，换 3~5 个 `random_state`，对测试预测取平均：
- 稳定单模型预测，降低方差，通常 LB 稳定小幅提升；
- 与算法集成正交，可叠加。

## 4. Stacking

用各模型的 **OOF 预测**做第二层特征：

```python
# 第一层：5 折内每折产出 val 折 OOF + 测试预测（train_gbm.py 即此结构）
# 第二层：LogisticRegression / Ridge 用 OOF 特征训练，预测测试特征
from sklearn.linear_model import LogisticRegression

meta = LogisticRegression(C=1.0)
meta.fit(oof_feats, y)
final = meta.predict_proba(test_feats)[:, 1]
```

- 第二层必须用第一层的 OOF（不是测试预测）训练，否则泄漏；
- 第二层模型越简单越好（LR/Ridge）；复杂 meta 需要再包一层 CV；
- Stacking 数据量小（<5k）时容易过拟合，优先简单平均。

## 5. 防坑

- 用 LB 调集成权重 → 过拟合 LB。
- 成员高度相关还集成 → 收益趋零，反而增加复杂度。
- 测试预测没对齐 id 就平均 → 结果全错；平均前按 id 排序并校验长度。
- Stacking 把测试预测当训练特征 → 泄漏。
- 为了"看起来专业"集成未经验证的模型 → OOF 下降，撤掉。
