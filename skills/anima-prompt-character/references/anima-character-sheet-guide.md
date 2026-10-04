# Anima 角色表与一致性指南（Character Sheet Guide）

配套 `SKILL.md`。本文件给四样东西：**身份锚点模板**、**四条可变轴的真实英文词表**、
**多角色归属配方**、**失败目录**。所有英文词都可以直接进提示词；标 † 的词更适合放在
自然语言句子里（它们靠 caption 语义生效，而不是靠标签统计）——不确定时先放句子，再做 A/B。

## 1. 身份锚点模板

### 1.1 填空模板（把尖括号替换成具体词，之后**整段冻结**）

```text
<发色> hair, <发长>, <发型细节 1>, <发型细节 2>, <瞳色> eyes, <主服装>, <下装>, <鞋>, <固定配饰>, <体型 1>, <体型 2>, <签名配件>
```

### 1.2 填好的样例（12 个标签，落在 8~16 的建议区间内）

```text
silver hair, very long hair, blunt bangs, sidelocks, purple eyes, black sailor dress, pleated skirt, brown loafers, red ribbon, petite, slender, eyepatch
```

### 1.3 锚点纪律

| 规则 | 原因 |
|---|---|
| 逐字复制，不改大小写、不改顺序、不改同义词 | 换一个词面，模型就当成了不同描述 |
| 锚点里不出现镜头、姿势、表情、背景、光照 | 这些是可变轴，混进锚点会让每张图都动 |
| 标签总数锁在 8~16 | 太长会被随机标签丢弃切成不同子集，反而不一致 |
| 签名配件放在锚点最末，必要时加权（`(eyepatch:1.6)`） | 最容易被丢掉的往往是最后那几个 |
| 岁感、气质用自然语言从句补 | `the same slender teenage girl` 比硬塞年龄标签安全 |

## 2. 轴 A：视角 / 视图

| 英文词 | 含义 | 备注 |
|---|---|---|
| `from front` | 正面 | 表格首格的默认 |
| `from side` | 侧面 | 转 90° |
| `from behind` | 背面 | 转 180° |
| `three-quarter view` † | 四分之三侧 | 用 caption 表述更稳 |
| `profile` † | 侧脸轮廓 | 与 `from side` 搭配 |
| `from above` / `from below` | 俯视 / 仰视 | 会同时改变比例，慎用于表格 |
| `dutch angle` | 倾斜机位 | 表格里会显得不统一 |
| `looking at viewer` / `looking away` / `looking back` | 视线 | 视线比身体朝向更容易控制 |
| `portrait` / `upper body` / `cowboy shot` / `full body` | 景别 | 表格内必须**每格相同** |
| `feet out of frame` | 脚出画 | 与 `cowboy shot` 同源 |

> 表格类构图务必让**景别与机位在所有格子里完全一致**，只让身体朝向变——否则模型会优先满足
> "变化"这个信号，把角色特征一起改掉。

## 3. 轴 B：表情

| 分组 | 英文词 |
|---|---|
| 正向 | `smile`, `grin`, `open mouth`, `closed mouth`, `laughing`, `smug`, `wink`, `one eye closed` |
| 中性 | `serious`, `expressionless`, `half-closed eyes`, `closed eyes`, `looking away` |
| 负向 | `pout`, `frown`, `angry`, `sad`, `crying`, `tears`, `scared`, `trembling` † |
| 反应 | `blush`, `embarrassed`, `surprised`, `wide eyes` †, `sweatdrop`, `nervous` † |
| 特殊 | `heart-shaped pupils` †, `star-shaped pupils` †, `sparkling eyes` † |

表情表结构：**锚点 + 固定构图块 + 单个表情词**。构图块（景别、背景、角度）必须逐字重复，
表情词每格只换一个；一次换两个字（如 `smile` → `angry, crying`）容易连五官比例一起改。

## 4. 轴 C：服装 / 装备变体

服装变体时，锚点要**拆开**：保留 `[发型层][眼睛层][轮廓层][签名配件层]`，把服装层交给可变块。

| 场景 | 英文词 |
|---|---|
| 日常 | `casual`, `hoodie`, `denim jacket`, `t-shirt`, `jeans`, `sneakers` |
| 校园 | `school uniform`, `sailor collar`, `blazer`, `pleated skirt`, `loafers` |
| 冬季 | `winter clothes`, `scarf`, `long coat`, `mittens`, `boots` |
| 和风 | `yukata`, `kimono`, `obi`, `geta`, `hair flower` |
| 舞台 / 偶像 | `idol costume`, `stage costume`, `frills`, `detached sleeves`, `arm warmers`, `boots` |
| 战斗 | `armor`, `plate armor`, `pauldrons`, `cape`, `gauntlets`, `sword` |
| 正式 | `suit`, `necktie`, `evening gown`, `gloves`, `heels` |
| 居家 | `pajamas`, `nightgown`, `slippers`, `hair down` |

