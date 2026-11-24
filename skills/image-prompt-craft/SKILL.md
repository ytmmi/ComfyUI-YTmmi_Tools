---
name: image-prompt-craft
description: The drafting discipline behind a strong image prompt - one thesis per frame, seven decisions taken in a fixed order (moment, value structure, light, space and lens, colour, material, finish), the five factory defaults every model falls back to, four ways to pin the scale of a subject, how to write materials as visible behaviour instead of adjectives, and a trimming order for drafts that run long. Use when a prompt is technically complete yet generic, when results keep drifting to centred symmetry, flat even light or an average face, when the subject keeps filling the whole frame, or when you need a repeatable drafting procedure before delivery. Model-agnostic - the same rules work as tags or as natural language.
version: 1.0.0
---

# 提示词工艺：成稿纪律（Prompt Craft）

七层美学（`image-aesthetics` 那一组）回答的是**每层决定什么**；
本 skill 回答的是**一次成稿怎么落笔**：先定哪一个主张、按什么顺序落七个决定、
哪些「出厂默认」必须先打掉、尺寸怎么钉住、材质怎么写、字数超了先砍哪一句。

两层是**上下游**，不是并列：**七层给内容，本 skill 给落笔顺序**。
诊断走七层（`image-aesthetics` 路由），成稿走本 skill。
一次只改一层：诊断阶段不要顺手改写法，成稿阶段不要顺手改构图。

## 何时使用

- 提示词**要素齐全但没主张**：每个词都对，画面却像模板；
- 结果总在**居中对称、光照均匀、平均脸、没有动作**——那是模型的出厂默认；
- 主体**总是撑满画面**，说「大」反而越说越大；
- 材质写成形容词后，**所有东西一样糙**；
- 草稿**太长**，注意力被稀释，需要一条稳定的砍字顺序；
- 要把提示词沉淀成**可复用的成稿流程**（工作流 / 模板 / 团队规范）。

**不适用**：只想判断问题在哪一层 → `image-aesthetics`；
只想调光 → `image-light-and-value`；只想调构图 → `image-composition`；
只想调配色 → `image-color-harmony`；
模型专属语法（权重、括号、评分、tag 串方言）→ 各家族 skill。

## 输出契约

- **只输出提示词正文**，不解释、不复述需求、不加标题与代码围栏；
- 默认只出正面提示词；用户明确要负面词、或说自己那边没有负面词时才追加两段式；
- **不写参数**（分辨率 / 步数 / CFG / 采样器 / LoRA 权重由工作流决定）；
- **不规定模型语法**：同一批英文词可以当 tag，也可以写进句子；
- 用户已指定的项**不覆盖**，只补它空着的部分；
- **七维的思考过程不写进输出**：只交付最终提示词正文；
- 内部顺序固定：先写完七维，再压到目标字数，**不要边写边砍**。

## 第一原则：一图一主张

模型是「平均机器」：给它一份平均的描述，它就给你一张平均的图。
所以提示词的价值不是**形容词的密度**，而是**承诺的密度**——你承诺了什么，画面才有东西可画。

一张图只允许有：

1. **一个**最高对比点（视线先落在哪）；
2. **一个**主导明度（整张图的基调）；
3. **一个**主动作（正在发生、尚未完成）；
4. **一个**色彩事件（颜色在哪里发生变化）。

其余一切都降为陪衬。「陪衬」不等于「删掉」，而是**不许和上面四项抢**：
第二个对比点、第二个主光、第二个饱和色都会让画面重新变平。

**自检**：如果这句话里有三个「最」，它就还没有主张。

## 七维决策（顺序不可换）

每一步只做一件事，做完再进下一步；跳步的结果是后面几维互相打架。

| # | 维度 | 这一维必须落地的决定 | 塌陷长相 |
| --- | --- | --- | --- |
| 1 | **瞬间** | 一个动作 + 一个朝向；句子里必须有**未完成的动作**或**刚留下的痕迹** | 静态摆拍、证件照 |
| 2 | **明度结构** | 一档主导占 55–70%；暗 / 中 / 亮三档的面积比；**焦点 = 最高对比处**（不是最亮处） | 三档均分、灰糊、脏 |
| 3 | **光** | 光源 / 方向 / 质量 / 色温 / 比例（stops）+ 衰减落点 | 均光无向、到处发光 |
| 4 | **空间与镜头** | 前 / 中 / 后景职责 + 焦段 + 机位高度 + 主体占画高 | 贴纸背景、人物自动撑满 |
| 5 | **色彩** | 四个角色各司其职（环境色 / 主体固有色 / 点缀色 / 肤色中性锚），面积比 60 / 30 / 8 / 2 | 三种主色互相打架、刺眼 |
| 6 | **材质** | 写**可见行为**，不写形容词；不同材质给不同细节级 | 一切同样糙、塑料感 |
| 7 | **收尾** | 颗粒 / halation / bloom 来源 / vignette / 失焦 | 成片没呼吸、边缘发脏 |

