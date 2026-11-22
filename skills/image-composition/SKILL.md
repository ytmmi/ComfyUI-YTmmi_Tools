---
name: image-composition
description: Fix and design framing in image-generation prompts with shot size, camera angle, view direction, subject placement, visual hierarchy, depth layering, negative space and special lenses. Use when a render puts the subject too small, centers everything, lets characters overlap without hierarchy or lets the background steal focus, and when a portrait, full-body character, poster or key visual, group shot or scenery-led image needs its framing rebuilt from prompt text alone. Model-agnostic: the same composition words work as tags or as natural language in any diffusion model.
version: 1.2.0
---

# 图像构图（Image Composition）

构图是提示词里**最便宜、收益最高、又最容易被忽略的一层**：同样的主体、场景与风格描述，
只改景别、机位、朝向、位置和分层词，画面就能从随手一张变成能当封面用的一帧。
本 skill 只做这一层——不碰角色一致性、不碰配色、不碰画风媒介、不碰负面词体系、不碰生成参数。

**本 skill 与模型无关。** 下文的英文构图词可以**作为 tag 或自然语言**嵌入你所用模型的提示词，
具体语法（分隔符、加权写法、是否区分标签与句子、标签顺序）**随模型而定**；本 skill 不规定语法，
只规定「画面结构该怎么写」。标 † 的词更适合放进自然语言句子（靠语义生效）；
其余词既可以当标签，也可以直接写进句子。

完整词表（景别 × 机位 × 朝向 × 位置 × 分层 × 取景装置 × 特殊镜头）与按用途的构图配方，
见 [`references/image-composition-vocabulary.md`](references/image-composition-vocabulary.md)。
本文件讲判断与流程。

## 何时使用

- 主体在画面里太小 / 太远，用户要封面感却给了全身远景；
- 一切都挤在正中，画面呆板、没有前后关系；
- 多个主体叠成一团，观者不知道该看谁；
- 背景细节抢戏，主体陷进环境里；
- 画面扁平：没有机位、没有分层、没有前景；
- 想用**鱼眼 / 球面 / 全景 / 等距 / 极端透视**这类特殊镜头；
- 已经写了构图词但看起来没生效（景别被环境描述拽远）；
- 为**头像 / 立绘 / 海报 KV / 群像 / 场景主导**图重建取景基线。

**不适用**：只调颜色 → `image-color-harmony`；只调光与明暗 → `image-light-and-value`；
只调层次与虚实 → `image-space-and-depth`；只调主次重音 → `image-contrast`；
说不清该调哪层 → 先读入口 `image-aesthetics`；只调画风 / 媒介 / 线条 → 风格类 skill；
只调动作方向与动态线 → 动作类 skill；角色身份一致性 → 角色类 skill。

## 输出契约

默认**只输出最终提示词 / 构图方案**，不要寒暄、不要解释、不要前言与后记。

- **默认只输出正向提示词正文**：用户没提负面词、也没说自己那边没有负面词时，**不要输出任何负面提示词**，
  也不要有 `Positive prompt` 之类的标题行——直接给能粘贴进生成节点的正文；
- 只在下列情况才追加负面提示词：① 用户明确要求负面词 / 负面提示词；② 用户表示自己那边没有设置负面词、
  需要一并给出；③ 用户要的是可直接运行的完整提示对。此时用两段式：

  ```text
  Positive prompt
  [正向提示词正文]

  Negative prompt
  [与该图相关的少量负面词]
  ```

- 默认格式**不带标签行**：不加 `Positive prompt` 标题、不加代码块围栏、不加建议与结尾祝语；
- **不输出任何参数段**：不附宽高比 / 分辨率 / 步数 / CFG / 采样器 / 种子 / 模型文件名；
  即使被问，也只回一句「这些由工作流设置决定」；
- 用户要的是**构图方案**（他还要自己写提示词）时，改用短条目交付：
  `景别 / 机位 / 朝向 / 位置 / 分层 / 装置` 各一行，不展开成文章；
- **用户已经指定了构图 / 镜头 / 主体位置时，绝不覆盖**，只在他给的框架内补分层与层级；
- 用户语言为中文时，**提示词正文仍用英文构图词**（这些词是通用视觉语言），交付时不要逐句翻译。

默认正文骨架：

