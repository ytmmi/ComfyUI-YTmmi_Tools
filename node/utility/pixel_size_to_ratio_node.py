# 像素大小指定比例
class PixelSizeToRatioNode:
    """将输入像素尺寸换算为指定宽高比，同时保持像素总数基本不变。"""

    CATEGORY = "YTmmi/utility"
    DESCRIPTION = '像素大小指定比例：输入宽高，按指定宽高比换算，保持像素总数基本不变'

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "宽": ("INT", {"default": 1024, "min": 1, "max": 100000}),
                "高": ("INT", {"default": 768, "min": 1, "max": 100000}),
                "比例宽": ("INT", {"default": 16, "min": 1, "max": 100000}),
                "比例高": ("INT", {"default": 9, "min": 1, "max": 100000}),
            }
        }

    RETURN_TYPES = ("INT", "INT")
    RETURN_NAMES = ("宽", "高")
    FUNCTION = "convert"
    OUTPUT_NODE = False
    OUTPUT_IS_LIST = (False, False)

    def convert(self, **kwargs):
        width = max(1, int(kwargs.get("宽", 1024)))
        height = max(1, int(kwargs.get("高", 768)))
        ratio_width = max(1, int(kwargs.get("比例宽", 16)))
        ratio_height = max(1, int(kwargs.get("比例高", 9)))

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
