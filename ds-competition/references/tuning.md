# 超参调优参考（Optuna）

目录：
1. 原则
2. LightGBM 参数空间
3. XGBoost / CatBoost 参数空间
4. 与固定折的集成

## 1. 原则

- 用与最终评估**完全相同**的折（`cv_setup.py` 生成的 fold 列）做调参目标函数；不要在调参时换切分。
- 每次 trial 内用早期停止控制迭代数，只调结构参数（学习率、叶子数、正则等）。
- 先粗后细：先 30~50 trial 找方向，再固定大方向微调。
- 调参前后对比必须同 seed、同特征集，否则不可比。
- 不要在 LB 上调参；LB 只做最终抽查。

## 2. LightGBM 参数空间

```python
import optuna


def lgbm_params(trial):
    return {
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.1, log=True),
        "num_leaves": trial.suggest_int("num_leaves", 15, 127, log=True),
        "min_child_samples": trial.suggest_int("min_child_samples", 10, 100, log=True),
        "feature_fraction": trial.suggest_float("feature_fraction", 0.5, 0.95),
        "bagging_fraction": trial.suggest_float("bagging_fraction", 0.5, 0.95),
        "bagging_freq": 1,
        "lambda_l1": trial.suggest_float("lambda_l1", 1e-3, 10, log=True),
        "lambda_l2": trial.suggest_float("lambda_l2", 1e-3, 10, log=True),
    }
```

- 迭代数交给早期停止（n_estimators 设大值，如 5000）。
- 数据量大或特征多时优先调 feature_fraction、min_child_samples；过拟合明显时先加正则。

## 3. XGBoost / CatBoost 参数空间

XGBoost：

```python
def xgb_params(trial):
    return {
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.1, log=True),
        "max_depth": trial.suggest_int("max_depth", 3, 9),
        "min_child_weight": trial.suggest_int("min_child_weight", 1, 50),
        "subsample": trial.suggest_float("subsample", 0.5, 0.95),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 0.95),
        "reg_alpha": trial.suggest_float("reg_alpha", 1e-3, 10, log=True),
        "reg_lambda": trial.suggest_float("reg_lambda", 1e-3, 10, log=True),
    }
```

CatBoost：`depth`（4~8）、`l2_leaf_reg`（1~10，log）、`random_strength`（1~10）、`bagging_temperature`（0~1）；类别特征直接传列名，原生处理高基数类别。

## 4. 与固定折的集成

```python
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score


df = pd.read_csv("train_with_folds.csv")  # 来自 cv_setup.py


def objective(trial):
    oof = np.zeros(len(df))
    for f in range(5):
        tr, va = df[df["fold"] != f], df[df["fold"] == f]
        model = lgb.LGBMClassifier(**lgbm_params(trial), n_estimators=5000, random_state=42)
        model.fit(
            tr[FEATURES], tr[TARGET],
            eval_set=[(va[FEATURES], va[TARGET])],
            callbacks=[lgb.early_stopping(100, verbose=False)],
        )
        oof[va.index] = model.predict_proba(va[FEATURES])[:, 1]
    return roc_auc_score(df[TARGET], oof)


study = optuna.create_study(direction="maximize")
study.optimize(objective, n_trials=50, show_progress_bar=True)
print(study.best_params, study.best_value)
```

- 每折都要独立训练，禁止把 fold 混进单次拟合（泄漏）。
- 最终模型用最优参数 + 全量数据训练并预测测试集；也可保留每折模型对测试预测取平均（更稳）。
- 调参结果只有让固定折的 OOF 提升才算数；提升 < 0.0005 时可视为噪声，别为微小提升引入复杂度。
