# MOSS-Image 二次元美学规则（官方 + 社区汇总）

配套 `moss-anime-prompt-template`。本文件把**官方文档**、**HF 上的二次元 LoRA 卡**、
**GitHub 社区 skill**、**哔哩哔哩 / Civitai 实测**里可复用的美学规则提炼成可执行条目。
每条标注证据级别：**【官方】**= OpenMOSS 文档明写；**【模型卡】**= 该 LoRA 作者实测；
**【社区】**= 第三方写法，未在本仓库验证。

## 一、模型事实（决定美学怎么写）【官方】

来源：`OpenMOSS/MOSS-Image` 的 `USERGUIDE.md`。

| 项 | 值 | 对美学的影响 |
| --- | --- | --- |
| 架构 | 5B 单流 DiT（42 层）+ **冻结的 Qwen3.5-9B 文本编码器** + FLUX.2 VAE | 文本编码器是**真 LLM**，长英文散文比 tag 汤好得多 |
| 提示词长度 | 约 4K token | 写得下完整的美术描述，不必压缩成短语 |
| 分辨率 | 推荐 **1M / 1.5M / 2M** 像素；0.25M–4M 均可；**边长 16 的倍数** | 小图细节塌，二次元建议 ≥1M |
| 步数 | **≥ 50** 最佳 | 低步数下五官与手指最先崩 |
| CFG | 默认 **3.0**（3.0–6.0）；长提示 3.0 够，短提示要往上加 | 短提示配低 CFG 会糊 |
| Shift | **5.0** | — |
| 采样器 | **Euler** | — |
| SLG | 标准 SLG scale 3（0.01–1.0）；两段式推荐 `uncond skip`、**跳过第 22 层**（22 / 24 / 26 都有用） | **关掉 SLG 会明显更「写实」，但细节容易塌** |
| 负面词 | 官方建议：`nsfw, worst quality, bad anatomy, watermark, jpeg artifact` | 负面不是越长越好 |
| Tag 顺序 | **Quality → Score → Meta → Year → Character → Series → Artist → General** | 只在 tag 串交付时用 |
| 文字渲染 | 支持，但换行与精确排版要靠插入 `\n` 或真实换行 | 海报类必须自己断行 |

> ⚠ 这些是**工作流参数**。按本 skill 的输出契约，**不写进提示词正文**。

## 二、三条最容易被忽略的官方口径

1. **移除 SLG 会让画面变写实**——所以「二次元感」不只是提示词的事；
   提示词已经写成二次元，SLG 关着也会往照片靠。
2. **文本编码器是冻结的 Qwen3.5-9B**，官方要求训 LoRA 时**不要微调文本编码器**；
   因此「画师名」在散文里效果弱，稳定画风只有 **LoRA** 一条路。
3. **Layout 是实验特性**：官方自己说它「让模型更难用」，并为此提供了 layout enhancer。
   二次元里除非要精确放字 / 摆物件，**优先 Caption**。

## 三、二次元的「画种词整组替换」【社区，逻辑可靠】

来源：`jialanhu0915/silver-moss-image-prompt-skill` 的 `references/styles/anime.md`。
核心不是「加一个风格词」，而是**开头整组画种词 + 同步删掉冲突词**：

| 目标画种 | 开头词组（放提示词最前） | 必须同步删掉 |
| --- | --- | --- |
| 90s 赛璐璐 OVA | `1990s (style), retro artstyle, anime screencap, cel shading, hand-painted cel animation, VHS color bleed` | `painterly, soft blending` |
| 黑白漫画网点 | `manga page, monochrome, greyscale, screentones, inked lineart, bold black ink outlines, pen crosshatching` | **正文所有颜色词** |
| 透明水彩 | `watercolor (medium), traditional media, ink and wash, soft pigment bleed on rough cold-press paper` | `flat color, crisp vector` |
| 扁平矢量波普 | `flat color, vector illustration, bold thick colored outlines, hard geometric cel shading, pop palette` | `gradient, airbrush, soft shading` |
| 厚涂刮刀 | `impasto, oil painting (medium), heavy visible brushstrokes, thick palette knife texture, painterly lineless` | `black outlines, lineart` |
| 动画原画手稿 | `anime genga, production art, rough pencil sketch, uncolored layout sheet, blue and red construction lines on paper` | 所有上色词 |
| Q 版 | `chibi, super deformed, 2-head-tall proportions, oversized head, tiny body, bold outlines` | 写实比例词 |
| 浮世绘 / 日本画 | `ukiyo-e, traditional Japanese woodblock print, nihonga, flat mineral pigments on aged washi, sumi ink contours` | `volumetric light, gradient, 3d render` |
| PC-98 像素 | `pixel art, 16-bit PC-98 adventure game graphic, visible square pixel grid, checkerboard dithering, limited palette` | `smooth, gradient` |
| 水墨重彩 | `Chinese wild ink and wash painting, dry-brush sumi outlines with flying-white texture, splashed ink with cinnabar and indigo on yellowed xuan paper` | `flat color, vector, glossy, airbrush` |

