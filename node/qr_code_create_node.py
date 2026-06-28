import numpy as np

try:
    import torch  # type: ignore
except Exception:
    torch = None

from PIL import Image

try:
    import qrcode
    from qrcode.main import QRCode
    from qrcode.constants import (
        ERROR_CORRECT_L,
        ERROR_CORRECT_M,
        ERROR_CORRECT_Q,
        ERROR_CORRECT_H,
    )
except Exception:
    qrcode = None


# 错误矫正等级映射
ERROR_CORRECT_MAP = {
    "L (7%)": ERROR_CORRECT_L,
    "M (15%)": ERROR_CORRECT_M,
    "Q (25%)": ERROR_CORRECT_Q,
    "H (30%)": ERROR_CORRECT_H,
}


class CreateQrCodeNode:
    """根据输入文本生成二维码图片。"""

    CATEGORY = "YTmmi/image"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "字符串": ("STRING", {"default": "Hello World", "multiline": True}),
                "错误矫正等级": (list(ERROR_CORRECT_MAP.keys()), {"default": "M (15%)"}),
                "边长": ("INT", {"default": 512, "min": 64, "max": 4096, "step": 8}),
                "边距": ("INT", {"default": 4, "min": 0, "max": 20, "step": 1}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "create"
    OUTPUT_NODE = False
    OUTPUT_IS_LIST = (False,)

    def create(
        self,
        字符串: str = "Hello World",
        错误矫正等级: str = "M (15%)",
        边长: int = 512,
        边距: int = 4,
    ) -> tuple:
        if qrcode is None:
            raise RuntimeError(
                "qrcode 未安装，请运行: pip install qrcode"
            )

        边长 = max(64, int(边长))
        边距 = max(0, int(边距))
        err_correct = ERROR_CORRECT_MAP.get(错误矫正等级, ERROR_CORRECT_M)

        # 生成二维码
        qr = QRCode(
            version=None,
            error_correction=err_correct,
            box_size=10,
            border=边距,
        )
        qr.add_data(字符串)
        qr.make(fit=True)

        # 生成 PIL Image（默认是黑白，用 fill_color/back_color 控制）
        qr_image = qr.make_image(fill_color="black", back_color="white").convert("RGB")

        # 缩放到指定边长
        qr_image = qr_image.resize((边长, 边长), Image.Resampling.NEAREST)

        array = np.array(qr_image).astype(np.float32) / 255.0
        tensor = torch.from_numpy(array).unsqueeze(0)
        return (tensor,)


NODE_CLASS_MAPPINGS = {
    "CreateQrCodeNode": CreateQrCodeNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CreateQrCodeNode": "创建二维码",
}

__all__ = [
    "CreateQrCodeNode",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
