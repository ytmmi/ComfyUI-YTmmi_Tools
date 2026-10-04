# Anima 提示词基准（Prompt Baseline）

本文件是 Anima 家族全部 skills 的**共同基准**，内容来自官方来源，供各 skills 相互引用。
写 Anima 提示词前，先确认本文件的硬规则；与用户显式要求冲突时，以用户要求为准。

## 1. 模型事实

| 项目 | 内容 |
|---|---|
| 模型 | Anima（CircleStone Labs × Comfy Org 合作发布） |
| 规模 | 20 亿参数（2B）文本生图模型，基于 NVIDIA Cosmos-Predict2-2B-Text2Image |
| 定位 | **动漫 / 插画 / 非写实艺术**；明确不擅长写实（realism 不在范围内） |
| 文本编码器 | Qwen-3 0.6B（`qwen_3_06b_base.safetensors`，放 `models/text_encoders/`） |
| VAE | Qwen-Image VAE（`qwen_image_vae.safetensors`，放 `models/vae/`） |
| 扩散模型 | `anima-base-v1.0.safetensors`（放 `models/diffusion_models/`，约 12.2 GB） |
| 训练数据 | 数百万动漫图 + 约 80 万非动漫艺术图；**未使用合成数据**；动漫知识截止 2025-09 |
| 分辨率 | 支持多种画幅；**具体尺寸由工作流设置，不写进提示词** |
| 语言 | 训练语料以英文 Danbooru 标签与英文自然语言为主；**模型面向的提示词默认写英文** |

### 版本差异（质量前缀必须与版本匹配）

| 版本 | 说明 | 质量前缀建议 |
|---|---|---|
| **Anima-Base v1.0** | 预训练基座，风格自由度最高、多样性最好；**LoRA 应用它训练** | `masterpiece, best quality, score_7, safe, ` |
| **Anima-Aesthetic** | 只在高质图上微调，且**训练时已剥离质量标签** | 可完全不写质量标签；保留 `masterpiece, best quality, ` 也安全；**正/负都不要 score_\*** |
| **Anima-Turbo** | 蒸馏加速版，稳定性更强但多样性降低 | 同 Aesthetic：少用甚至不用质量标签 |
| LoRA 增强工作流（如双美学 LoRA） | 第三方 `masterpiece-v51` 等 LoRA 基于 PonyV7 美学评分训练 | `masterpiece, very aesthetic, best quality, score_9, score_8, highres, absurdres, newest, year 2025` |

> **易错点**：HuggingFace 模型卡描述的是**裸模型**（用 `score_7`）。若工作流挂了 PonyV7 系美学 LoRA，
> 把 `score_7` 塞回去会**削弱** LoRA 效果；反之在裸模型上用 `score_9, score_8` 会过冲成"slop"。
> 判断不了版本时，只用裸模型安全前缀 `masterpiece, best quality, safe`，**不要输出参数数值**。

## 2. 提示词总规则（官方）

1. 训练分布 = **Danbooru 风格标签** + **自然语言长描述** + 两者混合。三者都可用，混合通常最稳。
2. 标签**全小写**，多词标签**用空格而不是下划线**；**唯一例外是 score 标签**（`score_7` 必须带下划线）。
3. Gelbooru 与 Danbooru 标签写法不同时，**优先 Gelbooru 版本**。
4. 官方推荐正向：`masterpiece, best quality, score_7, safe, `
5. 官方推荐负向：`worst quality, low quality, score_1, score_2, score_3, artist name, blurry, jpeg artifacts, chromatic aberration`
6. **提示词权重可用，但需要比 SDXL 更高的数值**：例 `(chibi:2)`。
7. 模型用**随机标签丢弃（tag dropout）**训练——不必（也不应）堆齐所有相关标签，漏掉部分标签不影响出图。
8. 画师标签**必须加 `@` 前缀**，否则效果极弱：`@nnn yryr`。
9. 纯自然语言时：**描述越细越好，至少 2 句**；过短的提示词会得到意外结果。
10. 角色要有"名字 + 外观描述"：`Digital artwork of Fern from Sousou no Frieren, with long purple hair and purple eyes, ...`；
    **多角色时尤其重要**，只堆角色名不加外观描述会让模型混淆。
11. 质量 / 画师标签可以放在自然语言提示词的最前面。
12. 写实不是它的强项——不要把它当摄影模型（除非用户明确要求"照片感的动漫渲染"）。

### 高杠杆规则（先看这 7 条，决定画面质感上限）

> 这几条是"同一段需求、出图质感差一档"的主因，来自官方模型卡与官方社区共识。
> **它们比堆砌质量词重要得多，动手写提示词前先过一遍。**

**1. 画师标签必选（第一杠杆）**

