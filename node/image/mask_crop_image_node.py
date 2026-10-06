# 遮罩裁剪图像
"""遮罩裁剪图像：按遮罩的非零区域裁剪图像与遮罩，并输出裁剪框坐标。

功能对齐 ComfyUI-Easy-Use 扩展的「遮罩裁剪图像」（imageCropFromMask）节点：
取遮罩非零区域的外接尺寸作为裁剪尺寸，以遮罩重心为中心定位裁剪框，
再把裁剪框夹取到画面范围内。本节点**只处理单张图像，不做批次**，
并把原来的 BBOX 输出拆成「坐标x / 坐标y / 宽 / 高」四个端口，
方便直接接给配套的「图像合并」节点还原画面；Easy-Use 的
「图像裁剪乘数」与「遮罩裁剪乘数」也合并为单一「裁剪乘数」。

与 Easy-Use 的差异：尺寸取 ``max - min + 1``，因此「裁剪乘数」为 1 时
裁剪框**完整包含遮罩的全部非零像素**（Easy-Use 用 ``max - min`` 会丢掉最后一列/行）。

坐标端口声明为 ``INT,FLOAT`` 联合类型：裁剪结果本来就是整数像素，
而配套「图像合并」的坐标输入是 FLOAT（需要支持 0~1 百分比），
联合类型让坐标既能接 FLOAT 输入、也能接 INT 输入。
"""

import numpy as np

try:
    import torch  # type: ignore
except Exception:  # pragma: no cover - 可选依赖降级，避免导入失败
    torch = None


def _as_single_image(image):
    """把 IMAGE 规整为 ``[1, H, W, C]``。"""
    tensor = image
    if tensor.ndim == 3:
        tensor = tensor.unsqueeze(0)
    elif tensor.ndim == 2:
        tensor = tensor.unsqueeze(0).unsqueeze(-1)
    return tensor


def _as_single_mask(mask):
    """把 MASK 规整为 ``[1, H, W]``。"""
    tensor = mask
    if tensor.ndim == 2:
        tensor = tensor.unsqueeze(0)
    elif tensor.ndim == 4 and tensor.shape[-1] == 1:
        tensor = tensor[..., 0]
    return tensor


def _place_axis(center: int, box: int, lo_mask: int, hi_mask: int, limit: int) -> int:
    """在 ``[0, limit - box]`` 内定位起点：以 ``center`` 居中，并优先保证覆盖 ``lo_mask..hi_mask``。

    只要 ``box`` 不小于遮罩跨度，就一定能找到一个既不越界、又完整包含遮罩的起点，
    此时在该区间内取「居中」的那一个；``box`` 小于跨度（``裁剪乘数 < 1``）时无法包含，
    退回单纯的居中并夹取到画面内。
    """
    start = center - box // 2

    # 左边界最靠右 / 最靠左时，仍能覆盖遮罩的取值区间
    contain_lo = max(0, hi_mask - box + 1)
    contain_hi = min(lo_mask, limit - box)
    if contain_lo <= contain_hi:
        return min(max(start, contain_lo), contain_hi)

    return max(0, min(start, limit - box))


def compute_crop_box(mask_np, crop_multi: float = 1.0):
    """按遮罩非零区域算出裁剪框 ``(x, y, 宽, 高)``。

    尺寸取 ``max - min + 1``（``max`` 是含端点的像素坐标），因此 ``裁剪乘数 = 1`` 时
    裁剪框**完整包含遮罩的所有非零像素**——这是本节点与 Easy-Use 的关键差异：
    Easy-Use 用 ``max - min`` 会少算最后一列/行，导致裁剪结果丢掉遮罩边缘
    （例如 10x10 的方形遮罩会被裁成 9x9）。

    中心取遮罩重心，随后在「既不越界、又完整包含遮罩」的范围内定位，
    因此 ``裁剪乘数 >= 1`` 时永远不会有遮罩像素落在裁剪框外。
    """
    height, width = mask_np.shape
    ys, xs = np.nonzero(mask_np)
    if xs.size == 0:
        raise ValueError("遮罩全为空白（没有任何非零像素），无法计算裁剪区域")

    min_x, max_x = int(xs.min()), int(xs.max())
    min_y, max_y = int(ys.min()), int(ys.max())

    # +1：max 是含端点的像素坐标，max - min + 1 才是遮罩真正占用的像素数
    box_w = max(1, int(round((max_x - min_x + 1) * crop_multi)))
    box_h = max(1, int(round((max_y - min_y + 1) * crop_multi)))
    box_w = min(box_w, width)
    box_h = min(box_h, height)

    center_x = int(round(float(xs.mean())))
    center_y = int(round(float(ys.mean())))

    x = _place_axis(center_x, box_w, min_x, max_x, width)
    y = _place_axis(center_y, box_h, min_y, max_y, height)
    return int(x), int(y), int(box_w), int(box_h)


