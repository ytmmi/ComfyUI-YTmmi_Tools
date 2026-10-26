# 像素大小指定比例
class PixelSizeToRatioNode:
    """将输入像素尺寸换算为指定宽高比，同时保持像素总数基本不变。"""

    CATEGORY = "YTmmi/utility"
    DESCRIPTION = '像素大小指定比例：输入宽高，按指定宽高比换算，保持像素总数基本不变；输出宽高取整为「分辨率步数」的倍数'

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "宽": ("INT", {"default": 1024, "min": 1, "max": 100000}),
                "高": ("INT", {"default": 768, "min": 1, "max": 100000}),
                "比例宽": ("INT", {"default": 16, "min": 1, "max": 100000}),
                "比例高": ("INT", {"default": 9, "min": 1, "max": 100000}),
                "分辨率步数": (
                    "INT",
                    {
                        "default": 1,
                        "min": 1,
                        "max": 256,
                        "step": 1,
                        "tooltip": "输出宽高取整到该值的倍数（与原生「缩放图像（像素）」的分辨率步数一致），1 表示不取整",
                    },
                ),
            }
        }

    RETURN_TYPES = ("INT", "INT")
    RETURN_NAMES = ("宽", "高")
    FUNCTION = "convert"
    OUTPUT_NODE = False
    OUTPUT_IS_LIST = (False, False)

    @staticmethod
    def _round_to_steps(value, steps):
        """取整到 steps 的倍数（与原生「缩放图像（像素）」同口径：四舍五入），至少保留一个步长。"""
        return max(steps, int(round(value / steps)) * steps)

    def convert(self, **kwargs):
        width = max(1, int(kwargs.get("宽", 1024)))
        height = max(1, int(kwargs.get("高", 768)))
        ratio_width = max(1, int(kwargs.get("比例宽", 16)))
        ratio_height = max(1, int(kwargs.get("比例高", 9)))
        resolution_steps = max(1, int(kwargs.get("分辨率步数", 1)))

        original_area = width * height
        # 分辨率步数=1 时与旧版逐像素一致：宽按面积开方四舍五入，高按取整后的宽反推
        exact_width = (original_area * ratio_width / ratio_height) ** 0.5
        output_width = self._round_to_steps(exact_width, resolution_steps)
        output_height = self._round_to_steps(output_width * ratio_height / ratio_width, resolution_steps)

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
