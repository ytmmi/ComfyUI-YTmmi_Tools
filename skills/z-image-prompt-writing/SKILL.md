---
name: z-image-prompt-writing
description: Write Z-Image (造相, Alibaba Tongyi 6B S3-DiT) text-to-image prompts in natural language, and pick the right variant and settings — Turbo's 8-step no-CFG path versus Base's 50-step CFG 3–5 path with a real negative prompt. Use when the user asks for Z-Image / 造相 / Z-Image-Turbo images, wants photorealistic or richly styled stills, needs to know whether a negative prompt is allowed, or wants a prompt that keeps the model's high diversity instead of collapsing onto one look.
version: 1.0.0
---

# Z-Image 提示词写作（Z-Image / 造相）

Z-Image 是阿里巴巴通义实验室的 **6B** 图像模型，架构为 **S3-DiT**（文本、视觉语义 token、
图像 VAE token 在序列级拼成统一输入流）。它读**自然语言**，擅长写实质感与**中英双语文字渲染**。

## 先分四个变体（写法与参数都不一样）

| 变体 | 步数 | CFG | 负面提示词 | 定位 |
| --- | --- | --- | --- | --- |
| **Z-Image-Turbo** | 8 | **无（guidance 0）** | **不适用** | 蒸馏版，质量最高、速度最快、**多样性低** |
| **Z-Image**（Base/SFT） | 30–50 | **3–5** | **有效，且模型对负面词敏感** | 基础版：美学丰富、**多样性高**、可微调 |
| **Z-Image-Omni-Base** | 50 | 有 | 有效 | 生成 + 编辑的原始底座 |
| **Z-Image-Edit** | 50 | 有 | 有效 | 指令式图像编辑 |

**这条必须先判断**：Turbo 没有 CFG 分支，**写负面提示词等于没用**（ComfyUI 里那段文本
根本不参与）；Base / Omni / Edit 有 CFG，**负面词是真的生效**，而且官方说明它「对负面提示词敏感」——
所以 Base 上负面词要**短而准**，堆一大串反而会削掉画面。

## 输出契约

1. **只输出提示词正文**（自然语言，一个或几个连贯段落），不要开头说明、结尾建议、解释、
   总结、Markdown 代码块围栏。
2. 用户用中文提问**不代表**要中文提示词：描述用**英文**更稳；但**画面里要出现的文字**必须
   保留它的原语言（中文就写中文，英文就写英文），并加引号。
3. **不写参数**：不写步数、CFG、采样器、种子、分辨率、模型文件名。被问到就回一句
   「由工作流设置决定（Turbo 8 步无 CFG；Base 30–50 步、CFG 3–5）」。
4. **需要负面词时单独给**，并且只在 Base / Omni / Edit 上给；Turbo 上直接说明「Turbo 无 CFG，
   不接收负面词，请改用正面描述」。
5. 用户给定的主体、人数、动作、服装、场景、风格、画面文字**原样保留**，只补空缺。

## 写作骨架（六段，缺段跳过）

| 段 | 写什么 | 注意 |
| --- | --- | --- |
| ① 媒介 + 摄影/绘画语言 | `A 35mm photograph of …` / `A gouache illustration of …` | 只给**一个**主媒介，别混 `photo` + `oil painting` |
| ② 主体与身份 | 2–4 个可见特征 | 写实类用生活阶段，不写具体年龄数字 |
| ③ 动作与因果 | 正在做什么，**结果可见** | 手要有接触对象；动作要有后果（褶皱、水花、影子） |
| ④ 空间与机位 | 前/中/后景、从哪看、多高 | 写清谁挡谁、视线朝向 |
| ⑤ 光与材质 | 光源位置、色温、影子方向、材质手感 | `soft window light from the left` 而不是 `good lighting` |
| ⑥ 文字与收束 | 画面文字逐字加引号；最后一条硬约束 | 无文字就明说「画面中没有文字」 |

官方示例的写法就是**自然语言里夹具体名词短语**：
`Young Chinese woman in red Hanfu, intricate embroidery. Impeccable makeup, red floral forehead
pattern. Elaborate high bun, golden phoenix headdress … Soft-lit outdoor night background,
silhouetted tiered pagoda, blurred colorful distant lights.`
—— 有名有姓的细节 + 光位 + 背景层次，**不是** `masterpiece, best quality` 这种空词。

## Turbo 与 Base 的写法差异

| 维度 | Turbo（8 步，无 CFG） | Base（30–50 步，CFG 3–5） |
| --- | --- | --- |
| 提示词长度 | 中长即可；它按原样读，**不会自动扩写** | 可以更长，细节越多越稳 |
| 多样性 | **低**：同提示词反复出图差别小 | **高**：同提示词会给不同构图与身份 |
| 排除不需要的东西 | 只能**正面写**（`no text anywhere` 这类自然语言约束） | 用**简短负面词**（`blurry, extra fingers`），别堆长串 |
| 想试方向 | 需要改提示词本身 | 可以先跑几条看多样性，再收敛 |
| 微调适配 | 不支持（N/A） | 适合做 LoRA / 微调底座 |

