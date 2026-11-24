---
name: image-contrast
description: Build deliberate contrast into an image prompt - value, colour, size, texture, sharpness, density and subject-count contrast - so the eye knows where to land and the frame stops reading as evenly important everywhere. Use when a render looks busy but flat, when nothing stands out, when a poster needs one clear accent, when a group shot has no hierarchy, or when the user asks for bold, minimal, dramatic or high-impact imagery. Model-agnostic: contrast words work as tags or natural language in any diffusion model.
version: 1.1.0
---

# 对比（Contrast）

对比不是「画面对比度高」，而是**让某件事比别的事更突出**。一张图看起来「什么都有但什么都不突出」，
几乎都是因为**所有维度都用同一个强度**：一样的明度、一样的饱和度、一样的清晰度、一样的大小。

本 skill 只管**对比关系**：明暗、色彩、大小、质感、虚实、密度、数量、方向。
不碰具体取景（→ `image-composition`）、不碰光位设计（→ `image-light-and-value`）、
不碰色相选择（→ `image-color-harmony`）。

完整词表与七种对比配方见 `references/image-contrast-vocabulary.md`。

## 何时使用

- 画面**很满但很平**，观者不知道先看哪；
- 海报 / 封面 / 主视觉**缺一个视觉重音**；
- 群像里**没有主次**，人人一样大；
- 颜色**互相打架**或全部一样重；
- 需要**极简**（靠对比制造张力）或**强冲击**（靠对比制造节奏）；
- 想让画面「高级」但不想靠堆装饰。

## 输出契约

- **只输出提示词正文 / 对比方案**，不解释、不复述需求；
- 默认只出正面提示词；用户明确要负面词时才追加两段式；
- 要**对比方案**时用短条目：`主对比 / 次对比 / 抑制项` 各一行；
- 用户已指定的对比关系不覆盖，只补另一层；
- 不写参数、不写 `high contrast` 这类空词。

## 八个对比维度（一次只用一到两个做主）

| 维度 | 怎么写 | 用在哪 |
| --- | --- | --- |
| **明暗** | `the subject is the only dark shape on a pale field` | 最通用、最便宜 |
| **色彩** | `a single saturated red against an otherwise muted scene` | 强调、品牌色 |
| **冷暖** | `cool blue shadows holding one warm amber lamp` | 氛围、夜晚 |
| **大小** | `a tiny figure beneath a colossal arch` | 尺度、巨构 |
| **质感** | `brushed metal against coarse linen` | 产品、材质叙事 |
| **虚实** | `the face razor-sharp, the street dissolved into bokeh` | 引导视线 |
| **密度** | `one empty wall beside a wall dense with small objects` | 版式、海报 |
| **数量** | `one figure among a crowd of identical silhouettes` | 叙事、孤独感 |

**规则**：主对比**只选一个**。第二个维度只能当**辅助**，并且强度要明显弱于主对比。
三个以上同时拉满 = 画面重新变平。

## 对比的三个使用原则

1. **对比必须服务视线**：最强的对比点 = 你想让观者第一眼看到的地方。
   如果你的主体不是全图最亮 / 最饱和 / 最清晰的东西，构图就错了。
   **焦点是「对比最强的地方」，不是「最亮的地方」**：全图只允许**一处**最高对比，
   把它钉在主体上，背景里不许出现比它更亮的东西（除非那个更亮的东西就是焦点本身）。
2. **对比要有归属**：写清「谁对谁」——`the subject against the background`，
   而不是笼统地写 `high contrast`。
3. **对比需要留白来成立**：没有低对比的区域，高对比就不成立。
   写一句 `everything else stays low-contrast and quiet` 作为抑制项。

## 抑制项（最常被忘的一半）

对比是「一半加法、一半减法」。光加不减，画面只会更乱。必须写清**什么被压下去**：

- 背景：`background pushed two stops darker and desaturated`；
- 非主体：`the other figures stay as flat grey silhouettes`；
- 细节：`no detail on the far wall`；
- 颜色：`everything except the accent stays within one muted family`。

## 常见失败与修法

| 症状 | 根因 | 修法 |
| --- | --- | --- |
| 很满但很平 | 所有维度同强度 | 选一个主对比拉满，其余写抑制项 |
| 主体不突出 | 主体不是最强对比点 | 提主体明度/饱和度/清晰度，压环境 |
| 画面花 | 缺抑制项 | 补「背景压暗压饱和、非主体降细节」 |
| 极简做成空 | 只有减法没有对比 | 极简靠「一大一小 / 一亮一暗」制造张力 |
| 强调色污染全图 | 强调色用量没约束 | 写 `appears only on X`（一个物件） |
| 写了 `high contrast` 无效 | 空词 | 写「谁对谁、在哪一层」 |

## 自检清单

- [ ] 主对比只有一个，且有明确归属（谁对谁）；
- [ ] 主体是全图最强的对比点；
- [ ] 写了抑制项（什么被压下去）；
- [ ] 辅对比强度明显弱于主对比；
- [ ] 强调色数量与位置有约束；
- [ ] 没有 `high contrast` / `eye-catching` / `striking` 这类空词；
- [ ] 没有参数、没有多余解释。

## 示例

**输入**：「一张极简咖啡包装主视觉，要有冲击力但不花」

```text
A single matte black cylindrical coffee tin stands slightly right of center on a pale oatmeal
paper backdrop. The tin is the only dark shape in the frame, and everything around it is held two
stops lighter and heavily desaturated, so the eye lands on the cylinder before it reads anything
else. One narrow warm brass band wraps the middle of the tin and is the only saturated colour in
the image. Surfaces are limited to two: the tin's soft matte coating, which takes a single long
vertical highlight, and the paper's visible fibre texture in the near foreground. The backdrop
carries no pattern, no props and no second object; the shadow the tin throws to the right stays
soft and low-contrast, and the far edge of the frame fades out entirely.
```

## 依据

- 「找对比就找到了趣味点」、把对比当作构图起点：David duChemin《Find the Contrast, Find the
  Interest》。
- 明暗对比引导视线（注意力先落在亮处再移向暗处）：Canon《Creating the Illusion of Space and
  Depth》与常见明度分区教学。
- 冷暖对比承担情绪落差：影视色彩分析中对冷暖并置的通行用法。
- 对比需要「一半加法一半减法」：mood.md 协议把 Anti-References 作为独立一半的做法。
- 焦点 = 最高对比处、抑制项写法与「看起来有对比其实没有」的判别：
  改编自 [prompt-craft](https://github.com/Luxvanyu/prompt-craft)（MIT License, Copyright (c) 2026 Luxvanyu）。

## 边界

- 不执行脚本、不生成图片、不调 API。
- 不写参数；不写空泛形容词。
- 不复制具体作品构图，只描述可观察的对比关系。