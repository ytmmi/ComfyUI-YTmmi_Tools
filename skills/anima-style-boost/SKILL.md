---
name: anima-style-boost
description: Intensify and polish the art direction of an existing Anima prompt, covering lineart quality, cel-shading depth, color design, lighting design, background density, key-visual polish and overall aesthetics. Use for Anima Base / Aesthetic / Turbo text-to-image prompts in ComfyUI when the style is already chosen but the render still looks flat, muddy or unfinished.
version: 1.0.0
---

# Anima 风格增强（Style Boost）

**风格控制（control）是"选哪个风格"，风格增强（boost）是"让选定的风格真正落地"。**
两者不能混着做：风格还没定就加一堆质感词，只会得到更精致的四不像。
如果用户还在犹豫媒介、渲染、年代、格式，**先用 `anima-style-control` 定死风格，再回来做增强**。

增强的对象是已完成度：线稿是否干净、明暗有没有层次、配色是否有设计、光照有没有方向、
背景是否有密度、细节是否撑得住。Anima 的裸 Base 版本默认风格朴素，是这套增强的主要使用场景。

读 `references/anima-boost-recipes.md` 获取轻/中/强三档 boost ladder 表、逐轴标签集，
以及 Aesthetic / Turbo 的专项注意事项。本文件只给决策流程。

## 输出契约

默认**只输出一条正面提示词**（增强后的正文）；仅在用户明确要求负面词时，才追加 `Negative prompt` 段：

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

### 1. 门禁：风格定了吗？

- 已定（用户给了明确风格词，或提示词里已有稳定的媒介+渲染）→ 继续；
- 未定 / 在漂移 → 停，交给 `anima-style-control`，不要在这里顺手替用户选风格；
- 用户说的"风格"其实是想要**另一个风格**而不是更强 → 也交给 `anima-style-control`。

### 2. 确认模型版本（决定能不能用 score）

| 版本 | 能不能加 score 标签 | 增强重点 |
|---|---|---|
| 裸 Anima-Base | 可以，`score_7` 保留 | 线稿 + 阴影层次 + 光照方向 + 背景密度（缺得最多） |
| Anima-Aesthetic | **不要**加任何 `score_*` | 已美学调优：补结构信息，少补美学形容词 |
| Anima-Turbo | **不要**加任何 `score_*` | 同 Aesthetic，且对比/饱和已偏高，别再加"更鲜艳" |
| 挂了 PonyV7 系美学 LoRA | 用 LoRA 的质量前缀，不是 `score_7` | 先确认 LoRA 触发词（见 `anima-lora-trigger`） |

版本判断不了 → 用 `masterpiece, best quality, safe` 安全前缀，**不加** score 标签。

### 3. 诊断：画面"平"在哪一层？

| 症状 | 缺的层 | 优先补 |
|---|---|---|
| 线条发毛、边缘糊、颜色出界 | 线 | `clean lineart, sharp lines, defined edges` |
| 明暗只有一档，像贴纸 | 上色 | `soft shading, layered shading, ambient occlusion` |
| 颜色脏、灰、没重点 | 配色 | `color contrast, vibrant colors, cohesive palette` |
| 光源不明、没有立体感 | 光 | `directional lighting, rim light, backlighting` |
| 背景像空白纸或一团糊 | 背景 | `detailed background, depth of field, atmospheric perspective` |
| 大构图没问题但看着"空" | 细节密度 | `detailed, intricate details`（**只加一个**） |

**一次只补 1~2 层**，补完再看。六个层同时开火就是 over-seasoning。

### 4. 选档位（轻 / 中 / 强）

| 档位 | 新增标签数 | 适用 |
|---|---|---|
| light | 3~5 个 | 只差一点完成度；Aesthetic / Turbo 默认用这档 |
| medium | 8~12 个 | 裸 Base 的典型平图；要出可交付立绘 / 立绘感插图 |
| strong | 14~18 个 | 明确要 KV / 海报级完成度，且用户能接受风格被推得更"精致" |

完整标签串见 `references/anima-boost-recipes.md` 的 boost ladder 表。

### 5. "加味但不加料"规则（本 skill 最重要的一条）

Anima 是用**随机标签丢弃（tag dropout）**训练的：训练时部分标签会被丢掉，模型因此学会"信息不全也能画"。
后果是——**同义词堆叠不会变强，只会互相稀释**，还会把画面推向"通用高完成度 slop"。

具体做法：

- 每一层最多 2~3 个标签，同义只留一个：要 `clean lineart` 就**不要**同时写 `sharp lineart,
  detailed lineart, crisp lines`；
- 质量词不叠加：已经有 `masterpiece, best quality` 就不要再加 `ultra detailed, highly detailed, 8k`；
- 美学词不叠加：`aesthetic` / `very aesthetic` / `beautiful` 选一个；
- 增强词要**有物理含义**（光从哪来、阴影落在哪、背景有什么），而不是空形容词。

