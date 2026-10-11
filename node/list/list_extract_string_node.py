# 列表提取字符串
"""列表提取字符串节点。

按位置（**从 0 开始**）取出列表中的某一项并转为字符串：

- 位置支持负数（``-1`` 表示最后一项、``-2`` 表示倒数第二项），与 Python 索引一致；
- 列表为空、或位置越界时抛出带中文说明的错误，便于在工作流中定位问题；
- 元素为 ``None`` 时输出空字符串，其它类型自动转为字符串。
"""

# 列表端口使用的类型名（本插件 6 个列表节点统一使用该类型，保证可互连）
LIST_TYPE = "LIST"


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


class ListExtractStringNode:
    """按位置从列表中取出某一项并输出为字符串。"""

    CATEGORY = "YTmmi/list"
    DESCRIPTION = "列表提取字符串：按位置（从 0 开始，支持负数从末尾取值）取出列表中的某一项并输出为字符串"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "列表": (LIST_TYPE,),
                "位置": ("INT", {"default": 0, "min": -9999, "max": 9999, "step": 1}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("字符串",)
    FUNCTION = "extract_string"
    OUTPUT_NODE = False
    OUTPUT_IS_LIST = (False,)
    SEARCH_ALIASES = [
        "list extract",
        "list item",
        "列表提取字符串",
        "提取列表项",
        "取列表元素",
    ]

    def extract_string(self, **kwargs):
        items = ensure_list(kwargs.get("列表"))
        raw_index = kwargs.get("位置", 0)
        index = int(raw_index) if raw_index is not None else 0

        if not items:
            raise ValueError("列表提取字符串：输入列表为空，没有可提取的项")

        # 负数按 Python 语义从末尾取值
        resolved = index + len(items) if index < 0 else index
        if resolved < 0 or resolved >= len(items):
            raise ValueError(
                f"列表提取字符串：位置 {index} 超出范围，"
                f"列表共 {len(items)} 项（可用 0 ~ {len(items) - 1}，或 -1 ~ -{len(items)}）"
            )

        return (item_to_string(items[resolved]),)


NODE_CLASS_MAPPINGS = {
    "ListExtractStringNode": ListExtractStringNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ListExtractStringNode": "列表提取字符串",
}

__all__ = [
    "ListExtractStringNode",
    "ensure_list",
    "item_to_string",
    "LIST_TYPE",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
