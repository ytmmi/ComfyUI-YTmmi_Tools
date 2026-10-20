# 保存图像
import json
import os
import re
from pathlib import Path
from typing import Any, Optional, Union

try:
    import torch  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    torch = None

from PIL import Image, PngImagePlugin

try:
    import folder_paths  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    folder_paths = None

# 保存格式：png 为默认，写法与 ComfyUI 官方「保存图像」节点一致（可嵌入工作流）
FORMAT_OPTIONS = ["png", "jpg"]
DEFAULT_FORMAT = "png"
PNG_COMPRESS_LEVEL = 4


def _normalize_workflow_payload(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict):
        if "workflow" in payload:
            return payload
        return {"workflow": payload}
    if payload is None:
        return {"workflow": {}}
    return {"workflow": payload}


def _pil_image_from(image: Any, keep_alpha: bool = False) -> Image.Image:
    """把 PIL / torch 图像转换为 PIL.Image；keep_alpha 为 True 时保留 alpha 通道。"""
    if isinstance(image, Image.Image):
        return image if keep_alpha else image.convert("RGB")

    if torch is not None and isinstance(image, torch.Tensor):
        if image.ndim == 4:
            image = image[0]
        if image.device.type != "cpu":
            image = image.detach().cpu()
        array = image.numpy()
        if array.ndim == 2:
            return Image.fromarray(
                (array * 255).clip(0, 255).astype("uint8"), "L"
            )
        if array.shape[-1] == 1:
            array = array.repeat(3, axis=-1)
        if array.shape[-1] == 4:
            pil_image = Image.fromarray(
                (array * 255).clip(0, 255).astype("uint8"), "RGBA"
            )
            return pil_image if keep_alpha else pil_image.convert("RGB")
        return Image.fromarray(
            (array * 255).clip(0, 255).astype("uint8"), "RGB"
        )

    raise TypeError(f"Unsupported image type: {type(image)!r}")


def save_jpeg_image(
    image: Any,
    output_path: Union[str, os.PathLike[str]],
    workflow_data: Optional[dict[str, Any]] = None,
    quality: int = 95,
) -> str:
    """直接把图片保存成 JPEG，并把工作流元数据写入 EXIF。"""
    workflow_payload = _normalize_workflow_payload(workflow_data)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    pil_image = _pil_image_from(image, keep_alpha=False).convert("RGB")

    exif = Image.Exif()
    prompt_json = json.dumps(workflow_payload, ensure_ascii=False, sort_keys=True)
    exif[0x0110] = f"prompt:{prompt_json}"          # EXIF Model tag
    exif[0x9286] = prompt_json.encode("utf-8")      # EXIF UserComment tag
    pil_image.save(output_path, format="JPEG", quality=quality, exif=exif)
    return str(output_path)


