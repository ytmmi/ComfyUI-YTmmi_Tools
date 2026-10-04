# Anima 负面词与质量前缀表（Negative Tables）

配套 `SKILL.md`。三块内容：**版本 → 前缀矩阵**、**按失败域分组的负面词表**（每域带"何时加 / 何时删"）、
**可见瑕疵 → 该加哪些词**的诊断对照，末尾附冲突速查与交付清单。

## 1. 版本 → 前缀矩阵

| 版本 | 正向质量前缀（逐字） | 负向 score 端 | 用错的症状 |
|---|---|---|---|
| 裸 Base v1.0 | `masterpiece, best quality, score_7, safe, ` | 保留 `score_1, score_2, score_3` | 正向写 `score_9, score_8` → 过冲：塑料感、过曝、细节糊成一片 |
| Anima-Aesthetic | `masterpiece, best quality, safe` | **全部删除** | 塞回 `score_*` → 画面被推向 slop，微调收益被抵消 |
| Anima-Turbo | `masterpiece, best quality, safe` | **全部删除** | 同上；Turbo 本身多样性就低，再叠 score 会更僵 |
| PonyV7 系美学 LoRA 栈 | `masterpiece, very aesthetic, best quality, score_9, score_8, highres, absurdres, newest, year 2025` | 保留 `score_1, score_2, score_3`（必要时补 `score_4, score_5`） | 塞 `score_7` → 削弱 LoRA 效果；不写美学词 → LoRA 白挂 |
| 未知 / 未说明 | `masterpiece, best quality, safe` | 删除（两端都收益不明） | 猜错版本比不猜更糟：不输出参数段，说明假设即可 |

> 记忆点：`score_*` 是**版本绑定**的标签。写它之前先回答"我跑的是哪个版本"，答不出来就别写。

## 2. 按失败域分组的负面词表

用法：官方默认骨架**始终在场**，再按本次需求挑 1~3 组贴上去。

```text
worst quality, low quality, lowres, blurry, jpeg artifacts, chromatic aberration
```

### 2.1 基础质量 / 伪影（几乎总在）

`worst quality`, `low quality`, `lowres`, `jpeg artifacts`, `chromatic aberration`, `noisy` †,
`oversaturated` †, `banding` †

- 何时加：任何一张图，作为骨架；
- 何时删：用户明确要**粗糙质感 / 复古噪点 / 低保真**时，删 `jpeg artifacts`、`noisy`。

### 2.2 解剖（anatomy）

`bad anatomy`, `bad proportions`, `extra limbs`, `missing limbs`, `extra arms`, `extra legs`,
`deformed`, `mutated hands`, `fused fingers`

- 何时加：全身、动态姿势、多人重叠、大幅透视；
- 何时删：Q 版 / chibi（`bad proportions` 会把比例往写实拉）、变形生物与机械体（`extra limbs` 会压掉
  合法的多余肢体）。

### 2.3 脸（face）

`duplicate face`, `extra face`, `cross-eyed`, `distorted face`, `disfigured`, `mismatched eyes`

- 何时加：面部特写、多人同框；
- 何时删：要异色瞳时删 `mismatched eyes`；三视图 / 表情表里出现多张脸是**正常**的，慎用 `duplicate face`。

### 2.4 手（hands）

`bad hands`, `extra fingers`, `missing fingers`, `fused fingers`, `too many fingers`

- 何时加：手在画面里、持物、手部特写；
- 何时删：手不在画面里（省 token）；手部是画面重点时可保留最精的三四个，不要写满。

### 2.5 角色一致性与表格（character / sheet）

`merged characters`, `fused characters`, `inconsistent character`, `outfit mismatch`,
`inconsistent hair color`, `inconsistent eye color`, `wrong attribute`, `color bleeding`

- 何时加：多角色同框、三视图、表情表、换装组；
- 何时删：**表格里慎用 `duplicated character`**——表格本来就要重复画同一角色，它可能把应该重复的格子
  一起压掉；单张多角色场景里它才是有用的。

### 2.6 分区 / 局部（regional & inpaint）

`color bleeding`, `seam line`, `visible mask edge`, `patchy repair`, `mismatched lighting`,
`mismatched style`, `out of place`

- 何时加：分区提示词、局部重绘、多区域拼合；
- 何时删：整图一次生成时用不上；完整做法交 `anima-prompt-regional`。

### 2.7 文字（text）

`unrelated text`, `garbled text`, `misspelled text`, `extra letters`, `floating text`, `caption` †

- 何时加：不想要画面里出现任何文字；
- 何时删：**用户要招牌 / 标题 / 名牌时整组删掉**，最多留 `garbled text, misspelled text` 保证字迹清晰；
  Anima 文字渲染弱，长文本本来就要后期加。

