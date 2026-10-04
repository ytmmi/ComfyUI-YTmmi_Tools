---
name: anima-prompt-format
description: Format any idea, brief, character concept, image description or mixed Chinese/English request into Anima-ready prompt blocks (Danbooru tags plus natural-language caption, with the official tag order and quality prefix). Use for Anima Base / Aesthetic / Turbo text-to-image prompts in ComfyUI, when the user mentions Anima, 二次元, 动漫插画, Danbooru tags or needs one consistent positive/negative prompt pair.
version: 1.2.1
---

# Anima 提示词格式化（Prompt Format）

把用户的任意输入（一句话想法、中文简述、角色设定、参考图描述、已有半成品提示词）
整理成 **Anima 可直接使用的提示词**。Anima 是 CircleStone Labs × Comfy Org 的 2B
二次元插画模型，不擅长写实。

读 `references/anima-prompt-baseline.md` 获取硬规则原文（标签顺序、质量前缀、
权重语法、版本差异、生成参数、能力边界）。本文件是精简工作流，规则冲突时以基准文件为准。

## 输出契约（必须遵守）

只输出 Anima 提示词正文：

```text
[quality/meta/year/safety 标签], [人数标签], [角色], [作品], [画师], [general 标签]. [1~3 句英文自然语言描述]
```

- **默认只出正面提示词**：用户没提负面词、也没说自己那边没有负面词时，**不要输出任何负面提示词**，
  也不要有 `Positive prompt` 之类的标题行——直接给可以粘贴进生成节点的正文；
- 只在下列情况才追加负面提示词：① 用户明确要求负面词 / 负面提示词 / negative prompt；
  ② 用户表示自己那边没有设置负面词、需要一并给出；③ 该 skills 的流程本身必须成对交付（见下）。
  此时改用两段式（负面词按对应小节裁剪，不要改变默认格式）：

  ```text
  Positive prompt
  [正面提示词正文]

  Negative prompt
  [裁剪后的负面词]
  ```

- 默认格式**不带标签行**：不加 `Positive prompt` 标题、不加代码块围栏、不加前言与结尾建议；
  输出要能被用户直接抠进 ComfyUI 的提示词框；
- **不输出任何参数段**：不附 `Suggested settings`、不附宽高比 / 分辨率 / 步数 / CFG /
  采样器 / 种子建议——即使被问也只用一句话说明「这些由工作流设置决定」，不要写进正文。

本文件后文的 `## 示例` 仍按**两段格式**演示（含 `Negative prompt`），用来说明用户要负面词时该怎么写；
默认交付按上面的正面单段格式输出即可。

## 高杠杆规则（先看这 5 条；完整原文见 `references/anima-prompt-baseline.md`）

> 这几条决定"同一段需求、出图质感差一档"。**比堆砌质量词重要得多**，动手前先过一遍。

1. **画师标签必选**：正文里必须有 **1 个带 `@` 的主画师**（画师是画面质感的第一杠杆，没有它会落在平庸的默认风格里）。
   用户没给画师时，**由你按媒介 / 年代 / 题材自己挑一个最匹配的知名画师**——不要留空、也不要退回纯风格词。
   权重 `(@artist name:2)` 起；**只 1 个最稳，最多 1~2 个**（Anima 用 Qwen3 编码器，多画师会互相污染嵌入）。
2. **权重用大数**：Anima 需要比 SDXL 大得多——常规 `(tag:2)` 起，强强调 `(tag:3)` ~ `(tag:5)`；
   用户给 `1.2` 这类小数要**放大到 2~5**。照抄 SDXL 数值会得到"权重没用"的错误结论。
3. **权重标签总数 ≤4**，优先给取景 / 角度：自然语言一旦描述环境，模型就会**把镜头拉远**、吃掉
   `upper body` / `close-up`——必须用 `(upper body:2)`、`(close-up:3)` 对抗，并在自然语言**首句**明确取景。
