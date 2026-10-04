# Anima 提示词体检表（Prompt Checklist）

`anima-prompt-optimize` 的可打印检查表。按**严重度顺序**从上往下修；每一行都是
`坏写法 → 好写法` 的对照，可直接照抄。

## 0. 严重度分级

| 级别 | 含义 | 不修的后果 |
|---|---|---|
| **S1 阻断** | 语法非法、版本前缀错误、safety 缺失 | 出图完全跑偏，或对 Aesthetic/Turbo 反向削弱 |
| **S2 结构** | 区段顺序错、人数缺失、正负冲突 | 主体数量错、风格撕裂、两边指令抵消 |
| **S3 效果** | 冗余同义堆叠、抽象形容词、caption 过短 | 画面变"通用 slop"、随机内容、不稳定 |
| **S4 打磨** | 权重偏低、细节词泛化、标点与格式 | 强度不足、语义被稀释 |

## 1. 逐字保留清单（先抄下来，全程一个字都不许动）

```text
[ ] 角色名 / 作品名 / 专有名词
[ ] @ 画师标签
[ ] 画面内可见文字（招牌、标题、必杀技名、非英文文案、符号）
[ ] LoRA 触发词（可能长得像乱码，不要"修正"）
[ ] 用户显式指定的 safety 等级
[ ] 用户显式给出的服装 / 道具 / 颜色 / 人数 / 显式否定项
```

> **禁止**新增用户没给过的画师名、LoRA 名、角色名、作品名。编错这些比留空更糟。

## 2. S1 阻断级：合法性与版本

| 坏写法 | 好写法 | 说明 |
|---|---|---|
| `long_hair` `blue_eyes` `looking_at_viewer` | `long hair` `blue eyes` `looking at viewer` | 多词标签用空格；下划线只属于 score 标签 |
| `score 7` | `score_7` | score 标签唯一保留下划线 |
| `score_9, score_8`（Aesthetic / Turbo） | 全部删除 | 这两个版本训练时已剥离质量标签，堆 score 会过冲 |
| `score_7`（挂了 PonyV7 系 LoRA） | 换成该 LoRA 的质量前缀 | `score_7` 会削弱 LoRA |
| `Long Hair` `MASTERPIECE` | `long hair` `masterpiece` | 标签区全小写 |
| `nnn yryr` | `@nnn yryr` | 画师标签必须带 `@`，否则效果极弱 |
| `{{chibi}}` `chibi::2` `(chibi)` | `(chibi:2)` | Anima 权重需要比 SDXL 更高 |
| `(mid-air:1.1)` | `(mid-air:2)` | 过低权重等于没写（Anima 常规 `:2` 起，强强调 `:3~5`） |
| 缺 safety | 补 `safe` / `sensitive` / `nsfw` / `explicit` | safety 段必写，按内容判定 |
| `a girl or a boy` / `maybe raining` | 删备选，只留最终画面 | 备选表述会让模型平均化 |

## 3. S2 结构级：顺序、人数、冲突

| 坏写法 | 好写法 | 说明 |
|---|---|---|
| `1girl, long hair, quality, safe` | `masterpiece, best quality, safe, 1girl, long hair` | 区段顺序：质量/meta/年/safety → 人数 → 角色 → 作品 → 画师 → general |
| 单角色无人数标签 | 加 `1girl` / `1boy` / `1other` + `solo` | 缺人数会随机出人数 |
| `1girl, 1girl` 或 `2girls` 配单人描述 | 与实际人数对齐 | 人数与描述必须一致 |
| `cel shading, photorealistic` | 保留 `cel shading`，写实词移入负面 | Anima 不做写实 |
| `painterly, flat cel shading` | 只留一个主导渲染 | 两个平级渲染互相打架 |
| `monochrome, vibrant colors` | 二选一 | 直接互斥 |
| `lineless, thick outlines` | 二选一 | 一个没线一个强调线 |
| `year 2005, newest, absurdres` | 年代与清晰度对齐 | 复古意图与高清晰意图相反 |
| 正面含 `motion blur`，负面也含 `motion blur` | 删负面那个 | 自相矛盾会让两边都失效 |
| Danbooru 写法与 Gelbooru 冲突 | 用 Gelbooru 版本 | 官方推荐 |
| 标签说 `cel shading`，caption 说 "thick visible brush strokes" | 二者取一，按用户意图 | 标签与自然语言必须一致 |

