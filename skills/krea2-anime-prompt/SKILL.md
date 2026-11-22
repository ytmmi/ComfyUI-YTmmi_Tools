---
name: krea2-anime-prompt
description: Write Krea 2 anime, manga and illustration prompts in the model's own natural-language caption dialect — one dominant art direction instead of stacked studio names, reconstructed scenes instead of proper nouns, story-beat poses with visible consequences, and identity anchors that survive the framing. Use for 二次元 / 动漫 / 插画 / IP 同人 / 漫画分镜 / 角色海报 requests on Krea 2, and when the user names a character or a painterly style rather than describing a scene.
version: 1.0.0
---

# Krea 2 二次元提示词（Krea2 Anime Prompt）

Krea 2 画二次元**不是** Anima / SDXL：它读的是自然语言 caption，不是 Danbooru tag 串。
本 skill 是 `krea2-prompt-writing` 的二次元分叉——底层规则不变（句子、忠实、不写参数），
额外补三件二次元特有的事：**画风方向、场景重构、角色身份锚点**。

## 与其它家族的分界（先确认再动笔）

| 用户要的 | 走哪个 |
| --- | --- |
| Krea 2 + 二次元 / 动漫 / 插画 / 同人 | **本 skill** |
| Krea 2 + 真人写实 / 商业摄影 / 产品 | `krea2-prompt-writing` |
| Krea 2 + 编辑级 1500–2700 词长文 | `krea2-editorial-longform` |
| Anima（`@画师`、score_9、tag 串、512 token 预算） | `anima-*` 家族，**不是**这里 |
| MOSS-Image（JSON Layout、bbox 坐标） | `moss-*` 家族，**不是**这里 |

**Krea 2 里写画师**：不要写 `@artist`、不要写 `by (artist:1.2)`，也不要只写一个名字指望模型认识。
把画风**翻译成视觉属性**：媒介（赛璐珞 / 厚涂 / 水墨 / 版画）、线条（粗细、是否闭合）、
上色（平涂 / 渐变 / 网点）、色盘、时代感。名字可以作为**附加**锚点出现（`in the manner of …`），
但**不能只有名字**。

## 输出契约

1. **只输出 caption 正文**（英文），不要标题、不要代码块、不要解释与结尾建议。
2. **一段或几段连贯散文**；即使是「短句堆叠」，每个片段也必须带介词 / 从句 / 后果，
   不能退化成 `1girl, solo, long hair`。
3. **不写** `masterpiece` / `best quality` / `score_9` / `8k` / `very aesthetic`、
   不写权重语法、不写分辨率 / 步数 / CFG / 采样器 / LoRA 强度。
4. **不写负面词串**；要排除（例如「不要第二个人」）就用一句自然语言写进收束。
5. **画内文字**逐字加引号，并给位置与材质。
6. 用户点名了角色 / 作品 / 画师 / 画幅 / 服装 / 动作时**原样保留**，只在空缺处补全。

## 四条硬规则

### ① 画风是一个决定，不是形容词堆

选**一个**主导视觉语言，然后用具体属性把它写实：

- 色盘（例如 muted teal shadows against bone-white highlights）；
- 线条（clean ligne claire / rough dry-brush outlines / no outlines at all）；
- 上色（flat cel shading with hard shadow edges / granular stippled gradients）；
- 媒介与时代（1990s cel animation / 1970s gekiga ink / modern digital painting）。

**禁止**同时挂三个画派（`Ghibli × cyberpunk × ukiyo-e`）——那只会得到一张谁都不像的图。
用户明确要混合时，用「一个主锚 + 一个有界限的偏移」，并在正文里写明偏移加在哪一层。

### ② 场景必须被重构，不能被命名

`World Martial Arts Tournament`、`Soul Society`、`Celestial Capital` 都是**标签**，
模型不会替你补出画面。把它拆成**那里实际有什么**：

- 建筑与物件：材质、尺度、磨损、堆叠方式；
- 空间关系：谁在前、谁在后、视线穿过什么；
- 时间 / 天气 / 光：光源位置、色温、影子方向、空气中的颗粒；
- 故事线索：一个能说明「这里刚发生过什么」的细节（翻倒的凳子、还冒热气的碗）。

