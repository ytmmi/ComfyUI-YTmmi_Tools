# ComfyUI-YTmmi_Tools

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

ComfyUI 自定义节点扩展包，提供图像、视频、文本与二维码等常用工具节点，并内置 OpenAI 兼容接口的大模型调用与 skills 提示词工程能力，可用于提示词编写、素材批处理与工作流自动化。

## 功能特性

- **图像处理**：保存与格式转换、纯色图像生成、文字水印、按遮罩裁剪与贴回、批量加载
- **视频处理**：多段视频拼接、视频预览
- **数据处理**：JSON 导出、像素尺寸比例换算、多重文本展示、API 密钥加密存储
- **大模型与 Skills**：调用任意 OpenAI 兼容接口，支持 skills 按需读取与多轮对话
- **二维码**：二维码 / 条形码识别与生成
- **MiniMax H3**：低噪细节精修采样节点

## 环境要求

- 已安装可正常运行的 ComfyUI（自带 torch / numpy 环境）
- Python 依赖（见 `requirements.txt`）：

```text
Pillow>=10.0.0
pyzbar>=0.1.9
qrcode>=8.0
av>=12.0.0
```

> 二维码识别依赖 pyzbar，其底层调用 zbar 动态库。Linux 需安装 `libzbar0`（Debian/Ubuntu）或 `zbar`（RHEL 系）；macOS 可执行 `brew install zbar`；Windows 通常需安装 Visual C++ 运行库。

## 安装

### 方式一：ComfyUI Manager

在 ComfyUI Manager 中搜索 `YTmmi` 或 `ComfyUI-YTmmi_Tools`，点击安装后重启 ComfyUI。

### 方式二：手动安装

```bash
cd ComfyUI/custom_nodes/
git clone https://github.com/ytmmi/ComfyUI-YTmmi_Tools.git
cd ComfyUI-YTmmi_Tools
pip install -r requirements.txt
```

安装完成后重启 ComfyUI，节点会出现在 `YTmmi` 分类下。

## 节点列表

### 图像处理（`YTmmi/image`）

| 节点 | 注册名 | 说明 |
|---|---|---|
| 保存jpg图像 | `SaveJPGNode` | 保存 JPEG 图像，工作流信息写入 EXIF |
| 图像转为png | `ImageToPngNode` | 保存 PNG 图像，同时保留 jpg 图像内的工作流信息 |
| 创建纯色图像 | `CreateSolidColorNode` | 按指定宽高、颜色与不透明度生成纯色图像 |
| 遮罩裁剪图像 | `MaskCropImageNode` | 按遮罩区域裁剪图像与遮罩，并输出裁剪框坐标 |
| 图像合并 | `ImageMergeNode` | 按坐标把上层图像贴到底层图像，支持遮罩蒙版 |
| 文字水印 | `TextWatermarkNode` | 为图像添加文字水印，可自定义字体、大小、位置、颜色与透明度 |
| 批量加载图像 | `BatchLoadImagesNode` | 从文件夹批量加载图像，支持排序、位置偏移与种子控制 |
| 二维码识别 | `QrCodeDecodeNode` | 识别图像中的二维码 / 条形码，输出解码文本 |
| 创建二维码 | `CreateQrCodeNode` | 根据文本生成二维码图片，可设置容错等级、边长与边距 |

### 视频处理（`YTmmi/video`）

| 节点 | 注册名 | 说明 |
|---|---|---|
| 视频拼接 | `VideoConcatNode` | 将多段视频（原生 `VIDEO` 类型）按接口顺序拼接，最多 10 路输入 |
| 预览视频 | `PreviewVideoNode` | 将视频保存为临时文件并在 ComfyUI 中播放预览，视频原样透传 |

### 数据处理（`YTmmi/utility`、`YTmmi/text`）

