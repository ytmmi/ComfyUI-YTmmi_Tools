---
name: anima-prompt-artist
description: Write Anima artist tags correctly (`@artist` is mandatory, otherwise the effect is very weak), anchor a single-artist style, mix two or three artists by weight, and describe a style safely without any artist name. Use when an Anima prompt needs a specific artist style, when a user-supplied artist name seems to be ignored, when two artists must be blended into one coherent look, or when the user has no artist in mind and only wants to describe a style.
version: 1.0.0
---

# Anima 画师标签与混合（Artist Tags & Mixing）

Anima 的画师标签是**最强的单一风格杠杆**：一个画师标签带来的画风变化，通常大过一堆质量词。
代价是它有两个硬约束——**必须带 `@` 前缀**，以及**只能用用户给的画师名**。

读共同基准 `anima-prompt-format/references/anima-prompt-baseline.md` 拿官方标签顺序与权重语法，读
`references/anima-artist-mixing.md` 拿权重写法、混合配方、发运前清单与反模式列表。
本文件讲决策。

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
| 用户明确给出画师名 | 直接用，加 `@`，按官方顺序放好 |
| 用户给了参考图 / 已有提示词 | 只沿用其中**已经出现**的 `@` 画师名，不要补写新的 |
| 用户只说"某某番的画风" | 那是作品/年代取向，不是画师名；用 `[作品]` 段或时代词表达 |
| 用户没说画师 | **不编**。走第 6 步的"无画师名风格描述" |

**绝不猜、绝不编画师名。** 具体危害：Anima 的画师标签是强条件，写错一个真实画师名，
画面会被强行拉去**那个人的风格**，你原本要的风格全部被盖掉；而且它看起来像"模型不听话"，
排查时会浪费大量时间在角色、权重、负面词上。此外把真人风格署名到不是他画的风格上也有署名问题。

### 2. 数量决策

| 画师标签数 | 定位 | 说明 |
|---|---|---|
| 1 | **最稳**，默认选择 | 风格方向明确、可复现 |
| 2~3 | 刻意的混合 | 需要权重分工，见第 5 步 |
| 4~9 | 一般不推荐 | 每个标签贡献被稀释，风格互相抵消，出图随机性骤增 |
| 10+ | 仅"画师混合实验" | 只在用户明确说要大杂烩时做，并说明结果不可控 |

数量越少越可控；**1 个强画师标签 + 准确的构图/角色词**，效果通常好过 5 个画师标签互相打架。

### 3. 记住 `@`（最容易漏的一条）

- 正确：`@artist a`；错误：`artist a`、`by artist a`、`artist: a`、`@Artist A`；
- `@` 之后**照抄用户给的名字书写**（Danbooru 画师名多为小写空格分词）；
- 漏掉 `@` 的表现是"风格几乎没变化"——先检查这一条，再怀疑版本、权重或负面词。

### 4. 权重：Anima 要更大的数

Anima 的权重可用，但**需要比 SDXL 更高的数值**（官方例：`(chibi:2)`）。

| 写法 | 实际效果 |
|---|---|
| `@artist a` | 基准 |
| `(@artist a:1.2)` | 轻微加强，肉眼几乎无差 |
| `(@artist a:1.4)` | **常用档**，明显主导画面风格 |
| `(@artist a:1.6)` ~ `(@artist a:2.0)` | 强主导，其他标签开始被压 |
| `(@artist a:2.5+)` | 结构崩坏风险明显上升 |

- 用显式数值，不要写 `((@artist a))` 这种嵌套括号——Anima 需要的是**更大的数**，不是更多层括号；
- 多词标签要**整段包进括号**：`(@artist a:1.4)`，不要 `@(artist a):1.4`。

### 5. 混合两个画师：要"一个融合的风格"，不是"两个风格抢地盘"

三条可操作规则：

1. **分主次**：主导 `1.3~1.5`，陪衬 `0.8~1.0`（低于 1 是把它的特征往回拉）；
2. **写清融合目标**：自然语言里点名要继承谁的什么——"keep the soft watercolor shading of the dominant
   style while borrowing crisp thin lineart from the accent style"（用**特征**描述，不要复述人名）；
3. **别混对立极端**：超精细厚涂 + 极简平涂、赛璐璐 + 油画，混出来通常是糊的；
   选年代、媒介、线条习惯接近的两个画师，融合才稳定。

### 6. 没有画师名时：用风格词描述（并交给 `anima-style-control`）

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

- **强画师标签让质量词堆积变得没必要**：有了 `(@artist a:1.4)`，先把 `score_*`、`very aesthetic`
  这类堆料撤掉做 A/B；很多时候撤掉更干净、也更省 token（Anima 有随机标签丢弃，省下的位置给角色）；
- **画师标签会与风格 LoRA 抢方向盘**：LoRA 也是风格条件。若挂了**风格 LoRA**，画师标签最多留 1 个
  并且降到 `1.0~1.2`，或者干脆不用；若挂的是**角色 LoRA**，画师标签可以正常用，但别让画师风格把
  LoRA 学到的脸压走；LoRA 触发词写法交 `anima-lora-trigger`；
- **负面里的 `artist name`**（官方默认负面里就有）会**压制画师标签效果**。要画师风格时必须删掉它，
  这是"加了画师标签却没效果"的第二大原因（第一大是漏 `@`）。

### 8. 自检（静默）

- 每个画师名都来自用户、且都带 `@`？
- 数量是否 ≤3（除非用户明确要实验）？
- 混合是否有明确主次权重，并写清融合目标？
- 负向是否已删 `artist name`？
- 是否没有把 `score_*` 与强画师标签一起无脑堆着？
- 画师标签是否在 artist 位（角色、作品之后，general 之前）？
- 正文里有没有混进 LoRA 文件名、模型名、参数？

## 示例

> 示例中的 `@artist a` / `@artist b` 是**占位符**，交付时替换为用户实际提供的画师名；
> 本 skill 不提供、也不猜任何真实画师名。

输入：`用 @artist a 的风格画一张雨中撑伞的少女`

```text
Positive prompt
masterpiece, best quality, safe, 1girl, solo, @artist a, black hair, medium hair, white dress, holding umbrella, rain, night city street, cowboy shot, depth of field, wet asphalt reflections, neon signs. A girl in a white dress holds an umbrella on a rain-soaked night street, wet asphalt mirroring the neon signs around her, the whole frame painted with the soft, clean look the artist tag pulls in.

Negative prompt
worst quality, low quality, lowres, blurry, jpeg artifacts, bad anatomy, bad hands, extra fingers, missing fingers, extra limbs, deformed, messy lineart, watermark, signature, username, logo
```

（注意负向里**没有 `artist name`**——它会把刚加的画师风格压掉。）

输入：`把 @artist a 和 @artist b 混起来，想要前者的柔和上色加后者的锐利线条`

```text
Positive prompt
masterpiece, best quality, safe, 1girl, solo, (@artist a:1.4), (@artist b:1.0), silver hair, long hair, blue eyes, military uniform, standing, looking at viewer, upper body, simple background. A single coherent illustration that keeps the soft watercolor shading and muted palette of the dominant style while borrowing crisp thin lineart from the accent style, the two influences blended into one consistent drawing rather than two styles competing.

Negative prompt
worst quality, low quality, lowres, blurry, jpeg artifacts, bad anatomy, bad hands, fused fingers, extra limbs, deformed, inconsistent style, messy lineart, watermark, signature, username, logo
```

（主次从权重上就能读出来：1.4 定基调，1.0 只提供线条特征；自然语言点名要融合的**特征**，
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
