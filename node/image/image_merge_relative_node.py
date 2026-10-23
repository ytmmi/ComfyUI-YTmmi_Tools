# 图像合并(相对)
"""图像合并(相对)：按「水平对齐 / 垂直对齐」把上层图像对齐到底层图像（画布），再叠加 x / y 偏移。

与「图像合并(坐标)」的差别只在**定位方式**：坐标版直接给出上层左上角的「坐标x / 坐标y」，
本节点先按对齐方式算出基准位置，再在基准上叠加偏移——
「左 / 上」的基准是 0，「居中」的基准是 ``(画布尺寸 - 上层尺寸) // 2``，
「右 / 下」的基准是 ``画布尺寸 - 上层尺寸``。偏移值 ``0 ~ 1``（不含 1）按**画布尺寸的百分比**，
其余按像素（可为负），与坐标版的坐标口径完全一致，因此 0.5 永远表示「半个画布」。

画布取**处于底层的那张图**：默认「图像0」在下、「图像1」在上，因此画布 = 图像0；
打开「图层顺序翻转」后「图像1」在下，画布 = 图像1。处于上层的那张图按对齐 + 偏移
贴到画布上，超出画布的部分会被裁掉，画布不会因此变大。

可选「遮罩」输入作用于**上层图层**，作为它的蒙版：遮罩为 1 的地方显示上层，
为 0 的地方透出底层——与 ComfyUI 官方「Image Composite Masked」的
``mask * source + (1 - mask) * destination`` 约定一致。

贴图 / 混合逻辑与「图像合并(坐标)」共用同一份实现（`image_merge_node` 的模块级助手），
两个节点的画布语义、通道归一化与蒙版极性因此逐像素一致。
"""

try:  # 作为插件包的一部分被加载（ComfyUI 的正常加载路径）
    from .image_merge_node import (
        _as_image_batch,
        _as_mask_batch,
        _paste,
        _resize_mask,
        _stretch,
        resolve_axis,
    )
except ImportError:  # 直接以模块方式加载（测试 / 独立脚本把 node/image 加进了 sys.path）
    from image_merge_node import (
        _as_image_batch,
        _as_mask_batch,
        _paste,
        _resize_mask,
        _stretch,
        resolve_axis,
    )

try:
    import torch  # type: ignore
except Exception:  # pragma: no cover - 可选依赖降级，避免导入失败
    torch = None


HORIZONTAL_ALIGNMENTS = ["左", "居中", "右"]
VERTICAL_ALIGNMENTS = ["上", "居中", "下"]


def resolve_aligned_axis(alignment: str, canvas_size: int, patch_size: int) -> int:
    """按对齐方式算基准位置（不含偏移）。

    「左 / 上」贴边对齐（0），「右 / 下」贴另一边（画布 - 上层），
    其余（含「居中」与任何未知值）取居中位置。上层比画布大时居中值可能为负，
    此时上层两侧等量溢出、由 `_paste` 裁掉。
    """
    alignment = str(alignment)
    if alignment in ("左", "上"):
        return 0
    if alignment in ("右", "下"):
        return canvas_size - patch_size
    return (canvas_size - patch_size) // 2


def resolve_relative_axis(alignment: str, offset: float, canvas_size: int, patch_size: int) -> int:
    """对齐基准 + 偏移：偏移 ``0 ~ 1``（不含 1）按画布尺寸的百分比，其余按像素。"""
    return resolve_aligned_axis(alignment, canvas_size, patch_size) + resolve_axis(offset, canvas_size)


