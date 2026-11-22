---
name: krea2-anime-style
description: Lock and elevate the art direction of Krea 2 anime images — pick one studio or painterly lineage as the dominant pull, translate it into medium, linework, shading, highlight and palette decisions, and keep the look from drifting between generations. Use when a Krea 2 anime render looks generic or off-model, when the user names a studio or an era (Ghibli, Shinkai, KyoAni, Madhouse, 90s Sunrise, retro OVA), or when a style LoRA is loaded and its trigger words plus the surrounding prompt must agree instead of fighting.
version: 1.1.0
---

# Krea 2 二次元画风锁定（Anime Style Lock）

Krea 2 画二次元最容易出的问题不是「不会画」，而是**画风发漂**：同一提示词两次出图，
一次像京阿尼一次像通用 AI 插画；或者堆了三个工作室名字，得到一张谁都不像的图。
本 skill 只干一件事：**把画风钉死，并且钉得住**。

## 官方给的「画风牵引」事实

Krea 官方在《Studio anime aesthetics with Krea 2》里点名：

> "The strongest pulls are Studio Ghibli, Makoto Shinkai / CoMix Wave, Kyoto Animation,
> Madhouse, and 1990s Sunrise."

落地三条：

1. **这五个是被训练得最扎实的画风**——用户点名它们时，模型确实能往那儿靠；
2. **点名工作室只是起点**，官方示例也都是「工作室 + 媒介 + 光 + 场景」一起写，不是只写名字；
3. **同时挂两个以上工作室会互相稀释**——要混合时必须指定主次与偏移层（见第四节）。

## 与兄弟 skills 的分工

| 要做的事 | 走哪个 |
| --- | --- |
| 写一条完整的二次元 caption（主体 / 场景 / 动作 / 身份） | `krea2-anime-prompt` |
| **把画风钉死、锁住、修漂移** | **本 skill** |
| 同一角色的多图一致性 / 三视图 / 表情表 | `krea2-anime-character` |
| 主视觉 / 海报 / 漫画分镜版式 | `krea2-anime-keyvisual` |
| 光影材质色盘等通用美学（非二次元专属） | `krea2-aesthetic-direction` |

**叠加顺序**：先 `krea2-anime-prompt` 决定「画什么」，再本 skill 决定「画成什么样」，
最后 `krea2-aesthetic-direction` 补光 / 材质 / 颗粒。**画风锚句全篇只能有一个**。

## 输出契约

1. **只输出 caption 正文**（英文），不要解释、不要标题、不要代码块围栏、不要结尾建议。
2. 正文里必须有**一句画风锚句**，由**至少四个维度**构成（见第二节）。
3. **不写** `masterpiece` / `best quality` / `score_9` / `8k` / `very aesthetic`、
   不写权重语法、不写分辨率 / 步数 / CFG / LoRA 权重。
4. 用了 LoRA 时：**触发词照抄原样**（不改写、不翻译、不加引号以外的修饰），
   放在正文**末尾**作为独立短语，并让正文描述与触发词指向同一种画风。
5. 用户点名的画风 / 时代 / 工作室**原样保留**，只在空缺处补决策。

## 一、画风锚句：四维锁定

一句能钉住的锚句至少包含四维，缺一维就会漂：

| 维度 | 要写到的细节 | 例 |
| --- | --- | --- |
| 媒介 | 赛璐珞 / 厚涂 / 水彩 / 版画 / 数字插画 | `a cel animation still` |
| 线条 | 粗细、是否闭合、有没有断线 | `clean closed outlines with uniform weight` |
| 上色 / 阴影 | 平涂还是渐变、阴影边缘硬还是软 | `flat cel shading with hard shadow edges` |
| 高光 / 色盘 | 高光在哪儿、主色与强调色 | `glossy hair highlights against a muted teal palette` |

**再加一句时代或工艺**（`1990s OVA` / `shot on film and transferred` / `screen-printed`）会更稳。

反面写法（必漂）：

```text
anime style, high quality, beautiful, masterpiece, best anime art
```

正面写法：

