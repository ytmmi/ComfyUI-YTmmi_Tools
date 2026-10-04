---
name: anima-prompt-optimize
description: Diagnose and repair an existing Anima prompt, covering tag order, underscore and spacing errors, missing subject count, a contradictory medium, overstuffed synonyms, a quality prefix that does not match the model version, a missing safety tag and vague four-word prompts. Use for Anima Base / Aesthetic / Turbo text-to-image prompts in ComfyUI when a prompt already exists but renders badly.
version: 1.2.0
---

# Anima 提示词优化（Prompt Optimize）

这个 skill 处理的是**已经存在、但出图不对**的提示词。它不重新创作，而是按固定顺序做体检、
逐条修复，最后仍然只交回两段提示词。

体检顺序固定为：**合法性 → 顺序 → 具体性 → 冲突 → 冗余 → 安全/版本前缀**。
顺序不能颠倒：先保证"能跑"，再谈"好看"；先消冲突，再删冗余。
完整的违规目录、修复对照与严重度排序见 `references/anima-prompt-checklist.md`。

标签语法、区段顺序、质量前缀的权威定义在 `anima-prompt-format` 的
`references/anima-prompt-baseline.md`；本文件不重复定义，只做诊断与修复流程。

## 输出契约

默认**只输出修复后的正面提示词正文**（不带标题行）；原提示词里本来就有负面词、或用户明确要求修复负面词时，才输出两段：

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

- 负面词只在**原本就有**或用户明确要求时才输出（示例仍按两段演示）。

## 工作流

### 1. 逐字保留清单（先划出来，后面一个字都不许动）

- 角色名、作品名、专有名词、`@` 画师标签；
- 用户要求出现在画面里的可见文字（招牌、标题、必杀技名、非英文文案）；
- LoRA 触发词（它可能长得像乱码，**不要"修正"它**）；
- 用户显式给出的 safety 等级与显式否定项；
- 用户显式给出的服装、道具、颜色、人数。

**永远不要**新增用户没给过的画师名、LoRA 名、角色名、作品名——编错这些比留空更糟。

### 2. 合法性检查（能不能跑）

| 违规 | 例子 | 修复 |
|---|---|---|
| 多词标签用下划线 | `long_hair` `blue_eyes` `looking_at_viewer` | 改空格：`long hair` `blue eyes` `looking at viewer` |
| score 标签丢了下划线 | `score 7` | 改回 `score_7`（score 标签是唯一保留下划线的标签） |
| 大小写混乱 | `Long Hair` `MASTERPIECE` | 标签区全小写（自然语言句子与可见文字保留原样） |
| 画师标签缺 `@` | `nnn yryr` | 加前缀：`@nnn yryr`（不加 @ 效果极弱） |
| 权重过低 | `(chibi:1)` `(mid-air:1.1)` | 提到 Anima 需要的量级：`(chibi:2)`、`(mid-air:2)`（常规 `:2` 起，强强调 `:3~5`） |
| 权重语法错 | `{{chibi}}` `chibi::2` | 改 `(chibi:2)` |
| 缺 safety 标签 | 只有 `1girl, solo, ...` | 按用户意图补 `safe` / `sensitive` / `nsfw` / `explicit` |
| 备选表述 | `a girl or a boy` `maybe raining` | 删掉备选，只留最终画面 |

### 3. 顺序检查

官方区段顺序：`[quality/meta/year/safety] [1girl/1boy 等] [character] [series] [artist] [general]`。

- 区段**之间**顺序必须正确；**区段内部**顺序随意，不要为了"好看"重排区段内标签；
- 最常见错误：人数标签 `1girl` 飘到 general 区段中间，或 safety 标签被扔到末尾；
- 修复时把所有 quality/meta/year/safety 归拢到开头，人数紧随其后。

### 4. 具体性检查

| 症状 | 修复 |
|---|---|
| 单角色图没有人数标签 | 补 `1girl` / `1boy` / `1other`，配 `solo` |
| 多角色只列名字不给外观 | 每个角色补外观锚点（发色、发型、眼睛、服装），否则模型会串味 |
| 只有名词堆叠，没有自然语言 | 补 1~3 句英文 caption 描述最终画面 |
| caption 少于 2 句 | 纯自然语言时至少 2 句，过短会出意外内容 |
| 描述的是"生成过程" | 改写成"最终画面"（删 `then` `after that` 类时序词） |
| 抽象形容词 | `cool` `nice` `beautiful` `amazing` → 翻译成可执行决策（冷色调 / 低角度 / 高对比），译不出就删 |

