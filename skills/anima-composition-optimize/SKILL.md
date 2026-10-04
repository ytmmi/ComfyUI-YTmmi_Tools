---
name: anima-composition-optimize
description: Fix and design framing in Anima prompts with shot size, camera angle, view direction, subject placement, visual hierarchy, depth layering and negative space. Use when an Anima render puts the subject too small, centers everything, lets characters overlap without hierarchy or lets the background steal focus, and when a portrait, poster/key-visual, group shot or scenery-led image needs its framing rebuilt from prompt text alone.
version: 1.0.0
---

# Anima 构图优化（Composition Optimization）

构图是 Anima 提示词里**最便宜、最容易被忽略的一层**：同样的角色与画师标签，只改景别、机位、
朝向和分层词，画面就能从"随手一张"变成"能当封面用的一帧"。本 skill 只做这一层，
不碰角色一致性、不碰负面词体系、不碰生成参数。

读共同基准 `anima-prompt-format/references/anima-prompt-baseline.md` 拿官方标签顺序与硬规则，读
`references/anima-composition-vocabulary.md` 拿完整的景别 × 机位 × 位置 × 分层 × 取景装置词表
与四类产出的构图配方。本文件讲判断与流程。

标 † 的词更适合放进自然语言句子（靠 caption 语义生效）；其余可以直接当 `general` 段标签用。

## 输出契约

默认**只输出正面提示词**，构图信息全部落在提示词正文里；用户明确要负面词时，才在后面追加 `Negative prompt` 段：

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

### 1. 先问"这张图拿来干什么"

| 产出用途 | 构图基线 |
|---|---|
| 头像 / 半身立绘 | 主体占画幅高度 50% 以上，背景弱化 |
| 全身立绘 | 全身完整入画，脚不切；四周留一点呼吸空间 |
| 海报 / KV | 大面积负空间留给标题，主体偏一侧或偏下 |
| 群像 | 先定 1 个主位，其余是陪位；高低错落 |
| 场景主导 | 环境是主体，人是尺度参照（人小是对的） |

用途决定景别基线。**没有用途就先问，或按"默认立绘"处理并在交付时说明假设。**

### 2. 选景别（从紧到松）

`portrait` → `upper body` → `cowboy shot` → `full body` → `wide shot`

- 想要"看得清表情"：`portrait` 或 `close-up` †；
- 想要"看得清服装"：`cowboy shot`（大腿以上）性价比最高；
- 想要"人在环境里"：`full body`，背景标签量必须同步减少；
- `wide shot` 只在**场景是主体**时用，否则主体必然太小。

### 3. 选机位与朝向

- 机位：`from below`（仰视，显强/压迫）、`from above`（俯视，显弱/可爱/渺小）、`dutch angle`（倾斜，紧张）、
  `eye level` †（平视，最中性）、`from side`、`from behind`；
- 朝向与视线分开写：身体可以 `from side`，视线仍 `looking at viewer`；
- 仰视会同时放大下半身、缩小头，用于立绘要谨慎；表格类构图禁止切机位。

### 4. 定主体位置与视觉层级

- 1 个主体：`centered`（对称、仪式感、头像）或 `off-center` †（更自然、便于留白）；
- 2 个主体：一左一右 + 一前一后，且**两者剪影要明显不同**；
- 3 个及以上：先给 1 个主位（居中 / 更大 / 更近），其余为陪位；负空间留在主位视线方向。

**视觉层级只有三个杠杆**：景别差、前后位置、细节量。三者至少给两个，否则观者不知道看谁。

### 5. 加分层与景深

`foreground` / `middle ground` / `background` 三段至少写两段；`depth of field`, `blurry background`,
`bokeh` 用来压低背景；`foreground` 里放一件虚化物（栏杆、花枝、飘落的纸）能立刻做出纵深。

### 6. 三分法与对称（当想法用，不当公式用）

- 三分法：自然语言写 `the subject sits on the left third, the horizon along the lower third`（†）；
- 对称：`symmetry`, `symmetric composition` † + `centered`，适合 KV、宗教感、仪式场景；
- 两种混用会互相削弱；一张图只选一种骨架。

### 7. 取景装置

`framed` †（窗框、门框、拱门、鸟居）、`vignette`、`border`、枝叶前景、背影前景。
取景装置是"用一个框再框一次主体"，适合竖构图海报；**横构图叠加多重框容易显得拥挤**。

### 8. 与动作、风格联动

- 动作构图：动作方向那一侧要留空间（`looking to the side` + 负空间），大动作需要更松的景别；
  完整规则交 `anima-motion-boost`；
- 风格构图：海报 / KV 的构图与普通立绘**不是同一套**（负空间位置、主体占比、要不要边框都不同）；
  风格本身交 `anima-style-control` / `anima-style-boost`。

### 9. 自检（静默）

