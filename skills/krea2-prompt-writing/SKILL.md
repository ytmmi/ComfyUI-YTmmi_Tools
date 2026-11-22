---
name: krea2-prompt-writing
description: Write or rewrite a Krea 2 (Krea-2 / K2) image prompt as a dense natural-language caption in the order the model was trained to read — medium and style anchor, subject and identity, wardrobe, causal action, camera and depth, materials and palette, light and its consequences, in-image typography — following the official Krea 2 rules (faithfulness first, one cohesive paragraph, no tag streams, no quality tokens, quoted text). Use when turning a short or vague idea into a paste-ready Krea 2 prompt, or when polishing an existing Krea 2 / K2 prompt that reads generic.
version: 1.0.0
---

# Krea 2 提示词写作（Krea2 Prompt Writing）

把用户的画面需求写成**一段（或几段）可解析的英文自然语言 caption**，直接粘进 Krea 2 的
prompt。本 skill 只管「怎么写」，不管出图参数、不管 workflow、不管负面词体系。

## 模型事实（决定写法，不要违背）

- Krea 2 是**单流 DiT** 图像基础模型，文本侧用 **Qwen3-VL** 一类视觉语言编码器，
  prompt 体系是**纯自然语言稠密 caption**，不是标签流。
- 官方说明（`docs/prompting.md`）：推荐**自然语言提示词**；**长而详细的提示词效果最好**，
  但模型也能在几乎没有提示工程的情况下出高质量图；**要渲染的文字用引号包住**。
- 变体：Medium / Large / Medium Turbo；turbo 最高 2k 分辨率。分辨率由工作流决定，
  **不要写进提示词**。
- Krea 2 与 Anima / SDXL / Pony 的写法**不通用**：Danbooru tag 串、`masterpiece`、
  `best quality`、`score_9`、`(tag:1.2)`、`@artist`、`8k`、`very aesthetic`
  在 Krea 2 里**只会引入噪声**，一律不写。

## 何时使用

- 用户用一两句话描述画面（「雨夜的便利店门口，一个女孩在等伞」），要一段能直接出图的
  Krea 2 prompt；
- 已有 Krea 2 prompt 但发灰、发空、要素互相打架，需要按官方规则重写；
- 需要把用户的**中文需求**转成英文 caption（正文英文，画内文字保留原语言）；
- 需要「短句档」与「长文档」之间的档位判断（见下文）。

**不适用**：
- 要写 1500–2700 词的「母题整块 + 有限替换位」编辑级长文 → `krea2-editorial-longform`；
- 二次元 / 动漫插画 / 画师画风 / IP 同人 → `krea2-anime-prompt`；
- 只调构图或只调配色 → 通用 `image-composition` / `image-color-harmony`（本 skill 与它们叠加使用，
  不重复它们的词表）。

## 输出契约（先读这一节）

1. **只输出 caption 正文**：不要开头说明、不要结尾建议、不要解释、不要总结、
   不要 `Positive prompt` 之类的标题行、不要 Markdown 代码块围栏。
2. **正文用英文**；用户用中文提问**不代表**要中文提示词。唯一例外是**画面里要出现的文字**，
   它保留原语言并加引号。
3. **一个（或几个）连贯段落**，有语法、有主语、有动词；**禁止**逗号分隔的离散 tag 列表，
   禁止 JSON、禁止 bullet。
4. **不写参数**：不写宽高比、分辨率、像素、步数、CFG、采样器、种子、模型文件名、
   LoRA 强度或工作流节点名。被问到就只回一句「由工作流设置决定」。
5. **不写负面提示词**，除非用户明确要，或明说自己那边没有负面词——此时才追加第二段，
   且用自然语言写「不要什么」，不要 `worst quality, blurry` 这类旧 tag 串。
6. **不改写用户已经写死的部分**：用户给定的主体、人数、动作、服装、场景、画幅、画内文字
   原样保留，只在空缺处补全。
7. **不输出推理过程**。风格、媒介、光位的选择在你内部完成，交付物只有 caption。

## 官方扩写规则（逐条执行）

来源：Krea 官方 `docs/expansion.txt`（同目录 `references/official-krea2-guidelines.md`
有原文与出处），落地到中文场景的解释如下：

1. **忠实优先**：保留用户全部主体、动作、颜色与空间关系；**不新增**用户没有暗示的物体、
   道具、角色或动物。扩写是「把已有信息写实」，不是「加戏」。
2. **可解析的 T2I 结构**：主体与它自己的属性、动作放在一起写；姿态、互动、空间布局用
   「落地」的措辞（谁在哪、朝向哪、手碰着什么），不要把所有形容词堆在句首。
