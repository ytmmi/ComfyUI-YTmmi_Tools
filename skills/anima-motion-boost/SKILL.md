---
name: anima-motion-boost
description: Strengthen pose, action, gesture and motion-energy wording for Anima prompts, including dynamic framing, motion blur taste, impact lines, before/after action beats. Use for Anima Base / Aesthetic / Turbo text-to-image prompts in ComfyUI when a generated image looks stiff, static or lifeless and the action inside it is unreadable.
version: 1.0.0
---

# Anima 动作增强（Motion Boost）

Anima 是单帧文生图模型：**它画不出时间，只能画一个瞬间**。所以"动作增强"不是往提示词里多塞几个动词，
而是把一句静态描述翻译成**一个能被单帧承载的动作节拍（action beat）**——同时交代清这个瞬间的身体姿态、
镜头站在哪里、以及画面里哪些东西"正在被运动带动"。

模型对动作的理解主要来自 Danbooru 的 action 标签（`running` `jumping` `mid-air` `holding sword`）
与英文自然语言的动词短语；两者混用最稳。权重需要比 SDXL 更高，例如 `(mid-air:1.4)`、`(dynamic pose:1.3)`。

读 `references/anima-motion-vocabulary.md` 获取完整动作词表（按身体部位 / 动作族 / 镜头交互 / 效果分类）、
组合配方与反模式清单。本文件只给工作流；标签顺序、质量前缀等硬规则以 `anima-prompt-format`
的基准文件 `references/anima-prompt-baseline.md` 为准。

## 输出契约

默认**只输出一条正面提示词**（动作增强后的正文）；仅在用户明确要求负面词时，才追加 `Negative prompt` 段：

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

### 1. 先判断"卡"在哪（静默完成，不要输出这一步）

| 症状 | 真实原因 | 处理 |
|---|---|---|
| 站姿正确但画面死板 | 只有静态名词，没有动作节拍 | 走第 2 步选节拍 |
| 手脚像面条 / 多一条胳膊 | 有动作词，但没交代躯干朝向和四肢位置 | 走第 3 步补体态锚点 |
| 模糊成一片 | 只靠 `motion blur` 暗示速度 | 走第 4 步换成运动证据 |
| 动作看不懂 | 动词太多（action soup），模型每个都出一半 | 走第 6 步砍到 ≤2 个 |
| 动作与镜头无关 | 低角度配静态站姿、特写配全身动作 | 走第 5 步做配对 |

### 2. 选**一个**动作节拍（起势 / 最高点 / 收招落地 / 情绪拍）

一个动作只能落在一个瞬间上。**四类里选一个，不要都写**：

| 节拍 | 何时用 | 代表写法 |
|---|---|---|
| 起势 before | 蓄力、拔刀、准备冲刺 | `crouching, stance, hand on hilt, leaning forward` |
| 最高点 peak | 空中、挥砍、跳跃顶点 | `mid-air, jumping, outstretched arm, arm up` |
| 收招/落地 after | 冲击、落地、余韵 | `landing, impact, dust cloud, kneeling` |
| 情绪拍 emotional beat | 没打斗也要动能 | `turning around, reaching out, looking back` |

自然语言区就用一句话点明这是哪一拍（`caught at the instant the swing reaches full extension`），
比堆十个动词有用。

### 3. 补体态锚点（这一步决定崩不崩）

至少给"躯干朝向 + 重心 + 两组四肢位置"：

- 躯干：`leaning forward`、`arched back`、`contrapposto`、`bent over`；
  `twisted torso` 只在真的需要扭转时用，它是崩坏高发词；
- 手臂：`outstretched arm`、`arm behind back`、`arm up`、`reaching towards viewer`、`hand on own hip`；
- 腿：`one leg extended`、`legs apart`、`walking on air`、`crossed legs`（静姿用）、`tucked legs`；
- 头与视线：`looking down`、`looking back`、`head tilted`、`eye contact`；
- 头发：`floating hair`、`hair blowing`、`wind lift`——头发是零成本动能。

**左右手分工要写死**（`holding sword in right hand, left arm extended`），
Anima 对"哪只手拿什么"比对人脸更敏感；不写死就等着看它自己发明第三只手。

### 4. 用"运动证据"替代运动模糊

Anima 不是视频模型，正面里 `motion blur` 写多了，线稿、五官、手指会一起糊掉。
优先让**被运动带动的静物**暗示速度：

- 风与布料：`wind`、`wind lift`、`clothes fluttering`、`floating skirt`、`coat flapping`、`ribbon`；
- 粒子与碎片：`droplets`、`water splash`、`debris`、`pebbles`、`dust cloud`、`smoke`、`sparks`、`petals`；
- 线条类：`speed lines`、`motion lines`、`afterimage`、`impact frame`、`shockwave`；
- 光与冲击：`rim light`、`lens flare`、`glowing`、`energy`。

真要 `motion blur` 时，把它**限定在不承载身份的部位或背景**：`motion blur on background`、
`blurry background`、`motion blur on legs`。绝不要让它落在脸上。

