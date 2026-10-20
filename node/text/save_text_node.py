# 保存文本
import csv
import io
import json
import os
import re
from pathlib import Path
from typing import Any, Optional

try:
    import torch  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    torch = None

try:
    import numpy  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    numpy = None

try:
    from PIL import Image  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    Image = None

try:
    import folder_paths  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    folder_paths = None

# 保存格式：扩展名即格式名，txt 为默认
FORMAT_OPTIONS = ["txt", "md", "csv", "json"]
DEFAULT_FORMAT = "txt"
# 命名方式：关闭（默认）= 文件前缀 + 自动序号；打开 = 使用「文件名」作为完整文件名
DEFAULT_USE_FILENAME = False
DEFAULT_PREFIX = "text"
DEFAULT_FILENAME = "text"
# Windows 非法文件名字符（不含中文等 Unicode 字符，故中文文件名会被原样保留）
_ILLEGAL_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|\x00-\x1f]')


def _sanitize_filename(value: Any, fallback: str) -> str:
    """清掉路径分隔符与 Windows 非法字符，保留中文；结果为空时用 fallback。"""
    text = "" if value is None else str(value)
    text = _ILLEGAL_FILENAME_CHARS.sub("_", text.strip()).strip(" .")
    return text or fallback


def _cell_text(value: Any) -> str:
    """把任意值转成 CSV 单元格文本。"""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, (dict, list, tuple)):
        return _json_text(value)
    summary = _summary_text(value)
    return summary if summary is not None else str(value)


def _json_text(value: Any) -> str:
    """JSON 序列化；遇到不可序列化对象时用 str() 兜底而不是抛错。"""
    try:
        return json.dumps(value, ensure_ascii=False, indent=2)
    except (TypeError, ValueError):
        return json.dumps(value, ensure_ascii=False, indent=2, default=str)


def _csv_text(value: Any) -> str:
    """把 dict / 二维列表 / 一维列表转成 CSV 文本（换行统一为 \\n）。"""
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")

    if isinstance(value, dict):
        writer.writerow(["key", "value"])
        for key, item in value.items():
            writer.writerow([_cell_text(key), _cell_text(item)])
        return buffer.getvalue()

    items = list(value) if isinstance(value, (list, tuple)) else [value]
    if items and all(isinstance(item, dict) for item in items):
        fieldnames: list[str] = []
        for item in items:
            for key in item:
                name = str(key)
                if name not in fieldnames:
                    fieldnames.append(name)
        dict_writer = csv.DictWriter(
            buffer, fieldnames=fieldnames, lineterminator="\n"
        )
        dict_writer.writeheader()
        for item in items:
            dict_writer.writerow(
                {
                    str(key): _cell_text(item.get(key, ""))
                    for key in item
                    if str(key) in fieldnames
                }
            )
        return buffer.getvalue()

    if items and all(isinstance(item, (list, tuple)) for item in items):
        for item in items:
            writer.writerow([_cell_text(cell) for cell in item])
        return buffer.getvalue()

    for item in items:
        writer.writerow([_cell_text(item)])
    return buffer.getvalue()


def _summary_text(value: Any) -> Optional[str]:
    """图像/数组等大对象只写结构摘要，避免把整张图逐像素转成文本。"""
    if torch is not None and isinstance(value, torch.Tensor):
        return (
            f"<torch.Tensor shape={tuple(value.shape)} "
            f"dtype={value.dtype} device={value.device}>"
        )
    if numpy is not None and isinstance(value, numpy.ndarray):
        return f"<numpy.ndarray shape={tuple(value.shape)} dtype={value.dtype}>"
    if Image is not None and isinstance(value, Image.Image):
        return f"<PIL.Image mode={value.mode} size={value.size}>"
    return None


def _to_text(value: Any, text_format: str) -> str:
    """把任意类型的输入转换成要写入文件的文本。

    - ``str`` 原样写出（不重排格式，与旧「保存json文件」节点的行为一致）；
    - ``bytes`` 按 UTF-8 解码；
    - 图像 / 张量 / 数组只写结构摘要；
    - ``csv`` 走 CSV 序列化，``json`` 走 JSON 序列化，``txt`` / ``md`` 对
      dict / list 用 JSON（可读性最好），其余用 ``str()``。
    """
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")

    summary = _summary_text(value)
    if summary is not None:
        return summary

    if text_format == "csv":
        return _csv_text(value)
    if text_format == "json":
        return _json_text(value)
    if isinstance(value, (dict, list, tuple)):
        return _json_text(value)
    return str(value)


def _next_counter(folder: Path, prefix: str) -> int:
    """扫描目录返回「已有最大序号 + 1」，逐条对齐官方 ``get_save_image_path``。

    规则与 ``node/image/save_image_node.py`` 的 ``SaveImageNode._next_counter``
    完全一致（两处都对齐 ``ComfyUI/folder_paths.py:529``），故这里不重复注释：
    判定在**完整文件名（含扩展名）**上做，取前 ``len(prefix) + 1`` 个字符、末位必须
    是 ``_``、前缀按 ``os.path.normcase`` 比较，余下部分先按第一个 ``.`` 再按第一个
    ``_`` 截断后 ``int()``，解析失败按 0 计入。**不要**改成先 ``splitext`` 去扩展名
    ——那样按最后一个点切分，含点前缀或「序号后还有段」的文件名都会算错。
    """
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