```text
[主体 / 场景 / 风格描述], [构图词 4~7 个], [1~3 句英文自然语言：把取景、空间、分层写死]
```

本 skill 不规定标签顺序与加权语法，按你所用模型的方式排布即可。

## 高杠杆规则（先看这 7 条）

> 构图这一层最容易被「自然语言漂移」吃掉，第 3 条是本 skill 存在的核心理由。

1. **构图词一次给 4~7 个**：少于 4 个画面没有主张，多于 7 个会互相争夺权重；
   同一维度**只给一个**（景别只能有一个主景别，机位不能同时俯视与仰视）；
   明显互斥的组合不要同写，否则模型会随机挑一个。
2. **三层混合、同一语义不跨层重复**：
   结构标签（管取景 / 位置 / 分层）→ 短视觉短语（管动作 / 氛围）→ 1~3 句稠密英文自然语言（管空间与光影）。
   标签层已经写了 `close-up`，自然语言首句就改用叙事式取景描述，不要再原样重复那个词。
3. **取景与角度必须写死**：若你所用模型支持加权语法，把有限的加权额度优先给取景 / 角度（全文加权词 ≤4 个）；
   不支持加权就靠**自然语言首句**把取景写死。只写一个孤零零的 `upper body` 最容易被环境描述拽远。
4. **视觉层级只有三个杠杆**：景别差、前后位置、细节量。三者**至少给两个**，否则观者不知道看谁。
5. **有主张地选装置**：用户没指定构图时，不要永远回落到最保守的 `cowboy shot` + `eye level` + `centered`；
   按题材主动挑一个景别、一个机位或一个特殊镜头写进去——**直接写、不反问、不在正文外解释**。
6. **因果链**：动作与天气必须落到**可见后果**（头发飘动、衣物受力、湿衣、积水、扬尘、逆光边缘），
   不要只丢一个孤立标签；构图也要有理由——低机位是为了压迫感，前景虚化物是为了纵深。
7. **动作落在「一个瞬间」上**：写「哪一刻」而不是「一串动作」；一张图只有一个瞬间（见工作流第 9 步）。

## 快速决策（30 秒选出一套构图）

0. **第一眼** → 先用一句话说出观者第一眼该看见什么；后面每一步都服务这一句。说不出来就先别急着选景别。
1. **用途** → 决定主体占比与留白位置（见工作流第 1 步的表）；
2. **景别** → 从紧到松挑一个（第 2 步）；
3. **机位** → 平视最中性；要压迫感用仰视，要渺小 / 可爱用俯视，要紧张用倾斜（第 3 步）；
4. **位置** → 单主体优先 `off-center` †；海报留负空间；多主体先给一个主位（第 4 步）；
5. **分层** → 前景一件虚化物 + 背景虚化（第 5 步）；
6. **装置** → 需要时加一个取景框，或按题材挑一个特殊镜头（第 7 步 / 特殊情况）；
7. **写死** → 自然语言首句复述取景与机位（对抗漂移）。

## 工作流

### 1. 先定「这张图拿来干什么」

| 产出用途 | 构图基线 |
|---|---|
| 头像 / 半身立绘 | 主体占画幅高度 50% 以上，背景弱化 |
| 全身立绘 | 全身完整入画，脚不切；四周留一点呼吸空间 |
| 海报 / KV | 大面积负空间留给标题，主体偏一侧或偏下 |
| 群像 | 先定 1 个主位，其余是陪位；高低错落 |
| 场景主导 | 环境是主体，人是尺度参照（人小是对的） |

用途决定景别基线。**用户没说用途时不要空转**：按题材自己定一个基线（实在拿不准就按默认立绘），
并考虑是否值得配一个特殊镜头（见「特殊情况」一节）。**不要为了构图反问用户。**

### 2. 选景别（从紧到松）

`portrait` → `upper body` → `cowboy shot` → `full body` → `wide shot`

- 想看清表情：`portrait` 或 `close-up` †；
- 想看清服装：`cowboy shot`（大腿以上）性价比最高；
- 想让人在环境里：`full body`，**背景信息量必须同步减少**；
- `wide shot` 只在**场景是主体**时用，否则主体必然太小；
- 景别选定后**优先占用一个加权额度**（按你所用模型的加权语法书写），
  理由见「取景对抗自然语言漂移」——这是构图词写了却没生效的头号原因。

