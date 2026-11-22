# MiniMax-H3-Image 官方提示词规则（原文与出处）

本文件是 `h3-image-prompt-writing` / `h3-image-edit-prompt` 的参考资料，收录：

- 官方 skill `h3-image-prompt-writing`（<https://github.com/MiniMax-AI/MiniMax-H3-Image>）
- 官方文生图指南 `references/t2i-en.txt`、编辑指南 `references/edit-en.txt`
- 官方 README 的 **Prompting Tips** 与 **Sizes / Request Parameters**
- 平台 API 文档 `platform.minimax.io/docs/guides/image-generation.md`
- ComfyUI 教程 `docs.comfy.org/tutorials/image/minimax/minimax-h3-image`

引号内为官方原文（英文），破折号后为中文落地。

## 一、模型与推理事实（写提示词前必须知道）

| 项 | 事实 | 对提示词的影响 |
| --- | --- | --- |
| 架构 | 33.1B 扩散 Transformer，BF16，蒸馏 6 步 | 不写步数、不写 CFG |
| 引导 | `guidance_scale` 固定 1，**没有 CFG** | **不存在负面提示词**；官方 API 与本地服务都会**拒绝** `negative_prompt` |
| 尺寸 | 原生约 16 MP；4–20 MP 可用；边长 32 的倍数 | 分辨率属于工作流参数，不写进正文 |
| 提示词长度 | ≤ 32000 字符；关闭增强时只有前约 4096 token 生效 | 长文可以，但别指望超长尾部生效 |
| 文本编码器 | Qwen3-VL-32B | 自然语言描述，不是 tag 流 |
| 提示词增强 | 官方 API 默认开（H3-Image-Context-IR）；ComfyUI T2I 模板默认关 | 本地部署**按原样读**，扩写由你完成 |
| 参考图 | 编辑 1–16 张，`<Picture 1>`…；不支持遮罩编辑、透明背景 | 编辑走 edit 指南 |
| 变体 | `MiniMax-H3-Image` / `MiniMax-H3-Image-Highspeed`（参数与限制相同） | 不影响提示词写法 |

## 二、官方 Prompting Tips（README 原文）

```text
- Task before style, layout before details. Say what the image is for and what is in it, then the
  layout, then the style through visible color, material and light instead of words like "premium".
- Quote every word to show, with its position and line breaks. Write "no text, letters or numbers in
  the image" when you want none.
- Give exact data for charts and educational images, with units and time ranges, and mark example
  data as such.
- Give each reference image a role, and say what changes and what stays: "Change the cup on the left
  to blue, keeping its shape, material, position and size."
- Write grids as rows and columns, such as "2 rows and 3 columns", not "2×3".
```

中文落地：

1. **先任务后风格，先版式后细节**——先说是干什么用的、有什么，再说版面，最后用可见的
   颜色 / 材质 / 光写风格，不要用 `premium` 这类空词。
2. **每个要显示的字都加引号**，并写位置与换行；不要文字时明确写「图里没有文字、字母或数字」。
3. **图表与科普图给精确数据**（数值、单位、时间范围），示例数据要标明是示例。
4. **每张参考图都要有角色**，并说清「什么变了、什么不变」。
5. **宫格写行列**（`2 rows and 3 columns`），不要写 `2×3`。

## 三、官方 t2i 指南的结构（节选与转述）

官方 `references/t2i-en.txt` 把写作分成四节，可直接当检查表用：

### 1. Develop the brief into an image（把需求变成画面）

- 选一个清晰的视觉焦点，围绕它构建**完成品**（场景或设计物），不要写成「给另一个作者
  的指令」或「几种方案列表」。
- 用户指定的实体、名称、数量、公式、数据、风格、媒介、朝向、空间关系都是**约束**，
  有意义的限定词与排除项要保留；**具名系统 / 产品要与泛称区分**。
- 补充细节要有目的：可读的互动、可信的材质、纵深、光、信息层级。
  **抽象艺术不必写实，极简 logo 不必加风景。**
- 具体的视觉选择 > 空泛质量词、隐藏背景故事、额外的主角。

### 2. Set the composition（定构图）

- 尊重明确的画布尺寸、朝向、分格与阅读顺序；**区分整张图与画面里的对象 / 屏幕 / 分格**。
- 宫格写清行数与列数；**行列数不决定画布比例**。
- 轮播页、卡片、幻灯片默认是独立画布，除非用户要总览或连续构图。
- 几何未指定时按交付物选：紧凑主体保持紧凑、对比需要并排、层叠信息需要竖向空间。
  **`cinematic` 这类风格词不决定画布。**

