# Anima 风格分类表（Style Taxonomy）

`anima-style-control` 的完整词表。所有条目为**英文**、**全小写**、多词用空格分隔。
每条给出 "use when / avoid when"，避免把两个互斥风格拼在一起。

## 0. 四个轴与组装顺序

```text
[year/era + quality + safety] [人数] [角色] [作品] [画师] [媒介 + 渲染 + 格式 + 质感]
```

风格串的推荐拼法：**1 个媒介 + 1 个渲染 + 1 个格式 + 0~2 个质感修饰**。
超过这个数量就会互相稀释（Anima 用 tag dropout 训练，堆同义词不加分）。

## 1. 媒介 medium

| 标签 | use when | avoid when |
|---|---|---|
| `digital painting` | 通用数字插画底座，配任何渲染都稳 | 要手绘纸感时（改用 `watercolor` / `gouache`） |
| `watercolor` | 柔和透明、晕染、青春日常、绘本 | 需要硬边高对比科幻或机械细节 |
| `ink` / `sumi-e` | 水墨、书法性笔触、大量留白 | 需要丰富中间调与渐变 |
| `colored pencil` | 温暖手绘、速写本、校园 | 需要高完成度海报级细节 |
| `pastel` | 粉质感、柔和粉彩、治愈系 | 需要锐利线条与暗部层次 |
| `gouache` | 不透明厚涂、插画绘本、色块明确 | 需要写实材质反射 |
| `charcoal` | 粗粝素描、暗调、概念图 | 需要干净平涂 |
| `pencil sketch` | 草稿、设定草图、过程稿 | 要成品上色（会互相矛盾） |
| `vector art` | 扁平商业插画、UI 风、图标感 | 要手绘笔触 |
| `pixel art` | 复古游戏、点阵 | 与 `highres` / `detailed background` 相冲 |
| `3d cg` / `game cg` | 游戏宣传、三维渲染感 | 与 `screentone`、`ink` 相冲 |
| `screentone` | 漫画网点、黑白灰调 | 与 `full color` / `vibrant colors` 相冲 |
| `manga` | 漫画分镜语言、黑白叙事 | 要全彩插画 |
| `monochrome` / `greyscale` | 黑白、单色 | 与任何彩色意图相冲 |
| `sepia` | 怀旧老照片感（插画内） | 要明快配色 |

## 2. 渲染 rendering

| 标签 | use when | avoid when |
|---|---|---|
| `cel shading` | 电视动画、赛璐璐平涂、硬阴影 | 与 `painterly` / `thick brush strokes` 同用 |
| `flat color` | 极简平涂、设计感插画 | 需要体积感与材质 |
| `soft shading` | 柔光过渡、现代立绘 | 要硬派漫画对比 |
| `painterly` | 厚涂、笔触可见、概念艺术 | 与 `cel shading` / `flat color` 同用 |
| `thick outlines` | 漫画感、复古动画、粗线 | 与 `lineless` 同用 |
| `clean lineart` | 现代精致立绘 | 要草稿或粗粝质感 |
| `lineless` | 无主线稿的厚涂/概念图 | 与 `thick outlines` / `lineart` 同用 |
| `airbrush` | 柔滑渐变、90 年代海报 | 要硬边平面设计感 |
| `gradient shading` | 现代数字感、平滑明暗 | 要颗粒与手绘感 |
| `chiaroscuro` | 强明暗对比、戏剧光 | 要明亮日常色调 |
| `halftone` | 印刷网屏、波普、复古印刷 | 要细腻渐变 |
| `impasto` | 厚颜料堆叠质感 | 要干净平涂 |

## 3. 年代 era / year

| 标签 | 视觉后果 | 建议搭配 |
|---|---|---|
| `newest` / `year 2025` | 锐利高光、丰富渐变、数字感强 | `clean lineart, gradient shading` |
| `recent` / `year 2019` | 现代立绘、柔和渐变 | `soft shading, digital painting` |
| `mid` / `year 2013` | 半厚涂、边缘略脏、色彩偏暖 | `painterly, semi-realistic shading` |
| `early` / `year 2005` | 赛璐璐平涂、色数少、颗粒与偏色 | `cel shading, thick outlines` |
| `old` / `year 1998` | 复古赛璐璐、胶片颗粒、噪点 | `cel shading, retro artstyle, grain` |