**这条是本文件里性价比最高的**：它把「画风」变成「一整组词 + 一组删除项」，
而不是扔一个形容词给模型猜。

## 四、用「版式容器」反推画风【社区】

写清楚**容器 + 容器里的字**，画风会跟着出来：

| 目标 | 开头 | 结尾容器句 |
| --- | --- | --- |
| Galgame / 视觉小说 CG | `visual novel cg, Japanese galgame screenshot, glossy anime coloring` | 底部半透明深蓝对话框 + 名牌，白色文字 `"……你终于来了。"` |
| TV 动画截帧 | `anime screencap, TV anime broadcast screenshot, cel shading, flat anime coloring` | 底部居中黄字黑描边字幕 `"别回头。"` |
| 角色设定集 | `anime character reference sheet, official design sheet on clean white background, multiple views` | 全身正面 + 三个表情头像 + 底部色卡 |
| 集换式卡牌 | `SSR anime trading card, ornate golden holographic frame border` | 顶部标题栏 + 右上五颗金星 + 底部数值框 |

## 五、「精修 / 松弛」分区：防草稿脸与塑料立绘【社区，最实用的一条】

二次元两种典型废图：**笔触松到脸上的半成品**、**全图过度锐化的塑料页游立绘**。
解法是把完成度**按部位分配**，四段骨架直接可抄：

```text
[画师触发词，无则整行删除]
High-taste 2D digital painting with selective focus: finely rendered luminous facial features and delicate hair strands, contrasted against expressive breathable painterly gouache brushwork on the clothing and a softly blurred background. Muted low-saturation palette of [2~3 色名]. Zero rough sketch lines.
[景别] of a slender [年龄] girl with balanced facial proportions, a softly tapered chin and a slender neck. [头颈微动态], she gazes with [眼神]. Soft blush on the nose tip and cheeks, glossy pale lips.
Her silky [发色] hair styled into [发型，加 slightly loose / airy translucent wisps], [手部与道具的简洁动作].
She wears [服装，加 clean matte fabric blocks, without gaudy patterns], set against a softly out-of-focus [背景].
```

三条派生规则（都很具体、都容易踩）：

1. **衣服不要复杂花纹**：`golden floral embroidery` 会分走注意力 → 写 `plain matte fabric blocks, no gaudy patterns`；
2. **发髻/丸子头写「微松」**：`neat round twin buns` → 两个黑球；`slightly loose round buns with airy translucent wisps` → 有层次；
3. **眼睛不要 `jewel-like, sparkling, ultra detailed`**：会触发大头大眼幼态脸 → 写 `luminous, water-clear eyes with soft highlights`。

## 六、主体锚点与年龄【社区】

- 脸靠**三个锚点**：`softly tapered chin`、`slender neck`、`half-lidded, languid`；
- 头发通用补丁：`slightly loose`、`airy translucent wisps`、`loose flyaway strands`；
- 手：`relaxed hands with five distinct fingers, natural knuckles`（二次元最先崩的部位）；
- **年龄双向排除**，且用二次元口径：`neither a big-headed 10-year-old child nor a mature 20-year-old woman`。
  注意社区实测：**即使是否定式，`child / 10-year-old` 也可能被抽出来用**，
  所以更稳的做法是换成 `slender, tall, teenage` 这类正面词。

## 七、色盘：自然语言优先于 HEX【社区】

Layout 的 `summary.palette` 字段 USERGUIDE 未记载（本地编译器接受该字段，但模型侧是否采纳未验证）。

```text
Muted, sophisticated low-saturation palette of dusty blue, warm cream and desaturated terracotta.
dominated strictly by this palette
```

并**删掉正文里与之冲突的具体颜色词**。

三档方案（可靠性从高到低，**不要混用**）：

| 档 | 做法 | 可靠性 |
| --- | --- | --- |
| A（默认） | 不写 `palette` 字段，色盘只写进 `summary.caption` | 高（已验证通道） |
| B（可试） | `summary.palette` 数组 + caption 里同时写同一组色名 | 中（互相印证） |
| C（不推荐） | 只写 `palette` 字段、caption 不提色 | 低（无兜底） |

完整写法、item 拆分规矩、最小示例与专有坑见 `SKILL.md` §13.1。

## 八、LoRA：触发词与参数【模型卡】

### 8.1 两类二次元 LoRA 的实际摆法

