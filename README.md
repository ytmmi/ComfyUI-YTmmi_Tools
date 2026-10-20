# ComfyUI-YTmmi_Tools

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![ComfyUI](https://img.shields.io/badge/ComfyUI-custom--nodes-blue.svg)](https://github.com/comfyanonymous/ComfyUI)

ComfyUI 自定义节点扩展包：图像、视频、列表、文本与二维码等常用工具节点，支持 OpenAI 兼容接口的大模型调用，以及 skills 提示词工程。

## 功能特性

- **图像**：保存与格式转换、纯色生成、文字水印、按遮罩裁剪与贴回、批量加载、图像合并
- **视频**：多段视频拼接、视频预览
- **列表**：字符串切分与列表互转、按位置提取、多列表合并、列表信息
- **数据**：文本导出（txt / md / csv / json）、像素比例换算、多重文本展示（结果写入工作流）、密钥加密存储
- **大模型**：OpenAI 兼容接口调用（支持 skills、图片输入、完整请求参数、多轮对话历史、工具调用）、Qwen-Image 2.1 提示词改写
- **二维码**：二维码 / 条形码生成与识别
- **MiniMax H3**：低噪细节精修采样

## 安装

```bash
cd ComfyUI/custom_nodes/
git clone https://github.com/ytmmi/ComfyUI-YTmmi_Tools.git
pip install -r requirements.txt
```

重启 ComfyUI 后节点出现在 `YTmmi` 分类下，也可通过 ComfyUI Manager 搜索安装。

二维码识别需额外安装 zbar 动态库：Linux `libzbar0`，macOS `brew install zbar`。

## 节点

| 分类 | 节点 |
|---|---|
| `YTmmi/image` | 保存图像、图像转为png、创建纯色图像、遮罩裁剪图像、图像合并、文字水印、批量加载图像、二维码识别、创建二维码 |
| `YTmmi/video` | 视频拼接、预览视频 |
| `YTmmi/utility` | 像素大小指定比例、展示文本（多重）、密钥储存器、skills管理器 |
| `YTmmi/list` | 分离字符串到列表、列表分离字符串、列表提取字符串、字符串到列表、合并列表、获取列表信息 |
| `YTmmi/text` | 保存文本、自定义LLM、生成Qwen2.1提示词 |
| `YTmmi/minimax-h3` | H3 低噪细节精修 |

列表类节点的端口按连线自动增减（上限：输出 20、输入 20 / 9）；「分离字符串到列表」的分隔符按字面量处理。

「保存图像」可选 `png`（默认）/ `jpg`：保存 PNG 时按 ComfyUI 官方「保存图像」节点的格式写入 `prompt` 与 `workflow` 文本块，把图片拖回画布即可还原工作流；输出「预览图片」与「文件名」（前缀 + 自动序号，不含后缀，批量时逐行一个）。序号按官方 `SaveImage` 的方式扫描输出目录后递增，连续运行不会覆盖历史输出。注册键为 `SaveImageNode`，本节点不兼容改名前的旧工作流。

## 保存文本

把任意类型的输入保存成文本文件，输入「文本」是通配类型（`*`），可以连接任何输出端口。

- **格式**：`txt`（默认）/ `md` / `csv` / `json`，扩展名即格式名。
- **命名**：`使用文件名` 开关关闭（默认）时用「文件前缀」+ 自动序号（`前缀_00001.txt`），序号按 ComfyUI 官方 `SaveImage` 的规则扫描输出目录后递增，连续运行不会覆盖历史文件；打开时直接用「文件名」作为完整文件名（同名文件会被覆盖）。
- **转换规则**：字符串原样写出（不重排格式）；`csv` 把 dict 写成 `key,value` 两列、dict 列表按表头并集、二维列表按行、一维列表单列；`json` 走 JSON 序列化（保留中文）；图像 / 张量 / 数组只写结构摘要（如 `<torch.Tensor shape=(1, 64, 64, 3) ...>`），不会把整张图逐像素转成文本。
- 输出「文件路径」（绝对路径）。可选「子文件夹」相对 ComfyUI 的 `output` 目录。

原「保存json文件」节点已由本节点取代（`json` 格式 + 字符串输入原样写出即等价行为）。

## 自定义LLM

调用任意 OpenAI 兼容的 `/chat/completions` 接口，输出「输出文本」与「简略上下文」。除基础参数（模型 / 温度 / 最大 token / top_p / 种子）外，还提供：

- **完整请求参数**：输出格式（`text` / `json_object`）、频率惩罚、存在惩罚、候选数量 `n`、`top_k`、推理强度 `reasoning_effort`、超时秒数、空输出重试次数。**默认值一律是「不发送」**，旧工作流行为不变。
- **多轮会话（节点后台维护）**：`启用多轮对话` 开关**默认关闭**；开启后节点自动把本节点此前的对话轮次拼到本轮之前，**不需要手工填写历史对话**。`最大会话轮数` 为 0 时不限制，大于 0 时达到上限后下一轮自动开新会话；关闭再开启、或 ComfyUI 重启都会自动开新会话。一个节点只维护一个会话，只保留纯文本轮次（图片只随当前轮发送）。
- **工具调用（内置工具，自动执行）**：节点内置 `read_skill` 工具（读取 `skills/` 中的文件），在 skills「自动」清单的多轮按需读取时自动随请求声明 `tools` + `tool_choice=auto`，无需人工配置。模型返回 `tool_calls` 时节点自动执行并把结果作为 `tool` 消息回注、继续下一轮；未知工具名不执行，只回注一条错误说明。节点**绝不执行任意代码**。
- **能力约束**：只有 `skills` 输入确实是「skills管理器」输出的「自动」清单（带自动标记**且**至少解析出 1 个 skills 名称）时才声明工具、进入多轮读取；且无论走原生 `tool_calls` 还是 `READ:` 文本协议，都只能读取**本次清单内**的 skills，清单外一律拒绝。因此要使用 skills 读取能力，**必须由「skills管理器」节点提供 `skills` 输入**。
- **图片输入增强**：最多 9 张图；`图片最长边` 发送前等比缩放（0 = 不缩放），`图片细节` 映射 `image_url.detail`。

「简略上下文」由节点代码确定性拼装，**不额外调用模型**：记录步数 / 输入 skills 名称 / 读取明细 / 每步思考与回复 / 最终输出；接口返回 `usage` 时追加「用量统计」段（输入、输出、合计 token、接口耗时、输出速度、工具调用数）。

## Skills

「skills管理器」读取 `skills/`（内置）与 `custom_skills/`（自定义）目录，输出的指导文本可接入「自定义LLM」。skills 仅作为提示词指导，节点不会执行其中声明的脚本、工具或网络调用。自定义写法见 [custom_skills/README.md](custom_skills/README.md)。

「模式」用于按任务家族筛选「自动」清单：`H3-*`（MiniMax H3 视频）、`qwen-image-*`（Qwen-Image 2.1 图像提示词）、`Anima`（二次元插画）、`moss`（MOSS-Image 图像提示词增强：caption / 像素级 Layout 两种交付物，随附本地编译脚本 `scripts/compile_prompt.py`）。

## 致谢

- [ComfyUI-YCNodes-MiniMax-H3](https://github.com/yichengup/ComfyUI-YCNodes-MiniMax-H3) — H3 低噪细节精修移植来源
- [ComfyUI_Qwen_H3_Prompt](https://github.com/chflame163/ComfyUI_Qwen_H3_Prompt) — skills 管理方式参考
- [MiniMax-AI/MiniMax-H3](https://github.com/MiniMax-AI/MiniMax-H3) — 内置 H3 skills 来源
- [Anima 模型卡](https://huggingface.co/circlestone-labs/Anima) / [ComfyUI 官方教程](https://docs.comfy.org/tutorials/image/anima/anima) — Anima skills 依据
- [moss-image-prompt-enhancer](skills/moss-image-prompt-enhancer/SKILL.md) — MOSS-Image caption / 像素级 Layout 提示词增强 skills 来源

## 许可证

[MIT License](https://opensource.org/licenses/MIT)
