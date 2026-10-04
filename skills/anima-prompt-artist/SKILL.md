---
name: anima-prompt-artist
description: Write Anima artist tags correctly (`@artist` is mandatory, otherwise the effect is very weak), anchor a single-artist style, mix two or three artists by weight, and describe a style safely without any artist name. Use when an Anima prompt needs a specific artist style, when a user-supplied artist name seems to be ignored, when two artists must be blended into one coherent look, or when the user has no artist in mind and only wants to describe a style.
version: 1.1.0
---

# Anima 画师标签与混合（Artist Tags & Mixing）

Anima 的画师标签是**最强的单一风格杠杆**：一个画师标签带来的画风变化，通常大过一堆质量词。
官方社区共识是"基础提示词里**必须有一个主画师**"——没有它，输出会落在平庸的默认风格里
（也就是常说的"AI 感"）。

它有两条硬约束：**必须带 `@` 前缀**（否则效果极弱），以及**必须挑一个与画面风格匹配的画师**。
用户给了画师名就照用；**用户没给时，由你按媒介 / 年代 / 题材自己挑一个最匹配的知名画师**，
不要留空、也不要直接退回纯风格词（风格词是最后的兜底，见第 6 步）。

读共同基准 `anima-prompt-format/references/anima-prompt-baseline.md` 拿官方标签顺序与权重语法，读
`references/anima-artist-mixing.md` 拿权重写法、混合配方、发运前清单与反模式列表。
本文件讲决策。

> 取景对抗漂移、权重预算（全文 ≤4 个加权标签）、Hybrid 三层结构、因果链等高杠杆规则，
> 见 `anima-prompt-format` 的「高杠杆规则」一节与共同基准；本文件只专攻画师这一层。

## 输出契约

默认**只输出正面提示词**；用户明确要负面词时，才在后面追加 `Negative prompt` 段：

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

- 要画师风格时提醒用户：负面里删掉 `artist name`（示例仍按两段演示）。

## 工作流

### 1. 先确认画师名从哪来

| 来源 | 处理 |
|---|---|
| 用户明确给出画师名 | 直接用，加 `@`，按官方顺序放好，权重 `:2` 起 |
| 用户给了参考图 / 已有提示词 | 沿用其中**已经出现**的 `@` 画师名；一个都没有时按下一行处理 |
| 用户只说"某某番的画风" | 那是作品 / 年代取向：可以同时用 `[作品]` 段或时代词，**但主画师仍要自己挑一个** |
| 用户没说画师 | **必选**：按媒介 / 年代 / 题材自己挑一个最匹配的知名画师（见下面的原则） |

**用户没给画师时，主画师这一格也必须填满。** 这是本 skill 最重要的一条：留空不是"保守"，
而是直接放弃了画质的第一杠杆，输出会明显平庸。

挑画师的原则：

1. **按媒介 / 题材匹配**：水彩、厚涂、赛璐璐、黑白漫画、像素、恐怖、机甲……先想"谁以这种画法出名"；
2. **按年代匹配**：需求提到老番质感就用那个年代的画师，不要拿当下的精细数字风格去画复古需求；
3. **优先知名度高、覆盖面广的画师**：这类名字在 Danbooru 上样本足、效果稳定，比冷门名字安全；
4. **写对拼写**：宁可选一个你有把握写对的，也不要凭印象拼一个冷门名字；
5. **确实拿不准就退回风格词**（见第 6 步）：改用媒介 / 线条 / 上色 / 配色 / 年代五槽描述，
   并在交付时说明"这次没用画师标签"。

> 为什么"猜错画师会盖掉风格"不能成为不挑画师的理由：写错画师确实会把画面拉去那个人的风格，
> 但**留空同样有确定代价**——落到默认的平庸风格。正确做法是**挑一个风格对路、又有把握写对的**。
> 选人时避开明显错配（把以黑白漫画出名的画师署名到全彩水彩需求上），就同时避开了质量问题与署名问题。

### 2. 数量决策

| 画师标签数 | 定位 | 说明 |
|---|---|---|
| 1 | **最稳**，默认选择 | 风格方向明确、可复现；官方社区推荐的基础配置 |
| 2 | 刻意的混合 | 需要权重分工，见第 5 步；这时开始出现嵌入互相污染 |
| 3 | 高风险 | 只在用户明确要求三方融合时做，并说明结果不可控 |
| 4+ | 不推荐 | 每个标签贡献被稀释，风格互相抵消，出图随机性骤增；除非用户明确要大杂烩实验 |

