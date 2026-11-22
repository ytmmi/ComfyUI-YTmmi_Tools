# Z-Image 官方规则与变体差异（原文与出处）

本文件是 `z-image-prompt-writing` / `z-image-bilingual-text` 的参考资料，收录：

- 官方仓库 <https://github.com/Tongyi-MAI/Z-Image> 的 README（模型表、架构、推理脚本）
- 官方权重：<https://huggingface.co/Tongyi-MAI/Z-Image>、<https://huggingface.co/Tongyi-MAI/Z-Image-Turbo>
- ComfyUI 教程：<https://docs.comfy.org/tutorials/image/z-image/z-image> 与 `.../z-image-turbo`
- ComfyUI 模板 `image_z_image.json` / `image_z_image_turbo.json`（含 Original Settings 注记）
- 技术报告：<https://arxiv.org/abs/2511.22699>

## 一、四个变体（官方 Model Zoo 表）

```text
| Model              | Step | CFG | Task          | Visual Quality | Diversity | Fine-Tunability |
| Z-Image-Omni-Base  | 50   | 有  | Gen. / Editing| Medium         | High      | Easy            |
| Z-Image            | 50   | 有  | Gen.          | High           | Medium    | Easy            |
| Z-Image-Turbo      | 8    | 无  | Gen.          | Very High      | Low       | N/A             |
| Z-Image-Edit       | 50   | 有  | Editing       | High           | Medium    | Easy            |
```

中文落地：

- **Turbo**：8 次函数评估（NFE），**无 CFG**，企业级 H800 上亚秒级，16 GB 显存可跑；
  写实最强、质量最高，但**多样性低**，且官方标注**不可微调**。
- **Base（Z-Image）**：50 步、CFG 有效，**美学丰富、多样性高、可控性好**，适合创意生成与微调。
  官方明确它**支持有效负面提示词**。
- **Omni-Base**：生成 + 编辑的原始底座，发布给社区做微调。
- **Edit**：指令式编辑变体，中英双语指令理解强。

> ⚠ **判断负面词是否生效，只看变体**：Turbo 没有 CFG 分支，负面提示词不参与计算；
> Base / Omni / Edit 有 CFG，负面词真实生效。

## 二、架构与提示词的关系

官方描述：*"We adopt a Scalable Single-Stream DiT (S3-DiT) architecture. In this setup, text,
visual semantic tokens, and image VAE tokens are concatenated at the sequence level to serve as a
unified input stream, maximizing parameter efficiency compared to dual-stream approaches."*

落地：

- 文本是**序列级拼接的统一流**，所以提示词按**自然语言顺序**被整体理解，
  写成 tag 串会破坏这种顺序语义；
- 文本编码器是 **Qwen3-4B**（ComfyUI 侧 `qwen_3_4b.safetensors`），
  中英双语理解是它的天然能力——**画面文字可以直接写中文**。

## 三、官方示例提示词（`inference.py`，Turbo 默认参数）

```text
Young Chinese woman in red Hanfu, intricate embroidery. Impeccable makeup, red floral forehead
pattern. Elaborate high bun, golden phoenix headdress, red flowers, beads. Holds round folding fan
with lady, trees, bird. Neon lightning-bolt lamp (⚡️), bright yellow glow, above extended left palm.
Soft-lit outdoor night background, silhouetted tiered pagoda (西安大雁塔), blurred colorful distant
lights.
```

从这条能读出官方期望的形状：

1. **先主体后配件**：人 → 妆造 → 头饰 → 手持物；
2. **每个名词都带修饰**（`intricate embroidery`、`golden phoenix headdress`），而不是空泛质量词；
3. **具体场景名词**（`silhouetted tiered pagoda`），甚至直接给中文地名；
4. **光位与层次收尾**（`Soft-lit outdoor night background, blurred colorful distant lights`）。

## 四、官方推荐参数（ComfyUI 模板注记）

| 项 | Turbo | Base |
| --- | --- | --- |
| 步数 | 8 | **30–50**（模板 Original Settings：`Steps: 30～50`） |
| CFG | 无（`guidance_scale = 0.0`） | **3–5**（模板注记：`cfg: 3～5`） |
| 默认分辨率 | 1024×1024 起（模板用 ResolutionSelector） | 同上 |
| 负面提示词 | 不参与 | **有效，且模型敏感** |
| 采样器 | 模板默认（euler 系） | 同左 |

这些是**工作流参数**，不要写进提示词正文。

## 五、Z-Image 的三种"能力卖点"及其写法

官方 README 的 Showcase 给了三块，可直接对应写法：

| 卖点 | 官方描述 | 写法落地 |
| --- | --- | --- |
| Photorealistic Quality | "strong photorealistic image generation while maintaining excellent aesthetic quality" | 给镜头 / 焦段 / 光位 / 材质，而不是 `realistic` |
| Accurate Bilingual Text Rendering | "excels at accurately rendering complex Chinese and English text" | 中文逐字加引号 + 位置 + 字体气质；控制在短句 |
| Prompt Enhancing & Reasoning | "enables it to transcend surface-level descriptions and tap into underlying world knowledge" | 可以写**意图与情境**（`a nook a librarian would build`），让模型补细节；关键约束仍要写死 |

## 六、常见误区

| 误区 | 事实 |
| --- | --- |
| 「Z-Image 和 Turbo 写法一样，负面词通用」 | 错。Turbo 无 CFG，负面词无效；Base 有 CFG 且**对负面词敏感**，越堆越差 |
| 「提示词越长越好」 | 不成立。自然语言顺序语义更重要；堆形容词会互相稀释 |
| 「要用 SD 的 tag 与权重语法」 | 不需要。`(x:1.2)` 这类语法没有训练分布支持，写进正文只会变成噪声 |
| 「Turbo 反复抽卡能出不同构图」 | Turbo 多样性低是设计取舍；要探索用 Base |
| 「中文提示词会降低质量」 | 文本编码器是 Qwen3-4B，**中英双语**；但**画面内文字**与**描述语言**是两件事，描述用英文更稳 |

## 七、出处与许可

- 代码与权重：Tongyi-MAI/Z-Image（GitHub）与 Hugging Face / ModelScope 同名仓库，许可见仓库 `LICENSE`。
- ComfyUI 教程与模板：<https://docs.comfy.org/tutorials/image/z-image/z-image>、
  <https://docs.comfy.org/tutorials/image/z-image/z-image-turbo>、
  <https://github.com/Comfy-Org/workflow_templates>（`templates/image_z_image*.json`）。
- 技术报告：<https://arxiv.org/abs/2511.22699>。
- 本文件只摘录规则与参数注记，不复制官方示例图。
