# ComfyUI-YTmmi_Tools

ComfyUI 自定义节点工具集，提供图片保存、JSON 文件导出、图片文字水印、批量图片加载、skills 管理及 MiniMax H3 视频采样调度等功能。

## 节点说明

### 图片处理

- **保存jpg图像** — 保存 JPEG，工作流信息写入 EXIF
- **图像转为png** — 保存 PNG，同时保留jpg图像内的工作流信息
- **创建纯色图像** — 创建指定宽高和颜色的纯色图像，支持 `不透明度`（0~1，默认 1.0）；不透明度小于 1 时输出带透明通道的 RGBA 图像，等于 1 时保持 RGB 三通道
- **遮罩裁剪图像** — 按遮罩区域裁剪图像与遮罩（对齐 ComfyUI-Easy-Use 的「遮罩裁剪图像」），输出 `原始图像` / `裁剪图像` / `裁剪遮罩` 与裁剪框的坐标x / 坐标y / 宽 / 高；只处理单张图像
- **图像合并** — 「遮罩裁剪图像」的配套还原节点，把上层图像按坐标贴到底层图像（画布）上，支持百分比坐标、宽高拉伸、图层顺序翻转，以及给上层图层加**蒙版**（遮罩输入）
- **文字水印** — 为图片添加水印，支持文字、字体、大小、位置、颜色、透明度自定义
- **批量加载图像** — 加载指定路径文件夹内的图像，支持多种排序、位置偏移、种子控制与批量输出

### 遮罩裁剪图像 与 图像合并

这一对节点用于「按遮罩抠出主体 → 处理 → 原样贴回」的工作流：**遮罩裁剪图像** 负责裁剪并输出裁剪框坐标，**图像合并** 负责按坐标还原。

```
[图像] ─┐
        ├─> [遮罩裁剪图像] ─> 原始图像 ──┐
[遮罩] ─┘        │                      ├─> [图像合并] ─> 图像
                 ├─> 裁剪图像 ──────────┘        ▲
                 ├─> 裁剪遮罩 ────────（可选：蒙版，作用于上层）
                 └─> 坐标x / 坐标y / 宽 / 高 ────┘
```

#### 遮罩裁剪图像

功能对齐 ComfyUI-Easy-Use 扩展的「遮罩裁剪图像」（`imageCropFromMask`）：取遮罩非零区域的外接尺寸作为裁剪尺寸，以遮罩重心为中心定位裁剪框，再把裁剪框夹取到画面范围内。

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `图像` | IMAGE | - | 待裁剪的图像，**只接受单张** |
| `遮罩` | MASK | - | 裁剪依据，**只接受单张**；全空白时报错 |
| `裁剪乘数` | FLOAT | 1.0 | Easy-Use 的「图像裁剪乘数」与「遮罩裁剪乘数」**合并为一个**，同时作用于图像与遮罩 |

输出（自上而下）：`原始图像`、`裁剪图像`、`裁剪遮罩`、`坐标x`、`坐标y`、`宽`、`高`。

- `原始图像` — 原样透传输入图像，可直接当「图像合并」的画布；
- `裁剪图像` / `裁剪遮罩` — 按裁剪框裁出的结果，尺寸恒等于 `高 × 宽`；
- `坐标x / 坐标y / 宽 / 高` — 裁剪框位置与尺寸，直接连给「图像合并」即可还原。

> **`裁剪乘数 = 1` 时裁剪框完整包含遮罩。** 尺寸取 `max − min + 1`（`max` 是含端点的像素坐标），所以遮罩的非零像素**一个都不会被裁掉**。
>
> **与 Easy-Use 的差异（均为可还原性所需）：** ① BBOX 输出被拆成 `坐标x / 坐标y / 宽 / 高` 四个端口；② 尺寸用 `max − min + 1` 而非 Easy-Use 的 `max − min`——后者会少算最后一列/行，导致裁剪结果**丢掉遮罩边缘**（例如 10×10 的方形遮罩被裁成 9×9）；③ 定位时在「既不越界、又完整包含遮罩」的范围内取居中的那一个，因此 `裁剪乘数 >= 1` 时遮罩必定被完全包含。`裁剪乘数 < 1` 时框比遮罩小，无法包含，此时只保证不越界。
>
> **坐标端口是 `INT,FLOAT` 联合类型。** 裁剪结果本来就是整数像素，但「图像合并」的坐标输入是 `FLOAT`（需要支持 `0~1` 百分比）。ComfyUI 的前端与后端都按**逗号拆分联合类型**做匹配，纯 `INT` 会被 `FLOAT` 拒绝、**连不上**；声明成 `INT,FLOAT` 后既能接 `FLOAT` 输入、也能接 `INT` 输入。`宽 / 高` 两边都是 `INT`，因此本来就能连。
>
> **不做批次。** Easy-Use 会对整批遮罩取统一外接尺寸并逐帧平滑裁剪框；本节点只处理单张图像，输入多张会直接报错（避免"整批共用一个框"这种隐式行为）。原来的 `BBox平滑Alpha` 参数也一并移除。

#### 图像合并

把上层图像按坐标贴到底层图像（画布）上，超出画布的部分裁掉，**画布不会因此变大**。

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `图像0` / `图像1` | IMAGE | - | 两张待合并的图像 |
| `坐标x` / `坐标y` | FLOAT | 0 | `0 ~ 1`（不含 1）按**画布尺寸的百分比**，其余按**像素**；可为负 |
| `宽` / `高` | INT | 0 | `0` = **不限制**（保持原尺寸），其余 = **拉伸**到指定尺寸 |
| `图层顺序翻转` | BOOLEAN | False | 默认「图像0」在下、「图像1」在上；打开后「图像1」在下 |
| `遮罩` | MASK | 可选 | **蒙版，作用于在上面的那个图层**：遮罩为 `1` 显示上层、为 `0` 透出底层 |

**画布 = 处于底层的那张图**：默认画布是「图像0」，打开「图层顺序翻转」后画布是「图像1」。百分比坐标按画布的宽高换算。

**关于 `遮罩`（蒙版）：**

