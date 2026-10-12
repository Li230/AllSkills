---
name: anything2manga
description: 竖屏 9:16 AI 漫剧生成——一句话主题一键出片（白模构图引导 + 台词驱动六要素生图 + VLM 图文核验 + 程序化 BGM + Remotion 合成 + 双合规标识）。用户要"把故事/主题做成漫剧/漫剧视频/AI 动画短剧"时使用。
---

# anything2manga · AI 漫剧生成

工程位置：`~/Desktop/Study/anything2manga`（Git 已纳管）。完整文档见该目录 `README.md`（管线/接入）与 `交付说明.md`（验收/踩坑）。

## 何时使用

- 用户给一句话主题（如"小猫和主人在超市买东西"），要生成 1-1.5 分钟竖屏漫剧成片
- 已有题材要重生成部分镜头、改剧本、调提示词

## 一键编排

```bash
cd ~/Desktop/Study/anything2manga
ALIYUN_API_KEY=<key> THEME="题材一句话" SLUG=<素材目录名> BUDGET=12 PROVIDER=aliyun bash scripts/make_film.sh
```

- `PROVIDER=mock`：0 元灰模全链路演练（先看故事与节奏再花钱）
- 六步：LLM 剧本（富镜头四元组）→ edge-tts 时间轴 → 白模 compose → 生图+VLM 核验 → BGM → 渲染
- 产物：`renders/<SLUG>_<VER>.mp4`、`costs_<SLUG>.json`（逐张留痕）、`qc/vlm_check_<SLUG>.md`

## 换新题材的零改码清单

1. 角色卡自动抽取到 `script/char_desc_<slug>.json`（可手改）
2. `scripts/generate.py` 补 `SCENE_LIBRARY['<slug>']`（每场景 80-120 字环境段，场景 id 固定：gate/market/hall/cave/circle/portal/forest）
3. 补 `LIGHT_ARC['<slug>']` 三章光照弧；关键道具加 `PROP_DESC`
4. `src/config.ts` 加 `HOOK['<slug>']`（片头钩子卡：高潮镜 + 两行悬念大字，缺省则片头黑场）
5. 非人角色加入 `NONHUMAN['<slug>']`（姿势走 OBJECT_POSE 非肢体映射，防止画出人手人腿）

## 硬约束（血泪换来的，不要绕过）

- **slug 印章闸门**：timeline.json 属于哪个 slug 是盖了章的；切题材必须重跑 tts_build，generate 检测不匹配会拒跑（曾因乱序白烧 8.4 元）
- **句长 10-18 字**：短句 = 镜头快闪 = 完播率崩（v7 教训：21/28 镜 <2.2s）
- **VLM 判"可视要素清单"不判台词原句**：比喻会被字面误判（"像抱着月亮"判否）
- **非人角色禁肢体姿势**：音箱/器物类角色用 OBJECT_POSE，否则长出人手人腿
- **画面禁文字**要写"文字一律模糊色块"，否则模型把台词原文印到屏幕上
- 生成前确认 shots 目录是空的（或含想要保留的图）——generate 跳过已存在文件

## QC 流程

1. 自动：VLM 闸门（生图时）+ `motion_check.py --frames fin_frames_<V>`（静止率）
2. 抽帧：`ffmpeg -i renders/<x>.mp4 -vf "fps=1/2,scale=720:1280" qc/fr_<x>/f_%03d.png`
3. 派 QC agent 走查：台词-画面可指认 ≥90%、高项清零才能交付
4. 人工复判 NEEDS_HUMAN.json（VLM 过严时目检放行）

## 成本口径（2026-09 实测）

生图 0.30 元/张；单集 28 镜含核验重试 8.4-12.9 元；TTS/白模/BGM/渲染 0 元。
