"""通用表格数据 EDA 脚本（tabular-ml-prep 技能配套）。

对任意 train.csv 直接跑：先做数据质量总检（重复行/常量列/类型可疑/
类别不一致/标签基本检查），再输出每列缺失率、按行缺失分布、
数值特征 IQR 异常、与标签的关系。可选 --test 对比 train/test 的
列集、类别全集与分布一致性（找出泄漏与漂移）。

用法:
  python tabular_eda.py --csv path/to/train.csv [--target addicted_label] [--id id]
  python tabular_eda.py --csv path/to/train.csv --test path/to/test.csv --target addicted_label
"""
import argparse

import numpy as np
import pandas as pd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, help="训练集 CSV 路径")
    ap.add_argument("--test", default=None, help="测试集 CSV 路径（可选，做一致性检查）")
    ap.add_argument("--target", default=None, help="标签列名（可选，给了才算与标签的关系）")
    ap.add_argument("--id", default="id", help="id 列名，默认 'id'")
    args = ap.parse_args()

    df = pd.read_csv(args.csv)
    n = len(df)
    drop_cols = [c for c in (args.id, args.target) if c in df.columns]
    feat_cols = [c for c in df.columns if c not in drop_cols]

    num_cols = df[feat_cols].select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df[feat_cols].select_dtypes(include=["object", "string", "category"]).columns.tolist()
    target = args.target if (args.target and args.target in df.columns) else None

    print(f"样本数={n:,}  连续型={len(num_cols)}  类别型={len(cat_cols)}  标签={target}")

    # ---- 零、数据质量总检 ----
    print("\n========== 零、数据质量总检 ==========")

    # 1. 完全重复行
    dup = int(df.duplicated().sum())
    print(f"完全重复行: {dup:,} ({dup/n*100:.2f}%)" + ("  <- 建议去重" if dup else ""))

    # 2. 常量/近常量列
    const_cols, near_const_cols = [], []
    for c in feat_cols:
        s = df[c].dropna()
        if len(s) == 0:
            const_cols.append(c)
        elif s.nunique() <= 1:
            const_cols.append(c)
        else:
            top = s.value_counts().iloc[0] / len(s)
            if top >= 0.9:
                near_const_cols.append((c, top))
    if const_cols:
        print(f"常量列(建议删): {const_cols}")
    if near_const_cols:
        print(f"近常量列(单值占比>=90%, 建议删): " + ", ".join(f"{c}({p:.0%})" for c, p in near_const_cols))

    # 3. 数值列被读成 object
    for c in cat_cols:
        s = df[c].dropna().astype(str).str.replace(",", "", regex=False)
        parseable = pd.to_numeric(s, errors="coerce").notna().mean()
        if parseable >= 0.8:
            print(f"类型可疑: {c} 是 object 但 {parseable:.0%} 可转数值  <- 建议 to_numeric(errors='coerce')")

    # 4. 类别一致性（strip + 小写归一后类别数下降 => 大小写/空格/同义值问题）
    for c in cat_cols:
        s = df[c].dropna().astype(str)
        raw = s.nunique()
        norm = s.str.strip().str.lower().nunique()
        if norm < raw:
            print(f"类别不一致: {c} 归一化后 {raw}->{norm} 类  <- 检查大小写/前后空格/同义值")

    # 5. 标签基本检查
    if target:
        if df[target].isna().any():
            print(f"标签缺失: {int(df[target].isna().sum()):,}  <- 标签缺失行需处理")
        vc = df[target].value_counts(dropna=False)
        for k, v in vc.items():
            ks = "缺失" if pd.isna(k) else str(k)
            print(f"  标签 {ks}: {int(v):,} ({v/n*100:.1f}%)")

    # 6. train/test 一致性
    if args.test:
        te = pd.read_csv(args.test)
        print("--- train/test 一致性 ---")
        train_cols = [c for c in df.columns if c != target]
        miss_c = [c for c in train_cols if c not in te.columns]
        extra_c = [c for c in te.columns if c not in train_cols]
        if miss_c:
            print(f"test 缺少列: {miss_c}")
        if extra_c:
            print(f"test 多余列: {extra_c}")
        common = [c for c in feat_cols if c in te.columns]
        overlap = df[common].drop_duplicates().merge(te[common].drop_duplicates(), on=common).shape[0]
        print(f"特征取值完全相同的行(跨集重复, 疑似泄漏): {overlap:,}")
        if args.id in df.columns and args.id in te.columns:
            inter = len(set(df[args.id]) & set(te[args.id]))
            print(f"id 重叠: {inter:,}  <- 泄漏红线" if inter else "id 无重叠: OK")
        for c in common:
            if c in num_cols and c in te.select_dtypes(include=[np.number]).columns:
                m1, m2 = df[c].mean(), te[c].mean()
                if m2 != 0 and abs(m1 - m2) / abs(m2) > 0.3:
                    print(f"分布漂移? {c}: train均值={m1:.3f} test均值={m2:.3f}")
            elif c in cat_cols:
                unseen = set(te[c].dropna().astype(str)) - set(df[c].dropna().astype(str))
                if unseen:
                    print(f"test 未见过类别: {c} -> {sorted(unseen)[:5]}")

    # ---- 一、每列缺失率 ----
    print("\n========== 一、每列缺失率 ==========")
    miss = df[feat_cols].isna().mean().sort_values(ascending=False) * 100
    for c in miss.index:
        print(f"  {c:<24} 缺失 {miss[c]:5.2f}%")
    print(f"  总缺失格子: {int(df[feat_cols].isna().sum().sum()):,}")

    print("\n========== 二、按行缺失个数分布 ==========")
    rm = df[feat_cols].isna().sum(axis=1)
    print(f"  完全无缺失: {(rm==0).sum():,} ({(rm==0).mean()*100:.1f}%)")
    print(f"  至少缺1个: {(rm>0).sum():,} ({(rm>0).mean()*100:.1f}%)")
    print(f"  缺>=3个:   {(rm>=3).sum():,} ({(rm>=3).mean()*100:.1f}%)")

    # ---- 三、连续型：IQR 异常 + 与标签关系 ----
    print("\n========== 三、连续型特征 ==========")
    for c in num_cols:
        s = df[c].dropna()
        q1, q3 = s.quantile([.25, .75]); iqr = q3 - q1
        out = s[(s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)]
        skew = df[c].skew()
        line = f"  {c:<24} 缺失{df[c].isna().mean()*100:4.1f}%  skew={skew:+.2f}  IQR异常={len(out)}({len(out)/len(s)*100:.2f}%)"
        if target:
            corr = df[c].corr(df[target])
            line += f"  与标签相关={corr:+.3f}"
        print(line)
        if target:
            edges = df[c].quantile(np.linspace(0, 1, 11)).drop_duplicates().values
            bins = pd.cut(df[c], bins=edges, include_lowest=True)
            rate = df.groupby(bins, observed=True)[target].mean() * 100
            lo, hi = rate.min(), rate.max()
            print(f"     标签率随取值: {lo:.1f}% ~ {hi:.1f}%  (区间数={len(rate)})")

    # ---- 四、类别型 ----
    if cat_cols:
        print("\n========== 四、类别型特征 ==========")
        for c in cat_cols:
            vc = df[c].value_counts(dropna=False)
            print(f"  {c}  缺失{df[c].isna().mean()*100:.1f}%")
            for k in vc.index:
                ks = "缺失" if pd.isna(k) else str(k)
                line = f"    {ks:<10} n={int(vc[k]):>7} ({vc[k]/n*100:4.1f}%)"
                if target:
                    mask = df[c].isna() if pd.isna(k) else (df[c] == k)
                    line += f"  标签率={df.loc[mask, target].mean()*100:.1f}%"
                print(line)


if __name__ == "__main__":
    main()
