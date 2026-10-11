# 列表分离字符串
"""列表分离字符串节点。

把列表的每一项按序号输出到对应端口（第 0 项 → ``字符串0``，第 1 项 → ``字符串1`` ……）：

- 最多输出 ``MAX_OUTPUTS``（20）项，**列表超出 20 项的部分不处理**（丢弃）；
- 列表不足 20 项时，多余端口输出**空字符串**（ComfyUI 要求所有声明的输出都必须返回）；
- 非字符串元素会被转为字符串，``None`` 元素输出空字符串；
- 执行时通过 ``ui`` 回传实际项数，前端据此只显示用得到的输出端口（按需显示）。
"""

# 列表端口使用的类型名（本插件 6 个列表节点统一使用该类型，保证可互连）
LIST_TYPE = "LIST"

# 输出端口上限（前端 JS 需与此保持一致）
MAX_OUTPUTS = 20


def ensure_list(value):
    """把输入规整为列表：None → []，列表/元组 → list，其它标量 → 单元素列表。"""
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def item_to_string(item):
    """把列表元素转为字符串，None 输出空字符串（避免出现 "None" 文本）。"""
    return "" if item is None else str(item)


class ListSplitStringsNode:
    """把列表每一项按序号输出到对应字符串端口。"""

    CATEGORY = "YTmmi/list"
    DESCRIPTION = "列表分离字符串：把列表每一项按序号输出到对应端口（最多 20 项），超出部分不处理，未使用的端口输出空字符串"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "列表": (LIST_TYPE,),
            }
        }

    RETURN_TYPES = ("STRING",) * MAX_OUTPUTS
    RETURN_NAMES = tuple(f"字符串{i}" for i in range(MAX_OUTPUTS))
    FUNCTION = "split_list"
    OUTPUT_NODE = False
    OUTPUT_IS_LIST = (False,) * MAX_OUTPUTS
    SEARCH_ALIASES = [
        "list to strings",
        "split list",
        "列表分离字符串",
        "列表转字符串",
        "展开列表",
    ]

    def split_list(self, **kwargs):
        items = ensure_list(kwargs.get("列表"))
        outputs = [
            item_to_string(items[i]) if i < len(items) else ""
            for i in range(MAX_OUTPUTS)
        ]
        # ui 回传实际项数：前端据此按需显示输出端口（超出 20 的部分已不处理）
        return {
            "ui": {"数量": [min(len(items), MAX_OUTPUTS)]},
            "result": tuple(outputs),
        }


NODE_CLASS_MAPPINGS = {
    "ListSplitStringsNode": ListSplitStringsNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ListSplitStringsNode": "列表分离字符串",
}

__all__ = [
    "ListSplitStringsNode",
    "ensure_list",
    "item_to_string",
    "MAX_OUTPUTS",
    "LIST_TYPE",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