- **只作用于上层**——默认是「图像1」，打开「图层顺序翻转」后变成「图像0」；
- 极性与 ComfyUI 官方「Image Composite Masked」一致：`遮罩 × 上层 + (1 − 遮罩) × 底层`，即**遮罩为 1 的地方显示上层**；
- 蒙版会**跟随上层的位置与尺寸**：上层按 `宽 / 高` 拉伸时，蒙版同步缩放到拉伸后的尺寸，因此逐像素对齐；
- 不接遮罩时上层完全不透明，行为与没有该输入时一致；
- 上层自带 alpha 时与蒙版**相乘**（例如 `alpha=0.5` × `遮罩=0.5` → 覆盖率 `0.25`）。

上层若为 4 通道（RGBA），按 alpha 与下层混合；通道数不一致时按 RGB 归一化处理，画布自身的 alpha 保持不变。

> 还原时把「遮罩裁剪图像」的 `原始图像` 接到 `图像0`、`裁剪图像` 接到 `图像1`，`坐标x / 坐标y / 宽 / 高` 直接连过来即可——裁剪框落在原图内时输出尺寸与原图完全一致。
>
> 若要把「遮罩裁剪图像」的 `裁剪遮罩` 接到 `遮罩`，注意该遮罩是**裁剪后**的，与上层图层同尺寸，可直接使用。

### 视频处理

- **视频拼接** — 将多段视频（ComfyUI 原生 VIDEO 类型，与「加载视频」等节点兼容）按接口顺序拼接为一段视频，连接末尾输入时自动增加输入接口，最多支持 10 路输入
- **预览视频** — 将 VIDEO 视频保存为临时文件并在 ComfyUI 中播放预览，视频原样透传可继续接入下游

### 数据处理

- **保存json文件** — 将 JSON 数据写入磁盘文件
- **像素大小指定比例** — 输入宽高，按指定宽高比换算，保持像素总数基本不变
- **展示文本（多重）** — 展示上游节点的字符串信息（数字、字符串、文本、JSON 等），支持 0~8 号共 9 个输入口，默认只显示「输入0」，连接后自动显现下一个输入口；2 个及以上输入自动按输入口序号分隔标注展示；音频、潜空间、视频等类型自动过滤不展示；**输入口已连接但内容为空时显示 `[空文本]` 占位提示**（与「未连接」可区分）
- **密钥储存器** — 加密保存 API 密钥与接口地址（以系统用户名前5位派生密钥，防止插件目录被复制后泄露），点击「保存」加密存储、「删除密钥」删除「选择密钥」下拉中选中的预设；执行后按「选择密钥」下拉名称输出密钥/接口地址
- **自定义LLM** — 调用任意 OpenAI 兼容格式的在线大模型接口（API Key + 接口地址 + 模型名 + 提示词），返回生成文本；模型名为下拉菜单，点击节点上的「获取模型」按钮自动拉取接口可用模型列表，支持温度/最大token/top_p/种子/生成后控制；支持 **skills 输入接口**（接入「skills管理器」输出的指导文本或自动清单；自动清单时与模型多轮按需读取，无需 tools 支持）；支持图片输入（最多 9 张，默认只显示 1 个图片输入口，连接后自动显现下一张），按 OpenAI 多模态格式发送，可适配 DeepSeek V4.1 Flash（deepseek-flash）等支持视觉输入的模型；除「输出文本」外另输出 **「简略上下文」**（本次运行的步数 / 输入 skills 名称 / 调用的 skills / 每步思考 / 最终输出，纯代码拼装、不调用模型总结）
- **skills管理器** — 管理并读取插件 `skills/`（内置）与 `custom_skills/`（自定义）目录中的 skills；选「自动」时只输出 skills 清单与读取协议，由自定义LLM与模型多轮按需读取（渐进式披露，按家族筛选首轮省约 90% 上下文），选具体 skills 时输出其完整指导文本；「模式」可按任务家族筛选（H3 视频 / Qwen-Image 文生图 / Qwen-Image 图像编辑 / Anima 二次元插画）；**所有操作不弹窗**，刷新结果通过按钮文字与控制台日志反馈

### 二维码

- **二维码识别** — 识别图片中的二维码，返回解码文本
- **创建二维码** — 根据文本生成二维码图片，支持错误矫正等级、边长、边距设置

### MiniMax H3

