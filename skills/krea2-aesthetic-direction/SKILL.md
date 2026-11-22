---
name: krea2-aesthetic-direction
description: Decide and write the aesthetic layer of a Krea 2 prompt — one dominant art direction instead of stacked adjectives, a lighting setup with a named source, material and surface behaviour, a counted palette with deliberate relationships, and grain/lens/texture that removes the generic AI look. Also maps Krea 2's own controls (Creativity Raw/Low/Medium/High, Intensity/Complexity/Movement sliders, up to 4 style references, moodboards) into equivalent prompt wording for workflows that expose only a text box. Use when Krea 2 output looks flat, plastic, over-polished, symmetrically perfect or "AI-generated", or when the user asks for a mood such as editorial, filmic, quiet luxury, analog, brutalist, pastel, neon or painterly.
version: 1.0.0
---

# Krea 2 美学方向（Aesthetic Direction）

Krea 2 的强项是**风格与创作方向**——它不是靠堆形容词变好看，而是靠你**替它做美术决定**：
一个主方向、一束有来源的光、几种讲得清的材质、一套数得过来的颜色、一点恰到好处的脏。

本 skill 只管**美学这一层**，不管主体设定、不管二次元角色、不管长文母题。

## 何时使用

- 出图**很 AI**：塑料感、过度干净、对称到假、脸像通用模特；
- 出图**平**：没有光、没有材质、颜色是"默认色"；
- 用户给的是**调性词**（编辑感 / 电影感 / 静谧 / 奢华 / 赛博 / 复古 / 手作 / 疗愈）；
- 需要**同一调性跨图稳定**（系列图、品牌 KV、分镜）；
- 工作流只有文本框，想复现 Krea 2 的滑杆 / 风格参考 / 情绪板效果。

**不适用**：
- 主体与叙事怎么搭 → `krea2-prompt-writing`；
- 二次元画风与角色 → `krea2-anime-prompt`；
- 1500–2700 词编辑级长文 → `krea2-editorial-longform`；
- 纯配色规则（跨模型通用）→ `image-color-harmony`（本 skill 只做 Krea 2 的落位与叠加）。

## 输出契约

1. **只输出提示词正文**（英文），不要解释、不要标题、不要代码块围栏、不要结尾建议。
2. 正文里**必须能读出四个决定**：主方向、光的来源、材质与表面、色盘关系。
3. **不写参数**：不写滑杆数值、不写 Creativity 档位名、不写分辨率、步数、采样器、
   LoRA 权重——这些属于界面控件，写进提示词只会变成噪声。
4. **不写空词**：`beautiful` / `perfect` / `high quality` / `8k` / `award-winning` /
   `masterpiece` 一律换成可观察的属性。
5. 用户点名的调性**原样保留**，只在空缺处替它做决定；不要偷换成你自己的偏好。

## Krea 2 的美学杠杆（官方控件 → 提示词等效写法）

Krea 2 界面上的四个控件，在只有文本框的工作流里要靠**措辞**来预演：

| 控件 | 官方行为 | 提示词里的等效写法 |
| --- | --- | --- |
| **Creativity: Raw** | 不扩展，只渲染明确描述的内容 | 描述**必须写满**：每个材质、每束光都要点到，不能留空让模型猜 |
| **Creativity: Low** | 紧贴字面，只补明显空缺 | 写主结构与光，细节留一层空白 |
| **Creativity: Medium**（默认） | 合理诠释 | 常规写法即可 |
| **Creativity: High** | 强力扩展，风格与氛围上发挥 | 只给方向词与锚句，让模型补细节（正文写短，靠主方向撑） |
| **Intensity −** | 平淡、暗哑 | `muted, desaturated, low-contrast, matte, flat light` |
| **Intensity +** | 风格化强烈 | `bold stylization, saturated accents, strong value contrast` |
| **Complexity −** | 简洁、干净 | `minimal, generous negative space, three elements only, clean edges` |
| **Complexity +** | 杂乱、密集 | `densely layered, crowded detail, overlapping forms` |
| **Movement −** | 静态 | `still, poised, quiet, no motion` |
| **Movement +** | 强姿态与镜头运动 | `mid-gesture, wind-swept, motion blur on the trailing edge, tilted framing` |
| **风格参考（≤4 张）** | 抽取风格并加权 | 用文字描述该参考的**四维属性**：色盘 / 线条 / 材质 / 构图 |
| **情绪板** | 整组图的共同方向 | 写一句 `the whole frame belongs to one visual world: …` 然后只给该世界的三条规则 |
| **Krea 风格（LoRA）** | 锁定某个美学 | 用 `a coherent look built on …` 描述它锁的是什么，**不要写 LoRA 名** |

> 滑杆与 Creativity 相互独立：Creativity 管"读得多字面"，滑杆管"输出长什么样"。
> 文字侧同理——**锚句决定方向，措辞密度决定发挥空间**。

## 五层美学骨架（缺层跳过，别改顺序）

| 层 | 要回答的问题 | 反面 |
| --- | --- | --- |
| ① 主方向 | 这是什么类型的美学？只选**一个** | `cinematic + anime + cyberpunk + Ghibli` 互相稀释 |
| ② 光 | 光从哪来、多高、多硬、什么色温、影子落在哪 | `dramatic lighting` / `beautiful light` |
| ③ 材质 | 2–4 个材质分区，各自的触感与反光行为 | 每个表面都写 `detailed` |
| ④ 色盘 | 3–5 个颜色 + 大致占比 + 谁是强调色 | 只写 `colorful` / `vibrant` |
| ⑤ 质感与镜头 | 颗粒、镜头、景深、微瑕疵 | 全都干净锐利，像渲染图 |

