try:
    import torch  # type: ignore
except Exception:
    torch = None

from PIL import Image

try:
    from pyzbar.pyzbar import decode as pyzbar_decode
except Exception:
    pyzbar_decode = None


def _tensor_to_pil(image: torch.Tensor) -> Image.Image:
    """将 ComfyUI 的 IMAGE 张量 (B,H,W,C) 转为 PIL Image。"""
    if image.ndim == 4:
        image = image[0]
    if image.device.type != "cpu":
        image = image.detach().cpu()
    array = image.numpy()
    if array.ndim == 3 and array.shape[-1] == 4:
        return Image.fromarray((array * 255).clip(0, 255).astype("uint8"), "RGBA")
    return Image.fromarray((array * 255).clip(0, 255).astype("uint8"), "RGB")


class QrCodeDecodeNode:
    """识别图片中的二维码，返回解码后的文本内容。"""

    CATEGORY = "YTmmi/image"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "decode"
    OUTPUT_NODE = False
    OUTPUT_IS_LIST = (False,)

    def decode(self, image) -> tuple:
        if pyzbar_decode is None:
            raise RuntimeError(
                "pyzbar 未安装，请运行: pip install pyzbar"
            )

        if image is None:
            return ("",)

        if torch is None or not isinstance(image, torch.Tensor):
            raise TypeError(f"Unsupported image type: {type(image)!r}")

        # 取第一张图
        pil_image = _tensor_to_pil(image)

        # 转为灰度图提升识别率
        gray = pil_image.convert("L")

        results = pyzbar_decode(gray)
        if not results:
            # 尝试用原图再识别一次
            results = pyzbar_decode(pil_image.convert("RGB"))

        if not results:
            return ("",)

        # 合并所有识别结果
        texts = [r.data.decode("utf-8", errors="replace") for r in results]
        return ("\n".join(texts),)


NODE_CLASS_MAPPINGS = {
    "QrCodeDecodeNode": QrCodeDecodeNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "QrCodeDecodeNode": "二维码识别",
}

__all__ = [
    "QrCodeDecodeNode",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
