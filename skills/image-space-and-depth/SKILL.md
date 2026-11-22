---
name: image-space-and-depth
description: Give an image prompt real depth - three separable depth bands, foreground framing, overlap and occlusion, scale cues, atmospheric perspective, and deliberate choice of what stays sharp versus what dissolves - so a render stops reading as flat cut-outs pasted on a backdrop. Use when a scene looks flat or cardboard-like, when foreground, subject and background sit at the same distance, when a landscape needs distance, or when the user asks for depth of field, bokeh, aerial perspective or a layered composition. Model-agnostic: the same words work as tags or natural language.
version: 1.0.0
---

# 空间与虚实（Space & Depth）

「平」通常不是画得不好，而是**画面里只有一层**：所有东西都在同一个距离上，
没有前景压边、没有遮挡、没有空气衰减，也没有清晰与模糊的差别。

本 skill 只管**空间结构**：景深分层、前景装置、遮挡关系、尺度参照、大气透视、虚实分配。
不碰景别与机位选择（→ `image-composition`）、不碰光位（→ `image-light-and-value`）。

## 何时使用

- 画面像**纸片贴在背景上**，没有纵深；
- 前景 / 主体 / 背景**在同一个距离**；
- 风景**没有远近**，远山和近树一样清楚；
- 需要**浅景深 / 散景**，或者需要**全景深**；
- 场景缺**尺度参照**（看不出多大）；
- 想要「层」的节奏：压边 → 主体 → 中景 → 远景 → 天光。

## 输出契约

- **只输出提示词正文 / 空间方案**；要方案时用短条目：`前景 / 中景 / 远景 / 虚实 / 空气` 各一行；
- 默认只出正面提示词；用户明确要负面词时才追加两段式；
- 不写参数；不写 `depth of field` 这种没有对象的空词（要写「什么清晰、什么糊」）；
- 用户已指定的机位或景别不覆盖，只补分层与虚实。

## 五层深度（缺层就会平）

| 层 | 作用 | 写法要点 |
| --- | --- | --- |
| **压边前景** | 制造纵深、构图框 | `out-of-focus foreground`, `a blurred railing cutting the lower left corner` |
| **主体层** | 视觉焦点 | 最清晰、对比最强 |
| **中景** | 交代环境、承接主体 | 细节递减，仍有结构 |
| **远景** | 空间延伸 | 只留轮廓与色块 |
| **天光 / 空气** | 统一整张图 | 雾、尘、雨、水汽、体积光 |

**四层以上同时清晰 = 又平又乱**。必须至少让一层明显模糊或压暗。

## 制造纵深的六个手段

1. **遮挡（overlap）**：前景挡住主体的一部分，是最强的深度线索；
2. **尺度递减**：同类物在远处变小（`a row of identical lamps receding`）；
3. **大气透视**：远处对比降低、饱和降低、偏冷/偏亮（`the far ridges fade into pale haze`）；
4. **虚实差**：近实远虚，或刻意反过来（主体之外全虚）；
5. **光的分层**：前景暗、主体亮、远景灰（或反过来）；
6. **引导线**：路径、栏杆、轨道把视线从前景带到远处。

## 虚实：先定焦点，再定光圈

- **浅景深**：`only the eyes and lashes are in focus, the ear and the street behind already softening`；
- **深景深**：`everything from the near railing to the far ridge stays sharp`；
- **选择性虚化**（最有效）：`the subject stays razor-sharp while every other plane drops into soft blur`。

**不要把 `bokeh` 当装饰**：写清「什么变成了光斑、光斑来自什么光源」。

## 尺度参照（让画面「有大小」）

- 人物：`a figure small enough to be half the height of one column`；
- 常见物：`a hand for scale`、`waist-high`、`two-storey`；
- 重复单元：`a grid of identical windows`；
- 不要用 `huge` / `massive` 这类空词代替参照物。

## 常见失败与修法

| 症状 | 根因 | 修法 |
| --- | --- | --- |
| 像纸片贴背景 | 没有遮挡与前景 | 加一层压边前景并让它挡住主体一角 |
| 远近一样清楚 | 缺大气透视与虚实差 | 远景降对比降饱和；主体外全虚 |
| 空间扁平但细节很多 | 每层都塞满细节 | 执行「一层清晰，其余递减」 |
| 看不出多大 | 没有尺度参照 | 加人物 / 手 / 重复单元作参照 |
| `bokeh` 没效果 | 没写光源与被虚化物 | 写「远处车灯化成暖色光斑」 |
| 前景抢戏 | 前景太亮太清晰 | 前景压暗、降饱和、加模糊 |

## 自检清单

- [ ] 至少有压边前景 / 中景 / 远景三层；
- [ ] 有一处明确的遮挡关系；
- [ ] 远景做了大气透视（降对比 / 降饱和 / 偏色）；
- [ ] 焦点明确：只写了「什么清晰、什么糊」；
- [ ] 有尺度参照物；
- [ ] 前景被压暗或虚化，没有抢主体；
- [ ] 没有 `depth of field` / `3d` / `epic` 这类空词；
- [ ] 没有参数与多余解释。

## 示例

**输入**：「山谷里的一座小寺庙，要很大很远的感觉」

```text
A wide view from a ridge opposite a deep valley. In the near foreground, out-of-focus pine
branches cut across the lower left corner and stay almost black, framing the scene without
competing with it. Below them, the middle distance holds a single small temple roof set on a
rock shelf, its pale plaster and dark tiles the sharpest and highest-contrast elements in the
frame; the winding stone stair that reaches it is still legible but loses fine detail. Beyond,
layered ridges recede in three progressively paler bands, each lower in contrast and shifted
toward cold blue-grey, until the farthest ridge dissolves into haze. A pair of birds, each no
bigger than a comma at this scale, crosses the brightest part of the sky. The temple roof is
about a tenth the width of the frame, which is what makes the valley read as large.
```

## 依据

- 深度线索（遮挡 / 尺度递减 / 大气透视 / 虚实 / 引导线 / 光的分层）：摄影与绘画通用的深度线索
  清单，Canon《Creating the Illusion of Space and Depth》与经典摄影教材。
- 「先分受光面与背光面，再按离光源远近划分亮度」的大层次做法：中文摄影教学《如何科学划分画面
  明暗层次》。
- 三层景深（前 / 中 / 后）作为版式与叙事分层：常见绘本与影视构图教材。

## 边界

- 不执行脚本、不生成图片、不调 API。
- 不写参数（光圈 / 焦距数值属工作流，仅可写可见结果）。
- 不规定模型语法。
- 不复制具体作品构图。