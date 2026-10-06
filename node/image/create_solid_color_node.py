# 创建纯色图像
import numpy as np

try:
    import torch  # type: ignore
except Exception:
    torch = None

from PIL import Image


def _parse_color(color_str: str) -> tuple[int, int, int]:
    """解析颜色字符串为 RGB 元组。
    支持格式：
      - #RRGGBB / #RGB  十六进制
      - R,G,B            十进制 RGB（逗号不区分半角/全角）
    """
    s = color_str.strip()
    if not s:
        return (255, 255, 255)

    # RGB 格式：以数字开头，含逗号
    if s[0].isdigit() and ("," in s or "，" in s):
        # 统一全角逗号为半角
        s = s.replace("，", ",")
        parts = [p.strip() for p in s.split(",")]
        if len(parts) == 3:
            try:
                vals = []
                for p in parts:
                    vals.append(max(0, min(255, int(p))) if p else 0)
                return (vals[0], vals[1], vals[2])
            except ValueError:
                pass

    # 十六进制格式
    s = s.lstrip("#")
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    if len(s) == 6:
        try:
            r = int(s[0:2], 16)
            g = int(s[2:4], 16)
            b = int(s[4:6], 16)
            return (r, g, b)
        except ValueError:
            pass

    return (255, 255, 255)


class CreateSolidColorNode:
    """创建纯色图像。"""

    CATEGORY = "YTmmi/image"
    DESCRIPTION = '创建纯色图像：按指定宽度、高度、颜色与不透明度生成纯色图像，不透明度小于 1 时输出带透明通道的图像'

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "宽": ("INT", {"default": 512, "min": 1, "max": 100000, "step": 1}),
                "高": ("INT", {"default": 512, "min": 1, "max": 100000, "step": 1}),
                "颜色": ("STRING", {"default": "#FFFFFF", "multiline": False}),
                # 与「文字水印」的「不透明度」保持一致：1 完全不透明、0 完全透明
                "不透明度": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("图片",)
    FUNCTION = "create"
    OUTPUT_NODE = False
    OUTPUT_IS_LIST = (False,)

    def create(
        self, 宽: int, 高: int, 颜色: str = "#FFFFFF", 不透明度: float = 1.0
    ) -> tuple:
        宽 = max(1, int(宽))
        高 = max(1, int(高))
        rgb = _parse_color(颜色)
        opacity = max(0.0, min(1.0, float(不透明度)))

        if opacity >= 1.0:
            # 完全不透明：保持原有的 RGB 三通道输出，不影响既有工作流
            pil_image = Image.new("RGB", (宽, 高), rgb)
        else:
            # 需要透明：输出 RGBA，alpha 由不透明度决定，RGB 仍是纯色本身
            alpha = int(round(opacity * 255))
            pil_image = Image.new("RGBA", (宽, 高), (rgb[0], rgb[1], rgb[2], alpha))

        array = np.array(pil_image).astype(np.float32) / 255.0

        if torch is None:
            raise RuntimeError("torch is not available")

        tensor = torch.from_numpy(array).unsqueeze(0)
        return (tensor,)


NODE_CLASS_MAPPINGS = {
    "CreateSolidColorNode": CreateSolidColorNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CreateSolidColorNode": "创建纯色图像",
}

__all__ = [
    "CreateSolidColorNode",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
