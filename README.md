# ComfyUI-YTmmi_Tools

ComfyUI 自定义节点工具集，提供图片保存、JSON 文件导出、图片文字水印、批量图片加载、skills 管理及 MiniMax H3 视频采样调度等功能。

## 节点说明

### 图片处理

- **保存jpg图像** — 保存 JPEG，工作流信息写入 EXIF
- **图像转为png** — 保存 PNG，同时保留jpg图像内的工作流信息
- **创建纯色图像** — 创建指定宽高和颜色的纯色图像
- **文字水印** — 为图片添加水印，支持文字、字体、大小、位置、颜色、透明度自定义
- **批量加载图像** — 加载指定路径文件夹内的图像，支持多种排序、位置偏移、种子控制与批量输出

### 视频处理

- **视频拼接** — 将多段视频（ComfyUI 原生 VIDEO 类型，与「加载视频」等节点兼容）按接口顺序拼接为一段视频，连接末尾输入时自动增加输入接口，最多支持 10 路输入
- **预览视频** — 将 VIDEO 视频保存为临时文件并在 ComfyUI 中播放预览，视频原样透传可继续接入下游

### 数据处理

- **保存json文件** — 将 JSON 数据写入磁盘文件
- **像素大小指定比例** — 输入宽高，按指定宽高比换算，保持像素总数基本不变
- **展示文本（多重）** — 展示上游节点的字符串信息（数字、字符串、文本、JSON 等），支持 0~8 号共 9 个输入口，默认只显示「输入0」，连接后自动显现下一个输入口；2 个及以上输入自动按输入口序号分隔标注展示；音频、潜空间、视频等类型自动过滤不展示；**输入口已连接但内容为空时显示 `[空文本]` 占位提示**（与「未连接」可区分）
- **密钥储存器** — 加密保存 API 密钥与接口地址（以系统用户名前5位派生密钥，防止插件目录被复制后泄露），点击「保存」加密存储、「删除密钥」删除「选择密钥」下拉中选中的预设；执行后按「选择密钥」下拉名称输出密钥/接口地址
- **自定义LLM** — 调用任意 OpenAI 兼容格式的在线大模型接口（API Key + 接口地址 + 模型名 + 提示词），返回生成文本；模型名为下拉菜单，点击节点上的「获取模型」按钮自动拉取接口可用模型列表，支持温度/最大token/top_p/种子；支持 **skills 输入接口**（接入「skills管理器」输出的指导文本或自动清单；自动清单时与模型多轮按需读取，无需 tools 支持）；支持图片输入（最多 9 张，默认只显示 1 个图片输入口，连接后自动显现下一张），按 OpenAI 多模态格式发送，可适配 DeepSeek V4.1 Flash（deepseek-flash）等支持视觉输入的模型
- **skills管理器** — 管理并读取插件 `skills/`（内置）与 `custom_skills/`（自定义）目录中的 skills；选「自动」时只输出 skills 清单与读取协议，由自定义LLM与模型多轮按需读取（渐进式披露，首轮省约 84% 上下文），选具体 skills 时输出其完整指导文本

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

**实测对比**（9 个内置 skills）：

| 方式 | 字符数 |
|---|---|
| 自动模式首轮（清单 + 协议） | 6,659 |
| 固定发送 h3-prompt-writing 全文 | 42,017 |
| 固定发送全部 9 个 skills 全文 | 233,787 |

自动模式首轮比固定发送单个 skills 全文**省约 84% 上下文**，且模型可自行决定是否需要 skills、需要哪个、以及是否需要进一步读取参考文件。

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
| `模式` | COMBO | auto | `h3-prompt-writing` 的参考资料选择：`auto` 同时提供基础与全参考两份指南；`H3-ref2va` 只用全参考指南；`H3-t2va` / `H3-i2va` / `H3-fl2va` / `H3-l2va` 只用基础指南 |
| `包含参考文件` | BOOLEAN | True | 是否一并读取 skills 的 `references/` 参考资料（仅「具体 skills」模式生效） |
| `最大字符数` | INT | 72000 | 指导文本字符上限，超出后不再追加参考资料 |
| `附加说明` | STRING | 按 skills | 追加到 skills 文本末尾的补充说明；**按所选 skills 自动填充输出强调**（抑制开头说明/结尾建议等无关元素），可自行删除或改写 |

输出：`skills`（完整指导文本或自动清单）、`skills名称`（所选 skills 的 id，自动模式为 `自动`）、`skills目录`（全部已发现 skills 的清单）。

### 内置 skills

`skills/` 内置 11 个 skills：

| skills | 说明 |
|---|---|
| `h3-prompt-writing` | MiniMax H3 视频提示词书写（T2VA/I2VA/FL2VA/L2VA/Ref2VA） |
| `qwen-image-t2i-prompt` | Qwen-Image 2.1 文生图提示词改写（八步观察者视角描述 + `wh_ratio`） |
| `qwen-image-edit-prompt` | Qwen-Image 2.1 图像编辑提示词改写（属性解耦 + `wh_ratio`/`ratio_follow`） |
| 其余 8 个 | MiniMax H3 官方风格类 skills（3D 动画、品牌宣传、纸艺定格等） |

其中 `qwen-image-t2i-prompt` 与 `qwen-image-edit-prompt` 来自用户提供的 Qwen-Image 2.1 系统提示词，已改写为 skills 形式：`SKILL.md` 为工作流摘要，**完整原始系统提示词逐字保存在 `references/` 下**（SHA256 与源文件一致），由 skills管理器一并加载。

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
| 其余风格类 skills | 留空（它们会输出分镜、制作方案，且可能含澄清提问与方案选项，强加会破坏其交互设计） |

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

### skills 目录约定

- 每个 skills 为 `skills/` 或 `custom_skills/` 下的一个子目录，目录名即 skills id；
- 子目录中必须包含 `SKILL.md`（skills 正文）；
- `SKILL.md` 顶部可选 YAML front matter：`name` / `description` / `display_name` / `version` / `tags`；
- 子目录可选 `meta.yaml`，提供 `display-name-zh`、`summary-cn`、`version`、`tag-cn` 等元数据；
- `references/` 下的 `.md` / `.txt` 会作为参考资料一并读取（受「最大字符数」限制）；
- skills id 只能包含小写字母、数字、点、下划线与连字符，且不能为 `auto`；
- 内置 `skills/` 优先，`custom_skills/` 中同 id 的 skills 不会覆盖内置。

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
│   │   ├── image_to_png_node.py        # 图像转为PNG
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
├── skills/                          # 内置 skills（11 个：MiniMax H3 官方 9 个 + Qwen-Image 2.1 提示词 2 个）
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

## 许可证

MIT