```text
A 1990s OVA cel animation still with clean closed outlines, flat cel shading and hard shadow
edges, glossy specular highlights on the hair, and a muted teal-and-rust palette held by one
saturated red accent.
```

## 二、五个「强牵引」各自怎么写

下面每条给出**可核对的视觉指纹**——不是让你写名字，是让你写名字背后的东西。
（名字可以出现，但**必须伴随指纹**。）

| 画风 | 视觉指纹（写进句子里的东西） |
| --- | --- |
| **Studio Ghibli** | 水彩底 + 赛璐珞上色的混合、大片通透的积云、食物与器物的高细节、柔和的环境光、草地与风的连续性 |
| **新海诚 / CoMix Wave** | 高饱和天空渐变、镜头光斑与逆光、极细的城市线条、云层结构清晰、光在玻璃与水面上的散射 |
| **京都动画** | 干净的闭合线条、极轻的阴影、发丝分组清晰、眼睛高光规整、日常场景的道具密度高 |
| **Madhouse** | 硬朗的阴影分割、粗而果断的墨线、动作帧的透视夸张、暗部大面积压深、脸部结构偏写实 |
| **90 年代 Sunrise** | 机械与机甲的板件感、逆光轮廓、颗粒胶片质感、饱和平涂 + 金属高光、片头式构图 |

**用户点名其它工作室 / 画师时**：按同一张表**现场拆四维**，不要只写名字。
拆不出来就退一步写「媒介 + 线条 + 上色 + 色盘 + 时代」，仍然比只写名字可靠。

## 三、防漂移：四道锁

1. **一句锚句**：画风只在开头出现一次；正文中间不再重复「anime style」这类词。
2. **工艺词**：给一个工艺锚点（`cel animation` / `gouache` / `screen-toned`），
   它比形容词更难被模型忽略。
3. **色盘数字化**：给 2–4 个颜色，其中一个做强调色——色盘一固定，画风就很难跑。
4. **收束句**：结尾一句排除性描述（`the whole frame keeps one cel-shaded look`），
   抵消模型中途换风格。

二次出图风格不一致时，按这个顺序排查：锚句是否只有一个 → 工艺词是否给了 →
色盘是否固定 → 收束句是否在。

## 四、混合画风的正确姿势

用户要「Ghibli × 赛博」这类混合时：

```text
主锚：<一个工作室 / 一种媒介>
偏移：<只偏移一到两层，并写明是哪层>
```

写法示例（结构可抄，内容不可抄）：

```text
The base is 1990s OVA cel animation — clean closed outlines and flat cel shading — but the
palette is pushed into neon magenta and cyan and the lighting is wet-street reflective,
which is the only cyberpunk element in the frame.
```

**禁止**：`Ghibli × Shinkai × ukiyo-e` 三锚并挂（必然互相稀释）。

## 五、整场从句速查（社区实测最有效的一条）

社区实测（`krea2-wildcards` 整理的八条整场从句）证明：**让媒介描述整张画面**，
比「点名一种画风」强得多。对比：

| 写法 | 例 | 结果 |
| --- | --- | --- |
| 命名式（弱） | `a chibi scene` | 像画面里摆了个 Q 版玩偶 |
| 整场式（强） | `the whole scene drawn chibi: super-deformed proportions, huge head, tiny body, flat cel colour` | 整张按 Q 版重画 |

可直接改词使用的整场从句（约 100 字符，纯英文）：

```text
The whole scene drawn as black-and-white manga: ink linework, screentone shading, no colour anywhere.
The whole scene as a watercolour storybook illustration: soft washes, gentle linework, painted background.
The whole scene as comic-book art: bold ink outlines, flat colour, halftone dots, drawn background.
The whole scene as a 1970s cel anime frame: hand-painted cels, muted palette, film grain, painted background.
The whole scene as a 1960s limited-animation cartoon: angular flat shapes, off-register colour, painted backdrop.
```

从摄影切到插画时的三条替换（社区总结）：`facing the camera` → `facing the viewer`；
`shallow depth of field` → `simplified background detail`；
镜头与影棚光术语 → 笔触 / 色盘 / 纸张 / 油墨 / 印刷术语。

