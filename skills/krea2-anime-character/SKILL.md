---
name: krea2-anime-character
description: Keep one anime character consistent across a set of Krea 2 images and build multi-view, multi-expression or outfit-variant sheets. Defines a reusable identity block (silhouette, hair grouping, eye design, signature garment layers, one distinguishing mark), fixes the invariants versus what may vary per shot, and writes sheet layouts such as front/side/back or expression grids in Krea 2's natural-language caption. Use when the user needs the same 二次元 character in several images, a character sheet, a turnaround, an expression board, or complains that the face or outfit keeps changing between generations.
version: 1.1.0
---

# Krea 2 二次元角色一致性（Anime Character Consistency）

Krea 2 没有角色 ID 机制：同一角色的「同一个人」感，完全靠你写一个**可复用、可核对**的
身份块（identity block），并在每次生成时**只改该改的，锁住不该变的**。

## 何时使用

- 同一角色要出**多张图**（分镜、连载插画、周边图、系列海报）；
- 要角色**三视图 / 转身图 / 表情表 / 服装变体**；
- 用户抱怨「每次生成脸都不一样」「衣服老是变」；
- 需要把一段设定**固化成模板**，供后续反复粘贴。

**不适用**：单张图里的角色描写 → `krea2-anime-prompt`；画风不统一 → `krea2-anime-style`；
同一角色的海报版式 → `krea2-anime-keyvisual`。

## 输出契约

1. **只输出 caption 正文**（英文），不要解释、不要清单式的「一致性说明」；
2. 需要**模板**时，单独输出一段可直接复用的**身份块**（同样不加标题与代码围栏外的东西）；
3. 每张图的描述里**身份块必须原样重现**（可以追加，不可以改写措辞）；
4. **不写**参数、不写 LoRA 权重、不写 `masterpiece` / `score_9`；
5. 用户给的设定（发色、瞳色、痣、饰品）**一字不改**。

## 一、身份块：五段式

一次写好，反复粘贴。每段都要求**可核对**（看图能验证），不许写评价词。

| 段 | 写什么 | 反例 → 正例 |
| --- | --- | --- |
| ① 轮廓 | 身高感、体型、剪影特征 | `beautiful figure` → `short and compact, narrow shoulders, straight silhouette` |
| ② 发型 | 长度 + 走向 + 分组方式 | `nice hair` → `black hair in two low braids, blunt bangs cut straight across the brow` |
| ③ 眼 / 脸 | 眼形、瞳色、高光位置、一处标记 | `pretty eyes` → `large amber eyes with a single hard highlight at eleven o'clock, a tiny mole under the left eye` |
| ④ 服装层次 | 由外到内的层 + 配色 + 材质 | `school uniform` → `navy blazer over a white shirt with a red ribbon tie, pleated grey skirt, scuffed loafers` |
| ⑤ 识别物 | 一个能一眼认出的随身物 | `accessories` → `a scuffed brass compass hanging from the belt loop` |

**关键**：第 ⑤ 段是性价比最高的一致性锚——一个具体物件比十句「同一角色」都管用。

## 二、不变量 vs 可变量

先列表，再动笔。**不变量写死在身份块里，可变量才随镜头变。**

| 不变量（每张必须原样出现） | 可变量（随镜头变） |
| --- | --- |
| 发型分组与长度、瞳色与眼形、识别物、痣 / 疤、服装的主色与层次 | 表情、姿势、机位、景别、光线方向、背景、时间与天气 |
| 服装的**层数**与**主色** | 外套穿脱、袖口挽起、配饰增减（要明确写「换了什么」）|

**换装规则**：换装时**按部位替换**（上装 / 下装 / 腿 / 鞋 / 配饰），
并**去掉旧部位**的描写——两套衣服同时出现是最常见的一致性崩坏。

## 三、角色设定表（sheet）的写法

Krea 2 读自然语言，宫格必须写成**行列**，并**逐格给内容**：

```text
<身份块> shown in a character sheet laid out as 2 rows and 3 columns on a plain warm grey
background. Row 1, column 1: a full-body front view standing straight with arms at rest.
Row 1, column 2: a full-body three-quarter view turned 45 degrees to her left.
Row 1, column 3: a full-body back view showing the braid ends and the coat's back seam.
Row 2, column 1: a close-up front view with a neutral expression.
Row 2, column 2: the same close-up with a surprised expression, eyebrows raised and mouth open.
Row 2, column 3: the same close-up smiling with eyes closed.
Consistent line weight, flat even lighting, no drop shadows, and no text or labels anywhere.
```