3. **风格规划留在内部**：媒介 / 风格 / 取景 / 光位是你在内部比较两三个方案后**选定一个**，
   交付时直接写出结论，**不要**输出「方案 A… 方案 B…」或任何 planning 块。
4. **文字渲染**：用户要画面里出现文字时，**逐字给出确切文本并用引号包住**，同时写清它的
   位置、材质与排印方式；超过 2–3 个词就提醒用户容易画错，建议只留主标题。
5. **避免过度指定**：不要臆造高具体度的服装款式、色号、材质或场景细节；用户没给的信息，
   补全时只补「能让画面立起来的最小集合」（例如「深色外套」而不是「Loro Piana 羊绒大衣」）。
6. **结构**：思考结束后只写**一段连贯散文**（长文档可以多段，但每段都要有语义推进），
   不要 bullet、不要 JSON、不要 Markdown。
7. **尊重已有细节**：用户 prompt 已经很详细时，**轻抛光**而不是大改——保住他们的措辞与方向。
8. **尊重人体**：写人物时保持体面，默认衣着覆盖身体，不主动写暴露描写。
9. **保留用户媒介**：用户说了 `photo of` / `photograph` / `illustration` / `painting` /
   `sketch` / `3D render`，就必须照做，**不要**为了好画而偷换成另一种媒介。

## 六层骨架（默认写作顺序）

按这个顺序写，读者（模型）能在最少的 token 里拿到最多的结构信息。层级缺哪层就跳过，
**不要改其余层的顺序**。

| 层 | 写什么 | 关键要求 | 例子 |
| --- | --- | --- | --- |
| ① 媒介 + 风格锚句 | 这是什么类型的画面 | 一句到位，只留**一个**主风格，不要堆三个画派 | `A stylized digital painting of …` |
| ② 主体 + 身份锚点 | 谁 / 什么，2–4 个可辨识特征 | 特征要**在取景里看得见**；抽象词换具体词 | `a young woman with a short choppy platinum bob and a small mole under the left eye` |
| ③ 服装 / 材质 | 穿什么、什么料子 | **只写取景到位的部位**（特写不写鞋）；材质写出触感 | `a structured black top with an architectural bust seam, matte wool crepe` |
| ④ 动作 + 因果 | 正在做什么，结果是什么 | 每个动作至少一个**可见后果**（光影、褶皱、飞起的发丝、被碰倒的东西） | `she leans into the doorway, and the rain light slides across the wet shoulder of her coat` |
| ⑤ 空间 + 机位 + 景深 | 在哪、从哪看、几层 | 写清前景 / 中景 / 远景各有什么；机位写「在哪、朝哪、多高」 | `shot at eye level from the far side of the aisle, a blurred shelf of cans in the near foreground` |
| ⑥ 材质分区 + 色盘 + 光位 | 画面靠什么质感与颜色站住 | 2–4 个材质分区；色盘给**百分比**；光写**方向 + 后果** | `materials split into wet asphalt, cold glass and dull aluminum; roughly 60% deep teal, 25% sodium orange, 15% bone white; warm light falls from a single low sodium lamp on the left, so her shadow stretches right and the puddle mirrors the lamp` |
| ⑦ 画内文字 / 收束 | 画面上的字、最后的排除 | 文字逐字加引号；收束只写一条硬约束 | `a small sign reading "OPEN 24H" in worn vinyl lettering; no second figure` |

**不要**在句首堆 10 个形容词再说是个人。主语先出现，属性跟主语走。

## 档位：短句档 vs 长文档

| 档位 | 体量 | 用在 | 写法要点 |
| --- | --- | --- | --- |
| **短句档** | 4–8 个语义单元，一段 60–120 词 | 概念图、头像、单件物品、快速试方向 | 仍要**有语法**（不是 tag 串）；媒介 + 主体 + 动作 + 场景 + 光，两层足够 |
| **标准档** | 一段 150–300 词 | 大多数接单场景 | 六层骨架走满，缺层跳过 |
| **长文档** | 多段 600–1500 词 | 编辑级主视觉、海报、需要材质分区与色盘百分比的画面 | 每段一个语义层，段内不重复；见 `krea2-editorial-longform` |

判据：用户说「来一张」「试试」→ 短句档；给的是完整 brief → 标准档；说是海报 / 主视觉 /
需要排版与色盘 → 长文档。**不要**默认写 1500 词，除非需求确实是编辑级。

