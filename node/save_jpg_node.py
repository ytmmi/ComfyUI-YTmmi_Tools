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


def _normalize_workflow_payload(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict):
        if "workflow" in payload:
            return payload
        return {"workflow": payload}
    if payload is None:
        return {"workflow": {}}
    return {"workflow": payload}


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

    if isinstance(image, Image.Image):
        pil_image = image.convert("RGB")
    elif torch is not None and isinstance(image, torch.Tensor):
        if image.ndim == 4:
            image = image[0]
        if image.device.type != "cpu":
            image = image.detach().cpu()
        array = image.numpy()
        if array.ndim == 3 and array.shape[-1] == 4:
            pil_image = Image.fromarray(
                (array * 255).clip(0, 255).astype("uint8"), "RGBA"
            ).convert("RGB")
        else:
            pil_image = Image.fromarray(
                (array * 255).clip(0, 255).astype("uint8"), "RGB"
            )
    else:
        raise TypeError(f"Unsupported image type: {type(image)!r}")

    exif = Image.Exif()
    prompt_json = json.dumps(workflow_payload, ensure_ascii=False, sort_keys=True)
    exif[0x0110] = f"prompt:{prompt_json}"          # EXIF Model tag
    exif[0x9286] = prompt_json.encode("utf-8")      # EXIF UserComment tag
    pil_image.save(output_path, format="JPEG", quality=quality, exif=exif)
    return str(output_path)


class SaveJPGNode:
    """将图片保存为 JPEG，并将工作流数据写入 EXIF 元数据，同时提供预览输出。"""

    CATEGORY = "YTmmi/image"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "filename_prefix": ("STRING", {"default": "ComfyUI"}),
                "quality": ("INT", {"default": 95, "min": 1, "max": 100}),
            },
            "optional": {
                "subfolder": ("STRING", {"default": ""}),
            },
            "hidden": {
                "prompt": ("PROMPT",),
                "extra_pnginfo": ("EXTRA_PNGINFO",),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("preview_image",)
    FUNCTION = "save"
    OUTPUT_NODE = True
    OUTPUT_IS_LIST = (False,)

    def save(self, image, filename_prefix="ComfyUI", quality=95, subfolder="", **kwargs):
        workflow_payload = self._collect_workflow_data(kwargs)
        output_dir = self._get_output_dir(subfolder)
        output_dir.mkdir(parents=True, exist_ok=True)

        if image is None:
            return (None,)

        pil_images = self._to_pil_images(image)
        for index, pil_image in enumerate(pil_images, start=1):
            safe_prefix = self._sanitize_filename(filename_prefix) or "ComfyUI"
            filename = f"{safe_prefix}_{index:05d}.jpg"
            output_path = output_dir / filename
            self._save_jpeg_with_metadata(
                pil_image, output_path, workflow_payload, quality
            )

        # 返回原始图像张量，用于预览
        return (image,)

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

    def _to_pil_images(self, image: Any) -> list[Image.Image]:
        if isinstance(image, Image.Image):
            return [image.convert("RGB")]

        if torch is not None and isinstance(image, torch.Tensor):
            if image.ndim == 4:
                tensors = [image[i] for i in range(image.shape[0])]
            else:
                tensors = [image]

            pil_images = []
            for tensor in tensors:
                if tensor.device.type != "cpu":
                    tensor = tensor.detach().cpu()
                array = tensor.numpy()
                if array.ndim == 4:
                    array = array[0]
                if array.ndim == 3:
                    if array.shape[-1] == 1:
                        array = array.repeat(3, axis=-1)
                    if array.shape[-1] == 4:
                        pil_image = Image.fromarray(
                            (array * 255).clip(0, 255).astype("uint8"), "RGBA"
                        )
                        pil_images.append(pil_image.convert("RGB"))
                        continue
                    pil_image = Image.fromarray(
                        (array * 255).clip(0, 255).astype("uint8"), "RGB"
                    )
                    pil_images.append(pil_image)
                else:
                    pil_images.append(
                        Image.fromarray((array * 255).clip(0, 255).astype("uint8"), "L")
                    )
            return pil_images

        if hasattr(image, "__iter__") and not isinstance(image, (str, bytes, dict)):
            result = []
            for item in image:
                result.extend(self._to_pil_images(item))
            return result

        raise TypeError(f"Unsupported image type: {type(image)!r}")

    def _save_jpeg_with_metadata(
        self,
        image: Image.Image,
        output_path: Path,
        workflow_payload: dict[str, Any],
        quality: int,
    ) -> None:
        exif = Image.Exif()
        metadata_text = json.dumps(workflow_payload, ensure_ascii=False, sort_keys=True)
        exif[0x0110] = f"prompt:{metadata_text}"
        exif[0x9286] = metadata_text.encode("utf-8")
        image.convert("RGB").save(output_path, format="JPEG", quality=quality, exif=exif)


NODE_CLASS_MAPPINGS = {
    "SaveJPGNode": SaveJPGNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SaveJPGNode": "保存jpg图像",
}

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "save_jpeg_image",
    "SaveJPGNode",
]