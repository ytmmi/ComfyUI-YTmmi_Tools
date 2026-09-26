# 展示文本（多重）
"""展示文本（多重）节点。

展示 0~8 号输入口传来的文本类信息（字符串、数字、布尔、JSON 结构等），
对非文本类型进行过滤，不展示其内容：
- torch.Tensor（图像 / 视频帧 / 蒙版等）→ 过滤
- LATENT（含 samples 键的字典）→ 过滤
- AUDIO（含 waveform / sample_rate 键的字典）→ 过滤

输入使用通配类型 "*"，允许连接任意类型的输出端口。
同时连接 2 个及以上输入口时，展示内容按输入口序号（0 起始）分隔标注，
例如：

【输入0】
内容一

────── 输入1 ──────

内容二

前端默认只显示「输入0」，连接后自动显现下一个输入口，最多 9 个
（输入0 ~ 输入8，与 MAX_INPUTS 一致）。
"""

import json

import torch

# 输入口总数：输入0 ~ 输入8，前端 JS 按此值同步动态端口
MAX_INPUTS = 9


class DisplayTextNode:
    """展示从 0~8 号输入口获取的字符串信息，过滤音频、潜空间、视频等非文本类型。"""

    CATEGORY = "YTmmi/utility"
    DESCRIPTION = '展示文本（多重）：展示上游节点 0~8 号输入口的字符串信息（数字、字符串、文本、JSON 等），多输入自动按输入口序号分隔标注；音频、潜空间、视频等类型自动过滤不展示'

    @classmethod
    def INPUT_TYPES(cls):
        optional = {}
        for i in range(MAX_INPUTS):
            optional[f"输入{i}"] = ("*",)
        return {
            "required": {
                "文本": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "placeholder": "展示结果将显示在这里",
                    },
                ),
            },
            "optional": optional,
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("文本",)
    FUNCTION = "show"
    OUTPUT_NODE = True
    OUTPUT_IS_LIST = (False,)
    SEARCH_ALIASES = ["show text", "display text", "文本显示", "展示文本", "多重文本", "文本合并展示"]

    def show(self, **kwargs):
        parts = []
        for i in range(MAX_INPUTS):
            value = kwargs.get(f"输入{i}")
            if value is None:
                continue
            parts.append((i, self._to_display_text(value)))

        if not parts:
            display_text = ""
        elif len(parts) == 1:
            display_text = parts[0][1]
        else:
            blocks = []
            for idx, text in parts:
                if idx == 0:
                    blocks.append(f"【输入{idx}】\n{text}")
                else:
                    blocks.append(f"────── 输入{idx} ──────\n\n{text}")
            display_text = "\n\n".join(blocks)
        return {"ui": {"文本": [display_text]}, "result": (display_text,)}

    @staticmethod
    def _to_display_text(value):
        """将输入值转换为展示文本；非文本类型返回过滤提示。"""
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        if isinstance(value, bool):
            return "True" if value else "False"
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, torch.Tensor):
            return "[不展示] 张量数据（图像 / 视频帧 / 蒙版等）"
        if isinstance(value, dict):
            if "samples" in value:
                return "[不展示] 潜空间数据 (LATENT)"
            if "waveform" in value or "sample_rate" in value:
                return "[不展示] 音频数据 (AUDIO)"
            if DisplayTextNode._contains_tensor(value):
                return "[不展示] 包含张量数据"
            try:
                return json.dumps(value, ensure_ascii=False, indent=2)
            except TypeError:
                return str(value)
        if isinstance(value, (list, tuple)):
            if DisplayTextNode._contains_tensor(value):
                return "[不展示] 包含张量数据"
            try:
                return json.dumps(list(value), ensure_ascii=False, indent=2)
            except TypeError:
                return str(value)
        return str(value)

    @staticmethod
    def _contains_tensor(value):
        """递归检查数据结构中是否包含 torch.Tensor。"""
        if isinstance(value, torch.Tensor):
            return True
        if isinstance(value, (list, tuple)):
            return any(DisplayTextNode._contains_tensor(v) for v in value)
        if isinstance(value, dict):
            return any(DisplayTextNode._contains_tensor(v) for v in value.values())
        return False


NODE_CLASS_MAPPINGS = {
    "DisplayTextNode": DisplayTextNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DisplayTextNode": "展示文本（多重）",
}

__all__ = [
    "DisplayTextNode",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
