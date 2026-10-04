# Anima 构图词汇表（Composition Vocabulary）

配套 `SKILL.md`。分两部分：**可直接进提示词的英文词汇表**（景别 × 机位 × 朝向 × 位置 × 分层 × 取景装置
× **特殊镜头 / 球面 / 极端透视**），以及**按产出类型与特殊情况给的构图配方**。
标 † 的词优先放进自然语言句子；其余可作 `general` 段标签。

## 0. 使用规则

1. 构图词一次给 **4~7 个**。少于 4 个画面没有主张，多于 7 个会互相争夺权重。
2. 同一维度**只给一个**：景别只能有一个主景别，机位不能同时 `from above` 和 `from below`。
3. 明显互斥的组合不要同写，模型会随机挑一个：

| 互斥组合 | 后果 |
|---|---|
| `close-up` / `portrait` + `full body` | 一会半身一会全身，批量出图时随机漂移 |
| `centered` + `off-center` | 主体位置不稳定 |
| `from above` + `from below` | 机位翻转 |
| `wide shot` + `detailed background` + 主体细节堆满 | 背景必然抢焦 |
| `dutch angle` + `symmetric composition` | 对称骨架被倾斜破坏 |

4. **特殊镜头（鱼眼 / 球面 / 极端透视）一次只用一个**，并且必须与题材匹配——完整词表见第 7 节。
   用户没指定构图时**允许自主挑一个**写进去；但**表格类场景（三视图 / 分镜 / 表情表 / `multiple views`）一律禁用**变形镜头。

## 1. 景别（shot size）

| 英文词 | 覆盖范围 | 适用 |
|---|---|---|
| `portrait` | 头肩 | 头像、表情、眼神戏 |
| `close-up` † | 面部特写 | 情绪爆点、瞳孔细节 |
| `upper body` | 腰以上 | 立绘、交互感、服装上半身 |
| `cowboy shot` | 大腿以上 | **通用性价比最高** |
| `full body` | 全身含脚 | 全身立绘、服装全貌 |
| `wide shot` | 人物 + 大环境 | 只有场景是主体时才用 |
| `feet out of frame` | 显式切脚 | 与 `cowboy shot` 同源，避免尴尬裁切 |

## 2. 机位与角度（camera angle）

| 英文词 | 效果 | 风险 |
|---|---|---|
| `eye level` † | 平视，中性 | 平淡，需要靠位置/分层补张力 |
| `from below` | 仰视，压迫感、英雄感 | 下半身放大、头变小 |
| `from above` | 俯视，弱小、可爱、孤独 | 容易显头大身短 |
| `dutch angle` | 倾斜，紧张、动感 | 与对称构图冲突；表格类禁用 |
| `foreshortening` † | 透视缩短 | 需要明确朝向，否则肢体崩 |
| `perspective` † | 强调透视 | 太泛，最好跟具体词一起用 |

## 3. 朝向与视线（view direction）

| 英文词 | 含义 |
|---|---|
| `from front` | 正面朝向观众 |
| `three-quarter view` † | 四分之三侧，最耐看 |
| `from side` / `profile` † | 90° 侧面 |
| `from behind` | 背对，常配 `looking back` |
| `looking at viewer` | 与观众对视 |
| `looking away` / `looking to the side` | 视线离画，留白方向由此决定 |
| `looking back` | 回头看，回头率最高的姿势词 |
| `head tilted` † | 歪头，配合可爱/疑惑 |

## 4. 主体位置（placement）

| 英文词 | 说明 |
|---|---|
| `centered` | 居中，对称与仪式感 |
| `off-center` † | 偏心，最自然的默认 |
| `left side` / `right side` | 明确左右，多角色必备 |
| `upper left` / `lower right` † | 精确到角，海报留白时用 |
| `symmetry` | 对称构图骨架 |
| `rule of thirds` † | 三分法，用句子写更稳 |

## 5. 分层与景深（layering & depth）

| 英文词 | 作用 |
|---|---|
| `foreground` | 最近一层，往往放虚化物 |
| `middle ground` | 主体所在地 |
| `background` | 环境层 |
| `depth of field` | 前后分离的核心词 |
| `blurry background` | 直接压低背景细节 |
| `blurry foreground` | 前景虚化，做纵深框 |
| `bokeh` | 光斑，夜景/逆光加分 |
| `backlighting` / `rim light` † | 主体边缘光，把主体从背景里拔出来 |
| `silhouette` | 剪影，强对比构图 |

## 6. 取景装置（framing device）