数量越少越可控；**1 个强画师标签 + 准确的构图/角色词**，效果通常好过 5 个画师标签互相打架。

### 3. 记住 `@`（最容易漏的一条）

- 正确：`@artist a`；错误：`artist a`、`by artist a`、`artist: a`、`@Artist A`；
- `@` 之后**照抄用户给的名字书写**（Danbooru 画师名多为小写空格分词）；
- 漏掉 `@` 的表现是"风格几乎没变化"——先检查这一条，再怀疑版本、权重或负面词。

### 4. 权重：Anima 要更大的数（最容易写小的一步）

Anima 的权重可用，但**需要比 SDXL 显著更高的数值**（官方例：`(chibi:2)`）。

| 写法 | 实际效果 |
|---|---|
| `@artist a` | 基准 |
| `(@artist a:1.2)` | **偏弱**，画师特征只是隐约出现（SDXL 里这档通常已经够用） |
| `(@artist a:2.0)` | **常规起点**——官方推荐的主画师档，风格明显主导画面 |
| `(@artist a:3.0)` ~ `(@artist a:4.0)` | 强强调，其他风格与细节标签开始被压 |
| `(@artist a:5.0)` | 极强，构图与细节可能被一起改写 |
| `(@artist a:0.8)` | 低于 1，是把它当"点缀"往回拉（用于混合时的陪衬） |

- **`2` 才是常用档，不是 `1.4`。** 照抄 SDXL 的 `1.1` / `1.2`，只会得出"画师标签好像没用"的结论；
- 用户给了 `1.2` 这类小数时，**放大到 2~5 区间**再写进提示词；
- 用显式数值，不要写 `((@artist a))` 这种嵌套括号——Anima 需要的是**更大的数**，不是更多层括号；
- 多词标签要**整段包进括号**：`(@artist a:2)`，不要 `@(artist a):2`；
- 权重标签全文**不超过 4 个**：画师通常占掉 1 个，剩下的优先留给取景 / 角度（见共同基准第 4 条）。

### 5. 混合两个画师：要"一个融合的风格"，不是"两个风格抢地盘"

三条可操作规则：

1. **分主次**：主导 `2.0~3.0`，陪衬 `1.0~1.5`（相对主画师压低；低于 1 是把它的特征往回拉）；
2. **写清融合目标**：自然语言里点名要继承谁的什么——"keep the soft watercolor shading of the dominant
   style while borrowing crisp thin lineart from the accent style"（用**特征**描述，不要复述人名）；
3. **别混对立极端**：超精细厚涂 + 极简平涂、赛璐璐 + 油画，混出来通常是糊的；
   选年代、媒介、线条习惯接近的两个画师，融合才稳定。

### 6. 兜底：实在挑不出画师时，用风格词描述（并交给 `anima-style-control`）

**这是最后的兜底，不是默认路径。** 只有在第 1 步确实挑不出一个有把握的画师时才走这里，
并且要在交付时说明"这次没用画师标签"。

按五个槽位各取 1~2 个词，就能得到比"in the style of …"更可控的方向：

| 槽位 | 英文词示例 |
|---|---|
| 媒介 medium | `digital painting`, `watercolor`, `oil painting`, `cel shading`, `flat color`, `sketch`, `ink drawing` |
| 线条 linework | `clean lineart`, `thin lineart`, `thick outlines`, `sketchy lineart`, `no lineart` |
| 上色 shading | `soft shading`, `hard shading`, `flat color`, `gradient shading`, `dappled light` |
| 配色 palette | `muted colors`, `pastel colors`, `high contrast`, `monochrome`, `sepia`, `vibrant colors` |
| 时代 era | 年份标签（`year 2014`）或时期标签（`early` / `mid` / `recent` / `newest`）、`retro artstyle` |

> 不要用"感觉像某人的风格"这种模糊自然语言来绕过画师标签——模型没有这个中间概念，
> 效果不如老老实实写媒介 + 线条 + 上色 + 配色 + 年代。

### 7. 与质量前缀、LoRA 的关系

- **强画师标签让质量词堆积变得没必要**：有了 `(@artist a:2)`，先把 `score_*`、`very aesthetic`
  这类堆料撤掉做 A/B；很多时候撤掉更干净、也更省 token（Anima 有随机标签丢弃，省下的位置给角色）；
