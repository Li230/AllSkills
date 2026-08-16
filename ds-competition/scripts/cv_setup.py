#!/usr/bin/env python3
"""生成交叉验证折（无泄漏），给训练集加 fold 列。

模式:
  stratified  分类任务，保持标签比例（默认）
  kfold       回归任务
  time        时间序列 TimeSeriesSplit，需 --time-col（会按时间列排序后切折）
  group       分组 GroupKFold，需 --group-col（同一组不会同时出现在训练/验证）

用法:
  python cv_setup.py --train train.csv --target addicted_label \
      --mode stratified --n-folds 5 --seed 42 --out train_with_folds.csv
"""
import argparse

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold, KFold, StratifiedKFold, TimeSeriesSplit


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--train", required=True, help="训练集 CSV 路径")
    ap.add_argument("--target", help="目标列名（打印每折标签比例用）")
    ap.add_argument(
        "--mode", choices=["stratified", "kfold", "time", "group"], default="stratified"
    )
    ap.add_argument("--time-col", help="时间列（mode=time 用）")
    ap.add_argument("--group-col", help="分组列（mode=group 用）")
    ap.add_argument("--n-folds", type=int, default=5)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", required=True, help="输出 CSV（train + fold 列）")
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    df = pd.read_csv(args.train)
    if "fold" in df.columns:
        print(f"[warn] 输入已含 fold 列，将覆盖（原 {df['fold'].nunique()} 折）")
        df = df.drop(columns=["fold"])

    y = df[args.target] if args.target else None
    folds = np.empty(len(df), dtype=int)

    if args.mode == "stratified":
        if y is None:
            raise SystemExit("--mode stratified 需要 --target")
        splitter = StratifiedKFold(
            n_splits=args.n_folds, shuffle=True, random_state=args.seed
        )
        for k, (_, val_idx) in enumerate(splitter.split(df.index, y)):
            folds[val_idx] = k
    elif args.mode == "kfold":
        splitter = KFold(n_splits=args.n_folds, shuffle=True, random_state=args.seed)
        for k, (_, val_idx) in enumerate(splitter.split(df.index)):
            folds[val_idx] = k
    elif args.mode == "time":
        if not args.time_col:
            raise SystemExit("--mode time 需要 --time-col")
        df = df.sort_values(args.time_col).reset_index(drop=True)
        folds = np.empty(len(df), dtype=int)
        for k, (_, val_idx) in enumerate(TimeSeriesSplit(n_splits=args.n_folds).split(df)):
            folds[val_idx] = k
    else:  # group
        if not args.group_col:
            raise SystemExit("--mode group 需要 --group-col")
        splitter = GroupKFold(n_splits=args.n_folds)
        for k, (_, val_idx) in enumerate(
            splitter.split(df.index, y, groups=df[args.group_col])
        ):
            folds[val_idx] = k

    df["fold"] = folds
    df.to_csv(args.out, index=False)

    print(f"折数: {args.n_folds}  模式: {args.mode}  seed: {args.seed}")
    print(df.groupby("fold").size().to_string())
    if y is not None and args.mode in ("stratified", "kfold"):
        print("每折目标均值(标签率):")
        print(df.groupby("fold")[args.target].mean().round(4).to_string())
        print(f"总体均值: {y.mean():.4f}")


if __name__ == "__main__":
    main()
