---
name: anima-prompt-negative
description: Build the Anima negative prompt and pick the correct quality prefix for Anima-Base, Anima-Aesthetic, Anima-Turbo and PonyV7-style aesthetic LoRA stacks. Use when an Anima prompt needs its score_* / quality tags decided, when a negative prompt must be trimmed to what one request actually needs, when the prompt gets plasticky or over-cooked slop, or when safety tags, `artist name` and text-related negatives have to agree with the positive prompt.
version: 1.0.0
---

# Anima 负面提示词与质量前缀（Negative Prompt & Quality Prefix）

负面提示词是**版本相关**的：同一个 `score_7` 写在裸 Base 上是对的，写在 Aesthetic / Turbo 上会把画面
推向 slop。所以本 skill 的第一件事不是加词，而是**先判定版本**；第二件事是**只加这次需求真正需要的词**。

读共同基准 `anima-prompt-format/references/anima-prompt-baseline.md` 拿官方默认正/负向原文与版本差异，读
`references/anima-negative-tables.md` 拿版本前缀矩阵、按失败域分组的负面词表和"可见瑕疵 → 该加哪些词"的
诊断对照。本文件讲流程与决策。

## 输出契约

本 skills 的触发条件就是用户要负面词，因此**默认成对交付**（正面正文 + 裁剪后的负面词）；若用户只问「负面词怎么改」，则可以只给负面词：

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

- 示例仍按两段演示，但**默认只交付正面**；本 skills 被调用时通常成对给出。

## 官方原文（逐字引用，别改写法）

正向默认前缀：

```text
masterpiece, best quality, score_7, safe, 
```

负向默认：

```text
worst quality, low quality, score_1, score_2, score_3, artist name, blurry, jpeg artifacts, chromatic aberration
```

- score 标签是**唯一保留下划线**的标签（`score_7` 不能写成 `score 7`）；
- 官方负向里的 `artist name` 会**压制画师标签效果**：要画师风格时必须删（见第 6 步）；
- 官方负向里的 `blurry` 与"要虚化背景"的需求冲突：改写成 `blurry subject` 或直接删（见第 5 步）。

## 工作流

### 1. 判定版本（决定一切的第一步）

| 证据 | 结论 |
|---|---|
| 用户说了 `Anima-Base` / `anima-base-v1.0` | 裸 Base |
| 用户说了 `Aesthetic` / `Turbo` | 质量标签剥离版 |
| 用户说挂了 `masterpiece-v51`、双美学 LoRA、PonyV7 系评分 LoRA | LoRA 增强栈 |
| 用户没提，或只说"Anima" | **未知 → 安全档** |

判定不了就**不要猜**：用安全前缀，不输出参数段，并在交付说明里写清假设（如果有交付说明的位置）。

### 2. 按版本写正向质量前缀

| 版本 | 正向前缀 |
|---|---|
| 裸 Base | `masterpiece, best quality, score_7, safe, ` |
| Aesthetic / Turbo | `masterpiece, best quality, safe`（**不写任何 score_\***） |
| PonyV7 系美学 LoRA 栈 | `masterpiece, very aesthetic, best quality, score_9, score_8, highres, absurdres, newest, year 2025` |
| 未知 | `masterpiece, best quality, safe` |

> Aesthetic / Turbo 是在**已剥离质量标签**的高质图上微调的：往它们身上塞 `score_*` 会把画面推向
> 过冲的"slop"（塑料感、过曝、糊成一团的细节）。这是本 skill 最常被搞错的一处。
> 反过来，在裸 Base 上写 `score_9, score_8` 同样会过冲——`score_7` 才是裸模型的尺度。

### 3. 从官方默认负面起手，按版本调整 score 端