基础提示词里**必须有 1 个带 `@` 的主画师**。没有画师标签锚定，输出会落在平庸的默认风格里
（也就是常说的"AI 感"）。**用户没有指定画师时，由你自己挑一个与需求（媒介 / 年代 / 题材）最匹配的
知名画师**，不要留空、也不要退回纯风格词。

- 画师权重从 `(@artist name:2)` 起；**只写 1 个最稳，最多 1~2 个**；
- Anima 用 Qwen3 作文本编码器（不是 SDXL 的 CLIP），会**上下文式**处理所有 token，
  多个画师名同时出现会让嵌入互相污染——这就是"多画师 = 高风险操作"的原因；
- 画师名要写对拼写。确实拿不准拼写时，才退回媒介 / 线条 / 上色 / 配色 / 年代五槽风格词
  （见 `anima-prompt-artist`）。

**2. 权重数值要比 SDXL 大一档**

官方原文：`(chibi:2)`。

- **常规强调 `(tag:2)` 起**；**强强调 `(tag:3)` ~ `(tag:5)`**；
- 用户给了 `1.2` 这类小数时，**一律放大到 2~5 区间**再写进提示词；
- 照抄 SDXL 的数值，只会得到"权重好像没什么用"的错误结论；
- 不要用嵌套括号代替数值（`((tag))` 不如 `(tag:2)` 可控）。

**3. 权重标签总数 ≤4，优先给取景 / 角度**

权重是稀缺资源。一段提示词里**带权重的标签总数不超过 4 个**，优先分给最容易被自然语言带跑的
取景与角度标签（见第 4 条）。

**4. 取景对抗自然语言漂移（最常被忽略的一条）**

一旦自然语言层开始描述环境，模型会**把镜头拉远**，直接忽略 `close-up` / `upper body` / `portrait`。
三步对抗：

1. 给取景标签**加强权重**：`(upper body:2)`、`(close-up:3)`；
2. 自然语言**首句**就把取景说死（`The composition is a tight close-up portrait…`）；
3. 仍然拉远就继续加：`(upper body:5)` 甚至 `(upper body:7)`。角度标签同理（`(low angle:2)`、
   `(dutch angle:3)`），并可在首句补一句视角描述。

**5. Hybrid 三层结构（官方最优解）**

| 层 | 内容 | 作用 |
|---|---|---|
| Hard Tags | 经 Booru 确认的离散标签：质量 / 年代 / 安全、人数、角色、作品、画师、已确认的外观服装道具 | 结构与精度 |
| Soft Phrases | 短视觉短语：`having fun`、`strong wind`、`cherry blossom blizzard` | 动作 / 情绪 / 环境效果 |
| NL Caption | 1~3 句稠密英文，整合氛围、空间关系、光影 | 影响力**远强于**标签 |

纯标签结构精确但画面扁平；纯自然语言细节丰富，但超过 2~3 段结构就崩。**三层混合最稳**，
并且**同一语义不跨层重复**——构图标签已经写了 `close-up`，自然语言里就不要再写一遍 `close-up`，
改用叙事强化。

**6. 因果链：动作与天气都要落到可见后果**

- 每个关键动作必须产生至少一个**可见结果**（头发飘动、衣物受力、扬尘、地面碎裂）；
- 天气 / 季节不能只写一个标签，要落到物理状态：不要只写 `rain`，要写
  `rain, wet clothes, splashing water, puddle, dark sky`；
- 环境事件必须影响角色、道具、服装、头发、表情或构图层次，否则它只是一个装饰词。

**7. 优化优先级（收益从高到低）**

| 优先级 | 优化项 | 核心手段 |
|---|---|---|
| 1 | **画师标签** | 必须 1 个带 `@` 的主画师；多画师限 1~2 个 |
| 2 | **光影与氛围** | 在自然语言层写 `rim light`、`volumetric god rays` 等 |
| 3 | **混合结构** | Hard Tags + Soft Phrases + NL Caption 三层分离 |
| 4 | **取景控制** | 取景 / 角度标签加权，对抗自然语言漂移 |
| 5 | 细节纹理 | `hatching`、`impasto` 等纹理标签或 Detail Tweaker LoRA |
| 6 | 多人分离 | 按角色分组排列属性 + 空间方位词 |
| 7 | 标签校订 | 失效标签改用自然语言补充描述 |
| 8 | 质量标签 | 按第 1 节的版本差异选前缀 |

**核心原则：在 Anima 里，"让模型知道要模仿谁"比"告诉模型要画得好看"有效得多**——
画师标签与光影的收益，远大于堆砌质量词与细节词。

## 3. 标签顺序（官方）

```text
[quality/meta/year/safety 标签] [1girl/1boy/1other 等人数标签] [character 角色] [series 作品] [artist 画师] [general 通用标签]
```

