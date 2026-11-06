# 批量加载图像
"""批量加载图像节点。

从指定文件夹批量加载图片，输出图像批次、当前种子与下一次读取位置。

输入说明：
- 路径：图片文件夹的绝对路径
- 顺序：文件排列方式（固定 / 随机 / 名称·时间·类型·大小的正序与反序）
- 位置：从第几张开始输出（1 为起始），超出总数自动回绕
- 种子：仅「顺序 = 随机」时用于打乱文件顺序
- 批次：一次输出几张图片

生成后控制（control_after_generate）：
「种子」使用 ComfyUI 官方的 control_after_generate 机制（与 KSampler 等节点完全
一致），**仅控制种子本身**，节点后端不参与：

- 后端只在「种子」输入上声明 ``"control_after_generate": True``；
- 前端据此自动生成配套的「生成后控制」下拉（固定值/递增值/递减值/随机值），
  该下拉 ``serialize: false``，**不会出现在发给后端的 prompt 里**；
- 生成结束后由前端在本地按所选模式改写「种子」控件值（下一次执行即用新种子），
  因此后端**无需**为种子维护状态缓存，也**无需**回填种子 ui。

「位置」的自动递增仍由后端维护（与官方生成后控制无关）：位置按批次递增，并通过
ui 回填给前端，因此本节点保留 IS_CHANGED，确保每次执行都真正重新读取图片。
"""
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
    """批量加载指定路径文件夹内的图像。"""

    CATEGORY = "YTmmi/image"
    DESCRIPTION = '批量加载图像：从文件夹批量加载图像为图像批次，支持随机/顺序读取与循环播放，输出图像列表、当前种子与下一次读取位置（含官方生成后控制）'

    # 类级缓存：按 unique_id 持久化「位置」运行状态（即使节点重新实例化也不丢失）
    # 只维护位置；种子由前端官方 control_after_generate 机制接管，后端不缓存
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
                # 「种子」使用 ComfyUI 官方 control_after_generate 机制（与 KSampler 一致）：
                # 前端据此自动生成配套的「生成后控制」下拉（固定值/递增值/递减值/随机值），
                # 该下拉 serialize:false 不会发给后端，仅由前端在生成后改写种子控件值。
                "种子": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": 0xFFFFFFFFFFFFFFFF,
                        "step": 1,
                        "control_after_generate": True,
                        "tooltip": "仅顺序为随机时生效：初始随机种子。"
                        "旁边的「生成后控制」可让它在每次生成后自动变化",
                    },
                ),
                "批次": ("INT", {"default": 1, "min": 1, "max": 9999, "step": 1, "tooltip": "一次输出几张图片"}),
            },
            "hidden": {"unique_id": "UNIQUE_ID"},
        }

    RETURN_TYPES = ("IMAGE", "INT", "INT")
    RETURN_NAMES = ("图片", "当前种子", "下一次位置")
    FUNCTION = "load"
    OUTPUT_NODE = False
    OUTPUT_IS_LIST = (False, False, False)
    SEARCH_ALIASES = [
        "批量加载",
        "batch load images",
        "加载图片",
        "种子",
        "生成后控制",
    ]

    @classmethod
    def IS_CHANGED(cls, unique_id="", **kwargs):
        """始终返回 float("NaN")，确保每次重新执行。

        「位置」每次执行都会按批次递增，缓存必须失效才会重新读取图片。
        （种子本身由前端官方 control_after_generate 改写，天然改变缓存 key。）
        """
        return float("NaN")

    def load(
        self,
        路径: str = "",
        顺序: str = "名称 正序",
        位置: int = 1,
        种子: int = 0,
        批次: int = 1,
        unique_id: str = "",
    ):
        if torch is None:
            raise RuntimeError("torch is not available")

        # 获取/初始化状态缓存（按 unique_id 持久化，跨实例不丢失）
        # 只维护「位置」：种子由前端官方 control_after_generate 机制接管，后端不缓存
        state = BatchLoadImagesNode._state_cache.setdefault(
            unique_id,
            {"current_pos": None, "last_ui_pos": None},
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

        # ── 种子（仅顺序为"随机"时使用）────────────────────────
        # 种子完全由前端官方 control_after_generate 机制接管：
        # 后端不推进、不缓存、不回填，直接使用输入值。
        effective_seed = 种子

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

        # 记录本次输出到 UI 的值，下次运行对比以判断是否手动修改
        state["last_ui_pos"] = effective_position

        return {
            # 只回填「位置」；「种子」由前端官方生成后控制机制本地改写，后端不回填
            "ui": {
                "pos": [state["current_pos"]],
            },
            "result": (result, effective_seed, state["current_pos"]),
        }



NODE_CLASS_MAPPINGS = {
    "BatchLoadImagesNode": BatchLoadImagesNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BatchLoadImagesNode": "批量加载图像",
}

__all__ = [
    "BatchLoadImagesNode",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