def save_png_image(
    image: Any,
    output_path: Union[str, os.PathLike[str]],
    prompt: Optional[dict[str, Any]] = None,
    extra_pnginfo: Optional[dict[str, Any]] = None,
    compress_level: int = PNG_COMPRESS_LEVEL,
) -> str:
    """按 ComfyUI 官方「保存图像」节点的方式保存 PNG。

    文本块写法与官方完全一致：``prompt`` 存 API 提示词，``extra_pnginfo`` 的每个键
    （通常是 ``workflow``）各存一个文本块，值各自 ``json.dumps``。把生成的 PNG 拖到
    ComfyUI 画布即可还原工作流。
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    pil_image = _pil_image_from(image, keep_alpha=True)

    metadata = PngImagePlugin.PngInfo()
    if prompt is not None:
        metadata.add_text("prompt", json.dumps(prompt))
    if isinstance(extra_pnginfo, dict):
        for key, value in extra_pnginfo.items():
            metadata.add_text(str(key), json.dumps(value))

    pil_image.save(
        output_path, format="PNG", pnginfo=metadata, compress_level=compress_level
    )
    return str(output_path)


class SaveImageNode:
    """将图片保存为 PNG（默认）或 JPG，输出预览图像与文件名。

    注册键为 ``SaveImageNode``：本节点**不兼容**改名前的旧工作流（旧工作流里记录
    的是 ``SaveJPGNode``）。序号按官方 ``SaveImage`` 的方式扫描输出目录后递增，
    因此连续运行不会覆盖历史输出。
    """

    CATEGORY = "YTmmi/image"
    DESCRIPTION = '保存图像：将图像保存为 PNG（默认，内嵌工作流）或 JPG 文件，输出预览图像与文件名'

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "图片": ("IMAGE",),
                "文件名前缀": ("STRING", {"default": "ComfyUI"}),
                "质量": ("INT", {"default": 95, "min": 1, "max": 100}),
            },
            "optional": {
                # 顺序不能改：旧工作流的 widgets_values 是 ["前缀", 质量, 子文件夹]，
                # 「格式」必须排在最后，旧工作流才会落到默认值 png 而不是错位。
                "子文件夹": ("STRING", {"default": ""}),
                "格式": (FORMAT_OPTIONS, {"default": DEFAULT_FORMAT}),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("预览图片", "文件名")
    FUNCTION = "save"
    OUTPUT_NODE = True
    OUTPUT_IS_LIST = (False, False)
    SEARCH_ALIASES = [
        "保存图像",
        "保存图片",
        "save image",
        "save png",
        "保存png",
        "保存jpg",
        "save jpg",
    ]

    def save(self, **kwargs):
        image = kwargs.get("图片")
        filename_prefix = kwargs.get("文件名前缀", "ComfyUI")
        quality = kwargs.get("质量", 95)
        subfolder = kwargs.get("子文件夹", "")
        image_format = self._normalize_format(kwargs.get("格式"))
        output_dir = kwargs.get("output_dir")
        prompt, extra_pnginfo = self._collect_metadata(kwargs)

        output_dir_path = (
            Path(output_dir)
            if output_dir is not None
            else self._get_output_dir(subfolder)
        )
        output_dir_path.mkdir(parents=True, exist_ok=True)

        if image is None:
            return (None, "")

        suffix = "png" if image_format == "png" else "jpg"
        safe_prefix = self._sanitize_filename(filename_prefix) or "ComfyUI"

        saved_names: list[str] = []
        pil_images = self._to_pil_images(image, keep_alpha=image_format == "png")
        # 与官方 SaveImage 一致：先扫描输出目录取「已有最大序号 + 1」，因此连续运行
        # 不会覆盖历史输出；同一批次内按偏移量递增，不再重复扫描。
        counter = self._next_counter(output_dir_path, safe_prefix)
        for offset, pil_image in enumerate(pil_images):
            # 文件名 = 前缀 + 自动序号；输出端口给的正是这一段（不含后缀）
            filename_base = f"{safe_prefix}_{counter + offset:05d}"
            output_path = output_dir_path / f"{filename_base}.{suffix}"
            if image_format == "png":
                self._save_png_with_metadata(
                    pil_image, output_path, prompt, extra_pnginfo
                )
            else:
                # JPG 没有 PNG 那样的文本块，沿用原有 EXIF 写法
                self._save_jpeg_with_metadata(
                    pil_image,
                    output_path,
                    self._collect_workflow_data(kwargs),
                    quality,
                )
            saved_names.append(filename_base)

        # 返回原始图像张量用于预览，并把本次保存的文件名（不含后缀）作为文本输出
        return (image, "\n".join(saved_names))

    @staticmethod
    def _next_counter(folder: Path, prefix: str) -> int:
        """扫描目录返回「已有最大序号 + 1」，逐条对齐官方 ``get_save_image_path``。

        官方 ``folder_paths.get_save_image_path``（``ComfyUI/folder_paths.py``）的
        判定是**在完整文件名（含扩展名）上**做的：

        1. 取文件名前 ``len(prefix) + 1`` 个字符，去掉最后一位后与前缀
           ``os.path.normcase`` 比较（Windows 上大小写不敏感）；
        2. 这前 ``len(prefix) + 1`` 个字符的最后一位必须正好是 ``_``；
        3. 余下部分先按**第一个** ``.`` 截断，再按第一个 ``_`` 截断，然后 ``int()``；
           解析失败按 ``0`` 计入；
        4. 取所有命中文件的最大值 + 1，一个都没命中则从 ``1`` 开始。

        这里刻意不写成「去掉扩展名再比较」：``splitext`` 按**最后一个**点切分，
        遇到含点的前缀（``v1.0``）或「序号后面还有段」的文件名（``x_00002.tar.png``）
        会和官方算错。``ComfyUI_00001_.png`` 与 ``ComfyUI_00002.png`` 两种官方历史
        写法都会被识别，扩展名本身不参与判定。
        """
        # 官方先对前缀做 ``basename(normpath(...))``；空前缀会变成 "."，这里保持一致
        # （节点入口已保证前缀非空，此归一化只为让计数规则与官方逐条对齐）。
        normalized = os.path.basename(os.path.normpath(prefix)) if prefix else "."
        prefix_len = len(normalized)
        prefix_key = os.path.normcase(normalized)
        highest: Optional[int] = None
        try:
            entries = os.listdir(folder)
        except (FileNotFoundError, NotADirectoryError):
            return 1
        for filename in entries:
            head = filename[: prefix_len + 1]
            if head[-1:] != "_":
                continue
            if os.path.normcase(head[:-1]) != prefix_key:
                continue
            remainder = filename[prefix_len + 1 :]
            try:
                digits = int(remainder.split(".")[0].split("_")[0])
            except (ValueError, IndexError):
                digits = 0
            if highest is None or digits > highest:
                highest = digits
        return 1 if highest is None else highest + 1

    @staticmethod
    def _normalize_format(value: Any) -> str:
        """把格式控件值归一化；无法识别时回落到默认的 png。"""
        if value is None:
            return DEFAULT_FORMAT
        text = str(value).strip().lower()
        if text in ("jpg", "jpeg"):
            return "jpg"
        return DEFAULT_FORMAT

    def _collect_metadata(
        self, kwargs: dict[str, Any]
    ) -> tuple[Any, Optional[dict[str, Any]]]:
        """取官方写法需要的原始元数据：API 提示词与 extra_pnginfo（含 workflow）。"""
        prompt = kwargs.get("prompt")
        extra_pnginfo = kwargs.get("extra_pnginfo")
        if not isinstance(extra_pnginfo, dict):
            extra_pnginfo = None
        return prompt, extra_pnginfo

    def _collect_workflow_data(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        prompt = kwargs.get("prompt")
        if prompt:
            return _normalize_workflow_payload(prompt)
        extra_pnginfo = kwargs.get("extra_pnginfo")
        if isinstance(extra_pnginfo, dict):
            return _normalize_workflow_payload(extra_pnginfo)
        return _normalize_workflow_payload({})

    def _get_output_dir(self, subfolder: str) -> Path:
        if folder_paths is not None:
            try:
                output_dir = folder_paths.get_output_directory()
                if subfolder:
                    output_dir = Path(output_dir) / subfolder
                return Path(output_dir)
            except Exception:
                pass
        base_dir = Path(os.getcwd()) / "output"
        if subfolder:
            base_dir = base_dir / subfolder
        return base_dir

    def _sanitize_filename(self, value: str) -> str:
        value = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
        return value or "ComfyUI"

    def _to_pil_images(self, image: Any, keep_alpha: bool = False) -> list[Image.Image]:
        if isinstance(image, Image.Image):
            return [image if keep_alpha else image.convert("RGB")]

        if torch is not None and isinstance(image, torch.Tensor):
            if image.ndim == 4:
                return [
                    _pil_image_from(image[i], keep_alpha=keep_alpha)
                    for i in range(image.shape[0])
                ]
            return [_pil_image_from(image, keep_alpha=keep_alpha)]

        if hasattr(image, "__iter__") and not isinstance(image, (str, bytes, dict)):
            result = []
            for item in image:
                result.extend(self._to_pil_images(item, keep_alpha=keep_alpha))
            return result

        raise TypeError(f"Unsupported image type: {type(image)!r}")

    def _save_png_with_metadata(
        self,
        image: Image.Image,
        output_path: Path,
        prompt: Any,
        extra_pnginfo: Optional[dict[str, Any]],
    ) -> None:
        save_png_image(
            image,
            output_path,
            prompt=prompt,
            extra_pnginfo=extra_pnginfo,
            compress_level=PNG_COMPRESS_LEVEL,
        )

    def _save_jpeg_with_metadata(
        self,
        image: Image.Image,
        output_path: Path,
        workflow_payload: dict[str, Any],
        quality: int,
    ) -> None:
        save_jpeg_image(
            image, output_path, workflow_data=workflow_payload, quality=quality
        )


NODE_CLASS_MAPPINGS = {
    # 注册键已改为 SaveImageNode；本节点不兼容改名前的旧工作流（旧键为 SaveJPGNode）
    "SaveImageNode": SaveImageNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SaveImageNode": "保存图像",
}

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "FORMAT_OPTIONS",
    "DEFAULT_FORMAT",
    "save_jpeg_image",
    "save_png_image",
    "SaveImageNode",
]
