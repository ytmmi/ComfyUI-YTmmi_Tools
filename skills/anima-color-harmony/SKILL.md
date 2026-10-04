---
name: anima-color-harmony
description: Design and enforce one coherent colour scheme in Anima prompts — hue relationships (monochrome, analogous, complementary, split-complementary, triadic), warm/cool structure, value and saturation balance, subject-versus-background colour separation, and the colour of the light. Use when an Anima render comes out muddy, clashing, washed out, all one note or "cheap looking", when a poster or key visual needs a deliberate palette, or when the user asks for a mood colour such as pastel, neon, sepia, duotone or teal-and-orange.
version: 1.0.0
---

# Anima 配色与颜色搭配（Color Harmony）

Anima 是"泛二次元"模型：**你不指定配色，它每次都会自己配一套**，而且经常配得浑、脏、或者整张只剩一个调子。
配色不是"多写几个颜色词"，而是先决定**色彩关系**——谁是主色、谁是对比色、谁是强调色，
明度和饱和度怎么分层，光是什么颜色——再把它落成提示词。

本 skill 只管**颜色**这一层：色相关系、明度 / 饱和度结构、主体与背景的分色、光的颜色、色彩分级。
不碰画风媒介（那是 `anima-style-control`）、不碰构图与镜头、不碰负面词体系。

读共同基准 `anima-prompt-format/references/anima-prompt-baseline.md` 拿标签顺序与权重语法，读
`references/anima-color-vocabulary.md` 拿颜色词表、七套配色骨架、情绪 → 配色对照表与失败修法。
本文件讲决策与流程。

## 输出契约

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

## 高杠杆规则（先看这 5 条；完整原文见 `anima-prompt-format/references/anima-prompt-baseline.md`）

> 配色属于**自然语言层**——自然语言对画面的影响力远强于标签，所以配色主要靠句子写，标签只做锚点。

1. **画师标签必选**：正文里必须有 **1 个带 `@` 的主画师**，权重 `(@artist name:2)` 起，只 1~2 个
   （用户没给就自己挑一个风格对路的，别留空）。画师标签对**饱和度与色彩倾向**影响极大——
   以黑白漫画见长的画师会把整张图拉向低饱和；
2. **权重用大数**：Anima 需要比 SDXL 大得多——常规 `(tag:2)` 起，强强调 `(tag:3)` ~ `(tag:5)`；
   用户给 `1.2` 这类小数要**放大到 2~5**；
3. **权重标签总数 ≤4**，优先给取景 / 角度与最需要压住的那一项；颜色词很少值得花额度；
4. **三层混合**：Hard Tags（Booru 标签，管结构）→ Soft Phrases（短视觉短语，管动作 / 氛围）→
   NL Caption（1~3 句稠密英文，管空间、光影与**配色**）。**同一语义不跨层重复**；
5. **因果链**：动作与天气必须落到**可见后果**（湿衣、积水、扬尘、逆光边缘），
   颜色也要有来源——光从哪来、什么颜色的光，决定了整张图的色调。

## 工作流

### 1. 先定"这张图要什么情绪"（静默完成，不输出这一步）

配色是情绪的载体，不是装饰。先在心里定一个词，再选骨架：

| 情绪 | 配色方向 |
|---|---|
| 治愈 / 清新 / 日常 | 高明度 + 低饱和 + 类似色（浅蓝 / 薄荷 / 奶白） |
| 燃 / 战斗 / 冲击 | 冷暖强对撞（暖橙主体 + 冷蓝背景）+ 高对比 + 一个高饱和强调色 |
| 赛博 / 夜景 / 未来 | 低明度 + 高饱和霓虹（品红 / 青）+ 大面积暗部 |
| 压抑 / 悲伤 / 孤独 | 低饱和 + 冷调 + 大面积负空间，只留一处暖色 |
| 怀旧 / 复古 / 老番 | 整体降饱和 + 偏黄 / 偏青的单色调 + `sepia` 或 `faded colors` |
| 童话 / 可爱 / 绘本 | 中高明度 + 中饱和 + 三角或类似色 + 干净的大色块 |
| 恐怖 / 诡异 | 极低饱和 + 单一冷色 + 一处反常的高饱和（血红 / 病绿） |

**用户已经给了情绪或颜色要求时，直接照他的走**；没给就按题材自己定一个（见第 7 步）。

### 2. 选配色骨架（hue relationship，最重要的一步）

一次只用**一套**骨架。骨架决定"画面看起来是不是配过色"：