class ImageMergeRelativeNode:
    """图像合并(相对)。"""

    CATEGORY = "YTmmi/image"
    DESCRIPTION = (
        "图像合并(相对)：按水平对齐与垂直对齐把上层图像贴到底层图像上，"
        "可再叠加x、y偏移，偏移值0~1为底图百分比、其余为像素，可用遮罩给上层做蒙版"
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "图像0": ("IMAGE",),
                "图像1": ("IMAGE",),
                # 对齐方式先定基准，再由「偏移x / 偏移y」微调（可为负）
                "水平对齐": (HORIZONTAL_ALIGNMENTS, {"default": "居中"}),
                "垂直对齐": (VERTICAL_ALIGNMENTS, {"default": "居中"}),
                # 偏移保持 FLOAT：既能填 0~1 百分比小数，也能接整数像素
                "偏移x": ("FLOAT", {"default": 0.0, "min": -100000.0, "max": 100000.0, "step": 1.0}),
                "偏移y": ("FLOAT", {"default": 0.0, "min": -100000.0, "max": 100000.0, "step": 1.0}),
                "宽": ("INT", {"default": 0, "min": 0, "max": 100000, "step": 1}),
                "高": ("INT", {"default": 0, "min": 0, "max": 100000, "step": 1}),
                "图层顺序翻转": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                # 蒙版只作用于「在上面的图层」：遮罩为 1 显示上层、为 0 透出底层
                "遮罩": ("MASK",),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("图像",)
    FUNCTION = "merge"
    OUTPUT_NODE = False
    OUTPUT_IS_LIST = (False,)
    SEARCH_ALIASES = [
        "image merge relative",
        "align image",
        "paste image relative",
        "图像合并(相对)",
        "图像合并",
        "相对对齐",
        "对齐合并",
    ]

    def merge(self, **kwargs):
        if torch is None:
            raise RuntimeError("图像合并(相对)节点需要 torch 环境")

        image0 = kwargs.get("图像0")
        image1 = kwargs.get("图像1")
        if image0 is None or image1 is None:
            raise ValueError("图像合并(相对)需要同时连接「图像0」与「图像1」")

        horizontal = kwargs.get("水平对齐", "居中")
        vertical = kwargs.get("垂直对齐", "居中")
        offset_x = float(kwargs.get("偏移x", 0.0))
        offset_y = float(kwargs.get("偏移y", 0.0))
        out_w = int(kwargs.get("宽", 0))
        out_h = int(kwargs.get("高", 0))
        flip = bool(kwargs.get("图层顺序翻转", False))
        mask = kwargs.get("遮罩")

        batch0 = _as_image_batch(image0).float()
        batch1 = _as_image_batch(image1).float()
        batch_mask = None if mask is None else _as_mask_batch(mask).float()

        # 底层决定画布：默认图像0 在下，翻转后图像1 在下
        bottom, top = (batch1, batch0) if flip else (batch0, batch1)

        batch = max(bottom.shape[0], top.shape[0])
        if batch_mask is not None:
            batch = max(batch, batch_mask.shape[0])

        results = []
        for index in range(batch):
            canvas_chw = bottom[min(index, bottom.shape[0] - 1)].permute(2, 0, 1)
            patch_chw = top[min(index, top.shape[0] - 1)].permute(2, 0, 1)

            # 宽 / 高为 0 表示不限制（保持原尺寸），否则按指定尺寸拉伸
            patch_chw = _stretch(patch_chw, out_h, out_w)

            _, canvas_h, canvas_w = canvas_chw.shape
            _, patch_h, patch_w = patch_chw.shape

            # 对齐基准按「拉伸后」的上层尺寸计算，偏移再叠加在基准上
            x = resolve_relative_axis(horizontal, offset_x, canvas_w, patch_w)
            y = resolve_relative_axis(vertical, offset_y, canvas_h, patch_h)

            mask_hw = None
            if batch_mask is not None:
                mask_index = min(index, batch_mask.shape[0] - 1)
                # 蒙版跟随上层图层的最终尺寸（含拉伸），逐像素对齐
                mask_hw = _resize_mask(batch_mask[mask_index], patch_h, patch_w)

            results.append(_paste(canvas_chw, patch_chw, x, y, mask_hw).permute(1, 2, 0))

        return (torch.stack(results, dim=0),)


NODE_CLASS_MAPPINGS = {
    "ImageMergeRelativeNode": ImageMergeRelativeNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageMergeRelativeNode": "图像合并(相对)",
}

__all__ = [
    "ImageMergeRelativeNode",
    "HORIZONTAL_ALIGNMENTS",
    "VERTICAL_ALIGNMENTS",
    "resolve_aligned_axis",
    "resolve_relative_axis",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
