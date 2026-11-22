---
name: z-image-bilingual-text
description: Compose Z-Image / 造相 prompts whose main subject is the lettering itself — Chinese and English posters, signage, packaging, book covers, menus, labels, bilingual layouts and typographic art — using the model's strong bilingual text rendering. Use when a Z-Image image must show exact wording, when the user wants 中文/English text baked into the image, when previous attempts produced garbled or missing characters, or when a design needs multi-line copy, hierarchy and layout rather than one caption.
version: 1.0.0
---

# Z-Image 双语文字与版式（Bilingual Text & Typography）

Z-Image 的核心卖点之一是**准确渲染复杂的中英文文字**。但「能渲染」不等于「随便写都能对」：
字数、层级、位置、字体气质、语言混排的写法和普通画面描述完全不同。

## 何时使用

- 海报、招牌、包装、书封、菜单、标签、票券、UI 截图中**文字是主体**；
- 需要**中英双语**同屏（对照、副标、双语标语）；
- 之前出图时中文缺笔画 / 变成乱码 / 英文拼错 / 文字整体消失；
- 需要多行文案、主副标题层级、左右分栏等**版式**，而不是一句话 caption。

**不适用**：只需要一句短文字做点缀 → `z-image-prompt-writing` 就够；
参考图编辑改字 → 用编辑流程（Z-Image-Edit），本 skill 只管文生图的文字与版式。

## 变体前提

| 变体 | 文字渲染表现 | 建议 |
| --- | --- | --- |
| **Z-Image-Turbo** | 最强的文字表现，8 步出图 | **首选**；密集文字建议多出几张挑最好的 |
| **Z-Image**（Base） | 文字能力好，但多样性会把版式也变掉 | 需要严格版式时用 Turbo；Base 上把版式写得更死 |
| Omni-Base / Edit | 编辑场景改字 | 见编辑流程 |

**注意**：Z-Image 没有「文字模式开关」，全靠提示词写清楚。

## 输出契约

1. **只输出提示词正文**（英文描述 + 画面内中文/英文原文），不要解释、不要代码块围栏、
   不要开头结尾客套。
2. **画面里的字逐字给全**，加引号，**保留原语言**（中文就是中文，不是拼音也不是翻译）。
3. 明确写出**位置、层级、对齐方式、行数**；不写「一些文字」「一段文案」这类占位。
4. **不要文字时明说**：`There is no text, lettering, or signage anywhere in the frame.`
5. 不写参数（步数 / CFG / 采样器 / 分辨率）。
6. 用户给了文案就**一字不改**；让你写文案时，**当场写出实际措辞**，不要留空。

## 文字层写法（五件事，缺一不可）

| 要素 | 要求 | 例 |
| --- | --- | --- |
| ① 内容 | 逐字加引号，原语言，原标点 | `the characters "老王面馆"` |
| ② 位置 | 具体到画面区域 / 相对物件 | `centered across the top fifth, above the doorway` |
| ③ 层级 | 主标 / 副标 / 正文的大小关系 | `the main title twice the height of the subtitle` |
| ④ 字体气质 | 不用字体名，用可见特征 | `heavy serif with tight spacing` / `毛笔楷体，笔画有飞白` |
| ⑤ 材质 / 呈现 | 印在什么上、怎么呈现 | `red lacquer on weathered wood` / `embossed foil on matte card` |

**字数纪律**（实测经验，按可靠性排序）：

- 中文主标 **2–6 字**最稳；8 字以上要拆成主标 + 副标；
- 英文主标 **1–3 个词**；一行超过 4 个词容易漏字母；
- 总文字量控制在 **12–20 个字符**内最可靠；再多的内容请分层，并接受需要多抽几次。

## 中英混排的三条规则

1. **主语言先定**：谁是主标题（中文或英文），谁是副标。不要两种语言同字号并排争主位。
2. **各自成行**：中文一行、英文一行，中间用分隔线或留白，不要在同一行里中英夹杂。
3. **翻译要一致**：双语对照时给出**完整对应**（中文标题 ↔ 英文标题），不要让模型自己翻——
   模型不会替你保证译法一致。

