---
name: image-mood-and-atmosphere
description: Build the emotional register and atmosphere of an image prompt - the feeling the frame should carry, the palette temperature and weather that produce it, the ambient medium (haze, dust, steam, rain), the pace implied by the composition, and the anti-references that would break it. Use when a render is technically correct but emotionally neutral, when the user asks for a mood (quiet, melancholic, nostalgic, tense, hopeful, lonely, cinematic), or when a scene needs atmosphere rather than more objects. Model-agnostic: mood is carried by described conditions, not by adjectives.
version: 1.0.0
---

# 情感与意境（Mood & Atmosphere）

「没有感觉」通常不是画得不对，而是**画面里没有任何东西在承载感觉**：
光是平的、空气是干净的、动作是静止的、颜色是中性的。

情感不是形容词，是**条件**：什么温度的光、什么湿度的空气、什么速度的动作、什么距离的关系。

本 skill 只管**情感与意境**：情绪基调、色温与天气、空气介质、节奏、以及反面参照（不要什么）。
不碰叙事内容（→ `image-subject-and-story`）、不碰光位设计（→ `image-light-and-value`）、
不碰配色关系（→ `image-color-harmony`）。

## 何时使用

- 画面**技术上没毛病，但看着没感觉**；
- 用户给的是情绪词（安静 / 孤独 / 怀旧 / 紧张 / 温柔 / 压抑 / 辽阔）；
- 场景已经写满，但**缺空气**（干净得像渲染图）；
- 需要在**同一主体**下切换情绪（系列图的不同氛围）；
- 出图「太满太亮太热闹」，与想要的调性相反。

## 输出契约

- **只输出提示词正文 / 情绪方案**，不解释、不复述需求；
- 要方案时用短条目：`基调 / 温度 / 空气 / 节奏 / 反面参照` 各一行；
- 默认只出正面提示词；用户明确要负面词、或明说自己那边没有负面词时才追加两段式；
- **不写 `emotional` / `atmospheric` / `moody` 作为情绪本身**——它们是结论，不是方法；
- 不写参数；不写 `cinematic` 这类空词（要写具体的光、空气与色温）。

## 情绪由五个条件承载（缺一个就回到中性）

| 条件 | 怎么写 | 指向的情绪 |
| --- | --- | --- |
| **色温** | `cool morning light, shadows blue` / `warm tungsten, amber cast` | 冷 = 疏离 / 清冷；暖 = 亲近 / 回忆 |
| **空气介质** | `thin haze`, `dust in the light`, `steam`, `fine rain`, `smoke` | 有介质 = 有呼吸；干净 = 广告感 |
| **明度键** | 整体压暗（low key）/ 整体提亮（high key） | 暗 = 压抑 / 神秘；亮 = 轻盈 / 日常 |
| **节奏** | `still, nothing moving`, `mid-gesture with fabric caught` | 静 = 沉思；动 = 紧张 / 活力 |
| **距离** | `with a metre of empty floor between them` | 近 = 亲密；远 = 疏离 |

**写三个就成立，写五个会饱和**。

## 三档明度键（美术与摄影通用）

| 键 | 定义 | 情绪 | 画面上怎么落 |
| --- | --- | --- | --- |
| **Low key** | 大部分落在暗部，只有小面积亮 | 压抑、神秘、庄重 | 暗部占 60%+，亮部只做引导 |
| **Mid key** | 均匀分布，中间调为主 | 中性、纪实、日常 | 避免极端明暗 |
| **High key** | 大部分落在亮部，阴影极淡 | 轻盈、通透、洁净 | 阴影透明不压死，饱和降 |

写法：`the whole frame sits in a low key, with only the window and her hands carrying light`。

## 空气介质：最便宜的「意境」

干净的画面读作**渲染图**；有一点介质就变成**现场**：

- 室内：`dust drifting in a single beam`、`steam from a cup`、`smoke hanging at shoulder height`；
- 室外：`thin rain`, `morning fog lying low`, `heat shimmer`, `snow falling slow and large`；
- 夜晚：`haze around the street lamps`, `breath visible in the cold`。

**规则**：介质必须**影响画面**——挡住远景、改变对比、吃进光线。只写 `foggy` 不写后果，等于没写。

