# ComfyUI-YTmmi_Tools

ComfyUI 自定义节点工具集，提供图片保存、JSON 文件导出及图片文字水印等功能。

## 节点说明

- **保存jpg图像** — 保存 JPEG，工作流信息写入 EXIF
- **图像转为png** — 保存 PNG，同时保留jpg图像内的工作流信息
- **保存json文件** — 将 JSON 数据写入磁盘文件
- **像素大小指定比例** — 输入宽高，按指定宽高比换算，保持像素总数基本不变
- **文字水印** — 为图片添加水印，支持文字、字体、大小、位置、颜色、透明度自定义

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
│   ├── image_to_png_node.py
│   ├── save_jpg_node.py
│   ├── save_json_file_node.py
│   └── text_watermark_node.py
├── test/
├── locales/
├── __init__.py
├── requirements.txt
└── README.md
```

## 许可证

MIT