4. **三层混合**：Hard Tags（Booru 标签，管结构）→ Soft Phrases（短视觉短语，管动作 / 氛围）→
   NL Caption（1~3 句稠密英文，管空间与光影）。纯标签扁平、纯自然语言超 2~3 段就崩，**同一语义不跨层重复**。
5. **因果链**：动作与天气必须落到**可见后果**（头发飘动、衣物受力、湿衣、积水、扬尘），
   不要只丢一个孤立标签——环境事件要影响角色或画面层次。

## 参数与提示词必须分离

- **提示词给文本编码器，参数给采样器，两者不能混**：分辨率、宽高比、种子、CFG、步数、
  采样器 / 调度器、模型文件名一律**不写进提示词**；宽高比与分辨率由工作流节点决定；
- **参数值一律不出现在输出里**：不要输出 `Suggested settings` 段，也不要给出宽高比、
  分辨率、步数、CFG、采样器或种子的具体数值。用户问到参数时，只回一句「这些由工作流设置决定」，
  不要在提示词前后附带数值；
- **质量前缀与模型版本绑定**（最易错）：裸 Base 用 `score_7`；**Aesthetic / Turbo 正负都不要 `score_*`**
  （它们是在剥离质量标签的语料上微调的，score 标签会推向 slop）；挂了 PonyV7 系美学 LoRA 的增强栈
  用 `score_9, score_8` 那一套，与裸模型前缀**不可互换**。

## 工作流

### 1. 抽取需求（静默完成，不要输出这一步）

- 主体：人数、角色身份、姿势、表情、服装、道具、物种、连续性锚点、LoRA 触发词；
- 场景：地点、时间、天气、氛围、色调、景别、视角、前/中/背景；
- 美术方向：动漫插画、赛璐璐上色、厚涂、漫画、封面 KV、三视图、分镜、Q 版、游戏 CG、概念稿；
- 需要保留的可见文字（招牌、标题、UI 文案、徽记文字、符号）——**逐字保留**；
- 是否需要分区 / 局部重绘 / 批量 / 三视图等特殊形态（交给对应 skills）。

用户给定的事实一律保留；缺失细节用协调的 Anima 原生选择补齐，但**主体必须仍是用户要的**。

### 2. 决定质量前缀（按版本分叉，最易错的一步）

| 情形 | 前缀 |
|---|---|
| 不知道版本（默认安全） | `masterpiece, best quality, safe` |
| 明确是裸 Base 模型 | `masterpiece, best quality, score_7, safe` |
| 明确是 Aesthetic / Turbo | `masterpiece, best quality, safe`（**不加 score_\***） |
| 明确挂了 PonyV7 系美学 LoRA | `masterpiece, very aesthetic, best quality, score_9, score_8, highres, absurdres, newest, year 2025` |

**只有用户明确说自己挂了 PonyV7 系美学 LoRA，才用最后一行的整套前缀。**
用户只是提到 `score_9` / `score_8`（例如"要 score_9 那种质量"）时，**只写他点名的 score 标签**，
不要顺手补上 `very aesthetic` / `absurdres` / `newest` / `year 2025`——那一整套是配合 LoRA 栈用的，
裸模型上会过冲；Aesthetic / Turbo 上更明确不该出现 `score_*`。

用户没提版本时**不要输出参数段**，只在提示词里用安全前缀；不要因为"看到 score_7 效果好"
就给 Aesthetic / Turbo 加 score 标签。

### 3. 组装 Positive prompt（标签区）

严格按官方区段顺序，区段内顺序随意：

```text
[quality/meta/year/safety] [人数] [角色] [作品] [画师] [general]
```

