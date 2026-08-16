#!/usr/bin/env python3
"""计算竞赛常用指标（分类/回归）。

用法:
  python metrics.py --csv oof.csv --true-col y_true --pred-col pred --metric auc
  python metrics.py --csv oof.csv --true-col y_true --pred-col p0,p1,p2 --metric logloss

--metric:
  auc        二分类 ROC-AUC（pred 为概率）
  logloss    对数损失（多分类时 --pred-col 传逗号分隔的概率列，如 p0,p1,p2）
  accuracy   准确率（pred 为概率时自动 argmax/四舍五入）
  rmse/mae   回归
  qwk        序数多分类二次加权 Kappa（pred 为概率时自动 argmax）
"""
import argparse
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    cohen_kappa_score,
    log_loss,
    mean_absolute_error,
    mean_squared_error,
    roc_auc_score,
)


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--csv", required=True)
    ap.add_argument("--true-col", required=True)
    ap.add_argument("--pred-col", required=True, help="单列或逗号分隔的多列（概率矩阵）")
    ap.add_argument(
        "--metric",
        choices=["auc", "logloss", "accuracy", "rmse", "mae", "qwk"],
        required=True,
    )
    args = ap.parse_args()

    df = pd.read_csv(args.csv)
    y_true = df[args.true_col].to_numpy()
    cols = [c.strip() for c in args.pred_col.split(",")]
    pred = df[cols].to_numpy() if len(cols) > 1 else df[cols[0]].to_numpy()
    pred_finite = np.all(np.isfinite(pred), axis=1) if pred.ndim > 1 else np.isfinite(pred)
    mask = np.isfinite(y_true) & pred_finite
    if not mask.all():
        print(f"[warn] 丢弃含 NaN 的行: {len(mask) - int(mask.sum())}", file=sys.stderr)
        y_true, pred = y_true[mask], pred[mask]

    if pred.ndim > 1:
        classes = pred.argmax(axis=1)
        proba = pred
    else:
        classes = np.round(pred).astype(int)
        proba = np.clip(pred, 1e-7, 1 - 1e-7)

    if args.metric == "auc":
        score = roc_auc_score(y_true, pred)
    elif args.metric == "logloss":
        score = log_loss(y_true, proba)
    elif args.metric == "accuracy":
        score = accuracy_score(y_true, classes)
    elif args.metric == "rmse":
        score = float(np.sqrt(mean_squared_error(y_true, pred)))
    elif args.metric == "mae":
        score = mean_absolute_error(y_true, pred)
    else:  # qwk
        score = cohen_kappa_score(y_true, classes, weights="quadratic")

    print(f"{args.metric}: {score:.6f}")


if __name__ == "__main__":
    main()