class MaskCropImageNode:
    """遮罩裁剪图像。"""

    CATEGORY = "YTmmi/image"
    DESCRIPTION = "遮罩裁剪图像：按遮罩区域裁剪图像与遮罩，输出裁剪框的坐标x、坐标y、宽、高，并原样透传原始图像"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "图像": ("IMAGE",),
                "遮罩": ("MASK",),
                "裁剪乘数": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 10.0, "step": 0.001}),
            },
        }

    # 坐标用 INT,FLOAT 联合类型：既能接「图像合并」的 FLOAT 坐标输入，也能接 INT 输入
    RETURN_TYPES = ("IMAGE", "IMAGE", "MASK", "INT,FLOAT", "INT,FLOAT", "INT", "INT")
    RETURN_NAMES = ("原始图像", "裁剪图像", "裁剪遮罩", "坐标x", "坐标y", "宽", "高")
    FUNCTION = "crop"
    OUTPUT_NODE = False
    OUTPUT_IS_LIST = (False, False, False, False, False, False, False)
    SEARCH_ALIASES = ["mask crop", "crop from mask", "遮罩裁剪", "裁剪图像"]

    def crop(self, **kwargs):
        if torch is None:
            raise RuntimeError("遮罩裁剪图像节点需要 torch 环境")

        image = kwargs.get("图像")
        mask = kwargs.get("遮罩")
        if image is None or mask is None:
            raise ValueError("遮罩裁剪图像需要同时连接「图像」与「遮罩」")

        # Easy-Use 的图像裁剪乘数与遮罩裁剪乘数在此合并为一个「裁剪乘数」，同时作用于两者
        crop_multi = float(kwargs.get("裁剪乘数", 1.0))

        image_t = _as_single_image(image).float()
        mask_t = _as_single_mask(mask).float()

        if image_t.shape[0] != 1:
            raise ValueError(
                f"遮罩裁剪图像只处理单张图像，当前输入为 {image_t.shape[0]} 张；"
                "请先用「Get Image from Batch」（image/batch）等节点取出单张"
            )
        if mask_t.shape[0] != 1:
            raise ValueError(
                f"遮罩裁剪图像只处理单张遮罩，当前输入为 {mask_t.shape[0]} 张；"
                "请先取出单张遮罩"
            )

        if image_t.shape[1] != mask_t.shape[1] or image_t.shape[2] != mask_t.shape[2]:
            raise ValueError(
                f"「图像」与「遮罩」尺寸不一致：图像 {image_t.shape[2]}x{image_t.shape[1]}，"
                f"遮罩 {mask_t.shape[2]}x{mask_t.shape[1]}"
            )

        mask_np = mask_t[0].detach().cpu().numpy() > 0
        x, y, box_w, box_h = compute_crop_box(mask_np, crop_multi)

        # 裁剪框已夹取到画面内，直接按它裁出，输出尺寸恒等于 (box_h, box_w)
        cropped_image = image_t[:, y : y + box_h, x : x + box_w, :]
        cropped_mask = mask_t[:, y : y + box_h, x : x + box_w]

        return (
            image_t,
            cropped_image,
            cropped_mask,
            int(x),
            int(y),
            int(box_w),
            int(box_h),
        )


NODE_CLASS_MAPPINGS = {
    "MaskCropImageNode": MaskCropImageNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MaskCropImageNode": "遮罩裁剪图像",
}

__all__ = [
    "MaskCropImageNode",
    "compute_crop_box",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