| 节点 | 注册名 | 分类 | 说明 |
|---|---|---|---|
| 像素大小指定比例 | `PixelSizeToRatioNode` | `YTmmi/utility` | 输入宽高，按指定宽高比换算，保持像素总数基本不变 |
| 展示文本（多重） | `DisplayTextNode` | `YTmmi/utility` | 展示上游节点 0~8 号输入口的字符串信息 |
| 密钥储存器 | `KeyStorageNode` | `YTmmi/utility` | 加密保存 API 密钥与接口地址，按名称输出 |
| skills管理器 | `SkillsManagerNode` | `YTmmi/utility` | 管理并读取内置与自定义 skills |
| 保存json文件 | `SaveJsonFileNode` | `YTmmi/text` | 将 JSON 数据写入磁盘文件 |
| 自定义LLM | `CustomLLMNode` | `YTmmi/text` | 调用 OpenAI 兼容接口生成文本，支持 skills 与图片输入 |

### MiniMax H3（`YTmmi/minimax-h3`）

| 节点 | 注册名 | 说明 |
|---|---|---|
| H3 低噪细节精修 | `YTmmiH3SigmaRefiner` | 在低噪点区（低 Sigma）局部加密采样步长，消解运动物体的边缘像素颗粒 |

## 核心节点说明

### 遮罩裁剪图像 与 图像合并

这一对节点用于「按遮罩抠出主体 → 处理 → 原样贴回」的工作流：**遮罩裁剪图像** 负责裁剪并输出裁剪框坐标，**图像合并** 负责按坐标还原。

```text
[图像] ─┐
        ├─> [遮罩裁剪图像] ─> 原始图像 ──┐
[遮罩] ─┘        │                      ├─> [图像合并] ─> 图像
                 ├─> 裁剪图像 ──────────┘        ▲
                 ├─> 裁剪遮罩 ────────（可选：蒙版，作用于上层）
                 └─> 坐标x / 坐标y / 宽 / 高 ────┘
```

#### 遮罩裁剪图像

取遮罩非零区域的外接尺寸作为裁剪尺寸，以遮罩重心为中心定位裁剪框，再把裁剪框夹取到画面范围内；**只处理单张图像**。

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `图像` | IMAGE | - | 待裁剪的图像，只接受单张 |
| `遮罩` | MASK | - | 裁剪依据，只接受单张；全空白时报错 |
| `裁剪乘数` | FLOAT | 1.0 | 裁剪框相对遮罩外接尺寸的倍率 |

输出（自上而下）：`原始图像`、`裁剪图像`、`裁剪遮罩`、`坐标x`、`坐标y`、`宽`、`高`。

- `原始图像` — 原样透传输入图像，可直接作为「图像合并」的画布；
- `裁剪图像` / `裁剪遮罩` — 按裁剪框裁出的结果，尺寸等于 `高 × 宽`；
- `坐标x` / `坐标y` / `宽` / `高` — 裁剪框位置与尺寸，直接连接「图像合并」即可还原。

裁剪框尺寸取遮罩外接尺寸 `max − min + 1`，因此 `裁剪乘数 = 1` 时遮罩的非零像素不会被裁掉。坐标端口为 `INT,FLOAT` 联合类型，既能连接 `FLOAT` 坐标输入，也能连接 `INT` 输入。

#### 图像合并

把上层图像按坐标贴到底层图像（画布）上，超出画布的部分裁掉，画布尺寸不变。

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `图像0` / `图像1` | IMAGE | - | 两张待合并的图像 |
| `坐标x` / `坐标y` | FLOAT | 0 | `0 ~ 1`（不含 1）按画布尺寸的百分比，其余按像素；可为负 |
| `宽` / `高` | INT | 0 | `0` 表示不限制（保持原尺寸），其余表示拉伸到指定尺寸 |
| `图层顺序翻转` | BOOLEAN | False | 默认「图像0」在下、「图像1」在上；打开后「图像1」在下 |
| `遮罩` | MASK | 可选 | 蒙版，作用于上面的那个图层：遮罩为 `1` 显示上层，为 `0` 透出底层 |

