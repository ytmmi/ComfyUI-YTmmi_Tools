# Krea 2 二次元社区实践参考（2026-11 整理）

配套 `krea2-anime-style` / `krea2-anime-character` / `krea2-anime-keyvisual`。
收录社区里**可复现、可核对**的做法；每条都标注来源，便于读者自行查证。

## 一、整场媒介先行（whole-scene medium）

来源：`sjh9714/krea2-wildcards` 的《Krea 2 whole-scene style recipes》
（整理自 r/StableDiffusion 的实测帖）。核心一条：

> **Put the medium first and make it describe the whole scene.**
> Then add the subject, composition, and details that belong to that medium.

同一个主体、同一个种子，只改措辞，结果差别很大：

| 写法 | 示例 | 问题 |
| --- | --- | --- |
| 命名式（弱） | `Children's picture book drawing, soft crayon and gouache…` | 像在桌上摆了一本绘本 |
| 整场式（强） | `Drawn the way a children's picture book is drawn: soft crayon and gouache, simple rounded shapes, flat gentle colour.` | 整张画面按这个媒介重画 |

**这是本仓库 `krea2-anime-style` 四维锚句的社区补充**：锚句不仅要写媒介，还要写清
「**整张画面都是用这种方式画的**」（`the whole scene drawn as …` / `drawn the way … is drawn`）。

### 八条可直接用的整场从句（约 100 字符，纯英文，无模型专属词）

```text
The whole scene drawn as black-and-white manga: ink linework, screentone shading, no colour anywhere.
The whole scene as a watercolour storybook illustration: soft washes, gentle linework, painted background.
The whole scene as comic-book art: bold ink outlines, flat colour, halftone dots, drawn background.
The whole scene drawn chibi: super-deformed proportions, huge head, tiny body, flat cel colour throughout.
The whole scene as a vintage gouache travel poster: flat opaque paint, simplified shapes, limited warm palette.
The whole scene as a 1970s cel anime frame: hand-painted cels, muted palette, film grain, painted background.
Printed the way pop art is printed: bold black outlines, flat primary colour, visible halftone dots.
The whole scene as a 1960s limited-animation cartoon: angular flat shapes, off-register colour, painted backdrop.
```

从摄影切到插画时，社区给了三条替换：

- `facing the camera` → `facing the viewer`
- `shallow depth of field` → `simplified background detail`
- 镜头与影棚光术语 → 笔触、色盘、纸张、油墨、印刷术语

## 二、提示词结构顺序（社区微调模型的经验）

来源：Civitai `Krea2 Cat Tower`（动漫向 Krea 2 微调）的 Prompting guidelines。
它建议的七段顺序与本仓库的六层骨架基本一致，可作为**另一种排布**：

```text
Main Subject + Pose/Action
→ Appearance, Clothing & Details
→ Props & Materials
→ Composition, Framing & Perspective
→ Environment & Background
→ Lighting, Color Palette & Mood
→ Overall Aesthetic & Medium
```

另一条重要提醒（同页）：

> **Unless you specify a particular style in the prompt, the default style will be anime-style.**

含义：动漫向微调模型的**默认风格就是二次元**，你不写反而更「标准」；
要做出风格差异，必须**显式给画风锚句**，否则得到的是通用的「AI 动漫感」。
这条正好解释了本仓库反复强调「一句锚句」的原因。

## 三、LoRA 触发词的两种摆放（社区实测）

| 来源 | 摆法 | 说明 |
| --- | --- | --- |
| Krea 官方 `Krea-2-LoRA-retroanime` | 末尾 | 例：`A deer grazing in the forest. Purple retro anime style` |
| 社区 `Epic Cinematic Anime (Krea2)` | **开头** | 触发词 `@snkbrush` 放在最前，后面用**平实句子**描述，不用标签、不用风格词 |

**结论**：位置**取决于该 LoRA 的训练方式**，官方风格 LoRA 用末尾、部分社区 LoRA 用开头。
通用做法：**按模型卡写的摆**；模型卡没写就先用末尾（官方风格 LoRA 的默认）。
两种都不要写权重数值进提示词。

### 二次元社区常见「避坑」参数（不进提示词，仅供工作流参考）

- CFG **不要超过 4**：Krea 2 Turbo 上 CFG 过高会让颜色「飞」成油画色块
  （来源：发现AI 社区帖《Krea 2 Turbo 挂 748cm 跑 Niji 二次元的避坑参数》）；
