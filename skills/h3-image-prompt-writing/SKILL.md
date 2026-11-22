---
name: h3-image-prompt-writing
description: Write MiniMax-H3-Image text-to-image prompts as a complete description of the finished image — purpose and deliverable, layout and reading order, subject state, visible style through material and light, and every word that appears quoted in place. Use for posters, infographics, charts and dashboards, product shots, UI screens, characters, scenes, storyboards, grids and multi-panel layouts on H3-Image, and when improving an H3-Image prompt that comes back empty, generic or full of invented lettering.
version: 1.0.0
---

# MiniMax-H3-Image 文生图提示词（H3-image Prompt Writing）

H3-Image 读的是**完成图的完整描述**：这张图是干什么用的、里面有什么、各在哪、长什么样、
以及画面上出现的**每一个字**。本 skill 只做文本侧，不管采样参数与工作流。

## 模型事实（决定写法，不要违背）

- 开放权重，扩散 Transformer 33.1B，BF16；**蒸馏为 6 步、guidance 固定 1**。
- **没有 CFG，因此没有负面提示词**：ComfyUI 模板与官方 API 都不接收 negative。
  **要排除什么，就正面写出来**（例如 `The image contains no text, letters or numbers.`）。
- 原生输出约 16 MP（4096×4096 起），任意宽高，**每条边对齐 32 px**；
  4 MP–20 MP 可用，16 MP 效果最好。分辨率与画幅属于工作流参数，**不写进提示词**。
- 文本编码器为 Qwen3-VL-32B；**提示词按原样读取**（本地部署不走官方 Prompt Expander）。
  所以「扩写」这件事由你完成，不要指望模型替你补全。
- 不支持：遮罩编辑（inpainting mask）、透明背景、预览图。
- 参考图编辑上限 16 张，按顺序在提示词里写成 `<Picture 1>`、`<Picture 2>` …（编辑另有 skill）。

## 何时使用

- 用户要海报 / 信息图 / 图表 / 仪表盘 / 产品图 / UI 界面 / 角色设定 / 场景 / 分镜 / 宫格；
- 已有 H3-Image 提示词，但画面空洞、风格靠形容词堆、或者自己乱加了标题与标签文字；
- 需要把一句中文需求写成能直接粘进 H3-Image 的英文描述；
- 需要判断画幅（3:4 竖版海报 / 16:9 横版 KV / 1:1 方图）并给出对应尺寸建议。

**不适用**：
- 要改 / 合成 / 换风格参考图 → `h3-image-edit-prompt`；
- MiniMax H3 **视频**（分镜、对白、音效）→ `h3-prompt-writing`；
- Anima / MOSS / Krea 2 的写法各自有专属 skill，**不要混用**（H3-Image 不是 tag 流模型）。

## 输出契约（先读这一节）

1. **只输出提示词正文**（英文），再加一行 `Aspect ratio: W:H`；不要开头说明、不要解释、
   不要总结、不要 Markdown 代码块围栏、不要复述规则。
2. 正文是**一段或几段连贯散文**（不是 tag 串、不是 bullet、不是 JSON）。
3. **画面上出现的每个字都要用引号给出完整原文**，并写清位置、层级与换行；
   不要写「一些图标」「一段文案」这种占位。
4. **不要文字时就明说**：`The image contains no text, letters or numbers.`
5. **不写参数**：不写步数、CFG、采样器、种子、模型名、LoRA、分辨率像素值。
6. **不写负面提示词**（模型没有负面分支）；要排除就在正向描述里写出来。
7. 用户给定的实体、名称、数量、公式、数据、风格、媒介、朝向、空间关系**一律保留**，
   只在空缺处补全；**不要编造真实统计、价格、认证或规格**——示例数据要标明是示例。

## 写作顺序（官方四层，别调换）