**画布 = 处于底层的那张图**：默认是「图像0」，打开「图层顺序翻转」后是「图像1」，百分比坐标按画布宽高换算。

- 蒙版只作用于上层，极性与 ComfyUI 官方「Image Composite Masked」一致；
- 蒙版会跟随上层的位置与尺寸，上层拉伸时蒙版同步缩放；
- 上层自带 alpha 时与蒙版相乘；不接遮罩时上层完全不透明。

还原时把「遮罩裁剪图像」的 `原始图像` 接到 `图像0`、`裁剪图像` 接到 `图像1`，并连上 `坐标x / 坐标y / 宽 / 高` 即可；若要把 `裁剪遮罩` 接到 `遮罩`，注意该遮罩是裁剪后的，与上层图层同尺寸。

### 自定义LLM

调用任意 OpenAI 兼容格式的在线大模型接口，返回生成文本。

- **接口配置**：API Key + 接口地址 + 模型名 + 提示词；
- **模型列表**：模型名为下拉菜单，点击节点上的「获取模型」按钮可自动拉取接口可用模型列表；
- **密钥来源**：可从「密钥储存器」中选择已保存的密钥，也可直接填写；
- **采样参数**：温度、最大 token、top_p、种子，以及官方的「生成后控制」；
- **skills 输入**：接入「skills管理器」输出的指导文本或自动清单，自动清单模式下与模型多轮按需读取，无需接口支持 tools；
- **图片输入**：最多 9 张，默认只显示 1 个图片输入口，连接后自动显现下一张；按 OpenAI 多模态格式发送，可适配支持视觉输入的模型。

输出端口：`输出文本`、`简略上下文`。

#### 生成后控制

「种子」使用 ComfyUI 官方的 `control_after_generate` 机制（与 KSampler 等节点一致），节点旁自动出现「生成后控制」下拉，仅控制种子本身：

| 选项 | 行为 |
|---|---|
| 固定值 | 种子保持不变 |
| 递增值 | 每次生成后种子 +1 |
| 递减值 | 每次生成后种子 -1 |
| 随机值 | 每次生成后随机一个新的种子 |

`种子` 默认为 `-1`，此时不发送 `seed` 字段（由服务端随机）；设为 `>= 0` 时原样发送。该机制不会改动温度、top_p 等其它采样参数。

#### 空输出处理

接口返回 200 但内容为空时，节点会给出带原因的明确报错，而不是静默输出空字符串：

| 情况 | 处理 |
|---|---|
| `finish_reason=length`（被截断） | 提示调大「最大token数」，不重试 |
| `finish_reason=stop` 但内容为空 | 视为瞬时抖动，自动重试最多 2 次 |
| `content_filter` | 提示内容被安全策略过滤 |
| `tool_calls` / `function_call` | 提示模型尝试调用工具（本节点未启用工具协议） |
| `content` 为空但有 `reasoning_content` | 回退使用思考内容 |
| `content` 为 parts 数组 | 自动拼接其中的文本 |
| `content` 为 `None` / 全空白 / 缺少字段 | 报错并列出常见原因 |

`最大token数` 默认为 **8192**，避免推理模型在思考阶段耗尽 token 导致最终答案为空。

#### 简略上下文

「简略上下文」端口把本次运行的轨迹拼成纯文本，便于核对「跑了几步、读了哪些 skills、最终产出了什么」：

| 内容 | 说明 |
|---|---|
| 模型 / 模式 | 本次使用的模型，以及单轮请求还是 skills 按需读取 |
| 步数 | 实际发生的接口请求次数 |
| 输入 skills（仅名称） | 从 skills 输入文本中解析出的 skills 名称 |
| 调用的 skills | 实际读取过的 skills 及次数 |
| 读取明细 | 逐个文件的相对路径与注入字符数 |
| 每一步 | 动作、思考、回复 |
| 最终输出 | 节点实际返回给下游的完整文本 |

该文本完全由节点代码确定性拼装，不会额外调用模型做总结。

### skills管理器