### 5. 镜头与动作配对

| 动作类型 | 镜头写法 | 理由 |
|---|---|---|
| 跳跃 / 下落 / 挥砍 | `low angle`、`from below`、`foreshortening` | 强化高度与压迫感 |
| 冲击 / 必杀 / 爆炸 | `dutch angle`、`wide shot`、`impact frame` | 失衡感表达冲击 |
| 冲刺 / 迎面跑来 | `from side`、`front view`、`perspective`、`speed lines` | 让位移方向可读 |
| 情绪拍 / 转身 / 回望 | `close-up`、`upper body`、`looking back`、`depth of field` | 保住表情 |

大爆炸配超广角会把角色吃掉：冲击镜头优先 `medium shot`，先保证**角色仍可辨认**再谈场面。

### 6. 控制动词密度（防 action soup）

主动作动词 **≤2 个**，其余全部交给体态标签和效果标签。
Anima 使用随机标签丢弃（tag dropout）训练，**同义动词堆叠不加分，只会互相稀释**——
`running, dashing, sprinting, charging` 同时出现，结果往往是一个四不像的半身站姿。

### 7. 加针对性负面

```text
bad anatomy, bad hands, extra fingers, missing fingers, extra limbs, extra arms, missing limbs,
fused fingers, twisted torso, deformed, broken proportions, static pose, stiff pose, motion smear, multiple views
```

- `extra arms` / `extra limbs` / `fused fingers`：极端姿势下最常出现的崩坏；
- 正面已经用了 `motion blur` 时，**不要**再把同名项写进负面（自相矛盾会让两边都失效）；
- 用户要的是"定格瞬间"时，正面不要写 `motion blur`，负面加 `motion smear, ghosting`；
- 用户要的是"速度感"时，负面里**不要**加 `speed lines`、`impact frame` 这类对抗项。

### 8. 交付前自检（静默）

- 是不是只落在**一个**动作节拍上？
- 躯干朝向、重心、左右手分工是否写清？
- 运动暗示是否主要靠风/布料/碎片/线条，而不是靠糊图？
- 镜头是否与动作强度匹配？角色在冲击镜头里还认得出吗？
- 身份、服装、画师、人数、safety 是否与用户给定的一致，一个字没动？
- 输出里是否只有 `Positive prompt` / `Negative prompt` 两段？

## 示例

输入：`1girl 从空中跳下挥刀砍向地面的敌人，要速度感和冲击力`

```text
Positive prompt
masterpiece, best quality, safe, 1girl, solo, long black hair, red eyes, black coat, holding sword, sword, mid-air, jumping, falling, dynamic pose, outstretched arm, arm behind back, one leg extended, looking down, angry, motion blur on background, speed lines, wind, floating hair, coat flapping, dust cloud, debris, impact, low angle, foreshortening, depth of field. A black-coated swordswoman drops from the sky above a shattered plaza with her blade already swinging down at the enemy below; her coat and long hair are torn upward by the fall while a ring of dust and stone debris bursts from the crater under the strike, one arm thrown back as counterweight and both legs extended, caught at the instant the swing reaches full extension.

Negative prompt
worst quality, low quality, lowres, blurry, jpeg artifacts, bad anatomy, bad hands, extra fingers, missing fingers, extra limbs, extra arms, missing limbs, fused fingers, twisted torso, deformed, broken proportions, static pose, stiff pose, motion smear, multiple views, duplicate face, crossed eyes, messy lineart, watermark, signature, username, logo, unrelated text
```

本次增强相对输入的改动（仅作讲解，不属于输出）：把 `从空中跳下挥刀` 收敛成"最高点 + 挥砍"**一个**节拍，
补了 `arm behind back` / `one leg extended` / `looking down` 三处体态锚点，用 `wind, floating hair,
coat flapping, dust cloud, debris, speed lines` 承担速度感，只把 `motion blur` 留给背景，
并加 `low angle` + `foreshortening` 与下劈动作配对。

## 边界

- 标签顺序、大小写/下划线、质量前缀、自然语言写法本身有问题 → 交给 `anima-prompt-format`；
- 动作之外还要定风格（赛璐璐 / 厚涂 / 漫画网点 / 年代感）→ 交给 `anima-style-control`；
- 风格已定、只是画面"平"、完成度不够 → 交给 `anima-style-boost`；
- 需要指定画师风格或画师混合 → 交给 `anima-prompt-artist`；
- 角色身份、多视图一致性、服装连续性 → 交给 `anima-prompt-character`；
- 景别、机位、前中后景布局等**非动作**构图问题 → 交给 `anima-composition-optimize`；
- 负面词需要整体重做（不只动作类）→ 交给 `anima-prompt-negative`；
- 分区上色 / 局部重绘里的动作控制 → 交给 `anima-prompt-regional`；
- 动作需要 LoRA 触发词配合 → 交给 `anima-lora-trigger`；
- 步数、CFG、采样器、分辨率的分离规则 → 见 `anima-prompt-format` 的「参数与提示词必须分离」一节（**参数既不写进提示词，也不在输出里给数值**）。