要点：

- **行优先、列其次**（`row 2, column 1`），不要写 `2×3`；
- 每格**只描述变化量**，身份块共用；
- 明确 **统一光照与线宽**，否则每格会各画各的；
- 结尾排除**文字与标签**（模型爱加 `Name / Age` 这类字）。

### 社区做法：给角色一个短编号

社区微调（`krea2-turbo-bbox`，约 90% 训练使用带编号的 grounding 写法）证明：
**短编号 + 每次重述特征**是跨格一致最省事的组合。核心三条可直接迁移到自然语言：

1. **编号只表示「这是同一个」**，身份仍来自描述——所以每次出现都要**重述关键特征**；
2. **编号要短**（`1` / `2` / `3`），长 slug 占预算且容易写错；
3. 同一角色在不同画面里**编号相同、描述随姿态与表情改变**，不变的只有特征。

本 skill 的五段式身份块就是它的自然语言版：身份块 = 编号指向的那段描述，逐张原样复制。

## 四、跨图一致性的三道保险

1. **模板复用**：身份块逐字复制，不做同义改写（改写 = 换人）；
2. **收束句固定**：每张图结尾都加同一句 `The character keeps exactly this hair, eyes and outfit in every view.`；
3. **可变量收敛**：一次只改一到两项（比如只换表情、只换机位），
   同时改三样以上时，模型很难判断哪一项是「同一角色」的证明。

## 五、常见失败与修法

| 症状 | 根因 | 修法 |
| --- | --- | --- |
| 脸每次都不一样 | 眼部 / 发型只有形容词 | 换成可核对特征（眼形 + 高光位置 + 痣） |
| 衣服来回变 | 两套服装描写并存 | 按部位替换，删掉旧部位描写 |
| 三视图各画各的 | 没有统一线宽与光照 | 加「统一线宽 / 平光 / 无投影」 |
| 宫格错位 | 写成了 `2×3` | 改写成 `2 rows and 3 columns` + 逐格 `row/column` |
| 多出文字标签 | 没有排除声明 | 结尾写 `no text or labels anywhere` |
| 换了机位就换人 | 可变量改太多 | 一次只改一项，其余锁死 |
| 角色像「通用美少女」 | 缺少识别物 | 加一个具体随身物 |

## 自检清单

- [ ] 五段式身份块齐全，且每段都可核对；
- [ ] 有一个具体识别物；
- [ ] 不变量 / 可变量已分开，正文里只改可变量；
- [ ] 换装按部位替换且没有旧衣服残留；
- [ ] 宫格写成行列并逐格给内容；
- [ ] 统一线宽 / 光照 / 无投影（设定表场景）；
- [ ] 结尾有排除文字标签的句子；
- [ ] 没有参数、没有 `masterpiece` / `score_9`、没有代码围栏与解释。

## 示例

**输入**：「给这个角色做一张六格表情表」

```text
A short, compact girl with narrow shoulders and a straight silhouette, black hair in two low
braids with blunt bangs cut straight across the brow, large amber eyes with a single hard
highlight at eleven o'clock, a tiny mole under the left eye, wearing a navy blazer over a white
shirt with a red ribbon tie and a pleated grey skirt, a scuffed brass compass hanging from the
belt loop. She is shown in an expression sheet laid out as 2 rows and 3 columns on a plain warm
grey background: row 1, column 1, a neutral expression; row 1, column 2, brows raised and mouth
slightly open in surprise; row 1, column 3, eyes closed in a soft smile; row 2, column 1, lips
pressed thin and eyes narrowed in annoyance; row 2, column 2, looking off to the right with a
faint blush; row 2, column 3, laughing with one hand near her mouth. Every cell uses the same
line weight, the same flat even lighting and no drop shadows. The character keeps exactly this
hair, eyes and outfit in every view, and no text or labels appear anywhere.
```

## 边界

- 不执行脚本、不生成图片、不调 API；不做角色识别或图像比对。
- 不写 LoRA 权重与参数；参考图编辑流程另用对应节点。
- IP 角色名只作描述性标识；需商用自行处理授权。
- 不保证像素级还原：一致性的上限由「特征写得够不够可核对」决定。