| LoRA | 触发词 | 摆位 | 强度 | 备注 |
| --- | --- | --- | --- | --- |
| `Moss-image-anime-lora`（seinen 向，HF `axiomofmind`） | `moss_seinen_style`（**可省略**） | 用则放**开头** | 2000 步/**1.0**（无触发词最佳）；1500 步 0.7–1.0 | **自然提示词里写 `anime character(s)` 比加触发词更好** |
| `FKEY Style`（厚涂二次元，Civitai） | `<\|artist\|>fkey<\|/artist\|>` | **第一行整行，紧跟换行** | **0.4–0.8**，起手 0.6 | 触发词里**不能有空格、句末不能加句号**，否则 BPE 合并边界变了会明显削弱 |
| `Kemmy Flat Half`（柔和平涂） | — | — | — | 软平涂 + 轻赛璐璐 + 干净线条 |

### 8.2 FKEY 卡给出的「结构 token」纪律【模型卡】

因为文本编码器是 Qwen3.5-9B，`<|...|>` 是**结构 token**：

- `<|artist|>fkey<|/artist|>` 与 `<|artist|> fkey <|/artist|>.` **不是同一个 token 序列**；
- 写法固定：**第一行、无空格、无句号、紧跟换行**；
- 风格不够强时，**先检查这一行**，不要先去调强度。

### 8.3 参数（FKEY 卡）

16–28 步（16 锐、25 适合复杂光）；CFG 3.0–3.5（过 4.5 对比度烧掉）；
`sgm_uniform` + `euler`；Flow shift 5.0（`ModelSamplingSD3`）；0.65–1.0 MP；边长 16 倍数。

> 再次强调：以上是**工作流参数**，不进提示词。

## 九、哔哩哔哩的一条二次元画风控制法【社区】

> UP 主结论：「用 Danbooru 的部分画风 tag + 自然语言短句**混合书写**，然后用
> `<|style|>` 标签包裹并**放在提示词开头**。」

与官方 tag 顺序、本 skill 的「画风独立首句」是同一条思路的两种表述：
**画风词必须在最前面，并且成组出现**。

注意 `<|style|>…<|/style|>` 属于**社区写法，不在官方文档里**，用之前先 A/B 一次，
判据：同一 seed 下脸是否更稳、特征是否串味。

## 十、二次元专属的负面层【社区】

在官方负面 `nsfw, worst quality, bad anatomy, watermark, jpeg artifact` 之外，二次元要加：

```text
oversized head, big round babyface, short stubby neck, wide-open staring eyes,
flat chest, plastic skin, oversaturated neon colors, gaudy gold embroidery, thick black outlines,
photorealistic, real human, photograph, camera flash, film grain, microscopic pores, 3d render
```

两条纪律：

- **要写字幕时，负面里去掉 `text` 与 `watermark`**，否则字幕会被一起压掉；
- **黑白漫画通道要删掉颜色词**，否则会变「局部留色」漫画。

## 十一、这条通道的专有坑（清单）

- 写实词残留（`pores, camera flash, film grain, unretouched`）→ 一定推回照片；
- 只写 `cel shading` 一个词切不动画风：正文其余 150 词还在描述写实毛孔时会被压制；
- Q 版通道混入正常比例描述 → 半 Q 半正常；
- `[R]` 档（关 SLG、低步数）：手指、双眼对称、发丝层次最先崩，必须补防崩短语；
- `[Q]` 档（开 SLG）：不要堆 `ultra detailed, intricate`，会把边缘拉硬。

## 十二、出处

- 【官方】`OpenMOSS/MOSS-Image` — `USERGUIDE.md`（参数、prompt guidelines、Layout、caption 规范）
- 【模型卡】HF `axiomofmind/Moss-image-anime-lora`（seinen 风、触发词可省、参数）
- 【模型卡】Civitai `FKEY Style | Painterly Anime LoRA for MOSS-Image`（结构 token 纪律、强度、参数）
- 【社区】GitHub `jialanhu0915/silver-moss-image-prompt-skill` — `references/styles/anime.md`、`examples/anime.md`
- 【社区】哔哩哔哩《【MOSS-Image】十八种二次元画风分享》（画风 tag + 自然语言混合、`<|style|>` 包裹置顶）
- 【社区】Civitai `Kemmy Flat Half`、`nkss style MOSS` 等二次元风格 LoRA 卡
- 【工具】HF `realrebelai/MOSS-Imagine_ComfyUI`、ComfyUI 官方 MOSS-Image 教程与模板

> 本文件只提炼方法，不复制其正文、示例图与 LoRA 权重。
> 社区条目均为第三方经验，效果随模型版本 / LoRA / 参数变化，以实测为准。