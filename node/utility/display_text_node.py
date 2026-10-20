# 展示文本（多重）
"""展示文本（多重）节点。

展示 0~8 号输入口传来的文本类信息（字符串、数字、布尔、JSON 结构等），
对非文本类型进行过滤，不展示其内容：
- torch.Tensor（图像 / 视频帧 / 蒙版等）→ 过滤
- LATENT（含 samples 键的字典）→ 过滤
- AUDIO（含 waveform / sample_rate 键的字典）→ 过滤

输入使用通配类型 "*"，允许连接任意类型的输出端口。
同时连接 2 个及以上输入口时，展示内容按输入口序号（0 起始）分隔标注，
所有输入口使用同一种分隔格式，例如：

────── 输入0 ──────

内容一

────── 输入1 ──────

内容二

前端默认只显示「输入0」，连接后自动显现下一个输入口，最多 9 个
（输入0 ~ 输入8，与 MAX_INPUTS 一致）。

展示文本嵌入工作流数据：
参考 ComfyUI-Easy-Use 的「展示任何」(easy showAnything) 节点，本节点在执行时
通过隐藏输入 unique_id / extra_pnginfo 拿到本次运行的工作流快照，并按节点 id
把展示文本写回该节点，使展示结果随工作流数据一起保留（而不是只存在于浏览器内存）。
"""

import json

import torch

# 输入口总数：输入0 ~ 输入8，前端 JS 按此值同步动态端口
MAX_INPUTS = 9

# 展示控件名：既用于 INPUT_TYPES 的展示控件，也用于回写工作流数据时的字段名
DISPLAY_WIDGET_NAME = "文本"


class DisplayTextNode:
    """展示从 0~8 号输入口获取的字符串信息，过滤音频、潜空间、视频等非文本类型。"""

    CATEGORY = "YTmmi/utility"
    DESCRIPTION = '展示文本（多重）：展示上游节点 0~8 号输入口的字符串信息（数字、字符串、文本、JSON 等），多输入自动按输入口序号分隔标注；音频、潜空间、视频等类型自动过滤不展示'

    @classmethod
    def INPUT_TYPES(cls):
        optional = {
            # 「文本」为展示控件（执行后回填结果）。放在 optional 可避免新版前端把
            # required STRING 转成可连接端口后，未连接时执行报 "Missing connection"。
            DISPLAY_WIDGET_NAME: (
                "STRING",
                {
                    "default": "",
                    "multiline": True,
                    "placeholder": "展示结果将显示在这里",
                },
            ),
        }
        for i in range(MAX_INPUTS):
            optional[f"输入{i}"] = ("*",)
        return {
            "required": {},
            "optional": optional,
            # 隐藏输入：由 ComfyUI 在执行时注入，不占用前端端口。
            # unique_id 用于定位当前节点，extra_pnginfo 是本次运行的工作流快照。
            "hidden": {
                "unique_id": "UNIQUE_ID",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
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
            text = self._to_display_text(value)
            # 已连接但内容为空：给出可见标记，避免与「未连接」无法区分
            # （上游节点空输出时，这里若显示空白会让人误以为节点没执行）
            if not str(text).strip():
                text = self._empty_placeholder(i)
            parts.append((i, text))

        if not parts:
            display_text = ""
        elif len(parts) == 1:
            display_text = parts[0][1]
        else:
            # 多输入统一用同一种分隔格式（输入0 不再使用「【输入0】」）
            blocks = [
                f"────── 输入{idx} ──────\n\n{text}" for idx, text in parts
            ]
            display_text = "\n\n".join(blocks)

        # 把展示文本写回本次运行的工作流快照，使其随工作流数据一起保留
        self._embed_display_text(
            kwargs.get("extra_pnginfo"),
            kwargs.get("unique_id"),
            display_text,
        )
        return {
            "ui": {DISPLAY_WIDGET_NAME: [display_text]},
            "result": (display_text,),
        }

    @staticmethod
    def _embed_display_text(extra_pnginfo, unique_id, display_text):
        """将展示文本写入工作流快照中本节点的 widgets_values。

        参考 ComfyUI-Easy-Use 的「展示任何」(easy showAnything)：ComfyUI 在执行
        节点时通过隐藏输入注入本次运行的工作流快照 (extra_pnginfo) 与节点 id
        (unique_id)，节点据此把结果写回自己的工作流节点，使展示文本成为工作流
        数据的一部分（历史记录、输出图片元数据、由 PNG 载入的工作流）。

        返回是否成功写入；任何结构不符合预期的情况都安静跳过，不影响节点执行。
        """
        if not isinstance(extra_pnginfo, dict):
            return False
        workflow = extra_pnginfo.get("workflow")
        if not isinstance(workflow, dict):
            return False
        nodes = workflow.get("nodes")
        if not isinstance(nodes, list):
            return False

        # unique_id 可能被包成单元素列表（取决于执行器传入形式）
        node_id = unique_id[0] if isinstance(unique_id, (list, tuple)) and unique_id else unique_id
        if node_id is None:
            return False

        target = next(
            (
                node
                for node in nodes
                if isinstance(node, dict) and str(node.get("id")) == str(node_id)
            ),
            None,
        )
        if target is None:
            return False

        # 「文本」是本节点唯一可序列化控件，位于 widgets_values 首位；
        # 保留其余位置，避免后续新增控件时被覆盖
        widgets_values = target.get("widgets_values")
        if isinstance(widgets_values, list) and widgets_values:
            widgets_values[0] = display_text
        else:
            target["widgets_values"] = [display_text]
        # 新版前端在启用按名恢复时会读取 widgets_values_named，存在则同步更新
        named = target.get("widgets_values_named")
        if isinstance(named, dict):
            named[DISPLAY_WIDGET_NAME] = display_text
        return True

    @staticmethod
    def _empty_placeholder(index):
        """已连接输入口的空内容占位提示。"""
        return (
            f"[空文本] 输入{index} 已连接，但上游输出为空字符串。\n"
            "请检查上游节点：常见原因是生成被截断（调大最大token数）、"
            "接口返回内容为空或提示词未产生有效输出。"
        )

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
