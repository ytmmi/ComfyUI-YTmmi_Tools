import random
from pathlib import Path

try:
    import torch  # type: ignore
except Exception:
    torch = None

from PIL import Image


# ── 支持的图片扩展名 ──────────────────────────────────────────────
SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tiff", ".tif"}


def _normalize_path(raw: str) -> str:
    """规范化路径：去除首尾空格、引号、尾部反斜杠。"""
    raw = raw.strip().strip("\"'")
    # 去除尾部反斜杠（但保留盘符根目录如 "E:\" → "E:\"）
    while len(raw) > 3 and raw.endswith("\\"):
        raw = raw[:-1]
    return raw


def _list_image_files(folder: str) -> list[Path]:
    """递归（或非递归）列出文件夹下所有支持的图片文件。"""
    p = Path(folder)
    if not p.is_dir():
        return []
    files = []
    for f in p.iterdir():
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append(f)
    return files


def _sort_files(
    files: list[Path], order: str
) -> list[Path]:
    """根据 order 对文件列表排序。"固定"保持文件系统原生顺序。"""
    if order in ("固定", "随机"):
        return files  # 固定→原生顺序，随机→由外部 shuffle 处理

    is_reverse = "反序" in order

    if order.startswith("名称"):
        key_func = lambda f: f.name.lower()
    elif order.startswith("时间"):
        key_func = lambda f: f.stat().st_mtime
    elif order.startswith("类型"):
        key_func = lambda f: (f.suffix.lower(), f.name.lower())
    elif order.startswith("大小"):
        key_func = lambda f: f.stat().st_size
    else:
        key_func = lambda f: f.name.lower()

    return sorted(files, key=key_func, reverse=is_reverse)


def _load_image_as_tensor(path: Path) -> "torch.Tensor":
    """加载单张图片并转换为 torch Tensor (1, H, W, 3)。"""
    img = Image.open(path).convert("RGB")
    import numpy as np

    array = np.array(img).astype(np.float32) / 255.0
    tensor = torch.from_numpy(array).unsqueeze(0)  # (1, H, W, 3)
    return tensor


def _unify_tensor_sizes(tensors: list) -> list:
    """将不同尺寸的 tensor 统一到最大尺寸（右下 padding 0）。"""
    if len(tensors) <= 1:
        return tensors

    max_h = max(t.shape[1] for t in tensors)
    max_w = max(t.shape[2] for t in tensors)
    unified = []
    for t in tensors:
        h, w = t.shape[1], t.shape[2]
        if h == max_h and w == max_w:
            unified.append(t)
            continue
        padded = torch.zeros((1, max_h, max_w, 3), dtype=t.dtype, device=t.device)
        padded[:, :h, :w, :] = t
        unified.append(padded)
    return unified


