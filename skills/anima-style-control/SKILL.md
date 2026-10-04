---
name: anima-style-control
description: Choose and enforce one explicit art style, medium and rendering technique for Anima prompts, covering cel shading, painterly, manga screentone, retro anime, 2000s anime, game CG, key visual, watercolor, ink and chibi. Use for Anima Base / Aesthetic / Turbo text-to-image prompts in ComfyUI when the look drifts between generations or the style is still undecided.
version: 1.1.0
---

# Anima 风格控制（Style Control）

Anima 在风格上是"泛二次元"模型：**你不指定风格，它每次都会自己挑一个**，而且大概率每次都不一样。
风格控制要解决的就是这件事——从媒介（medium）、渲染（rendering）、年代（era）、格式（format）
四个轴上各选一个，拼成**一个主导风格串**，然后在整批生成里逐字复用。

写风格之前先确认标签语法：标签全小写、多词用空格、画师标签必须带 `@`、权重需要比 SDXL **大得多**
（常规 `(painterly:2)` 起，强强调 `:3~5`）。这些硬规则见 `anima-prompt-format` 的
`references/anima-prompt-baseline.md`。

读 `references/anima-style-taxonomy.md` 获取完整风格分类表（含每个标签的 "use when / avoid when"）
与批量锁风格配方。本文件只给决策流程。

## 输出契约

默认**只输出一条正面提示词**（风格锁定后的正文）；仅在用户明确要求负面词时，才追加 `Negative prompt` 段：

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

## 工作流

### 1. 先判断风格是否已经确定

- 用户给了明确的风格词（赛璐璐、厚涂、水墨、网点、90 年代赛璐璐、游戏 CG）→ 直接进入第 2 步；
- 用户只给了题材（"画个剑士"）→ **由你选**，但选完要锁死，不要给"或 A 或 B"的备选；
- 用户要的是"更好看/更精致"而不是"换风格" → 这是风格增强，交给 `anima-style-boost`；
- **一条提示词只能有一个主导风格**。第二风格只允许作为**辅助质感**出现一次
  （例如 `watercolor` + `visible paper texture`），两个平级媒介会互相打架。

### 2. 在四个轴上各选一个

| 轴 | 可选值（英文标签） | 作用 |
|---|---|---|
| 媒介 medium | `digital painting` `watercolor` `ink` `sumi-e` `colored pencil` `pastel` `gouache` `charcoal` `pencil sketch` `vector art` `pixel art` `3d cg` `game cg` `screentone` `manga` `monochrome` | 决定"这是用什么画的" |
| 渲染 rendering | `cel shading` `flat color` `soft shading` `painterly` `thick outlines` `clean lineart` `lineless` `airbrush` `gradient shading` `chiaroscuro` `halftone` `impasto` | 决定明暗与线条的处理方式 |
| 年代 era | `newest` `recent` `mid` `early` `old` + `year 2025`…`year 2005` | 决定"像哪个时代的作品" |
| 格式 format | `official art` `anime screenshot` `key visual` `promotional art` `character sheet` `reference sheet` `manga cover` `poster` `illustration` | 决定"这是哪一类图" |

四轴组合示例：`digital painting + painterly + year 2013/mid + key visual`＝2010 年代游戏宣传 KV；
`screentone + clean lineart + old + manga cover`＝老式漫画封面。

### 3. 用年代与 meta 标签调色（最容易被忽略的一步）

- 年代：`newest`/`year 2025` → 高光锐利、渐变丰富、数字感强；`mid`/`year 2013` → 半厚涂、
  柔和渐变、边缘略脏；`old`/`early`/`year 2005` → 赛璐璐平涂、少量颜色、颗粒与偏色。
- meta：`anime screenshot` 会把画面推向"电视动画截图"（构图随意、线条偏简、分辨率感偏低）；
  `official art` 推向"官方立绘"（干净、中心构图、修饰过）；`highres` / `absurdres` 推向高细节，
  与 `old`、`sketch`、`pixel art` 的意图**相反**。
- 年代标签和 meta 标签**一起改**才有效，只改一个会出现"2025 年的线条 + 2005 年的配色"这种撕裂感。

### 4. 把风格标签放到正确区段

按官方区段顺序：`[quality/meta/year/safety] [人数] [角色] [作品] [画师] [general]`。

- 年代 / meta / 质量 / safety → 全部进第一个区段（`year 2005, early, normal quality, safe, ...`）；
- 媒介与渲染 → 放进 general 区段（画完主体与服装之后），或写在自然语言区里；
- 画师标签 → 独立区段，带 `@`（`@nnn yryr`）。**用户没给画师名就不要编造**，
  编错画师名会直接毁掉风格；需要画师风格请走 `anima-prompt-artist`；
- 区段内顺序随意，但区段之间不要乱。

### 5. 冲突检查（写完风格串后必做）