### 3. 选机位与朝向

- 机位：`from below`（仰视，显强 / 压迫）、`from above`（俯视，显弱 / 可爱 / 渺小）、`dutch angle`（倾斜，紧张）、
  `eye level` †（平视，最中性）、`from side`、`from behind`；
- 朝向与视线分开写：身体可以 `from side`，视线仍 `looking at viewer`；
- 仰视会同时放大下半身、缩小头，用于立绘要谨慎；
- 表格类 / 多视图版式**禁止切机位**（分格之间机位必须一致）；
- 角度同样受自然语言漂移影响，按需加权，并在自然语言首句补一句视角。

### 4. 定主体位置与视觉层级

- 1 个主体：`centered`（对称、仪式感、头像）或 `off-center` †（更自然、便于留白）；
- 2 个主体：一左一右 + 一前一后，且**两者剪影要明显不同**；
- 3 个及以上：先给 1 个主位（居中 / 更大 / 更近），其余为陪位；负空间留在主位视线方向。

**视觉层级只有三个杠杆**：景别差、前后位置、细节量。三者至少给两个，否则观者不知道看谁。

### 5. 加分层与景深

`foreground` / `middle ground` / `background` 三段至少写两段；`depth of field`、`blurry background`、
`bokeh` 用来压低背景；`foreground` 里放一件虚化物（栏杆、花枝、飘落的纸、近处的肩背）能立刻做出纵深。

### 6. 三分法与对称（当想法用，不当公式用）

- 三分法：自然语言写 `the subject sits on the left third, the horizon along the lower third` †；
- 对称：`symmetry`、`symmetric composition` † + `centered`，适合 KV、宗教感、仪式场景；
- 两种混用会互相削弱；一张图只选一种骨架。

### 7. 取景装置

`framed` †（窗框、门框、拱门、鸟居）、`vignette`、`border`、枝叶前景、背影前景。
取景装置是「用一个框再框一次主体」，适合竖构图海报；**横构图叠加多重框容易显得拥挤**。
框本身也要分层：框在 `foreground` 且虚化，主体在 `middle ground` 实焦。

### 8. 与动作、风格联动

- 动作构图：动作方向那一侧要留空间（`looking to the side` + 负空间），大动作需要更松的景别；
- 风格构图：海报 / KV 的构图与普通立绘**不是同一套**（负空间位置、主体占比、要不要边框都不同）；
- 画风 / 媒介 / 线条由风格类 skill 决定，本 skill 不碰；但要注意**极简平涂风格不要叠加高细节背景词**；
- **相机、人物、光色可以往返调**：先给一个能跑的三件套（景别 + 主光 + 主体位置），再逐项微调；不要一次把每一项都锁死。

### 9. 选一个「瞬间」（动作落在哪一帧）

构图定完取景与层级之后，还要决定**动作停在哪一刻**——同一段动作，选错瞬间整张图就没有信息量：

| 意图 | 选哪一刻 | 画面特征 |
|---|---|---|
| 将起 / 蓄势 | 动作开始前一瞬 | 视线朝向目标、重心压低、手已抬起、衣物还没被带动 |
| 进行中 | 幅度最大时 | 明确的运动方向、肢体前后拉开、速度线可作选配 |
| 接触 | 受力或交接的那一刻 | 接触点清楚（拳、拍、握手、落座）、受力方向可见、双方姿态互相影响 |
| 收势 | 结束后的残留 | 已定格的姿态 + 动作留下的痕迹（扬尘、涟漪、被压弯的草、松开的手） |

规则：

- 一张图只选**一个**瞬间：同时要求「拔刀 + 跳跃 + 落地」，模型会随机挑一个或糊成一团；
- 拿不准就**对比相邻时刻**：哪一帧更能说明「这张图在讲什么」，就选那一帧；
- **先定关键物件或身体的位置朝向支撑，再让姿态与之对应**（刀插在地上 → 手在高处握住刀柄；脚踩上石头 → 重心已经移过去）；
- 没有「必须几个动作 / 几个表情」的配额：**一个动作做到位，好过三个动作都不到位**。

### 10. 自检（静默）

