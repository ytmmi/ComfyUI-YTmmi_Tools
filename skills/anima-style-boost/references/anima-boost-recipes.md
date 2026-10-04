# Anima 增强配方（Boost Recipes）

`anima-style-boost` 的档位表与逐轴标签集。所有条目为**英文小写**，可直接追加到提示词的 general 区段。

## 0. 三条铁律

1. **风格优先**：本文件的标签只能强化已经选定的风格，不能替换它。风格未定 → 先走 `anima-style-control`。
2. **dropout 规则**：Anima 用随机标签丢弃训练，同义词堆叠会稀释语义，不会变强。每层 ≤3 个，同义只留一个。
3. **一次 1~2 层**：六层同时加＝over-seasoning，结果是"通用高完成度 slop"，风格反而更模糊。

## 1. Boost ladder（轻 / 中 / 强）

### Light（3~5 个）—— Aesthetic / Turbo 默认档

```text
clean lineart, soft shading, rim light, detailed background, depth of field
```

适用：只差一点完成度；或模型本身已做过美学调优，只需补结构与光向。

### Medium（8~12 个）—— 裸 Base 平图的标准档

```text
clean lineart, cel shading, soft shading, layered shading,
vibrant colors, warm color palette,
backlighting, god rays,
detailed background, atmospheric perspective, depth of field
```

适用：要出可交付立绘/插图；风格仍保持原样，只是完成度上来。

### Strong（14~18 个）—— KV / 海报级

```text
clean lineart, sharp lines, cel shading, soft shading, layered shading, ambient occlusion,
vibrant colors, cohesive palette, high contrast,
directional lighting, rim light, backlighting, god rays, bloom,
detailed background, intricate background, atmospheric perspective, depth of field, detailed
```

适用：用户明确要 KV / 主视觉，并接受风格被推得更精致。**风险**：背景会抢主体，必须配 `depth of field`
和负面 `busy background, cluttered`。

## 2. 逐轴标签集（按需取用，不要全取）

### 2.1 线 lineart

| 目标 | 标签 | 备注 |
|---|---|---|
| 干净现代 | `clean lineart`, `sharp lines`, `defined edges` | 与 `thick outlines` 二选一 |
| 漫画感 | `thick outlines`, `bold lines` | 与 `lineless` 互斥 |
| 无主线 | `lineless` | 厚涂/概念图用 |
| 草稿感 | `rough lines`, `sketch lines` | 配合 `pencil sketch`，**不要**再加 `clean lineart` |
| 修复发毛 | `messy lineart` 放**负面** | 比正面加 `clean lineart` 更直接 |

### 2.2 上色 shading

`soft shading` `layered shading` `ambient occlusion` `gradient shading` `hard shadows` `soft shadows`
`subsurface scattering`（半写实厚涂用）`cel shading` `flat color` `airbrush`

- `soft shading` + `layered shading` 是平图最有效的两词；
- `ambient occlusion` 加体积感，但过量会让画面发脏；
- `cel shading` 与 `soft shading` 可以共存（现代立绘常见），但**不要**再加 `painterly`。

### 2.3 配色 color design

`vibrant colors` `color contrast` `cohesive palette` `warm color palette` `cool color palette`
`muted colors` `pastel palette` `high contrast` `complementary colors` `limited palette`

- 一次只选**一个方向**：`vibrant colors` 与 `muted colors` 互斥；`warm` 与 `cool` 互斥；
- `limited palette` 适合复古/水墨/赛璐璐；与 `vibrant colors` 同时出现会互相抵消。

### 2.4 光照 lighting

`directional lighting` `rim light` `backlighting` `god rays` `dappled sunlight` `bloom` `lens flare`
`volumetric lighting` `soft lighting` `dramatic lighting` `chiaroscuro` `studio lighting`

- 光照是"平图"最短的补药：加一个方向 + 一个边缘光，立体感立刻出来；
- `dramatic lighting` / `chiaroscuro` 会整体压暗画面，日常题材慎用；
- `bloom` / `lens flare` 过量＝廉价感，base 增强里最多留一个。