- 标签**全小写**，多词标签**用空格**（`long hair` 而不是 `long_hair`）；
- 唯一例外：`score_9` / `score_7` 这类 score 标签**保留下划线**；
- 人数标签要写够：`1girl` `solo`、`2girls`、`1boy, 1girl`、`multiple girls`；
- 画师标签**必须 `@` 开头**（`@nnn yryr`）——不加 @ 效果极弱，这是官方硬规则；
- **画师标签必选**：这里必须落下 **1 个**主画师，权重 `(@artist name:2)` 起（最多 1~2 个）。
  用户给了画师名 → 照抄并加 `@`；**用户没给 → 你按媒介 / 年代 / 题材自己挑一个最匹配的知名画师**，
  不要留空、也不要退回纯风格词；挑不好或拿不准拼写时再看 `anima-prompt-artist`；
- 取景 / 角度标签按第 4 步的**对抗漂移**规则加权（`(upper body:2)`）；
  **全文带权重的标签不超过 4 个**，优先分给取景与角度；
- **用户没指定构图 / 镜头时**：允许你**自主**挑一个与题材匹配的构图或**特殊镜头**
  （`fisheye lens`、`spherical composition`、`extreme foreshortening`、`isometric` 等，
  见 `anima-composition-optimize` 的「特殊情况」一节），**不要永远回落到最保守的默认值**；
  但① 用户已经指定构图时**绝不覆盖**，② 一次只用**一个**特殊装置，③ 表格类场景（三视图 / 分镜）禁用；
- Danbooru 与 Gelbooru 写法冲突时**用 Gelbooru 版本**；
- 不要堆砌同义质量词；Anima 用随机标签丢弃训练，**不需要标签堆满**。

### 4. 组装 Positive prompt（自然语言区）

标签区之后接 `.` 再写 **1~3 句英文描述**，把标签没能表达的内容说清：

- **首句先交代取景**（`The composition is a tight close-up portrait…`）：自然语言一旦开始描述环境，
  模型就会**把镜头拉远**并忽略 `upper body` / `close-up` / `portrait` 这类取景标签。
  对抗办法是两步一起做——标签区给取景加权 `(upper body:2)`、`(close-up:3)`，**首句再把取景写死**；
  如果仍然拉远，就把权重加到 `(upper body:5)` 甚至 `(upper body:7)`；
- 先给画面定调一句（媒介 + 主体 + 环境 + 色调整体感）；
- 角色细节写在一起（发色发型、眼睛、表情、视线、服装、道具、姿态）；
- 背景细节写在一起，用空间词定位（`foreground` `left side` `center` `background`）；
- 光影与氛围写在**自然语言层**（`rim light`、`volumetric god rays`、`dreamy pastel atmosphere`、
  `soft glowing light`）——这是收益仅次于画师标签的一层，不要只靠标签区；
- 动作与天气要落到**可见后果**（头发飘动、衣物受力、湿衣、积水、扬尘），不要只写一个孤立名词；
- **同一语义不跨层重复**：标签区已经写了 `close-up`，这里就不要再写一遍 `close-up`，改用叙事强化；
- 写"最终画面"而不是"生成过程"；不出现 `or` / `maybe` / `could be`；
- 纯自然语言时**至少 2 句**，过短会出意外内容。

### 5. 组装 Negative prompt

从官方默认负面起手，再**只加与本次需求相关的项**：

```text
worst quality, low quality, lowres, blurry, jpeg artifacts, bad anatomy, bad hands, extra fingers, missing fingers, extra limbs, deformed, duplicate face, crossed eyes, messy lineart, watermark, signature, username, logo, unrelated text
```

裁剪规则：

- 用户需要画面里出现文字 → **删掉 `unrelated text`**，必要时只留 `garbled text, misspelled text`；
- 三视图 / 角色一致性 → 加 `inconsistent character, outfit mismatch`；
- 多角色 / 分区 → 加 `merged characters, duplicated character`；
- 局部重绘 → 加 `visible mask edge, patchy repair, mismatched lighting, mismatched style`；
- 负面里**不要**出现直接对抗用户需求的内容（例如用户要 `nsfw`，就不要把 `nsfw` 写进负面）。

### 6. 交付前自检（静默）