| 骨架 | 构成 | 观感 | 适用 |
|---|---|---|---|
| **单色** monochrome | 同一色相，只变明度 / 饱和度 | 高级、安静、极易统一 | 特写、氛围图、需要克制时 |
| **类似色** analogous | 相邻色相（蓝 → 青 → 绿） | 和谐、自然、不刺眼 | 日常、风景、治愈 |
| **互补** complementary | 对角色相（蓝 / 橙、紫 / 黄） | 对比最强、最醒目 | 海报、燃、需要"跳出来" |
| **分割互补** split-complementary | 主色 + 对角色相两侧 | 比互补柔和，仍有对比 | 立绘、大部分商业插画 |
| **三角** triadic | 三色等距（红 / 黄 / 蓝） | 活泼、卡通、儿童向 | 绘本、Q 版、游戏 UI 感 |
| **冷暖对抗** warm-cool | 暖主体 + 冷背景（或反之） | 电影感，主体自动浮出 | **最万能的默认**，尤其是立绘 |
| **单一强调色** accent | 整体低饱和，只留一处高饱和 | 视线被精确引导 | 情绪图、极简、需要一个焦点 |

落地写法：**主色 + 辅色 + 强调色**三个就够，比例按 60 : 30 : 10。
颜色**主要写进自然语言**（`a warm amber palette against cool blue shadows`），
标签只做锚点（`pastel colors`、`muted colors`、`high contrast`）。

### 3. 定明度与饱和度结构

只选色相不够——同一组色相，明度 / 饱和度结构不同，出来的完全是两张图：

| 结构 | 写法方向 | 观感 |
|---|---|---|
| 高明度 + 低饱和 | `pastel colors, soft lighting, low contrast` | 清新、治愈、透气 |
| 高明度 + 高饱和 | `vibrant colors, high key, bright` | 明快、卡通、广告 |
| 低明度 + 高饱和 | `dark background, neon lights, high contrast` | 浓郁、赛博、夜戏 |
| 低明度 + 低饱和 | `muted colors, low contrast, desaturated` | 压抑、写实向、纪实 |
| 单一强调色 | `limited palette` + 只给一处高饱和 | 高级、视线集中 |

- **不要所有颜色都中饱和**——那是"发灰"和"廉价"的共同来源；
- 想要"高级感"就**降饱和、加明度对比**；想要"浓郁"就**降明度、加饱和**。

### 4. 给主体与背景分色（最容易被忽略、收益最大的一步）

主体"陷进背景"几乎都是因为两者色相或明度太接近。**至少做一层分离**：

| 分离手段 | 写法 | 适用 |
|---|---|---|
| **温度分离** | 暖主体 + 冷背景（`warm amber skin tones against a cool blue-grey background`） | 最自然、最通用 |
| **明度分离** | 亮主体 + 暗背景（`bright subject against a dark background`） | 夜景、舞台、聚光灯 |
| **饱和度分离** | 高饱和主体 + 低饱和背景（`vivid subject, desaturated background`） | 立绘、海报、KV |
| **色相分离** | 背景用主体色的**对比色相** | 需要强视觉冲击时 |
| **边缘分离** | `rim light` / `backlighting` 勾一圈轮廓光 | 与上面任意一条叠加都有效 |

配套规则：

- 背景**不要**用与主体相同的色相，除非刻意做"融进环境"的效果；
- 眼睛、发饰、签名配件可以用**强调色**——这是最便宜的记忆点；
- 背景色块**越少越好**：`simple background` 或两三个色块，比"五彩斑斓的背景"高级得多。

### 5. 定光的颜色（光的颜色就是画面的基调）

配色的一半来自光。**先定光色，再定物体色**：

| 光况 | 颜色写法 | 效果 |
|---|---|---|
| 金色时刻 | `golden hour, warm key light, cool blue shadows` | 暖亮部 + 冷暗部，最讨喜 |
| 蓝调时刻 | `blue hour, cool ambient light, warm window lights` | 整体冷、局部暖点 |
| 正午 | `bright daylight, clear blue sky, crisp shadows` | 高对比、色相干净 |
| 霓虹夜 | `neon lights, magenta and cyan glow, wet asphalt reflections` | 双色霓虹是最稳的夜景方案 |
| 月光 | `moonlight, cool blue tones, low saturation` | 冷、低饱和、安静 |
| 室内暖光 | `warm indoor lighting, soft shadows, amber tones` | 亲密、日常 |
| 逆光 | `backlighting, rim light, glowing edges` | 轮廓发光，主体与背景自动分离 |

光的颜色写清楚之后，物体的固有色**不必逐个交代**——模型会自己算。