### 3. Make scenes physically readable（让场景读得懂）

- 写主体的**可见状态 / 动作、视角、场景、有意义的光**；默认单一冻结瞬间。
- 序列任务要用**可见证据**表现每个事件与结果，不能只靠情绪。
- 保持拓扑与左右、前后、视线、运动方向一致；相机相对的身体朝向、可见体面、手、
  支撑点与接触必须自洽。
- 不要为了迁就姿势而镜像版面或移动目标；球场、棋盘、路径、楼梯、房间的结构除非要求
  否则保持原样，必需的场地标记与标签要可见。

### 4. Complete designed artifacts（设计类交付物要写完）

- 按阅读顺序建立信息层级；**每个被要求的分区都要有实际内容**——
  标题、图示、控件、标签或文案。`some icons` / `a paragraph of copy` 不算完成。
- 用户让你写文案时，**直接写出实际措辞**（用户语言，或需求指定语言）。
- 图表：轴、单位、刻度、图例齐全；**数据标记要与给定数值一致**；
  可推导结果（总数、最佳项）由你算好，不要委派给模型。
- 对比视图（平面 / 渲染、正面 / 背面）共用同一套物体与关系。
- 虚构设计可以自拟内容，但**不要把编造的真实统计、价格、认证、规格当成事实**。

## 四、官方 edit 指南的写作顺序（编辑专用）

官方 `references/edit-en.txt` 要求写成**一段连续纯文本**，顺序固定：

```text
源定义（<Picture N> → <Subject N>） → 目标总述与各源的关系 → 变化与新增的细节
```

- **不要输出这些小标题**，它们只是组织写作用的。
- **叙述最终状态**（`The former location is filled by continuous tabletop.`），
  不要写编辑命令。
- 关系四种写法：
  - 完全保留：单独一句 `<Subject N> is fully preserved.`
  - 部分保留：说明保留哪些类别、改动什么；
  - 属性迁移：`<Subject 2> supplies the exact body color transferred to <Subject 1>.`
  - 弱参考：`<Subject 2> serves as a weak style reference…`
- 移动、旋转、复制、重新打光、遮挡都算**改动**；「完全保留的父项里不能有被编辑的子项」。
- 文字改动要给**完整的结果行**，不是只给替换词；翻译要给实际译文，原文保留在定义里。

## 五、API / ComfyUI 参数（不进提示词）

| 参数 | 值 | 说明 |
| --- | --- | --- |
| `num_inference_steps` | 省略或 6 | 其它值返回 400 |
| `guidance_scale` | 省略或 1 | 其它值返回 400 |
| `negative_prompt` | **不支持** | 会被拒绝 |
| `size` | `WIDTHxHEIGHT`，边长 32 倍数，面积 655360–20000000，比例 1:3–3:1 | ComfyUI 本地 |
| `aspect_ratio` + `area` | `1K` / `2K` / `4K` | 官方 API；与 `size` 二选一 |
| `min_generation_area` | 默认 4194304（2048×2048），传 1024 关闭 | 小尺寸会被放大再缩回 |

16 MP 常用尺寸：

| 比例 | 尺寸 |
| --- | --- |
| 1:1 | 4096×4096 |
| 4:3 / 3:4 | 4736×3552 / 3552×4736 |
| 3:2 / 2:3 | 5024×3360 / 3360×5024 |
| 16:9 / 9:16 | 5472×3072 / 3072×5472 |
| 21:9 | 6272×2688 |

## 六、出处与许可

- 官方仓库：<https://github.com/MiniMax-AI/MiniMax-H3-Image>（`skills/h3-image-prompt-writing`、
  `README.md` 的 Prompting Tips / Sizes / Request Parameters）。
- 官方模型卡：<https://huggingface.co/MiniMaxAI/MiniMax-H3-Image>；提示词扩展器：
  <https://huggingface.co/MiniMaxAI/MiniMax-H3-Image-PE>（Qwen3.8-27B FP4 微调）。
- 平台文档：<https://platform.minimax.io/docs/guides/image-generation.md>、
  <https://platform.minimax.io/docs/api-reference/image-generation-h3-context-ir.md>。
- ComfyUI 教程：<https://docs.comfy.org/tutorials/image/minimax/minimax-h3-image>。
- 许可证：MiniMax-H3-Image Community License Agreement（见官方仓库 `LICENSE`）。
  本文件只摘录**写作规则条文**，不复制官方图片资源与示例图。
