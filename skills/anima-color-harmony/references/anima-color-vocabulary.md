# Anima 配色词表（Color Vocabulary）

配套 `SKILL.md`。六部分：**颜色标签速查**、**七套配色骨架**（含可直接抄的写法）、
**明度 × 饱和度矩阵与情绪对照**、**主体-背景分色配方与失败修法**、
**暗部环境色与大气透视**、**双色调 / 电影感调色**。

标 † 的词**优先放进自然语言句子**；其余可以直接当 `general` 段标签用。

## 0. 使用规则

1. **颜色主要靠自然语言写。** 自然语言对画面的影响力远强于标签，颜色词尤其如此——
   标签只做锚点，**2~3 个封顶**，三色以上就开始互相稀释。
2. **一次只用一套骨架**，主色 + 辅色 + 强调色三色封顶，比例按 **60 : 30 : 10**。
3. **先定光色，再定物体色。** 光的颜色定了，固有色模型会自己算，不必逐个交代。
4. 标 † 的写进句子（如 `a warm amber palette against cool blue shadows`），其余可当标签。
5. 与 `anima-style-control` 的分工：那边决定**画法与媒介**，这边只决定**颜色关系**。

## 1. 颜色标签速查

| 英文词 | 作用 | 注意 |
|---|---|---|
| `pastel colors` | 高明度、低饱和 | 治愈 / 清新系的标配锚点 |
| `muted colors` | 整体降饱和 | 高级感、纪实、压抑向 |
| `vibrant colors` † | 高饱和 | 与 `muted colors` 互斥，不要同时写 |
| `high contrast` † | 强明暗对比 | 与 `low contrast` 互斥；配冷背景更显立体 |
| `low contrast` † | 弱对比、柔和 | 容易"发灰"，需要靠色相拉开层次 |
| `limited palette` | 限制色种数 | 高级感的来源；要配自然语言点名主色，否则模型不知道限制成哪几个 |
| `monochrome` | 单色 | 会压掉其它色相；要"单色 + 一处强调"时用自然语言补那一处 |
| `greyscale` | 全灰阶 | 只有黑白灰，与任何彩色词冲突 |
| `sepia` | 棕褐色调 | 怀旧 / 老照片感；与鲜艳色冲突 |
| `faded colors` † | 褪色 | 复古、回忆、胶片感 |
| `colorful` | 多彩 | 与"收敛配色"方向相反，**慎用**；多数"廉价感"来自它 |
| `colorful background` / `gradient background` | 背景用色 | 容易抢焦，主体的分色要同步加强 |
| `dark background` / `white background` / `simple background` | 背景基调 | 做主体-背景分色最省事的三件套 |
| `neon lights` | 霓虹光 | 夜景双色方案的地基（品红 / 青） |
| `backlighting` / `rim light` † | 边缘光 | 最便宜的主体-背景分离手段 |
| `glowing` † | 自发光 | 用于光源、魔法、屏幕；滥用会糊 |
| `teal and orange` † | 青橙调色 | 商业电影感；本身已规定配色，不要再叠一套骨架 |
| `duotone` / `two-tone` † | 双色调 | 海报 / 极简；需点名是哪两个色 |
| `atmospheric perspective` † | 大气透视 | 远景降饱和 + 偏冷 + 低对比，拉开纵深 |
| `bounce light` † | 反光 | 给暗部补环境色，高级感的常见来源 |
| `deep blue shadows` / `dark teal shadows` † | 暗部环境色 | 替代纯黑；暗部"发脏"的常用解 |

> **颜色标签的共同风险**：它们约束的是"整体倾向"，不是具体色相。要精确到"哪一块是什么颜色"，
> 必须用自然语言写（`the only saturated note is the green of her eyes`）。

## 2. 七套配色骨架

每套都给出可直接改写的写法。三色按 **主 / 辅 / 强调**排列。

### 2.1 单色 monochrome