| 版本 | 负向里的 score 端 |
|---|---|
| 裸 Base | 保留 `score_1, score_2, score_3` |
| Aesthetic / Turbo | **删掉全部 score_\***（正负一致：都不写 score） |
| PonyV7 系美学 LoRA 栈 | 保留 `score_1, score_2, score_3`（把低分端压走），必要时补到 `score_4, score_5` |
| 未知 | 删掉 score 端（在 Aesthetic/Turbo 上是负收益，在 Base 上也只是弱收益） |

### 4. 负面不是垃圾场：只加这次需求需要的组

Anima 用**随机标签丢弃**训练：负面堆得越多，每条得到的权重越薄，还会顺带压掉合法的画面内容。
默认骨架 + 本需求相关的 **1~3 组** 就够。

| 组 | 何时加 | 何时删 / 慎用 |
|---|---|---|
| 解剖 set | 全身、复杂姿势、多人重叠 | 想要 Q 版 / 变形生物 / 机械体时删掉 `bad proportions`、`extra limbs` |
| 脸 set | 特写、多人同框、海报 | 要异色瞳时删 `mismatched eyes`；要同一张脸重复出现（表格）时慎用 `duplicate face` |
| 手 set | 手部可见、持物 | 手不在画面里可以不写；写太多会连带压掉手部细节 |
| 角色表 set | 三视图、表情表、多角色 | 表格里慎用 `duplicated character`（会把本该重复的格子一起压掉） |
| 分区 set | 分区提示词、区域遮罩 | 换区域时记得同步改，见 `anima-prompt-regional` |
| 局部重绘 set | inpaint / 局部修 | 遮罩边缘词只在重绘时用 |
| 文字 set | 不要画面里出现文字时 | **用户要文字/招牌/标题时整组删掉**，最多留 `garbled text, misspelled text` |
| 水印 set | 不想要签名、平台水印 | 要画师署名风格时与水印词的边界要分清 |
| 构图 set | 框架有硬要求（立绘不切脚） | 与正向景别冲突时以正向为准，例：正向 `feet out of frame` 就别加 `bad crop` |

可选加，但别默认全上：`bad crop`、`out of frame`、`cluttered background`、`extra characters`。

> `extra characters` 只在**人数是硬要求**时加（单角色立绘、固定队伍、三视图）；群像 / 人群场景加了
> 会把路人一起压掉。

### 5. 冲突检测：负面里不许出现对抗需求的词

做法：把正向提示词扫一遍，命中下表就删除对应负面词。

| 正向里出现了 | 负面里必须删 / 改 |
|---|---|
| 画师标签 `@…` | `artist name`（否则画师效果被压制） |
| `simple background` | 负面不要 `simple background` / `busy background` 混着写 |
| `depth of field` / `blurry background` | 裸 `blurry` → 改 `blurry subject` |
| 招牌、标题、名牌等可见文字 | `unrelated text`、`english text`、`text` |
| Q 版 / chibi | `bad proportions` |
| 异色瞳 | `mismatched eyes`、`uneven eyes` |
| 怪物 / 机械 / 多臂角色 | `extra limbs`、`extra arms`、`mutated hands` |
| 三视图 / 表情表 | `duplicated character`、`multiple views` |
| 人群 / 群像 | `extra characters` |
| 夜景 / 暗调 | 任何 `dark`、`underexposed` 类词 |
| `nsfw` / `sensitive` / `explicit` | 负向里同名的 safety 词 |

### 6. `artist name` 的取舍

- 它在**官方默认负面里**，作用是压掉"署名式"的风格倾向，常和 `signature` 一起承担去签名的职责；
- 但它是**画师标签的天敌**：加了 `@` 画师标签却觉得没效果时，第二个要检查的就是它（第一个是漏了 `@`）；
- 决策：要画师风格 → 删；要干净、通用、不带某位画师签名的观感 → 保留。

### 7. safety 标签是刻意选择，正负必须自洽