### 6. 用户没指定配色时：自主选一套

**用户没说颜色、也没给情绪方向时，不要交一张"没有配色主张"的图。**
按题材从第 1 步的情绪表里挑一个方向，配一套骨架写进去——
**直接写、不反问、不在正文之外解释**（输出契约只允许提示词正文）。

硬约束三条：

1. 用户**已经指定**了颜色 / 色调 / 情绪 → **绝不覆盖**，只在他给的框架内优化；
2. **一次只用一套骨架**（不要单色 + 三角一起上），主色 + 辅色 + 强调色三色封顶；
3. **不要为了"好看"堆颜色词**：颜色主要靠自然语言句子表达，标签锚点 2~3 个足够。

### 7. 常见配色失败与提示词级修法

| 现象 | 成因 | 只改颜色词的修法 |
|---|---|---|
| 画面发灰 / 发浑 | 冷暖混在同一区域，且全部中饱和 | 定一个主色相 + 一个对比色相；主体加饱和、背景降饱和 |
| 刺眼 / 廉价 | 全部高饱和 + 大面积互补对撞 | 保留一个高饱和，其余降下来；按 60 : 30 : 10 分配 |
| 主体陷进背景 | 主体与背景色相 / 明度太接近 | 加温度或明度分离，再补 `rim light` |
| 整张只剩一个调子 | 单色骨架但明度也一致 | 拉开明度层次，或加一个强调色（眼睛 / 配件 / 光源） |
| 色彩割裂 | 每个元素各用一套色 | 收敛到主 / 辅 / 强调三色，其余去饱和 |
| 与画风冲突 | 极简平涂却堆了渐变与光斑 | 删掉彩色光斑，回到 `flat color` + `limited palette` |
| 饱和度忽高忽低（批量） | 画师标签与颜色词互相打架 | 画师标签权重降到 2 以内，颜色改由自然语言统一描述 |

### 8. 自检（静默）

- 是不是**只用了一套**配色骨架？
- 主 / 辅 / 强调是否清楚，颜色数量是否收敛（不是每个元素一个颜色）？
- 主体与背景之间**至少做了一层分离**（温度 / 明度 / 饱和度 / 色相 / 边缘光）？
- 光的颜色有没有交代？整张图的基调能不能用一句话说清？
- 明度与饱和度的结构是否与想要的情绪一致？
- 有没有把颜色词堆成一大串（超过 3 个颜色标签就该收敛）？
- 有没有把宽高比 / 分辨率 / 种子 / CFG / 步数 / 采样器 / 模型文件名漏进正文？
- 用户已经指定的颜色 / 情绪，是否一个字都没改？

## 示例

输入：`雨夜霓虹街头的银发少女，想有电影感`

```text
Positive prompt
masterpiece, best quality, safe, 1girl, solo, silver hair, long hair, blue eyes, black coat, cowboy shot, from below, off-center, night city street, neon lights, wet asphalt reflections, cinematic. The palette is a cool magenta-and-cyan neon night cut by one warm amber accent on her face: magenta and cyan signs rim her silhouette while the wet street mirrors both colours back, her skin keeping a warm amber tone so she separates cleanly from the cold background, deep blue shadows swallowing everything else.
```

输入：`画个治愈系的少女在窗边`

```text
Positive prompt
masterpiece, best quality, safe, 1girl, solo, brown hair, medium hair, green eyes, white dress, upper body, sitting, window, indoor, morning. An analogous pastel palette, pale mint and soft cream against a light sky blue, kept high in value and low in saturation; warm morning light falls through the window with soft shadows, and the only saturated note is the green of her eyes and the small potted plant on the sill.
```

## 边界

- 选媒介 / 线条 / 年代 / 画面格式（赛璐璐、厚涂、漫画网点、老番质感）→ `anima-style-control`；
- 画面"平"、完成度不够、缺细节与纹理（不是颜色问题）→ `anima-style-boost`；
- 光的方向、体积光、材质与细节量 → `anima-style-boost`；本 skill 只负责**光的颜色**；
- 景别 / 机位 / 主体摆放 / 前后景分层 / 特殊镜头 → `anima-composition-optimize`；
- 画师标签的选择与权重（也影响色彩倾向）→ `anima-prompt-artist`；
- 分区提示词里不同区域各自配色 → `anima-prompt-regional`；
- 负面词体系与质量前缀 → `anima-prompt-negative`；
- 分区 / 局部重绘里的颜色一致性 → `anima-prompt-regional`；
- 宽高比、分辨率、步数、CFG 属于**工作流设置**，既不写进提示词，也不在输出里给数值。
