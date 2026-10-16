# 生成Qwen2.1提示词
"""生成Qwen2.1提示词节点。

用本地 **Qwen-Image-2.1 PE-I2I**（Qwen3.5-9B 微调 + W4A8 量化）把用户提示词改写成
Qwen-Image 2.1 可直接使用的提示词，并单独输出模型的思考内容。

内置系统提示词 = **官方提示词原文**（逐字符，见 `QWEN21_T2I_SYSTEM_PROMPT` /
`QWEN21_EDIT_SYSTEM_PROMPT`），与插件 `skills/qwen-image-{t2i,edit}-prompt/references/`
下的官方参考文档**字节一致**（由单测 parity 用例守住）：
- 文生图：8 步法（拆分需求 → 定画幅 → 开场句 → 元素清单 → 走画面 → 文字 → 光照 → 收尾）+ 全篇风格规则；
- 图像编辑：两套语言决策 (A)/(B)、属性解耦原则、`<imageN>` 引用规则、`wh_ratio`/`ratio_follow`
  判定表（含扩图/全景/三视图）、思考流程，末尾以 `The user's edit instruction to rewrite is:` 引导用户指令。
   官方原文很长（t2i ≈ 9.9k 字符 / edit ≈ 17.7k 字符 → 首 token 前要多算 prefill），
   介意速度时可自己接「系统提示词」输入端口换成精简版。

模型来源：`models/LLM`（目录名**大小写不敏感**）下的 `.safetensors` 量化权重，
即 ComfyUI 官方 `comfyui-quantized` 格式（`__metadata__._quantization_metadata`，
权重为 `asym_w4a8_int8` / `int8_tensorwise` + ConvRot，视觉塔与 norm/bias 保持 bf16）。

为什么不用自写算子：ComfyUI 0.26+/0.40 已原生支持 Qwen3.5 文本编码器与 w4a8 量化算子
（`comfy.text_encoders.qwen35` + `comfy.ops.mixed_precision_ops` + `comfy_kitchen`），
本节点直接走 `comfy.sd.load_clip` → `clip.tokenize/generate/decode`，因此量化权重
**始终以打包形式驻留**，不会被展开成 17.5GB 的 bf16。

8GB 显存（RTX 4060 Laptop）特化：
1. **静态独占加载**（`disable_dynamic=True`）：关掉 ComfyUI 的逐 token 权重分页。
   实测同一模型同一张卡，动态分页 ~100s/token，静态独占 ~0.3s/token。
2. **按打包体积判「自动」**：ComfyUI 原生启发式按 bf16 展开（12.77GB）判定，8GB 卡必然
   退回内存；本节点读 safetensors 头部按真实存储（6.38GB）判定，从而走最快的显存独占。
3. **分块词表投影**：int8 词表头（0.95GB）在原生实现里每次调用都要转置拷贝一份，
   只剩 ~1GB 空闲显存时会触发分配器抖动（单次 logits 123ms → 3.9s）。这里按词表
   分块走**同一个** int8 算子，瞬时分配降到 chunk 级，数学完全一致。
4. **视觉塔按需上显存**：不带图时视觉塔（0.85GB bf16）留在内存，带图时才搬上显存。
5. **算子后端自适应**：`torch < cu130` 时 comfy_kitchen 会禁用 CUDA 量化后端，
   此时自动打开 triton 融合核（同一套 w4a8 数学，实测约 2 倍于 eager 回退）。
6. **模型跨次运行缓存**：读取 6.4GB + 构建约 8s，缓存后同一模型只付一次。
7. **思考预算**（`思考预算`，默认 256，0 = 不限）：软提示 + 硬截断——用满预算就强制把
   `</think>` 作为下一个 token 注入，保证仍然产出答案。实测不限预算时 512 个 token 会被
   思考全部吃满、生成文本为空；预算 128 时思考被闭合、产出 1554 字合法 JSON，整轮还更快。
"""

import contextlib
import dataclasses
import gc
import json
import logging
import struct
from pathlib import Path
from types import MethodType

LOGGER = logging.getLogger("YTmmi.TextGenerateQwen21Prompt")

try:
    import torch
except Exception:  # pragma: no cover - 无 torch 时仅保证模块可导入
    torch = None

# ============================== 常量 ==============================

NODE_DISPLAY_NAME = "生成Qwen2.1提示词"

# models/LLM 目录名（大小写不敏感比较，测试断言这里必须是小写常量）
LLM_DIR_NAME = "llm"
MODEL_SUFFIXES = (".safetensors",)

# 「运行设备」
DEVICE_AUTO = "自动"
DEVICE_VRAM = "显存"
DEVICE_RAM = "内存"

# 「任务类型」
TASK_AUTO = "自动"
TASK_T2I = "文生图"
TASK_EDIT = "图像编辑"

# 「采样模式」
SAMPLING_ON = "on"
SAMPLING_OFF = "off"

# 词表分块默认行数：248320 词表 / 32768 = 8 块，单块 int8 转置瞬时分配约 128MB
HEAD_CHUNK_ROWS_DEFAULT = 32768
# 参考图最长边默认值（与视觉塔 patch=16、merge=2 匹配，须为 32 的倍数）
VISION_MAX_SIDE_DEFAULT = 1024
VISION_PATCH_MULTIPLE = 32

# 思考预算默认值（token 数；0 = 不限）。Qwen3.5 的思考是普通 token 流，1 token ≈ 1 步，
# 不设预算时模型可能把「最大长度」全部花在思考上而产出空答案。
THINKING_BUDGET_DEFAULT = 256
# 思考预算的软提示：先让模型自觉简短，硬性截断（强制吐出 `</think>`）再兜底
THINKING_BUDGET_HINT = ("Keep your internal reasoning brief — at most about {budget} tokens — "
                        "then stop thinking and write the final JSON answer directly.")
# 官方 edit 提示词末尾的引导句（必须**紧贴**用户指令，因此软提示要插在它前面）
EDIT_INSTRUCTION_CUE = "The user's edit instruction to rewrite is:"

# 显存预留：CUDA 上下文 + 词表/logits 等临时量
VRAM_RESERVE_BYTES = 384 * 1024 * 1024
# 「自动」判定可独占显存的上限比例（其余留给系统与其他节点）
AUTO_VRAM_FRACTION = 0.9

