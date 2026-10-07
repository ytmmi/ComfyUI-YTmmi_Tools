# ComfyUI-YTmmi_Tools

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

ComfyUI 自定义节点扩展包，提供图像、视频、文本与二维码等常用工具节点，并支持 OpenAI 兼容接口的大模型调用与 skills 提示词工程。

## 功能特性

- **图像**：保存与格式转换、纯色生成、文字水印、按遮罩裁剪与贴回、批量加载
- **视频**：多段视频拼接、视频预览
- **数据**：JSON 导出、像素比例换算、多重文本展示、密钥加密存储
- **大模型**：调用 OpenAI 兼容接口，支持 skills 与图片输入
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
| `YTmmi/text` | 保存json文件、自定义LLM |
| `YTmmi/minimax-h3` | H3 低噪细节精修 |

## Skills

「skills管理器」读取插件 `skills/`（内置）与 `custom_skills/`（自定义）目录下的 skills，输出的指导文本可接入「自定义LLM」作为提示词指导：选择「自动」时只输出清单与读取协议，由模型按需多轮读取正文；也可直接选择某个 skills 输出其完整文本。

每个 skills 是一个子目录，内含 `SKILL.md`，可选 `meta.yaml` 与 `references/`。自定义 skills 的写法见 [custom_skills/README.md](custom_skills/README.md)。

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
