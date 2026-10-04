---
name: anima-prompt-regional
description: Build Anima prompt blocks for Regional LLLite multi-region control and for inpaint / repair work. Use when the user wants different subjects in different colour masks, a local repaint, a hand/face fix, or any prompt that must describe a preserved whole-image context plus a masked-area result. Returns the required multi-block prompt plus a negative prompt.
version: 1.0.0
---

# Anima 分区与局部重绘（Regional / Inpaint）

为 Anima 生成**分区（Regional LLLite）**与**局部重绘（inpaint / repair）**所需的提示词块。
这两种形态都不是"一对正负提示词"能表达的，必须按固定块结构交付。

读 `references/anima-regional-guide.md` 获取块模板、区域写法与失败模式清单。
模型硬规则见 `anima-prompt-format/references/anima-prompt-baseline.md`。

## 两种输出契约

默认**只输出正面部分**：Regional 给 `Global prompt` + 各区域块，Inpaint 给 `Whole image context` + `Masked area prompt`。
这些块标签（`Global prompt` / `<颜色> region` / `Whole image context` / `Masked area prompt`）是**结构必需**的，不属于「多余的标题行」。
只有用户明确要求负面词时，才在**最后**追加 `Negative prompt` 段（全局负面 + 该形态的专属负面）。

只输出 Anima 提示词正文：

### A. Regional LLLite（分区）

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

```text
Global prompt
[全图共享的质量/风格/世界/光照]

<颜色> region
[该颜色遮罩区域内的主体或物件，必须写明左/右/前景/背景]

<颜色> region
[…]
```

- 用户明确要负面词时，才在这个块结构**最后**追加 `Negative prompt` 段（本文件 `## 示例` 演示了含负面的完整形态）；
- 区域块**一种遮罩颜色一块**，颜色名只作为**区域标签**，不代表最终画面颜色
  （除非该遮罩颜色本身就是要出现在画面里的颜色）；
- 区域块必须写**空间关系**（左/右/前景/背景/上下），否则区域会互相渗透；
- `Global prompt` 只写全图共享项；不要把某个区域独有的内容写进全局。

### B. Inpaint / repair（局部重绘）

```text
Whole image context
[保留部分的风格、光照、角色/世界身份]

Masked area prompt
[被修复区域**最终应有的样子**]
```

- **关键规则：写"目标成品"，不写"编辑动作"。**
  错误：`remove the extra finger, fix the hand`
  正确：`a natural five-finger hand with correct anime anatomy, slender fingers, matching skin tone, matching cel-shaded highlights`；
- `Whole image context` 负责"别把周围画风带跑"，所以必须包含画风与光照方向。

## 工作流

### 1. 判定形态

| 用户意图 | 形态 |
|---|---|
| 一张图里不同位置放不同主体 / 不同风格 | Regional（A） |
| 修手、修脸、换衣服、补背景、去物件 | Inpaint（B） |
| 先分区再局部细化 | A → B 串联（先给 A 的全套块，再给 B 的块） |

### 2. Regional：先写全局，再切区域

1. **Global prompt**：质量前缀（按版本，见 `anima-prompt-negative`）+ 统一风格 + 统一光照 + 统一色调；
2. **区域划分**：按用户给的遮罩颜色或按空间划分建议颜色（红=主角、蓝=对手、绿=背景、黄=文字/前景物件是社区常用约定）；
3. **每块只写该区域**：主体 + 外观 + 朝向 + 与该区域的相对位置；
4. **禁止跨区引用**：不要写"和红区一样的人"，每个区域自包含；
5. **Negative prompt**：全局负面 + 分区专属负面。

### 3. Inpaint：先锁定上下文，再写目标

1. **Whole image context**：媒介与画风（`anime illustration, clean lineart, soft cel shading`）+ 角色身份 + 服装配色 + 光照方向 + 背景类型 + "保持不变"的表述；
2. **Masked area prompt**：只描述该局部**完成后**的样子，包含解剖正确性、材质、配色、与接缝处的过渡（`sleeve cuff aligned naturally with the wrist`）；
3. **Negative prompt**：局部重绘专属负面（见下）。

