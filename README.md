# ComfyUI-YTmmi_Tools

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![ComfyUI](https://img.shields.io/badge/ComfyUI-custom--nodes-blue.svg)](https://github.com/comfyanonymous/ComfyUI)

ComfyUI 自定义节点扩展包：图像、视频、列表、文本与二维码等常用工具节点，支持 OpenAI 兼容接口的大模型调用，以及 skills 提示词工程。

## 功能特性

- **图像**：保存与格式转换、纯色生成、文字水印、按遮罩裁剪与贴回、批量加载、图像合并
- **视频**：多段视频拼接、视频预览
- **列表**：字符串切分与列表互转、按位置提取、多列表合并、列表信息
- **数据**：JSON 导出、像素比例换算、多重文本展示（结果写入工作流）、密钥加密存储
- **大模型**：OpenAI 兼容接口调用（支持 skills 与图片输入）、Qwen-Image 2.1 提示词改写
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
| `YTmmi/image` | 保存jpg图像、图像转为png、创建纯色图像、遮罩裁剪图像、图像合并、文字水印、批量加载图像、二维码识别、创建二维码 |
| `YTmmi/video` | 视频拼接、预览视频 |
| `YTmmi/utility` | 像素大小指定比例、展示文本（多重）、密钥储存器、skills管理器 |
| `YTmmi/list` | 分离字符串到列表、列表分离字符串、列表提取字符串、字符串到列表、合并列表、获取列表信息 |
| `YTmmi/text` | 保存json文件、自定义LLM、生成Qwen2.1提示词 |
| `YTmmi/minimax-h3` | H3 低噪细节精修 |

列表类节点的端口按连线自动增减（上限：输出 20、输入 20 / 9）；「分离字符串到列表」的分隔符按字面量处理。

## Skills

「skills管理器」读取 `skills/`（内置）与 `custom_skills/`（自定义）目录，输出的指导文本可接入「自定义LLM」。skills 仅作为提示词指导，节点不会执行其中声明的脚本、工具或网络调用。自定义写法见 [custom_skills/README.md](custom_skills/README.md)。

## 致谢

- [ComfyUI-YCNodes-MiniMax-H3](https://github.com/yichengup/ComfyUI-YCNodes-MiniMax-H3) — H3 低噪细节精修移植来源
- [ComfyUI_Qwen_H3_Prompt](https://github.com/chflame163/ComfyUI_Qwen_H3_Prompt) — skills 管理方式参考
- [MiniMax-AI/MiniMax-H3](https://github.com/MiniMax-AI/MiniMax-H3) — 内置 H3 skills 来源
- [Anima 模型卡](https://huggingface.co/circlestone-labs/Anima) / [ComfyUI 官方教程](https://docs.comfy.org/tutorials/image/anima/anima) — Anima skills 依据

## 许可证

[MIT License](https://opensource.org/licenses/MIT)
