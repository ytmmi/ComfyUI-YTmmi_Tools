# ComfyUI-YTmmi_Tools

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

ComfyUI 自定义节点扩展包，提供图像、视频、文本与二维码等常用工具节点，并支持 OpenAI 兼容接口的大模型调用与 skills 提示词工程。

## 功能特性

- **图像**：保存与格式转换、纯色生成、文字水印、按遮罩裁剪与贴回、批量加载
- **视频**：多段视频拼接、视频预览
- **列表**：字符串按分隔符切分、列表逐项分离为字符串端口、按位置提取、多字符串合并为列表、多列表合并、列表信息
- **数据**：JSON 导出、像素比例换算、多重文本展示（结果可嵌入工作流数据）、密钥加密存储
- **大模型**：调用 OpenAI 兼容接口，支持 skills 与图片输入；本地 Qwen-Image 2.1 提示词改写（W4A8 量化，8GB 显存特化）
- **二维码**：二维码 / 条形码生成与识别
- **MiniMax H3**：低噪细节精修采样

## 安装

```bash
cd ComfyUI/custom_nodes/
git clone https://github.com/ytmmi/ComfyUI-YTmmi_Tools.git
cd ComfyUI-YTmmi_Tools
pip install -r requirements.txt
```

重启 ComfyUI 后，节点出现在 `YTmmi` 分类下；也可通过 ComfyUI Manager 搜索安装。

依赖：`Pillow`、`pyzbar`、`qrcode`、`av`。其中二维码识别依赖 zbar 动态库（Linux 装 `libzbar0`，macOS 装 `brew install zbar`）。

## 节点

| 分类 | 节点 |
|---|---|
| `YTmmi/image` | 保存jpg图像、图像转为png、创建纯色图像、遮罩裁剪图像、图像合并、文字水印、批量加载图像、二维码识别、创建二维码 |
| `YTmmi/video` | 视频拼接、预览视频 |
| `YTmmi/utility` | 像素大小指定比例、展示文本（多重）、密钥储存器、skills管理器 |
| `YTmmi/list` | 分离字符串到列表、列表分离字符串、列表提取字符串、字符串到列表、合并列表、获取列表信息 |
| `YTmmi/text` | 保存json文件、自定义LLM、生成Qwen2.1提示词 |
| `YTmmi/minimax-h3` | H3 低噪细节精修 |

> 「分离字符串到列表」的「保留分隔符」开关打开时保留分隔符并置于后一项开头：`111---222---333` 按 `---` 切分为 `111` / `---222` / `---333`；关闭（默认）则为 `111` / `222` / `333`。分隔符按**字面量**处理，`.` `|` `*` 等正则元字符无需转义。

> 「列表分离字符串」「字符串到列表」「合并列表」的端口按需显示：连接末尾端口后自动追加下一个端口，上限分别为 20 个输出、20 个输入、9 个输入。三者均在**工作流构建阶段（运行前）**即按连线增减端口，与运行结果无关，节点默认高度取最小值。

> 「展示文本（多重）」会把展示结果写入工作流数据：保存工作流后重新载入仍能看到上次的文本，历史记录与输出图片元数据中的工作流同样带有该文本。

> 「生成Qwen2.1提示词」在节点内自带模型加载（不放 CLIP 加载器），读取 `models/LLM` 下的量化权重（`.safetensors`，ComfyUI 官方 `comfyui-quantized` 格式，如 `Qwen-Image-2.1-PE-I2I-Heretic-W4A8.safetensors`），把提示词改写为 Qwen-Image 2.1 可直接使用的提示词；可接参考图做「图像编辑」改写，另输出模型「思考内容」。**内置系统提示词是官方原文**（文生图八步法 / 图像编辑两套语言决策 + `wh_ratio`、`ratio_follow` 判定表，与 `skills/qwen-image-*-prompt/references/` 下的官方文档字节一致），代价是首 token 前要多算 prefill（文生图约 2.4k token ≈ 4.1s，图像编辑约 4.5k token ≈ 7.5s），稳态每 token 速度不变——介意速度可以自己接「系统提示词」端口换成精简版。针对 8GB 显存做了静态独占加载、按打包体积判定设备、分块词表投影、视觉塔「prefill 用完即下卡」、量化权重整体驻留保护、算子后端自适应与模型缓存：RTX 4060 Laptop 8GB + `torch 2.13+cu130` 实测文生图 77s 出一份完整 JSON（含 9s 加载）、带 512px 参考图的图像编辑 60s；48 token 稳态 **0.32s/token（约 3.2 token/s）**，约为「原生 CLIPLoader + 生成节点」写法的 **3.1 倍**。打开「思考」时「思考预算」（默认 256，0 = 不限）会软提示 + 硬截断思考：不限预算时 512 个 token 会被思考全部吃满、生成文本为空；预算 128 时可正常产出答案且整轮更快。采样参数与原生 TextGenerate 逐项对齐（温度 / top_k / top_p / min_p / 重复惩罚 / 存在惩罚 / 种子）；`mtp` 固定关闭——本权重不含 `mtp.*` 张量，与原生 `mtp="auto"` 完全等价。

## Skills

「skills管理器」读取插件 `skills/`（内置）与 `custom_skills/`（自定义）目录下的 skills，输出的指导文本可接入「自定义LLM」作为提示词指导：选择「自动」时只输出清单与读取协议，由模型按需多轮读取正文；也可直接选择某个 skills 输出其完整文本。

每个 skills 是一个子目录，内含 `SKILL.md`，可选 `meta.yaml` 与 `references/`。自定义 skills 的写法见 [custom_skills/README.md](custom_skills/README.md)。

> 「选择skills」与「模式」的选中值会随工作流保存，且**一旦选了具体 skills 或某个模式，自动刷新就不再改动下拉选项与选中值**（避免下次运行又回到「自动」）。需要重新扫描 skills 目录时，点节点上的「刷新skills」按钮强制重扫。

> skills 内容仅作为模型提示词指导，节点不会执行其中声明的脚本、工具或网络调用。

## 项目结构

```text
ComfyUI-YTmmi_Tools/
├── node/            # 节点代码（按分类分目录）
├── skills/          # 内置 skills
├── custom_skills/   # 自定义 skills
├── js/              # 前端扩展脚本
├── test/            # 单元测试
├── __init__.py      # 插件入口
├── requirements.txt
└── README.md
```

## 致谢

- [ComfyUI-YCNodes-MiniMax-H3](https://github.com/yichengup/ComfyUI-YCNodes-MiniMax-H3) — H3 低噪细节精修移植自该仓库
- [ComfyUI_Qwen_H3_Prompt](https://github.com/chflame163/ComfyUI_Qwen_H3_Prompt) — skills 管理方式参考该仓库
- [MiniMax-AI/MiniMax-H3](https://github.com/MiniMax-AI/MiniMax-H3) — 内置 H3 skills 来源
- [Anima 官方模型卡](https://huggingface.co/circlestone-labs/Anima) 与 [ComfyUI 官方教程](https://docs.comfy.org/tutorials/image/anima/anima) — Anima skills 依据

## 许可证

本项目基于 [MIT License](https://opensource.org/licenses/MIT) 开源。