class SaveTextNode:
    """把任意类型的输入保存为文本文件，输出文件路径。

    「使用文件名」开关关闭（默认）时用「文件前缀」+ 自动序号命名，序号按官方
    ``SaveImage`` 的规则扫描输出目录后递增，连续运行不会覆盖历史文件；打开时直接
    用「文件名」作为完整文件名（同名文件会被覆盖，这正是该模式的用途）。
    """

    CATEGORY = "YTmmi/text"
    DESCRIPTION = (
        '保存文本：把任意类型的输入保存为 txt / md / csv / json 文本文件，'
        '可用「文件前缀」+ 自动序号或指定「文件名」，输出文件路径'
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # 通配类型：允许连接任意类型的输出端口
                "文本": ("*",),
                "使用文件名": (
                    "BOOLEAN",
                    {
                        "default": DEFAULT_USE_FILENAME,
                        # label_on / label_off 让开关直接显示当前生效的是哪一种命名
                        "label_on": "文件名",
                        "label_off": "文件前缀",
                        "tooltip": "关闭：用「文件前缀」+ 自动序号命名；打开：用「文件名」作为完整文件名",
                    },
                ),
                "文件前缀": (
                    "STRING",
                    {"default": DEFAULT_PREFIX, "tooltip": "关闭「使用文件名」时生效，会自动追加序号"},
                ),
                "文件名": (
                    "STRING",
                    {"default": DEFAULT_FILENAME, "tooltip": "打开「使用文件名」时生效，同名文件会被覆盖"},
                ),
                "格式": (FORMAT_OPTIONS, {"default": DEFAULT_FORMAT}),
            },
            "optional": {
                "子文件夹": ("STRING", {"default": ""}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("文件路径",)
    FUNCTION = "save"
    OUTPUT_NODE = True
    OUTPUT_IS_LIST = (False,)
    SEARCH_ALIASES = [
        "保存文本",
        "保存文本文件",
        "保存txt",
        "保存json",
        "保存csv",
        "保存md",
        "save text",
        "save txt",
        "save json",
    ]

    def save(self, **kwargs):
        content = kwargs.get("文本")
        use_filename = self._normalize_bool(kwargs.get("使用文件名"))
        filename_prefix = kwargs.get("文件前缀", DEFAULT_PREFIX)
        filename = kwargs.get("文件名", DEFAULT_FILENAME)
        text_format = self._normalize_format(kwargs.get("格式"))
        subfolder = kwargs.get("子文件夹", "")
        output_dir = kwargs.get("output_dir")

        output_dir_path = (
            # output_dir 仅供测试覆盖根目录；子文件夹在两种情况下都要生效
            self._get_output_dir(subfolder, base_dir=output_dir)
            if output_dir is not None
            else self._get_output_dir(subfolder)
        )
        output_dir_path.mkdir(parents=True, exist_ok=True)

        payload = _to_text(content, text_format)

        if use_filename:
            # 指定文件名模式：已带同格式后缀时不重复追加
            name = _sanitize_filename(filename, DEFAULT_FILENAME)
            if name.lower().endswith(f".{text_format}"):
                filename_base = name[: -(len(text_format) + 1)]
                filename = name
            else:
                filename_base = name
                filename = f"{name}.{text_format}"
        else:
            # 前缀模式：与官方 SaveImage 一致，先扫描输出目录取「已有最大序号 + 1」
            prefix = _sanitize_filename(filename_prefix, DEFAULT_PREFIX)
            filename_base = f"{prefix}_{_next_counter(output_dir_path, prefix):05d}"
            filename = f"{filename_base}.{text_format}"

        output_path = output_dir_path / filename
        output_path.write_text(payload, encoding="utf-8", newline="\n")
        return (str(output_path),)

    @staticmethod
    def _normalize_bool(value: Any) -> bool:
        """把开关值归一化；字符串 "false"/"0"/"" 视为关闭。"""
        if isinstance(value, bool):
            return value
        if value is None:
            return DEFAULT_USE_FILENAME
        if isinstance(value, (int, float)):
            return bool(value)
        return str(value).strip().lower() not in ("", "0", "false", "no", "off")

    @staticmethod
    def _normalize_format(value: Any) -> str:
        """把格式控件值归一化；无法识别时回落到默认的 txt。"""
        if value is None:
            return DEFAULT_FORMAT
        text = str(value).strip().lower()
        return text if text in FORMAT_OPTIONS else DEFAULT_FORMAT

    def _get_output_dir(self, subfolder: str, base_dir: Any = None) -> Path:
        if base_dir is not None:
            root = Path(base_dir)
            return root / subfolder if subfolder else root
        if folder_paths is not None:
            try:
                output_dir = folder_paths.get_output_directory()
                if subfolder:
                    output_dir = Path(output_dir) / subfolder
                return Path(output_dir)
            except Exception:
                pass
        root = Path(os.getcwd()) / "output"
        return root / subfolder if subfolder else root


NODE_CLASS_MAPPINGS = {
    "SaveTextNode": SaveTextNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SaveTextNode": "保存文本",
}

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "FORMAT_OPTIONS",
    "DEFAULT_FORMAT",
    "SaveTextNode",
]
