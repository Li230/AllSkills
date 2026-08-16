#!/usr/bin/env python3
"""校验并生成提交文件。

用法:
  python make_submission.py --sample sample_submission.csv \
      --pred test_preds.csv --out submission.csv
  # --pred 需含 id 列 + 预测列（列名默认取 sample 第二列，可用 --pred-col 指定）

检查:
  - 预测 id 集合与 sample 完全一致（缺失/多余都报错）
  - 按 sample 的 id 顺序重排输出
  - 概率类指标可加 --check-bounds 检查越界
"""
import argparse
import sys

import numpy as np
import pandas as pd


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--sample", required=True)
    ap.add_argument("--pred", required=True)
    ap.add_argument("--id-col", default="id")
    ap.add_argument("--pred-col", help="默认取 sample 第二列列名")
    ap.add_argument("--out", required=True)
    ap.add_argument("--check-bounds", action="store_true", help="检查预测值是否在 [0,1]")
    args = ap.parse_args()

    sample = pd.read_csv(args.sample)
    pred = pd.read_csv(args.pred)
    pred_col = args.pred_col or sample.columns[1]
    if pred_col not in pred.columns:
        raise SystemExit(f"--pred 缺少预测列 {pred_col!r}，实际列: {list(pred.columns)}")
    if args.id_col not in pred.columns:
        raise SystemExit(f"--pred 缺少 id 列 {args.id_col!r}，实际列: {list(pred.columns)}")

    p = pred[[args.id_col, pred_col]].drop_duplicates(args.id_col)
    if len(p) != len(pred):
        print("[warn] --pred 存在重复 id，已去重", file=sys.stderr)
    if len(p) != len(sample):
        raise SystemExit(f"id 数量不一致: pred={len(p)} sample={len(sample)}")

    missing = set(sample[args.id_col]) - set(p[args.id_col])
    extra = set(p[args.id_col]) - set(sample[args.id_col])
    if missing:
        raise SystemExit(f"sample 有但 pred 缺失的 id 数: {len(missing)}，示例: {sorted(missing)[:5]}")
    if extra:
        raise SystemExit(f"pred 有但 sample 没有的 id 数: {len(extra)}，示例: {sorted(extra)[:5]}")

    values = p.set_index(args.id_col)[pred_col]
    sub = sample[[args.id_col]].copy()
    sub[pred_col] = sample[args.id_col].map(values).to_numpy()

    if args.check_bounds and sub[pred_col].notna().any():
        v = sub[pred_col].to_numpy()
        if v.min() < 0 or v.max() > 1:
            print(f"[warn] 预测值越界 [0,1]: min={v.min():.4f} max={v.max():.4f}", file=sys.stderr)
    if sub[pred_col].isna().any():
        raise SystemExit("重排后存在缺失预测，检查 id 映射")

    sub.to_csv(args.out, index=False)
    print(f"已写出: {args.out}  ({len(sub)} 行, 列: {list(sub.columns)})")
    print(sub.head(3).to_string(index=False))


if __name__ == "__main__":
    main()