| 层 | 写什么 | 例子 |
| --- | --- | --- |
| ① 任务与交付物 | 这张图是什么、给谁看、承载什么信息 | `A clean 16:9 sales dashboard on a warm white background…` |
| ② 版式与阅读顺序 | 分区、数量、位置、视角、留白；密集内容先说分区再逐区填 | `The title "Quarterly sales" sits at the upper left. Two summary cards occupy the top row beneath it…` |
| ③ 主体状态与动作 | 谁 / 什么、处于什么状态、正在做什么（单一冻结瞬间） | `She leans slightly forward and looks down at the clay…` |
| ④ 风格与光 | **用可见的颜色、材质、光位、质感写风格**，不用 `premium` / `high-end` | `soft side light, brushed-metal reflections, generous white space` |

**先任务后风格，先版式后细节。** 风格词（cinematic / 高级）不决定画幅，画幅由版面决定。

## 硬规则

### 一、文字与信息

- **逐字加引号**：`the words "HEARTH JAZZ" in bold letters at the top`。
  保留原语言、大小写、标点、数字、拼写与行序；空格按原样，不要换成全角空格。
- **层级要写**：标题 / 副标 / 正文各用多大、什么位置、几行。
- **没有文字就明写**：不加这句，模型会自己补标题、标签和装饰性字母。
- **数据必须精确**：图表给数值、单位、坐标轴刻度、图例、时间范围；
  示例数据写 `illustrative`，**不要**把编造的数字当真实数据。
- **推导结果自己算**：总数、最佳项、百分比由你算出后写进提示词，不要交给模型算。

### 二、版式与几何

- **宫格写行列**：`2 rows and 3 columns` 或 `3×3 (rows × columns)`，
  **不要**写 `2×3`（会被理解成别的意思）；不规则版式直接描述：
  `3 panels on top and 2 below`，指定位写 `row 2, column 1`。
- **区分整体与局部**：整张画布 ≠ 画面里的一块屏幕 / 一个分格；
  轮播页、卡片、幻灯片默认是**各自独立的画布**，除非用户要总览图。
- **AI 生成的版面**：密集内容先命名分区，再逐区填内容，不要一次堆满。

### 三、物理可读性

- 写清**视角**（从哪看、多高、多近）、**接触点**（手在哪、抓着什么、受力方向）、
  **光影方向**（光源位置 → 影子落在哪）。
- 单一冻结瞬间；要序列时，用**可见证据**表现每个事件的结果，不要只写情绪。
- 保持左 / 右、前 / 后、视线方向、地面标记与标签一致，别让构图自我矛盾。

### 四、设计类交付物

- 每个被要求的分区都要有**实际内容**：标题、控件、轴、图例、标签、正文。
- UI 写清控件与选中态；图表写清轴、单位、刻度、图例；科研图写清变量定义与箭头端点。
- 极简设计就保持极简，不要把清单逐条填满。

## 画幅（写进 `Aspect ratio` 行，不写进正文）

比例范围 1:3 – 3:1。用户给了就照用；超出范围时用最近的合法比例并说明；没给就按版面选。

| 版面 | 比例 | 对应 16 MP 尺寸（宽×高，边长 32 的倍数） |
| --- | --- | --- |
| 方形专辑 / 产品 / 图标 | 1:1 | 4096×4096 |
| 竖版海报 / 手机 UI | 3:4 | 3552×4736 |
| 竖版长图 | 9:16 | 3072×5472 |
| 横版 KV / 仪表盘 | 16:9 | 5472×3072 |
| 横版宽幅 | 21:9 | 6272×2688 |
| 4:3 / 3:2 | 4:3 · 3:2 | 4736×3552 · 5024×3360 |

尺寸属于工作流参数，**不要**把像素写进提示词。

## 常见失败与修法