### 4. Negative 选择

**Regional 专属负面**：

```text
worst quality, low quality, lowres, bad anatomy, bad hands, extra fingers, missing fingers, merged characters, wrong region, duplicated character, object bleeding into other region, messy lineart, watermark, signature, username, logo
```

**Inpaint 专属负面**：

```text
visible mask edge, patchy repair, mismatched lighting, mismatched style, mismatched lineart, bad anatomy, bad hands, extra fingers, missing fingers, fused fingers, deformed fingers, distorted wrist, messy lineart
```

按需求裁剪，并删除与用户需求直接冲突的项（例如用户就是要在画面里放文字，就不要留 `unrelated text`）。

### 5. 交付前自检（静默）

- Regional：每个区域是否有明确的空间词？区域之间是否互相引用？
- Regional：`Global prompt` 里有没有混进某个区域独有的内容？
- Inpaint：`Masked area prompt` 是否写成了"编辑动作"而不是"目标成品"？
- Inpaint：`Whole image context` 是否包含画风与光照方向（否则修复区会串味）？
- 负面是否包含该形态的专属项（`wrong region` / `visible mask edge` 等）？
- 有没有把宽高比、遮罩尺寸、重绘强度、步数写进提示词？（这些属于工作流，不属于提示词）

## 示例

### Regional

输入：`左边主角，右边反派，背景是城堡，上方放标题`

```text
Global prompt
masterpiece, best quality, safe, anime key visual, fantasy duel poster, dramatic lighting, clean lineart, polished cel shading, detailed castle background, high contrast blue and gold palette

Red region
The heroine occupies the foreground center-left: a young knight with short white hair, blue eyes, a silver breastplate and a torn red cape, holding a glowing sword forward with a determined expression.

Blue region
The antagonist occupies the right side and one layer further back: a tall dark sorcerer in a black robe, violet magical smoke curling around one hand, looking down toward the heroine.

Green region
A ruined gothic castle fills the far background, broken towers, moonlit stone arches and drifting mist behind both characters.

Yellow region
A short glowing fantasy title sits across the upper band, bright golden serif letters, readable and clearly separated from the characters.

Negative prompt
worst quality, low quality, lowres, bad anatomy, bad hands, extra fingers, missing fingers, merged characters, wrong region, duplicated character, object bleeding into other region, messy lineart, watermark, signature, username, logo
```

### Inpaint

输入：`修手，保持原来的二次元风格和衣服`

```text
Whole image context
anime illustration, clean lineart, soft cel shading; the original character identity, outfit colours, lighting direction, background and overall art style are preserved unchanged.

Masked area prompt
a natural five-finger human hand with correct anime anatomy, slender fingers, clean knuckles, relaxed pose, matching skin tone, matching cel-shaded highlights, sleeve cuff aligned naturally with the wrist.

Negative prompt
visible mask edge, patchy repair, mismatched lighting, mismatched style, mismatched lineart, bad anatomy, bad hands, extra fingers, missing fingers, fused fingers, deformed fingers, distorted wrist, messy lineart
```

## 边界

- 只要一对正负提示词（普通文生图）→ 用 `anima-prompt-format`；
- 需要角色在多张图里保持一致 → 用 `anima-prompt-character`；
- 需要决定质量前缀 / 负面词按版本调优 → 用 `anima-prompt-negative`；
- 需要构图层面的主体摆放建议（不涉及遮罩）→ 用 `anima-composition-optimize`；
- 需要 LoRA 触发词与权重写法 → 用 `anima-lora-trigger`；
- 遮罩怎么画、重绘强度设多少属于工作流操作，本 skills 不负责，也**不要给出重绘强度或遮罩尺寸的数值**。