管理并读取插件 `skills/`（内置）与 `custom_skills/`（自定义）目录中的 skills。

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `选择skills` | COMBO | 自动 | `自动` 表示只输出清单与读取协议，由模型多轮按需读取；也可选具体 skills 直接输出其完整指导文本 |
| `模式` | COMBO | auto | 任务模式，仅在「选择skills」为 `自动` 时生效，用于按任务家族筛选清单 |
| `包含参考文件` | BOOLEAN | True | 是否一并读取 skills 的 `references/` 参考资料（仅「具体 skills」模式生效） |
| `最大字符数` | INT | 72000 | 指导文本字符上限，超出后不再追加参考资料 |
| `附加说明` | STRING | 按 skills | 追加到 skills 文本末尾的补充说明，可按所选 skills 自动填充，也可自行改写或清空 |

输出端口：`skills`、`skills名称`、`skills目录`。

「刷新skills」等操作不使用弹窗，刷新结果通过按钮文字短暂变化与控制台日志反馈，避免打断画布操作。

#### 模式与任务家族

「模式」仅在「选择skills」为 `自动` 时生效，用于限定自动挑选 skills 的任务家族：

| `模式` | 任务家族 | 自动清单包含 |
|---|---|---|
| `auto` | 全部 | 全部内置 skills（不筛选） |
| `H3-t2va` / `H3-i2va` / `H3-fl2va` / `H3-l2va` / `H3-ref2va` | H3 视频 | H3 家族 skills |
| `qwen-image-t2i` | Qwen-Image 文生图 | `qwen-image-t2i-prompt` |
| `qwen-image-edit` | Qwen-Image 图像编辑 | `qwen-image-edit-prompt` |
| `Anima` | Anima 二次元插画 | `anima-*` 系列 skills |

手动指定具体 skills 时「模式」不再参与筛选，加载该 skills 的全部参考资料。

### H3 低噪细节精修

