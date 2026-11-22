---
name: krea2-editorial-longform
description: Assemble a Krea 2 editor-manual long-form prompt (roughly 1500–2700 words) the way the 白垩光 / K2 editorial sets do it — one motif block that decides composition, materials, light positions and typography, plus only a few bounded replacement slots (character identity, aspect, wardrobe parts, in-image type). Use when the user wants a poster-grade key visual, a future-luxury editorial scene, or a long Krea 2 prompt with palette percentages and five-layer depth rather than a short caption.
version: 1.0.0
---

# Krea 2 编辑级长文提示词（Editorial Longform）

Krea 2 的官方样例是「一段稠密 caption」；但社区跑出了一条更长的路线——**母题整块长文**：
一条母题（motif）一次性决定整张画面的构图、材质分区、光位与排版语言，只在少数**有界限的
替换位**上换内容。本 skill 就是这条路线的方法论与写法。

> 参考实现：[Comfyui-K2-Editorial](https://github.com/lingdongbudong/Comfyui-K2-Editorial)
> 的「白垩光 / 未来奢华编辑主视觉」母题库（553 条母题，每条 1500–2700 词英文长提示词，
> 一个母题决定整张画面，只做有限替换）。本 skill 提炼其**写作结构**，不复制其母题正文。

## 输出契约（先读这一节）

1. **只输出长文正文本身**：不要开头说明、结尾建议、解释与总结，不要 Markdown 代码块围栏，
   不要 `01 / 02` 这类段号（段号只用于你自己排结构）。
2. 正文用**英文**，且必须是**有语法的自然语言句子**——Krea 2 读的是 caption，
   长文只是「更长的 caption」，不是 tag 池。
3. **不写参数**：分辨率、宽高比、步数、CFG、采样器、种子、模型名一律不出现在正文里。
4. **不写负面词串**：要排除就把 1–3 条硬约束写成自然语言句子（`no second figure`）。
5. 用户已写死的母题、角色、画幅、画内文字**原样保留**，只替换四类替换位。
6. 体量按需求选：终端用户明确要短就降档，**不要**默认输出 2000 词。

## 何时使用

- 用户要**海报级 / 主视觉 / 杂志内页 / 发布会 KV**，且接受长提示词；
- 用户要「未来奢华 / 白垩光 / 编辑感 / 高级感」这类**整体调性**而不是单个主体；
- 已有短 caption，但画面撑不起版面：材质单一、没有色盘结构、没有排版语言；
- 需要批量生产同一调性、不同母题的一组图（母题可复用，替换位可批量灌）。

**不适用**：
- 用户只要一张普通图 / 头像 / 单件物品 → `krea2-prompt-writing` 的短句档或标准档；
- 二次元 / 动漫 → `krea2-anime-prompt`；
- 用户明确拒绝长提示词，或工作流有 token 上限 → 退回标准档，别硬写 2000 词。

## 核心原则：宁可整块，不要随机池

一条长文里的 25 段是**互相咬合**的：母题说「一点透视的横向长廊」，材质段就不能写「四面围合」；
光位说「左上单光源」，地面反射段就不能写「四周均匀打光」。所以：

- **一个母题 = 一个整体设计**，不做「场景池 × 光位池 × 材质池」的随机组合，
  否则立刻互相矛盾；
- **替换位要少而有界限**：角色身份、画幅、服装（按部位）、画内文字，四类足够；
- 新增内容只允许加在**它自己的层**里，不允许改动别层已经定死的结构。

## 长文骨架（25 段，可按母题删减，不可改顺序）

完整段落清单、每段的字数预算与写法要点见
`references/longform-25-sections.md`。这里是速览：

| # | 段 | 作用 | 字数预算 |
| --- | --- | --- | --- |
| 01 | 母题声明 | 一句话锁定整张画面的设计意图 | 30–60 |
| 02 | 媒介与渲染语言 | 3D 场景 / 平面海报 / 摄影棚，渲染质感 | 50–90 |
| 03 | 画幅与版面 | 横向 / 竖向、版心、留白比例 | 30–70 |
| 04 | 构图骨格 | 一点透视 / 中心对称 / 对角线，视线动线 | 80–140 |
| 05 | 巨构结构 | 最大的那个形体，尺度感怎么建立 | 100–180 |
| 06 | 中景构筑 | 第二层结构，与巨构的咬合方式 | 80–140 |
| 07 | 前景装置 | 压边的前景物件，制造纵深 | 60–110 |
| 08 | 地面 / 基座 | 材质、反射、接缝、磨损 | 70–120 |
| 09 | 角色身份锚点 | **替换位①**：谁、2–4 个高信息特征 | 80–150 |
| 10 | 角色姿态 | 姿态、重心、朝向、手的动作 | 70–120 |
| 11 | 服装（按部位） | **替换位②**：上装 / 下装 / 腿部 / 鞋 / 配饰 | 90–160 |
| 12 | 角色与空间的关系 | 人怎么被空间容纳（遮挡、投影、尺度对比） | 60–110 |
| 13 | 材质分区 A | 第一组材质：命名 + 触感 + 反光行为 | 70–120 |
| 14 | 材质分区 B | 第二组材质，与 A 的对比关系 | 70–120 |
| 15 | 材质分区 C | 第三组材质，通常是「无材质的空」 | 50–90 |
| 16 | 色盘与百分比 | 3–5 个颜色 + 各自的画面占比 | 50–90 |
| 17 | 光位 A：主光 | 方向、高度、色温、软硬 | 70–120 |
| 18 | 光位 B：补光 / 环境光 | 二次光源与它带来的色偏 | 50–90 |
| 19 | 光位 C：反射与溢出 | 光在材质上的二次行为 | 60–100 |
| 20 | 五层景深 | 前 / 中 / 后 / 更远 / 背景，各层清晰度 | 80–140 |
| 21 | 空气与介质 | 雾、尘、蒸汽、雨、体积光 | 50–90 |
| 22 | 排版语言 | **替换位③**：画内文字、字体气质、位置、材质 | 70–130 |
| 23 | 细节密度控制 | 哪里密、哪里空（防止糊成一团） | 50–90 |
| 24 | 硬约束 / 排除 | 1–3 条必须成立的规则 | 40–80 |
| 25 | 收束句 | 一句话回到整体调性 | 30–60 |

**总和控制在 1500–2700 词**。低于 1500 说明段没写透；高于 2700 通常是材质段重复了。

## 三种母题分支

| 分支 | 段数 | 特点 | 什么时候用 |
| --- | --- | --- | --- |
| **scene（3D 场景）** | 20–25 段 | 机位、材质分区、色盘百分比、五层景深齐全 | 主视觉、空间叙事、品牌 KV |
| **poster（平面海报）** | 12–18 段 | 保留版式与大标题，角色按海报语法适配 | 活动海报、唱片封面、杂志内页 |
| **short（短提示词）** | 4–8 段 | 每段短句，只换身份并追加一句服装说明 | 快速试方向、批量变体 |

选错分支是最常见的浪费：海报需求写成 25 段空间叙事，模型会给你一张「有海报文字的空间图」。

## 替换位规则（只有这四类）

1. **角色身份**：只替换身份锚点段里的角色描述；同时**剥掉**原文身份句里写死的原作服装
   （否则「选了 A 的衣柜」画出来还是 B 的制服）。
2. **画幅**：横向母题不能塞进竖屏——横向序列 / 一点透视 / 长排在竖屏会崩。
   竖屏要换成向上的结构、紧密取景、角色占比约 40%。
3. **服装（按部位）**：**只写母题描述到的部位**。母题只说外套领子，就只换上装；
   补一双鞋会把取景拉远，构图跟着变形。
4. **画内文字**：保留位置 / 字体 / 材质描述，只换文字内容；超过 3 个词就容易画错；
   完全不要文字时，把整段排版语言改写成「无排印、纯图像」的版面描述，而不是留空。

⚠ **母题里的服装如果出现在非服装段**（机位段、材质段、反射段），整篇要统一替换，
否则模型会同时读到两套衣服。替换要在**全文层**做，不是只改服装段。

## 色盘百分比怎么写

写成 `roughly 60% deep teal, 25% sodium orange, 15% bone white` 这种**可核对**的形式：

- 3–5 个颜色，总和 100%；
- 至少一个颜色是「暗部色」、一个「高光色」、一个「意外色」（用来打破单调）；
- 百分比与后面的材质 / 光位段必须自洽：说 60% 深青，就不能让主光把画面照成暖白。

## 自检清单

- [ ] 段落顺序没乱，缺的段是**整段删掉**而不是内容挪走；
- [ ] 色盘百分比总和 100%，且与光位、材质段不打架；
- [ ] 材质分区 2–4 个，其余表面明确写「平滑 / 干净」；
- [ ] 五层景深每层都有清晰度描述（不要五层都清晰）；
- [ ] 角色只占母题需要的位置，没有被服装描写拉远取景；
- [ ] 全文只有**一套**服装描述（替换后没有残留旧衣服）；
- [ ] 画内文字逐字加引号，≤3 个词；
- [ ] 没有 tag 串、`masterpiece` / `best quality` / `score_9` / `8k`、权重语法、
      分辨率 / 步数 / CFG；
- [ ] 没有开头说明、结尾建议、代码块围栏。

## 示例（节选，展示的是**结构**不是完整长文）

```text
01  This is a future-luxury editorial key visual built around a single motif: a chalk-lit
    colonnade that reads as one continuous white mass, interrupted only by the figure.
02  Rendered as a high-end 3D scene with matte chalk plaster, brushed aluminum and one
    polished black-lacquer plane, lit like an architectural photography shoot.
03  Composed for a 3:4 poster, the negative space above the figure held open for a title.
04  The structure runs on one-point perspective, the colonnade receding to a small bright
    aperture at the center; the eye enters at the lower right and stops at the figure.
…
16  The palette is roughly 62% chalk white, 20% cold graphite, 12% warm sodium leakage and
    6% oxidized copper — the copper is the only saturated note and appears once, on the clasp.
17  A single hard key light enters high from the upper left at roughly 35 degrees, cool at
    5600K, so every column throws a long shadow to the lower right…
```

## 边界

- **不执行**脚本、不生成图片、不联网；只产出文本。
- 不复制上游母题库正文；需要具体母题时由用户提供或自行撰写。
- 不做版权角色考据；角色名只作描述性标识，商用需自行取得授权。
- 用户工作流有 token 上限时主动降档，不要硬塞 2000 词。