```text
monochrome, limited palette, low contrast
A single blue-grey family rendered in five values, from near-white highlights to deep navy shadows.
```
- **适用**：特写、氛围图、需要克制与高级感时；
- **风险**：明度再拉不开就真的是一张灰图——**必须**指定明度跨度。

### 2.2 类似色 analogous

```text
pastel colors, soft lighting
An analogous palette of pale mint, soft cream and light sky blue, kept high in value and low in saturation.
```
- **适用**：日常、治愈、风景、室内；
- **风险**：容易平淡，靠明度层次与一个稍重的强调色救回来。

### 2.3 互补 complementary（对比最强）

```text
high contrast, vibrant colors
A complementary clash of warm orange and cold blue: the orange sits on the subject, the blue owns the whole background.
```
- **适用**：海报、燃、需要"跳出来"；
- **风险**：两边都高饱和会刺眼——**只让一边高饱和**，另一边降下来。

### 2.4 分割互补 split-complementary（最实用）

```text
limited palette
A split-complementary scheme: a warm red-orange subject against blue-green and teal surroundings.
```
- **适用**：大部分立绘与商业插画——比互补柔和，又比类似色有对比；
- **风险**：三个色相都要出现，否则退化成互补或类似色，但**别三色均分**，按 60 : 30 : 10。

### 2.5 三角 triadic

```text
vibrant colors, flat color
A triadic palette of red, yellow and blue in flat cel-shaded blocks with clean outlines.
```
- **适用**：绘本、Q 版、游戏 UI 感、儿童向；
- **风险**：三色等强会花——必须指定**主色占大面积**，另两色只做点缀。

### 2.6 冷暖对抗 warm-cool（最万能的默认）

```text
high contrast, rim light
Warm amber light on the subject against cool blue-grey shadows in the background.
```
- **适用**：几乎任何题材，尤其立绘与人物特写；
- **风险**：几乎没有——只要别让冷暖在同一个区域里打架（`warm face, warm background, warm clothes` 就是打架）。

### 2.7 单一强调色 accent

```text
limited palette, muted colors
An almost desaturated grey-green image with exactly one saturated red accent: her ribbon, her eyes and the distant traffic light.
```
- **适用**：情绪图、极简、需要一个明确焦点；
- **风险**：强调色**必须点名具体物体**，否则模型会把它撒得满画面都是。

## 3. 明度 × 饱和度矩阵

| | 低饱和 | 高饱和 |
|---|---|---|
| **高明度** | 清新、治愈、透气（pastel） | 明快、卡通、广告（pop） |
| **低明度** | 压抑、纪实、写实向（muted） | 浓郁、赛博、夜戏（neon） |

- **"发灰"的成因**：全部落在中间饱和 + 中间明度。解法是**往对角走**——要么亮而淡，要么暗而浓；
- **"廉价"的成因**：大面积高饱和 + 互补对撞。解法是**只留一个高饱和**；
- **"高级"的常见配方**：低饱和 + 明确明度层次 + 一个强调色。

## 4. 情绪 → 配色对照

| 情绪 / 题材 | 骨架 | 明度 × 饱和 | 建议写法 |
|---|---|---|---|
| 治愈 / 清新 / 日常 | 类似色 | 高明度 × 低饱和 | `pastel colors, soft lighting, high key` |
| 燃 / 战斗 / 冲击 | 冷暖对抗 | 高对比 | `high contrast` + 暖主体 / 冷背景 + 一处高饱和 |
| 赛博 / 夜景 / 未来 | 互补（品红 / 青） | 低明度 × 高饱和 | `neon lights, dark background, wet asphalt reflections` |
| 压抑 / 悲伤 / 孤独 | 单色（冷） | 低明度 × 低饱和 | `muted colors, low contrast, cool blue tones` |
| 怀旧 / 复古 / 老番 | 单色（黄 / 青） | 全区间 × 低饱和 | `sepia` 或 `faded colors` + 少量暖光 |
| 童话 / 可爱 / 绘本 | 三角或类似色 | 中高明度 × 中饱和 | `vibrant colors, flat color` + 大色块 |
| 恐怖 / 诡异 | 单色 + 一处反常 | 低明度 × 极低饱和 | 冷灰绿打底，只留一处血红或病绿 |
| 华丽 / 魔法 / 舞台 | 互补 + 发光 | 低明度 × 高饱和 | `glowing`, 互补双色 + `rim light` |

