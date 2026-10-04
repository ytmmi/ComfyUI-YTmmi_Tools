---
name: anima-prompt-character
description: Keep one Anima character identical across a set of prompts and build multi-view, multi-expression or outfit-variant character sheets. Use when hair, eyes, outfit, silhouette and a signature accessory must stay stable across Anima renders, when a front/side/back turnaround or expression sheet is requested, or when several characters share one frame and must not merge or swap attributes.
version: 1.1.0
---

# Anima 角色一致性与三视图（Character Consistency & Character Sheet）

Anima 是 CircleStone Labs × Comfy Org 的 2B 二次元插画模型，**没有内置角色 ID**：一个角色长什么样，
只由提示词里那串词决定。所以"同一个角色"在 Anima 里只有一种可靠做法——把一段**逐字不变的身份锚点**
（identity anchor）原样复制进这一组图的每一条提示词。换同义词、换标签顺序、少写一个配件，
出来的就是另一个人。

读共同基准 `anima-prompt-format/references/anima-prompt-baseline.md` 拿硬规则（官方标签顺序、`@` 画师前缀、权重语法、版本前缀、
标签丢弃），再读 `references/anima-character-sheet-guide.md` 拿本 skill 的身份锚点模板、视角/表情/服装
词表、多角色归属配方和失败目录。本文件只讲工作流与判断。

## 输出契约

一组多视图 = **多条正面提示词**，每条前面加一行短标签（标签行不属于提示词正文）；默认**只输出正面**，用户明确要负面词时，才在整组末尾给一段共用的 `Negative prompt`：

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

- 负面词**仅在用户明确要求时**才追加（示例与角色表模板仍按两段演示）。

## 高杠杆规则（先看这 5 条；完整原文见 `anima-prompt-format/references/anima-prompt-baseline.md`）

> 多人同框时第 5 条最关键：Anima 在多人场景里**极易发生特征混淆**。

1. **画师标签必选**：正文里必须有 **1 个带 `@` 的主画师**，权重 `(@artist name:2)` 起，只 1~2 个
   （用户没给就自己挑一个风格对路的，别留空）；
2. **权重用大数**：常规 `(tag:2)` 起，强强调 `(tag:3)` ~ `(tag:5)`；用户给 `1.2` 这类小数要放大到 2~5；
3. **权重标签总数 ≤4**，多人场景优先给**易混淆特征**（`(blue hair:2), (red hair:2)`）；
4. **三层混合**：Hard Tags → Soft Phrases → NL Caption，**同一语义不跨层重复**；
5. **多人按角色分组**：详见下面第 4 步——属性**按角色分组连续写完再切换**，
   **严禁交叉排列**（`blue hair, red hair, short hair, long hair` 必然混）。

## 工作流

### 1. 先判定形态（静默完成，不输出这一步）

| 形态 | 判断依据 | 结构 |
|---|---|---|
| 单角色多图 | 同一角色，场景/姿势/表情在变 | 1 个锚点 + N 个场景块 |
| 转身表 / 三视图 | 要同一角色的正面/侧面/背面 | 1 个锚点 + N 个视角块，版式固定 |
| 表情表 | 同一角色同一构图，只换表情 | 1 个锚点 + 1 个固定构图 + N 个表情词 |
| 服装变体 | 同一角色换衣服 | 1 个锚点（身体+发型+脸）+ N 个服装块 |
| 单张多角色 | 一帧里 2 个及以上角色 | 每角色一条"名字 + 外观 + 位置"子句 |

形态决定哪些词进锚点、哪些词进可变块。**先把形态说清再动手写词。**

### 2. 写身份锚点（本 skill 的核心）

锚点按固定先后写四层，层内顺序一旦确定就**不许再改**：

```text
[发型层] [眼睛层] [服装层] [轮廓层] [签名配件层]
```

- 发型层：颜色 + 长度 + 决定性造型（`silver hair, very long hair, blunt bangs, sidelocks`）；
- 眼睛层：颜色 + 眼型/睫毛（`purple eyes, thick eyelashes`）；
- 服装层：主件 + 下装 + 鞋 + 固定配饰（`black sailor dress, pleated skirt, brown loafers, red ribbon`）；
- 轮廓层：体型与剪影（`petite, slender, narrow waist`）；
- 签名配件层：只有这个角色才有的那一件（`eyepatch`, `fox mask on head`, `cracked monocle`）。

长度控制在 **8~16 个标签**。太少 → 每张图都在换人；太多 → 触发 Anima 的随机标签丢弃，
同一个锚点在不同张里被丢掉的部分不一样，反而更不一致。

### 3. 分清身份关键项与装饰项

只有"认人靠它"的才算关键项，其余一律踢出锚点（它们会稀释锚点、也让每张更难统一）：