QWEN21_T2I_SYSTEM_PROMPT = """# Image Prompt Rewriting Expert

You turn a user's image request into one long English paragraph that describes the
finished image as if you were looking at it, plus the aspect ratio it should be
rendered at. You are not talking to the user and not talking to a renderer: you are
an observer reporting what is in the frame.

Work through the eight steps below in order. Each step commits one decision; later
steps never revise an earlier one.

## Step 1 — Read the brief and split it in two

List what the user has fixed and what they have left open.

Fixed, and it must survive into your description unchanged: every string of text
they want shown, every named object, every count, every stated colour, every stated
position, and the aspect ratio if they gave one. Copy their text strings character
for character, in their own script, including punctuation and spacing.

A third thing they may give you is an instruction about the job rather than about the
picture — "use double quotes", "no hard-edged blocks", "4K, no noise", "make sure the
text is sharp". That is not content. Obey it silently where it applies and never echo
it: the description states what is in the frame, never what must be done.

Open, and you must decide it: everything they did not mention. A three-word request
and a three-hundred-word request both become a description of the same size, so a
short brief means you are inventing most of the frame, not writing less.

## Step 2 — Fix the frame

Decide the orientation from the subject, then pick the ratio.

If the user states a ratio, use it. Otherwise: `3:2` for anything horizontal and
`2:3` for anything vertical — these are the two defaults and cover most images.
Use `1:1` for a square badge, icon, album cover or single centred emblem, `16:9`
for a wide cinematic or presentation frame, `1:2` or `9:16` for a phone screen or a
tall standing banner. `3:4`, `2:1`, `21:9`, `4:3`, `9:21`, `4:5`, `3:1`, `5:4`,
`1:3` exist but only when the subject or the user really calls for them.

The ratio lives only in the `wh_ratio` field. Never write a ratio, a resolution, or
a pixel count into the description itself.

## Step 3 — Write the opening sentence

One sentence, around twenty words. Name the medium, the style, the subject, and the
background or palette; usually name the orientation too:

`The image is a ⟨vertical / wide / square / tall⟩ ⟨style⟩ ⟨photograph · poster · illustration · scene · portrait · infographic · close-up · graphic · page · card · sheet · logo⟩ of ⟨subject⟩, ⟨the background and its palette⟩.`

`This is a …` or a bare `A vertical realistic photograph of …` work equally well. The
medium noun is the one part that is never omitted.

The style word goes here — realistic, photorealistic, minimalist, flat-vector,
cinematic, watercolour, isometric, editorial, hand-drawn, 3D-rendered, retro. Name
it once here; you may echo it in the closing sentence.

## Step 4 — Inventory before you write

Before any more prose, settle two lists.

Every element that will appear, each with a place in the frame: upper-left,
across the top, on the far right, in the lower-third, in the centre, in front of,
behind, tucked into the corner. You will need eight to fourteen such positional
phrases, about ten typically, and they must reach the corners, the edges and the
centre — not cluster in the middle.

Every piece of text that will be legible in the image, in reading order.

## Step 5 — Walk the frame

Now describe it in order. Which order depends on how the frame is filled.

**If the frame is divided into regions** — a poster, a page, an interface, a layout, a
wide scene with several things in it — walk the regions:

1. The background and the surface it sits on — this comes immediately after the
   opening sentence, not at the end.
2. The top band: headline, header bar, sky, ceiling, whatever occupies the top edge.
3. Down and across the body of the frame: left side, then centre, then right side.
   Give each region one or two sentences.
4. The bottom band: footer, foreground, ground plane, base row.

**If one subject fills the frame** — a portrait, a close-up, a single object — walk
the subject instead: the background and how far it falls off, then the subject's pose
and where it is placed in the frame, then head and face, then body and each garment or
surface, then what is held or touching it, then whatever little is left at the edges.
Keep using positional phrases inside the subject — in the upper-left of the frame,
behind the left shoulder, along the lower edge — so the frame stays locatable.

Roughly a third of your sentences should open on the positional phrase itself —
"On the right side of the frame, …", "In the upper-left corner, …", "Across the
lower third, …" — so the reader always knows where they are looking.

Keep it to one paragraph. Break to a new paragraph only when the image is genuinely
built from stacked regions — panels, cards, sections, slides — and then one
paragraph per region, each opening on where that region sits.

## Step 6 — Set every piece of text

Skip this step if nothing in the image is meant to be read — a third of images have
no legible text at all, and inventing signage for them is a mistake.

Otherwise, for each string from your Step 4 list, in reading order, name where it sits,
what it looks like, and what it says: `a bold black headline across the top reads "…"`.

Put the string in straight double quotes, in its own script — Chinese, Russian,
Korean, Japanese and Arabic text stays in Chinese, Russian, Korean, Japanese and
Arabic. Give its weight, colour, case and relative size. Describe a line break as a
second line rather than putting a real newline inside the string. If a mark is not meant
to be read — distant signage, a label behind glass, dense body copy — call it
blurred, indistinct, or too small to read rather than inventing letters. If the image contains a chart
or a table, its axes, tick labels, legend entries, series and cell values are text
too: write them out.

## Step 7 — Give the lighting its own sentence

Every image has light in it, and the description always accounts for it: the source,
its direction, its quality, and the shadows and highlights it leaves. Soft diffused
daylight from a window on the left, hard overhead studio light, warm low sun, flat
even ambient light for a diagram.

Once the contents are placed, give it a sentence of its own — `The lighting is …` —
or, if the light is what makes a particular surface look the way it does, fold it into
that surface's sentence. Either way it is stated explicitly, not left implied.

## Step 8 — Close with the whole frame

End on a single sentence that steps back:

`The overall composition ⟨is / uses / feels⟩ …`

`The composition is …`, `The overall design …`, `The overall mood …`, `The overall
palette …` and `The image has …` are the same move. Cover balance and symmetry, the
palette, the style, and the mood in that one sentence. Write exactly one such
sentence — do not follow it with a second summary.

## Throughout

**Size.** The description runs about twenty sentences and four to five hundred words,
roughly twenty-five words a sentence. That is the same size whether the brief was three
words or three hundred: a dense frame with many regions and a lot of text runs longer, a
single quiet subject runs shorter, but a thin brief never buys a thin description.

**Observe, don't instruct.** Present tense, third person, declarative. No "you", no
"create", no "make sure", no "the AI should". No quality boosters — no "masterpiece",
"8K", "highly detailed", "award-winning".

**Hedge what you cannot be certain of.** An observer describing a picture says
"appears to be", "likely", "suggesting", and offers a pair — "a notebook
or a tablet", "wood or dark laminate" — when the thing is genuinely ambiguous. Do
this often; it is the natural register here. Be flatly definite only about what the
user fixed.

**Name colours with a modifier, almost never bare.** Deep navy, muted olive, pale
cream, warm terracotta, soft dusty rose, blue-grey, off-white, charcoal, brownish-
green. Hex codes only if the user gave them.

**Give the material, not just the noun.** Brushed metal, matte plastic, glossy
ceramic, coarse linen, weathered wood, frosted glass, grain, scuffs, condensation,
visible brush strokes, paper fibre.

**Enumerate; never summarise.** "Several items" and "various decorations" are not
descriptions. Say what each thing is. Write small counts as words — three, five,
twelve — and if something is partly hidden, say so and describe the visible part.

**People get their observable surface.** Build, posture, where they are looking,
expression, hair, skin tone, and each garment with its colour and material. Age is a
life stage or a decade — a child, a teenager, a young adult, middle-aged, elderly,
in her thirties — never a number of years. If a face is turned away or cropped, say
that instead of describing it.

**Objects by class, not by brand.** A silver laptop, a mirrorless camera, a compact
hatchback — unless the user named the brand. Photographic and design vocabulary is
welcome: shallow depth of field, bokeh, backlit, close-up, negative space,
grid, drop shadow.

**Everything holds together physically.** Shadows fall away from the light, reflections
match what is in front of the surface, scale is consistent between neighbouring
objects, and a surface reacts to what sits on it. If the user asked for something
impossible, describe it as the image shows it and let the rest of the scene stay
coherent around it.

## Language

The description is always in English, whatever language the request arrives in. The
only exception is text shown inside the image, which stays in its own script.

## Output format

Return one strictly valid JSON object on a single line, nothing before or after:

{"rewritten_prompt": "<the description>", "wh_ratio": "<e.g. 3:2>"}"""

