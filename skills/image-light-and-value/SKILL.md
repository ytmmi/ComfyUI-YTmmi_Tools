---
name: image-light-and-value
description: Design the light and the value structure of an image prompt - where light comes from and how hard it is, how many stops the scene holds, which surfaces catch the highlight and which fall into shadow, what colour the shadows take, and how contrast guides the eye to the subject. Use when a render looks flat, evenly lit or grey, when the subject does not separate from the background, when a scene needs a named light setup (window, overcast, golden hour, single hard key, practicals at night), or when the image needs a deliberate low-key or high-key treatment. Model-agnostic: the same words work as tags or as natural language.
version: 1.0.0
---

# 光影与明度（Light & Value）

**光影是提示词里第二便宜、收益最高的一层**（仅次于构图）：同样的主体与配色，只把「光从哪来、
多硬、落在哪、影子什么颜色」写清楚，画面立刻从「平面涂色」变成「有空间的一帧」。

本 skill 只管**光与明度结构**：光源、光质、明度分层、投影、反差、高低调。
不碰构图取景（→ `image-composition`）、不碰色相关系（→ `image-color-harmony`）、
不碰画风媒介、不碰负面词体系。

**与模型无关**：下面的英文词可以当 tag 也可以写进句子；标 † 的更适合放进自然语言。

完整词表、光位布置、明度分层模板与失败修法见
`references/image-light-vocabulary.md`；本文件讲判断与流程。

## 何时使用

- 画面**平 / 灰 / 均匀亮**，像贴图没打光；
- 主体**陷进背景**，前后分不开；
- 影子**没有方向**，或者到处都在发光；
- 需要指定一种**光位**（窗光 / 阴天 / 黄金时刻 / 单硬光 / 夜景实用光源 / 顶光 / 轮廓光）；
- 需要**低调整体压暗**或**高调通透**的明度处理；
- 想用光影**引导视线**（亮的地方先被看到）；
- 已经写了 `cinematic lighting` 但完全没效果。

**不适用**：只调取景 → `image-composition`；只调颜色关系 → `image-color-harmony`；
只调风格笔触 → 风格类 skill；角色身份 → 角色类 skill。

## 输出契约

默认**只输出最终提示词正文 / 光影方案**，不寒暄、不解释、不复述需求：

- **默认只出正面提示词**；只有用户明确要负面词、或明说自己那边没有负面词时才追加两段式；
- 不输出 `Suggested settings`、不写分辨率 / 步数 / CFG / 采样器；
- 用户要的是**光影方案**（自己还要写提示词）时，改用短条目：`主光 / 次光 / 明度 / 影子 / 反差` 各一行；
- 用户已指定光位或时间时**不覆盖**，只补影子方向与明度关系；
- 用户用中文提问时，**提示词正文仍用英文光位词**，不要逐句翻译。

## 一束光要回答的五个问题

只写 `dramatic lighting` 等于没写。一束能用的光必须能回答：

| # | 问题 | 写成什么 |
| --- | --- | --- |
| ① | 光源是什么、在哪 | `a single low window on the left` / `one sodium street lamp above and behind` |
| ② | 多硬 / 多大 | `hard`（小光源、边缘锐利）/ `soft`（大面积、过渡长）/ `diffused`（阴天） |
| ③ | 什么颜色 | `cool daylight at roughly 5600K` / `warm tungsten` / `sickly green fluorescent` |
| ④ | 照亮哪些面、跳过哪些面 | `lits the near cheek and the collarbone, leaving the far side of the face in shadow` |
| ⑤ | 影子落在哪、什么颜色 | `casts a long shadow to the lower right, with the shadow side picking up cool blue from the sky` |

**①–⑤ 缺一个，光就会「消失」**：最常见的是只有 ①②（写了光源与软硬），没有 ④⑤，
结果光被模型平均分配到每个面上。

## 明度结构：先分三档，再谈细节

画面能不能读，取决于**明度有没有分层**。任何一张图先定三档：

| 档 | 占比建议 | 写什么 |
| --- | --- | --- |
| 亮部（高光 / 受光面） | 10–25% | 高光形状、材质反光的锐度 |
| 中间调 | 40–60% | 主色、皮肤、面料的主体表现 |
| 暗部 | 25–40% | 影子颜色、是否有细节、是否压死 |

**两条硬规则**：

1. **暗部必须有颜色**：写 `shadows lean cool teal` / `deep indigo`，而不是 `dark`。
   纯黑或没有颜色的暗部是「发灰」与「廉价」的主要来源。
2. **高光必须有形状**：写 `a narrow specular streak along the rim` / `a soft rectangular window shape on the floor`，
   而不是 `bright`。高光形状是材质与光源的证据。

## 光位速查（选一个，不要叠三个）

| 光位 | 写法要点 | 典型效果 |
| --- | --- | --- |
| **窗光** | 单侧大窗 + 地面光斑 + 远侧冷影 | 室内、安静、有呼吸感 |
| **阴天漫射** | 无方向、影子极淡、饱和度高但不刺 | 纪实、产品、清冷 |
| **黄金时刻** | 低角度暖侧光 + 长影 + 冷檐影 | 温暖、电影感 |
| **单硬光** | 小光源 + 边缘锐利的影子 + 大面积压暗 | 戏剧性、编辑感 |
| **夜景实用光源** | 钠灯 / 霓虹 / 招牌，各有色相，湿面反射 | 城市、赛博、情绪 |
| **轮廓光 / 逆光** | 背后强光 + 边缘亮线 + 正面压暗 | 剪影、氛围、分离主体 |
| **顶光** | 上方硬光 + 眼窝与下颌阴影 | 压迫、审讯、不安 |
| **反光板 / 次光** | 一块冷或暖的填充，只影响暗部 | 去死黑、保留细节 |