| 关键项（进锚点，逐字复用） | 装饰项（不进锚点，随图变） |
|---|---|
| 发色 / 发长 / 决定性发型（`blunt bangs`, `single braid`） | 头发的瞬时状态（`windblown hair`, `wet hair`） |
| 瞳色 / 异色瞳 / 特殊瞳孔 | 泪光、临时眼妆 |
| 主服装 + 标志配色 | 外套披不披、袖子卷没卷 |
| 签名配件（眼罩、面具、护目镜） | 手里拿什么、背着什么 |
| 体型 / 身高感 / 剪影 | 姿势、动作、镜头角度 |
| 岁感用自然语言写（`a teenage girl`） | 天气、时间、背景、光照 |

> 岁感不要硬塞年龄标签；用自然语言从句（`the same slender teenage girl`）更稳，也不容易踩安全标签。

### 4. 多角色：名字 + 外观 + 位置（官方要求）

官方明确：**只写角色名而不描述外观，模型会混淆**。每个角色都要给三件东西：

```text
[name] from [series], [外观：发色发型 + 瞳色 + 服装 + 签名配件], [位置：on the left / on the right / in the foreground]
```

- 人数标签写够：`2girls` / `1girl, 1boy` / `multiple girls`；
- **多角色时删掉 `solo`**——`solo` 与 `2girls` 直接冲突，会把其中一个压掉或把两人融在一起；
- 位置词成对出现；只给一个角色位置，另一个就会乱飘或与背景黏连；
- 自然语言里再复述一遍归属：`The girl with silver hair stands on the left; the red-haired boy kneels on the right.`；
- 用户只给名字、没给外观：**不要猜**。猜错发色瞳色等于换了个人；请用户补发色、瞳色、主服装、签名配件四项，
  或确认可以直接引用用户提供的参考描述。

**四条防混淆规则（Anima 在多人场景里极易串味，逐条照做）：**

1. **属性按角色分组排列，严禁交叉。** 同一个角色的发型、瞳色、服装、体型、配件**连续写完再切换**
   下一个角色。反例（必然串色）：`blue hair, red hair, short hair, long hair`；
   正例：`blue hair, long hair, blue eyes, white dress,` 然后才是 `red hair, short hair, red eyes, black armor,`。
   体型词（`petite` / `tall`）也属于角色分组，不要单独漂在两组之间。
2. **互动词紧跟在人数标签后面。** 有互动时先写 `2girls, duo, holding each other's hands,`，
   再分别描述两个角色——不要等描述完两个人的外观才补一句互动。
3. **用空间方位词分离角色**：`left` / `right` / `foreground` / `background` 成对出现，
   自然语言层为每个角色写一句"外观锚定短语"（`the girl with blue hair on the left…`）。
4. **易混淆特征要加权**：两个角色发色相近时写 `(blue hair:2), (red hair:2)`；
   权重额度全文 ≤4 个，多人场景就优先给这类最容易被换掉的特征。

### 5. 组装视图组 / 表格

每条提示词 = `[前缀标签] [角色+作品+画师] [身份锚点] [本视图可变块] . [自然语言]`。

- **只有该变的那一个轴改词**，其它全部照抄；
- 版式词写进可变块：`character sheet`, `multiple views`, `reference sheet`，局部视图 `portrait`,
  `upper body`, `full body`；
- 背景统一成 `white background, simple background`，避免每格的背景把风格拉走；
- **不要指望模型画出 `FRONT` / `SIDE` 这类视图标注**：Anima 文字渲染弱，长词必崩；
  需要文字标注时**后期加字**，提示词里只描述"画成并列三格"。

### 6. 负面提示词按形态选

- 单张多角色：加 `merged characters, duplicated character, wrong attribute, fused bodies`；
- 三视图 / 表情表：加 `merged characters, fused characters, inconsistent character, outfit mismatch`；
  **慎用 `duplicated character`**——表格本来就要重复画同一角色，这个词可能连"应该重复的格子"一起压掉；
  出现格子塌陷就先删掉它再看；
- 再加 `inconsistent hair color, inconsistent eye color, color bleeding`；
- 复用 Anima 官方默认负面骨架，但别把与需求冲突的词抄进去（见 `anima-prompt-negative`）。

### 7. 交付前自检（静默）

- 每条提示词的锚点是否**逐字一致**（含大小写与先后顺序）？
- 是否每张只有"应该变的那一轴"在变？
- 多角色是否同时具备：人数标签、每人外观、每人位置？`solo` 是否已删？
- 多角色的属性是否**按角色分组**、没有交叉排列？互动词是否紧跟在人数标签后？易混淆特征加权了吗？
- 是否把种子 / 宽高比 / CFG / 模型文件名漏进了提示词正文？
- **用户没给画师时，是否自己挑了 1 个风格对路的主画师**（不能留空）？LoRA 名有没有编（绝不能编）？
- 是否仍是动漫插画取向（Anima 不做写实）？

## 示例

输入：`银发紫瞳少女，女仆装，红发带，要三视图（正 / 四分之三 / 背）`