QWEN21_EDIT_SYSTEM_PROMPT = """# Edit Prompt Enhancer — General (v2, 精简版)

**FIRST — there are TWO separate language decisions. Do NOT conflate them.**

**(A) Language of the rewritten prompt's DESCRIPTIVE prose — every word OUTSIDE double quotes (the description you write for the diffusion model, NOT the text painted into the image). This decision is final and non-negotiable:**
- User instruction is in Chinese → write the description in Chinese.
- User instruction is in English → write the description in English.
- User instruction is in ANY other language (Japanese, Korean, French, Spanish, Thai, etc.) → write the description in English.

**(B) Language of the TEXT THAT WILL BE RENDERED INTO THE OUTPUT IMAGE — the content INSIDE double quotes. Decide it in this strict priority order:**
1. If the user's instruction gives the exact text to write, OR names a target language for the text (e.g. "改成'夏日特惠'", "把标题写成英文", "add a Japanese title", "write the caption in Thai") → render exactly that text / in exactly that specified language.
2. Otherwise, if the input image already contains text → render in the DOMINANT language of the image's existing text — even when the instruction is written in a different language.
3. Otherwise (the image contains no text AND the instruction names no target language) → render in the language of the user's instruction itself — including Japanese, Korean, Thai, Arabic, French, etc. Do NOT force it to English.
Worked example: image is mostly Thai, instruction is in English asking to add/redesign a title without giving the exact words or a language → the rendered (quoted) text must be **Thai** (the image's dominant language), while the surrounding description (A) is still written in English.

Two reinforcements on decision (B): all rendered (quoted) text must be **monolingual** — do not mix Chinese and English inside the quotes and do not emit a bilingual pair unless the user explicitly asks for one. And **genre never overrides input language**: a "spec sheet / cinematic data-document / storyboard / technical parameter" look is achieved through layout and typography, NOT by switching rendered labels to English — every header, label, and caption stays in the decided language (standardized units and user-given proper nouns may remain Latin).

You are an expert at clarifying image editing instructions. Given a user's vague or ambiguous edit instruction and the input image(s), rewrite it into a precise, unambiguous, actionable editing directive. An input image is ALWAYS present — this is always an image-editing task, never text-to-image from nothing.

## Core Objective

Rewrite the instruction so a downstream image-editing model can execute it without guessing — anchored on what the input image(s) actually show, faithful to the user's intent, inventing nothing.

**How much you build is intent-branched.** When the user wants *this picture changed* (a local object/attribute/background edit, a text or UI edit, a quality or style change, a viewpoint/canvas transform), clarify and constrain: say exactly what changes, and let everything else stand. When the user wants *a new picture of this subject* (placing a subject in a new scene, compositing across images, a photo-shoot or poster or infographic built from a reference), construct actively: design the scene, lighting, composition and layout to a professional standard. Scale the elaboration to what was asked — a plain placement stays restrained, a styled shoot or a publication-grade poster is built out fully.

## The Governing Principle — Attribute Disentanglement at Full Strength

**Edit exactly the attribute(s) the user named, push each to a strong and unmistakable degree, and hold everything else at input fidelity.**

Both halves matter, and the two failure modes are symmetric:

- **Leakage** — touching what the user did not name (a sharpen that re-grades color, an upscale that reframes, a style change that drifts a face, an outfit swap that drops an accessory, a background change that "helpfully" cleans up something unmentioned).
- **Under-editing** — an output a viewer could mistake for the unedited input, because the requested change was applied faintly.

Preservation locks **content, never edit strength**. Recognizability is bought by naming what stays fixed, not by holding the effect back.

## What to Anchor, What to Decide

**Anchor on the image.** Every spatial, tonal and contextual claim comes from what is visibly there. If you are unsure a detail exists, leave it out — a preserved element described at a higher level of abstraction is always safer than an invented specific.

**Say what stays, without repainting it.** Name the untargeted content by type, position and role rather than describing its appearance, and prefer one blanket preservation clause over walking the frame. A preservation description reads to the model as a generation instruction: the more concretely you describe something you meant to keep, the more likely it drifts. Describe appearance concretely only for what you are actually changing, or when it is the only way to disambiguate between similar objects.

**Identity is the hardest invariant.** A person's facial identity and the personal accessories that make them recognizable; a product's exact design, markings and count; and the input's rendering medium (photograph, anime, illustration, sketch, 3D render, painting) all survive every edit unless the user explicitly targets them. When identity comes from a reference image, point at that image rather than describing features in words — verbal descriptions make the model regenerate and degrade the likeness.

**Resolve ambiguity, then commit.** Turn vague intent, imprecise spatial reference and unparameterized style words into something concrete and observable. Translate abstract quality language into the visual properties it implies. Where the instruction offers alternatives or contradicts itself, pick the most reasonable reading and state it as a decision. Keep the user's own action verb, spatial relations and described state intact, and treat anything they asked to preserve as absolute. Preserve creative or physically impossible intent rather than correcting it.

**Only what was asked.** Do not add operations the user did not request, and do not clean up unmentioned defects, overlays or clutter however prominent they look. When an edit removes, moves or reveals something, say enough about the newly exposed region that the result stays physically coherent.

**Text in the image is literal.** Whenever readable text will appear in the output, commit to the exact characters — every element, quoted, nothing summarized or abbreviated away. Text you cannot commit to should not be added at all. Match the typography and language the input establishes unless the user asks otherwise. When the operation extends the canvas outward, name it as outpainting explicitly.

**Write it as an instruction.** Lead with the operation, not a description of the finished picture, and write from the perspective of someone holding only the input image(s).

## Thinking Process

Before emitting JSON, reason through: what the image(s) actually contain (including a complete reading of any text present); what the user is asking for and which attributes that names; what must therefore stay fixed; the output size; and finally the composed directive. Close with a check that every visible element is either the target of the edit or covered by what stays fixed, that the requested change is unmistakable, that nothing outside the target was touched, and that every quoted string obeys language decision (B).

## Image Reference Rules

For Multi-Image Input (N >= 2), the rewritten instruction MUST use `<image1>`, `<image2>`, ... to refer to each input image. Do not use natural language references like "图1", "第一张图", "the first image", or "image A". This tagging format is mandatory and non-negotiable. For single-image input (N = 1), do NOT use tags — refer to the image naturally ("图像", "图片中", "the image").

State each image's role explicitly — which one is the canvas whose composition and untargeted content survive, and which supply material to transfer — and say what is taken from each. For scene generation with no canvas (合影/合照 and the like), all images serve as identity sources. Describe every referenced image individually; never compress several into a range or a group to avoid describing them one by one.

## Output Size Determination

You must determine two output fields: `wh_ratio` and `ratio_follow`. These two fields are mutually exclusive — when one has a value, the other must be empty string "".

### Step 1: Check if the user explicitly specified a size or aspect ratio

Look for any of the following in the user's edit instruction:
- Exact pixel dimensions: "1920x1080", "800×600", "1080p"
- Aspect ratios: "16:9", "4:3", "3:2", "9:16", "1:1"
- Descriptive terms mapped to aspect ratios:
  - "正方形" / "square" / "头像" / "avatar" / "profile picture" / "专辑封面" / "album cover" → "1:1"
  - "横版" / "landscape" / "横屏" / "电脑壁纸" / "desktop wallpaper" / "宽屏" / "widescreen" / "视频封面" / "video thumbnail" / "PPT" / "幻灯片" / "slide" / "演示文稿" → "16:9"
  - "竖版" / "portrait" / "竖屏" / "手机壁纸" / "phone wallpaper" / "手机屏幕" / "Instagram story" / "Stories" / "Reels" / "短视频封面" → "9:16"
  - "手机全面屏" / "全面屏" / "iPhone屏幕" / "iPhone screen" → "18:39"
  - "安卓全面屏" / "Android screen" → "9:20"
  - "超宽" / "ultrawide" / "带鱼屏" → "7:3"
  - "电影画面" / "cinematic" / "电影比例" / "宽银幕" / "cinemascope" → "21:9"
  - "海报" / "poster" → "2:3"
  - "证件照" / "ID photo" / "passport photo" / "小红书" / "Xiaohongshu" → "3:4"
  - "iPad屏幕" / "tablet" / "平板屏幕" → "4:3"
  - "全景图" / "panoramic" / "panorama" → "2:1"
  - "名片" / "business card" → "9:5"
  - "A4" → "5:7"(竖向)or "7:5"(横向)
  - "1080p" / "720p" → "16:9"

**High-resolution keywords ("2K", "4K", "8K") are quality descriptors, NOT aspect ratio indicators.** When the user mentions "2K", "4K", or "8K", these only express a desire for high image quality. They must NOT be used to infer or determine the aspect ratio. The aspect ratio should still be determined by other explicit cues or by the input image's ratio. For output resolution, always use 2K-level resolution regardless of whether the user says "2K", "4K", or "8K".

If the user specified a size or ratio:
→ `wh_ratio` = the corresponding ratio (e.g., "16:9", "1:1", "3:2")
→ `ratio_follow` = ""

If the user specified exact pixel dimensions (e.g., "1920x1080"), convert to the simplest integer ratio (1920:1080 = 16:9).

### Step 2: If the user did NOT specify any size or ratio

#### Single-image editing (1 input image):
The output should follow the input image's resolution.
→ `wh_ratio` = ""
→ `ratio_follow` = "<image1>"

**Exception — Single-image scene generation**: If the task generates a new scene from scratch using the input image only as an identity reference (e.g., "拍一套写真", "cosplay成X", "穿越到古代"), do NOT follow the input image's ratio — the output is a new composition, not an edit of the existing image. Instead, choose `wh_ratio` by scene semantics:

| Scene type | wh_ratio |
|---|---|
| Portrait / 写真 / half-body | "2:3" |
| Full-body scene / outdoor activity | "3:4" |
| Landscape-oriented scene | "3:2" |
| No clear orientation hint | Follow the input image's ratio (set `ratio_follow` to `<image1>`, `wh_ratio` to "") |

#### Multi-image editing (N ≥ 2 input images):
You must identify the **canvas image** (the image whose composition and framing the output should follow), then set `ratio_follow` to that image's tag.

| Edit type | Canvas | ratio_follow |
|---|---|---|
| Compositing — transfer subject into a scene ("把A P到B中", "放到", "加入到") | The target scene image | "<imageX>" (scene image number) |
| Face/head swap ("换脸", "换头") | The body image | "<imageX>" (body image number) |
| Clothing swap ("换衣服", "换装") | The person image | "<imageX>" (person image number) |
| Style transfer ("画成X的风格", "风格迁移") | The content image (not the style reference) | "<imageX>" (content image number) |
| Background replacement | The foreground subject image | "<imageX>" (subject image number) |
| Local object replacement | The original image being edited | "<imageX>" (original image number) |
| Scene generation — no canvas ("合影", "合照", "一起变老", "让他们X") | No canvas — you must choose a ratio | See below |

For **scene generation tasks with no canvas** (合影, 合照, 一起吃饭, etc.), set `ratio_follow` = "" and choose `wh_ratio` by scene semantics:

| Scene type | wh_ratio |
|---|---|
| Group photo / 合影 / 合照 | "3:2" |
| Portrait / 写真 | "2:3" |
| Poster / 海报 | "2:3" |
| Desktop wallpaper | "16:9" |
| Phone wallpaper | "9:16" |
| No clear orientation hint | Follow the last input image's ratio (set `ratio_follow` to the last image, `wh_ratio` to "") |

#### Outpainting (扩图 / 延伸画面):

For outpainting tasks where the user did NOT specify a target aspect ratio, do NOT simply follow the input image's ratio — outpainting changes the image's proportions by definition. Instead, infer the new ratio from the extension direction:

- Extend **right only** or **left only**: widen the ratio. E.g., a 1:1 input → "3:2"; a 3:4 input → "1:1" or "4:3".
- Extend **both left and right**: widen more aggressively. E.g., a 1:1 input → "16:9" or "2:1".
- Extend **down only** or **up only**: make the ratio taller. E.g., a 1:1 input → "2:3"; a 16:9 input → "4:3" or "1:1".
- Extend **both up and down**: make the ratio significantly taller. E.g., a 1:1 input → "9:16".
- Extend **all sides**: keep the original ratio (the image grows uniformly).

As a general rule, estimate the extended area as roughly 30%–50% additional space in the specified direction(s), then compute the new W:H ratio accordingly. Set `ratio_follow` = "" and `wh_ratio` = the inferred ratio.

#### Panoramic generation (全景 / panorama):

| Panoramic type | wh_ratio |
|---|---|
| Standard panorama / 全景 | "2:1" |
| Wide panorama / 超宽全景 | "3:1" |
| 360° / VR panorama | "2:1" |
| User specified a different ratio | Use the user's specified ratio |

Set `ratio_follow` = "".

#### Three-view drawings and multi-grid generation (三视图 / 多宫格):

For three-view or multi-panel grid generation where the user did NOT specify an aspect ratio, do NOT use a fixed default. Determine it adaptively from:

1. **Subject shape proportion**: a tall standing person is vertically oriented, a car is horizontally oriented, a round object roughly square.
2. **Panel layout arrangement**: how the panels are arranged (1×3 horizontal, 3×1 vertical, 2×2) and the shape of each panel.
3. **Combined ratio**: (single panel W × columns) : (single panel H × rows), choosing the ratio that best fits the content without excessive empty space or cropping.

Examples:
- Three side-by-side views of a standing person (each panel ~1:3, portrait) → overall ratio = "1:1" — do NOT over-widen to "2:1" or "3:1", which would squash each portrait panel (use "3:1" only when each panel is itself landscape, e.g., a car)
- Three side-by-side views of a car (each panel ~3:2) → overall ratio = "3:1" or "9:2"
- 2×2 grid of a square object → overall ratio = "1:1"
- 3×3 grid of square panels → overall ratio = "1:1"

Set `ratio_follow` = "" and `wh_ratio` = the adaptively determined ratio.

## Output Format
Output a valid JSON object with exactly three fields:
```json
{
  "rewritten_prompt": "<the rewritten editing instruction>",
  "wh_ratio": "<aspect ratio like '16:9', or empty string>",
  "ratio_follow": "<'<image1>' / '<image2>' / ... / ''>"
}
```

`rewritten_prompt` formatting rules:
- The entire rewritten prompt must be a single continuous paragraph with NO line breaks or newline characters (`\\n`).
- All text that should appear as visible, readable content in the output image must be enclosed in double quotes (""). Descriptive or structural language that does not appear as rendered text should NOT be quoted.
- **Never include any resolution or aspect ratio information in `rewritten_prompt`** (e.g., "2:3", "16:9", "1920x1080", "2K", "4K"). Resolution and aspect ratio are conveyed exclusively through the `wh_ratio` and `ratio_follow` fields.
- Write it out in full — no ellipsis, no truncation.
- State requirements affirmatively ("保持背景与输入图完全一致") rather than as prohibitions ("禁止改变背景"). Standard preservation phrasing "保持/保留[X]不变" is fine.
- Be precise and decisive: no hedging, no unresolved alternatives, no vague degree words left unresolved.
- **Language-purge self-check (do this last)**: re-scan every double-quoted string — the text that will be RENDERED in the image — and enforce language decision (B). No quoted string may mix Chinese and English, form a bilingual pair, or carry a parenthetical translation gloss unless the user explicitly asked. Standardized units and user-given proper nouns may remain Latin.

Rules for each field:
- `rewritten_prompt`: The rewritten editing instruction. The descriptive prose (outside double quotes) follows language decision (A); the text rendered inside the image (inside double quotes) follows language decision (B). Retain proper nouns and domain-specific terms in their original language, placed in English double quotes.
- `wh_ratio`: The target aspect ratio as "W:H". Set to "" when the output resolution should follow an input image instead.
- `ratio_follow`: Which input image's resolution the output should follow ("<image1>", "<image2>", …). Set to "" when a specific aspect ratio is provided in `wh_ratio`.

Mutual exclusivity rule:
- If `wh_ratio` has a value → `ratio_follow` must be ""
- If `ratio_follow` is "<imageX>" → `wh_ratio` must be ""

Do not include any text outside the JSON object — no greetings, no explanations, no markdown code fences.

The user's edit instruction to rewrite is:"""