### 2.5 背景 background

`detailed background` `intricate background` `dense foliage` `background detail` `atmospheric perspective`
`depth of field` `blurry background` `bokeh` `scenery` `wide shot`

- `detailed background` + `depth of field` 是"背景有料但主体清楚"的标配；
- 主体是重点时用 `blurry background` / `bokeh` 而不是继续加背景标签；
- `scenery` 会把背景推成风景主体，人物题材慎用。

### 2.6 细节密度 detail density

`detailed` `intricate details` `fine details` `textured shading` `fabric folds` `detailed armor`

- 这一层**只留 1~2 个**，它是最容易触发 slop 的一层；
- `detailed` 与 `intricate details` 同义，**只写一个**；
- 更好的做法是把细节写到具体对象上（`fabric folds`、`detailed armor`），而不是写泛化的 `detailed`。

## 3. 增强过头时的负面兜底

```text
oversaturated, hdr, overexposed, blown out highlights, plastic texture, glossy skin,
over-sharpened, noisy, cluttered, busy background, washed out, muddy colors
```

| 症状 | 负面 |
|---|---|
| 颜色发腻、像开 HDR | `oversaturated, hdr, plastic texture` |
| 高光死白 | `overexposed, blown out highlights` |
| 皮肤塑料感 | `glossy skin, plastic texture` |
| 背景喧宾夺主 | `busy background, cluttered` |
| 整体发灰发脏 | `muddy colors, washed out` |
| 过度锐化噪点 | `over-sharpened, noisy` |

**反例**：不要用 `flat color` 当"治平图"的负面词——正面若含 `cel shading`，两者互相抵消。
治平图只能靠加法（`soft shading, layered shading, rim light`）。

## 4. 按模型版本分档

| 版本 | 默认档 | 可以加 score_* 吗 | 特别提醒 |
|---|---|---|---|
| **Anima-Base v1.0** | medium | 可以（`score_7`） | 默认风格朴素，是最需要 boost 的版本 |
| **Anima-Aesthetic** | light | **不可以**，正负都不要 | 训练时已剥离质量标签，堆美学形容词会过冲 |
| **Anima-Turbo** | light | **不可以** | 蒸馏版，对比与饱和已偏高，别再加 `vibrant colors` |
| PonyV7 系美学 LoRA 工作流 | light~medium | 用 LoRA 自己的前缀（`score_9, score_8`） | `score_7` 会削弱 LoRA；触发词见 `anima-lora-trigger` |

### Aesthetic / Turbo 专项

- **不要**加 `score_*`、`very aesthetic`、`beautiful`、`masterpiece` 之外的美学词堆；
- 它们的 boost 重点在**结构信息**：光照方向（`directional lighting, rim light`）、
  背景密度（`detailed background, depth of field`）、线稿清晰度（`clean lineart`）；
- 想"更鲜艳/更精致"是反方向操作：这两个版本已经在美学分布上收敛，继续推只会过曝；
- 负面优先 `overexposed, blown out highlights, over-sharpened, plastic texture`。

### 裸 Base 专项

- 保留 `masterpiece, best quality, score_7, safe`；
- 平图的根因通常是**没有线稿描述 + 没有阴影层次 + 没有光向 + 背景空**，按 2.1→2.5 顺序补；
- 补完仍平 → 检查是不是 `(xxx:1)` 这类过低权重（Anima 的常规档是 `:2` 起，照抄 SDXL 的
  `1.3` / `1.4` 基本看不出效果）。

## 5. 快速对照：症状 → 最小处方

| 症状 | 最小处方（light 档） |
|---|---|
| 线稿糊 | 负面 `messy lineart` + 正面 `clean lineart` |
| 像贴纸 | `soft shading, layered shading` |
| 颜色脏 | `cohesive palette, color contrast` |
| 没有立体感 | `directional lighting, rim light` |
| 背景空 | `detailed background, depth of field` |
| 主体被背景吃掉 | 正面 `rim light, depth of field` + 负面 `busy background, cluttered` |
| 整体廉价发亮 | 负面 `oversaturated, hdr, plastic texture` |