移植自 [ComfyUI-YCNodes-MiniMax-H3](https://github.com/yichengup/ComfyUI-YCNodes-MiniMax-H3) 的 `H3 Sigma Refiner` 节点，算法逻辑与原实现保持一致。

**原理**：对低 Sigma 区间进行局部加步——保留原始调度的高噪头部不动，从阈值点起把尾部重采样成更长、更平滑的曲线，让模型在细节收尾阶段多走几步，减少高速运动边缘的像素紊乱。

**接线**：插在调度器与采样器之间。

```text
BasicScheduler -> (sigmas) -> H3 低噪细节精修 -> (sigmas) -> SamplerCustomAdvanced
```

| 参数 | 类型 | 默认值 | 范围 | 说明 |
|---|---|---|---|---|
| `噪声序列` | SIGMAS | - | - | 原始噪声序列 |
| `额外步数` | INT | 1 | 0 ~ 15 | 低噪区间额外增加的步数，为 0 时原样返回 |
| `起始Sigma` | FLOAT | 0.7 | 0.0 ~ 20.0 | 启动加步的 Sigma 阈值 |
| `结束Sigma` | FLOAT | 0.0 | 0.0 ~ 5.0 | 结束细化的 Sigma 边界 |
| `插值曲线` | COMBO | cosine | cosine / linear / exponential | 尾部插值分布曲线 |

- **cosine**（默认）：趋近 0 时分布更密，消噪更平滑；
- **linear**：均匀分布；
- **exponential**：能量前移，尾部大步走向末点。

## Skills

「skills管理器」与「自定义LLM」的 skills 接口参考 [ComfyUI_Qwen_H3_Prompt](https://github.com/chflame163/ComfyUI_Qwen_H3_Prompt) 的 skills 管理方式实现：插件启动时扫描 `skills/`（内置）与 `custom_skills/`（自定义）目录，每个 skills 为其中一个子目录，目录中必须包含 `SKILL.md`。

```text
[skills管理器] -> (skills) -> [自定义LLM] -> 输出文本
```

### 两种 skills 模式

| `选择skills` | 行为 | 上下文占用 |
|---|---|---|
| **自动**（默认） | 只把 skills 清单与读取协议发给模型，模型按需请求读取正文，多轮往返直到给出答案（渐进式披露） | 首轮较小，按家族筛选后更少 |
| 具体 skills | 直接输出该 skills 的完整指导文本（含 `references/`），单轮请求 | 取决于 skills 体积 |

选择「自动」后，模型可单独输出一行读取指令，节点读取对应文件并回注对话，继续下一轮：

```text
READ: <skills名称>                  # 读取该 skills 的 SKILL.md
READ: <skills名称>/<相对路径>        # 读取该 skills 内的参考文件
```

- 不依赖接口的 `tools` / function calling 支持，对各类中转端点兼容性较好；
- 若模型首轮即可作答，则只请求一次，不产生额外往返；
- 若模型持续请求读取，受 `skills最大轮数`（默认 8）保护并强制收尾；
- 读取失败会把错误回注给模型，让其改名重试，而不是直接中断；
- 图片输入挂在最初那条 user 消息上，后续每一轮仍然可见。

「自定义LLM」在 skills 接入自动清单时，额外提供三个多轮控制参数：

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `skills最大轮数` | INT | 8 | 最大读取往返轮数，防止模型不守协议导致死循环 |
| `skills单次读取上限` | INT | 72000 | 单次读取文件的字符上限，超出截断 |
| `skills累计上限` | INT | 300000 | 多轮累计注入的字符上限，防止上下文无限膨胀 |

### 内置 skills

`skills/` 内置 23 个 skills（4 个家族）：

| 家族 | skills | 说明 |
|---|---|---|
| H3 视频 | `h3-prompt-writing` | MiniMax H3 视频提示词书写（T2VA / I2VA / FL2VA / L2VA / Ref2VA） |
| H3 视频 | 其余 8 个 | MiniMax H3 官方风格类 skills（3D 动画、品牌宣传、纸艺定格等） |
| Qwen-Image | `qwen-image-t2i-prompt` | Qwen-Image 2.1 文生图提示词改写 |
| Qwen-Image | `qwen-image-edit-prompt` | Qwen-Image 2.1 图像编辑提示词改写 |
| Anima | `anima-prompt-format` | 提示词格式化（官方标签顺序 + 版本化质量前缀） |
| Anima | `anima-motion-boost` | 动作增强（动作节拍、动态构图、运动证据） |
| Anima | `anima-style-control` | 风格控制（媒介 × 渲染 × 年代 × 版式） |
| Anima | `anima-style-boost` | 风格增强（线 → 上色 → 色彩 → 光照 → 背景） |
| Anima | `anima-prompt-optimize` | 提示词优化（顺序 / 空格 / 一致性 / 冲突 / 冗余） |
| Anima | `anima-composition-optimize` | 构图优化（景别 × 机位 × 主体摆放 × 前后景层次） |
| Anima | `anima-color-harmony` | 配色与颜色搭配（配色骨架、明度/饱和度结构、光的颜色） |
| Anima | `anima-prompt-artist` | 画师标签与混合 |
| Anima | `anima-prompt-character` | 角色一致性与三视图 |
| Anima | `anima-prompt-negative` | 负面提示词与质量前缀 |
| Anima | `anima-prompt-regional` | 分区与局部重绘 |
| Anima | `anima-lora-trigger` | LoRA 触发词与权重 |

12 个 Anima skills 共用一份基准文档 [`skills/anima-prompt-format/references/anima-prompt-baseline.md`](skills/anima-prompt-format/references/anima-prompt-baseline.md)（标签顺序、质量前缀、权重语法、版本差异与能力边界）。

### skills 目录约定

- 每个 skills 为 `skills/` 或 `custom_skills/` 下的一个子目录，目录名即 skills id；
- 子目录中必须包含 `SKILL.md`（skills 正文）；
- `SKILL.md` 顶部可选 YAML front matter：`name` / `description` / `display_name` / `version` / `tags` / `extra-note`；
- 子目录可选 `meta.yaml`，提供 `display-name-zh`、`summary-cn`、`version`、`tag-cn`、`extra-note` 等元数据；
- `extra-note` 用于为该 skills 指定默认「附加说明」，不写则按 id 规则自动决定；
- `references/` 下的 `.md` / `.txt` 会作为参考资料一并读取（受「最大字符数」限制）；
- skills id 只能包含小写字母、数字、点、下划线与连字符，且不能为 `auto`；
- 内置 `skills/` 优先，`custom_skills/` 中同 id 的 skills 不会覆盖内置。

自定义 skills 的详细写法见 [custom_skills/README.md](custom_skills/README.md)。

> **安全边界**：skills 内容仅作为模型提示词指导，节点不会执行其中声明的脚本、工具、网络调用或审批流程。

## 项目结构

```text
ComfyUI-YTmmi_Tools/
├── node/                              # 节点代码，按 CATEGORY 分类存放
│   ├── __init__.py                    # node 包汇总入口
│   ├── image/                         # YTmmi/image 分类（图像 / 二维码）
│   ├── video/                         # YTmmi/video 分类
│   ├── text/                          # YTmmi/text 分类
│   ├── utility/                       # YTmmi/utility 分类
│   └── minimax_h3/                    # YTmmi/minimax-h3 分类
├── skills/                            # 内置 skills（MiniMax H3 + Qwen-Image + Anima）
├── custom_skills/                     # 自定义 skills（用户自行添加）
├── js/                                # 前端扩展脚本（按钮、动态输入接口、结果回填等）
├── test/                              # 单元测试
├── data/                              # 运行时数据（密钥存储等，不纳入版本控制）
├── __init__.py                        # 插件入口，注册节点与前端目录
├── requirements.txt
├── README.md
└── .gitignore
```

## 贡献

欢迎通过 Issue 反馈问题或提出建议，也欢迎提交 Pull Request 改进节点与 skills。提交前建议在本地运行 `test/` 下的单元测试。

## 致谢

本项目部分功能参考或移植自以下开源项目，感谢原作者的实现：

- [ComfyUI-YCNodes-MiniMax-H3](https://github.com/yichengup/ComfyUI-YCNodes-MiniMax-H3) — 专为 MiniMax H3 视频模型打造的 ComfyUI 节点包
  - **H3 低噪细节精修**节点移植自该仓库
- [ComfyUI_Qwen_H3_Prompt](https://github.com/chflame163/ComfyUI_Qwen_H3_Prompt) — 在 ComfyUI 内使用本地 Qwen 模型驱动 Minimax H3 官方 skills 生成提示词
  - **skills管理器**与**自定义LLM 的 skills 接口**参考该仓库的 skills 管理方式实现
  - `skills/` 目录中的 9 个 MiniMax H3 skills 来自 [MiniMax-AI/MiniMax-H3](https://github.com/MiniMax-AI/MiniMax-H3) 官方 skills
- **Qwen-Image 2.1 提示词改写**（`qwen-image-t2i-prompt`、`qwen-image-edit-prompt`）— 基于 Qwen-Image 2.1 系统提示词整理为 skills 形式，完整原文逐字保存在各自的 `references/` 下
- **Anima 二次元插画 skills**（`anima-*`，12 个）— 基于 [CircleStone Labs / Comfy Org Anima 官方模型卡](https://huggingface.co/circlestone-labs/Anima) 与 [ComfyUI 官方 Anima 教程](https://docs.comfy.org/tutorials/image/anima/anima) 整理；分区 / 局部重绘与提示词工程写法参考社区项目 [anima-prompt-crafter-skill](https://github.com/AI-KSK/anima-prompt-crafter-skill) 与 [comfyui-good-anima](https://github.com/ShiroEirin/comfyui-good-anima)（Anima 模型本身由 CircleStone Labs 发布，遵循其非商业许可）

## 许可证

本项目基于 [MIT License](https://opensource.org/licenses/MIT) 开源。
