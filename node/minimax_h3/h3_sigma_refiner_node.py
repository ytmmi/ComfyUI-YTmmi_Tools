# H3 低噪细节精修
"""H3 低噪细节精修节点（H3 Sigma Refiner）。

移植自上游仓库 ComfyUI-YCNodes-MiniMax-H3（作者 亦诚，MIT 许可）的
`py/h3_sigma_refiner.py`，节点算法与原实现保持一致，仅按本项目规范调整了
注册键名（YTmmiH3SigmaRefiner）、分类（YTmmi/minimax-h3）、控件中文名与
DESCRIPTION，并补充了输入校验。

功能：
    对低噪点区间（低 Sigma 阶段）做局部「微雕」加步——保留原始调度的高噪
    头部不动，从起始阈值点起把尾部重采样成更长、更平滑的曲线，让模型在细节
    收尾阶段多走几步，消解高速运动边缘的马赛克与像素紊乱。

接线：
    BasicScheduler -> (sigmas) -> H3 低噪细节精修 -> (sigmas) -> SamplerCustomAdvanced
"""

import math

try:
    import torch  # type: ignore
except Exception:  # 缺少 torch 时降级，保证插件导入不失败
    torch = None

# 尾部插值分布曲线（控件选项，键为内部值，值为界面提示）
SPACING_OPTIONS = ["cosine", "linear", "exponential"]


class H3SigmaRefinerNode:
    """对低噪点区间（低 Sigma 阶段）局部加步，消除高速运动边缘的马赛克与像素紊乱。"""

    CATEGORY = "YTmmi/minimax-h3"
    DESCRIPTION = 'H3 低噪细节精修：在低噪点区（低 Sigma）局部加密采样步长，消解运动物体的边缘像素颗粒'

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "噪声序列": (
                    "SIGMAS",
                    {"tooltip": "输入的原始噪声序列（通常来自调度器 BasicScheduler）"},
                ),
                "额外步数": (
                    "INT",
                    {
                        "default": 1,
                        "min": 0,
                        "max": 15,
                        "step": 1,
                        "tooltip": "在低噪点区间额外增加的细节平滑步数，为 0 时原样返回",
                    },
                ),
                "起始Sigma": (
                    "FLOAT",
                    {
                        "default": 0.7,
                        "min": 0.0,
                        "max": 20.0,
                        "step": 0.01,
                        "tooltip": "启动细节加步的 Sigma 阈值，H3 推荐设在 2.0 ~ 3.5 之间",
                    },
                ),
                "结束Sigma": (
                    "FLOAT",
                    {
                        "default": 0.0,
                        "min": 0.0,
                        "max": 5.0,
                        "step": 0.01,
                        "tooltip": "结束细化的 Sigma 边界（默认 0.0）",
                    },
                ),
                "插值曲线": (
                    SPACING_OPTIONS,
                    {
                        "default": "cosine",
                        "tooltip": "尾部插值分布曲线：cosine 在趋近于 0 时分布更密，消噪最丝滑；"
                        "linear 均匀分布；exponential 能量前移、尾部大步走向末点",
                    },
                ),
            }
        }

    RETURN_TYPES = ("SIGMAS",)
    RETURN_NAMES = ("噪声序列",)
    FUNCTION = "refine_sigmas"
    OUTPUT_NODE = False
    OUTPUT_IS_LIST = (False,)
    SEARCH_ALIASES = [
        "H3 Sigma Refiner",
        "Sigma Refiner",
        "低噪细节精修",
        "sigma 加步",
        "minimax h3",
    ]

    def refine_sigmas(self, **kwargs):
        if torch is None:
            raise RuntimeError("H3 低噪细节精修：当前环境缺少 torch，无法处理 SIGMAS")

        sigmas = kwargs.get("噪声序列")
        extra_steps = int(kwargs.get("额外步数", 1))
        start_at_sigma = float(kwargs.get("起始Sigma", 0.7))
        end_at_sigma = float(kwargs.get("结束Sigma", 0.0))
        spacing = kwargs.get("插值曲线", "cosine")

        if sigmas is None:
            raise ValueError("H3 低噪细节精修：未接收到噪声序列（sigmas）输入")
        if not torch.is_tensor(sigmas):
            raise TypeError(
                f"H3 低噪细节精修：噪声序列必须是 torch.Tensor，实际为 {type(sigmas).__name__}"
            )
        if sigmas.numel() == 0:
            return (sigmas,)

        # 无需加步时原样返回，保持与上游实现一致
        if extra_steps <= 0:
            return (sigmas,)

        # 确保在 CPU 侧处理数值
        sigmas_cpu = sigmas.detach().cpu()

        # 寻找进入起始阈值的第一个索引位置
        idx = -1
        for i, s in enumerate(sigmas_cpu):
            if s <= start_at_sigma:
                idx = i
                break

        # 如果未达到阈值，或仅剩最后一步（0.0），无需处理
        if idx == -1 or idx >= len(sigmas_cpu) - 1:
            return (sigmas,)

        # 提取头部未修改序列与待精修的起始点
        unmodified_head = sigmas_cpu[:idx]
        start_value = sigmas_cpu[idx].item()
        end_value = max(end_at_sigma, sigmas_cpu[-1].item())

        original_tail_len = len(sigmas_cpu) - idx
        new_tail_len = original_tail_len + extra_steps

        # 1D 插值因子映射 [0.0, 1.0]
        t = torch.linspace(0.0, 1.0, steps=new_tail_len)

        if spacing == "cosine":
            factor = (1.0 - torch.cos(t * math.pi)) / 2.0
        elif spacing == "exponential":
            alpha = 3.0
            factor = (torch.exp(t * alpha) - 1.0) / (math.exp(alpha) - 1.0)
        else:  # linear（未知取值同样按线性处理，避免执行中断）
            factor = t

        # 根据对应曲线计算出新的高密度平滑尾端
        new_tail = start_value + (end_value - start_value) * factor

        # 如果原始序列最末端是 0.0 且终点值大于 0.0，需要保留最终的绝对收敛点 0.0
        if sigmas_cpu[-1].item() == 0.0 and end_value > 0.0:
            new_tail = torch.cat(
                [new_tail, torch.zeros(1, dtype=new_tail.dtype, device=new_tail.device)]
            )

        # 拼接头部与精修尾部
        new_sigmas = torch.cat([unmodified_head, new_tail])

        return (new_sigmas.to(device=sigmas.device, dtype=sigmas.dtype),)


NODE_CLASS_MAPPINGS = {
    "YTmmiH3SigmaRefiner": H3SigmaRefinerNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "YTmmiH3SigmaRefiner": "H3 低噪细节精修",
}

__all__ = [
    "H3SigmaRefinerNode",
    "SPACING_OPTIONS",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
