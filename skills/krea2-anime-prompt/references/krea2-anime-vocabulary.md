# Krea 2 二次元：画风 / 场景 / 身份写法对照

本文件是 `krea2-anime-prompt` 的参考资料。前三节是**可替换词槽**，第四节是**反例库**。

## 一、画风翻译表（名字 → 视觉属性）

写画风时至少翻译其中**四个维度**；只写名字等于没写。

| 维度 | 可选值（英文，直接进句子） |
| --- | --- |
| 媒介 | `cel animation` / `digital painting` / `ink illustration` / `watercolor` / `gouache` / `screen-tone manga` / `airbrushed 1980s poster` / `risograph print` |
| 线条 | `clean ligne claire outlines` / `rough dry-brush contours` / `no visible outlines` / `tapered ink strokes` / `sketchy double-line hatching` |
| 上色 | `flat cel shading` / `hard-edged shadow shapes` / `granular stippled gradients` / `soft airbrushed transitions` / `duotone spot color` / `watercolor bleed` |
| 高光 | `glossy specular highlights on the hair` / `matte surfaces with no specular at all` / `rim light only` |
| 时代 | `1990s OVA` / `early-2000s TV anime` / `modern web illustration` / `1970s gekiga` / `Showa-era poster` |
| 色盘 | `muted teal and bone white` / `saturated primaries` / `sepia and rust` / `pastel with one acid accent` |

**组合示例（可直接照抄结构，不要照抄内容）**：

```text
A 1990s OVA-style cel animation still: flat cel shading with hard shadow edges, clean
ligne claire outlines, glossy specular highlights on the hair, and a muted teal-and-rust
palette with one saturated red accent.
```

## 二、场景重构模板

把一个地名写成画面，用下面五个槽位各写一句，再挑三个最有辨识度的展开：

1. **尺度与结构**：这里最大的东西是什么、占画面多少；
2. **材质**：地面 / 墙 / 家具各是什么料子，新旧程度如何；
3. **空间关系**：前 / 中 / 远三层各有什么，视线从哪进、停在哪；
4. **时间与光**：光源位置、色温、影子方向、空气里的颗粒（雨、尘、蒸汽、雪）；
5. **故事线索**：一个说明「刚发生过什么」的细节。

模板句：

```text
Set in <地点>, where <最大的结构> occupies <画面比例>, its <材质> worn <新旧>.
In the foreground <前景物件> sits out of focus; in the middle distance <主体> <动作>;
behind, <远景> dissolves into <空气介质>.
<时间> light comes from <方向>, so shadows fall <方向> and <表面> reflects <光源>.
A <线索细节> shows that <刚才发生了什么>.
```

## 三、身份锚点槽位

| 槽位 | 写法要求 | 例 |
| --- | --- | --- |
| 发型 | 形状 + 走向 + 长度 | `short choppy platinum bob with heavy bangs` |
| 面部特征 | 眼睛 / 痣 / 疤 / 妆容，**一个**就够 | `a small mole under the left eye` |
| 轮廓 | 体型或标志性剪影 | `narrow shoulders and a long straight silhouette` |
| 服装层次 | 层次 + 配色 + 材质 | `a navy sailor collar over a white blouse, crisp cotton` |
| 道具 | 随身物 + 状态 | `a scuffed leather satchel, strap worn thin` |

**只选当前景别看得见的槽位**；写了看不见的槽位只是浪费 token，还可能把模型拉远取景。

## 四、反例库（这些写法在 Krea 2 里会退化）

| 反例 | 问题 | 改法 |
| --- | --- | --- |
| `masterpiece, best quality, 1girl, solo, long hair` | tag 流，无语法无空间 | 写成句子：`A girl with long hair stands alone…` |
| `by (artist:1.3), @artist_name` | 权重 / @ 语法在自然语言编码器里无效 | 翻译成媒介 + 线条 + 上色 + 色盘 |
| `Ghibli style, Makoto Shinkai style, cyberpunk` | 三个画派互相稀释 | 选一个主锚 + 一个有界限的偏移，写清偏移加在哪层 |
| `Soul Society` / `World Martial Arts Tournament` | 专有名词不等于画面 | 用第二节五槽位重构 |
| `very beautiful, ultra detailed, 8k` | 空词 | 换成具体材质 / 光位 / 色盘 |
| `dynamic pose` | 无发力方向、无后果 | 写重心、发力方向、被带起的头发 / 水花 / 衣摆 |
| `two girls`（无绑定） | 特征会串味 | 每人「位置 + 特征 + 动作 + 反应」 |
| `best quality, worst quality`（正负混写） | 负面词不属于 Krea 2 的正向 caption | 删掉；要排除就写 `no second figure` |

## 五、出处

- 模型与官方写作规则：<https://github.com/krea-ai/krea-2>（`docs/prompting.md`、
  `docs/expansion.txt`）。
- 二次元家族的分层方法（画风锚句、场景重构、故事节点姿势、身份锚点）参考了社区
  Krea 2 提示词 skill 的共通做法（`krea2-anime-prompt-director`、
  `comfyui-kreatool` 等），此处按本仓库的 skill 规范重写，不直接复制其文本。
- 本 skill 与上述项目无隶属关系。