# ============================== 路径与模型发现 ==============================


def _comfy_root():
    """ComfyUI 根目录（含 comfy 包与 models 目录）。"""
    try:
        import comfy  # noqa: F401
        return Path(__import__("comfy").__file__).resolve().parent.parent
    except Exception:
        return None


def _plugin_derived_root():
    """从插件自身位置向上找 ComfyUI 根目录（同时含 models/ 与 comfy/ 或 main.py）。

    裸 Python（未启动 ComfyUI、`folder_paths` 与 `comfy` 都不在 sys.path）时靠它兜底。
    """
    here = Path(__file__).resolve()
    for parent in here.parents:
        try:
            if (parent / "models").is_dir() and ((parent / "comfy").is_dir() or (parent / "main.py").is_file()):
                return parent / "models"
        except OSError:
            continue
    return None


def _model_roots():
    """候选的 models 根目录（仅返回存在的目录，保序去重）。"""
    roots = []
    try:
        import folder_paths
        models_dir = getattr(folder_paths, "models_dir", None)
        if models_dir:
            roots.append(Path(models_dir))
    except Exception:
        pass
    root = _comfy_root()
    if root is not None:
        roots.append(root / "models")
    fallback = _plugin_derived_root()
    if fallback is not None:
        roots.append(fallback)

    out = []
    for candidate in roots:
        try:
            if candidate.is_dir() and candidate not in out:
                out.append(candidate)
        except OSError:
            continue
    return out


def llm_model_dirs():
    """`models/LLM` 目录列表（目录名大小写不敏感）。"""
    dirs = []
    for root in _model_roots():
        try:
            children = sorted(root.iterdir())
        except OSError:
            continue
        for child in children:
            try:
                if child.is_dir() and child.name.lower() == LLM_DIR_NAME and child not in dirs:
                    dirs.append(child)
            except OSError:
                continue
    return dirs


def list_llm_models():
    """`models/LLM` 下的量化权重文件名（排序，供 COMBO 使用）。"""
    names = []
    for directory in llm_model_dirs():
        try:
            entries = sorted(directory.iterdir())
        except OSError:
            continue
        for entry in entries:
            try:
                if entry.is_file() and entry.suffix.lower() in MODEL_SUFFIXES and entry.name not in names:
                    names.append(entry.name)
            except OSError:
                continue
    return names


def resolve_model_path(name):
    """把下拉里的文件名（或绝对路径）解析为实际存在的权重路径；找不到返回 None。"""
    if name is None:
        return None
    text = str(name).strip()
    if not text:
        return None
    path = Path(text)
    if path.is_absolute():
        try:
            return path if path.is_file() else None
        except OSError:
            return None
    for directory in llm_model_dirs():
        candidate = directory / path.name
        try:
            if candidate.is_file():
                return candidate
        except OSError:
            continue
    return None


# ============================== 体积与放置 ==============================


def _read_safetensors_header(path):
    """只读 safetensors 头部（不映射张量），返回 (张量表, __metadata__)。"""
    with open(path, "rb") as handle:
        raw = handle.read(8)
        if len(raw) < 8:
            raise ValueError("safetensors 头部不完整：{}".format(path))
        (header_size,) = struct.unpack("<Q", raw)
        header = json.loads(handle.read(header_size).decode("utf-8"))
    metadata = header.pop("__metadata__", {}) or {}
    return header, metadata


def _safetensors_header(path):
    """只读 safetensors 头部（不映射张量），返回 {张量名: 头部信息}。"""
    return _read_safetensors_header(path)[0]


def _safetensors_metadata(path):
    """只读 safetensors 的 `__metadata__`（量化格式声明在这里）。"""
    return _read_safetensors_header(path)[1]


_DTYPE_BYTES = {
    "F64": 8, "I64": 8, "F32": 4, "I32": 4, "F16": 2, "BF16": 2, "I16": 2, "U16": 2,
    "F8_E4M3": 1, "F8_E5M2": 1, "I8": 1, "U8": 1, "BOOL": 1,
}


def state_dict_storage_bytes(state_dict):
    """权重文件的**实际存储**字节数（量化张量按打包字节，不按逻辑元素展开）。

    只读文件头即可算出：`numel(shape) * dtype_size`。9B 模型里 int4 打包权重是
    逻辑体积的一半，用「逻辑元素 × bf16」估算会得到 17.5GB、把 8GB 卡误判成放不下。
    """
    total = 0
    for info in state_dict.values():
        count = 1
        for dim in info["shape"]:
            count *= int(dim)
        total += count * _DTYPE_BYTES.get(info["dtype"], 1)
    return total


def state_dict_logical_size(state_dict, metadata=None):
    """把权重按原始精度展开后的**逻辑**体积（诊断/对比用）。

    打包格式（int4/int6）在文件里存的是半宽/0.75 宽的 int8，逻辑元素数是打包元素数的
    2 倍 / 4/3 倍；量化格式从 `__metadata__._quantization_metadata` 读，读不到就按
    bf16 稠密（×2）保守估计。
    """
    formats = {}
    if metadata:
        try:
            formats = json.loads(metadata.get("_quantization_metadata", "{}")).get("layers", {})
        except Exception:
            formats = {}
    total = 0
    for name, info in state_dict.items():
        count = 1
        for dim in info["shape"]:
            count *= int(dim)
        layer = name[:-len(".weight")] if name.endswith(".weight") else None
        factor = 2  # bf16
        if layer is not None:
            fmt = (formats.get(layer) or {}).get("format")
            if fmt == "asym_w4a8_int8":
                count *= 2
            elif fmt == "w6a8_int8":
                count = count * 4 // 3
        total += count * factor
    return total


def file_storage_bytes(path):
    """量化权重文件的实际存储体积（读头部，微秒级）。"""
    return state_dict_storage_bytes(_safetensors_header(path))


@dataclasses.dataclass
class Placement:
    """一次加载的完整放置方案（不只是一个初始设备）。"""

    load_device: object
    offload_device: object
    initial_device: object
    disable_dynamic: bool
    reason: str = ""


def _cpu():
    return torch.device("cpu")


def _accelerator_device():
    """可用的加速设备（CUDA / MPS），没有则返回 None。"""
    if torch is None:
        return None
    try:
        import comfy.model_management as mm
        device = mm.get_torch_device()
        if mm.is_device_cuda(device) or mm.is_device_mps(device):
            return device
    except Exception:
        pass
    try:
        if torch.cuda.is_available():
            return torch.device("cuda")
    except Exception:
        pass
    return None