## 画幅（只建议，不写进正文）

| 画面结构 | 建议画幅 |
| --- | --- |
| 横向铺开：长排、一点透视、横向序列、宽景 | `16:9` / `3:2` |
| 竖向结构：向上生长、紧密取景、全身直立 | `3:4` / `2:3` / `9:16` |
| 图标感、产品、方形专辑封面 | `1:1` |
| 海报、杂志内页 | `4:5` / `3:4` |

画幅写进工作流参数，**不要**写成 `--ar 16:9` 塞进正文。构图细节交给 `image-composition`。

## 常见失败与修法

| 症状 | 根因 | 修法 |
| --- | --- | --- |
| 画面发空、主体孤立 | 只有主体没有环境因果 | 补第 ⑤⑥ 层：环境怎么参与、光从哪来、影子落在哪 |
| 风格平庸、AI 感重 | 风格锚句是 `beautiful, high quality` 这类空词 | 换成一个具体的媒介 + 质地（`blocky painterly brushstrokes` / `granular stippled shading`） |
| 主体变形、人数变多 | 多人没有绑定属性 | 每个角色写明「位置 + 身份 + 2–4 个特征 + 动作」，并在收束加 `no second figure` |
| 服装被模型加戏 | 写了取景看不到的部位 | 只写取景内的部位；特写不要提鞋和裙摆 |
| 画面糊成一团 | 每个表面都被装饰 | 只保留 2–4 个材质分区，其余写「平滑 / 干净」 |
| 画内文字错字 | 文字太长 | 压到 1–3 个词，逐字加引号，别写两句标语 |
| 提示词写了 tag 串 | 沿用旧模型习惯 | 全部改成句子，一个逗号接一个名词短语的写法要拆开重写 |

## 自检清单（交付前逐条过）

- [ ] 正文是**句子**，不是 tag 串；没有 `masterpiece` / `best quality` / `score_9` / `8k`；
- [ ] 没有 `(x:1.2)` 这类权重语法，没有 `@artist`；
- [ ] 没有分辨率 / 步数 / CFG / 采样器 / 种子 / LoRA 强度；
- [ ] 用户给的主体、人数、动作、颜色、场景**一个没丢**，也没有多出他没提的东西；
- [ ] 每个动作都有可见后果，光有方向也有后果；
- [ ] 画内文字逐字加引号，并写了位置与材质；
- [ ] 只有一个主风格锚句，没有互相打架的媒介（`photograph` + `oil painting` 不能同时当主锚）；
- [ ] 没有标题行、代码块、开头说明与结尾建议，没有中文译文附在英文后面（除非用户要）。

## 示例

**输入**：「雨夜便利店门口，一个女孩抱着塑料袋等雨停，霓虹反光」

**输出（标准档，一段）**：

```text
A cinematic photograph of a young woman waiting out the rain under the fluorescent awning of a convenience store at night. She hugs a thin plastic bag against her chest, its handles digging creases into her damp sleeve, and the hem of her oversized grey hoodie hangs heavy with moisture. Rain streaks the glass door behind her while the store's cold white tubes flatten her face into even light; across the wet asphalt, a red and a cyan neon sign smear into long vertical reflections that reach her shoes. The framing is a medium shot at eye level from just outside the awning, a blurred stack of crates in the near foreground and the empty street dissolving into violet haze behind her. Materials separate cleanly into wet asphalt, cheap reflective plastic and matte cotton. Warm sodium light spills from the left, so her shadow falls right and the puddle repeats the awning in a broken line. A small sticker on the door reads "OPEN 24H".
```

**输入**：「把这段 Krea 2 提示词改成更具体的：`a beautiful woman, masterpiece, best quality, 8k, (detailed face:1.2)`」

**输出（短句档，一段）**：

```text
A close-up portrait photograph of a woman in her late twenties with sun-freckled skin and a slightly off-centre gaze, soft window light from her left carving a bright edge along her cheekbone while the right side of her face settles into shadow. A single strand of dark hair crosses her lower lip. The background is a plain matte wall in muted olive, out of focus.
```

## 边界

- **不执行**任何脚本、不调用外部 API、不生成图片；只产出文本。
- **不做**版权角色的事实性考据（角色外观细节由用户或 `krea2-anime-prompt` 负责）。
- **不做**参数调优建议（步数 / CFG / 采样器 / 放大链路一律不回）。
- 用户要求输出**中文提示词**时先确认：Krea 2 的提示词以英文为佳，中文可写但不保证同等效果；
  用户坚持则照写，正文语言保持单一，不要中英混排。
