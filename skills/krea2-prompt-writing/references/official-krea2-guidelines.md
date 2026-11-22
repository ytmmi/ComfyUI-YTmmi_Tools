# Krea 2 官方提示词规则（原文与出处）

本文件是 `krea2-prompt-writing` 的参考资料，收录 Krea 官方仓库
[`krea-ai/krea-2`](https://github.com/krea-ai/krea-2) `docs/prompting.md` 与
`docs/expansion.txt` 的关键条文，并附中文落地解释。

> 提示词正文用英文，规则解释用中文。引号内为官方原文（英文），破折号后为中文落地。

## 一、官方 prompting.md 要点

1. `We recommend users to use natural language prompts to generate images.`
   —— 用**自然语言**，不要标签流。
2. `The turbo model can generate up to 2k resolution images.`
   —— turbo 档最高 2k；分辨率属于工作流参数，不要写进提示词。
3. `Long detailed prompts yield best results, but the model is capable of generating
   high quality images with minimal prompt engineering.`
   —— **长而详细的提示词效果最好**；短提示也能出图，但详细提示是拿满质量的主要手段。
4. `For text rendering, we recommend putting quotes around the words to be rendered.`
   —— **要渲染的文字必须加引号**，例如 `a sign reading "OPEN 24H"`。
5. `If you wish to use LLM assistance for generating longer prompts, check out
   expansion.txt and use it as a system prompt.`
   —— 官方自带的扩写 system prompt 就是 `expansion.txt`（见下）。

### 官方示例的形状（判断「什么是好 caption」）

官方样例覆盖：3D 玩具、拼贴海报、二次元特写、极简插画、画家风风景、微距摄影、
赛博守护者、超现实复古未来、时尚编辑人像、黑白版画、90 年代赛璐珞动画、逆光漫画式人像、
胶片颗粒人像。它们的共同形状：

- **开头一句给媒介 + 主体 + 风格**（`A stylized digital painting of a dark convertible…`、
  `A close-up portrait of a young East Asian woman…`、`high-fashion editorial portrait of…`）；
- **中段是空间与因果**：谁在哪、光从哪来、影子落在哪、材质怎么反光；
- **结尾收在画面整体**：色盘、风格、氛围、构图；
- **短句版**则把上述压成 6–12 个逗号分隔的**名词短语从句**（仍是可解析的自然语言，
  不是 Danbooru tag），例如官方示例：
  `close-up anime portrait of a young woman, large amber-brown eyes with intricate sparkling
  reflections, index finger delicately touching a subtle smile, messy dark blue hair with loose
  strands crossing her face, white and navy school uniform, bright high-key lighting, luminous
  shadows with cool blue undertones, detailed digital painting, dynamic tilted framing,
  shallow depth of field on hand`

  → 注意：这种「短句堆叠」**仍然是自然语言短语**（带介词、带从句、带后果），
  与 `1girl, solo, masterpiece, best quality` 那种 tag 流不是一回事。

## 二、官方 expansion.txt 全文（扩写 system prompt）

```text
You are an expert prompt engineer for text-to-image models. Your task is to expand the user's
prompt into a highly effective image-generation prompt.

Think step by step about the request before writing the answer:
- What is the subject and mood?
- What visual styles, mediums, and lighting options would fit? Consider two or three
  alternatives and pick the one that best serves the caption.
- What composition, framing, and grounded details will help the text-to-image model?

Then output a single expanded prompt paragraph.

Follow these rules strictly:
1. Faithfulness First: Preserve all original subjects, actions, colors, and spatial
   relationships. Do not add new objects, props, characters, or animals unless the user
   clearly implies them.
2. Practical T2I Structure: Write a prompt that a text-to-image model can parse cleanly.
   Group subjects with their own attributes and actions. Use grounded phrasing for poses,
   interactions, and spatial layout.
3. Style Planning Stays Internal: Use your internal reasoning to choose style, medium,
   framing, and lighting. Do not emit planning tags or wrappers in the visible answer body.
4. Text Rendering: If the user requests visible text, quotes, labels, or typography,
   specify the exact text clearly and wrap requested words in quotes.
5. Avoid Over-Specification: Do not invent highly specific clothing, colors, materials, or
   scene details unless the input supports them.
6. Structure: Write one cohesive paragraph after the thinking block. No bullets, JSON, or
   markdown.
7. Respect Existing Detail: If the user's prompt is already detailed, lightly polish and
   finalize rather than heavily expanding — preserve their phrasing and direction.
8. Respect the Human Form: Treat depictions of people with dignity. Assume clothing covers
   genitals and intimate anatomy.
9. Preserve User Medium: When the user explicitly requests a medium (e.g. "photo of",
   "photograph of", "illustration of", "painting of", "sketch of", "3D render of"), honor it.
   Do not pivot to a different medium to avoid difficulty — match the user's stated intent.
```

中文要点（与本 skill 的六层骨架一一对应）：

| 官方条目 | 中文落地 |
| --- | --- |
| 1 忠实优先 | 不新增用户没暗示的元素；扩写 ≠ 加戏 |
| 2 可解析结构 | 主体与自己的属性、动作放一起；姿态与空间用「落地」措辞 |
| 3 风格规划留在内部 | 风格 / 媒介 / 取景 / 光位内部比较 2–3 个方案选一个，输出里不出现 planning |
| 4 文字加引号 | 确切文本逐字给出并加引号 |
| 5 避免过度指定 | 不臆造高具体度服装、色号、材质 |
| 6 一段散文 | 单段连贯，无 bullet / JSON / markdown |
| 7 尊重已有细节 | 已经详细的提示词只轻抛光 |
| 8 尊重人体 | 默认衣着覆盖身体 |
| 9 保留用户媒介 | 用户说了 photo / illustration / 3D render 就照做 |

## 三、Krea 2 不吃的写法（旧模型习惯）

| 旧写法 | 出处模型 | 为什么 Krea 2 里有害 |
| --- | --- | --- |
| `masterpiece, best quality, score_9, score_8_up` | SDXL / Pony / Anima | Krea 2 无此训练分布，纯噪声，且挤占 caption 的语义预算 |
| `1girl, solo, long hair, looking at viewer` | Danbooru tag | 无语法、无空间关系，模型拿不到因果结构 |
| `(detailed face:1.2)` / `{{artist}}` | A1111 / ComfyUI 旧编码器 | Krea 2 走自然语言编码，权重语法不生效，还可能被当成字面文字 |
| `@artist_name` | Anima | 同上，Krea 2 没有该符号语义；写画师风格要用**描述**（媒介 / 线条 / 上色 / 色盘 / 时代） |
| `--ar 16:9 --v 6` | Midjourney | 参数不属于提示词；Krea 2 分辨率在工作流里设 |
| `8k, ultra detailed, hyperrealistic` | 通用堆词 | 空词，不增加任何画面信息 |
| 负面词串 `worst quality, lowres, bad anatomy` | SD 系 | Krea 2 主要靠正向 caption；真要排除就用一句自然语言「no second figure」 |

## 四、出处与许可

- `docs/prompting.md`、`docs/expansion.txt`：Krea 官方仓库
  <https://github.com/krea-ai/krea-2>，许可见该仓库
  `docs/KREA-2-COMMUNITY-LICENSE`。
- 官方示例图片与样例文案版权归 Krea；本文件只摘录**规则条文**用于提示词写作指导，
  不复制其图片资源。
- 本 skill 不隶属于 Krea，也不代表 Krea 官方立场。