## 版式骨架（海报类的默认写法）

```text
① 媒介与用途：什么类型的版面（A2 poster / packaging label / book cover）
② 画幅倾向：竖版 / 方版 / 横版（只描述版面结构，不写像素）
③ 分区：上中下 / 左中右各放什么，比例大致多少
④ 主标：文字 + 位置 + 层级 + 字体气质 + 材质
⑤ 副标 / 正文：同上，若不需要就明说「只有主标，没有其他文字」
⑥ 图像元素：图与字的关系（图在上、字压图、字留白区）
⑦ 色彩与材质：底色、油墨、纸张/金属/织物
⑧ 收束：一条硬约束（例如「除上述文字外，画面中没有其他文字」）
```

## 常见失败与修法

| 症状 | 根因 | 修法 |
| --- | --- | --- |
| 中文缺笔画 / 变成形近字 | 字数太多或太生僻 | 拆短、换常用字、把主标压到 2–6 字 |
| 文字整体消失 | 提示词里没给位置或材质 | 补「印在什么上、在画面哪个区域」 |
| 英文漏字母 / 拼错 | 一行词太多 | 压到 1–3 个词，逐字加引号 |
| 多出没要的文字 | 没声明「没有其他文字」 | 收束句写死：`no other text appears in the frame` |
| 中英挤在一行互相干扰 | 混排没分行 | 明确中文一行、英文一行 |
| 版式每次都不一样 | 用了 Base（多样性高） | 换 Turbo；或把分区比例写得更死 |
| 字体气质不像 | 写了字体名（`思源黑体`） | 改写成可见特征（笔画粗细、衬线、字距、倾斜） |

## 自检清单

- [ ] 每段文字的**原文**都在提示词里逐字出现，并加了引号；
- [ ] 中文字是中文、英文是英文，没有拼音或音译替代；
- [ ] 每段文字都有位置、层级、字体气质、材质四要素；
- [ ] 主标字数在可靠区间（中文 2–6 字 / 英文 1–3 词）；
- [ ] 双语时各自成行、各有明确主次；
- [ ] 结尾声明了「除上述文字外没有其他文字」（或明确说明还有哪些）；
- [ ] 没有参数、没有 tag 串、没有 `masterpiece` / `8k`；
- [ ] 没有开头说明、结尾建议、代码块围栏。

## 示例

**输入**：「一张 A2 竖版海报，主题是『雨夜集市』，下面一行英文 RAIN NIGHT MARKET，
底部小字 11.22 20:00，深蓝底色，霓虹感」

**输出**：

```text
A vertical A2 poster for a night market, printed on matte uncoated stock with a deep indigo base
tone. The upper two thirds carry a photographic image of a rainy alley market: warm lantern light
blurring into red and amber bokeh, wet pavement reflecting the stalls, a few blurred figures under
umbrellas. The lower third is a calm indigo field reserved for type. Centered there, the Chinese
title "雨夜集市" is set in a heavy brush-style 楷体 with visible dry-brush edges, rendered in warm
off-white ink and sized at roughly one eighth of the poster height; directly beneath it, the
English line "RAIN NIGHT MARKET" appears in a thin wide-tracked sans-serif at about a quarter of
the title's height. At the bottom edge, aligned left with a 40 mm margin, the small line "11.22
20:00" is set in the same thin sans-serif, half the size of the English line. A single thin
horizontal rule separates the image from the type field. No other text, logos, or labels appear
anywhere on the poster.
```

## 边界

- **不执行**脚本、不调 API、不生成图片。
- 不编造真实品牌名、认证、价格；示例数据要标明是示例。
- 不保证一次成功：密集文字建议同提示词多出几张挑选，这是模型特性，不是提示词错误。
- 不负责遮罩改字（需要编辑流程）。

## 参考

需要字表、双语对照模板与更多版式时读
`references/z-image-text-layouts.md`。