## 推理型需求（Prompt Enhancer 的用法）

官方强调 Z-Image 有**提示词增强与推理**能力：它能从描述里推出「世界知识」而不是只照字面画。
所以你可以直接写**需求**而不只是外观，例如：

- `A cozy reading nook for a rainy afternoon, the kind a librarian would build for herself`
  —— 让模型自己补出书架、暖灯、雨窗；
- `A street-food stall that looks like it has been there for thirty years`
  —— 「三十年」会转成磨损、油渍、褪色招牌这些可见证据。

但**不要**把推理当借口省掉关键约束：人数、朝向、画面文字、品牌/型号仍然要写死。

## 文字渲染（Z-Image 的强项，但别滥用）

- 每个字都要**逐字加引号**，并写位置、字号层级与换行：
  `a shop sign reading "老王面馆" in red lacquer characters above the door`。
- 中文按中文写、英文按英文写，**不要**把中文音译成英文去画。
- 一句话文案控制在 **2–8 个字**（中文）/ **1–3 个词**（英文）最稳；长句容易漏字或错字。
- 需要大量排印 / 海报版式 / 双语对照时，改用 `z-image-bilingual-text`。

## 画幅与分辨率

画幅属于工作流参数，**不写进提示词**。ComfyUI 模板默认 1024×1024 起，
常用比例 1:1 / 4:3 / 3:4 / 16:9 / 9:16；高清需求在采样前放大分辨率即可。

## 常见失败与修法

| 症状 | 根因 | 修法 |
| --- | --- | --- |
| Turbo 上写了负面词但没用 | Turbo 无 CFG | 删掉负面词，改成正面描述 |
| Base 上负面词越写越多、画面越差 | 官方说明 Base **对负面词敏感** | 负面词压到 3–6 个，只留真正要压的 |
| 画面「很 AI」、通篇空词 | 用了 `masterpiece` / `8k` / `best quality` | 换成具体材质、光位、镜头语言 |
| Turbo 反复出图几乎一样 | Turbo 多样性低是设计如此 | 想探索就换 Base，或改提示词的关键词 |
| 中文写成乱码 / 缺笔画 | 文字太长或没加引号 | 压字数、逐字加引号、写清位置与字体气质 |
| 主体被环境吃掉 | 空间层次没写 | 补前景/中景/远景与遮挡关系 |
| 手部/接触变形 | 没写接触对象与受力 | 写「手抓着什么、在哪、结果如何」 |

## 自检清单

- [ ] 先确认了变体：Turbo 不写负面词，Base/Omni/Edit 才写；
- [ ] 正文是自然语言，没有 tag 串、没有 `masterpiece` / `8k` / `best quality`；
- [ ] 没有参数（步数 / CFG / 采样器 / 种子 / 分辨率）；
- [ ] 主体有 2–4 个可见特征，动作有可见后果；
- [ ] 光有方向也有后果；空间有前后层次；
- [ ] 画面文字逐字加引号、给了位置与层级；无文字时明确说了没有文字；
- [ ] 用户给的主体、人数、场景、风格一个没丢，也没多出他没要的东西；
- [ ] 没有开头说明、结尾建议、代码块围栏。

## 示例

**输入（Turbo）**：「雨夜的老面馆门口，一个穿雨衣的外卖员在等出餐，招牌要有字」

**输出**：

```text
A 35mm photograph of a small noodle shop entrance on a rainy night. A delivery rider in a damp
yellow raincoat stands just under the awning, one hand holding a phone up against the drizzle, the
other steadying a thermal bag at his hip; water beads on the bag's strap and runs off the hem of
his coat. Above the door, a red lacquer sign reads "老王面馆" in weathered characters, one corner
of the panel chipped so the pale wood shows through. Warm tungsten light spills from inside the shop
and lands on the wet pavement in a long yellow rectangle, where the rider's shadow breaks across a
shallow puddle. Behind him, the street dissolves into blue rain haze and two blurred scooter
headlights. Steam curls out of a vent above the kitchen window and disappears into the dark.
```

**输入（Base，需要排除多余文字）**：「陶艺工作坊，女陶艺师拉坯，不要任何文字」

**输出（正文）**：写实摄影风描述（机位在她左侧手部高度、双手对抗式接触泥坯、侧窗光、
腕下淡影），结尾一句 `There is no text, lettering, or signage anywhere in the frame.`

**输出（负面词，仅 Base）**：

```text
Negative prompt: text, watermark, letters
```

## 边界

- **不执行**脚本、不调 API、不生成图片；只产出文本。
- 不给参数调优建议（步数 / CFG / 采样器由工作流决定；Base 官方参考 30–50 步、CFG 3–5）。
- 不做版权角色考据；角色名只作描述性标识。
- 参考图编辑（Z-Image-Edit / Omni-Base）不在本 skill 范围，需要时按编辑指令写，并同样遵守变体差异。