- 主体在画幅里占比与用途匹配吗？
- 用户没指定构图时，是否**有主张地**选了一个装置，而不是永远回落到保守默认值？
- 若用了鱼眼 / 球面 / 极端透视：是不是**只用了一个**？与题材、画幅匹配吗？自然语言首句点明了吗？
  是不是表格类场景（那样必须禁用）？
- **取景 / 角度写死了没有**？自然语言**首句**有没有把取景复述成叙事句？
- 全文构图词是否 4~7 个、同一维度是否只有一个、有没有写互斥组合？
- 视觉层级是否靠至少两个杠杆建立？前景 / 中景 / 背景是否至少写了两段？
- 负空间位置与视线方向一致吗？背景信息量是否超过全文的三分之一？
- 有没有把宽高比 / 分辨率 / 种子 / CFG / 步数 / 模型名漏进正文？
- 用户已经指定的构图 / 镜头，是否一个字都没改？
- 动作是否落在**一个**明确的瞬间上（将起 / 进行中 / 接触 / 收势），而不是三个时刻混写？

## 特殊情况：鱼眼 / 球面 / 极端透视（可自主选用）

**用户没指定构图或镜头时，不要永远回落到最保守的默认值。** 按题材**主动挑一个**合适的特殊装置写进提示词，
让画面有主张——**直接写、不反问、不在正文外解释**（输出契约只允许提示词正文或方案）。

| 题材 | 推荐的特殊装置 | 理由 |
|---|---|---|
| 动作 / 竞速 / 街头 / 极限 | `fisheye lens`、`extreme foreshortening`、`wide angle lens` | 变形本身就是速度与冲击 |
| 梦境 / 宇宙 / 万花筒 / 被环境包裹 | `spherical composition`、`curved horizon` | 沉浸感，四周向中心收拢 |
| 风景 / 群像铺陈 / 场景主导 | `panorama`、`bird's-eye view` | 横向或俯瞰铺开信息量 |
| 建筑 / 房间 / 机械 / 概念设定 | `isometric`、`cross-section` | 结构清晰、无透视干扰 |
| 情绪戏 / 特写 / 立绘 | **不要用变形镜头**，靠景别 + 光影 | 变形会削弱表情 |

硬约束四条：

1. **用户已经指定了构图 / 镜头 → 绝不覆盖**，只在他给的框架内优化；
2. **一次只用一个新的特殊装置**，不要鱼眼 + 球面 + 等距一起上；
3. **表格类禁用**：三视图 / 表情表 / 分镜 / `multiple views` 里绝不叠加鱼眼或球面；
4. **必须配自然语言**，且首句就点明——特殊镜头很容易被普通标签淹没。

```text
fisheye lens, dynamic pose, from below, centered, city street, neon signs, foreground debris, blurry background. The whole frame bends outward like a fisheye photograph, the street's paving lines curving up and away at the edges while she stays dead centre, one arm thrown toward the lens.
```

> 完整词表（每条的效果 / 适用 / 风险）、选用原则，以及鱼眼 / 球面 / 等距的配方，
> 见 `references/image-composition-vocabulary.md` 第 7 与 8.5 节。

## 取景对抗自然语言漂移（关键规则）

一旦自然语言层开始描述环境，模型会**把镜头拉远**，直接忽略 `close-up` / `upper body` / `portrait`
这些取景词——看起来就像构图词白写了。这不是玄学：**自然语言对画面的影响力通常强于零散标签**，
所以环境描述会把镜头往外拽。

三步对抗，按顺序用：

1. **给取景加权**——按你所用模型的加权语法；
2. **自然语言首句把取景写死**：`The composition is a tight close-up portrait ...`；
3. **仍然拉远就继续加**：提高取景权重，或把取景挪进更靠前的句子里；角度同理。

配套约束：

- 加权词总数保持精简（≤4 个），取景 / 角度优先；
- 背景信息量砍到主体的三分之一以下，否则镜头也会被背景撑开；
- **同一语义不跨层重复**：标签区写了 `close-up`，自然语言首句就改用叙事式取景描述。

> 反向自查：出图后如果主体比预期小、或景别与提示词不符，**先怀疑这一条**，
> 而不是去调采样参数——参数改不了取景漂移。

## 宽高比不写在提示词里

