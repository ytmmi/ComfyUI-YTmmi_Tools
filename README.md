# ComfyUI-YTmmi_Tools

ComfyUI 自定义节点工具集，提供图片保存、JSON 文件导出、图片文字水印及批量图片加载等功能。

## 节点说明

### 图片处理

- **保存jpg图像** — 保存 JPEG，工作流信息写入 EXIF
- **图像转为png** — 保存 PNG，同时保留jpg图像内的工作流信息
- **创建纯色图片** — 创建指定宽高和颜色的纯色图片
- **文字水印** — 为图片添加水印，支持文字、字体、大小、位置、颜色、透明度自定义
- **批量加载图片** — 加载指定路径文件夹内的图片，支持多种排序、位置偏移、种子控制与批量输出

### 数据处理

- **保存json文件** — 将 JSON 数据写入磁盘文件
- **像素大小指定比例** — 输入宽高，按指定宽高比换算，保持像素总数基本不变

### 二维码

- **二维码识别** — 识别图片中的二维码，返回解码文本
- **创建二维码** — 根据文本生成二维码图片，支持错误矫正等级、边长、边距设置

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
├── node/
│   ├── batch_load_images_node.py   # 批量加载图片
│   ├── create_solid_color_node.py  # 创建纯色图片
│   ├── image_to_png_node.py        # 图像转为PNG
│   ├── pixel_size_to_ratio_node.py # 像素大小指定比例
│   ├── qr_code_create_node.py      # 创建二维码
│   ├── qr_code_decode_node.py      # 二维码识别
│   ├── save_jpg_node.py            # 保存JPG图像
│   ├── save_json_file_node.py      # 保存JSON文件
│   └── text_watermark_node.py      # 文字水印
├── js/
│   └── auto_fill_widget.js         # 前端扩展：执行后自动回填控件值
├── test/
├── locales/
├── __init__.py
├── requirements.txt
└── README.md
```

## 许可证

MIT