用户没给场景时，**不要**留空背景。按角色的原作世界选一个叙事上有意义的经典场所，
用至少三个场所专属标识把它钉住。用户给了场景就保留并加细节，不要替换。

### ③ 姿势要有故事节点，不要站桩

除非用户要头像 / 立绘 / 静物，否则给角色一个**属于这个场所的具体动作**，并写出：

- 发力方向与身体力学（重心在哪只脚、肩膀往哪拧）；
- 表情与视线（看向谁 / 看向画外哪个点）；
- **可见后果**（被带起的头发、被踩碎的水洼、被推开的风铃、衣袖的拉扯）。

多角色必须**互相作用**：每个人写明「对谁做了什么、对方的反应是什么」，
不要排成一排各自摆姿势。

### ④ 身份锚点要能被取景看见

点名角色时，给 2–4 个**高信息量**特征：发型与走向、脸部或瞳孔特征、体型与轮廓、
标志性服装层次与配色、随身道具。**只选该景别看得见的**——特写不要写鞋，
全身不要只写瞳孔。原作已知就照写，不确定就**不要编**（宁可用描述性外观，也不要写错设定）。

## 取景对照（二次元常用）

| 景别 | 写什么 | 不写什么 |
| --- | --- | --- |
| 特写 / 大特写 | 眼睛高光、发丝走向、表情肌肉、皮肤或网点质感 | 鞋、裙摆、全身比例 |
| 半身 / 牛仔镜头 | 上半身服装层次、手部动作、身后环境一层 | 腿与鞋 |
| 全身 | 服装整体轮廓、站姿与重心、脚与地面接触、影子 | 瞳孔细节（写也无效） |
| 场景主导 | 建筑 / 地形 / 光线的三个层次 | 角色细节（人只是尺度参照） |

## 自检清单

- [ ] 只有一个主画风锚句，且写的是**视觉属性**而不是画师名字；
- [ ] 场景由具体物件与空间关系构成，没有靠专有名词；
- [ ] 动作有发力方向与**至少一个可见后果**；
- [ ] 多角色时每人有位置 + 特征 + 动作 + 反应；
- [ ] 身份特征在**当前景别**可见；
- [ ] 没有 tag 串、`@artist`、`score_9`、权重语法、参数数值；
- [ ] 画内文字逐字加引号；
- [ ] 没有标题行、代码块、开头说明与结尾建议。

## 示例

**输入**：「Krea 2 画一张初音未来在雨夜车站的插画，赛博一点」

**输出（标准档）**：

```text
A modern digital illustration in a clean anime style with crisp cel shading and hard-edged
shadow shapes. Hatsune Miku stands alone on the covered platform of a suburban train station
after midnight, her long teal twin-tails lifted slightly by the wind that funnels between the
tracks, the black-and-magenta hair ties catching a hard rim from the vending machine glow
behind her. She holds her phone up with both hands, its cold screen lighting the underside of
her chin while the rest of her face stays in the blue-violet shadow of the roof. Rain falls
beyond the shelter in thin bright lines and breaks into white sparks where it hits the rails.
The palette is built from deep cyan shadow, sodium orange leakage from the street, and the
bone-white of her uniform blouse, roughly 60 / 25 / 15. A low wide angle from the far end of
the platform puts the yellow tactile strip as a bright diagonal in the foreground, the empty
bench and its reflecting puddle in the middle distance, and the city stacked in soft bokeh
behind. A flickering sign above her reads "NEXT TRAIN 4 MIN".
```

## 边界

- 不做版权角色的设定考据（不确定就不写死）；不复制原作画面构图。
- 不生成图片、不执行脚本、不调外部 API。
- 不输出参数建议、不输出负面词串、不输出中英双语（用户明确要中文才切）。
- 用户要求的角色 / 画风 / 场景若涉及受版权保护的具体作品，按描述性标识处理，并提醒商用需授权。
