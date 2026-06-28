import os
from typing import Any

import numpy as np

try:
    import torch  # type: ignore
except Exception:
    torch = None

from PIL import Image, ImageDraw, ImageFont

CATEGORY = "YTmmi/image"

# ── 系统字体扫描 ──────────────────────────────────────────────

_FONT_CACHE: list[str] | None = None
_FONT_PATH_MAP: dict[str, str] = {}  # 显示名 → 文件路径


def _get_font_dirs_grouped() -> tuple[list[str], list[str]]:
    """返回 (用户字体目录列表, 系统字体目录列表)。"""
    user_dirs: list[str] = []
    sys_dirs: list[str] = []

    # Windows 用户自行安装的字体目录
    local_fonts = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Fonts")
    if local_fonts and os.path.isdir(local_fonts):
        user_dirs.append(local_fonts)
    # macOS / Linux 用户目录
    for d in [os.path.expanduser("~/Library/Fonts"), os.path.expanduser("~/.fonts")]:
        if os.path.isdir(d):
            user_dirs.append(d)

    # Windows 系统字体目录
    windir = os.environ.get("WINDIR", "C:\\Windows")
    sys_fonts = os.path.join(windir, "Fonts")
    if os.path.isdir(sys_fonts):
        sys_dirs.append(sys_fonts)
    # macOS 系统字体目录
    for d in ["/System/Library/Fonts", "/Library/Fonts"]:
        if os.path.isdir(d):
            sys_dirs.append(d)
    # Linux 系统字体目录
    for d in ["/usr/share/fonts", "/usr/local/share/fonts"]:
        if os.path.isdir(d):
            sys_dirs.append(d)

    return user_dirs, sys_dirs


def _get_font_display_name(font_path: str) -> str:
    """从字体文件路径中提取可读的字体显示名称。"""
    stem = os.path.splitext(os.path.basename(font_path))[0]
    try:
        font = ImageFont.truetype(font_path, 12)
        if hasattr(font, "getname"):
            name = font.getname()[0]
            if name:
                return name
        family = getattr(font, "family", None)
        if family:
            return family
    except Exception:
        pass
    name = stem.replace("_", " ").replace("-", " ")
    return " ".join(word.capitalize() for word in name.split())


def scan_system_fonts() -> list[str]:
    """扫描系统字体目录，返回字体显示名列表。
    用户字体在前，系统字体在后，中间用分隔线隔开。"""
    global _FONT_CACHE, _FONT_PATH_MAP
    if _FONT_CACHE is not None:
        return _FONT_CACHE

    extensions = (".ttf", ".ttc", ".otf")
    seen_stems: set[str] = set()
    _FONT_PATH_MAP = {}
    fonts: list[str] = ["自动"]
    separator = "──────────────"

    def _scan_dir(font_dir: str) -> None:
        if not os.path.isdir(font_dir):
            return
        try:
            for fname in sorted(os.listdir(font_dir)):
                if not fname.lower().endswith(extensions):
                    continue
                fpath = os.path.join(font_dir, fname)
                stem = os.path.splitext(fname)[0].lower()
                if stem in seen_stems:
                    continue
                seen_stems.add(stem)
                display = _get_font_display_name(fpath)
                # 同名时用户字体优先
                if display not in _FONT_PATH_MAP:
                    _FONT_PATH_MAP[display] = fpath
                fonts.append(display)
        except Exception:
            pass

    user_dirs, sys_dirs = _get_font_dirs_grouped()

    # 用户字体（在前面）
    for d in user_dirs:
        _scan_dir(d)

    # 分隔线
    if len(fonts) > 1:
        fonts.append(separator)

    # 系统字体（在后面）
    for d in sys_dirs:
        _scan_dir(d)

    _FONT_CACHE = fonts
    return fonts


def _load_font(font_choice: str, size: int) -> ImageFont.FreeTypeFont:
    """根据用户选择的字体名称加载字体。'自动' 时自动检测系统字体。"""
    if font_choice == "自动":
        return _auto_detect_font(size)
    fpath = _FONT_PATH_MAP.get(font_choice)
    if fpath and os.path.isfile(fpath):
        try:
            return ImageFont.truetype(fpath, size)
        except Exception:
            pass
    return _auto_detect_font(size)


