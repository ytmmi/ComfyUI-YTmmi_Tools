# Anima 画师标签混合手册（Artist Mixing）

配套 `SKILL.md`。四块内容：**权重写法速查**、**四个混合配方**、**发运前清单**、**反模式列表**，
末尾附"无画师名"的五槽风格词表。

> 本文件不提供任何真实画师名。所有示例中的 `@artist a` / `@artist b` 都是占位符，
> 必须替换成用户实际提供的画师名；猜错画师名会直接盖掉你要的风格。

## 1. 权重写法速查

| 写法 | 含义 | Anima 上的实际观感 |
|---|---|---|
| `@artist a` | 不写权重 | 基准 |
| `(@artist a:1.1)` | 显式 1.1 | 几乎无变化（SDXL 里这个档位通常已经能看出来） |
| `(@artist a:1.3)` | 常用起点 | 明显偏向该画师 |
| `(@artist a:1.4)` | **主推档** | 画面风格由它定调 |
| `(@artist a:1.6)` | 强 | 其他风格/细节标签开始被压 |
| `(@artist a:2.0)` | 官方 `(chibi:2)` 同档 | 强力覆盖，构图与细节可能被一起改写 |
| `(@artist a:0.8)` | 低于 1 | 把它当"点缀"往回拉，用于混合时的陪衬 |
| `[tag]` | 弱化写法 | 是否生效取决于工作流的权重解析，别当默认手段 |

要点：

- **Anima 需要比 SDXL 更大的数值。** 经验换算：SDXL 里习惯写 `1.1` 的场合，Anima 通常要写到
  `1.3~1.5` 才有同级观感；照抄 SDXL 的数值会得到"好像没什么用"的结论。
- **不要用嵌套括号代替数值。** `((@artist a))` 这类写法在 Anima 上不如直接写 `(@artist a:1.4)` 可控。
- **多词标签整段包进括号**：`(@artist a:1.4)` 正确；`@(artist a):1.4` 错误。
- 权重是**解析层**的事：不同 ComfyUI 权重节点（正负提示词节点的权重解析方式）可能不同，
  换工作流后如果画师效果突然变了，先确认权重语法是否还是同一套。
- 权重的作用对象是**整个标签**，不是单个词；把 `@artist a` 拆成两个标签会改变它的含义。

## 2. 四个混合配方

### 配方 A：主导 + 点缀（最稳，默认推荐）

```text
(@artist a:1.4), (@artist b:0.9)
```
- 一个定调、一个只提供局部特征；
- 自然语言写明继承什么：`keeping the muted palette and soft shading of the dominant style while taking
  only the crisp thin lineart from the accent style`；
- 陪衬低于 1.0 是有意的——它是在"往回拉"，不是在"再加强"。

### 配方 B：年代融合（同代两个画师）

```text
year 2014, mid, (@artist a:1.2), (@artist b:1.2)
```
- 选**年代接近**的两个画师，风格坐标本来就重叠，融合稳定；
- 年代标签放 quality/meta 位（年份与时期属官方时间标签段），不要塞进 general；
- 跨代混（`newest` 的数字精细风格 + `early` 的粗线条）多数情况会糊，除非用户明确要这种冲突感。

### 配方 C：线条 / 上色分工（进阶，风险最高）

```text
(@artist a:1.0), (@artist b:1.0)
```
自然语言里显式分工：`crisp thin lineart drawn in the accent style, colored with the soft watercolor
shading of the other style`。
- 两个权重相等是对的：这里靠**语义分工**而不是靠权重分主次；
- 若结果两边都不像，先改成配方 A（分出主次），再逐步往 C 走。

### 配方 D：单画师锚点（基线，用于对照）

```text
(@artist a:1.4)  →  (@artist a)  →  (@artist a:1.0)
```
做三档 A/B 找出"刚好够"的数值。有了基线版本，才知道混合到底带来了什么。

## 3. 发运前清单

- [ ] 每个画师名都**来自用户**（原始提示词、参考图说明、或用户口述），没有一个是我猜的；
- [ ] 每个标签都带 `@`，且名字书写与用户给的一致；
- [ ] 画师标签在 artist 位（人数 → 角色 → 作品 → **画师** → general）；
- [ ] 数量 ≤3（除非用户明确要求画师混合实验）；
- [ ] 混合时有明确主次，或明确的语义分工；
- [ ] 负向里**已删 `artist name`**；
- [ ] 强画师标签在场时，检查是否还堆着 `score_*` / `very aesthetic` 等质量堆料（先撤掉做 A/B）；
- [ ] 若挂了风格 LoRA：画师标签 ≤1 且权重降到 1.0~1.2，或不用；
- [ ] 提示词正文里没有 LoRA 文件名、模型名、参数、宽高比。

## 4. 反模式列表

| 反模式 | 后果 | 正确做法 |
|---|---|---|
| 漏写 `@`（`artist a`、`by artist a`、`artist: a`） | 风格几乎无变化——这是第一大排查点 | `@artist a` |
| 自己编一个画师名 | 强行套上别人的风格，原本要的风格全被盖掉 | 只使用用户给的名字；没有就用五槽风格词 |
| 一次塞 10 个画师 | 每个贡献被稀释；有随机标签丢弃时每次出图风格都不一样 | 1 个（稳）/ 2~3 个（刻意混合） |
| 负向保留 `artist name` | 直接压制画师标签效果——第二大排查点 | 要画师风格时删掉它 |
| `((@artist a))` 嵌套括号 | 效果不如显式数值，且难以预测 | `(@artist a:1.4)` |
| 只在句子里写 `in the style of <name>` 而不放标签 | 模型没有"某某风格"的中间概念，效果弱 | 既放带 `@` 的标签，又用特征词描述取向 |
| 用画师标签去修人体/手 | 画师标签是风格条件，不解决结构问题 | 交给负面词与重绘流程 |
| 画师标签 + `absurdres` 级别的细节堆料同时上 | 细节词把画师的留白/平涂特征压掉 | 先减质量堆料，看画师标签本身能走多远 |
| 用作品名代替画师名 | 会拉进该作品的官方画风或截图感，不等于画师风格 | 明确问用户要画师名，或改用风格词 |
| 照抄 SDXL 的权重数值 | 得出"画师标签没用"的错误结论 | Anima 用更大的数（常用 1.3~1.5） |

## 5. 附：无画师名时的五槽风格词表

| 槽位 | 可选英文词 |
|---|---|
| 媒介 medium | `digital painting`, `watercolor`, `oil painting`, `gouache` †, `cel shading`, `flat color`, `sketch`, `ink drawing`, `pixel art` |
| 线条 linework | `clean lineart`, `thin lineart`, `thick outlines`, `sketchy lineart`, `rough lineart`, `no lineart` |
| 上色 shading | `soft shading`, `hard shading`, `flat color`, `gradient shading`, `dappled light`, `rim light` |
| 配色 palette | `muted colors`, `pastel colors`, `high contrast`, `low contrast`, `monochrome`, `sepia`, `vibrant colors` |
| 年代 era | `year 2014` 等具体年份；`early` / `mid` / `recent` / `newest` 时期标签；`retro artstyle` |

五槽各取 1~2 个即可，全填满会互相稀释。风格打磨的完整流程交 `anima-style-control` /
`anima-style-boost`。