**一密一空**：一层的细节密度拉满，另一层必须留白。整张都密 = 糊成一团。

## 反「AI 感」十条硬规则

1. **材质要讲得清**：`brushed aluminum`、`coarse linen`、`chipped enamel`、
   `wet asphalt`——不是 `high quality material`。
2. **光要有来源**：`a single low sodium lamp on the left`，并且写出影子方向。
3. **颜色要数得过来**：3–5 个，给一个"意外色"打破单调。
4. **允许不完美**：磨损、灰尘、指纹、折痕、水渍、旧标签——一处就够，会立刻去塑料感。
5. **避免完美对称**：主体偏轴、地平线略斜、前景遮挡一角。
6. **给尺度参照**：`a hand for scale`、`waist-high`、`two-storey`。
7. **写媒介与工艺**：`shot on 35mm`、`screen-printed`、`gouache on cold-press paper`。
8. **控制细节密度**：明确说"哪里密、哪里空"。
9. **人物写"表面"不写"评价"**：写皮肤质感、发丝走向、衣料垂坠，不写 `beautiful face`。
10. **删掉所有评价性形容词**：`stunning`、`breathtaking`、`ultra-detailed` 都换成观察。

## 调性 → 配方

常见调性都有可复用的**骨架**（不确定时先按骨架走，再改内容）。
配方库见 `references/krea2-aesthetic-recipes.md`：胶片写实、编辑大片、静谧留白、奢华材质、
粗野主义、赛博霓虹、手作纸感、复古广告、暗调油画、日系清新、工业纪实、粉彩梦境。

用法：**配方锁结构（光位 / 材质分区 / 色盘关系），不锁内容**——内容永远来自用户需求。

## 与风格参考 / 情绪板的文字替代

工作流里贴不了图时，把参考图拆成四维来描述（不要假装看过图）：

```text
The palette follows <两到三个颜色 + 占比>; the linework is <线条特征>;
surfaces are <材质与反光行为>; the framing leans on <构图特征>.
```

情绪板则用一句"世界规则"锁定，例如：
`Every surface in this frame belongs to the same quiet world: chalk-white plaster, one warm lamp,
and nothing glossy.`

## 常见失败与修法

| 症状 | 根因 | 修法 |
| --- | --- | --- |
| 塑料感 / 像 3D 渲染 | 材质只有名词没有触感 | 每个材质补"触感 + 反光行为"，再点一处磨损 |
| 过度干净 | 没有任何微瑕疵 | 加一处灰尘 / 指纹 / 折痕 |
| 画面发灰 | 色盘没结构、暗部没有颜色 | 给暗部指定一个色相（`shadows lean cool teal`） |
| 主体陷进背景 | 明度与饱和度没分家 | 主体高对比、背景压饱和 |
| 风格像大杂烩 | 堆了两个以上主方向 | 只留一个主方向，其余降为"偏移"并写清偏移层 |
| 人物"AI 脸" | 写的是评价不是特征 | 换成可见特征：肤质、发丝、痣、表情肌肉 |
| 整张糊成一团 | 每层都密 | 执行"一密一空"，并写清哪里空 |
| 写死参数后效果更差 | 把滑杆 / LoRA 数值写进正文 | 删掉数值，改成等效描述 |

## 自检清单

- [ ] 只有一个主美学方向，没有互相稀释的第二个；
- [ ] 光有来源、方向、软硬，且影子有落点；
- [ ] 2–4 个材质分区，每个都有触感与反光行为；
- [ ] 色盘 3–5 色，有主色 / 对比色 / 意外色，暗部有颜色；
- [ ] 有质感或镜头层（颗粒 / 镜头 / 景深 / 微瑕疵）；
- [ ] 没有 `beautiful` / `perfect` / `high quality` / `8k` / `masterpiece`；
- [ ] 没有滑杆数值、Creativity 档位名、LoRA 名、分辨率；
- [ ] 没有标题行、代码块围栏、解释与结尾建议。

## 示例

**输入**：「一张高端面霜的产品图，要高级感」

**差的写法**：`a luxurious premium cosmetic product photo, high quality, elegant, beautiful lighting, 8k, masterpiece`

**输出**：

```text
A studio still life of a frosted glass cosmetic jar standing on a slab of honed limestone. The jar
occupies the lower third and slightly right of center, its brushed-aluminum lid catching one narrow
specular streak. Light comes from a single large softbox above and to the left at roughly 45
degrees, so the jar casts a short, soft-edged shadow to the lower right and the limestone's pores
stay readable in the highlight. Surfaces are deliberately few: cold frosted glass with a faint
condensation haze, warm matte stone, and one shallow pool of water that mirrors the lid in a broken
line. The palette is roughly 70% warm bone, 20% cool grey, 8% deep green from a single folded leaf
at the left edge, and 2% warm brass in the lid. Fine 35mm film grain sits evenly across the frame,
and the background falls off into a soft gradient of the same bone tone. A small paper label on the
jar is slightly lifted at one corner.
```

## 边界

- 不执行脚本、不生成图片、不调 API。
- 不写参数（滑杆、Creativity 档、LoRA、分辨率）——这些由工作流决定。
- 不做版权画师模仿；需要"像某位画家的质感"时翻译成媒介 / 线条 / 上色 / 色盘 / 时代。
- 配方库锁结构不锁内容，禁止把示例道具直接搬进用户画面。
