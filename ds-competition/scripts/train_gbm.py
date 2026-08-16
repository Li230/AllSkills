#!/usr/bin/env python3
"""竞赛 GBM 训练脚本：OOF 交叉验证 + 测试集预测 + 提交文件 + 特征重要性。

LightGBM 优先；未安装时自动回退 sklearn HistGradientBoosting（本机即用此路径）。
类别特征自动识别（object/category），LGBM 走原生 categorical，HGB 走 from_dtype。
缺失值不填充：树模型原生支持 NaN。

用法:
  python train_gbm.py --train train_with_folds.csv --test test.csv \
      --sample sample_submission.csv --target addicted_label \
      --task binary --folds-col fold --out experiments/run1
  # 无 fold 列时自动按 --task 切折（分类分层、回归普通 KFold）

多分类任务的目标会按排序类别编码为 0..k-1。
"""
import argparse
import json
import os
import time

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, log_loss, roc_auc_score

try:
    import lightgbm as lgb

    USE_LGB = True
except ImportError:
    USE_LGB = False
    from sklearn.ensemble import (
        HistGradientBoostingClassifier,
        HistGradientBoostingRegressor,
    )


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--train", required=True)
    ap.add_argument("--test", required=True)
    ap.add_argument("--sample", required=True, help="sample_submission.csv 模板")
    ap.add_argument("--target", required=True)
    ap.add_argument("--task", choices=["binary", "multiclass", "regression"], required=True)
    ap.add_argument("--id-col", default="id")
    ap.add_argument("--folds-col", help="train 里的折列；缺省自动切折")
    ap.add_argument("--n-folds", type=int, default=5)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--learning-rate", type=float, default=0.05)
    ap.add_argument("--num-leaves", type=int, default=31)
    ap.add_argument("--max-iter", type=int, default=2000, help="LGBM n_estimators / HGB max_iter")
    ap.add_argument("--early-stopping", type=int, default=100)
    ap.add_argument("--nrows", type=int, help="只读前 N 行（冒烟测试用）")
    ap.add_argument("--out", required=True, help="输出目录（自动创建）")
    return ap.parse_args()


def encode_cats(df: pd.DataFrame, cat_cols, ref: dict | None = None) -> pd.DataFrame:
    """类别列统一编码：NaN -> '__NA__'，测试集未知取值归入 '__NA__'。"""
    for c in cat_cols:
        s = df[c].fillna("__NA__")
        if ref is not None:
            s = pd.Categorical(s, categories=ref[c])
            s = s.fillna("__NA__")
        else:
            s = pd.Categorical(s)
            if "__NA__" not in s.categories:
                s = s.add_categories("__NA__")
        df[c] = s
    return df


def load(args) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, np.ndarray, np.ndarray | None, list]:
    train = pd.read_csv(args.train, nrows=args.nrows)
    test = pd.read_csv(args.test)
    sample = pd.read_csv(args.sample)

    y = train[args.target].to_numpy()
    if args.task != "regression":
        y = pd.Categorical(y, categories=np.unique(y)).codes

    train_ids, test_ids = train[args.id_col].copy(), test[args.id_col].copy()
    folds = train[args.folds_col].to_numpy() if args.folds_col else None
    drop = [args.id_col, args.target] + ([args.folds_col] if args.folds_col else [])
    feat_train, feat_test = train.drop(columns=drop), test.drop(columns=[args.id_col])
    cat_cols = feat_train.select_dtypes(
        include=["object", "category", "string"]
    ).columns.tolist()
    encode_cats(feat_train, cat_cols, ref=None)
    ref = {c: list(feat_train[c].cat.categories) for c in cat_cols}
    encode_cats(feat_test, cat_cols, ref=ref)

    missing = [c for c in feat_train.columns if c not in feat_test.columns]
    if missing:
        raise SystemExit(f"test 缺少特征列: {missing}")
    feat_test = feat_test[feat_train.columns]
    return feat_train, feat_test, sample, y, folds, train_ids, test_ids


def make_model(task, args, n_classes):
    common = dict(learning_rate=args.learning_rate, random_state=args.seed)
    if USE_LGB:
        params = dict(
            objective="binary" if task == "binary" else "multiclass" if task == "multiclass" else "regression",
            metric="auc" if task == "binary" else "multi_logloss" if task == "multiclass" else "rmse",
            num_leaves=args.num_leaves,
            n_estimators=args.max_iter,
            early_stopping_rounds=args.early_stopping,
            feature_fraction=0.8,
            bagging_fraction=0.8,
            bagging_freq=1,
            verbosity=-1,
            **common,
        )
        if task == "multiclass":
            params["num_class"] = n_classes
        cls = lgb.LGBMClassifier(**params) if task != "regression" else lgb.LGBMRegressor(**params)
        return cls, params

    params = dict(
        max_iter=args.max_iter,
        early_stopping=True,
        n_iter_no_change=args.early_stopping,
        l2_regularization=1.0,
        categorical_features="from_dtype",
        **common,
    )
    if task == "regression":
        return HistGradientBoostingRegressor(loss="squared_error", **params), params
    return HistGradientBoostingClassifier(loss="log_loss", **params), params