> 年代必须与 meta 对齐：`old` 配 `absurdres` 会互相拆台；`newest` 配 `sketch` 也会。

## 4. 格式 format

| 标签 | use when | avoid when |
|---|---|---|
| `official art` | 官方立绘、干净中心构图 | 要"截图感"的随意构图 |
| `anime screenshot` | 电视动画截图、平实视角、简线 | 要海报级精致度 |
| `key visual` | 宣传主视觉、纵向构图、强主题 | 要日常随手拍感 |
| `promotional art` | 游戏/番剧宣传图 | 要草图或设定稿 |
| `character sheet` / `reference sheet` | 多视图、设定集 | 要单一戏剧性构图（多视图见 `anima-prompt-character`） |
| `manga cover` | 封面、标题留白、强对比 | 要纯插画无版式 |
| `poster` | 版式感、大留白、标题位 | 要满构图细节 |
| `illustration` | 通用兜底 | 需要更强的格式指向时 |

## 5. 质感与调性质感（0~2 个）

`paper texture` `canvas texture` `grain` `film grain` `noise` `brush strokes` `visible brush strokes`
`watercolor wash` `color bleed` `ink splatter` `splatter` `rough lines` `sketch lines` `textured shading`
`muted colors` `pastel palette` `high contrast` `monochromatic palette` `warm palette` `cool palette`
`soft focus` `vignette`

## 6. 与质量前缀的相互影响（易错）

| 风格意图 | 危险前缀 | 后果 | 建议 |
|---|---|---|---|
| `pencil sketch` / `rough lines` | `score_9, score_8, absurdres, newest` | 被拉回光滑高完成度数字插画 | 用 `masterpiece, best quality, safe`，去掉 score 与 absurdres |
| `monochrome` / `screentone` | `vibrant colors` 类 LoRA 或 `very aesthetic` | 出现彩色渗入 | 负面加 `vibrant colors, colorful` |
| `old` / `year 1998` | `absurdres, highres, newest` | 复古意图被抹平 | 只留 `normal quality, safe` |
| `pixel art` | `highres, absurdres, detailed background` | 点阵被当成低分辨率噪声修补 | 负面加 `blurry, jpeg artifacts` 并删 highres |
| 裸 Base 出平图 | 不写任何质量词 | 画面很"平" | 加 `masterpiece, best quality, score_7, safe` |
| Aesthetic / Turbo | `score_9, score_8` | 过冲成 slop | **不要**加 score 标签（见基准文件第 1 节） |

## 7. 风格锁定配方（批量 / 系列）

```text
固定段（每张逐字相同）：
  <year/era>, <quality>, <safety>, <人数段保持不变>, <画师段保持不变>, <媒介 + 渲染 + 格式 + 质感>

可变段（每张只改这里）：
  <角色外观/服装/动作/表情> + <自然语言 1~3 句>
```

操作要点：

1. 先出一张"风格样张"，确认风格串后**冻结**，后续所有图复制该串；
2. 冻结后不改质量前缀、不改 meta/year 段、不换采样器与 CFG；
3. 每张只替换主体与动作（动作改写交给 `anima-motion-boost`）；
4. 系列图里角色一致性交给 `anima-prompt-character`，画师权重交给 `anima-prompt-artist`；
5. 记录下这份风格串（写在本系列的说明里），否则下一批会重新漂移。

## 8. 反模式速查

- 两个平级媒介并列：`watercolor, oil painting, pixel art` → 三者都画不好。
- 渲染互斥：`painterly, cel shading` / `lineless, thick outlines`。
- 年代与清晰度互斥：`year 1998, absurdres`。
- 色调互斥：`monochrome, vibrant colors`。
- 写实越界：`photorealistic, cel shading, 1girl`。
- 编造画师：`@some artist` 用户没提过 → **禁止**，改走 `anima-prompt-artist`。
- 风格写进自然语言却与标签矛盾：标签 `cel shading` + 句子 "painted with thick visible brush strokes"。