- **画师标签会与风格 LoRA 抢方向盘**：LoRA 也是风格条件。若挂了**风格 LoRA**，画师标签最多留 1 个
  并且降到 `1.0~1.5`，或者干脆不用；若挂的是**角色 LoRA**，画师标签可以正常用，但别让画师风格把
  LoRA 学到的脸压走；LoRA 触发词写法交 `anima-lora-trigger`；
- **负面里的 `artist name`**（官方默认负面里就有）会**压制画师标签效果**。要画师风格时必须删掉它，
  这是"加了画师标签却没效果"的第二大原因（第一大是漏 `@`）。

### 8. 自检（静默）

- **有没有落下主画师**（用户没给时，是否自己挑了一个风格对路的）？这是最容易漏、影响最大的一条；
- 每个画师标签是否都带 `@`、拼写是否有把握？
- 数量是否 ≤2（刻意混合时）？有没有意识到多画师会互相污染嵌入？
- 权重是否用了 Anima 档位（主画师 `:2` 起），而不是 SDXL 的 `1.1` / `1.4`？
- 全文加权标签是否 **≤4 个**？
- 混合是否有明确主次权重（主导 `2.0~3.0` / 陪衬 `1.0~1.5`），并写清融合目标？
- 负向是否已删 `artist name`？
- 画师标签是否在 artist 位（角色、作品之后，general 之前）？
- 正文里有没有混进 LoRA 文件名、模型名、参数？

## 示例

> 示例中的 `@artist a` / `@artist b` 是**占位符**，交付时替换成真实存在的画师名：
> 用户给了就用用户的；**用户没给就由你按媒介 / 年代 / 题材挑一个，并核对拼写**。
> 本 skill 不列候选名单，也不提供任何"风格 → 画师"的固定映射。

输入：`用 @artist a 的风格画一张雨中撑伞的少女`

```text
Positive prompt
masterpiece, best quality, safe, 1girl, solo, (@artist a:2), (cowboy shot:2), black hair, medium hair, white dress, holding umbrella, rain, night city street, wet asphalt reflections, neon signs, depth of field. The composition is a tight cowboy shot: a girl in a white dress holds an umbrella on a rain-soaked night street, rain soaking the hem of her dress and splashing off the asphalt, the wet road mirroring the neon signs around her, painted with the soft, clean look the artist tag pulls in.

Negative prompt
worst quality, low quality, lowres, blurry, jpeg artifacts, bad anatomy, bad hands, extra fingers, missing fingers, extra limbs, deformed, messy lineart, watermark, signature, username, logo
```

（注意负向里**没有 `artist name`**——它会把刚加的画师风格压掉。）

输入：`把 @artist a 和 @artist b 混起来，想要前者的柔和上色加后者的锐利线条`

```text
Positive prompt
masterpiece, best quality, safe, 1girl, solo, (@artist a:3), (@artist b:1.5), (upper body:2), silver hair, long hair, blue eyes, military uniform, standing, looking at viewer, simple background. The composition is a tight upper body portrait that keeps the soft watercolor shading and muted palette of the dominant style while borrowing crisp thin lineart from the accent style, the two influences blended into one consistent drawing rather than two styles competing.

Negative prompt
worst quality, low quality, lowres, blurry, jpeg artifacts, bad anatomy, bad hands, fused fingers, extra limbs, deformed, inconsistent style, messy lineart, watermark, signature, username, logo
```

（主次从权重上就能读出来：`3` 定基调，`1.5` 只提供线条特征；自然语言点名要融合的**特征**，
而不是重复两个人名。）

## 边界

- 只要基础格式化、不涉及画师 → `anima-prompt-format`；
- 不用画师名、纯用媒介/线条/上色/配色/年代描述风格 → `anima-style-control`、`anima-style-boost`；
- 构图与画风的配合（海报要什么构图）→ `anima-composition-optimize`；
- 角色一致性（画师风格固定但角色跑了）→ `anima-prompt-character`；
- LoRA 触发词、LoRA 与画师标签的权重协商 → `anima-lora-trigger`；
- 负面词里该不该保留 `artist name`、质量前缀怎么选 → `anima-prompt-negative`；
- 分区提示词里不同区域用不同画风 → `anima-prompt-regional`；
- 用户想要多套风格方案对比 → `anima-prompt-optimize`。