def predict(model, X, task):
    if task == "regression":
        return model.predict(X)
    proba = model.predict_proba(X)
    return proba[:, 1] if task == "binary" else proba


def oof_score(y_true, pred, task):
    if task == "binary":
        return {"auc": roc_auc_score(y_true, pred), "logloss": log_loss(y_true, np.clip(pred, 1e-7, 1 - 1e-7))}
    if task == "multiclass":
        return {"logloss": log_loss(y_true, np.clip(pred, 1e-7, 1 - 1e-7)), "accuracy": accuracy_score(y_true, pred.argmax(1))}
    return {"rmse": float(np.sqrt(np.mean((y_true - pred) ** 2)))}


def main() -> None:
    args = parse_args()
    os.makedirs(args.out, exist_ok=True)
    X, X_test, sample, y, folds, train_ids, test_ids = load(args)
    t0 = time.time()

    if folds is not None:
        n_folds = len(np.unique(folds))
    else:
        from sklearn.model_selection import KFold, StratifiedKFold

        if args.task == "regression":
            splitter = KFold(n_splits=args.n_folds, shuffle=True, random_state=args.seed)
            folds = np.empty(len(X), dtype=int)
            for k, (_, val_idx) in enumerate(splitter.split(X)):
                folds[val_idx] = k
        else:
            splitter = StratifiedKFold(n_splits=args.n_folds, shuffle=True, random_state=args.seed)
            folds = np.empty(len(X), dtype=int)
            for k, (_, val_idx) in enumerate(splitter.split(X, y)):
                folds[val_idx] = k
        n_folds = args.n_folds

    n_classes = len(np.unique(y)) if args.task != "regression" else 0
    pred_dim = n_classes if args.task == "multiclass" else 1
    oof = np.zeros((len(X), pred_dim) if pred_dim > 1 else len(X))
    test_pred = np.zeros((len(X_test), pred_dim) if pred_dim > 1 else len(X_test))
    imp = np.zeros(len(X.columns))
    backend = "lightgbm" if USE_LGB else "histgradientboosting"

    for f in range(n_folds):
        tr_idx, va_idx = np.where(folds != f)[0], np.where(folds == f)[0]
        model, params = make_model(args.task, args, n_classes)
        fit_kwargs = {}
        if USE_LGB:
            fit_kwargs["eval_set"] = [(X.iloc[va_idx], y[va_idx])]
        model.fit(X.iloc[tr_idx], y[tr_idx], **fit_kwargs)

        oof[va_idx] = predict(model, X.iloc[va_idx], args.task)
        test_pred += predict(model, X_test, args.task) / n_folds
        if USE_LGB:
            b = model.booster_
            imp += b.feature_importance(importance_type="gain") / n_folds
        print(f"fold {f}: train={len(tr_idx)} val={len(va_idx)}")

    score = oof_score(y, oof, args.task)
    print(f"OOF {score}  backend={backend}  folds={n_folds}  seed={args.seed}")

    pred_col = sample.columns[1]
    sub = sample[[args.id_col]].copy()
    if args.task == "binary":
        sub[pred_col] = test_ids.map(dict(zip(test_ids, test_pred)))
    elif args.task == "multiclass":
        # 提交列存 argmax 类别（原类别名需按 np.unique 排序映射）
        sub[pred_col] = test_pred.argmax(1)
    else:
        sub[pred_col] = test_ids.map(dict(zip(test_ids, test_pred)))

    if sub[pred_col].isna().any():
        raise SystemExit("提交列存在缺失，检查 test id 与 sample id 是否一致")
    sub.to_csv(os.path.join(args.out, "submission.csv"), index=False)

    if USE_LGB:
        pd.DataFrame({"feature": X.columns, "gain": imp}).sort_values("gain", ascending=False).to_csv(
            os.path.join(args.out, "importances.csv"), index=False
        )
    oof_out = pd.DataFrame({"y_true": y})
    if pred_dim == 1:
        oof_out["pred"] = oof
    else:
        for j in range(pred_dim):
            oof_out[f"p{j}"] = oof[:, j]
    oof_out.to_csv(os.path.join(args.out, "oof.csv"), index=False)
    with open(os.path.join(args.out, "run.json"), "w", encoding="utf-8") as fh:
        json.dump(
            {"args": vars(args), "backend": backend, "oof": score, "seconds": round(time.time() - t0, 1)},
            fh,
            ensure_ascii=False,
            indent=2,
        )
    print(f"输出目录: {args.out}  (submission.csv / oof.csv / run.json{', importances.csv' if USE_LGB else ''})")


if __name__ == "__main__":
    main()
