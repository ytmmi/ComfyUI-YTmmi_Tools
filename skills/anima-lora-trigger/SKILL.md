---
name: anima-lora-trigger
description: Place LoRA trigger words and prompt weights correctly in Anima prompts, including character LoRAs, style LoRAs, multi-LoRA role separation, and the higher weight values Anima needs compared with SDXL. Use when the user supplies trigger words, trains or tests Anima LoRAs, or needs weighted tags such as (chibi:2).
version: 1.1.0
---

# Anima LoRA 触发词与权重

处理 Anima 提示词中的**权重语法**与**触发词（trigger word）**摆放。
Anima 的权重语法与 SDXL 相同，但**需要更大的数值**才能看到效果。

读 `references/anima-weight-syntax.md` 获取权重语法细节、组合配方与排障表。

## 输出契约

与 `anima-prompt-format` 一致：**默认只输出正面提示词正文**；只在用户明确要求负面词、或需要说明与负面词冲突（如 `artist name`）时，才追加 `Negative prompt` 段。

只输出 Anima 提示词正文：

```text
[quality/meta/year/safety 标签], [人数标签], [角色], [作品], [画师], [general 标签]. [1~3 句英文自然语言描述]
```

- **默认只出正面提示词**：用户没提负面词、也没说自己那边没有负面词时，**不要输出任何负面提示词**，
  也不要有 `Positive prompt` 之类的标题行——直接给可以粘贴进生成节点的正文；
- 只在下列情况才追加负面提示词：① 用户明确要求负面词 / 负面提示词 / negative prompt；
  ② 用户表示自己那边没有设置负面词、需要一并给出；③ 该 skills 的流程本身必须成对交付（见下）。
  此时改用两段式（负面词按对应小节裁剪，不要改变默认格式）：

  ```text
  Positive prompt
  [正面提示词正文]

  Negative prompt
  [裁剪后的负面词]
  ```

- 默认格式**不带标签行**：不加 `Positive prompt` 标题、不加代码块围栏、不加前言与结尾建议；
  输出要能被用户直接抠进 ComfyUI 的提示词框；
- **不输出任何参数段**：不附 `Suggested settings`、不附宽高比 / 分辨率 / 步数 / CFG /
  采样器 / 种子建议——即使被问也只用一句话说明「这些由工作流设置决定」，不要写进正文；
- 触发词写进**提示词正文**，放在它作用的角色/风格附近；
- **不要**在提示词里写 LoRA 文件名、LoRA 强度数字（`<lora:xxx:0.8>` 属于工作流接线，不属于提示词）；
- **不输出任何强度或参数数值**（不附 `Suggested settings`）：LoRA 强度与生成参数都是
  工作流侧设置，被问到时只用一句话说明，不要写进提示词或附在末尾；
- 用户没给触发词时**绝不编造**触发词，直接说明需要他提供。

## 硬规则

1. **权重值要比 SDXL 大得多**：官方示例就是 `(chibi:2)`。SDXL 常见的 `(x:1.2)` 在 Anima 上几乎看不出差别。
   建议区间：常规强调 `2` 起、明显强调 `2.5~3`、强强调 `3~4`；超过 5 往往过曝、变形或烧图。
   全文**加权标签总数 ≤4 个**，把额度优先给最需要压过其它因素的那一路。
2. **触发词保持逐字原样**：大小写、下划线、空格全部照抄，不要"顺手规范化"。
   Danbooru 的空格规则只适用于普通标签，**不适用于用户提供的触发词**。
3. **触发词要贴近它作用的对象**：
   - 角色 LoRA → 紧跟人数标签之后、角色名之前；
   - 风格 LoRA → 放在风格/媒介标签区（质量标签之后、通用标签之前）；
   - 双 LoRA 时用自然语言把两者角色说清（`the character trigger defines identity while the style trigger defines rendering`）。
4. **触发词不要和同义标签打架**：LoRA 已经定义了某个特征时，不要再堆一堆同义词标签去"加强"它。
5. **多 LoRA 时不要混写**：每个触发词各管一件事（身份 / 风格 / 服装 / 背景），错位会让身份漂移。
6. **`artist name` 负面会压掉画师风格**——用画师风格 LoRA 或画师标签时，负面里要删掉 `artist name`。

## 工作流

1. **收集触发词**：向用户要（角色 LoRA / 风格 LoRA / 服装 LoRA 各是什么触发词）。缺就明说，不要猜。
2. **判定 LoRA 角色**：身份类、风格类、服装道具类、背景类——角色决定摆放位置。
3. **摆放位置**：

```text
[质量/元信息/安全] [人数] [角色 LoRA 触发词] [角色名] [作品] [画师] [风格 LoRA 触发词] [通用标签]. [自然语言描述]
```

4. **加权重**：只对**确实需要强调**的标签加权重（主体身份、关键风格）。默认不加，加了要能说出理由。
5. **冲突检查**：触发词与普通标签是否重复？权重总和是否过大？是否与负面词互相抵消？
6. **写出自然语言区**：用散文把触发词的角色说清，帮助模型归位（尤其多 LoRA）。
7. **负面**：删掉 `artist name`（若要画师风格），按需保留解剖类负面。

## 示例

输入：`角色触发词 sakura_alt，风格触发词 watercolor_wash，想要水彩感的樱，风格再强一点`

```text
Positive prompt
masterpiece, best quality, safe, 1girl, solo, sakura_alt, Sakura, short pink hair, green eyes, school uniform, (watercolor_wash:3), watercolor, soft bleeding pigment edges, paper texture, full body, standing under a blooming cherry tree, warm spring light. The character trigger keeps Sakura's identity and uniform consistent, while the style trigger drives the rendering toward loose watercolor washes with visible paper grain and soft pigment blooms.

Negative prompt
worst quality, low quality, lowres, blurry, jpeg artifacts, bad anatomy, bad hands, extra fingers, missing fingers, extra limbs, deformed, duplicate face, crossed eyes, messy lineart, watermark, signature, username, logo, unrelated text
```

> 注意这里负面**没有** `artist name`（用户要的是风格化渲染），也**没有**写 LoRA 强度。

> 模型版本匹配：**Anima LoRA 用 Anima-Base 训练与推理**，挂到 Aesthetic/Turbo 上容易漂——
> 这是工作流侧的注意点，**不要写进提示词，也不要附强度数值**。

## 边界

- 标签顺序 / 质量前缀 / 参数与提示词分离 → 用 `anima-prompt-format`；
- 要选画师风格而不是 LoRA 风格 → 用 `anima-prompt-artist`；
- LoRA 的加载、接线、开关属于 ComfyUI 工作流操作，本 skills 不负责。