## 六、用了 LoRA 时怎么写

Krea 2 的官方风格 LoRA 用**触发词**驱动，例：`Purple retro anime style`。规则：

1. **触发词逐字照抄**，不要翻译、不要拆开、不要塞进句子中间；
2. **摆位按模型卡走**：官方风格 LoRA（如 `Krea-2-LoRA-retroanime`）放**末尾**；
   部分社区 LoRA（如 `@snkbrush`）要求放**开头**，后面用平实句子描述；
   模型卡没写时**先用末尾**（官方风格 LoRA 的默认）；
3. **正文描述必须与触发词指向同一画风**——触发词说 retro，正文却写 modern digital
   painting，两者会互相拉扯；
4. **不写 LoRA 权重**（`0.8` 这类数值属于工作流，不进提示词）；
5. 没有 LoRA 时**不要**自己编触发词——那些词没有对应权重，写了只有噪声。

```text
<主体与场景的自然语言描述> … , Purple retro anime style
```

## 七、常见失败与修法

| 症状 | 根因 | 修法 |
| --- | --- | --- |
| 两次出图风格不一样 | 锚句太长 / 分散 / 没有工艺词 | 压成一句、补工艺词、加收束句 |
| 像「通用 AI 插画」 | 只有 `anime style` 这类空词 | 换四维锚句，点名一个强牵引流派 |
| 三个工作室混成四不像 | 多锚并挂 | 只留一个主锚，偏移只动一到两层 |
| 脸崩 / 线条糊 | 线条维度没写 | 补 `clean closed outlines` / 线宽一致性 |
| 上了 LoRA 但没效果 | 触发词被改写或位置太靠前 | 原样照抄、放到末尾 |
| 上了 LoRA 反而怪 | 正文画风与触发词冲突 | 让正文描述与触发词同向 |
| 上色发灰 | 阴影边缘没定软硬 | 明写 `hard shadow edges` 或 `soft airbrushed transitions` |

## 八、自检清单

- [ ] 全篇只有**一句**画风锚句，且四维齐全（媒介 / 线条 / 上色 / 高光或色盘）；
- [ ] 有一个工艺锚点（cel / gouache / screen-tone / film）；
- [ ] 色盘 2–4 色且有一个强调色；
- [ ] 收束句确认整张保持同一画风；
- [ ] 混合画风时只有一个主锚 + 明确写在哪一层偏移；
- [ ] LoRA 触发词原样、放末尾、与正文同向（无 LoRA 则完全不提触发词）；
- [ ] 没有 `masterpiece` / `score_9` / `8k` / 权重语法 / 参数数值；
- [ ] 没有标题行、代码块围栏、解释与结尾建议。

## 示例

**输入**：「Krea 2 画一张京都动画风格的放学后教室，一个女生靠在窗边」

```text
A Kyoto Animation-style illustration: clean closed linework with uniform weight, very light
shading that only deepens at contact points, hair grouped into clearly separated strands with
neat specular highlights in the eyes, and a soft warm palette of cream walls, pale wood and one
cobalt sky seen through the window. A girl in a navy sailor uniform leans against the window
frame with one elbow on the sill, her sleeve creasing where it folds against the metal; late
afternoon light comes through the glass from behind her and lays a long soft rectangle across
the floor and the desk beside her, where a half-open notebook and a cold can of tea sit.
The classroom behind holds rows of desks receding in clean perspective, chalk dust drifting in
the light. The whole frame keeps one flat, evenly lit cel look with no painterly texture.
```

## 参考

社区整场从句、触发词摆位实测、CFG / Clip Skip 避坑、跨格 character_id 做法，
见 `references/krea2-anime-community-notes.md`。

## 边界

- 不执行脚本、不生成图片、不调 API。
- 不写 LoRA 权重、步数、CFG、分辨率（由工作流决定）。
- 画风点名只作风格描述，不代表任何授权或关联；模仿具体作品的角色与画面需自行处理版权。
- 不复制任何工作室的具体画面构图，只描述可观察的视觉指纹。