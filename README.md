# ComfyUI-YTmmi_Tools

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![ComfyUI](https://img.shields.io/badge/ComfyUI-custom--nodes-blue.svg)](https://github.com/comfyanonymous/ComfyUI)

ComfyUI 常用工具节点合集：图像处理、视频拼接、音频信息、列表与文本工具、二维码，以及 OpenAI 兼容接口的大模型调用与 skills 提示词管理。

## 功能

- **图像**：保存与格式转换、纯色生成、文字水印、遮罩裁剪与贴回、批量加载、图像合并（坐标 / 相对对齐）
- **视频 / 音频**：多段拼接与预览、音频元数据读取
- **列表 / 文本**：字符串与列表互转、按位置提取、列表合并、文本导出（txt / md / csv / json）
- **大模型**：OpenAI 兼容接口、多轮会话、内置工具调用、Qwen-Image 2.1 提示词改写
- **其他**：二维码 / 条形码生成与识别、密钥加密存储、MiniMax H3 低噪细节精修

## 安装

```bash
cd ComfyUI/custom_nodes/
git clone https://github.com/ytmmi/ComfyUI-YTmmi_Tools.git
pip install -r requirements.txt
```

重启 ComfyUI，节点出现在 `YTmmi` 分类下；也可通过 ComfyUI Manager 搜索安装。
二维码识别需额外安装 zbar：Linux `libzbar0`、macOS `brew install zbar`。

## 节点

| 分类 | 节点 |
|---|---|
| `YTmmi/image` | 保存图像、图像转为png、创建纯色图像、遮罩裁剪图像、图像合并(坐标)、图像合并(相对)、文字水印、批量加载图像、二维码识别、创建二维码 |
| `YTmmi/video` | 视频拼接、预览视频 |
| `YTmmi/audio` | 获取音频信息 |
| `YTmmi/text` | 保存文本、自定义LLM、生成Qwen2.1提示词 |
| `YTmmi/list` | 分离字符串到列表、列表分离字符串、列表提取字符串、字符串到列表、合并列表、获取列表信息 |
| `YTmmi/utility` | 像素大小指定比例、展示文本（多重）、密钥储存器、skills管理器 |
| `YTmmi/minimax-h3` | H3 低噪细节精修 |

## 使用要点

- **图像合并**：画布为处于底层的那张图（「图层顺序翻转」可切换）。坐标 / 偏移 `0~1`（不含 1）按底图百分比、其余按像素，可为负；`宽` / `高` 为 `0` 表示不拉伸。可选「遮罩」作用于上层。
- **保存文本**：「文本」为通配输入（`*`），可连接任意端口；`使用文件名` 关闭时按前缀 + 自动序号命名，打开时按完整文件名（同名覆盖）。
- **保存图像**：`png`（默认）/ `jpg`；PNG 内嵌 `prompt` 与 `workflow`，拖回画布即可还原工作流。
- **自定义LLM**：多轮会话与内置工具调用默认按需启用，`skills` 输入需来自「skills管理器」；节点不执行任意代码。
- **列表类节点**：端口按连线自动增减（输出上限 20、输入 20 / 9）。

skills 的编写方式见 [custom_skills/README.md](custom_skills/README.md)。

## 致谢

- [ComfyUI-YCNodes-MiniMax-H3](https://github.com/yichengup/ComfyUI-YCNodes-MiniMax-H3) — H3 低噪细节精修
- [ComfyUI_Qwen_H3_Prompt](https://github.com/chflame163/ComfyUI_Qwen_H3_Prompt) — skills 管理方式
- [MiniMax-AI/MiniMax-H3](https://github.com/MiniMax-AI/MiniMax-H3) — 内置 H3 skills
- [Anima 模型卡](https://huggingface.co/circlestone-labs/Anima) / [ComfyUI 官方教程](https://docs.comfy.org/tutorials/image/anima/anima) — Anima skills 依据
- [moss-image-prompt-enhancer](skills/moss-image-prompt-enhancer/SKILL.md) — MOSS-Image 提示词增强 skills

## 许可证

[MIT License](https://opensource.org/licenses/MIT)
