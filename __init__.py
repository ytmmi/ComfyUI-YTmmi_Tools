try:
    from .node.image_to_png_node import ImageToPngNode
    from .node.save_json_file_node import SaveJsonFileNode
    from .node.save_jpg_node import SaveJPGNode
except ImportError:  # pragma: no cover - fallback for direct module loading
    from node.image_to_png_node import ImageToPngNode
    from node.save_json_file_node import SaveJsonFileNode
    from node.save_jpg_node import SaveJPGNode

NODE_CLASS_MAPPINGS = {
    "SaveJPGNode": SaveJPGNode,
    "ImageToPngNode": ImageToPngNode,
    "SaveJsonFileNode": SaveJsonFileNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SaveJPGNode": "保存jpg图像",
    "ImageToPngNode": "图像转为png",
    "SaveJsonFileNode": "保存json文件",
}

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "ImageToPngNode",
    "SaveJsonFileNode",
    "SaveJPGNode",
]
