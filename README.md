# ComfyUI-YTmmi_Tools

ComfyUI 自定义节点工具集，提供图片保存、JSON 文件导出、图片文字水印、批量图片加载及 MiniMax H3 视频采样调度等功能。

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
- **展示文本（多重）** — 展示上游节点的字符串信息（数字、字符串、文本、JSON 等），支持 0~8 号共 9 个输入口，默认只显示「输入0」，连接后自动显现下一个输入口；2 个及以上输入自动按输入口序号分隔标注展示；音频、潜空间、视频等类型自动过滤不展示
- **密钥储存器** — 加密保存 API 密钥与接口地址（以系统用户名前5位派生密钥，防止插件目录被复制后泄露），点击「保存」加密存储、「删除密钥」删除「选择密钥」下拉中选中的预设；执行后按「选择密钥」下拉名称输出密钥/接口地址
- **自定义LLM** — 调用任意 OpenAI 兼容格式的在线大模型接口（API Key + 接口地址 + 模型名 + 提示词），返回生成文本；模型名为下拉菜单，点击节点上的「获取模型」按钮自动拉取接口可用模型列表，支持温度/最大token/top_p/种子；支持图片输入（最多 9 张，默认只显示 1 个图片输入口，连接后自动显现下一张），按 OpenAI 多模态格式发送，可适配 DeepSeek V4.1 Flash（deepseek-flash）等支持视觉输入的模型

### 二维码

- **二维码识别** — 识别图片中的二维码，返回解码文本
- **创建二维码** — 根据文本生成二维码图片，支持错误矫正等级、边长、边距设置

### MiniMax H3

- **H3 低噪细节精修** — 在低噪点区（低 Sigma）局部加密采样步长，消解运动物体的边缘像素颗粒；移植自 [ComfyUI-YCNodes-MiniMax-H3](https://github.com/yichengup/ComfyUI-YCNodes-MiniMax-H3.git)

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
│   │   └── pixel_size_to_ratio_node.py # 像素大小指定比例
│   ├── text/                        # YTmmi/text 分类
│   │   ├── custom_llm_node.py          # 自定义LLM
│   │   └── save_json_file_node.py      # 保存JSON文件
│   └── minimax_h3/                  # YTmmi/minimax-h3 分类
│       └── h3_sigma_refiner_node.py    # H3 低噪细节精修
├── js/
│   ├── auto_fill_widget.js         # 前端扩展：执行后自动回填控件值
│   ├── custom_llm_widget.js       # 前端扩展：自定义LLM获取模型按钮
│   ├── display_text_widget.js      # 前端扩展：展示文本（多重）动态输入接口与结果回填
│   ├── key_storage_widget.js      # 前端扩展：密钥储存器保存/删除按钮与下拉
│   └── video_concat_widget.js      # 前端扩展：视频拼接动态输入接口
├── test/
├── locales/
├── __init__.py
├── requirements.txt
└── README.md
```

## 致谢

本项目的 **H3 低噪细节精修**（H3 Sigma Refiner）节点移植自以下开源仓库，感谢原作者的实现：

- [ComfyUI-YCNodes-MiniMax-H3](https://github.com/yichengup/ComfyUI-YCNodes-MiniMax-H3.git) — 专为 MiniMax H3 视频模型打造的 ComfyUI 节点包（作者：亦诚，MIT 许可）

## 许可证

MIT