## 4. S3 效果级：冗余与具体性

| 坏写法 | 好写法 | 说明 |
|---|---|---|
| `masterpiece, best quality, ultra detailed, highly detailed, 8k, absurdres` | `masterpiece, best quality`（+ 版本匹配的 score） | 同义质量词堆叠会稀释 |
| `detailed, intricate details, fine details` | 只留一个 | dropout 训练下同义不加分 |
| `aesthetic, very aesthetic, beautiful` | 只留一个 | 同上 |
| `long hair, Long Hair` | 删一个 | 大小写变体是重复 |
| 只有名词堆叠、无 caption | 补 1~3 句英文最终画面描述 | 纯自然语言至少 2 句 |
| caption 只有 1 句 | 扩到 2 句以上 | 过短会出意外内容 |
| `cool` `nice` `beautiful` `amazing` | 译成可执行决策或删除 | 抽象形容词不可执行 |
| `a girl, then she turns around` | 去掉时序词，写最终画面 | 不要写"生成过程" |
| 多角色只列名字 | 每个角色补发色/发型/瞳色/服装 | 否则角色串味 |

## 5. S4 打磨级

| 坏写法 | 好写法 | 说明 |
|---|---|---|
| 泛化 `detailed` | `detailed armor` / `fabric folds` | 细节写到具体对象上 |
| 标签区末尾混着 `safe` | `safe` 回到第一区段 | 区段内顺序随意，区段间不行 |
| 逗号与句号混用 | 标签区用逗号，caption 前用句号 | 让模型分清标签与自然语言 |
| 权重超过 `2.5` | 回收 1.2~1.6 区间 | 过高权重会烧结构 |

## 6. 扩写顺序（4 词级 → 可用提示词）

```text
1 合法性 + 区段顺序
2 safety + 与版本匹配的质量前缀
3 人数标签（1girl / 1boy / solo）
4 主体身份细节（发色、发型、瞳色、服装、道具）
5 动作与体态（含左右手分工）
6 场景 / 时间 / 天气
7 镜头与景别（low angle / close-up / wide shot）
8 风格（媒介 + 渲染 + 年代 + 格式）
9 光与色（directional lighting / rim light / warm color palette）
10 caption 1~3 句
```

**上限参考**：单角色 25~35 个标签 + 1~3 句 caption。超出这个量级继续加就是冗余。
补齐的细节是**协调的默认值**；用户给过设定时以其为准，且不得编造角色名 / 作品名 / 画师名。

## 7. 裁剪顺序（从最先砍到最不该砍）

```text
1  同义质量词与美学词        ← 最安全，收益最高
2  泛化细节词 detailed / intricate details
3  重复标签与大小写变体
4  备选表述（or / maybe / could be）
5  冲突项的一半（保留用户更在意的那半）
--- 以下保留，不动 ---
   主体身份、人数、safety、可见文字、用户显式约束、画师标签、风格主串
```

## 8. 常见误修（不要做这些）

| 误修 | 为什么错 |
|---|---|
| 把 LoRA 触发词"拼写修正" | 触发词是任意字符串，改了就不触发 |
| 把用户给的画师名补成 `@` 之外还换人 | 编造画师名属于禁止项 |
| 把 `score_7` 塞进 Aesthetic / Turbo | 反向削弱，是官方明确的易错点 |
| 把 `safe` 改成 `nsfw` "以防万一" | 擅自改变内容边界 |
| 把中文可见文字翻成英文 | 可见文字必须逐字保留 |
| 把 `photorealistic` 从正面挪到正面别处 | 写实越界，应删除或移入负面 |
| 为了"更详细"再加 10 个同义标签 | 触发 slop，属于 S3 违规 |
| 把变更说明插在两段提示词之间 | 破坏输出契约；说明只能放在两段之后 |