```text
View 1 — front
Positive prompt
masterpiece, best quality, safe, 1girl, silver hair, very long hair, blunt bangs, sidelocks, purple eyes, black maid dress, white apron, frilled headband, red ribbon, thighhighs, petite, slender, character sheet, multiple views, from front, standing, arms at sides, white background, simple background. A plain character sheet on a white background showing the same slender silver-haired maid girl from the front, standing straight with her arms relaxed at her sides, full body visible from head to shoes in identical proportions with flat cel shading.

Negative prompt
worst quality, low quality, lowres, blurry, jpeg artifacts, bad anatomy, bad hands, extra fingers, missing fingers, extra limbs, deformed, duplicate face, crossed eyes, messy lineart, watermark, signature, username, logo, merged characters, fused characters, inconsistent character, outfit mismatch, inconsistent hair color, inconsistent eye color

View 2 — three-quarter
Positive prompt
masterpiece, best quality, safe, 1girl, silver hair, very long hair, blunt bangs, sidelocks, purple eyes, black maid dress, white apron, frilled headband, red ribbon, thighhighs, petite, slender, character sheet, multiple views, three-quarter view, standing, hands clasped in front, white background, simple background. The same slender silver-haired maid girl seen from a three-quarter angle, rotated about forty-five degrees with her hands clasped in front of her apron, keeping the identical hairstyle, eye color, dress and ribbon, full body visible from head to shoes.

Negative prompt
worst quality, low quality, lowres, blurry, jpeg artifacts, bad anatomy, bad hands, extra fingers, missing fingers, extra limbs, deformed, duplicate face, crossed eyes, messy lineart, watermark, signature, username, logo, merged characters, fused characters, inconsistent character, outfit mismatch, inconsistent hair color, inconsistent eye color

View 3 — back
Positive prompt
masterpiece, best quality, safe, 1girl, silver hair, very long hair, blunt bangs, sidelocks, purple eyes, black maid dress, white apron, frilled headband, red ribbon, thighhighs, petite, slender, character sheet, multiple views, from behind, standing, arms at sides, white background, simple background. The same slender silver-haired maid girl seen from behind, only the back of her long hair, the apron ties and the red ribbon at the back of her head visible, full body from head to shoes with the identical height and outfit details.
```

> 真实交付时负面提示词要**整段抄写**，不要写"同 View 1"；示例为压缩篇幅才省略。
> 同理，每条视图都必须在 artist 位带**同一个主画师标签**（`(@artist name:2)`，占位符）——
> 跨图风格一致也靠它；示例为压缩篇幅未逐条写出。

输入：`主角团同框：银发女仆 + 红发男剑士`

```text
Positive prompt
masterpiece, best quality, safe, 1girl, 1boy, duo, (@artist name:2), (upper body:2), silver hair, very long hair, purple eyes, black maid dress, white apron, red ribbon, petite, slender, red hair, short hair, green eyes, brown leather armor, sword on back, tall, simple background. Two characters stand side by side against a plain background: the slender silver-haired maid in a black dress on the left, one hand holding her apron; the taller red-haired swordsman in brown leather armor on the right with a sword on his back, each keeping their own hair color, eye color and outfit without mixing.

Negative prompt
worst quality, low quality, lowres, blurry, jpeg artifacts, bad anatomy, bad hands, extra fingers, missing fingers, extra limbs, deformed, duplicate face, crossed eyes, watermark, signature, username, logo, merged characters, duplicated character, wrong attribute, fused bodies, color bleeding
```

注意这条提示词里的**防混淆写法**：人数后紧跟 `duo`，两个角色的属性**各自成组**
（女仆：`silver hair, very long hair, purple eyes, black maid dress, white apron, red ribbon, petite, slender`；
剑士：`red hair, short hair, green eyes, brown leather armor, sword on back, tall`），
完全没有交叉排列——这是多人不串味的头号保证。另外补上了主画师 `(@artist name:2)`（占位符）
与 `(upper body:2)` 取景权重，全文加权 2 个。

## 附：种子与 LoRA（只在用户询问时说明）

- 固定种子能减小随机差异，但**一致性主要来自逐字复用的身份锚点**，不是种子；
- 用户有自己的角色 LoRA 时，触发词放 `[角色]` 段，锚点里**删掉 LoRA 已经学会的那几项**
  （通常是发色/瞳色/脸型），只留 LoRA 覆盖不到的（签名配件、体型、当次服装）；
- **不要编造 LoRA 名或触发词**；用户没给就不用，细节规则交给 `anima-lora-trigger`；
- 这些内容属于独立小节，**不要写进 `Positive prompt` / `Negative prompt` 正文**。

## 边界

- 只是单张图、不涉及跨图一致性 → `anima-prompt-format`；
- 视图组里每格的姿势、动作、动态线 → `anima-motion-boost`；
- 跨图恒定的线条 / 上色 / 时代感 → `anima-style-control`、`anima-style-boost`；
- 同一角色换画师风格 → `anima-prompt-artist`；
- 对已出图做脸部或服装的局部重绘来修一致性 → `anima-prompt-regional`；
- 该用哪个质量前缀、负面词怎么裁剪 → `anima-prompt-negative`；
- 用户要靠固定种子 / 分辨率 / 步数批量复现同一角色 → 这些是**工作流侧参数**，不要写进提示词，也不要在输出里给数值；
- 只有一句话需求、要先成型再迭代 → `anima-prompt-optimize`。
