---
name: krea2-anime-keyvisual
description: Build Krea 2 anime key visuals, posters and manga panels — one readable focal hierarchy, a typographic zone reserved for the title, in-panel speech bubbles and SFX handled as quoted text, and manga panel grids written as rows and columns. Covers the sketch-to-panel workflow (rough sketch as a reference, then a tight prompt for the finished look) and the anime poster layout that keeps the character readable at thumbnail size. Use for 二次元 主视觉 / 海报 / 封面 / 漫画分镜 / 关键帧 on Krea 2.
version: 1.0.0
---

# Krea 2 二次元主视觉与分镜（Anime Key Visual）

一张二次元主视觉要同时成立三件事：**构图能一眼读懂**、**角色在缩略图下仍可辨识**、
**文字有地方放**。漫画分镜还要多一件：**格与格的阅读顺序**。

本 skill 管这三/四件事，不管画风锁定（→ `krea2-anime-style`）与角色一致性（→ `krea2-anime-character`）。

## 何时使用

- 二次元**主视觉 / 海报 / 封面 / 活动 KV / 游戏 key art**；
- **漫画分镜 / 四格 / 单页**，需要格位与阅读顺序；
- **草图 → 成图**：用户给了一张随手草图或线稿，要出成品；
- 角色单图很好看，但**做成海报就散了**。

## 输出契约

1. **只输出 caption 正文**（英文），不要解释、不要标题、不要代码块围栏；
2. 画内文字**逐字加引号**并写位置、层级、材质；不出现文字时**明说无文字**；
3. **不写**分辨率、步数、CFG、LoRA 权重、`masterpiece` / `score_9` / `8k`；
4. 分镜必须写成 **rows and columns** 并按阅读顺序逐格给内容；
5. 用户的标题文案**一字不改**；让你写文案时当场写出实际措辞。

## 一、主视觉的焦点层级

一张 KV 的失败通常是「什么都重要」。按三层写死：

| 层 | 占画面 | 写什么 |
| --- | --- | --- |
| 第一眼 | 30–50% | 角色（脸 / 上半身）+ 最强的明度对比 |
| 第二眼 | 20–30% | 一个叙事道具或动作结果（剑、花、翻起的水、飞散的书页） |
| 第三眼 | 其余 | 环境与光，**压饱和、压细节** |

**缩略图测试**：把画面缩到 200px，如果第一眼不是角色的脸或轮廓，构图就错了。

## 二、留出文字区（typographic zone）

海报一定要**先留位置再画内容**：

- 竖版：上方 1/4 或下方 1/4 留一块**低细节区**（天空 / 纯色 / 虚化），标题放这里；
- 横版：左侧或右侧留 1/3 竖条；
- 角色**不要**压在这块区域上，否则标题必然糊。

写法：`the top quarter stays open as a low-detail sky band, reserved for a title`。

## 三、画内文字

- 逐字加引号：`the title "雨夜集市"`；
- 给位置 + 层级 + 字体气质 + 材质：`set in heavy brush-style 楷体, warm off-white ink, centered`；
- 主标控制在：中文 2–6 字 / 英文 1–3 词（超出容易漏字）；
- **没有文字时**：`No text, lettering, or speech bubbles appear anywhere in the frame.`

## 四、漫画分镜

格位必须写成行列，并**逐格**给内容与阅读顺序：

```text
A manga page in 3 rows and 2 columns, read right to left, top to bottom.
Row 1, column 2 (first panel): a wide establishing shot of the rooftop at dusk.
Row 1, column 1: a medium shot of the girl turning her head toward the stairs.
Row 2, column 2: an extreme close-up of her hand tightening on the railing.
Row 2, column 1: a small panel of the empty stairwell, seen from above.
Row 3, column 2: a large panel spanning both columns, her silhouette against the sky.
Each panel has a thin black border with consistent gutter width.
```

要点：

- **阅读方向要写**（`read right to left` 是日漫默认，但必须显式写）；
- **跨格**要写（`a large panel spanning both columns`），不要指望模型自己合；
- **格线宽与间距统一**（`consistent gutter width`），否则像拼贴；
- **对话气泡**：写成 `a speech bubble in the upper left of the panel reading "…"`，
  文本逐字给；气泡**不要**压在脸上；
- **拟声词**按画面文字处理（加引号 + 位置 + 粗体感）。

## 五、草图 → 成图

官方推荐流程（Krea 2 的草图转成品）：

1. **画粗草图**：构图、姿态、取景，不用干净；
2. **把草图当参考图**上传（最多 4 张风格参考）；
3. **写一条紧的提示词**写成品样貌：角色、光、氛围、画风；
4. 不要用提示词去「描述草图本身」，而是描述**成品**。

只有文本框时，等价做法是：把草图里的**构图信息写死**
（谁在哪、多大、朝哪、遮住什么），不要写「一个草图的场景」这类描述。

## 六、常见失败与修法

| 症状 | 根因 | 修法 |
| --- | --- | --- |
| 缩略图看不出主角 | 焦点层级没写 | 指定第一眼占比与最强对比 |
| 标题糊在角色上 | 没留文字区 | 先留低细节带，再放角色 |
| 分镜阅读顺序乱 | 没写方向 | 显式写 `read right to left, top to bottom` |
| 格子大小一样像九宫格 | 没指定跨格 | 写一格跨两列做视觉重音 |
| 对话气泡挡脸 | 气泡位置没写 | 指定气泡在格内空白处 |
| 多出没要的文字 | 没排除 | 收束句 `no other text appears` |
| 画风散了 | 缺画风锚句 | 叠加 `krea2-anime-style` 的一句锚句 |

## 自检清单

- [ ] 焦点层级三层明确，缩略图能认出主角；
- [ ] 有留白 / 低细节带放标题；
- [ ] 文字逐字加引号并给位置层级，或明说无文字；
- [ ] 分镜写成行列 + 阅读方向 + 跨格 + 统一格距；
- [ ] 气泡与拟声词都有位置与逐字文本；
- [ ] 只有一句画风锚句（来自 `krea2-anime-style`）；
- [ ] 没有参数、没有 `masterpiece` / `score_9`、没有代码围栏与解释。

## 示例

**输入**：「一张竖版二次元活动主视觉，标题『星屑观测』，一个女生在天文台穹顶下抬头」

```text
A vertical anime key visual: a girl in a navy duffel coat stands small in the lower third of
the frame, looking up into the open dome of a small observatory, her face lit from above by a
single cold beam; she is the first thing the eye lands on because she is the only high-contrast
shape against the deep blue interior. In the middle distance the telescope's matte white tube
cuts a diagonal across the dome's ribs, and a scatter of star charts and a tipped mug sit on the
desk beside her, catching a warm desk-lamp pool as the second read. The upper quarter stays open
as a low-detail band of dark blue dome interior, reserved for the title. The title "星屑观测"
is set there in thin widely tracked serif characters, pale silver ink, at about one tenth of the
poster height, with a single small line "STARDUST OBSERVATION" directly beneath at a third of
that size. One cel-animation style anchor holds the whole frame: clean closed outlines, flat cel
shading with hard shadow edges, and a palette of deep indigo, cold silver and one warm amber.
No other text appears anywhere on the poster.
```

## 边界

- 不执行脚本、不生成图片、不调 API。
- 不保证文字一次成型：密集文字建议多出几张挑选（模型特性）。
- 分镜只做**提示词级**的格位设计，不替代分镜表排版工具。
- 不复制任何真实作品的画面构图或标题文案。