规则：换装组的负向词里加 `outfit mismatch`；同一角色的**配色主调**尽量不变（发色 + 一个主色），
否则四张图会被读成四个人。

## 5. 轴 D：姿态与动作

`standing`, `sitting`, `kneeling`, `crouching`, `walking`, `running`, `jumping`, `arms at sides`,
`arms behind back`, `hand on hip`, `hands clasped`, `holding sword`, `looking up`。

这张轴与构图强耦合（动作需要空间、需要景别配合），完整规则交给 `anima-motion-boost`；
本 skill 只要求：**姿态词永远不进锚点**，以及视图组里姿态变化时保持景别不变。

## 6. 多角色归属配方

### 配方 1：左右分置（最稳）

```text
2girls, [name A] from [series A], [A: 发色 发长 瞳色 服装 配件], on the left, [name B] from [series B], [B: 发色 发长 瞳色 服装 配件], on the right
```
自然语言再复述一遍："the girl with X stands on the left; the girl with Y stands on the right"。

### 配方 2：前后遮挡（有纵深，风险中等）

一人 `in the foreground`、一人 `in the background`，配 `depth of field, blurry background`。
要求两人**剪影差异明显**（发型、服装轮廓、身高至少差两项），否则容易融成一团。

### 配方 3：群像三角（3 人以上）

`3girls, multiple girls` + 一个视觉主位（`centered`、景别更大）+ 两个陪位（左右、景别更小）。
自然语言写清"谁在中间、谁更高、谁在前"。配角标签量要明显少于主角，否则焦点散掉。

### 归属绑定的三条硬约束

1. 每个名字**后面紧跟**自己的外观从句，不要把所有外观堆在最后统一分配；
2. 位置词成对出现，不写单边；
3. 多角色场景里删掉 `solo`，并把人数标签写在 `[人数]` 段（角色段之前）。

## 7. 表格版式与文字标注

| 需求 | 提示词写法 | 注意 |
|---|---|---|
| 并列三格 | `character sheet, multiple views` + 自然语言"three panels side by side" | 版式靠 caption，别指望布局标签 |
| 干净背景 | `white background, simple background` | 每格逐字相同 |
| 边框 | `border` + 自然语言"thin dividing lines" | 线宽不可控 |
| 视图文字标注 | **不要在提示词里要** | Anima 文字渲染弱，`FRONT` 这类词会糊成乱码；后期加字 |
| 数值/身高标尺 | 同上，后期加 | 模型会把标尺当成随手画的道具 |

## 8. 失败目录（现象 → 成因 → 修法）

| 现象 | 成因 | 提示词级修法 |
|---|---|---|
| 两张图不是同一个人 | 锚点被改写、缩写或换了同义词 | 锚点整段复制，标签数固定 8~16；不同图的锚点做逐字 diff |
| 同锚点仍每张略不同 | 锚点太长，被随机标签丢弃切成不同子集 | 缩短锚点；给签名配件加权 `(eyepatch:1.6)` |
| 两个角色换头 / 换发色 | 外观离名字太远、缺位置词 | 名字后紧跟外观从句；补 `on the left/right`；负向 `wrong attribute` |
| 两个角色融合成一团 | 缺人数标签或写了 `solo`；剪影太像 | 补 `2girls`；删 `solo`；让发型/服装/身高至少差两项；负向 `merged characters, fused bodies` |
| 表格被压成一格 | 版式词不足；负向里含 `multiple views` / `duplicated` | 自然语言写清"三个并列格子"；检查负向并删掉冲突词 |
| 某一格丢了签名配件 | 配件写在可变块、或排在锚点最后被丢弃 | 把配件锁进锚点并加权 |
| 每格上色/线条不同 | 风格子句没固定，或背景词每格不同 | 风格子句逐字复用，背景统一白底 |
| 表格里多出陌生角色 | 缺人数标签 | 补 `1girl` / `2girls`；负向加 `extra characters` † |
| 角色像另一个人 | 中途换了画师标签或 LoRA / 采样器 | 画师标签与生成设置也一并冻结（参数属工作流侧，不写进提示词、不在输出里给数值） |
| 表情表变了脸型 | 一次换两个以上表情词 | 每格只换一个表情词 |

## 9. 发运前检查清单

- [ ] 锚点在这组图里逐字一致（用文本对比确认，不靠记忆）；
- [ ] 锚点只含发型 / 眼睛 / 服装 / 轮廓 / 签名配件，不含镜头、姿势、表情、背景；
- [ ] 每格景别与机位完全相同（表格类）；
- [ ] 多角色：人数标签 + 每人外观 + 每人位置齐备，`solo` 已删；
- [ ] 负向词按形态选过，且没有与需求对抗的词；
- [ ] 没有把种子、宽高比、CFG、步数、模型名写进提示词；
- [ ] 没有凭空出现的画师名或 LoRA 名。