- 正向 safety 段**只写一个**：`safe` / `sensitive` / `nsfw` / `explicit`；
- 用户没提 → 默认 `safe`（与官方默认前缀一致），并把它当成默认假设；
- 用户在负向里写同名的 safety 词 → 自相矛盾，删掉；把相反词写进负向只是**次要辅助**，
  主杠杆始终是正向那个标签；
- 不要在没有用户指示时擅自升级或降级 safety 等级；这是用户/工作流的决定，不是提示词技巧问题；
- 用户明确要 `sensitive` / `nsfw` 时，如实照写，不要加说教、也不要偷偷替换成 `safe`。

### 8. 自检（静默）

- 版本判定有没有依据？判断不了是否用了安全前缀且没输出参数？
- `score_*` 是否只出现在该出现的版本上（Base 正向 `score_7`、Aesthetic/Turbo 全无）？
- 负面是不是"官方骨架 + 1~3 组"，而不是几十个词的清单？
- 有没有与正向需求对抗的负面词？
- 正向 safety 标签是否只有一个，且与负向自洽？
- 正文里是否混进了分辨率、种子、CFG、步数、模型名？

## 示例

输入：`工作流挂了 PonyV7 系美学 LoRA；雪夜车站的少女插画，画面里不要出现任何文字`

版本判定：LoRA 增强栈 → 正向用美学评分前缀；负向保留低分端 score。

```text
Positive prompt
masterpiece, very aesthetic, best quality, score_9, score_8, highres, absurdres, newest, year 2025, safe, 1girl, solo, silver hair, long hair, white coat, scarf, standing, train station platform, night, snow, fluorescent lights, cowboy shot, depth of field, cold blue palette. A lone silver-haired girl in a white coat waits on a snow-covered station platform at night, fluorescent lights smearing across the wet ground, her breath visible in the cold air, the whole frame kept clean with no lettering of any kind.

Negative prompt
worst quality, low quality, score_1, score_2, score_3, blurry subject, jpeg artifacts, chromatic aberration, bad anatomy, bad hands, extra fingers, missing fingers, extra limbs, deformed, watermark, signature, username, logo, twitter username, web address, unrelated text, garbled text, misspelled text
```

版本相关说明：

- 正向用 `score_9, score_8`（美学 LoRA 栈的尺度），**不是**裸 Base 的 `score_7`；前缀里带了
  `very aesthetic, highres, absurdres, newest, year 2025`，这是该栈的搭法；
- 负向保留 `score_1, score_2, score_3`（与正向同源，压低分端），
  但因为正向没有画师标签，`artist name` 保留与否都行——本例选择删掉它，只留 `signature, username` 等
  去水印词；
- 用户要求画面无文字 → 文字组保留 `unrelated text, garbled text, misspelled text`；
- 正向要 `depth of field` → 负向把裸 `blurry` 改写为 `blurry subject`，避免自相矛盾。

同一需求若用户说明是 **Aesthetic 版**：正向改成 `masterpiece, best quality, safe`，
负向**删掉全部 score_\***，其余按失败域裁剪——同一张图，前缀完全不同。

## 边界

- 只做基础格式化、不涉及版本与负面调优 → `anima-prompt-format`；
- 负面词要按区域分别设置 → `anima-prompt-regional`；
- 构图层面的失败（主体太小、背景抢戏）→ `anima-composition-optimize`；
- 动作崩坏、动态模糊类问题 → `anima-motion-boost`；
- 画师标签本身的写法与混合 → `anima-prompt-artist`；
- 风格词表与质感方向 → `anima-style-control`、`anima-style-boost`；
- 角色一致性类负面（`inconsistent character` 等）→ `anima-prompt-character`；
- LoRA 触发词与 LoRA 权重 → `anima-lora-trigger`；
- 种子、步数、CFG、分辨率与采样器属于**工作流侧参数**，不要写进提示词，也不要在输出里给数值；
- 需求还很模糊、要先发散重构 → `anima-prompt-optimize`。
