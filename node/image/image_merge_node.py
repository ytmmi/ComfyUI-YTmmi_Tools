# 图像合并
"""图像合并：把一张图像按坐标贴到另一张图像（画布）上，用于还原「遮罩裁剪图像」的裁剪结果。

画布取**处于底层的那张图**：默认「图像0」在下、「图像1」在上，因此画布 = 图像0；
打开「图层顺序翻转」后「图像1」在下，画布 = 图像1。处于上层的那张图按「坐标x / 坐标y」
贴到画布上，超出画布的部分会被裁掉，画布不会因此变大。
"""

try:
    import torch  # type: ignore
    import torch.nn.functional as F  # type: ignore
except Exception:  # pragma: no cover - 可选依赖降级，避免导入失败
    torch = None
    F = None


def resolve_axis(value: float, canvas_size: int) -> int:
    """坐标换算：0 ~ 1（不含 1）按画布尺寸的百分比，其余按像素。"""
    value = float(value)
    if 0.0 <= value < 1.0:
        return int(round(value * canvas_size))
    return int(round(value))


def _as_image_batch(image):
    """把 IMAGE 规整为 [B, H, W, C]。"""
    tensor = image
    if tensor.ndim == 3:
        tensor = tensor.unsqueeze(0)
    elif tensor.ndim == 2:
        tensor = tensor.unsqueeze(0).unsqueeze(-1)
    return tensor


def _stretch(chw, out_h: int, out_w: int):
    """把 [C,H,W] 拉伸到指定宽高（宽高为 0 时表示该方向不限制）。"""
    _, height, width = chw.shape
    target_h = out_h if out_h > 0 else height
    target_w = out_w if out_w > 0 else width
    if target_h == height and target_w == width:
        return chw
    return F.interpolate(
        chw.unsqueeze(0),
        size=(max(1, target_h), max(1, target_w)),
        mode="bilinear",
        align_corners=False,
        antialias=True,
    ).squeeze(0)


def _split_alpha(chw):
    """把 [C,H,W] 拆成 (RGB 三通道, alpha 或 None)，兼容 1 / 3 / 4 通道。"""
    channels = chw.shape[0]
    if channels == 1:
        return chw.expand(3, -1, -1), None
    if channels == 3:
        return chw, None
    return chw[:3], chw[3:4]


def _paste(canvas_chw, patch_chw, x: int, y: int):
    """把 patch 贴到 canvas 的 (x, y) 处，超出画布的部分裁掉。"""
    _, canvas_h, canvas_w = canvas_chw.shape
    _, patch_h, patch_w = patch_chw.shape

    # 画布上的目标矩形与 patch 上的源矩形取交集
    dst_x0 = max(0, x)
    dst_y0 = max(0, y)
    dst_x1 = min(canvas_w, x + patch_w)
    dst_y1 = min(canvas_h, y + patch_h)
    if dst_x1 <= dst_x0 or dst_y1 <= dst_y0:
        return canvas_chw  # 完全在画布外，原样返回

    src_x0 = dst_x0 - x
    src_y0 = dst_y0 - y
    src_x1 = src_x0 + (dst_x1 - dst_x0)
    src_y1 = src_y0 + (dst_y1 - dst_y0)

    patch_region = patch_chw[:, src_y0:src_y1, src_x0:src_x1]
    canvas_region = canvas_chw[:, dst_y0:dst_y1, dst_x0:dst_x1]

    # 统一按 RGB(+可选 alpha) 处理，再按画布原本的通道数还原
    patch_rgb, patch_alpha = _split_alpha(patch_region)
    canvas_rgb, _ = _split_alpha(canvas_region)

    if patch_alpha is None:
        blended = patch_rgb
    else:
        # 带 alpha 的上层与下层混合
        blended = patch_rgb * patch_alpha + canvas_rgb * (1.0 - patch_alpha)

    canvas_channels = canvas_region.shape[0]
    if canvas_channels == 1:
        canvas_region = blended.mean(dim=0, keepdim=True)
    elif canvas_channels == 3:
        canvas_region = blended
    else:
        # 画布带 alpha：保留画布自身的 alpha 通道
        canvas_region = torch.cat([blended, canvas_region[3:4]], dim=0)

    canvas_chw = canvas_chw.clone()
    canvas_chw[:, dst_y0:dst_y1, dst_x0:dst_x1] = canvas_region
    return canvas_chw


class ImageMergeNode:
    """图像合并。"""

    CATEGORY = "YTmmi/image"
    DESCRIPTION = "图像合并：把上层图像按坐标x、坐标y贴到底层图像上，用于还原遮罩裁剪图像的结果"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "图像0": ("IMAGE",),
                "图像1": ("IMAGE",),
                # 坐标保持 FLOAT：既能填 0~1 百分比小数，也能接「遮罩裁剪图像」
                # 的坐标输出（该输出声明为 INT,FLOAT 联合类型，含 FLOAT 故可连）
                "坐标x": ("FLOAT", {"default": 0.0, "min": -100000.0, "max": 100000.0, "step": 1.0}),
                "坐标y": ("FLOAT", {"default": 0.0, "min": -100000.0, "max": 100000.0, "step": 1.0}),
                "宽": ("INT", {"default": 0, "min": 0, "max": 100000, "step": 1}),
                "高": ("INT", {"default": 0, "min": 0, "max": 100000, "step": 1}),
                "图层顺序翻转": ("BOOLEAN", {"default": False}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("图像",)
    FUNCTION = "merge"
    OUTPUT_NODE = False
    OUTPUT_IS_LIST = (False,)
    SEARCH_ALIASES = ["image merge", "paste image", "uncrop", "图像合并", "图像拼接"]

    def merge(self, **kwargs):
        if torch is None:
            raise RuntimeError("图像合并节点需要 torch 环境")

        image0 = kwargs.get("图像0")
        image1 = kwargs.get("图像1")
        if image0 is None or image1 is None:
            raise ValueError("图像合并需要同时连接「图像0」与「图像1」")

        coord_x = float(kwargs.get("坐标x", 0.0))
        coord_y = float(kwargs.get("坐标y", 0.0))
        out_w = int(kwargs.get("宽", 0))
        out_h = int(kwargs.get("高", 0))
        flip = bool(kwargs.get("图层顺序翻转", False))

        batch0 = _as_image_batch(image0).float()
        batch1 = _as_image_batch(image1).float()

        # 底层决定画布：默认图像0 在下，翻转后图像1 在下
        bottom, top = (batch1, batch0) if flip else (batch0, batch1)

        batch = max(bottom.shape[0], top.shape[0])
        results = []
        for index in range(batch):
            canvas_chw = bottom[min(index, bottom.shape[0] - 1)].permute(2, 0, 1)
            patch_chw = top[min(index, top.shape[0] - 1)].permute(2, 0, 1)

            _, canvas_h, canvas_w = canvas_chw.shape
            x = resolve_axis(coord_x, canvas_w)
            y = resolve_axis(coord_y, canvas_h)

            # 宽 / 高为 0 表示不限制（保持原尺寸），否则按指定尺寸拉伸
            patch_chw = _stretch(patch_chw, out_h, out_w)
            results.append(_paste(canvas_chw, patch_chw, x, y).permute(1, 2, 0))

        return (torch.stack(results, dim=0),)


NODE_CLASS_MAPPINGS = {
    "ImageMergeNode": ImageMergeNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageMergeNode": "图像合并",
}

__all__ = [
    "ImageMergeNode",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