## 5. 光的颜色（先定这个）

| 光况 | 写法 | 效果 |
|---|---|---|
| 金色时刻 | `golden hour, warm key light, cool blue shadows` | 暖亮部 + 冷暗部，最讨喜 |
| 蓝调时刻 | `blue hour, cool ambient light, warm window lights` | 整体冷、局部暖点 |
| 正午 | `bright daylight, clear blue sky, crisp shadows` | 高对比、色相干净 |
| 霓虹夜 | `neon lights, magenta and cyan glow, wet asphalt reflections` | 双色霓虹是最稳的夜景方案 |
| 月光 | `moonlight, cool blue tones, low saturation` | 冷、低饱和、安静 |
| 室内暖光 | `warm indoor lighting, soft shadows, amber tones` | 亲密、日常 |
| 逆光 | `backlighting, rim light, glowing edges` | 轮廓发光，主体与背景自动分离 |
| 舞台 | `spotlight, dark background, rim light` | 强明度分离，主体自动浮出 |

> 逆光 / 边缘光**同时**是分色手段与光效，性价比最高；不确定时优先加它。

## 6. 主体与背景分色配方（四选一，至少用一个）

```text
温度分离  warm amber skin tones against a cool blue-grey background
明度分离  a bright subject against a dark background
饱和分离  a vivid subject, desaturated background
色相分离  a red-clad figure against a deep green forest
边缘分离  + rim light
```

- 背景色块越少越高级：`simple background` + 两三个色块，胜过"五彩斑斓"；
- 眼睛、发饰、签名配件用**强调色**，是最便宜的记忆点；
- **反面写法**：`warm face, warm background, warm clothes` ——冷暖不分开，主体必然陷进去。

## 7. 常见失败 → 最小处方

| 现象 | 最小处方 |
|---|---|
| 发灰 / 发浑 | 定一个主色相 + 一个对比色相；主体加饱和、背景降饱和 |
| 暗部发脏 / 发死 | 暗部改用环境色（`deep blue shadows` / `dark teal shadows`），亮暗色相相反 |
| 刺眼 / 廉价 | 删掉 `colorful`；只留一个高饱和，其余降到 `muted colors` |
| 互补交界振颤 | 错开明度：一边亮一边暗，或只让一边高饱和 |
| 主体陷进背景 | 加温度或明度分离，再补 `rim light` |
| 只有一个调子 | 拉开明度跨度，或加一个**点名物体**的强调色 |
| 前后景粘成一片 | 加 `atmospheric perspective`，远景降饱和 + 偏冷 + 低对比 |
| 色彩割裂 | 收敛到主 / 辅 / 强调三色，其余去饱和 |
| 太花 | 删 `gradient background` / `colorful background`，改 `simple background` |
| 与画风冲突 | 极简平涂就删彩色光斑，回到 `flat color` + `limited palette` |
| 批量出图饱和度飘 | 画师标签权重压到 2 以内，颜色统一交给自然语言描述 |

## 8. 配色自检清单

