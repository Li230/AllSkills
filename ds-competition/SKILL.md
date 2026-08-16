---
name: ds-competition
description: "End-to-end workflow for data science / machine-learning competitions (Kaggle、天池等数据科学竞赛): reproducible setup, validation design matching the metric, GBM baseline with OOF predictions, hyperparameter tuning, ensembling, and submission verification. Use when working on a competition with train/test/sample_submission CSV files — building a baseline, improving CV score, preparing a submission, or debugging validation/leakage problems. Complements tabular-ml-prep (EDA/cleaning/feature engineering)."
---

# Data Science Competition 数据科学竞赛工作流

## 核心原则

- **本地 CV 是唯一可信的迭代信号**：CV 必须与竞赛指标一致；LB 只做校准与抽查，不用于调参。
- **一次只改一个变量**，每次改动记录 OOF 指标，用实验日志对比。
- **固定 seed**，全流程可复现；提交前做 seed 稳定性检查。
- **预处理器/编码器只在训练折内 fit**，测试集统计量一律不参与训练。
- **先跑通简单基线**，再逐步加复杂度（KISS）。

## 环境

- 本机默认解释器：`/opt/anaconda3/bin/python`（含 pandas/sklearn）。
- GBM 库缺失时先装：`pip install lightgbm xgboost catboost optuna`；**未装也能跑**——`train_gbm.py` 自动回退 sklearn `HistGradientBoosting`。

## 工作流

### 步骤 0 — 读懂赛题

- 确认文件角色：`train.csv`（带标签）、`test.csv`（待预测）、`sample_submission.csv`（格式模板，占位值=基线）。
- 从竞赛页面确认**指标**（AUC / LogLoss / RMSE / QWK 等）与提交格式（概率列还是类别列）。
- 确认 train/test 的 id 无重叠、sample 的 id 与 test 完全一致。

### 步骤 1 — 搭建可复现脚手架

- 建目录：`data/`、`experiments/`、`submissions/`。
- 用 `scripts/cv_setup.py` 生成折文件（`train_with_folds.csv`），折一旦生成就固定复用：

```bash
python scripts/cv_setup.py --train data/train.csv --target addicted_label \
    --mode stratified --n-folds 5 --seed 42 --out data/train_with_folds.csv
```

- 建实验日志（CSV：时间 / 配置 / OOF / 备注），每次实验追加一行。

### 步骤 2 — EDA、清洗、特征工程

- 此阶段交给 **tabular-ml-prep** skill（`/Users/macbookair/.workbuddy/skills/tabular-ml-prep/SKILL.md`）：数据质量总检（重复行/常量列/类型/类别一致性/train↔test 重叠）→ 缺失 → 异常 → 类别编码 → 特征工程，全程"用验证指标决策"。
- 通用 EDA 脚本：`tabular-ml-prep/scripts/tabular_eda.py`（加 `--test` 可对比 train/test 一致性）。

### 步骤 3 — 验证设计（最关键）

- CV 策略按数据类型选（分类分层 / 回归 KFold / 时间 TimeSeries / 分组 Group），细节见 `references/validation.md`。
- 所有预处理只在训练折内 fit；折划分固定后不再变。
- 跑一版干净基线并提交一次，建立 CV↔LB 校准线；后续只用 CV 迭代。

### 步骤 4 — 跑基线

```bash
python scripts/train_gbm.py --train data/train_with_folds.csv \
    --test data/test.csv --sample data/sample_submission.csv \
    --target addicted_label --task binary --folds-col fold \
    --out experiments/baseline
```

- 输出：OOF 预测（`oof.csv`）、测试预测（`submission.csv`）、指标（`run.json`）、特征重要性（LightGBM 时 `importances.csv`）。
- 记录 OOF 指标作为后续所有改动的对照基准。

### 步骤 5 — 迭代：特征与调参

- **特征 ablation**：新特征单独去掉后 OOF 下降才保留。
- **调参**：用 `references/tuning.md` 的 Optuna 配方，目标函数跑**同一套固定折**；只有 OOF 提升才算数（<0.0005 视为噪声）。
- 一次只动一个变量；每步对比 OOF。

### 步骤 6 — 集成

- 多个模型（不同算法/特征集）OOF 接近且预测相关 <0.95 时做集成，方法见 `references/ensembling.md`。
- 权重只按 OOF 定；集成前后都提交一次验证。

### 步骤 7 — 提交前检查

```bash
python scripts/make_submission.py --sample data/sample_submission.csv \
    --pred experiments/baseline/submission.csv --out submissions/v1.csv --check-bounds
```

- 校验 id 集合与 sample 完全一致、顺序重排、概率越界警告。
- seed 稳定性：同配置 3~5 个 seed，OOF 标准差大则取平均再提交。
- 泄漏自查：预处理是否在 split 后 fit？目标编码是否 OOF？OOF 是否异常高（AUC>0.99）？

## 防坑清单

- 预处理在切折前 fit、目标编码用全量均值 → 泄漏。
- CV 与指标不一致（用准确率评不平衡分类）。
- 反复提交刷 LB / 用 LB 调参调权重 → 过拟合 LB。
- 提交格式错：id 缺失/多余/顺序乱/列名不符。
- 类别列高基数硬 One-Hot；缺失列无脑 dropna。
- 为了"显得完整"引入未验证的模型或特征。

## 资源

- `scripts/cv_setup.py`：生成折（stratified/kfold/time/group），无泄漏。
- `scripts/train_gbm.py`：GBM 基线（LGBM 优先、HGB 回退），OOF + 提交 + 特征重要性。
- `scripts/metrics.py`：auc/logloss/accuracy/rmse/mae/qwk。
- `scripts/make_submission.py`：提交格式校验与生成。
- `references/validation.md`：CV 策略、指标对齐、泄漏、CV↔LB。
- `references/tuning.md`：Optuna 调参配方。
- `references/ensembling.md`：平均/加权/排名/Stacking。
- 互补 skill：`tabular-ml-prep`（EDA/清洗/特征工程）。