# ── 节点类 ───────────────────────────────────────────────────────
class BatchLoadImagesNode:
    """批量加载指定路径文件夹内的图片。"""

    CATEGORY = "YTmmi/image"

    # 类级缓存：按 unique_id 持久化运行状态（即使节点重新实例化也不丢失）
    _state_cache: dict[str, dict] = {}

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "路径": ("STRING", {"default": "", "tooltip": "图片文件夹的绝对路径，如 E:\\QQ"}),
                "顺序": (
                    [
                        "固定",
                        "随机",
                        "名称 正序",
                        "名称 反序",
                        "时间 正序",
                        "时间 反序",
                        "类型 正序",
                        "类型 反序",
                        "大小 正序",
                        "大小 反序",
                    ],
                    {"default": "名称 正序", "tooltip": "图片排列顺序，固定时位置参数不变"},
                ),
                "位置": ("INT", {"default": 1, "min": 1, "max": 9999999, "step": 1, "tooltip": "从第几张图片开始输出（1为起始）"}),
                "种子": ("INT", {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF, "step": 1, "tooltip": "仅顺序为随机时生效：初始随机种子"}),
                "批次": ("INT", {"default": 1, "min": 1, "max": 9999, "step": 1, "tooltip": "一次输出几张图片"}),
                "生成后控制": (
                    ["固定", "增量", "递减", "随机化"],
                    {"default": "固定", "tooltip": "控制种子的变化方式"},
                ),
            },
            "hidden": {"unique_id": "UNIQUE_ID"},
        }

    RETURN_TYPES = ("IMAGE", "INT", "INT")
    RETURN_NAMES = ("images", "当前种子", "下一次位置")
    FUNCTION = "load"
    OUTPUT_NODE = False
    OUTPUT_IS_LIST = (False, False, False)

    @classmethod
    def IS_CHANGED(cls, unique_id="", **kwargs):
        """始终返回 float("NaN")，确保每次重新执行。"""
        return float("NaN")

    def load(
        self,
        路径: str = "",
        顺序: str = "名称 正序",
        位置: int = 1,
        种子: int = 0,
        批次: int = 1,
        生成后控制: str = "固定",
        unique_id: str = "",
    ):
        if torch is None:
            raise RuntimeError("torch is not available")

        # 获取/初始化状态缓存（按 unique_id 持久化，跨实例不丢失）
        state = BatchLoadImagesNode._state_cache.setdefault(
            unique_id,
            {
                "current_pos": None, "last_ui_pos": None,
                "current_seed": None, "last_ui_seed": None,
            },
        )

        # 1. 规范化路径
        folder = _normalize_path(路径)
        if not folder:
            raise ValueError("路径不能为空")

        folder_path = Path(folder)
        if not folder_path.is_dir():
            raise ValueError(f"路径不存在或不是文件夹: {folder}")

        # 2. 列出图片文件
        files = _list_image_files(str(folder_path))
        if not files:
            raise ValueError(f"文件夹中没有找到支持的图片文件: {folder}")

        total = len(files)

        # 3. 排序
        files = _sort_files(files, 顺序)

        # ── 种子控制（仅顺序为"随机"时使用）─────────────────
        # 检测用户是否手动修改了"种子"（区别于 JS 自动回填）
        if state["last_ui_seed"] is not None and 种子 != state["last_ui_seed"]:
            state["current_seed"] = 种子
        elif state["current_seed"] is None:
            state["current_seed"] = 种子

        effective_seed = state["current_seed"]

        # 仅随机顺序时才用种子打乱
        if 顺序 == "随机":
            rng = random.Random(effective_seed)
            rng.shuffle(files)

        # ── 位置控制（"固定"和"随机"时位置不变）─────────────────
        # 检测用户是否手动修改了"位置"（区别于 JS 自动回填）
        if state["last_ui_pos"] is not None and 位置 != state["last_ui_pos"]:
            state["current_pos"] = 位置
        elif state["current_pos"] is None:
            state["current_pos"] = 位置

        effective_position = state["current_pos"]

        # 4. 计算索引（1-indexed → 0-indexed，超出取余回绕）
        pos = (effective_position - 1) % total
        # 5. 从起始位置取批次数量的图片（同样支持取余回绕）
        batch_size = max(1, int(批次))
        selected: list[Path] = []
        for i in range(batch_size):
            idx = (pos + i) % total
            selected.append(files[idx])

        # 6. 加载图片为 tensor，统一尺寸后拼接
        tensors = [_load_image_as_tensor(p) for p in selected]
        tensors = _unify_tensor_sizes(tensors)
        result = torch.cat(tensors, dim=0)  # (B, H, W, 3)

        # ── 运行后控制：先输出图片，再改变参数 ──────────────
        # 位置：非"固定"且非"随机"时 +批次
        if 顺序 not in ("随机", "固定"):
            state["current_pos"] = effective_position + batch_size

        # 种子：根据生成后控制模式改变
        if 生成后控制 == "增量":
            state["current_seed"] = effective_seed + 1
        elif 生成后控制 == "递减":
            state["current_seed"] = effective_seed - 1
        elif 生成后控制 == "随机化":
            state["current_seed"] = random.randint(0, 0xFFFFFFFFFFFFFFFF)

        # 记录本次输出到 UI 的值，下次运行对比以判断是否手动修改
        state["last_ui_seed"] = effective_seed
        state["last_ui_pos"] = effective_position

        return {
            "ui": {
                "seed": [effective_seed],
                "pos": [state["current_pos"]],
            },
            "result": (result, effective_seed, state["current_pos"]),
        }



NODE_CLASS_MAPPINGS = {
    "BatchLoadImagesNode": BatchLoadImagesNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BatchLoadImagesNode": "批量加载图片",
}

__all__ = [
    "BatchLoadImagesNode",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