| 冲突组合 | 为什么冲突 | 处理 |
|---|---|---|
| `painterly` + `flat cel shading` / `cel shading` | 一个要笔触与过渡，一个要硬边平涂 | 只留一个主导渲染 |
| `photorealistic` / `photograph` + 任意动漫标签 | Anima 不做写实，会出塑料感 | 删掉写实词（写实越界见基准文件第 8 节） |
| `monochrome` / `greyscale` + `vibrant colors` | 直接互斥 | 二选一 |
| `lineless` + `thick outlines` | 一个没有线，一个强调线 | 只留一个 |
| `screentone` + `full color` | 网点是黑白/单色语言 | 要么 `monochrome screentone`，要么放弃网点 |
| `3d cg` + `screentone` | 三维渲染与手绘网点不共存 | 二选一 |
| `chibi` + `realistic proportions` / `tall` | 头身比互斥 | 用 `chibi` 就别写比例词 |
| `old` / `year 2005` + `absurdres, newest` | 年代意图与清晰度意图相反 | 年代与清晰度对齐 |
| `sketch` + `flat color` / `finished` | 草稿语言与成品上色冲突 | 明确要草稿就删上色词 |

### 6. 用明确描述做风格迁移，而不是点名真人画师

用户说"要像某某的画风"时：

1. **不要**写 `in the style of <在世画师姓名>`，也**不要**自己编造画师标签；
2. 把风格拆成可命名的技术特征：线条（`clean lineart` / `rough sketch lines`）、
   上色（`cel shading` / `painterly` / `watercolor wash`）、色彩（`muted colors` / `high contrast` /
   `pastel palette`）、光影（`hard shadows` / `soft rim light` / `chiaroscuro`）、
   质感（`paper texture` / `canvas texture` / `grain`）；
3. 用户自己提供了画师名 → 加 `@` 前缀原样使用，并交给 `anima-prompt-artist` 处理混合与权重；
4. 只是要"某个年代的氛围" → 用年代 + meta 标签，比点名更稳。

### 7. 锁风格（批量 / 系列图）

同一批图要看起来像同一部作品，靠的是**固定风格串 + 固定区段位置**：

- 把质量/meta/年代/safety 段和风格段**逐字复制**，每一张都不许改；
- 每次只改主体区段（角色、服装、动作）与自然语言描述；
- 批量时**不要**在两次生成之间换采样器或 CFG（那属于工作流侧参数，不写进提示词），
  否则线稿与色彩的落点会变；
- 角色本身的一致性交给 `anima-prompt-character`；画师权重微调交给 `anima-prompt-artist`。

### 8. 交付前自检（静默）

- 是不是只有**一个**主导风格？有没有两个平级媒介并列？
- 年代与 meta 是否互相支持，而不是互相拆台？
- 风格标签是否落在正确区段？画师是否带 `@`？是否**没有**编造画师名？
- 冲突表里有没有中招的组合？
- 用户原有的主体、文字内容与约束是否一字未动？
- 输出里是否只有 `Positive prompt` / `Negative prompt` 两段？

## 示例

输入：`想要 2010 年代游戏 CG 风格的剑士宣传图，厚涂一点，别写实`

```text
Positive prompt
year 2013, mid, masterpiece, best quality, safe, 1boy, solo, male focus, armor, cape, sword, standing, game cg, digital painting, painterly, semi-realistic shading, thick brush strokes, detailed armor, rim light, embers, depth of field, promotional art, key visual, highres. A mid-2010s game-CG promotional illustration of a lone armored swordsman standing at a cliff edge, painted with visible thick brush strokes and layered semi-realistic shading instead of flat cel colors, cold blue rim light along his pauldrons while warm embers drift past his cape, framed as a vertical key visual with the figure dominant in the center and the landscape falling away behind him.

Negative prompt
worst quality, low quality, lowres, blurry, jpeg artifacts, cel shading, flat color, screentone, photograph, photorealistic, live action, 3d render, bad anatomy, bad hands, extra fingers, missing fingers, extra limbs, deformed, duplicate face, messy lineart, watermark, signature, username, logo, unrelated text
```

风格串拆解（仅作讲解，不属于输出）：`year 2013, mid` 定年代，`game cg, digital painting, painterly,
semi-realistic shading, thick brush strokes` 定媒介与渲染，`promotional art, key visual` 定格式，
自然语言里用 `instead of flat cel colors` 明确排除对手风格，负面里把 `cel shading, flat color,
photorealistic` 三件事堵住——注意 `3d render` 只在与 `game cg` 的厚涂方向冲突时才放负面。

## 边界

- 标签顺序、大小写、权重语法、质量前缀本身有问题 → 交给 `anima-prompt-format`；
- 画师风格混搭、画师权重、`@` 标签策略 → 交给 `anima-prompt-artist`；
- 风格已定，只是想让它更精致（线稿、上色层次、配色、光照、背景密度）→ 交给 `anima-style-boost`；
- 角色身份、多视图一致性、系列图里的角色不变 → 交给 `anima-prompt-character`；
- 景别、机位、前中后景、留白布局 → 交给 `anima-composition-optimize`；
- 负面词整体策略（不只风格冲突类）→ 交给 `anima-prompt-negative`；
- 分区上色 / 局部重绘里的风格一致性 → 交给 `anima-prompt-regional`；
- LoRA 自带风格、需要写触发词 → 交给 `anima-lora-trigger`；
- 采样器 / 步数 / CFG / 分辨率属于**工作流侧参数**，不写进提示词，也不在输出里给数值；
- 用户要求写实照片 → 先说明 Anima 不做写实（除照片感动漫渲染），再决定是否改写需求。