- **H3 低噪细节精修** — 在低噪点区（低 Sigma）局部加密采样步长，消解运动物体的边缘像素颗粒；移植自 [ComfyUI-YCNodes-MiniMax-H3](https://github.com/yichengup/ComfyUI-YCNodes-MiniMax-H3.git)

## skills 说明

「skills管理器」与「自定义LLM」的 skills 接口，参考 [ComfyUI_Qwen_H3_Prompt](https://github.com/chflame163/ComfyUI_Qwen_H3_Prompt.git) 的 skills 管理方式实现：插件启动时扫描 `skills/`（内置）与 `custom_skills/`（自定义）目录，每个 skills 为其中一个子目录，目录中必须包含 `SKILL.md`。

```
[skills管理器] -> (skills) -> [自定义LLM] -> 输出文本
```

### 两种 skills 模式

| `选择skills` | 行为 | 上下文占用 |
|---|---|---|
| **自动**（默认） | 只把 skills **清单与读取协议**发给模型，模型按需请求读取正文，多轮往返直到给出答案（**渐进式披露**） | 首轮约 6.7k 字符 |
| 具体 skills | 直接输出该 skills 的完整指导文本（含 `references/`），单轮请求 | 如 h3-prompt-writing 约 42k 字符 |

**实测对比**（23 个内置 skills，`模式` = `auto`）：

| 方式 | 字符数 |
|---|---|
| 自动模式首轮（清单 + 协议，不筛选） | 12,930 |
| 自动模式首轮（`模式` = `qwen-image-t2i`，按家族筛选） | 813 |
| 自动模式首轮（`模式` = `Anima`，按家族筛选） | 5,995 |
| 固定发送 h3-prompt-writing 全文 | 42,017 |
| 固定发送全部 23 个 skills 全文 | 430,463 |

自动模式首轮比固定发送单个 skills 全文**省约 69% 上下文**（按家族筛选时约 86%~98%），且模型可自行决定是否需要 skills、需要哪个、以及是否需要进一步读取参考文件。

### 渐进式披露（自动模式）

选择「自动」后，模型可**单独输出一行**读取指令，节点读取对应文件并回注对话，继续下一轮：

```
READ: <skills名称>                      # 读取该 skills 的 SKILL.md
READ: <skills名称>/<相对路径>            # 读取该 skills 内的参考文件
```

实际往返示例（读取 SKILL.md → 读取 base-en.txt → 作答）：

| 轮次 | 消息数 | 上下文 | 已加载内容 |
|---|---|---|---|
| 第 1 轮 | 2 | 6,682 字符 | 仅清单 |
| 第 2 轮 | 4 | 9,406 字符 | + SKILL.md |
| 第 3 轮 | 6 | 25,284 字符 | + references/base-en.txt |

- **不依赖** 接口的 `tools` / function calling 支持，因此对国内中转端点等兼容性最好；
- 若模型首轮就能直接作答，则**只请求一次**（不产生额外往返）；
- 若模型不遵守协议一直请求读取，受 `skills最大轮数`（默认 8）保护并强制收尾；
- 读取失败（名称错误等）会把错误回注给模型，让它改名重试，而不是直接中断；
- 图片输入挂在最初那条 user 消息上，后续每一轮都仍然可见。

> **关于 `h3-prompt-writing` 的两份指南：** `references/base-en.txt`（T2VA/I2VA/FL2VA/L2VA）与 `references/ref-en.txt`（Ref2VA）**并非重复内容**——实测两者非空行交集仅 2 行（均为代码围栏），且 `ref-en.txt` 有 4 处明确声明其镜头/运镜/对白规则"shared with / follows the Video Prompt Writing Guide"，即**依赖 base-en**。因此 `模式` 为 `auto` 时同时提供两份，避免因小失大。

### skills管理器

管理并读取 skills，输出所选 skills 的完整指导文本。

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `选择skills` | COMBO | 自动 | `自动` = 只输出清单与读取协议，由模型多轮按需读取（渐进式披露）；也可选具体 skills 直接输出其完整指导文本。点击「刷新skills」按钮可重新扫描 |
| `模式` | COMBO | auto | **任务模式，仅在「选择skills」= `自动` 时生效**（见下） |
| `包含参考文件` | BOOLEAN | True | 是否一并读取 skills 的 `references/` 参考资料（仅「具体 skills」模式生效） |
| `最大字符数` | INT | 72000 | 指导文本字符上限，超出后不再追加参考资料 |
| `附加说明` | STRING | 按 skills | 追加到 skills 文本末尾的补充说明；**按所选 skills 自动填充输出强调**（抑制开头说明/结尾建议等无关元素），可自行删除或改写 |

#### 不弹窗的反馈方式

「刷新skills」等操作**不使用 alert / confirm / 自绘弹窗**，避免打断画布操作：

| 情形 | 反馈 |
|---|---|
| 刷新成功 | 按钮文字短暂变为绿色 `✓ 已发现 N 个`（约 2.2 秒后复原），并在 `console.info` 打印 skills 列表 |
| 刷新失败 | 按钮文字短暂变为红色 `✗ 刷新失败`，具体原因写 `console.warn`（F12 可见） |
| 未发现任何 skills | 按钮显示 `✗ 未发现 skills`，`console.warn` 给出「放哪里、要什么文件」的说明 |
| 节点创建时的自动刷新 | **静默**：不改按钮文字，只更新下拉选项与控制台日志 |

#### 选择skills 与 模式 的联动

**「模式」只在「选择skills」为 `自动` 时生效**——因为模式描述的是"自动挑选 skills 时限定哪个任务家族"，一旦手动指定了 skills，就由该 skills 自身决定输出，模式不再参与。

| 「选择skills」 | 「模式」 | 实际效果 |
|---|---|---|
| `自动` | `auto` | 列出全部 skills，不筛选 |
| `自动` | `H3-*` / `qwen-image-*` / `Anima` | 按任务家族筛选清单 |
| 具体 skills | 任意值 | **模式失效**：不筛选，且加载该 skills 的**全部**参考资料 |

前端会在切换到具体 skills 时**自动把「模式」切回 `auto`**，切回 `自动` 时再恢复你此前选的模式（不会被清掉）。这样界面上始终不会出现"模式看起来选了但实际没生效"的困惑状态。

> 例：手动选 `h3-prompt-writing` 时，无论模式是 `auto` 还是 `H3-ref2va`，都会加载 base-en + ref-en 两份指南（42,017 字符）。若想让模式真正筛选，请把「选择skills」设为 `自动`。

#### 模式与任务家族

下表均为「选择skills」= `自动` 时的行为：

| `模式` | 任务家族 | 「自动」清单包含 |
|---|---|---|
| `auto` | 全部 | 23 个（不筛选） |
| `H3-t2va` / `H3-i2va` / `H3-fl2va` / `H3-l2va` / `H3-ref2va` | H3 视频 | 9 个（排除 2 个 Qwen-Image 与 12 个 Anima） |
| `qwen-image-t2i` | Qwen-Image 文生图 | **仅 `qwen-image-t2i-prompt`** |
| `qwen-image-edit` | Qwen-Image 图像编辑 | **仅 `qwen-image-edit-prompt`** |
| `Anima` | Anima 二次元插画 | **仅 12 个 `anima-*`** |

非 `auto` 模式的清单还会带一行**家族提示**（例：`当前模式：Anima（二次元插画）——本清单仅列出 Anima 家族的 skills，请只在本家族内选择`），进一步降低模型路由到错误家族的概率。

**筛选的意义**：模式已表明任务类型时，清单里不应再出现无关家族的 skills，否则模型可能路由到错误家族（例如选了 `Anima` 却读到 H3 视频 skills）。实测清单体积（23 个内置 skills）：

| `模式` | 清单字符数 | 筛选后 skills 数 |
|---|---|---|
| `auto` | 12,930 | 23 |
| `H3-t2va` | 6,743 | 9 |
| `qwen-image-t2i` | 813 | 1 |
| `qwen-image-edit` | 863 | 1 |
| `Anima` | 5,995 | 12 |

> **模式在节点内的唯一实际作用就是「任务家族筛选」。** 自动清单只列 skills 的 id 与描述（不含正文），模型 `READ:` 某个 skills 时读到的也只是它的 `SKILL.md`，参考资料需另行 `READ: <skills>/references/xxx`——因此模式无法、也不会去挑参考资料。手动分支下模式已被中和，两份指南一律加载。
>
> `skill_instructions(skill_id, mode=...)` 作为公开 API 仍支持按模式挑指南（`H3-ref2va` → 仅 ref-en；其余 H3 模式 → 仅 base-en），供外部调用与测试使用；节点自身不再走该分支。

输出：`skills`（完整指导文本或自动清单）、`skills名称`（所选 skills 的 id，自动模式为 `自动`）、`skills目录`（全部已发现 skills 的清单）。

### 内置 skills

`skills/` 内置 23 个 skills（4 个家族）：

| 家族 | skills | 说明 |
|---|---|---|
| H3 视频 | `h3-prompt-writing` | MiniMax H3 视频提示词书写（T2VA/I2VA/FL2VA/L2VA/Ref2VA） |
| H3 视频 | 其余 8 个 | MiniMax H3 官方风格类 skills（3D 动画、品牌宣传、纸艺定格等） |
| Qwen-Image | `qwen-image-t2i-prompt` | Qwen-Image 2.1 文生图提示词改写（八步观察者视角描述 + `wh_ratio`） |
| Qwen-Image | `qwen-image-edit-prompt` | Qwen-Image 2.1 图像编辑提示词改写（属性解耦 + `wh_ratio`/`ratio_follow`） |
| **Anima** | `anima-prompt-format` | Anima 提示词格式化（官方标签顺序 + 版本化质量前缀 + 两段式输出） |
| **Anima** | `anima-motion-boost` | 动作增强（动作节拍、动态构图、运动证据、避免解剖崩坏） |
| **Anima** | `anima-style-control` | 风格控制（媒介 × 渲染 × 年代 × 版式的风格分类与锁定） |
| **Anima** | `anima-style-boost` | 风格增强（线 → 上色 → 色彩 → 光照 → 背景的分层增强阶梯） |
| **Anima** | `anima-prompt-optimize` | 提示词优化（顺序/空格/一致性/冲突/冗余/版本前缀的逐项修复） |
| **Anima** | `anima-composition-optimize` | 构图优化（景别 × 机位 × 主体摆放 × 前后景层次 × **鱼眼 / 球面 / 极端透视等特殊情况**） |
| **Anima** | `anima-color-harmony` | **配色与颜色搭配**（配色骨架 × 明度/饱和度结构 × 主体-背景分色 × 暗部环境色与大气透视 × 光的颜色 × 双色调调色，含七套骨架与失败修法） |
| **Anima** | `anima-prompt-artist` | 画师标签与混合（`@artist` 强制前缀、多画师权重兑配） |
| **Anima** | `anima-prompt-character` | 角色一致性与三视图（身份锚点 + 多视图/多表情角色表） |
| **Anima** | `anima-prompt-negative` | 负面提示词与质量前缀（版本矩阵 + 按失败域的负面词表） |
| **Anima** | `anima-prompt-regional` | 分区与局部重绘（Regional LLLite 分区块 / inpaint 目标成品写法） |
| **Anima** | `anima-lora-trigger` | LoRA 触发词与权重（Anima 权重需比 SDXL 更高，多 LoRA 角色分派） |

其中 `qwen-image-t2i-prompt` 与 `qwen-image-edit-prompt` 来自用户提供的 Qwen-Image 2.1 系统提示词，已改写为 skills 形式：`SKILL.md` 为工作流摘要，**完整原始系统提示词逐字保存在 `references/` 下**（SHA256 与源文件一致），由 skills管理器一并加载。

**Anima 家族**基于 [CircleStone Labs / Comfy Org 官方 Anima 模型卡](https://huggingface.co/circlestone-labs/Anima)、[ComfyUI 官方 Anima 教程](https://docs.comfy.org/tutorials/image/anima/anima) 与社区提示词工程实践整理，全部 12 个 Anima skills 共用一份基准文档 [`skills/anima-prompt-format/references/anima-prompt-baseline.md`](skills/anima-prompt-format/references/anima-prompt-baseline.md)（标签顺序、质量前缀、权重语法、版本差异、能力边界）。Anima 家族的输出默认是**只给正面提示词**，且**不输出任何参数数值**，因此其「附加说明」使用**专属强调**；该强调可在 `SKILL.md` front matter 用 `extra-note:` 覆盖。

#### Anima 高杠杆规则（对齐手写系统提示词）

实测「Anima 家族 skills + 渐进式披露」的输出曾不如一份手写的 Anima 系统提示词，差距集中在四处。现在这四条已经写进**共同基准**与**各关键 skills 的正文**（渐进式披露只读 `SKILL.md`，不会自动读基准，所以规则必须内联）：

| 规则 | 说明 |
|---|---|
| **① 画师标签必选** | 正文必须有 **1 个带 `@` 的主画师**，权重 `(@artist name:2)` 起，只 1~2 个。**用户没给画师时由模型自己挑一个风格对路的**（旧版写的是"绝不编画师名"，会导致输出里根本没有画师标签——画质第一杠杆直接丢掉）。Anima 用 Qwen3 编码器，多画师会互相污染嵌入 |
| **② 权重用大数** | Anima 需要比 SDXL **大得多**：常规 `(tag:2)` 起，强强调 `(tag:3)`~`(tag:5)`；用户给 `1.2` 这类小数要放大到 2~5。全家族已清除 SDXL 档位示例（`1.3`/`1.4` 在 Anima 上几乎等于没写） |
| **③ 取景对抗自然语言漂移** | 自然语言一旦描述环境就会**把镜头拉远**，吃掉 `upper body`/`close-up`。必须给取景加权 `(upper body:2)`、自然语言**首句写死取景**，不够再加到 `:5`/`:7`；**加权标签总数 ≤4 个** |
| **④ 多人特征分离** | 属性**按角色分组连续写完再切换**，严禁交叉排列；互动词紧跟在人数标签后；易混淆特征加权 `(blue hair:2), (red hair:2)` |
| **⑤ 特殊情况可自主选用** | 用户没指定构图 / 镜头时，**允许模型按题材主动选一个特殊装置**（`fisheye lens` 鱼眼、`spherical composition` 球面构图、`extreme foreshortening` 极端透视、`isometric` 等距版式、`panorama` 全景……），**不要永远回落到最保守的默认景别**。硬约束：用户已指定时**绝不覆盖**、一次只用**一个**、**表格类场景（三视图 / 分镜 / 表情表）禁用**；词表另附每条的效果 / 适用题材 / 风险与三套配方 |

配套改动：Anima 模式的**家族提示**现在会明确要求模型**先读取共同基准**（此前渐进式披露下基准从未被读到），并点出上述硬规则。改动过的 skills 版本号升到 `1.1.0` / `1.2.0`。

#### Anima 配色与颜色搭配（`anima-color-harmony`）

Anima 不指定配色时每次都会自己配一套，常见结果是**发灰、刺眼、或整张只剩一个调子**。该 skills 只管**颜色**这一层，按四步走：

| 步骤 | 内容 |
|---|---|
| **① 选配色骨架** | 七套骨架任选其一（**一次只用一套**）：单色 / 类似色 / 互补 / 分割互补 / 三角 / **冷暖对抗**（最万能的默认）/ 单一强调色。落地为**主色 + 辅色 + 强调色**，比例 60 : 30 : 10 |
| **② 定明度 × 饱和度结构** | 高明度低饱和＝清新治愈；高饱和低明度＝赛博夜戏；**"发灰"的成因就是停在中间饱和 + 中间明度**，解法是往对角走；**互补对撞必须错开明度**（两边都又亮又饱和会在交界处振颤刺眼） |
| **③ 主体与背景分色** | 五种分离手段至少用一层：温度 / 明度 / 饱和度 / 色相 / 边缘光。主体"陷进背景"几乎都是因为两者色相或明度太接近 |
| **④ 定光的颜色** | 先定光色再定物体色——金色时刻、蓝调时刻、霓虹双色、月光、室内暖光、逆光……光的颜色就是画面的基调 |
| **⑤ 暗部写环境色，不写"固有色变暗"** | **暗部是"发灰 / 发脏"最隐蔽的成因**：亮暗色相相反（暖亮冷影 / 冷亮暖影），暗部用 `deep blue shadows` 而非纯黑，`bounce light` 给暗部补环境色 |
| **⑥ 有远景就做大气透视** | 远景**降饱和 + 偏冷 + 提明度 + 降对比**，否则前后景粘成一片。与第 ③ 步是两件事：分色管主体**跳出**背景，大气透视管**纵深** |
| **⑦ 点名调色时直接用** | `teal and orange`（青橙）/ `duotone`（双色调）/ `monochrome` / `faded colors` / 霓虹双色——**这些词本身就规定配色，用了就不再叠骨架**（会互相稀释） |

配套 `references/anima-color-vocabulary.md` 提供：颜色标签速查（含**互斥提醒**：`vibrant colors` ✗ `muted colors`、`high contrast` ✗ `low contrast`、`monochrome` ✗ 彩色词）、七套骨架的可抄写法、明度×饱和度矩阵、**情绪 → 配色对照表**（治愈 / 燃 / 赛博 / 压抑 / 怀旧 / 童话 / 恐怖 / 华丽）、光的颜色表、分色配方、**暗部环境色与大气透视**、**双色调 / 电影感调色表**与**失败 → 最小处方**表（含"暗部发脏""互补振颤""前后景粘连"三条新增处方）。

与相邻 skills 的分工：**画法与媒介**归 `anima-style-control`，**细节与纹理**归 `anima-style-boost`，**构图与镜头**归 `anima-composition-optimize`，本 skills 只负责**颜色关系**（其中"光的颜色 / 暗部环境色 / 大气透视的颜色处理"归本 skills，"光的方向与体积"归 `anima-style-boost`）。用户没指定配色时**允许模型自主选一套**（硬约束：用户已指定时绝不覆盖、一次只用一套骨架、颜色标签 ≤3 个）。

> Anima 模式的**家族提示**（`mode_family_hint`）会显式要求模型：遇到**配色 / 色调 / 颜色关系**类需求
> （发灰、刺眼、主体陷进背景、整张只剩一个调子，或用户点名 pastel / neon / sepia / duotone / 电影感调色）
> 时**另读 `anima-color-harmony`**——否则模型只被要求读共同基准，不一定路由到配色 skills。
> 同时该 skills 加入了节点 `SEARCH_ALIASES`（`anima` / `二次元` / `配色` / `颜色搭配` / `color harmony` / `palette`）。

### 附加说明的默认强调

「附加说明」文本框会**按所选 skills 自动填充**一条输出强调，作用是抑制无关元素——开头的说明、结尾的建议、解释、总结、代码块围栏：

```
【输出要求】只输出所选 skills 规定格式的最终内容本身（提示词正文、JSON 等，
以 skills 的格式契约为准）；不要输出任何开头说明、结尾建议、解释、总结、前言、
后记或 Markdown 代码块围栏，也不要复述本条要求。
```

> **为什么强调里不写具体格式**：JSON 与散文都只是「提示词正文」的不同形态，输出格式本来就由所选 skills 的输出契约规定。强调只负责"不要夹带无关元素"，因此同一条可通用于散文类与 JSON 类 skills，不必按格式分叉。

| skills 类型 | 默认强调 |
|---|---|
| 产出单一交付物（id 含 `prompt`）：`h3-prompt-writing`、`qwen-image-t2i-prompt`、`qwen-image-edit-prompt` | 上面的强调说明 |
| `自动` | 同上（不预设具体 skills，用同一套通用强调） |
| **Anima 家族（id 含 `anima`）** | **专属强调**（见下）：**默认只给正面提示词**，负面仅在明确要求时追加，并禁止把分辨率/CFG/步数/采样器写进提示词 |
| 其余风格类 skills | 留空（它们会输出分镜、制作方案，且可能含澄清提问与方案选项，强加会破坏其交互设计） |

**Anima 家族的专属强调**（`ANIMA_FORMAT_NOTE`）——该家族默认**只交付正面提示词**（负面词只在用户明确要求、或用户表示自己那边没有负面词时才追加），并且**任何参数都不出现在输出里**：

```
【输出要求】只输出 Anima 提示词正文本身：**默认只给正面提示词**，不要输出负面提示词、
不要加 `Positive prompt` 之类的标题行、不要加 Markdown 代码块围栏。只有当用户明确要求
负面词 / negative prompt，或表示自己那边没有设置负面词时，才追加第二段 `Negative prompt`。
不要输出开头说明、结尾建议、解释、总结、前言或后记；不要把分辨率、宽高比、种子、CFG、
步数、采样器或模型文件名写进提示词，也不要另附 `Suggested settings` 或任何参数数值——
这些都属于 ComfyUI 工作流设置，被问到时只回一句「由工作流设置决定」。也不要复述本条要求。
```

> **为什么强调里不留「用户索要参数时单列一段」的出口**：README 与各 Anima skills 的输出契约
> 都写明「被问到参数只回一句『由工作流设置决定』」。强调里若再开一个 `Suggested settings`
> 的例外口，等于把参数段重新放回输出，与契约直接矛盾——实测模型会顺着这个出口夹带参数。
> 因此该出口已删除，并由 `test_anima_format_note_has_no_parameter_escape_hatch` 守卫。

**Anima skills 的输出默认**（12 个 skills 的 `## 输出契约` 小节统一约定）：

| 情形 | 输出 |
|---|---|
| 用户没提负面词（默认） | **只给正面提示词正文**，无标题行、无代码块围栏，可直接粘进生成节点 |
| 用户明确要负面词 / 说"我这边没有负面词" | `Positive prompt` / `Negative prompt` 两段，负面词按对应小节裁剪 |
| 问到参数（宽高比 / 分辨率 / 步数 / CFG / 采样器 / 种子） | **只回一句「由工作流设置决定」**，不给数值、不附 `Suggested settings` 段 |
| `anima-prompt-negative` 被调用 | 默认成对交付（触发条件本身就是用户要负面词） |
| `anima-prompt-optimize` 且原提示词自带负面词 | 输出两段（修复负面词） |
| `anima-prompt-regional` | `Global prompt` + 区域块 / `Whole image context` + `Masked area prompt` 为**结构必需**块标签；`Negative prompt` 仅在明确要求时追加 |

> 各 skills 的 `## 示例` 仍按含 `Negative prompt` 的两段形态演示，用来说明"用户要负面词时该怎么写"。
> **Anima skills 正文里不再出现任何具体参数值**（分辨率区间、步数、CFG、采样器名等一律移除），
> 从源头消除"模型顺手把参数段一起输出"的可能；参数参考只在 [Anima 官方模型卡](https://huggingface.co/circlestone-labs/Anima) 与 [ComfyUI 官方教程](https://docs.comfy.org/tutorials/image/anima/anima)。

行为规则：

| 当前 `附加说明` 值 | 结果 |
|---|---|
| 空 / 等于已知默认强调 | 自动替换为所选 skills 对应的强调说明 |
| 用户自定义内容 | **永不覆盖** |

- **可随时删除**：清空文本框即完全不追加任何说明（测试覆盖）。
- 若某个 skills 需要不同的强调，可在其 `SKILL.md` front matter 用 `extra-note:` 自行声明，优先级高于默认值——新增此类 skills 无需改代码。

「自定义LLM」在 `skills` 接入自动清单时，额外提供三个多轮控制参数：

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `skills最大轮数` | INT | 8 | 最大读取往返轮数，防止模型不守协议导致死循环 |
| `skills单次读取上限` | INT | 72000 | 单次读取文件的字符上限，超出截断 |
| `skills累计上限` | INT | 300000 | 多轮累计注入的字符上限，防止上下文无限膨胀 |

### 生成后控制（随机数控制）

「自定义LLM」的「种子」使用 **ComfyUI 官方的 `control_after_generate` 机制**（与「K采样器 / KSampler」等节点完全一致），在「种子」旁自动出现「生成后控制」下拉，**仅控制种子本身**：

| `生成后控制` | 行为 |
|---|---|
| `固定值` | 种子保持不变 |
| `递增值` | 每次生成后种子 +1 |
| `递减值` | 每次生成后种子 -1 |
| `随机值` | 每次生成后随机一个新的种子（`control_after_generate: true` 时前端默认项） |

实现方式（与 KSampler 同源，节点后端不参与）：

- 后端只在「种子」输入上声明 `"control_after_generate": True`；
- 前端据此自动生成配套的「生成后控制」下拉，该下拉 `serialize: false`，**不会出现在发给后端的 prompt 里**；
- 生成结束后由前端在本地按所选模式改写「种子」控件值，下一次执行即使用新种子——因此节点**无需**状态缓存、**无需** `ui` 回填、**也无需** `IS_CHANGED`。

> 这也意味着「生成后控制」的选项名与界面表现完全跟随官方前端（中文界面显示 `固定值/递增值/递减值/随机值`，英文界面显示 `fixed/increment/decrement/randomize`），本插件不另行定义控件。

- `种子` 默认 `-1`，此时**不发送** `seed` 字段（由服务端随机）；设为 `>= 0` 时原样发送；
- 该机制只管「种子」，不会改动温度、top_p 等其它采样参数。

### 空输出处理

接口返回 200 但内容为空时，节点**不再静默输出空字符串**（否则下游「展示文本（多重）」看起来像没执行），而是给出带原因的明确报错：

| 情况 | 处理 |
|---|---|
| `finish_reason=length`（被截断） | 报错提示调大「最大token数」，**不重试**（确定性原因） |
| `finish_reason=stop` 但内容空 | 视为瞬时抖动，**自动重试**最多 2 次 |
| `content_filter` | 报错提示内容被安全策略过滤 |
| `tool_calls` / `function_call` | 报错提示模型尝试调用工具（本节点未启用工具协议） |
| `content` 为空但有 `reasoning_content` | 回退使用思考内容（不返回空） |
| `content` 为 parts 数组 | 自动拼接其中的文本 |
| `content` 为 `None` / 全空白 / 缺少字段 | 报错并列出常见原因 |

`最大token数` 默认值已从 1024 提高到 **8192**——推理模型（如 `deepseek-reasoner`）会先消耗大量 token 用于思考，1024 很容易在思考阶段就耗尽而导致最终答案为空。

### 简略上下文（自定义LLM 的第二个输出端口）

「自定义LLM」除「输出文本」外，另有 **「简略上下文」** 输出端口，把**本次运行**的轨迹拼成纯文本，用来核对"跑了几步、读了哪些 skills、最终产出了什么"：

| 内容 | 说明 |
|---|---|
| 模型 / 模式 | 本次使用的模型，以及单轮请求还是 skills 按需读取（含最大轮数） |
| 步数 | 实际发生的接口请求次数（多轮时每一步 ↔ 一次请求） |
| 输入 skills（仅名称） | 从 skills 输入文本中确定性解析出的 skills **名称**，不含描述与正文 |
| 调用的 skills | 实际 `READ:` 读取过的 skills 及次数 |
| 读取明细 | 逐个文件的相对路径与注入字符数 |
| 每一步 | 动作（读取了哪个文件 / 读取失败 / 达到上限 / 直接作答）、**思考**、回复 |
| 最终输出 | 节点实际返回给下游的完整文本 |

```
# 简略上下文（本次运行，由节点代码拼装，未经模型总结）

- 模型：deepseek-chat
- 模式：skills 按需读取（渐进式披露，最多 8 轮）
- 步数：3 步（每步 = 一次接口请求）
- 输入 skills（仅名称，共 1 个）：qwen-image-t2i-prompt
- 调用的 skills：qwen-image-t2i-prompt（2 次）
- 读取明细（共 2 个文件，注入 13,715 字符）：
  - qwen-image-t2i-prompt/SKILL.md（3,807 字符）
  - qwen-image-t2i-prompt/references/t2i-rewrite-guide.md（9,908 字符）

## 第 1 步
- 动作：读取 qwen-image-t2i-prompt/SKILL.md（3,807 字符）并回注对话
- 思考：
  先读改写指南正文再动手。
- 回复：
  READ: qwen-image-t2i-prompt

## 第 3 步
- 动作：直接作答（本轮未请求读取）
- 思考：（无）

## 最终输出

一只橘猫坐在窗台上的写实照片
```

- **完全由节点代码确定性拼装，不额外调用模型做任何总结**——因此「步数」就等于实际接口请求次数，生成这份记录**不会多请求一次**；
- 输入 skills **只记名称**（自动清单逐行解析 `- id（显示名）: 描述`；手动选择只认首行 `# 已选 skills：id`），不复制正文；
- 模型的思考字段（`reasoning_content` / `reasoning`）此前只在 `content` 为空时被当作兜底，现在会被**独立保留**下来供核对；模型未返回思考时显示「（无）」；
- 单轮请求同样产出该端口（1 步 + 最终输出），因此可直接把它接到「展示文本（多重）」查看。

### skills 目录约定

- 每个 skills 为 `skills/` 或 `custom_skills/` 下的一个子目录，目录名即 skills id；
- 子目录中必须包含 `SKILL.md`（skills 正文）；
- `SKILL.md` 顶部可选 YAML front matter：`name` / `description` / `display_name` / `version` / `tags` / `extra-note`；
- 子目录可选 `meta.yaml`，提供 `display-name-zh`、`summary-cn`、`version`、`tag-cn`、`extra-note` 等元数据；
- `extra-note` 用于为该 skills 指定默认「附加说明」（覆盖内置的通用强调），不写则按 id 规则自动决定；
- `references/` 下的 `.md` / `.txt` 会作为参考资料一并读取（受「最大字符数」限制）；
- skills id 只能包含小写字母、数字、点、下划线与连字符，且不能为 `auto`；
- 内置 `skills/` 优先，`custom_skills/` 中同 id 的 skills 不会覆盖内置。

> **变更检测覆盖整个 skills 目录。** 发现结果按「目录签名」缓存，节点 `IS_CHANGED` 也返回该签名。
> 签名遍历每个 skills 子目录下的**全部文件**（`SKILL.md`、`meta.yaml`、`references/` 下的参考资料……），
> 记录相对路径 + mtime + 大小。因此**改动参考资料同样会让缓存失效并触发重新执行**——
> 早先的签名只覆盖 `SKILL.md` / `meta.yaml` 两个固定文件，改了 `references/` 下的内容
> 节点不会重新执行，用户读到的仍是旧内容且没有任何提示。

自定义 skills 的详细写法见 [custom_skills/README.md](custom_skills/README.md)。

> **安全边界：** skills 内容仅作为模型提示词指导，节点不会执行其中声明的脚本、工具、网络调用或审批流程。

## 移植节点说明

### H3 低噪细节精修（H3 Sigma Refiner）

移植自 [ComfyUI-YCNodes-MiniMax-H3](https://github.com/yichengup/ComfyUI-YCNodes-MiniMax-H3.git)（作者：亦诚，MIT 许可）的 `H3 Sigma Refiner` 节点，算法逻辑与原实现保持一致，按本项目规范调整了注册键名（`YTmmiH3SigmaRefiner`）、分类（`YTmmi/minimax-h3`）、控件中文名与 `DESCRIPTION`，并补充了输入类型校验。

**原理：** 对低 Sigma 区间进行局部加步——保留原始调度的高噪头部不动，从阈值点起把尾部重采样成更长、更平滑的曲线，让模型在细节收尾阶段多走几步，消除高速运动边缘的马赛克与像素紊乱。

**接线：** 插在调度器和采样器之间。

```
BasicScheduler -> (sigmas) -> H3 低噪细节精修 -> (sigmas) -> SamplerCustomAdvanced
```

| 参数 | 类型 | 默认值 | 范围 | 说明 |
|---|---|---|---|---|
| `噪声序列` | SIGMAS | - | - | 原始噪声序列 |
| `额外步数` | INT | 1 | 0 ~ 15 | 低噪区间额外增加的步数，为 0 时原样返回 |
| `起始Sigma` | FLOAT | 0.7 | 0.0 ~ 20.0 | 启动加步的 Sigma 阈值 |
| `结束Sigma` | FLOAT | 0.0 | 0.0 ~ 5.0 | 结束细化的 Sigma 边界 |
| `插值曲线` | COMBO | cosine | cosine / linear / exponential | 尾部插值分布曲线 |

**插值曲线：**

- **cosine**（默认）：趋近 0 时分布更密，消噪最丝滑
- **linear**：均匀分布
- **exponential**：能量前移，尾部大步走向末点

## 安装

将本仓库克隆或下载到 ComfyUI 的自定义节点目录：

```bash
cd ComfyUI/custom_nodes/
git clone https://github.com/ytmmi/ComfyUI-YTmmi_Tools
```

或手动将文件夹放置到 `ComfyUI/custom_nodes/` 下，然后重启 ComfyUI。

## 项目结构

```
ComfyUI-YTmmi_Tools/
├── node/                            # 节点代码，按 CATEGORY 分类存放
│   ├── __init__.py                  # node 包汇总入口
│   ├── image/                       # YTmmi/image 分类（图像/二维码）
│   │   ├── batch_load_images_node.py   # 批量加载图像
│   │   ├── create_solid_color_node.py  # 创建纯色图像
│   │   ├── image_merge_node.py         # 图像合并
│   │   ├── image_to_png_node.py        # 图像转为PNG
│   │   ├── mask_crop_image_node.py     # 遮罩裁剪图像
│   │   ├── qr_code_create_node.py      # 创建二维码
│   │   ├── qr_code_decode_node.py      # 二维码识别
│   │   ├── save_jpg_node.py            # 保存JPG图像
│   │   └── text_watermark_node.py      # 文字水印
│   ├── video/                       # YTmmi/video 分类
│   │   ├── preview_video_node.py       # 预览视频
│   │   └── video_concat_node.py        # 视频拼接
│   ├── utility/                     # YTmmi/utility 分类
│   │   ├── display_text_node.py        # 展示文本（多重）
│   │   ├── key_storage_node.py         # 密钥储存器
│   │   ├── pixel_size_to_ratio_node.py # 像素大小指定比例
│   │   └── skills_manager_node.py      # skills管理器
│   ├── text/                        # YTmmi/text 分类
│   │   ├── custom_llm_node.py          # 自定义LLM
│   │   └── save_json_file_node.py      # 保存JSON文件
│   └── minimax_h3/                  # YTmmi/minimax-h3 分类
│       └── h3_sigma_refiner_node.py    # H3 低噪细节精修
├── skills/                          # 内置 skills（23 个：MiniMax H3 官方 9 个 + Qwen-Image 2.1 提示词 2 个 + Anima 二次元 12 个）
├── custom_skills/                   # 自定义 skills（用户自行添加）
├── js/
│   ├── auto_fill_widget.js         # 前端扩展：执行后自动回填控件值
│   ├── custom_llm_widget.js       # 前端扩展：自定义LLM获取模型按钮
│   ├── display_text_widget.js      # 前端扩展：展示文本（多重）动态输入接口与结果回填
│   ├── key_storage_widget.js      # 前端扩展：密钥储存器保存/删除按钮与下拉
│   ├── skills_manager_widget.js   # 前端扩展：skills管理器刷新skills按钮
│   └── video_concat_widget.js      # 前端扩展：视频拼接动态输入接口
├── test/
├── locales/
├── __init__.py
├── requirements.txt
└── README.md
```

## 致谢

本项目的以下功能参考/移植自开源仓库，感谢原作者的实现：

- [ComfyUI-YCNodes-MiniMax-H3](https://github.com/yichengup/ComfyUI-YCNodes-MiniMax-H3.git) — 专为 MiniMax H3 视频模型打造的 ComfyUI 节点包（作者：亦诚，MIT 许可）
  - **H3 低噪细节精修**（H3 Sigma Refiner）节点移植自该仓库
- [ComfyUI_Qwen_H3_Prompt](https://github.com/chflame163/ComfyUI_Qwen_H3_Prompt.git) — 在 ComfyUI 内使用本地 Qwen3.8 驱动 Minimax H3 官方 skills 生成 H3 提示词
  - **skills管理器** 与 **自定义LLM 的 skills 接口** 参考该仓库的 skills 管理方式实现
  - `skills/` 目录中的 9 个 MiniMax H3 skills 来自 [MiniMax-AI/MiniMax-H3](https://github.com/MiniMax-AI/MiniMax-H3) 官方 skills
- **Qwen-Image 2.1 提示词改写**（`qwen-image-t2i-prompt`、`qwen-image-edit-prompt`）— 由用户提供的 Qwen-Image 2.1 系统提示词改写为 skills；原始系统提示词逐字保留在各自的 `references/` 下（SHA256 与源文件一致）
- **Anima 二次元插画 skills**（`anima-*`，12 个）— 基于 [CircleStone Labs / Comfy Org Anima 官方模型卡](https://huggingface.co/circlestone-labs/Anima) 与 [ComfyUI 官方 Anima 教程](https://docs.comfy.org/tutorials/image/anima/anima) 整理；分区/局部重绘与提示词工程写法参考社区项目 [anima-prompt-crafter-skill](https://github.com/AI-KSK/anima-prompt-crafter-skill) 与 [comfyui-good-anima](https://github.com/ShiroEirin/comfyui-good-anima)（Anima 模型本身由 CircleStone Labs 发布，遵循其非商业许可）

## 许可证

MIT