- Clip Skip 固定 **2**；
- 深色制服 / 夜景暗部发焦时，社区做法是 **LoRA 权重 0.75 + 文本权重 1.0**；
- 动漫向微调（Cat Tower 等）：分辨率 1024–2048、8 步、CFG 1、euler / er_sde、simple / normal。

> ⚠ 以上是**工作流参数**，按本仓库规则**不写进提示词正文**。

## 四、跨格角色一致：character_id 复用

来源：社区微调 `krea2-turbo-bbox` 的 `PROMPTING.md`（约 90% 训练使用紧凑 grounding DSL）。
它给了一个**可直接借用的思路**：给角色一个**短编号**，每出现一次就复用同一个编号。

```text
p[0,0,1000,333]  Top panel: the barista takes an order, alert and cheerful.
p[0,333,1000,666] Middle panel: the barista pulling shots, sleeves pushed up, focused.
ac:1[80,40,400,320] A barista with a messy green hoodie and short auburn hair, smiling brightly.
ac:1[560,370,900,650] The same barista mid-shift, sleeves rolled, brow furrowed.
```

三条可迁移到**纯自然语言**的结论：

1. **编号只是「这是同一个」的标签**，身份仍来自描述——所以每次出现都要**重述关键特征**；
2. **编号要短**（`1` / `2` / `3`），长 slug 会占预算且容易写错；
3. 同一角色在多格里**编号相同**、描述不同（描述变的是表情 / 姿态，不变的是特征）。

`krea2-anime-character` 的五段式身份块就是这条的「自然语言版」：
身份块 = 编号所指向的那段描述，每张图原样复制。

## 五、哔哩哔哩生态里值得知道的东西

（均为社区作品，非官方，链接会随作者调整而失效）

| 方向 | 内容 | 对本仓库的用处 |
| --- | --- | --- |
| 风格批量 | UP 主整理 Krea 2 风格情绪板扩展（数千条）、风格扩展（数百条）与官方提示词通配符（近 2 万条），配合 `comfyui-easy-use` 的风格选择器 / 通配符节点使用 | 说明「风格词」在社区是**批量资产**，所以更需要**一句锚句 + 四维属性**来收敛 |
| 动漫向 LoRA | 场景原画师向 LoRA（二次元概念 / 装饰艺术 / 科幻 / 古风四风格）、AsianMix 亚洲混血脸型（触发词 `asian woman`，权重 0.8 起） | 触发词要**逐字照抄、按模型卡摆位** |
| 工作流 | 多模型对照、提示词反推洗图、a2r（动漫转真人）等整合流 | 反推洗图时仍要**重写画风锚句**，否则反推出来的只是「通用动漫感」 |
| 实践帖 | 论坛实测「CFG 一过 4 色彩就飞」「Clip Skip 锁 2」 | 已收进第三节避坑参数 |

## 六、把社区做法接进本仓库 skills 的位置

| 社区做法 | 落到哪个 skill 的哪一节 |
| --- | --- |
| 整场媒介先行、八条整场从句 | `krea2-anime-style`「一、画风锚句」与「五、整场从句速查」 |
| 七段结构顺序、默认即动漫 | `krea2-anime-prompt`「写作顺序」补充说明 |
| 触发词开头 vs 末尾 | `krea2-anime-style`「五、用了 LoRA 时怎么写」 |
| character_id 复用 | `krea2-anime-character`「三、设定表」与「四、三道保险」 |
| 避坑参数 | 仅作为工作流提示，**不写进提示词** |

## 七、出处

- `sjh9714/krea2-wildcards` — `styles/README.md`（八条整场从句；原始讨论在 r/StableDiffusion）
- Civitai `Krea2 Cat Tower`（`nukomasshigura/Krea2-Cat-Tower`）— Prompting guidelines / Recommended Setting
- HuggingFace `jimmycarter/krea2-turbo-bbox` — `PROMPTING.md`（grounding DSL、character_id）
- HuggingFace `krea/Krea-2-LoRA-retroanime` — 官方风格 LoRA，触发词 `Purple retro anime style`，放末尾
- Civitai `Epic Cinematic Anime (Krea2)` — 触发词 `@snkbrush` 放开头，平实句子描述
- 发现AI 社区帖 — Krea 2 Turbo 跑 Niji 二次元的 CFG / Clip Skip / 权重避坑
- 哔哩哔哩 — Krea2 风格情绪板与通配符整理、动漫向 LoRA 与工作流合辑、`krea2-anime-prompt-director` skill（B 站有配套讲解视频）

> 以上均为社区经验，**非 Krea 官方规范**；不同模型变体、不同 LoRA 可能表现不同，
> 以实测为准。本文件只提炼方法，不复制其正文与示例图。