**为什么不能换序**：瞬间决定「拍什么」，明度决定「画面的骨架」，
光决定「哪一面被看见」，空间决定「从哪儿看」，色彩决定「颜色落在哪」，
材质决定「触感」，收尾决定「成片感」。
先调光再定瞬间，等于给一张不知道拍什么的光。

## 反默认清单：先打掉五个出厂设置

模型自带一套「平均画面」设定。以下五条**每次成稿都要主动打掉**：

| 出厂默认 | 为什么塌 | 破法（直接写进提示词） |
| --- | --- | --- |
| **居中对称** | 模型默认把主体放正中 | 主体放 1/3 处，另一侧**显式写成空**：`subject on the left third, the right two thirds left as empty wall` |
| **均光无向** | 没有方向就没有体积 | 指定方向 + 质量 + 比例：`a single low window on the left`，`the fill side falls three stops under` |
| **纹理均质** | 全图同锐度 = 平 | 只给一处锐利：`sharp only on the face, everything past the shoulder already softening` |
| **平均脸** | 人脸先验是标准脸 | 加一处不对称：`a slightly crooked nose, one eye a little narrower` |
| **无瞬间** | 没有动作就没有故事 | 写未完成的动作 / 刚留下的痕迹 / 视线还没落到镜头：`her eyes have not found the lens yet` |

**四个高频病灶**（比上面五条更常见）：

- **用元素堆叠代替设计**：列了一堆东西，但它们之间没有主次；
- **用形容词代替参数**：`beautiful` / `dramatic` / `stunning` 不产生画面，只占字数；
- **全图同一锐度**：一张图里至少要有三档清晰度；
- **跨稿同模子**：每张图都是同一个人、同一个机位、同一种光——固定「主光 + 明度键 + 主色关系」可以，但主体与瞬间必须每稿换。

## 尺寸：四把尺（按优先级）

模型对「大小」的判断靠**先验**，不靠形容词。要让主体变小或变大，靠的是**参照物**。

| 优先级 | 尺 | 怎么用 | 例 |
| --- | --- | --- | --- |
| 1（最强） | **去名尺** | 不用「马克杯」「手机」这类有名字的物体，改写成特征 | `a single-handled white glazed cylinder` 而不是 `a mug` |
| 2 | **公认尺 + 距离** | 给一个大家都认识的尺寸，再给距离 | `a brick is 24 cm tall`，`two metres from the camera` |
| 3 | **同深度对位句** | 让主体和已知物处在同一深度 | `the same depth as the fence post behind her` |
| 4 | **裁切尺** | 用裁切表达大小 | `only her forearms fit inside the frame` |

**要写「大」就不要只写 big**：写「她站在谁旁边」。
同理，要写「小」也不要只写 tiny——写「她几乎缩在门框里」。
名字先验压过一切：模型见过「马克杯」就会画马克杯，你改不掉它的形状。

## 材质：写可见行为，不写形容词

材质不是名词，是**这个材质在光下会做什么**。每种材质给一个不同的可见行为：

| 材质 | 别写 | 写成 |
| --- | --- | --- |
| 湿发 | wet hair | `strands clumped and stuck to the cheek` |
| 湿布 | wet cloth | `the fabric gone dark and clinging` |
| 水珠 | water | `each drop carrying a pinpoint specular highlight` |
| 皮革 | leather | `a bright band along each fold, the worn edge gone pale` |
| 旧金属 | rusty metal | `bright scratches on the raised ridges, dark in the grooves` |
| 木 | wood | `grain sharper in the near edge, softer across the far panel` |
| 旧布 | fabric | `washed many times, soft and slightly wrinkled` |

**不同材质必须给不同细节级**：不可能头发与金属同时是微距特写。
远景材质只保留可辨轮廓，焦点材质才给到亚结构的程度。

## 字数预算（长提示词的纪律）

面向**单向注意力**编码器（越靠前权重越大）的模型，长提示词会被稀释：
靠后的内容权重下降，人物与服装甚至会整段重抽。

| 档 | 总长（英文词） | 适用 |
| --- | --- | --- |
| 紧 | 450–550 | 主体单一、背景简单 |
| 标准 | 600–800 | 常规人物 / 场景 |
| 宽 | 850–1100 | 多主体、多层空间、需要文字排版 |