- **有没有落下主画师**（带 `@`、权重 `:2` 起、只 1~2 个）？这是最容易漏、影响最大的一条；
- 带权重的标签是否 **≤4 个**，且优先给了取景 / 角度？
- 自然语言**首句是否写死了取景**（对抗漂移）？
- 动作与天气是否落到了**可见后果**？
- 质量前缀是否与版本匹配（有没有把 PonyV7 那整套前缀用在裸模型 / Aesthetic 上）？
- 有没有把宽高比 / 分辨率 / 种子 / CFG / 步数 / 采样器 / 模型文件名漏进提示词？
- 用户要求的每个主体、角色、可见文字、风格、约束是否都还在？
- 标签区顺序是否符合 `[质量/元信息/安全] [人数] [角色] [作品] [画师] [通用]`？
- 标签是否全小写、多词是否用空格、score 标签是否保留下划线、画师是否带 `@`？
- 标签与自然语言是否互相加强，而不是重复空洞同义词？
- 是否始终是动漫 / 插画取向（除非用户明确要照片感动漫）？
- 输出是否按默认格式交付（只有正面正文，没有标题行、围栏或参数段）？

## 示例

输入：`银发少女站在废弃都市，孤独感，要安全的图`

```text
Positive prompt
masterpiece, best quality, safe, 1girl, solo, silver hair, long hair, blue eyes, black cloak, ruined city, overgrown concrete, melancholic atmosphere, (@artist name:2), (cowboy shot:2), off-center, left side, cool gray palette, detailed background. The composition is an off-center cowboy shot: a lone silver-haired girl in a black cloak stands in the middle of an abandoned city avenue, her cloak drifting in the wind while moss-covered concrete and broken glass catch the cold light around her; the collapsed towers behind fall into pale morning haze, muted and out of focus so she stays the one thing you look at.

Negative prompt
worst quality, low quality, lowres, blurry, jpeg artifacts, bad anatomy, bad hands, extra fingers, missing fingers, extra limbs, deformed, duplicate face, crossed eyes, messy lineart, watermark, signature, username, logo, unrelated text
```

> 示例里的 `@artist name` 是**占位符**——交付时要换成你自己按媒介 / 题材挑的、真实存在的知名画师名，
> 并核对拼写。这里只演示它该出现的位置（artist 位）与权重档（`:2` 起）。
> 注意两条高杠杆改动：**补上主画师**、**给取景加权 `(cowboy shot:2)` 并在首句写死取景**。

输入：`画个角色，2021 年的老番质感，要標題「STARLIGHT」`

```text
Positive prompt
year 2021, mid, normal quality, safe, 1girl, solo, medium hair, brown eyes, school uniform, standing, night city street, neon signs, upper body, cel shading, retro anime screenshot, "STARLIGHT" as a short neon sign above the girl. An anime-style girl in a navy school uniform stands on a rainy neon street at night, warm sign light rimming her hair while reflections pool on the asphalt, the short glowing title sign sits clearly in the upper left and stays readable.

Negative prompt
worst quality, low quality, lowres, blurry, jpeg artifacts, bad anatomy, bad hands, extra fingers, missing fingers, extra limbs, deformed, duplicate face, crossed eyes, messy lineart, watermark, signature, username, logo, garbled text, misspelled text
```

## 边界

- 用户要"照片级写实"时先说明 Anima 不做写实（除非他要的就是照片感的动漫渲染）；
- 用户要长段文字排版：说明 Anima 文字渲染弱，建议只保留单词或短句，长文字后期加；
- 需要画师风格混合 → 交给 `anima-prompt-artist`；
- 整体配色 / 颜色搭配 / 色调与情绪 → 交给 `anima-color-harmony`；
- 需要分区 / 局部重绘 → 交给 `anima-prompt-regional`；
- 需要角色多视图一致性 → 交给 `anima-prompt-character`；
- 需要负面词专项调优 / 版本质量前缀决策 → 交给 `anima-prompt-negative`。
