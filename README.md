# ComfyUI-YTmmi_Tools

这是一个用于 ComfyUI 的自定义节点集合，当前包含用于图片和 JSON 数据处理的节点。

## 功能特点

- 保存 JPEG 图像，并将工作流数据写入图片元数据
- 将输入图像保存为 PNG，并输出工作流 JSON 数据
- 将 JSON 数据保存为独立文件

## 已支持节点

### 1. 保存jpg图像

- 输入：图像、文件名前缀、质量等
- 输出：保存后的图片文件
- 特点：会将当前工作流信息写入图片元数据

### 2. 图像转为png

- 输入：图像、文件名前缀等
- 输出：
  - 图像
  - workflow_json 字符串
- 特点：将图像保存为 PNG，并附带工作流 JSON 数据

### 3. 保存json文件

- 输入：JSON 数据、文件名前缀等
- 输出：保存后的 JSON 文件路径
- 特点：将 JSON 内容写入磁盘文件

## 安装

将当前仓库目录放置到 ComfyUI 的自定义节点目录下，例如：

```
ComfyUI/custom_nodes/ComfyUI-YTmmi_Tools
```

然后重启 ComfyUI 即可在节点菜单中看到相关节点。

## 开发说明

项目结构如下：

```
ComfyUI-YTmmi_Tools/
├── node/
│   ├── save_jpg_node.py
│   ├── image_to_png_node.py
│   ├── save_json_file_node.py
│   └── __init__.py
├── test/
├── requirements.txt
├── __init__.py
└── README.md
```


## 许可证

本项目按当前仓库设置进行维护。