`framed` †、`picture frame`、`window`、`doorway`、`arch`、`torii gate`、`branch`、`curtain`,
`vignette`、`border`、`letterboxed` †、`polaroid` †。

用法：竖构图叠加一层框最有效；横构图叠两层以上会显得堵。框本身也要分层
（框在 `foreground` 且虚化，主体在 `middle ground` 实焦）。

## 7. 特殊镜头与特殊构图（进阶，可自主选用）

> **用户没指定构图 / 镜头时，可以从这一节主动挑一个写进提示词**（见 `SKILL.md` 的
> 「特殊情况：鱼眼 / 球面 / 极端透视」一节）；用户**已经指定**构图时**绝不覆盖**。
> 三条硬约束：**一次只用一个**特殊装置；必须与题材匹配；
> **表格类场景（三视图 / 分镜 / 表情表 / `multiple views`）一律禁用**。

### 7.1 镜头与透视（lens & perspective）

| 英文词 | 效果 | 什么时候用 | 风险 / 注意 |
|---|---|---|---|
| `fisheye lens` | **鱼眼**：画面沿球面强烈弯曲，中心膨胀、边缘压缩，视场极宽 | 冲击力、速度感、街头 / 室内 / 极限运动，以及"世界被卷起来"的超现实感 | 直线全变弧线——**不要与规则版式、表格、对称建筑同用**；脸贴边会严重变形，主体尽量放中心 |
| `wide angle lens` | **广角**：视野宽、近大远小夸张，但没有鱼眼那种球面弯曲 | 环境信息量大：舞台、街道、室内纵深 | 边缘人物会被拉胖，主体别贴边 |
| `extreme foreshortening` † | **极端透视缩短**：某个肢体 / 物体朝镜头伸来并被极大放大 | 伸手、指向观众、踢击、冲出画面 | 必须写清朝向与"哪一部分朝前"，否则肢体崩坏 |
| `exaggerated perspective` / `perspective distortion` | 透视夸张 / 变形，比鱼眼温和 | 与 `from below`、`worm's-eye view` 叠加做压迫感 | 全画面仍保持直线的场合用它替代鱼眼 |
| `forced perspective` | **强制透视**：靠大小对比制造错觉（小人变巨人 / 巨人变玩偶） | 奇幻、玩具感、超现实 | 需要写清谁在前、谁在后、谁离镜头近 |

### 7.2 球面与全景（spherical & panorama）

| 英文词 | 效果 | 什么时候用 |
|---|---|---|
| `spherical composition` | **球面构图**：画面像被包在一个球体 / 穹顶里，四周向中心收拢 | 沉浸感、梦境、宇宙 / 星空 / 万花筒，角色被环境"包裹" |
| `curved horizon` | 地平线弯曲 | 与鱼眼 / 球面配套，强化"站在球面上"的感觉 |
| `panorama` | 全景：极宽画幅横向铺开 | 场景主导、横向风景、群像铺陈 |
| `360 view` † / `wraparound composition` † | 环视 / 环绕构图 | 需要在自然语言里点明"周围一圈都是……" |
| `diorama` | 微缩景箱：整幅像放在球罩 / 盒子里的一个小世界 | 玩具感、可爱、概念稿 |

> **球面 / 全景依赖宽画幅**：竖构图写 `spherical composition`，多半只得到一张内容拥挤的方图。
> 画幅由工作流决定，所以这类装置适合用在**横向或方图画布**上；竖构图请改用
> `extreme foreshortening` 或 `worm's-eye view`。

### 7.3 极端机位与版式（extreme camera & layout）

| 英文词 | 效果 | 什么时候用 | 风险 |
|---|---|---|---|
| `bird's-eye view` | 鸟瞰：近乎垂直俯视，全局展示 | 地图感、房间布局、群像调度 | 角色变小、脸看不清 |
| `worm's-eye view` | 虫视：极端仰视 | 压迫感、巨物、英雄登场 | 下半身被放大到失真 |
| `overhead` / `from directly above` | 正上方俯拍 | 平躺、泳池、桌面静物 | 需明确角色朝向，否则像"躺着" |
| `isometric` | 等距视角：无透视的 45° 斜俯视 | 建筑 / 房间 / 游戏场景、概念设定 | 人物会"贴纸化"，不适合情绪戏 |
| `cross-section` | 剖面：把空间切开看内部 | 建筑、机械、房间结构 | 要用自然语言说明切在哪 |
| `tiled` / `panel layout` / `multiple views` | 分格 / 多视图版式 | 表情表、分镜、步骤图 | **属表格类：禁止叠加鱼眼等变形镜头** |

### 7.4 选用原则（怎么挑）

