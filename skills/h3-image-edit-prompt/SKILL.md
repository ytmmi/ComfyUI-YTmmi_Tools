---
name: h3-image-edit-prompt
description: Write MiniMax-H3-Image reference-image edit prompts as one continuous paragraph in the official order — define every <Picture N> as a <Subject N>, state the target overview and each source's role (fully preserved / partially preserved / attribute transfer / weak reference), then complete the changed and newly written content. Use when editing, combining, restyling or extending supplied images with H3-Image, keeping product or character identity across up to 16 references, or when an edit prompt fails because preserved content drifts or two references bleed into each other.
version: 1.0.0
---

# MiniMax-H3-Image 参考图编辑提示词（H3-image Edit Prompt）

H3-Image 的编辑与文生图**同一个 checkpoint**，但提示词的写法完全不同：
编辑写的是**一段连续的、描述最终成品**的散文，按官方固定顺序组织，而不是一串指令。

## 何时使用

- 用户提供 1–16 张图，要求改颜色 / 换物体 / 换背景 / 合成 / 换风格 / 延伸画面；
- 要保住商品或角色的**身份一致性**，只改其中一部分；
- 已有的编辑提示词「保不住该保留的东西」或「两张参考图互相串味」；
- 需要在多轮编辑里指定「这一轮用哪张图、改什么、什么不变」。

**不适用**：
- 没有参考图的纯文生图 → `h3-image-prompt-writing`；
- H3 **视频**的全参考模式（Ref2VA）→ `h3-prompt-writing`；
- 需要用遮罩做局部重绘 → H3-Image **不支持**遮罩编辑，改不了就换模型或换方案。

## 输出契约

1. **只输出一段连续纯文本**（英文），不要分段标题、不要 bullet、不要代码块围栏、
   不要开头说明与结尾建议。
2. **不要打印组织用的阶段名**（「源定义 / 目标总述 / 变化细节」只用于你自己排结构）。
3. **叙述最终状态**，不要写编辑命令：
   `The former location is filled by continuous tabletop.` 而不是 `Remove the cup.`
   （要显示的字面文案本身可以是命令句，那是画面内容。）
4. 参考图按**用户给出的顺序**写成 `<Picture 1>`、`<Picture 2>` …；
   `@Picture 1`、`@图1` 都视为 `<Picture 1>`。
5. **不写负面词、不写参数**（6 步、CFG 1 固定；没有 negative 分支）。

## 三段结构（官方顺序，不可调换）

### ① 定义参考内容

- 每张图里被用到的东西给一个编号：`The red cup on the left in <Picture 1> is <Subject 1>.`
- `<Picture N>` 保持用户给的顺序，`<Subject N>` **全文稳定**，不要中途换号。
- 一个身份由多张图支撑时，**逐张点名**，不要写「所有参考图」。
- 只借**属性**的图，定义为属性而不是整个物体（`The body color of the vase in <Picture 2> is <Subject 2>.`）。
- **完全移除 / 全新目标**不占 Subject 号，在目标总述里说明位置。
- 每处文字 / 数据要**逐行转录一次**（含将被改写的原文），保留语言、标点、大小写、行序；
  看不清就写「无法辨认」，**不要猜**，也不要把它当成删除许可。

### ② 目标总述与各源关系

- 以 `The target image` 开头，先给最终画面是什么（局部编辑 / 参考图合成）。
- **画布与版面**：有明确尺寸 / 裁剪就照用；否则保留被编辑底图的画布。
  用「底图或指定构图参考」决定取景，**不要用给颜色的参考图决定取景**。
- 每个 Subject 都要有**独立的关系句**：

| 关系 | 写法 |
| --- | --- |
| 完全保留 | 单独一句：`<Subject N> is fully preserved.` |
| 部分保留 | 写明保留哪些类别、改动什么 |
| 属性迁移 | `<Subject 2> supplies the exact body color transferred to <Subject 1>.` |
| 弱参考 | `<Subject 2> serves as a weak style reference for the new background, with freely adapted forms.` |

- **移动 / 旋转 / 复制 / 重新打光 / 遮挡都算改动**；「完全保留」的父项里不能有被编辑的子项。
- 新产生的影子与反射，算作它影响到的范围的改动。
- 精确颜色直接引用源属性，**不要猜 HEX、也不要换成近似色名**（用户给了值才写值）。

### ③ 写完变化与新增内容

- 把结果写具体：形状、材质、接触、纵深、透视、光、版面。
  换整张环境可以写长；只改一个颜色就该**保持局部**。