画面比例由**生成工作流的画布尺寸**决定，提示词里写 `vertical composition` 之类
只能影响内容密度，改不了画布形状。竖版海报、横版场景、方图头像的差别请在**工作流里**设定；
提示词只负责「在这块画布里怎么排」。用户问宽高比时，只回一句「由工作流设置决定」——
**不要给出具体比例或分辨率数值，也不要附参数段**。

## 常见构图失败与修法

| 现象 | 成因 | 只改构图词的修法 |
|---|---|---|
| 主体太小 | 用了 `wide shot` / 背景词太多 | 换 `cowboy shot` 或 `upper body`；删掉多余背景词；把主体描述提前 |
| 一切都挤在中间 | 默认居中 + 没有前后差 | 改 `off-center` † + `left side`；加 `foreground` 虚化物 |
| 多角色叠成一团无主次 | 缺景别差与前后差 | 主角 `upper body` + `foreground`，配角 `full body` + `background` |
| 背景抢戏 | 背景信息量过大、无景深 | `blurry background, depth of field`；背景细节词砍到主体的三分之一以下 |
| 画面扁平 | 无机位、无分层、无前景 | 加 `from below` 或 `dutch angle` + 一个 `foreground` 物件 |
| 裁切别扭 | 景别与主体不匹配 | 换景别，或显式 `feet out of frame`；必要时在负面词加 `bad crop` |
| 留白位置不对（海报） | 没指定负空间方向 | 自然语言写清 `large empty space in the upper third for a title` † |
| 视线方向撞墙 | 主体贴边且看向墙 | 把主体移到另一侧，负空间留在视线前方 |
| 特殊镜头没生效 | 被普通标签淹没 | 自然语言首句点明镜头，并给该装置加权 |
| 表格类版式机位乱 | 多视图里混用了不同机位 | 统一机位与视距，禁用变形镜头 |

## 示例

输入：`银发少女站在废墟城市，有孤独感，想当封面用`
问题：主体太小、居中、背景细节抢戏、无纵深。

改写前（构图层缺位）：

```text
1girl, solo, silver hair, long hair, black coat, ruined city, full body, wide shot, centered, detailed background, dramatic lighting, broken windows, collapsed towers, rubble. A lone silver-haired girl in a black coat stands in the middle of a ruined city avenue, the collapsed towers and broken windows described in as much detail as she is, everything evenly lit and evenly sharp from edge to edge.
```

**只改构图相关词**后的版本：

```text
cowboy shot (weighted), from below, off-center, left side, silver hair, long hair, black coat, ruined city, foreground rubble, blurry background, depth of field, backlighting. The composition is a tight off-center cowboy shot seen from slightly below: a lone silver-haired girl in a black coat stands on the left of the frame, the collapsed towers behind her falling out of focus while a blurred slab of rubble crosses the near foreground, and a wide empty band of pale haze is left in the upper right for a cover title.
```

改动点：`full body, wide shot, centered` → `cowboy shot, from below, off-center, left side`；
再加 `foreground rubble`（前景分层）、`blurry background, depth of field`（压低背景）、
`backlighting`（主体与背景分离）。主体与场景词一个都没动。
另外三处按「高杠杆规则」补齐：**给取景加权**、**自然语言首句写死取景**、**砍掉背景细节堆量**。
负面词里若要写虚化，应写 `blurry subject`——这次要的就是虚化背景，直接写 `blurry` 会自相矛盾。

（`weighted` 处按你所用模型的加权语法书写。）

## 边界

- 只要整体配色 / 色调 / 颜色关系 → **配色类 skill**；本 skill 只管构图与镜头，不管颜色。
  需要主体从背景里跳出来时，本 skill 用**位置 / 分层 / 景深**做到，不用色相与明度——那是配色 skill 的活。
- 只改线条 / 上色 / 年代感 / 画面质感 → 风格类 skill；
- 姿势、动作方向、动态线、动作与留白的配合 → 动作类 skill（本 skill 只负责把动作方向所需的空间留出来）；
- 角色身份归属与一致性 → 角色类 skill（本 skill 只负责位置与层级）；
- 分区提示词、局部重绘里的构图修正 → 分区类 skill；
- 负面词体系与质量前缀 → 负面词类 skill；
- 宽高比、分辨率、步数、CFG 属于**工作流与模型版本**，既不写进提示词，也不在输出里给数值；
- 需求本身还很模糊、要先发散 → 需求发散类 skill。