### 5. 冲突检查

| 冲突 | 处理 |
|---|---|
| `photorealistic` / `photograph` 与 `cel shading` / 动漫标签同现 | Anima 不做写实：保留动漫侧，把写实词删掉（必要时移入负面） |
| `painterly` 与 `flat cel shading` / `cel shading` | 只留一个主导渲染 |
| `monochrome` 与 `vibrant colors` | 二选一 |
| `lineless` 与 `thick outlines` | 二选一 |
| 标签与 caption 互相矛盾 | 以**用户明确意图**为准，改写另一方 |
| Danbooru 与 Gelbooru 写法不同 | 优先 Gelbooru 版本 |
| 正面与负面出现同一个词 | 删掉负面里的那一个（自相矛盾会让两边都失效） |
| `year 2005, absurdres, newest` | 年代意图与清晰度意图互斥，按用户目标二选一 |

### 6. 冗余检查

- 同义质量词堆叠：`masterpiece, best quality, ultra detailed, highly detailed, 8k, absurdres` →
  只留 `masterpiece, best quality`（外加版本匹配的 score 前缀）；
- 同义细节词：`detailed, intricate details, fine details` → 只留一个；
- 同义美学词：`aesthetic, very aesthetic, beautiful` → 只留一个；
- 重复标签与大小写变体：`long hair, Long Hair` → 删一个。
- 依据：Anima 用**随机标签丢弃**训练，堆同义词不会变强，只会稀释语义并把画面推向通用 slop。

### 7. 安全 / 版本前缀检查

| 情形 | 前缀 |
|---|---|
| 版本未知（默认） | `masterpiece, best quality, safe`，**不加** score |
| 明确裸 Base | `masterpiece, best quality, score_7, safe` |
| 明确 Aesthetic / Turbo | `masterpiece, best quality, safe`，**正负都不要** `score_*` |
| 明确挂了 PonyV7 系美学 LoRA | 用 LoRA 的质量前缀（`score_9, score_8, ...`），**不要**塞回 `score_7` |

`safety` 段必写。用户没提就按内容判定：日常 / 一般向用 `safe`，不要擅自升级也不要擅自降级。

### 8. 过短要扩、过长要砍

**扩写顺序**（4 词级提示词 → 可用提示词，逐层加，每层加完就够）：

```text
1 合法性+顺序  →  2 safety+质量前缀  →  3 人数  →  4 主体身份细节  →  5 动作与体态
→  6 场景/时间/天气  →  7 镜头与景别  →  8 风格(媒介+渲染+年代+格式)  →  9 光与色  →  10 caption 1~3 句
```

合理上限：单角色约 25~35 个标签 + 1~3 句 caption。再往上加就是冗余。
补齐的细节属于**协调的默认选择**；用户给过设定时以其为准，并**不要**顺手编造角色名、作品名、LoRA 名。
**但画师例外**：用户没给画师时，必须由你按媒介 / 年代 / 题材挑一个风格对路的知名画师
（见 `anima-prompt-artist`），不要留空。

**用户没指定构图 / 镜头时，允许自主加一个特殊装置**（`fisheye lens` 鱼眼、`spherical composition`
球面构图、`extreme foreshortening` 极端透视、`isometric` 等距版式、`panorama` 全景等，
见 `anima-composition-optimize`），不要永远停在最保守的默认景别上；但用户已指定构图时**绝不覆盖**，
且一次只用**一个**特殊装置（表格类 / 三视图 / 分镜场景禁用）。

**裁剪顺序**（从最先砍到最不该砍）：

```text
1 同义质量/美学词  →  2 泛化细节词(detailed, intricate details)  →  3 重复与大小写变体
→  4 备选表述(or/maybe)  →  5 冲突项的一半  →  [以下保留] 主体身份、人数、safety、
   可见文字、用户显式约束、画师标签、风格主串
```

### 9. 交付前自检（静默）

- 逐字保留清单里的内容是否一个字都没动？
- 六项检查是否都走完？有没有为了"顺手"改动用户没要求的部分？
- 修好后的前缀是否与模型版本匹配？safety 是否还在？
- 输出是不是只有两段？变更说明（若用户要）是否放在了提示词之后？
- 有没有编造角色名 / LoRA 名？（**画师不在此列**——用户没给时你应当自己挑一个，见上面第 8 步）
- 用户没指定构图 / 镜头时，是否主动用上了一个合适的特殊装置（而不是停在默认景别）？