1. **看题材**：动作 / 竞速 / 街头 → 鱼眼、极端透视；梦境 / 宇宙 / 被环境包裹 → 球面、弯曲地平线；
   风景 / 群像铺陈 → 全景、鸟瞰；建筑 / 机械 / 系统 → 等距、剖面；**情绪戏 / 特写 → 不要用变形镜头**；
2. **看画幅**：竖构图适合 `extreme foreshortening`、`worm's-eye view`；横 / 方构图适合 `panorama`、球面；
3. **一次一个**：两个变形镜头同时上会互相打架，画面直接糊掉；
4. **必须配自然语言**：特殊镜头很容易被普通标签淹没，**自然语言首句就要点明**——
   例如 `The whole frame bends outward like a fisheye photograph, the street's paving lines curving away at the edges.`；
5. **值得花 1 个权重额度**：`(fisheye lens:2)`、`(spherical composition:2)`——但全文加权标签仍 **≤4 个**；
6. **表格类禁用**：`character sheet` / `multiple views` / 三视图 / 分镜 / 表情表里绝不叠加鱼眼或球面。

## 8. 按产出类型的构图配方

### 8.1 头像 / 半身立绘

```text
portrait, eye level, centered, depth of field, blurry background, simple background
```
自然语言：主体占画幅高度一半以上，背景只留色块与光。

### 8.2 海报 / KV

```text
cowboy shot, from below, off-center, left side, foreground <物件>, blurry background, depth of field, backlighting
```
自然语言必须写清负空间位置与用途：`a wide empty band in the upper third for the title` †。
KV 与普通立绘不是同一套：主体更偏、留白更大、边框可选、对比更强。

### 8.3 群像

```text
3girls, multiple girls, upper body, centered, foreground, background, depth of field
```
主位 `upper body` + `foreground`，陪位 `full body` + `background`；高低错落；每人剪影区分。

### 8.4 场景主导

```text
wide shot, from above, centered, middle ground, background, depth of field, atmospheric perspective †
```
人是尺度参照，可以小；背景细节量可以超过人物，但要靠 `atmospheric perspective`（远近空气感）分层。

### 8.5 特殊情况（自主选用时）

**鱼眼冲击镜头**（动作 / 街头 / 速度感；主体必须居中，否则脸会变形）

```text
(@artist name:2), (fisheye lens:2), dynamic pose, from below, centered, foreground debris, blurry background, city street, neon signs
The whole frame bends outward like a fisheye photograph, the street's paving lines curving up and away at the edges while she stays dead centre, one arm thrown toward the lens.
```

**球面全景**（梦境 / 宇宙 / 被环境包裹；适合横构图或方图）

```text
(@artist name:2), (spherical composition:2), centered, middle ground, background, depth of field, atmospheric perspective, starfield, drifting petals
The scene wraps around her like the inside of a sphere, the starfield and drifting petals curving in from every edge toward the centre where she floats.
```

**等距版式**（建筑 / 房间 / 概念设定；人物会贴纸化，别用于情绪戏）

```text
(@artist name:2), isometric, bird's-eye view, wide shot, centered, room interior, furniture, soft lighting
The whole room is laid out on a clean isometric grid, walls cut away so every corner stays visible while she sits at the desk in the middle.
```

> 三条配方的加权标签都控制在 2 个以内，给取景 / 角度留出额度（全文 ≤4）。
> 注意：球面 / 全景配方**不要**再叠 `fisheye lens`——一次只用**一个**变形装置。

## 9. 构图自检清单

- [ ] 景别与用途匹配（封面用 `wide shot` 是错的）；
- [ ] 同一维度只有一个词，没有写互斥组合；
- [ ] 用户没指定构图时，是否**有主张地**选了一个装置，而不是永远回落到最保守的默认值？
- [ ] 若用了鱼眼 / 球面 / 极端透视：是不是**只用了一个**？与题材、画幅匹配吗？自然语言首句点明了吗？
      是不是表格类场景（那样必须禁用）？
- [ ] 视觉层级至少用了两个杠杆（景别差 / 前后差 / 细节量差）；
- [ ] 前景 / 中景 / 背景至少写了两段；
- [ ] 负空间位置与视线方向一致；
- [ ] 背景标签量不超过全文三分之一；
- [ ] 构图词全部在 `general` 段，没有混进 quality / meta / safety；
- [ ] 正文里没有宽高比、分辨率、种子、CFG、步数、模型名；
- [ ] 与风格 skill 交付的风格子句不冲突（例如极简风格不要叠 `absurdres` 级别的细节词）。