**每个区段内部的标签顺序可以任意**，但**区段之间的先后关系要遵守**。

各段可用标签：

| 段位 | 标签 |
|---|---|
| quality（人类评分） | `masterpiece` `best quality` `good quality` `normal quality` `low quality` `worst quality` |
| quality（PonyV7 美学模型） | `score_9` `score_8` … `score_1`（**带下划线**） |
| 时间 | 具体年：`year 2025` `year 2024`…；时期：`newest` `recent` `mid` `early` `old` |
| meta | `highres` `absurdres` `anime screenshot` `jpeg artifacts` `official art` 等 |
| safety | `safe` `sensitive` `nsfw` `explicit` |
| 人数 | `1girl` `1boy` `1other` `2girls` `multiple girls` `solo` `group` 等 |

> 质量标签可以只用人类评分、只用美学评分、两者都用、或都不用——**各种组合都有效**。

## 4. 官方完整标签示例

```text
year 2025, newest, normal quality, score_5, highres, safe, 1girl, oomuro sakurako, yuru yuri, @nnn yryr, smile, brown hair, hat, solo, fur-trimmed gloves, open mouth, long hair, gift box, fang, skirt, red gloves, blunt bangs, gloves, one eye closed, shirt, brown eyes, santa costume, red hat, skin fang, twitter username, white background, holding bag, fur trim, simple background, brown skirt, bag, gift bag, looking at viewer, santa hat, ;d, red shirt, box, gift, fur-trimmed headwear, holding, red capelet, holding box, capelet
```

## 5. 自然语言提示词要点

- 角色名、作品名**遵循标准英文大小写**（`Fern`、`Sousou no Frieren`）。
- 写"最终画面"而不是"生成过程"；不要出现 `or` / `maybe` / `could be` 这类备选表述。
- 角色细节写在一起、背景细节写在一起，用空间词（`left/right/center/foreground/middle ground/background`）定位。
- 不要自相矛盾（如 `photorealistic documentary photograph, flat anime cel shading` 同时出现）。

## 6. dataset tag（数据集标签，进阶）

为提升风格与题材多样性，Anima 额外训练了两个**非动漫**数据集（LAION-POP 的 ye-pop 版、DeviantArt，均已过滤照片）。
这两个数据集的 caption 带"数据集标签"，**固定放在提示词最开头并换行**，第二行可选放 alt-text（ye-pop）或作品标题（DeviantArt）：

```text
ye-pop
For Sale: Others by Arun Prem
Abstract, oil painting of three faceless, blue-skinned figures. Left: white, draped figure; center: yellow-shirted, dark-haired figure; right: red-veiled, dark-haired figure carrying another. Bold, textured colors, minimalist style.
```

```text
deviantart
Flame
Digital painting of a fiery dragon with glowing yellow eyes, black horns, and a long, sinuous tail, perched on a glowing, molten rock formation. The background is a gradient of dark purple to orange.
```

> 只有在用户明确要"非动漫风格 / 概念艺术 / 抽象绘画"时才考虑用 dataset tag；动漫插图**不要**乱加。

## 7. 官方生成参数（**不属于 skill 输出，数值不写进任何交付内容**）

> ⚠️ 生成参数属于 **ComfyUI 工作流设置**，不写进提示词，也**不要**在交付内容里附
> `Suggested settings` 段或给出任何数值。需要参数参考时请查官方模型卡与 ComfyUI 教程，
> 不要在提示词交付里转述。

- 采样器 / 调度器、步数、CFG、分辨率、宽高比、种子：**全部属于工作流侧**；
- 提示词交付物里只允许出现提示词正文（或用户明确要负面词时的 `Negative prompt` 段）。

## 8. 能力边界（写提示词时必须避坑）

- **不做写实**：写实渲染超出范围，会得到塑料感 / 崩坏结果。
- **文字渲染弱**：能出单个词，偶尔短句；**长文本必然崩**——需要长文字时改用后期加字。
- **Base 版默认风格朴素**：不写画师标签 / 质量标签时画面会很"平"。
- **短提示词会出意外内容**：明确内容需求时，用足够详细的描述 + 恰当 safety 标签约束。

## 9. 来源

- 模型卡：<https://huggingface.co/circlestone-labs/Anima>
- ComfyUI 官方教程（Anima Base v1）：<https://docs.comfy.org/tutorials/image/anima/anima>
- 社区工作流参考（质量前缀与 LoRA 栈、采样器组合）：<https://github.com/ShiroEirin/comfyui-good-anima>
- 社区提示词工程参考（分层写法与 Regional / inpaint 模板）：<https://github.com/AI-KSK/anima-prompt-crafter-skill>