def _device_total_bytes(device):
    """加速设备的总显存字节数（拿不到返回 0）。"""
    if torch is None or device is None:
        return 0
    try:
        if getattr(device, "type", "") == "cuda" and torch.cuda.is_available():
            index = device.index if device.index is not None else torch.cuda.current_device()
            return int(torch.cuda.get_device_properties(index).total_memory)
    except Exception:
        pass
    try:
        if getattr(device, "type", "") == "cuda":
            return int(torch.cuda.mem_get_info()[1])
    except Exception:
        pass
    return 0


def resolve_placement(storage_bytes, preference=DEVICE_AUTO):
    """按「运行设备」给出完整放置方案。

    - 显存：静态独占显存（关掉动态分页），offload 仍留在内存以便回退；
    - 内存：全部在内存中静态运行；
    - 自动：按**打包体积**判断能否独占显存（放得下就走最快的静态路径），
      放不下才交回 ComfyUI 自己的显存管理。
    """
    accelerator = _accelerator_device()
    cpu = _cpu()

    if preference == DEVICE_RAM:
        return Placement(cpu, cpu, cpu, True, "按设置强制在内存中运行")
    if preference == DEVICE_VRAM and accelerator is not None:
        return Placement(accelerator, cpu, accelerator, True, "按设置强制独占显存")
    if accelerator is not None:
        total = _device_total_bytes(accelerator)
        budget = int(total * AUTO_VRAM_FRACTION) if total else 0
        if budget and storage_bytes + VRAM_RESERVE_BYTES <= budget:
            return Placement(accelerator, cpu, accelerator, True,
                             "打包体积 {:.2f}GB 可独占显存（{:.2f}GB 预算）".format(
                                 storage_bytes / 1024 ** 3, budget / 1024 ** 3))
    load_device = accelerator if accelerator is not None else cpu
    return Placement(load_device, cpu, None, False, "显存放不下，交由 ComfyUI 显存管理按需换入")


def resolve_initial_device(storage_bytes, preference=DEVICE_AUTO):
    """放置方案对应的初始设备；交给 ComfyUI 时用它的原生启发式。"""
    placement = resolve_placement(storage_bytes, preference)
    if placement.initial_device is not None:
        return placement.initial_device
    try:
        import comfy.model_management as mm
        return mm.text_encoder_initial_device(
            placement.load_device, placement.offload_device, storage_bytes * 2)
    except Exception:
        return placement.load_device


# ============================== 量化算子后端 ==============================


def enable_fast_quant_backend():
    """挑选最快的量化算子后端，返回后端名（幂等：已启用 triton 时仍返回 triton）。

    `comfy_kitchen` 在 `torch.version.cuda < 13` 时**会禁用 CUDA 后端**（日志里有明确
    警告），此时 w4a8 只能走 eager 回退：同样的数学，但反量化是多条逐元素 kernel。
    打开 triton 后端后是单个融合 kernel（实测 gate_proj 12.0ms vs 26.3ms）。
    CUDA 后端可用时它的优先级本来就高于 triton，这里的开启不会改变选择。
    """
    try:
        import comfy_kitchen as ck
    except Exception:
        return "unknown"
    try:
        backends = ck.list_backends()
    except Exception:
        return "unknown"
    cuda = backends.get("cuda", {})
    if cuda.get("available") and not cuda.get("disabled"):
        return "cuda"
    triton = backends.get("triton", {})
    if triton.get("available"):
        if not triton.get("disabled"):
            return "triton"  # 之前已经打开过（幂等，避免缓存键抖动导致重复加载）
        try:
            ck.registry.enable("triton")
            LOGGER.info("CUDA 量化后端不可用（%s），已启用 triton 融合核",
                        cuda.get("unavailable_reason") or "torch < cu130")
            return "triton"
        except Exception as exc:  # pragma: no cover - 仅环境异常
            LOGGER.warning("启用 triton 后端失败：%s", exc)
    return "eager"


# ============================== 视觉 ==============================


def _fit_vision_size(height, width, max_side, multiple=VISION_PATCH_MULTIPLE):
    """按最长边缩放后的 (高, 宽)，两者都是 multiple 的倍数（视觉塔 patch=16 × merge=2）。"""
    if height <= 0 or width <= 0:
        raise ValueError("图像尺寸非法：{}x{}".format(width, height))
    target = max(int(max_side), multiple)
    scale = target / float(max(height, width))
    out_h = max(multiple, int(round(height * scale / multiple)) * multiple)
    out_w = max(multiple, int(round(width * scale / multiple)) * multiple)
    return out_h, out_w


def _resize_for_vision(image, max_side=VISION_MAX_SIDE_DEFAULT, multiple=VISION_PATCH_MULTIPLE):
    """把参考图缩放到最长边 = max_side，且宽高都是 multiple 的倍数（batch 保留）。"""
    if image is None:
        return None
    if torch is None:
        raise RuntimeError("缺少 torch，无法处理参考图")
    if image.dim() == 3:
        image = image.unsqueeze(0)
    height, width = int(image.shape[1]), int(image.shape[2])
    out_h, out_w = _fit_vision_size(height, width, max_side, multiple)
    if (out_h, out_w) == (height, width):
        return image
    x = image.permute(0, 3, 1, 2)
    x = torch.nn.functional.interpolate(
        x, size=(out_h, out_w), mode="bicubic", align_corners=False, antialias=True)
    return x.permute(0, 2, 3, 1).clamp(0.0, 1.0)


# ============================== 分块词表投影 ==============================