- 主体在画幅里占比与用途匹配吗？
- 视觉层级是否靠至少两个杠杆建立？
- 前景 / 中景 / 背景是否至少写了两段？
- 构图词是否都落在 `general` 段？
- 有没有把宽高比 / 分辨率 / 参数漏进正文？
- 背景标签量是否超过全文的三分之一（超过就会抢焦）？

## 宽高比不写在提示词里

画面比例由 **ComfyUI 工作流的 latent 尺寸**决定，提示词写 `vertical composition` 之类
只能影响内容密度，改不了画布形状。竖版海报、横版场景、方图头像的差别请在**工作流里**设定；
提示词只负责"在这块画布里怎么排"。
用户问宽高比时，只回一句"由工作流设置决定"——**不要给出具体比例或分辨率数值，也不要附参数段**。

## 常见构图失败与提示词级修法

| 现象 | 成因 | 只改构图词的修法 |
|---|---|---|
| 主体太小 | 用了 `wide shot` / 背景标签太多 | 换 `cowboy shot` 或 `upper body`；删掉多余背景标签；把主体标签提前 |
| 一切都挤在中间 | 默认居中 + 没有前后差 | 改 `off-center` † + `left side`；加 `foreground` 虚化物 |
| 多角色叠成一团无主次 | 缺景别差与前后差 | 主角 `upper body` + `foreground`，配角 `full body` + `background` |
| 背景抢戏 | 背景标签量过大、无景深 | `blurry background, depth of field`；背景细节词砍到主角的三分之一以下 |
| 画面扁平 | 无机位、无分层、无前景 | 加 `from below` 或 `dutch angle` + 一个 `foreground` 物件 |
| 裁切别扭 | 景别与主体不匹配 | 换景别，或显式 `feet out of frame`；负向加 `bad crop` |
| 留白位置不对（海报） | 没指定负空间方向 | 自然语言写清 `large empty space in the upper third for a title` † |
| 视线方向撞墙 | 主体贴边且看向墙 | 把主体移到另一侧，负空间留在视线前方 |

## 示例

输入：`银发少女站在废墟城市，有孤独感，想当封面用`
问题：主体太小、居中、背景细节抢戏、无纵深。

```text
Positive prompt
masterpiece, best quality, safe, 1girl, solo, silver hair, long hair, black coat, ruined city, full body, wide shot, centered, detailed background, dramatic lighting, moss, broken windows, collapsed towers, rubble. A lone silver-haired girl in a black coat stands in the middle of a ruined city avenue, the collapsed towers and broken windows described in as much detail as she is, everything evenly lit and evenly sharp from edge to edge.

Negative prompt
worst quality, low quality, lowres, blurry, jpeg artifacts, bad anatomy, bad hands, extra limbs, deformed, messy lineart, watermark, signature, username, logo
```

**只改构图相关词**后的版本：

```text
Positive prompt
masterpiece, best quality, safe, 1girl, solo, silver hair, long hair, black coat, ruined city, cowboy shot, from below, off-center, left side, foreground rubble, blurry background, depth of field, backlighting. A lone silver-haired girl in a black coat stands off-center on the left of the frame, seen from slightly below; the collapsed towers behind her fall out of focus, a blurred slab of rubble crosses the near foreground, and a wide empty band of pale haze is left in the upper right for a cover title.

Negative prompt
worst quality, low quality, lowres, blurry subject, jpeg artifacts, bad anatomy, bad hands, extra limbs, deformed, bad crop, messy lineart, watermark, signature, username, logo, cluttered background
```

改动点：`full body, wide shot, centered` → `cowboy shot, from below, off-center, left side`；
再加 `foreground rubble`（前景分层）、`blurry background, depth of field`（压低背景）、
`backlighting`（主体与背景分离）。角色与风格标签一个都没动。
注意负向里 `blurry` 换成了 `blurry subject`——这次要的就是虚化背景，直接写 `blurry` 会自相矛盾。

## 边界

- 不涉及构图、只要把需求整成一对提示词 → `anima-prompt-format`；
- 姿势、动作方向、动态线、动作与留白的配合 → `anima-motion-boost`；
- 线条 / 上色 / 时代感 / 画面质感 → `anima-style-control`、`anima-style-boost`；
- 多角色身份归属与一致性（不是位置问题）→ `anima-prompt-character`；
- 分区提示词、局部重绘里的构图修正 → `anima-prompt-regional`；
- 画师标签与风格混合 → `anima-prompt-artist`；
- 负面词体系与质量前缀（例如 `cluttered background` 该不该加）→ `anima-prompt-negative`；
- 宽高比、分辨率、步数、CFG 属于**工作流与模型版本**，既不写进提示词，也不在输出里给数值；
- 需求本身还很模糊、要先发散 → `anima-prompt-optimize`。