### 6. 标签归位

- 质量 / meta 类增强词（`highres`、`absurdres`）→ 第一区段，紧跟质量前缀；
- 线稿、上色、配色、光照、背景、细节类 → general 区段（主体与服装之后），或自然语言区；
- 权重需要比 SDXL 更高：`(soft shading:1.3)`、`(rim light:1.4)`；
- 不要把 `photorealistic` 之类的写实词当"细节增强"塞进来——Anima 不做写实。

### 7. 保住主体可读性

增强的最大副作用是**背景与细节抢走主体**。约束手段：

- 背景细节 + `depth of field` / `blurry background` 一起用，把景深给主体；
- 用 `silhouette` / `rim light` / `backlighting` 把主体从密集背景里"抠"出来；
- 主体占画面比例靠自然语言说明（`the figure occupies the center third of the frame`）；
- 负面加 `busy background, cluttered`，而不是继续往正面堆细节。

### 8. 增强过头时（负面兜底）

```text
oversaturated, hdr, overexposed, blown out highlights, plastic texture, glossy skin,
over-sharpened, noisy, cluttered, busy background, washed out, muddy colors
```

- Base 增强过头 → `oversaturated, hdr, plastic texture`；
- Aesthetic / Turbo 增强过头 → 它们本来对比就高，优先 `overexposed, blown out highlights,
  over-sharpened`；
- 注意**不要**把 `flat color` 写进负面去"治平图"：如果正面要的是 `cel shading`，这等于自己打自己；
  治平图应该靠 `soft shading, layered shading` 加法，而不是靠负面。

### 9. 交付前自检（静默）

- 主导风格是否原封不动？有没有在"增强"的名义下换了渲染方式？
- 每层标签是否 ≤3 个、同义是否只有一个？
- 版本对不对？Aesthetic / Turbo 里有没有混进 `score_*`？
- 增强后主体还是画面里最清楚的东西吗？
- 用户原有的角色、文字、人数、safety 是否一字未动？
- 输出里是否只有 `Positive prompt` / `Negative prompt` 两段？

## 示例

输入：裸 Base 出图偏平，**原提示词**（before，用户已给出、不得改动主体）要求做**中档增强**：

```text
masterpiece, best quality, score_7, safe, 1girl, solo, long hair, white dress, standing, forest
```

输出（after）：

```text
Positive prompt
masterpiece, best quality, score_7, safe, 1girl, solo, long hair, white dress, standing, forest, clean lineart, cel shading, soft shading, layered shading, vibrant colors, warm color palette, backlighting, god rays, dappled sunlight, detailed background, dense foliage, atmospheric perspective, depth of field. A white-dressed girl stands in a sunlit forest, drawn with thin clean lineart over layered soft cel shading, warm green-and-gold palette, sunlight breaking through the canopy in visible shafts and pooling on broad leaves, foreground foliage thrown out of focus so her figure stays the brightest and sharpest shape in frame.

Negative prompt
worst quality, low quality, lowres, blurry, jpeg artifacts, bad anatomy, bad hands, extra fingers, missing fingers, extra limbs, deformed, duplicate face, crossed eyes, messy lineart, muddy colors, washed out, oversaturated, cluttered, busy background, watermark, signature, username, logo, unrelated text
```

本次 boost 实际新增的标签（仅作讲解，不属于输出）：
线 `clean lineart` → 上色 `cel shading, soft shading, layered shading` →
配色 `vibrant colors, warm color palette` → 光 `backlighting, god rays, dappled sunlight` →
背景 `detailed background, dense foliage, atmospheric perspective, depth of field`。
共 13 个（中档），没有加任何同义质量词，`score_7` 因为是裸 Base 而保留，负面只加了
"增强过头/主体被抢"这一类失败模式。

## 边界

- 风格尚未确定（还在选赛璐璐 / 厚涂 / 网点 / 年代）→ 交给 `anima-style-control`；
- 标签顺序、大小写、权重语法、质量前缀写错 → 交给 `anima-prompt-format`；
- 动作僵硬、姿势无动能 → 交给 `anima-motion-boost`；
- 画师风格与画师权重 → 交给 `anima-prompt-artist`；
- 角色三视图 / 跨图一致性 → 交给 `anima-prompt-character`；
- 景别、机位、前中后景、留白 → 交给 `anima-composition-optimize`；
- 负面词需要整体重做（不只增强过头类）→ 交给 `anima-prompt-negative`；
- 分区上色 / 局部重绘的局部增强 → 交给 `anima-prompt-regional`；
- LoRA 触发词、LoRA 自带质感 → 交给 `anima-lora-trigger`；
- 步数 / CFG / 采样器 / 分辨率属于**工作流侧参数**，不写进提示词，也不在输出里给数值。
