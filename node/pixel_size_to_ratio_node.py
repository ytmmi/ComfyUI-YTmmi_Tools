class PixelSizeToRatioNode:
    """将输入像素尺寸换算为指定宽高比，同时保持像素总数基本不变。"""

    CATEGORY = "YTmmi/utility"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "width": ("INT", {"default": 1024, "min": 1, "max": 100000}),
                "height": ("INT", {"default": 768, "min": 1, "max": 100000}),
                "ratio_width": ("INT", {"default": 16, "min": 1, "max": 100000}),
                "ratio_height": ("INT", {"default": 9, "min": 1, "max": 100000}),
            }
        }

    RETURN_TYPES = ("INT", "INT")
    RETURN_NAMES = ("width", "height")
    FUNCTION = "convert"
    OUTPUT_NODE = False
    OUTPUT_IS_LIST = (False, False)

    def convert(self, width, height, ratio_width, ratio_height):
        width = max(1, int(width))
        height = max(1, int(height))
        ratio_width = max(1, int(ratio_width))
        ratio_height = max(1, int(ratio_height))

        original_area = width * height
        output_width = max(1, round((original_area * ratio_width / ratio_height) ** 0.5))
        output_height = max(1, round(output_width * ratio_height / ratio_width))

        return (output_width, output_height)


NODE_CLASS_MAPPINGS = {
    "PixelSizeToRatioNode": PixelSizeToRatioNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PixelSizeToRatioNode": "像素大小指定比例",
}

__all__ = [
    "PixelSizeToRatioNode",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
