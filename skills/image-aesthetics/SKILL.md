---
name: image-aesthetics
description: The entry point for the model-agnostic aesthetics layer of an image prompt - composition, colour theory, contrast, light and value, space and depth, subject and story, mood and atmosphere. Explains what each layer decides, the order to fix them in, which skill to load for a given symptom, and how to combine them without the layers contradicting each other. Use when an image looks wrong but it is unclear which layer is at fault, when several aesthetic problems overlap, or when designing a repeatable aesthetic workflow for a prompt library.
version: 1.0.0
---

# 通用美学：入口与分层（Image Aesthetics）

「画面不好看」几乎从来不是一个问题，而是**七层里某几层没决定**。
本 skill 是这一层的**路由与顺序**：先判断问题在哪层，再读对应 skill，避免几个 skill 各说各话。

## 七层美学（每层只决定一件事）

| 层 | 决定什么 | 对应 skill | 典型症状 |
| --- | --- | --- | --- |
| **构图** | 从哪看、看多大、主体在哪 | `image-composition` | 主体太小 / 全挤正中 / 没前后 |
| **对比** | 先看什么、什么被压下去 | `image-contrast` | 很满但很平 / 没有重音 |
| **光影与明度** | 光从哪来、明暗怎么分 | `image-light-and-value` | 平 / 灰 / 影子没方向 |
| **空间与虚实** | 有几层、什么清晰什么糊 | `image-space-and-depth` | 像纸片贴背景 / 远景一样清楚 |
| **色彩理论** | 谁是主色、怎么配、暗部什么色 | `image-color-harmony` | 发灰 / 刺眼 / 只剩一个调子 |
| **主题与叙事** | 这张图在说什么 | `image-subject-and-story` | 漂亮但空 / 主角不明 |
| **情感与意境** | 什么感觉、什么空气 | `image-mood-and-atmosphere` | 技术上没毛病但没感觉 |

另有 `image-artist-chain`（画师串），**只对二次元生效**，不属于通用层，不要把它套在写实上。

**这九支是「通用基线层」：每一组、每个模式的清单里都会完整加载**，不属于任何单一模型家族。
换句话说，只要工作流接了 skills管理器，无论选的是 H3 / Krea2 / MOSS / Z-Image / Anima 还是
Qwen-Image，这一层都在——**它是跨家族共用的图像工艺基线，不是可选附件**。
家族 skills 负责「这个模型怎么说话」，这一层负责「这张画怎么好看」。

## 修的顺序（从大到小，不要反着来）

```text
1 主题与叙事   —— 先说清这张图在说什么（说不清就别往下做）
2 构图         —— 定取景：谁在画面里、多大、从哪看
3 空间与虚实   —— 定层次：前景 / 主体 / 远景，谁清晰
4 光影与明度   —— 定光与明暗：光源、软硬、影子落点、明度键
5 对比         —— 定重音：主对比是什么、什么被压下去
6 色彩理论     —— 定色：主色 / 对比色 / 强调色、暗部颜色
7 情感与意境   —— 定空气与节奏：色温、介质、反面参照
```

**为什么是这个顺序**：前面的层决定后面层的自由度。
主题没定就调色，等于给一张不知道在说什么的图配颜色；构图没定就调光，光会落在错的地方。

## 症状 → 先查哪一层

| 你看到的 | 先查 | 再查 |
| --- | --- | --- |
| 平、灰、像贴图 | 光影与明度 | 空间与虚实 |
| 很满但很平 | 对比 | 构图 |
| 主体不突出 | 对比 | 构图、光影 |
| 像纸片贴背景 | 空间与虚实 | 光影 |
| 颜色脏 / 刺眼 | 色彩理论 | 光影（暗部颜色） |
| 漂亮但空 | 主题与叙事 | 对比 |
| 没感觉 | 情感与意境 | 光影、色彩 |
| 不知道先看哪 | 构图 | 对比 |

**一次只改一层**，否则无法判断是哪一层起作用（与调参同理）。

## 叠加纪律（最重要的一节）

七层同时拉满 = 画面重新变平。叠加时守四条：

1. **每层只出一个决定**：一个主光、一个主对比、一个主色关系、一个主题。
2. **下层服从上层**：光位服从构图（光要落在你想让人看的地方）、色彩服从对比、
   空气服从中景与远景的分层。
3. **矛盾时砍新加的**：已经写了暖光又加冷调，就砍冷调，不要在矛盾里找折中。
4. **有明确的抑制项**：至少写一处「什么都不在那里」——空墙、无文字、无第二人。

## 输出契约（所有美学 skill 共用）

- **只输出提示词正文**，不解释、不复述需求、不加标题与代码围栏；
- 默认只出正面提示词；用户明确要负面词、或说自己那边没有负面词时才追加两段式；
- **不写参数**（分辨率 / 步数 / CFG / 采样器 / LoRA 权重由工作流决定）；
- **不规定模型语法**：同一批英文词可以当 tag、也可以写进句子，语法随模型；
- 用户已指定的项**不覆盖**，只补它空着的部分。

## 词汇的两种写法

- **tag 写法**：`close-up, low angle, rim light, teal shadows` —— 适合 tag 系模型；
- **自然语言写法**：`the light comes from a low window on the left, so her shadow falls right`
  —— 适合 caption 系模型（Krea 2 / H3-Image / MOSS / Z-Image 等）。

**同一套判断，两种落笔**。不确定模型吃哪套时，写成**短句 + 关键名词**这种混合体，两边都读得懂。

## 常见整体失败

| 症状 | 根因 | 修法 |
| --- | --- | --- |
| 每张图风格都飘 | 没有固定的层决策 | 把「主光 + 明度键 + 主色关系」固化成模板 |
| 加了 skill 反而更差 | 多层同时拉满 | 回到「一次只改一层」 |
| 画面很「AI」 | 缺空气、缺瑕疵、缺抑制项 | 查情感与意境的反面参照 |
| 套错模型写法 | 用了 tag 语法写 caption 模型 | 换自然语言写法 |

## 自检清单

- [ ] 能一句话说出这张图在说什么（主题层已定）；
- [ ] 七层里**每层最多一个决定**，没有互相打架；
- [ ] 至少一处抑制项；
- [ ] 写法与目标模型匹配（tag / 自然语言）；
- [ ] 没有参数、没有空词、没有多余解释；
- [ ] 只输出了最终正文。

## 依据

- 布光与明度术语：StudioBinder《Film Lighting Terms》；明度键：Proko《How to Organize Values》、
  John MacDonald《Understanding Value Keys》。
- 情绪 → 条件（色温 / 介质 / 明度 / 反面参照）的映射：`mood.md` 协议
  （Owl-Listener/perceptual-protocols）。
- 单帧叙事与缺席叙事：Magnum《Telling Stories: the Single Image vs. the Series》、
  负空间作为 absence 工具的符号学研究。
- 对比作为构图起点：David duChemin《Find the Contrast, Find the Interest》。

## 边界

- 不执行脚本、不生成图片、不调 API。
- 不绑定任何具体模型；模型专属写法由各家族的 skill 负责。
- 不复制具体作品的画面与构图。