- [ ] 是不是**只用了一套**配色骨架？
- [ ] 主 / 辅 / 强调是否清楚？颜色数量收敛了吗（不是每个元素一个颜色）？
- [ ] 主体与背景之间**至少做了一层分离**（温度 / 明度 / 饱和度 / 色相 / 边缘光）？
- [ ] 暗部写的是**环境色**还是"固有色变暗"？亮部与暗部的色相相反吗？
- [ ] 有远景时，**大气透视**做了吗（远景降饱和 + 偏冷 + 低对比）？
- [ ] 光的颜色交代了吗？整张图的基调能用一句话说清吗？
- [ ] 明度 × 饱和度的落点与想要的情绪一致吗（别停在"中明度中饱和"）？
- [ ] 互补对撞时**明度错开**了吗（不是两边都又亮又饱和）？
- [ ] 颜色标签是否 ≤3 个，其余都写进自然语言了？
- [ ] 有没有写互斥组合（`vibrant colors` + `muted colors`、`high contrast` + `low contrast`、
      `monochrome` + 彩色词）？
- [ ] 用了 `teal and orange` / `duotone` 之类**自带配色**的词时，是否又叠了一套骨架？
- [ ] 用户已经指定的颜色 / 情绪，是否一个字都没改？
- [ ] 正文里没有宽高比、分辨率、种子、CFG、步数、模型名？

## 9. 暗部环境色与大气透视（纵深与通透）

### 9.1 暗部不是"固有色变暗"

把阴影写成同一个颜色的低明度版，是"发灰 / 发脏"最隐蔽的成因。暗部的颜色应当来自
**环境光**，并且**与亮部色相相反**：

```text
暖光冷影  warm golden light with cool blue shadows
冷光暖影  cool moonlight with warm amber bounce light in the shadows
```

| 反面写法 | 问题 | 改法 |
|---|---|---|
| `black shadows` | 纯黑压死颜色，画面发闷 | `deep blue shadows` / `dark teal shadows` |
| `darker red clothes` | 暗部只是固有色变暗 → 灰 | 暗部改成环境色（冷影或暖影） |
| 亮暗同色相 | 缺冷暖对比，画面平 | 亮暖暗冷（或亮冷暗暖） |

- `bounce light`（反光）是给暗部补环境色最省事的词，高级感常见来源；
- 与 `rim light` 分工：`rim light` 勾**轮廓**（分离主体与背景），`bounce light` 补**暗部**（通透度）。

### 9.2 大气透视（有远景就必须做）

远景**降饱和 + 偏冷 + 提明度 + 降对比**，否则前后景粘成一片、没有纵深：

| 层次 | 颜色处理 |
|---|---|
| 前景 | 饱和最高、对比最强、色相最纯 |
| 中景 | 略降饱和、对比减弱 |
| 远景 | 明显降饱和 + 偏冷偏灰 + 低对比 |

```text
atmospheric perspective, hazy distant background
the distant towers lose saturation, lift in value and drop in contrast
```

> **别和第 6 节的分色搞混**：分色管主体**跳出**背景（局部对比），
> 大气透视管**纵深**（整体由近到远的衰减）。两者可以同时用。

## 10. 双色调 / 电影感调色（用户点名时直接用）

这些词**本身就规定了配色**，用了就不要再叠一套骨架（会互相稀释）：

| 名称 | 写法 | 观感 | 注意 |
|---|---|---|---|
| 青橙 | `teal and orange color grading` | 商业电影感：肤色暖、环境冷 | 最稳的电影调色，人物题材首选 |
| 双色调 | `duotone, two-tone palette` + 点名两色 | 海报、极简、强风格化 | 必须点名是哪两个色，否则会撒开 |
| 单色调 | `monochrome` + 点名色相 | 高级、克制 | 要指定明度跨度，否则是一张灰图 |
| 褪色胶片 | `faded colors, film grain, low contrast` | 回忆、复古 | 与高饱和词互斥 |
| 霓虹双色 | `neon lights, magenta and cyan glow` | 赛博夜景 | 配 `wet asphalt reflections` 最稳 |

> **青橙为什么好用**：它同时满足第 6 节的温度分离（暖主体 / 冷背景）
> 与第 3 节的明度错开（暖亮 / 冷暗），等于一次做完两件事。