## 情绪 → 配方（选一个，可微调）

| 想要的 | 色温 | 空气 | 明度键 | 节奏 |
| --- | --- | --- | --- | --- |
| 安静 / 疗愈 | 中性偏冷 | 薄雾 | high key | 静止 |
| 怀旧 / 温柔 | 暖（琥珀 / 棕） | 尘、薄烟 | mid key | 缓慢 |
| 孤独 / 疏离 | 冷蓝 | 雨、雾 | low key | 静止 |
| 紧张 / 压迫 | 冷绿 / 冷白 | 无（干净反而更冷） | low key | 悬停（将动未动） |
| 辽阔 / 崇高 | 冷 + 一点暖 | 大气透视 | mid key | 静止 |
| 希望 / 清晨 | 冷蓝 + 暖底 | 薄雾 | high key | 刚启动 |
| 神秘 / 梦 | 紫 / 青 | 浓雾 | low key | 悬浮 |

## 反面参照（Anti-reference）：最容易被忘的一半

情绪同样靠**排除**成立。写下「不要什么」，比写十个「要什么」更省力：

- 要安静 → 排除 `crowds, signage, saturated colour, motion blur`；
- 要高级 → 排除 `plastic sheen, oversaturated neon, stock-photo smiles`；
- 要真实 → 排除 `perfect symmetry, uniform light, HDR`。

有负面框时写进负面；没有负面框时写一句自然语言排除（`no signage anywhere`）。

## 常见失败与修法

| 症状 | 根因 | 修法 |
| --- | --- | --- |
| 没感觉 | 五个条件一个没写 | 至少补色温 + 空气 + 明度键 |
| 太满太亮 | 明度键错了 | 换 low key，压暗部，减饱和 |
| 像渲染图 | 空气太干净 | 加尘 / 雾 / 水汽，并写出它挡住了什么 |
| 情绪靠形容词 | 只写 `melancholic` | 换成条件：冷光、雨、静止、距离 |
| 越加越乱 | 五个条件全拉满 | 只留三个，其余归零 |
| 系列图情绪不稳 | 没有固定配方 | 固定色温 + 明度键，只变内容 |

## 自检清单

- [ ] 写了色温、空气介质、明度键中的至少三个；
- [ ] 空气介质写出了它对画面的影响（挡远景 / 吃光 / 降对比）；
- [ ] 明度键与想要的情绪一致；
- [ ] 节奏（静 / 动 / 将动未动）明确；
- [ ] 有反面参照（自然语言或负面词）；
- [ ] 没有 `emotional` / `moody` / `atmospheric` / `cinematic` 当方法用；
- [ ] 没有参数与多余解释。

## 示例

**输入**：「清晨的海边小屋，一个人坐着，安静但不要孤独」

```text
Just after sunrise, in a mid key: the light is cool and thin, the sky holding a pale blue that
warms only near the horizon, and the shadows under the eaves stay transparent rather than black.
A low haze lies over the water and softens the far headland into a single grey-blue band, so the
distance reads as distance without turning dramatic. A man sits on the step of a small timber
house with a mug balanced on his knee, both hands around it, and nothing else in the frame is
moving: the water is flat, the curtain inside hangs still, and a thin line of steam rises from
the mug and bends slightly in the offshore breeze. The palette stays within cool grey-blue, wet
timber and one warm note from the mug. There is no signage, no other person and no boat on the
water.
```

## 依据

- 明度键（low / mid / high key）与「整体落在明度标尺的哪一段」：John MacDonald《Understanding
  Value Keys for Painting Landscapes》(OutdoorPainter)、Proko《How to Organize Values》。
- 情绪映射到光的条件（色温、软硬、阴影行为、空气）的写法：`mood.md` 协议
  （Owl-Listener/perceptual-protocols）的 Essence / Colour / Texture / Emotional Register /
  Anti-References 五段映射，以及 `cinematic-prompting` 的「具名布光优于空词」。
- 反面参照（anti-reference）作为独立一半的做法：同上 mood.md 协议。

## 边界

- 不执行脚本、不生成图片、不调 API。
- 不写参数；不用形容词代替条件。
- 不替用户编造真实事件或数据；不复制具体作品画面。