def _install_chunked_head(root, chunk_rows=HEAD_CHUNK_ROWS_DEFAULT):
    """把 lm_head 的 logits 计算换成按词表分块，数学与 ComfyUI 原生 int8 算子完全一致。

    原生 `int8_linear` 每次调用都 `weight.T.contiguous()`：248320×4096 的 int8 词表头
    意味着每次生成一个 token 都要额外申请 0.95GB 并整表转置拷贝。8GB 卡上只剩约 1GB
    空闲显存时这会触发分配器抖动（实测单次 logits 从隔离基准 123ms 涨到 3.9s）。
    分块后瞬时分配降到 chunk 级（32768 行 ≈ 128MB），且仍走同一个 `int8_linear` 算子。
    """
    if root is None or torch is None or int(chunk_rows) <= 0:
        return False
    module = getattr(getattr(root, "model", None), "lm_head", None)
    weight = getattr(module, "weight", None)
    if module is None or weight is None:
        return False
    try:
        from comfy_kitchen.tensor import QuantizedTensor
    except Exception:
        return False
    if not isinstance(weight, QuantizedTensor):
        return False
    params = getattr(weight, "_params", None)
    qdata = getattr(weight, "_qdata", None)
    if params is None or qdata is None or not getattr(params, "orig_shape", None):
        return False
    if len(tuple(params.orig_shape)) != 2:
        return False

    layout_type = getattr(module, "layout_type", None) or getattr(weight, "layout_type", None)
    vocab, inner = int(params.orig_shape[0]), int(params.orig_shape[1])
    scale = getattr(params, "scale", None)
    if layout_type is None or qdata.shape[0] != vocab:
        return False
    chunk_rows = max(1, min(int(chunk_rows), vocab))

    def chunked_logits(self, x):
        tail = x[:, -1:]
        parts = []
        for start in range(0, vocab, chunk_rows):
            end = min(start + chunk_rows, vocab)
            sub_scale = scale[start:end] if (scale is not None and scale.dim() >= 2) else scale
            sub_params = dataclasses.replace(params, scale=sub_scale, orig_shape=(end - start, inner))
            sub = QuantizedTensor(qdata[start:end], layout_type, sub_params)
            parts.append(torch.nn.functional.linear(tail, sub, None))
        return parts[0] if len(parts) == 1 else torch.cat(parts, dim=-1)

    root.logits = MethodType(chunked_logits, root)
    LOGGER.info("已启用分块词表投影：%d 行/块，共 %d 块", chunk_rows, (vocab + chunk_rows - 1) // chunk_rows)
    return True


# ============================== 思考预算 ==============================


def _transformers_tokenizer(clip):
    """从 CLIP 里掏出 transformers 的分词器（用于查特殊 token 的 id）。"""
    tokenizer = getattr(clip, "tokenizer", None)
    name = getattr(tokenizer, "clip_name", None)
    inner = getattr(tokenizer, name, None) if isinstance(name, str) else None
    return getattr(inner, "tokenizer", inner)


def _think_end_token_id(clip):
    """`</think>` 的 token id；查不到返回 None（此时思考预算退化为只加软提示）。"""
    tokenizer = _transformers_tokenizer(clip)
    for candidate in ("</think>", "<|/think|>", "</thinking>"):
        try:
            token_id = tokenizer.convert_tokens_to_ids(candidate)
        except Exception:
            continue
        if isinstance(token_id, int) and token_id >= 0 and token_id != getattr(tokenizer, "unk_token_id", None):
            return token_id
    # 兜底：Qwen3.5 的思考标记是单个 added token，可用 decode 反查
    for token_id in (248069,):
        try:
            if "</think>" in clip.decode([token_id]):
                return token_id
        except Exception:
            continue
    return None


def with_thinking_hint(system_prompt, budget):
    """把思考预算的软提示插进系统提示词。

    官方 edit 提示词以 `The user's edit instruction to rewrite is:` 结尾，这一句必须**紧贴**
    用户指令，所以软提示要插在它**前面**，不能直接追加到末尾。
    """
    hint = THINKING_BUDGET_HINT.format(budget=int(budget))
    text = (system_prompt or "").rstrip()
    if text.endswith(EDIT_INSTRUCTION_CUE):
        head = text[:-len(EDIT_INSTRUCTION_CUE)].rstrip()
        return "{}\n\n{}\n{}".format(head, hint, EDIT_INSTRUCTION_CUE)
    return "{}\n\n{}".format(text, hint)


def sample_token_with_thinking_budget(original, think_end_id, budget):
    """包一层 `sample_token`：思考用满 budget 个 token 后强制吐出 `</think>`。

    Qwen3.5 的思考就是普通 token 流（`<think>…</think>`），预算用尽时把 `</think>` 作为
    下一个 token 注入，模型随即转入正式答案——否则模型可能把「最大长度」全部花在思考上，
    最终返回空答案（实测 `思考=True` + 小 max_length 就是这个表现）。

    ⚠️ 一旦思考块关闭（模型自己吐出了 `</think>`，或这里强制注入）就**彻底停止干预**，
    否则会在正式答案中间插进 `</think>`。`budget <= 0` 表示不限，原样返回原函数。
    """
    if int(budget) <= 0:
        return original

    state = {"steps": 0, "closed": False}

    def sample_token(logits, *args, **kwargs):
        if state["closed"]:
            return original(logits, *args, **kwargs)
        if state["steps"] >= int(budget):
            state["closed"] = True
            return torch.full((logits.shape[0], 1), int(think_end_id),
                              dtype=torch.long, device=logits.device)
        token = original(logits, *args, **kwargs)
        state["steps"] += 1
        try:
            if int(token.reshape(-1)[0]) == int(think_end_id):
                state["closed"] = True
        except Exception:
            pass
        return token

    return sample_token


@contextlib.contextmanager
def temporary_sample_token(root, sampler):
    """临时替换实例上的 `sample_token`，退出时**精确还原**。

    `sample_token` 通常是类方法（`BaseGenerate.sample_token`），实例上原本没有这个属性，
    所以退出时 `del` 即可回落；但若实例上原本就有（测试替身 / 未来改动），必须还原原值，
    否则下一次调用会丢掉采样器。
    """
    previous = root.__dict__.get("sample_token") if hasattr(root, "__dict__") else None
    root.sample_token = sampler
    try:
        yield
    finally:
        if previous is not None:
            root.sample_token = previous
        else:
            try:
                del root.sample_token
            except AttributeError:
                pass


# ============================== 加载（含跨次运行缓存） ==============================


@dataclasses.dataclass
class LoadedModel:
    """一份已加载（并缓存）的模型。"""

    key: str
    path: Path
    clip: object
    inner: object
    root: object
    device: object
    storage_bytes: int
    backend: str
    head_chunk_rows: int = HEAD_CHUNK_ROWS_DEFAULT
    chunked_head: bool = False
    vision_on_gpu: bool = False
    placement_key: str = ""

    @property
    def visual(self):
        return getattr(self.root, "visual", None)


# 按权重路径缓存：同一份权重绝不重复加载（重复加载会触发 ComfyUI 卸载旧 patcher，
# 在部分环境（torch 2.8+cu129 + triton）卸载 mmap 量化权重会直接崩进程）。
# 只保留当前这一份权重：8GB 卡上两份 6.38GB 编码器根本放不下，多缓存没有意义。
_MODEL_CACHE = {}


def _clip_inner(clip):
    """取 SD1ClipModel 里真正的文本编码器（属性名 = clip_name，如 qwen35_9b）。"""
    cond = getattr(clip, "cond_stage_model", None)
    name = getattr(cond, "clip", None)
    if isinstance(name, str):
        inner = getattr(cond, name, None)
        if inner is not None:
            return inner
    for module in getattr(cond, "modules", lambda: [])():
        if hasattr(module, "transformer"):
            return module
    return None


def _weights_device(root):
    """模型主体权重当前所在设备（取第一个量化权重）。"""
    if root is None:
        return None
    try:
        model = getattr(root, "model", root)
        layers = getattr(model, "layers", None)
        if layers:
            for parameter in layers[0].parameters():
                return parameter.device
        for parameter in root.parameters():
            return parameter.device
    except Exception:
        return None
    return None


def _evict_cache(keep_key=None):
    """丢掉不再使用的缓存条目并归还显存。"""
    dropped = False
    for key in list(_MODEL_CACHE.keys()):
        if keep_key is not None and key == keep_key:
            continue
        _MODEL_CACHE.pop(key, None)
        dropped = True
    if dropped:
        gc.collect()
        try:
            import comfy.model_management as mm
            mm.soft_empty_cache()
        except Exception:
            pass


def load_qwen35_clip(model_path, device_preference=DEVICE_AUTO,
                     head_chunk_rows=HEAD_CHUNK_ROWS_DEFAULT):
    """加载（或复用缓存）Qwen-Image-2.1 PE-I2I 的文本编码器与分词器。

    缓存按**权重路径**索引：同一份权重只加载一次；只有「设备方案变了」或「换了另一个
    权重文件」才会真正重新加载。
    """
    if torch is None:
        raise RuntimeError("缺少 torch，无法加载模型")
    path = Path(model_path)
    if not path.is_file():
        raise ValueError("{}：模型文件不存在（{}）".format(NODE_DISPLAY_NAME, path))

    storage_bytes = file_storage_bytes(path)
    placement = resolve_placement(storage_bytes, device_preference)
    placement_key = "{}/{}/{}".format(placement.load_device, placement.offload_device,
                                      placement.disable_dynamic)
    backend = enable_fast_quant_backend()
    key = str(path.resolve())

    cached = _MODEL_CACHE.get(key)
    if cached is not None and cached.placement_key == placement_key:
        _apply_head_chunk(cached, head_chunk_rows)
        cached.backend = backend
        _ensure_resident(cached, placement)
        return cached

    _evict_cache(keep_key=key)

    import comfy.sd as comfy_sd

    model_options = {
        "load_device": placement.load_device,
        "offload_device": placement.offload_device,
    }
    if placement.initial_device is not None:
        model_options["initial_device"] = placement.initial_device

    LOGGER.info("%s：加载 %s（%s，%.2fGB 权重，后端 %s）", NODE_DISPLAY_NAME, path.name,
                placement.reason, storage_bytes / 1024 ** 3, backend)
    clip = comfy_sd.load_clip(
        [str(path)],
        embedding_directory=None,
        clip_type=comfy_sd.CLIPType.QWEN_IMAGE,
        model_options=model_options,
        disable_dynamic=placement.disable_dynamic,
    )
    inner = _clip_inner(clip)
    root = getattr(inner, "transformer", None) if inner is not None else None
    if root is None:
        raise RuntimeError("{}：模型结构不是 Qwen3.5（未找到 transformer），请确认权重".format(NODE_DISPLAY_NAME))

    entry = LoadedModel(
        key=key, path=path, clip=clip, inner=inner, root=root,
        device=placement.load_device, storage_bytes=storage_bytes, backend=backend,
        placement_key=placement_key)
    _apply_head_chunk(entry, head_chunk_rows)
    _place_vision(entry, want_gpu=False)
    _MODEL_CACHE[key] = entry
    _ensure_resident(entry, placement)
    return entry


def _apply_head_chunk(entry, chunk_rows):
    """按当前设置安装/卸载分块词表投影（同一份权重上可反复切换）。"""
    chunk_rows = int(chunk_rows or 0)
    if chunk_rows == int(entry.head_chunk_rows or 0) and entry.chunked_head == (chunk_rows > 0):
        return entry.chunked_head
    if chunk_rows <= 0:
        try:
            delattr(entry.root, "logits")
        except AttributeError:
            pass
        entry.chunked_head = False
    else:
        entry.chunked_head = _install_chunked_head(entry.root, chunk_rows)
    entry.head_chunk_rows = chunk_rows
    return entry.chunked_head


def _ensure_resident(entry, placement):
    """确保权重真的在目标设备（缓存命中时模型可能已被 ComfyUI 换回内存）。"""
    if torch is None:
        return
    target = placement.load_device
    current = _weights_device(entry.root)
    if current is None or current.type == target.type:
        return
    try:
        import comfy.model_management as mm
        mm.load_models_gpu([entry.clip.patcher], force_full_load=True)
    except Exception as exc:
        LOGGER.warning("%s：把权重换回 %s 失败：%s", NODE_DISPLAY_NAME, target, exc)
        return
    entry.device = target
    LOGGER.info("%s：缓存权重已换回 %s", NODE_DISPLAY_NAME, target)


def _free_vram_gb(device):
    """诊断用：设备空闲显存（GB）。"""
    try:
        import comfy.model_management as mm
        return mm.get_free_memory(device) / 1024 ** 3
    except Exception:
        try:
            return torch.cuda.mem_get_info()[0] / 1024 ** 3
        except Exception:
            return -1.0


def module_bytes(module):
    """模块参数占用的字节数（量化张量按打包存储算）。"""
    total = 0
    for parameter in module.parameters():
        if parameter is None:
            continue
        try:
            total += parameter.numel() * parameter.element_size()
        except Exception:
            continue
    return total


def _encoder_loaded_model(entry):
    """ComfyUI 侧代表本模型的那条 LoadedModel（用于 keep_loaded，避免被部分卸载）。"""
    try:
        import comfy.model_management as mm
        for loaded in mm.loaded_models():
            if loaded.model is entry.clip.patcher:
                return loaded
    except Exception:
        pass
    return None


def ensure_encoder_residency(entry, extra_bytes=0):
    """确保量化编码器**完整**驻留目标设备，并为本节点要用的额外显存腾地方。

    ⚠️ 必须做这一步，否则会踩到一个会崩进程的坑（正式环境 cu130 实测：
    `torch.AcceleratorError: CUDA error: invalid argument`）：视觉塔用裸 `.to("cuda")` 上了卡，
    ComfyUI 的显存账本并不知道这 0.85GB；一旦空闲显存不够，`clip.generate` 里的
    `load_models_gpu` 就会决定**部分卸载**文本编码器，而 `partially_unload` 会对量化权重调
    `m.to(device)`，comfy_kitchen 的 `QuantizedTensor._handle_to_copy` 在这个组合下直接报
    CUDA invalid argument（随后还可能带崩进程）。

    因此：① 权重不在目标设备时，才走一次 `free_memory` + `force_full_load` 整体加载；
    ② 权重已在设备上时，只按需卸载**别的**模型（`keep_loaded` 保住自己），绝不让 ComfyUI
    碰我们的量化权重。
    """
    if torch is None or str(getattr(entry.device, "type", "")) == "cpu":
        return
    try:
        import comfy.model_management as mm
    except Exception:
        return
    keep = [loaded for loaded in (_encoder_loaded_model(entry),) if loaded is not None]
    headroom = int(extra_bytes) + 512 * 1024 * 1024
    current = _weights_device(entry.root)
    if current is None or current.type != entry.device.type:
        try:
            mm.free_memory(int(entry.storage_bytes * 1.15) + headroom, entry.device, keep_loaded=keep)
            mm.load_models_gpu([entry.clip.patcher], force_full_load=True)
            LOGGER.info("%s：权重已整体加载到 %s", NODE_DISPLAY_NAME, entry.device)
        except Exception as exc:  # pragma: no cover - 仅环境异常
            LOGGER.warning("%s：整体加载失败：%s", NODE_DISPLAY_NAME, exc)
        return
    try:
        if mm.get_free_memory(entry.device) < headroom:
            mm.free_memory(headroom, entry.device, keep_loaded=keep)
    except Exception as exc:  # pragma: no cover - 仅环境异常
        LOGGER.warning("%s：腾显存失败：%s", NODE_DISPLAY_NAME, exc)


def generate_without_patcher(entry, tokens, **kwargs):
    """直接调用编码器自身的 `generate`，绕过 `CLIP.generate` 里的 `load_model`。

    `CLIP.generate` 会先 `load_models_gpu([patcher], memory_required=...)`；当显存紧张
    （带图的 8GB 场景）它会尝试**部分卸载我们的量化权重**从而崩在
    `QuantizedTensor._to_copy` 上。权重驻留由 `ensure_encoder_residency` 负责，
    这里只做 `CLIP.generate` 剩下的部分：设置 clip 选项 + 设备上下文 + 量化矩阵乘开关。
    """
    inner = entry.inner
    if inner is None:  # 结构异常（或测试替身）时退回原生路径
        return entry.clip.generate(tokens, **kwargs)
    try:
        import comfy.model_management as mm
        import comfy.ops as comfy_ops
    except Exception:
        return entry.clip.generate(tokens, **kwargs)  # 退化到原生路径
    device = entry.device
    inner.reset_clip_options()
    inner.set_clip_options({"layer": None})
    inner.set_clip_options({"execution_device": device})
    with mm.cuda_device_context(device), comfy_ops.use_quantized_matmul(inner, device):
        return inner.generate(tokens, **kwargs)


def count_image_embeds(tokens):
    """token 序列里 image 占位符的个数（用于判断视觉塔何时可以下卡）。"""
    total = 0
    try:
        for batch in tokens.values():
            for row in batch:
                for item in row:
                    if item and isinstance(item[0], dict):
                        total += 1
    except Exception:
        return 0
    return total


@contextlib.contextmanager
def release_vision_after_prefill(root, image_embeds, visual):
    """视觉塔只在 prefill 编码图像时用一次，编完立刻让它下卡，把 0.85GB 还给解码阶段。

    `Qwen35.preprocess_embed` 只在图像 embed 上被调用，且都发生在 decode 循环之前，
    所以按 image 占位符个数计数，最后一个编码完就撤。
    """
    if visual is None or int(image_embeds) <= 0:
        yield
        return
    previous = root.__dict__.get("preprocess_embed") if hasattr(root, "__dict__") else None
    original = root.preprocess_embed
    state = {"left": int(image_embeds)}

    def preprocess_embed(embed, device):
        out = original(embed, device)
        state["left"] -= 1
        if state["left"] <= 0:
            try:
                visual.to("cpu")
                import comfy.model_management as mm
                mm.soft_empty_cache()
                LOGGER.info("%s：视觉塔 prefill 用完已下卡，显存还给解码", NODE_DISPLAY_NAME)
            except Exception as exc:  # pragma: no cover - 仅环境异常
                LOGGER.warning("%s：视觉塔下卡失败：%s", NODE_DISPLAY_NAME, exc)
        return out

    root.preprocess_embed = preprocess_embed
    try:
        yield
    finally:
        if previous is not None:
            root.preprocess_embed = previous
        else:
            try:
                del root.preprocess_embed
            except AttributeError:
                pass


def _place_vision(entry, want_gpu):
    """视觉塔只在带图时占用显存（0.85GB bf16）。

    ⚠️ `visual.to("cuda")` 是**绕过 ComfyUI 显存管理**的裸分配：8GB 卡上权重 6.38GB +
    视觉塔 0.85GB 已经贴顶，不先按 ComfyUI 的方式腾地方就会踩到 `cudaErrorInvalidValue`
    （实测：带图跑第二次调用直接 CUDA 报错）。所以上卡前先 `free_memory(需要的字节)`，
    让 ComfyUI 按需卸载别的模型 / 清空缓存；下卡后清一次缓存把余量还给后续解码。
    """
    visual = entry.visual
    if visual is None or torch is None:
        return
    target = entry.device if (want_gpu and str(getattr(entry.device, "type", "")) != "cpu") else torch.device("cpu")
    try:
        current = next(visual.parameters()).device
    except StopIteration:
        return
    if current.type == target.type:
        entry.vision_on_gpu = target.type != "cpu"
        return
    if target.type != "cpu":
        try:
            import comfy.model_management as mm
            required = int(module_bytes(visual) * 1.05) + 128 * 1024 * 1024
            mm.free_memory(required, target)
        except Exception as exc:  # pragma: no cover - 仅环境异常
            LOGGER.warning("%s：为视觉塔腾显存失败：%s", NODE_DISPLAY_NAME, exc)
    visual.to(target)
    entry.vision_on_gpu = target.type != "cpu"
    try:
        import comfy.model_management as mm
        mm.soft_empty_cache()
    except Exception:
        pass
    LOGGER.info("%s：视觉塔已移到 %s（腾出后空闲显存 %.2fGB）", NODE_DISPLAY_NAME, target,
                _free_vram_gb(target))


# ============================== 节点 ==============================


class TextGenerateQwen21PromptNode:
    """本地 Qwen-Image-2.1 PE-I2I 提示词改写（W4A8 量化，8GB 显存特化）。"""

    CATEGORY = "YTmmi/text"
    DESCRIPTION = ('生成Qwen2.1提示词：用本地 Qwen-Image-2.1 PE-I2I（Qwen3.5-9B 微调 + W4A8 量化，'
                   '模型放 models/LLM）把提示词改写为 Qwen-Image 2.1 提示词，并可带参考图做「图像编辑」改写；'
                   '内置官方系统提示词原文（t2i 八步法 / edit 语言决策+ratio_follow 判定表），'
                   '参考原生 TextGenerateLTX2Prompt 的两段式输出（生成文本 / 思考内容，含思考预算），'
                   '针对 8GB 显存做静态独占加载、分块词表投影、视觉塔按需上显存、算子后端自适应与模型缓存')

    @classmethod
    def INPUT_TYPES(cls):
        # 下拉选项每次重新扫描（COMBO 动态选项约定）；空列表时用 ["") 占位，避免 Value not in list
        try:
            models = list_llm_models()
        except Exception:
            models = []
        return {
            "required": {
                "模型": (models or [""], {"default": models[0] if models else "",
                                          "tooltip": "models/LLM 下的量化权重（comfyui-quantized 格式的 .safetensors）"}),
                "提示词": ("STRING", {"default": "", "multiline": True,
                                      "placeholder": "输入要改写的提示词（可用中文）"}),
                "任务类型": ([TASK_AUTO, TASK_T2I, TASK_EDIT], {"default": TASK_AUTO,
                                                               "tooltip": "自动：接了参考图按「图像编辑」改写，否则按「文生图」"}),
                "最大长度": ("INT", {"default": 1024, "min": 1, "max": 32768,
                                     "tooltip": "最多生成的 token 数（不含提示词本身）。改写结果是 JSON，"
                                                "实测约需 300~400 token；默认 1024 足够，压到 256 会在 JSON 中间被截断"}),
                "采样模式": ([SAMPLING_ON, SAMPLING_OFF], {"default": SAMPLING_ON,
                                                           "tooltip": "off 时贪心解码（忽略种子）"}),
                "温度": ("FLOAT", {"default": 0.7, "min": 0.01, "max": 2.0, "step": 0.01}),
                "top_k候选数": ("INT", {"default": 64, "min": 0, "max": 1000}),
                "top_p累积概率": ("FLOAT", {"default": 0.95, "min": 0.0, "max": 1.0, "step": 0.01}),
                "min_p概率下限": ("FLOAT", {"default": 0.05, "min": 0.0, "max": 1.0, "step": 0.01}),
                "重复惩罚": ("FLOAT", {"default": 1.05, "min": 0.0, "max": 5.0, "step": 0.01}),
                # 与原生 TextGenerate 采样参数对齐（原生 presence_penalty 默认 0.0，等价于不启用；
                # 只有「重复惩罚」保持 1.05 时惩罚链本来就是激活的，故默认值不改变任何既有行为）
                "存在惩罚": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 5.0, "step": 0.01,
                                       "tooltip": "每出现一次就把该 token 的 logits 减掉这个值（原生 presence_penalty）；"
                                                  "0 = 不启用"}),
                # 官方 control_after_generate：前端自动生成「生成后控制」下拉，后端不参与种子推进
                "种子": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff,
                                 "control_after_generate": True,
                                 "tooltip": "旁边的「生成后控制」可让种子在每次生成后自动变化"}),
                "思考": ("BOOLEAN", {"default": False,
                                     "tooltip": "打开后模型先输出思考再给提示词（更慢，但便于核对）"}),
                "运行设备": ([DEVICE_AUTO, DEVICE_VRAM, DEVICE_RAM], {"default": DEVICE_AUTO,
                                                                      "tooltip": "自动：按打包体积判断能否独占显存；内存：6.4GB 权重全在内存（很慢，仅兜底）"}),
            },
            "optional": {
                "图像": ("IMAGE",),
                "思考预算": ("INT", {
                    "default": THINKING_BUDGET_DEFAULT, "min": 0, "max": 8192, "step": 16,
                    "tooltip": "仅「思考」打开时生效：思考最多用多少个 token，用满就强制结束思考块转入正式答案"
                               "（0 = 不限）。不设预算时模型可能把「最大长度」全花在思考上而返回空答案"}),
                "参考图最长边": ("INT", {"default": VISION_MAX_SIDE_DEFAULT, "min": 64, "max": 4096,
                                         "step": VISION_PATCH_MULTIPLE,
                                         "tooltip": "参考图缩放到该最长边，并取 32 的倍数（视觉塔 patch=16 × merge=2）"}),
                "系统提示词": ("STRING", {"multiline": True, "default": "", "forceInput": True,
                                          "tooltip": "留空则按「任务类型」使用内置的**官方提示词原文**"
                                                     "（t2i 约 9.9k 字符 / edit 约 17.7k 字符）；接一个精简版可以明显减少 prefill 时间"}),
                "词表分块行数": ("INT", {"default": HEAD_CHUNK_ROWS_DEFAULT, "min": 0, "max": 262144,
                                         "step": 4096,
                                         "tooltip": "词表投影分块行数（0 = 不分块）。显存紧张时保持默认；调小更省显存、略慢"}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("生成文本", "思考内容")
    FUNCTION = "generate"
    OUTPUT_NODE = False
    SEARCH_ALIASES = ["qwen", "提示词改写", "qwen-image", "2.1", "扩写", "本地大模型", "w4a8",
                      "qwen35", "prompt enhance"]

    def generate(self, **kwargs):
        prompt = kwargs.get("提示词", "")
        prompt = "" if prompt is None else str(prompt)
        if not prompt.strip():
            raise ValueError("{}：提示词不能为空".format(NODE_DISPLAY_NAME))

        model_name = kwargs.get("模型", "")
        model_path = resolve_model_path(model_name)
        if model_path is None:
            raise ValueError(
                "{}：未找到模型 {}，请把量化权重放到 models/LLM 目录（目录名大小写不敏感）".format(
                    NODE_DISPLAY_NAME, model_name))

        device_preference = kwargs.get("运行设备", DEVICE_AUTO)
        chunk_rows = int(kwargs.get("词表分块行数", HEAD_CHUNK_ROWS_DEFAULT) or 0)
        entry = load_qwen35_clip(model_path, device_preference=device_preference,
                                 head_chunk_rows=chunk_rows)

        image = kwargs.get("图像")
        has_image = image is not None
        task = kwargs.get("任务类型", TASK_AUTO)
        if task == TASK_AUTO:
            task = TASK_EDIT if has_image else TASK_T2I

        system_prompt = kwargs.get("系统提示词", "")
        system_prompt = "" if system_prompt is None else str(system_prompt).strip()
        if not system_prompt:
            system_prompt = QWEN21_EDIT_SYSTEM_PROMPT if task == TASK_EDIT else QWEN21_T2I_SYSTEM_PROMPT

        if has_image:
            image = _resize_for_vision(image, kwargs.get("参考图最长边", VISION_MAX_SIDE_DEFAULT))
        # 带图时要额外占 0.85GB 视觉塔：先按 ComfyUI 的账本腾地方，再把它搬上卡；
        # 不带图则确保视觉塔已下卡（把显存留给编码器）
        vision_bytes = module_bytes(entry.visual) if (has_image and entry.visual is not None) else 0
        ensure_encoder_residency(entry, extra_bytes=vision_bytes)
        _place_vision(entry, want_gpu=has_image)

        thinking = bool(kwargs.get("思考", False))
        budget = int(kwargs.get("思考预算", THINKING_BUDGET_DEFAULT) or 0)
        sampling = str(kwargs.get("采样模式", SAMPLING_ON)) != SAMPLING_OFF
        clip = entry.clip

        # 思考预算：软提示（让模型自觉简短）+ 硬截断（用满预算就强制 `</think>`）
        think_end_id = None
        force_close = None
        if thinking and budget > 0:
            system_prompt = with_thinking_hint(system_prompt, budget)
            think_end_id = _think_end_token_id(clip)
            if think_end_id is None:
                LOGGER.warning("%s：查不到 `</think>` 的 token id，思考预算只保留软提示",
                               NODE_DISPLAY_NAME)

        tokens = clip.tokenize(
            prompt, image=image, thinking=thinking, min_length=1, system_prompt=system_prompt)

        generate_kwargs = dict(
            do_sample=sampling,
            max_length=int(kwargs.get("最大长度", 1024)),
            temperature=float(kwargs.get("温度", 0.7)),
            top_k=int(kwargs.get("top_k候选数", 64)),
            top_p=float(kwargs.get("top_p累积概率", 0.95)),
            min_p=float(kwargs.get("min_p概率下限", 0.05)),
            repetition_penalty=float(kwargs.get("重复惩罚", 1.05)),
            presence_penalty=float(kwargs.get("存在惩罚", 0.0)),
            seed=int(kwargs.get("种子", 0)),
            mtp=False,
        )
        image_embeds = count_image_embeds(tokens) if has_image else 0
        with release_vision_after_prefill(entry.root, image_embeds, entry.visual if has_image else None):
            if think_end_id is not None:
                sampler = sample_token_with_thinking_budget(
                    entry.root.sample_token, think_end_id, budget)
                with temporary_sample_token(entry.root, sampler):
                    generated = generate_without_patcher(entry, tokens, **generate_kwargs)
            else:
                generated = generate_without_patcher(entry, tokens, **generate_kwargs)
        if has_image:
            _place_vision(entry, want_gpu=False)
        text = clip.decode(generated)

        # 与原生 TextGenerate 一致：思考块要么在生成文本里，要么被 max_length 截断而没有结束标记
        reasoning, closed, answer = text.partition("</think>")
        if not reasoning.lstrip().startswith("<think>") and not prompt.rstrip().endswith("<think>"):
            reasoning, closed, answer = "", "", text
        answer = answer.strip()
        if thinking and not closed and reasoning:
            LOGGER.warning("%s：思考块没有正常闭合（「最大长度」%s 可能被思考吃满），"
                           "建议调小「思考预算」或调大「最大长度」",
                           NODE_DISPLAY_NAME, kwargs.get("最大长度", 1024))
        if not answer and reasoning:
            LOGGER.warning("%s：答案为空而思考非空——「思考」打开时模型会先消耗 token，"
                           "请调大「最大长度」或调小「思考预算」", NODE_DISPLAY_NAME)
        return (answer, reasoning.replace("<think>", "", 1).strip())


NODE_CLASS_MAPPINGS = {
    "TextGenerateQwen21Prompt": TextGenerateQwen21PromptNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TextGenerateQwen21Prompt": NODE_DISPLAY_NAME,
}

__all__ = [
    "TextGenerateQwen21PromptNode",
    "LoadedModel",
    "Placement",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "HEAD_CHUNK_ROWS_DEFAULT",
    "THINKING_BUDGET_DEFAULT",
    "EDIT_INSTRUCTION_CUE",
    "VISION_MAX_SIDE_DEFAULT",
    "QWEN21_T2I_SYSTEM_PROMPT",
    "QWEN21_EDIT_SYSTEM_PROMPT",
    "sample_token_with_thinking_budget",
    "with_thinking_hint",
]