### 2.8 水印 / 署名（watermark）

`watermark`, `signature`, `username`, `logo`, `twitter username`, `patreon username`,
`web address`, `copyright name`, `artist name`

- 何时加：要干净的原创观感、平台水印很讨厌时；
- 何时删：**要画师标签效果时必须删 `artist name`**；`signature` 与画师署名的边界按用户要求定。

### 2.9 构图 / 裁切（framing）

`bad crop`, `out of frame`, `cut off`, `cluttered background`, `extra characters`

- 何时加：立绘不能切脚、单角色不能多出人、海报要干净；
- 何时删：正向写了 `feet out of frame` 就别加 `bad crop`；群像 / 人群场景删 `extra characters`
  （否则路人被压掉）；要细节丰富的背景时删 `cluttered background`。

### 2.10 safety

`safe` / `sensitive` / `nsfw` / `explicit` 是**正向的选择**；负向只做次要辅助。

- 正向选了 `safe` → 负向可以加 `nsfw, explicit` 作为辅助，但别指望它替代正向标签；
- 正向选了 `sensitive` / `nsfw` → **负向里绝不能出现同名或相反的 safety 词**；
- 正向里**只写一个** safety 标签，多个并存等于自相矛盾。

## 3. 诊断对照：看到瑕疵 → 加这些词

| 可见瑕疵 | 优先补的负面词 | 同时检查正向 |
|---|---|---|
| 手指数量不对、手糊成团 | `bad hands, extra fingers, missing fingers, fused fingers` | 手部姿势词是否太复杂 |
| 多出一条手臂 / 腿 | `extra limbs, extra arms, extra legs, bad anatomy` | 姿势与构图是否冲突 |
| 脸歪、眼睛不对称 | `distorted face, cross-eyed, disfigured` | 景别是否过紧（特写下更容易崩） |
| 两个人融成一团 / 换头 | `merged characters, fused characters, wrong attribute` | 人数标签、每人外观与位置（`anima-prompt-character`） |
| 三视图里角色不像同一个人 | `inconsistent character, outfit mismatch, inconsistent hair color` | 身份锚点是否逐字复用 |
| 画面里冒出无关文字 | `unrelated text, garbled text, extra letters` | 是否要招牌文字 |
| 角落有签名 / 水印 | `watermark, signature, username, web address` | 是否要画师风格（决定 `artist name` 去留） |
| 背景杂乱抢焦 | `cluttered background` | 景深与背景标签量（`anima-composition-optimize`） |
| 肢解式裁切 | `bad crop, out of frame` | 景别是否匹配用途 |
| 局部重绘有接缝 | `seam line, visible mask edge, mismatched lighting` | 遮罩范围（`anima-prompt-regional`） |
| 画面塑料感、过曝、细节糊 | **先核对版本**：Aesthetic/Turbo 上是否误写了 `score_*` | 质量前缀矩阵（第 1 节） |
| 风格像被"洗掉"了 | 删除 `artist name` | 画师标签是否带 `@`（`anima-prompt-artist`） |

## 4. 冲突速查（负面词 vs 正向需求）

| 正向有 | 负面删 / 改 |
|---|---|
| `@` 画师标签 | `artist name` |
| `depth of field` / `blurry background` | `blurry` → `blurry subject` |
| 招牌 / 标题 / 名牌文字 | `unrelated text`, `english text`, `text` |
| Q 版 / chibi | `bad proportions` |
| 异色瞳 | `mismatched eyes` |
| 怪物 / 机械 / 多臂 | `extra limbs`, `extra arms`, `mutated hands` |
| 三视图 / 表情表 | `duplicated character`, `multiple views` |
| 人群 / 群像 | `extra characters` |
| `feet out of frame` | `bad crop` |
| 夜景 / 暗调 | `dark`, `underexposed` 类词 |
| `nsfw` / `sensitive` | 同名 safety 词 |

## 5. 交付前清单

- [ ] 版本有依据，或明确使用安全档且**没有输出参数段**；
- [ ] `score_*` 与该版本匹配（Base 正向 `score_7`；Aesthetic/Turbo 正负都无）；
- [ ] 负面 = 官方骨架 + 1~3 组，没有堆成几十个词；
- [ ] 做过冲突速查，没有与请求对抗的词；
- [ ] 正向 safety 标签只有一个，且与负向自洽；
- [ ] 正文里没有分辨率、宽高比、种子、CFG、步数、模型名、LoRA 文件名；
- [ ] 所有 score 标签保留下划线，其余标签小写 + 空格分词。