- **删除**用「结果表面 / 空出的空间」描述；**移动**是移位，**复制**是新增实例，三者不要混。
- 完全保留之后只用裸 Subject 号做锚点，**不要重新描写它的外观**；
  部分保留只展开变化，不重复保留部分的外观。
- 文字改动给**完整结果行**；翻译给出实际译文，原文留在定义里。
- 结果写完就停，不要补充无信息量的内容。

## 硬规则

- **一张图一个明确目标**：多轮编辑时写明这一轮用哪张、改什么、什么不变；
  不要写「之前那张」这种指代。
- **宫格写行列**（`2 rows and 3 columns`），指定位写 `row 2, column 1`。
- **不要编造看不见的细节**：隐藏部分、看不清的文字、精确色值、陌生物体身份都不许猜；
  需要时用可见线索定位。
- **不确定要局部化**：能支持的内容写完，看不清的区域保留原样，不要声称已完整转写。
- 用户没给目标描述也行——你负责把目标补成可画的描述（这是官方明确允许的）。

## 画幅

- 保留输入取景时，**用输入图的比例**；改版式时按新版面选，范围 1:3–3:1。
- 16 MP 常用：1:1 4096×4096、4:3 4736×3552、3:4 3552×4736、16:9 5472×3072、9:16 3072×5472。
- 画幅与尺寸写在工作流 / 参数里；本 skill 只在末尾用 `Aspect ratio: W:H` 一行给出建议。

## 常见失败与修法

| 症状 | 根因 | 修法 |
| --- | --- | --- |
| 该保留的变了 | 没写「完全保留」句 | 给每个非目标 Subject 补 `<Subject N> is fully preserved.` |
| 两张参考图串味 | 一个 Subject 混合了两个来源 | 拆成两个 Subject，各自定义角色与保留范围 |
| 换了颜色但形状也变了 | 只写「部分保留」没列保留类别 | 写明 shape / material / position / scale 都保留 |
| 改动扩散到全图 | 改动范围没界定 | 写清「变化到哪为止」，并说明其余部分不变 |
| 文字改了但排版崩了 | 只给替换词 | 给完整结果行，并说明版面 / 图表结构是否保留 |
| 参考图编号对不上 | 编号中途换号 / 用了「所有参考图」 | 固定 `<Subject N>`，多图支撑时逐张点名 |
| 编辑提示词写成命令 | 沿用 inpainting 习惯 | 改写成「最终状态」的叙述句 |

## 自检清单

- [ ] 每张被用到的参考图都有 `<Picture N>`，且顺序与用户给的一致；
- [ ] 每个被用到的内容都有稳定的 `<Subject N>`，编号全文没有变化；
- [ ] 每个 Subject 都有明确关系（完全保留 / 部分保留 / 属性迁移 / 弱参考）；
- [ ] 画布 / 取景有依据（底图或指定构图参考），不是来自颜色参考图；
- [ ] 改动范围写清了，删除用「填补后的表面」描述；
- [ ] 文字改动给了完整结果行；看不清的内容没有被猜；
- [ ] 没有负面词、没有参数、没有阶段小标题、没有代码块围栏；
- [ ] 只有一段连续文本。

## 示例

**输入**：`@Picture 1` 是左边一只红杯、右边一颗柠檬放在桌面；「只把红杯改成蓝色，其它都别动」

**输出**：

```text
The red cup on the left in <Picture 1> is <Subject 1>. The lemon on the right in <Picture 1> is <Subject 2>. The target image shows <Subject 1> with a blue finish. <Subject 1> is partially preserved; its shape, material, position, and scale remain while its surface color changes. <Subject 2> is fully preserved. The blue finish follows the existing surface shading and highlights of <Subject 1>, with the rest of the source image unchanged.
```

`Aspect ratio: 4:3`

**输入**：`@Picture 1` 是米色大衣正面图，`@Picture 2` 是一只彩色釉面花瓶；
「用图 1 的大衣做一张竖版时尚海报，颜色严格照图 2 的瓶身色，版型和面料不变，写一句英文标题，不要品牌名」

**输出要点**：`<Subject 1>` = 大衣（部分保留：版型、面料、褶皱、正面展示不变，颜色 / 尺度 / 位置改变）；
`<Subject 2>` = 瓶身颜色（`supplies the exact body color transferred to <Subject 1>`，
并注明不引入釉面与瓶型）；目标总述给海报版式与标题位置，标题**逐字加引号**写出。

## 边界

- **不执行**脚本、不调 API、不生成图片。
- 不猜看不见的内容；不把编造的数据当真实数据。
- 不支持遮罩局部重绘与透明背景——用户要这些时说明限制并给替代方案。
- 参考图涉及版权素材时按描述性使用处理，商用需自行取得授权。