def _auto_detect_font(size: int) -> ImageFont.FreeTypeFont:
    """自动检测系统中合适的中文字体。"""
    candidates = [
        os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", name)
        for name in ["msyh.ttc", "msyhbd.ttc", "simhei.ttf", "simsun.ttc", "yahei.ttc"]
    ] + [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    ]
    for path in candidates:
        if os.path.isfile(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    try:
        import subprocess
        result = subprocess.run(
            ["fc-match", "-f", "%{file}", "sans"],
            capture_output=True, text=True, timeout=3,
        )
        fpath = result.stdout.strip()
        if fpath and os.path.isfile(fpath):
            return ImageFont.truetype(fpath, size)
    except Exception:
        pass
    return ImageFont.load_default()


def _parse_hex_color(hex_str: str) -> tuple[int, int, int]:
    """解析十六进制颜色字符串为 RGB 元组。支持 #RRGGBB 和 #RGB 格式。"""
    hex_str = hex_str.lstrip("#").strip()
    if not hex_str:
        return (255, 255, 255)
    if len(hex_str) == 3:
        hex_str = "".join(c * 2 for c in hex_str)
    if len(hex_str) == 6:
        try:
            r = int(hex_str[0:2], 16)
            g = int(hex_str[2:4], 16)
            b = int(hex_str[4:6], 16)
            return (r, g, b)
        except ValueError:
            pass
    return (255, 255, 255)


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


def _pil_to_tensor(pil_image: Image.Image) -> torch.Tensor:
    """将 PIL Image 转为 ComfyUI 的 IMAGE 张量 (1,H,W,C)。"""
    array = np.array(pil_image.convert("RGB")).astype(np.float32) / 255.0
    return torch.from_numpy(array).unsqueeze(0)


class TextWatermarkNode:
    """为图片添加文字水印。"""

    CATEGORY = CATEGORY

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "文字": ("STRING", {"default": "Sample Watermark", "multiline": False}),
                "字体": (scan_system_fonts(), {"default": "自动"}),
                "字大小": ("FLOAT", {"default": 0.05, "min": 0.001, "max": 9999, "step": 0.001}),
                "字位置x": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 99999, "step": 0.001}),
                "字位置y": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 99999, "step": 0.001}),
                "文字颜色": ("STRING", {"default": "#FFFFFF", "multiline": False}),
            },
            "optional": {
                "不透明度": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "apply_watermark"
    OUTPUT_NODE = False
    OUTPUT_IS_LIST = (False,)

    def _resolve_size(self, size: float, image_width: int) -> int:
        """解析字号：0-1 为相对图片宽的比例，>1 为绝对像素。"""
        if 0 < size <= 1.0:
            return max(1, int(size * image_width))
        return max(1, int(size))

    def _resolve_position(self, pos: float, dimension: int) -> int:
        """解析位置：0-1 为相对位置，>1 为绝对像素。"""
        if 0 <= pos <= 1.0:
            return int(pos * dimension)
        return int(pos)

    def apply_watermark(
        self,
        image: Any,
        文字: str = "Sample Watermark",
        字体: str = "自动",
        字大小: float = 0.05,
        字位置x: float = 0.5,
        字位置y: float = 0.5,
        文字颜色: str = "#FFFFFF",
        不透明度: float = 1.0,
        **kwargs,
    ) -> tuple:
        if image is None:
            return (None,)

        if torch is None or not isinstance(image, torch.Tensor):
            raise TypeError(f"Unsupported image type: {type(image)!r}")

        # 获取批量大小
        batch_size = image.shape[0] if image.ndim == 4 else 1

        result_tensors = []
        for i in range(batch_size):
            img_tensor = image[i] if image.ndim == 4 else image
            pil_image = _tensor_to_pil(img_tensor.unsqueeze(0) if img_tensor.ndim == 3 else img_tensor)
            img_width, img_height = pil_image.size

            # 解析字号
            font_size = self._resolve_size(字大小, img_width)
            font = _load_font(字体, font_size)

            # 解析位置
            pos_x = self._resolve_position(字位置x, img_width)
            pos_y = self._resolve_position(字位置y, img_height)

            # 绘制水印
            if pil_image.mode != "RGBA":
                pil_image = pil_image.convert("RGBA")

            # 创建透明层绘制文字
            txt_layer = Image.new("RGBA", pil_image.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(txt_layer)

            # 计算文字边界，用于对齐
            bbox = draw.textbbox((0, 0), 文字, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            # 如果位置在中心附近，微调使文字居中
            draw_x = pos_x - text_width // 2
            draw_y = pos_y - text_height // 2

            # 解析颜色（支持 #RRGGBB 或 #RGB 格式）
            color_rgb = _parse_hex_color(文字颜色)
            alpha = max(0, min(255, int(不透明度 * 255)))
            draw.text((draw_x, draw_y), 文字, font=font, fill=(*color_rgb, alpha))

            # 合并图层
            watermarked = Image.alpha_composite(pil_image, txt_layer).convert("RGB")

            result_tensors.append(_pil_to_tensor(watermarked))

        result = torch.cat(result_tensors, dim=0)
        return (result,)


NODE_CLASS_MAPPINGS = {
    "TextWatermarkNode": TextWatermarkNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TextWatermarkNode": "文字水印",
}

__all__ = [
    "TextWatermarkNode",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