**主光只能有一个**。次光与反射只允许**改暗部**，不允许再造一个独立方向。

### 具名布光（人像 / 单人场景，直接写名字比描述更稳）

影视与摄影里有几个**已被命名**的布光，写名字比解释更快，模型也认得：

| 名称 | 光位 | 特征 | 情绪 |
| --- | --- | --- | --- |
| **Rembrandt** | 主光 45° 侧上 | 暗面颊上有一个三角光斑 | 古典、戏剧 |
| **Butterfly** | 正上方偏前 | 鼻下蝶形小影 | 美妆、时尚、光洁 |
| **Split** | 主光 90° 正侧 | 半边脸全暗 | 悬疑、冲突、黑色电影 |
| **Loop** | 主光 30–45° 侧上 | 鼻侧小三角影 | 最通用的讨喜人像 |
| **Rim / Edge** | 逆光 | 主体边缘亮线，与背景分离 | 科幻、圣感、分离 |

出处：StudioBinder《Film Lighting Terms》对 Key / Fill / Back / Rim / Practical / Hard / Soft /
Motivated 的定义，以及 Proko 对明度键的分档。

## 反差：用对比度引导视线

- **高反差**：明暗跨度大、暗部压死、高光过曝一点——戏剧、强冲击、广告；
- **低反差**：跨度小、整体灰、细节多——纪实、日系、静谧；
- **局部反差**才是关键：**主体高反差、环境低反差**，视线自然落到主体上；
  反之环境越花，主体越要压。

写法：`the face keeps the only strong value contrast in the frame while the room stays low-contrast`。

## 常见失败与修法

| 症状 | 根因 | 修法 |
| --- | --- | --- |
| 画面平、像贴图 | 只有 ①②，没有 ④⑤ | 补「照亮哪些面」与「影子落在哪」 |
| 主体陷进背景 | 明度或饱和度没分家 | 主体提反差、背景压饱和压细节 |
| 到处都在发光 | 主光不唯一 | 只留一个主光，其余降为反射 |
| 发灰、脏 | 暗部没有颜色、高光没有形状 | 暗部指定色相；高光写形状 |
| 影子方向矛盾 | 光源写了但影子没约束 | 写「影子朝右下方」，并检查所有物体一致 |
| 脸部一片死黑 | 只有主光没有次光 | 加一句反射光，只影响暗部 |
| 写了 `cinematic lighting` 没用 | 空词 | 换成光源 + 软硬 + 方向 + 后果 |

## 自检清单

- [ ] 五个问题都回答了（来源 / 软硬 / 颜色 / 照亮面 / 影子落点）；
- [ ] 只有一个主光，次光只改暗部；
- [ ] 暗部有颜色，高光有形状；
- [ ] 三档明度比例大致成立，没有整张同一个灰度；
- [ ] 主体与环境的反差有区分（主体高、环境低）；
- [ ] 没有 `beautiful lighting` / `cinematic lighting` 这类空词；
- [ ] 没有参数、没有负面词串（除非用户要）；
- [ ] 只有最终正文，没有解释与结尾建议。

## 示例

**输入**：「雨夜便利店门口，一个女孩在等雨，霓虹反光」（要氛围不要平）

```text
A medium shot at eye level from just outside the awning of a convenience store at night. A young
woman in a damp grey hoodie waits under the fluorescent tube, hugging a thin plastic bag against
her chest. A single cold white tube above her is the key light: it falls almost straight down, so
the top of her hair and the ridge of her nose take the brightest highlight while her eye sockets
and jaw stay in a narrow band of shadow. Warm sodium light spills from the far end of the street
as the only other source, catching the wet asphalt in long broken streaks of orange that reach her
shoes. Her shadow falls almost straight down and slightly toward the camera, and the shadow side
of her face carries a cool blue-violet fill from the open night sky rather than turning black.
Behind her, the glass door throws back a dim doubled reflection of the awning, and the street
beyond dissolves into rain haze at a much lower contrast than her face.
```

## 依据

- 布光术语（Key / Fill / Back / Rim / Ambient / Practical / Bounce / Hard / Soft / Motivated /
  Accent、High key / Low key / Chiaroscuro、Rembrandt / Split / Loop / Butterfly / Silhouette）：
  StudioBinder《Film Lighting Terms — A Complete Filmmaker's Glossary》。
- 明度键（低 / 中 / 高调）作为「整张图在明度标尺上的位置」：John MacDonald《Understanding Value
  Keys for Painting Landscapes》、Proko《How to Organize Values》。
- 「具名布光优于空词」的提示词实践：社区 cinematic-prompting 指南。

## 边界

- 不执行脚本、不生成图片、不调 API。
- 不写参数（步数 / CFG / 采样器 / 分辨率由工作流决定）。
- 不规定模型语法（tag 或自然语言随模型），只规定「光该怎么写」。
- 不复制任何具体作品的光位构图，只描述可观察的光学现象。