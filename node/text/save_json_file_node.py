# 保存json文件
import json
import os
import re
from pathlib import Path

try:
    import folder_paths  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    folder_paths = None


class SaveJsonFileNode:
    """将 JSON 数据保存为文件，并输出文件路径。"""

    CATEGORY = "YTmmi/text"
    DESCRIPTION = '保存json文件：将 JSON 数据写入磁盘文件，返回文件路径'

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "json数据": ("STRING", {"default": "{}"}),
                "文件名前缀": ("STRING", {"default": "workflow"}),
            },
            "optional": {
                "子文件夹": ("STRING", {"default": ""}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("json文件路径",)
    FUNCTION = "save"
    OUTPUT_NODE = True
    OUTPUT_IS_LIST = (False,)

    def save(self, **kwargs):
        json_data = kwargs.get("json数据")
        filename_prefix = kwargs.get("文件名前缀", "workflow")
        subfolder = kwargs.get("子文件夹", "")
        output_dir = kwargs.get("output_dir")
        output_dir_path = (
            Path(output_dir) if output_dir is not None else self._get_output_dir(subfolder)
        )
        output_dir_path.mkdir(parents=True, exist_ok=True)

        if isinstance(json_data, (dict, list)):
            payload = json.dumps(json_data, ensure_ascii=False, indent=2, sort_keys=True)
        else:
            payload = str(json_data or "{}")

        safe_prefix = re.sub(r"[^A-Za-z0-9._-]+", "_", str(filename_prefix).strip()) or "workflow"
        output_path = output_dir_path / f"{safe_prefix}.json"
        output_path.write_text(payload, encoding="utf-8")
        return (str(output_path),)

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


NODE_CLASS_MAPPINGS = {
    "SaveJsonFileNode": SaveJsonFileNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SaveJsonFileNode": "保存json文件",
}

__all__ = [
    "SaveJsonFileNode",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
