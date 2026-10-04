# Anima 构图词汇表（Composition Vocabulary）

配套 `SKILL.md`。分两部分：**可直接进提示词的英文词汇表**（景别 × 机位 × 朝向 × 位置 × 分层 × 取景装置），
以及**按产出类型给的构图配方**。标 † 的词优先放进自然语言句子；其余可作 `general` 段标签。

## 0. 使用规则

1. 构图词一次给 **4~7 个**。少于 4 个画面没有主张，多于 7 个会互相争夺权重。
2. 同一维度**只给一个**：景别只能有一个主景别，机位不能同时 `from above` 和 `from below`。
3. 明显互斥的组合不要同写，模型会随机挑一个：

| 互斥组合 | 后果 |
|---|---|
| `close-up` / `portrait` + `full body` | 一会半身一会全身，批量出图时随机漂移 |
| `centered` + `off-center` | 主体位置不稳定 |
| `from above` + `from below` | 机位翻转 |
| `wide shot` + `detailed background` + 主体细节堆满 | 背景必然抢焦 |
| `dutch angle` + `symmetric composition` | 对称骨架被倾斜破坏 |

## 1. 景别（shot size）

| 英文词 | 覆盖范围 | 适用 |
|---|---|---|
| `portrait` | 头肩 | 头像、表情、眼神戏 |
| `close-up` † | 面部特写 | 情绪爆点、瞳孔细节 |
| `upper body` | 腰以上 | 立绘、交互感、服装上半身 |
| `cowboy shot` | 大腿以上 | **通用性价比最高** |
| `full body` | 全身含脚 | 全身立绘、服装全貌 |
| `wide shot` | 人物 + 大环境 | 只有场景是主体时才用 |
| `feet out of frame` | 显式切脚 | 与 `cowboy shot` 同源，避免尴尬裁切 |

## 2. 机位与角度（camera angle）

| 英文词 | 效果 | 风险 |
|---|---|---|
| `eye level` † | 平视，中性 | 平淡，需要靠位置/分层补张力 |
| `from below` | 仰视，压迫感、英雄感 | 下半身放大、头变小 |
| `from above` | 俯视，弱小、可爱、孤独 | 容易显头大身短 |
| `dutch angle` | 倾斜，紧张、动感 | 与对称构图冲突；表格类禁用 |
| `foreshortening` † | 透视缩短 | 需要明确朝向，否则肢体崩 |
| `perspective` † | 强调透视 | 太泛，最好跟具体词一起用 |

## 3. 朝向与视线（view direction）

| 英文词 | 含义 |
|---|---|
| `from front` | 正面朝向观众 |
| `three-quarter view` † | 四分之三侧，最耐看 |
| `from side` / `profile` † | 90° 侧面 |
| `from behind` | 背对，常配 `looking back` |
| `looking at viewer` | 与观众对视 |
| `looking away` / `looking to the side` | 视线离画，留白方向由此决定 |
| `looking back` | 回头看，回头率最高的姿势词 |
| `head tilted` † | 歪头，配合可爱/疑惑 |

## 4. 主体位置（placement）

| 英文词 | 说明 |
|---|---|
| `centered` | 居中，对称与仪式感 |
| `off-center` † | 偏心，最自然的默认 |
| `left side` / `right side` | 明确左右，多角色必备 |
| `upper left` / `lower right` † | 精确到角，海报留白时用 |
| `symmetry` | 对称构图骨架 |
| `rule of thirds` † | 三分法，用句子写更稳 |

## 5. 分层与景深（layering & depth）

| 英文词 | 作用 |
|---|---|
| `foreground` | 最近一层，往往放虚化物 |
| `middle ground` | 主体所在地 |
| `background` | 环境层 |
| `depth of field` | 前后分离的核心词 |
| `blurry background` | 直接压低背景细节 |
| `blurry foreground` | 前景虚化，做纵深框 |
| `bokeh` | 光斑，夜景/逆光加分 |
| `backlighting` / `rim light` † | 主体边缘光，把主体从背景里拔出来 |
| `silhouette` | 剪影，强对比构图 |

## 6. 取景装置（framing device）

`framed` †、`picture frame`、`window`、`doorway`、`arch`、`torii gate`、`branch`、`curtain`,
`vignette`、`border`、`letterboxed` †、`polaroid` †。

用法：竖构图叠加一层框最有效；横构图叠两层以上会显得堵。框本身也要分层
（框在 `foreground` 且虚化，主体在 `middle ground` 实焦）。

## 7. 按产出类型的构图配方

### 7.1 头像 / 半身立绘

```text
portrait, eye level, centered, depth of field, blurry background, simple background
```
自然语言：主体占画幅高度一半以上，背景只留色块与光。

### 7.2 海报 / KV

```text
cowboy shot, from below, off-center, left side, foreground <物件>, blurry background, depth of field, backlighting
```
自然语言必须写清负空间位置与用途：`a wide empty band in the upper third for the title` †。
KV 与普通立绘不是同一套：主体更偏、留白更大、边框可选、对比更强。

### 7.3 群像

```text
3girls, multiple girls, upper body, centered, foreground, background, depth of field
```
主位 `upper body` + `foreground`，陪位 `full body` + `background`；高低错落；每人剪影区分。

### 7.4 场景主导

```text
wide shot, from above, centered, middle ground, background, depth of field, atmospheric perspective †
```
人是尺度参照，可以小；背景细节量可以超过人物，但要靠 `atmospheric perspective`（远近空气感）分层。

## 8. 构图自检清单

- [ ] 景别与用途匹配（封面用 `wide shot` 是错的）；
- [ ] 同一维度只有一个词，没有写互斥组合；
- [ ] 视觉层级至少用了两个杠杆（景别差 / 前后差 / 细节量差）；
- [ ] 前景 / 中景 / 背景至少写了两段；
- [ ] 负空间位置与视线方向一致；
- [ ] 背景标签量不超过全文三分之一；
- [ ] 构图词全部在 `general` 段，没有混进 quality / meta / safety；
- [ ] 正文里没有宽高比、分辨率、种子、CFG、步数、模型名；
- [ ] 与风格 skill 交付的风格子句不冲突（例如极简风格不要叠 `absurdres` 级别的细节词）。