**超预算时的删除顺序**（从先删到后删）：

1. 元话语（`a sense of`、`the feeling of`、`highly detailed`）；
2. 重复的形容词（同一个形容已经在别处出现）；
3. 次要道具；
4. 颜色的第二处描述；
5. 表情的第三句；
6. **最后才动**主体动作与光路。

**永远不删**：风格头、光路的三个落点、明度三档的数量、尺寸锚的对位句、颗粒层的定稿句。
这些是结构信息，砍掉它们等于把提示词退回成形容词堆。

详细的分档切分、每段禁忌与自检三问见 `references/word-budget.md`。

## 否定句纪律

**首轮不要写防御性否定**：`no halo`、`without text`、`no extra people` 这类句子
会把被否定的概念**激活**——模型读到 `halo`，就可能画一个光环出来。

- 首轮：只写**要什么**，以及**环境本身自带什么**；
- 需要阻止模型把空白画成实体时（空暗被画成隧道壁、空地变成墙），
  一次写全被排除的实体：`it is not a wall, not a building, not any solid thing, it is simply nothing`；
- 修复轮（已经出过错图）才连写否认，并且只针对**上一版确实画错的那一项**。

## 自检清单

- [ ] 这张图的**一个主张**是什么？一句话能说出来（最高对比点 / 主导明度 / 主动作 / 色彩事件各只有一个）；
- [ ] 七维**按顺序**都落了决定，没有跳步；
- [ ] 五个出厂默认**都被打掉**（位置、光向、锐度、脸、瞬间）；
- [ ] 主体尺寸有**参照物**兜底，不靠 big / tiny；
- [ ] 材质写的是**可见行为**，且不同材质细节级不同；
- [ ] 画面里有**至少一处空 / 少**（抑制项），没有元素堆叠；
- [ ] 没有 `beautiful` / `dramatic` / `stunning` 这类不产生画面的词；
- [ ] 字数在目标档内，超预算时**按删除顺序**砍过了，结构信息没被砍；
- [ ] 没有首轮的防御性否定句；
- [ ] 只输出最终正文，没有思考过程与解释。

## 示例

**输入**：「一个人在雨夜便利店门口等雨，要电影感，不要平」

```text
A medium shot from just outside the awning, the camera at the woman's own eye height, her
shoulder filling the left third while the right two thirds stay an empty wall of rain haze.
One cold fluorescent tube above the doorway is the only key: it drops almost straight down, so
the ridge of her nose and the top of her hair carry the brightest edge in the frame while her
eye sockets and jaw sit one band darker. The fill side of her face falls about three stops
under the key and picks up a blue-violet wash from the open sky instead of turning black. A
warm sodium lamp far down the street is the only other source and it reaches no further than
her shoes, breaking into thin orange streaks across the wet asphalt. The subject's own dark
grey hoodie holds the largest mid-tone mass in the frame, the doorway and the street beyond
sink into a narrow low band, and a single small point of light is left above five percent of
the picture. Her hair has gone dark where the rain has soaked it, the strands clumped and
stuck to her cheek, while the dry ends still separate into individual strands. The pavement
is a hard specular surface, each puddle carrying its own pinpoint highlight, and the coarse
grain of the image sits evenly over the whole frame, the shadows included.
```

## 依据

- **prompt-craft**（`https://github.com/Luxvanyu/prompt-craft`，MIT License, Copyright (c) 2026 Luxvanyu）：
  本 skill 的七维决策顺序、一图一主张、反默认清单、尺寸四把尺、材质可见行为与字数预算
  均改编自该项目（其规则来自 174 张出图实验与 10958 条真实提示词），已改写为本地中文口径；
  本地版本只保留方法，不复制其原文与具体文案。
- 明度键、具名布光、反面参照、缺席叙事等仍以 StudioBinder《Film Lighting Terms》、
  Proko《How to Organize Values》、John MacDonald《Understanding Value Keys》、
  David duChemin《Find the Contrast, Find the Interest》、Magnum《Telling Stories》、
  `mood.md` 协议为依据（详见 `image-aesthetics` 的「依据」段）。

## 边界

- 不执行脚本、不生成图片、不调 API。
- 不绑定任何具体模型；不写权重、括号、评分、`BREAK` 等模型专属语法。
- 不复制具体作品的构图、光位或原文；prompt-craft 提供的是方法，不是可抄的句子。
- 字数档位以**英文词**计，且以单向注意力编码器为前提；换模型时按该模型的注意力特性调整
  （见 `references/word-budget.md`）。