| 症状 | 根因 | 修法 |
| --- | --- | --- |
| 画面自己冒出标题 / 乱码字母 | 没有声明「无文字」 | 加 `The image contains no text, letters or numbers.` |
| 文字拼错、多出副标 | 文字太长 / 没给层级 | 压到 1–3 个词，逐字加引号，写清位置与字号层级 |
| 画面空、没有重点 | 只写了主体，没写版式与光 | 补第 ②④ 层：分区、留白、光源与影子 |
| 风格「很 AI」 | 用了 `premium` / `high-end` 这类空词 | 换成可见材质、颜色、光位、质感 |
| 图表数据乱写 | 没给精确数值与轴 | 给值、单位、刻度、图例；推导结果自己算 |
| 版式糊成一团 | 每个区域都塞满 | 说明哪密哪空，保留留白 |
| 多主体串味 | 没绑定位置与状态 | 每个主体写「位置 + 状态 + 动作 + 与其他主体的关系」 |
| 写了负面词 | 沿用 SD 习惯 | 删掉；模型无负面分支，改成正面表述 |

## 自检清单（交付前逐条过）

- [ ] 开头交代了「这是什么图、给谁看」，而不是先堆形容词；
- [ ] 版式、分区、阅读顺序、留白都写了；
- [ ] 每个出现的字都加引号、位置与层级明确；无文字时写了「无文字」声明；
- [ ] 数值、单位、刻度、图例完整，推导结果是自己算的，示例数据标了 illustrative；
- [ ] 风格由材质 / 颜色 / 光位 / 质感构成，没有 `premium`、`high quality`、`8k`；
- [ ] 没有 tag 串、没有权重语法、没有参数、没有负面词；
- [ ] 画幅在 1:3–3:1 内，且与版面匹配；
- [ ] 没有开头说明、结尾建议、代码块围栏。

## 示例

**输入**：「设计一张 16:9 的季度销售仪表盘，标题 Quarterly sales，
A/B/C 三个产品分别卖了 12、18、9 件，要有柱状图、小表格、总数和最佳产品，简洁，别编额外数据」

**输出**：

```text
A clean 16:9 sales dashboard on a warm white background uses a restrained charcoal-and-teal palette, crisp sans-serif typography, and a consistent alignment grid. The title "Quarterly sales" sits at the upper left. Two compact summary cards occupy the top row beneath it: "Total units" with the value "39", and "Best-performing product" with "B — 18 units". These values summarize the supplied three-product dataset.

The lower left contains a large vertical bar chart. Its horizontal axis is labeled "Product", with categories "A", "B", and "C" in that order; its vertical axis is labeled "Units" and has evenly spaced ticks at 0, 5, 10, 15, and 20. All bars share the same zero baseline and equal widths. Their heights correspond exactly to 12, 18, and 9, and each value is printed clearly above its bar. Product B is teal; A and C use the same muted gray. Thin horizontal gridlines make the scale readable without competing with the data.

At the lower right, a compact table has the column headings "Product" and "Units", followed by the rows "A | 12", "B | 18", and "C | 9". Its B row carries a subtle teal accent matching the highlighted bar. Balanced spacing separates the summary cards, chart, and table. There are no invented dates, forecasts, percentage changes, or additional data series.
```

`Aspect ratio: 16:9`

**输入**：「一张陶艺工作坊的照片，女陶艺师在拉坯，从她左侧拍，突出手和泥，不要文字」

输出要点（完整描述，不是短句）：视角 `viewed from her left side at approximately hand level`；
构图包含侧脸、肩、前臂、双手与整只碗；冻结在「左手托外壁、右手指尖修内壁」的一瞬；
湿泥、同心纹、侧窗自然光、腕下淡影；结尾 `No lettering or additional people appear.`

## 边界

- **不执行**脚本、不调 API、不生成图片；只产出文本（需要出图由工作流或 API 负责）。
- 不编造真实统计、价格、认证、规格；不替代用户做版权与合规判断。
- 不输出参数建议（步数固定 6、CFG 固定 1，问就说由工作流决定）。
- 不处理参考图编辑（交给 `h3-image-edit-prompt`）。