## 示例

### 示例 A：修复一条坏提示词

输入：

```text
best quality, masterpiece, ultra detailed, highly detailed, 8k, long_hair, blue_eyes, 1girl, looking at viewer, cel shading, photorealistic, safe, artist nnn yryr, score_7
```

```text
Positive prompt
masterpiece, best quality, safe, 1girl, solo, long hair, blue eyes, looking at viewer, cel shading, @nnn yryr. A calm anime illustration of a girl with long hair and blue eyes looking straight at the viewer, drawn with flat cel shading and clean lineart against a simple background.

Negative prompt
worst quality, low quality, lowres, blurry, jpeg artifacts, bad anatomy, bad hands, extra fingers, missing fingers, extra limbs, deformed, duplicate face, crossed eyes, messy lineart, photorealistic, photograph, live action, watermark, signature, username, logo, unrelated text
```

Changelog（仅作讲解；用户没要时不输出）
- 冗余：`ultra detailed, highly detailed, 8k` 与 `masterpiece, best quality` 同义，删除；
- 合法性：`long_hair` → `long hair`；`blue_eyes` → `blue eyes`；`artist nnn yryr` → `@nnn yryr`；
- 顺序：`1girl` 提到人数区段并补 `solo`；
- 冲突：`cel shading` 与 `photorealistic` 互斥，保留动漫侧，写实词移入负面；
- 版本：未说明版本，按安全前缀处理，去掉 `score_7`；`safe` 保留；
- 具体性：原文没有 caption，补一句最终画面描述。

### 示例 B：扩写一条 4 词提示词

输入：`1girl, sword, sunset, cool`

```text
Positive prompt
masterpiece, best quality, safe, 1girl, solo, long black hair, red eyes, black coat, holding sword in right hand, standing, sunset, orange sky, clouds, rooftop, backlighting, rim light, wind, floating hair, coat flapping, low angle, depth of field. A lone swordswoman stands on a rooftop ridge at sunset with her blade resting point-down against the tiles, orange backlight cutting a hard rim along her coat and hair while the city below sinks into warm haze, framed from a low angle that keeps her silhouette dominant.

Negative prompt
worst quality, low quality, lowres, blurry, jpeg artifacts, bad anatomy, bad hands, extra fingers, missing fingers, extra limbs, extra arms, deformed, duplicate face, crossed eyes, messy lineart, watermark, signature, username, logo, unrelated text
```

Changelog（仅作讲解；用户没要时不输出）
- `cool` 是歧义形容词（冷色 / 帅气），两种读法会导出完全不同的图，因此**不译**，改由
  `low angle` + `rim light` + `coat flapping` 落实"帅气"，冷色则交给 `sunset, orange sky` 的反差；
- 按扩写顺序补：人数 `solo` → 身份细节（黑长发、红眼、黑外套，属协调默认值，用户有设定时以其为准）
  → 动作体态（`holding sword in right hand, standing`）→ 场景（`sunset, orange sky, clouds, rooftop`）
  → 镜头（`low angle, depth of field`）→ 光（`backlighting, rim light`）→ 运动证据（`wind, floating hair, coat flapping`）；
- 全文**没有**新增角色名、作品名、画师名。

## 边界

- 提示词是从零开始写（不是修复已有内容）→ 交给 `anima-prompt-format`；
- 风格未定，需要先选一个主导风格 → 交给 `anima-style-control`；
- 风格已定但仍然"平"、需要提升完成度 → 交给 `anima-style-boost`；
- 修复后的动作依然僵硬 → 交给 `anima-motion-boost`；
- 需要画师标签、画师混合与权重 → 交给 `anima-prompt-artist`；
- 角色一致性、多视图、跨图身份 → 交给 `anima-prompt-character`；
- 景别、机位、前中后景、留白布局 → 交给 `anima-composition-optimize`；
- 负面词需要整体重做而非局部修补 → 交给 `anima-prompt-negative`；
- 分区上色 / 局部重绘提示词 → 交给 `anima-prompt-regional`；
- LoRA 触发词缺失或被误删 → 交给 `anima-lora-trigger`；
- 出图问题其实来自步数 / CFG / 采样器 / 分辨率 → 这些是**工作流侧参数**，不要写进提示词，也不要在输出里给数值；
- 用户要求写实照片 → 说明 Anima 不做写实，不要靠"修复"把提示词改成写实向。
