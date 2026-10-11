# 获取列表信息
"""获取列表信息节点。

读取列表的统计信息并输出：

- ``元素数量``（INT）：列表长度；
- ``是否为空``（BOOLEAN）：长度是否为 0；
- ``首项`` / ``末项``（STRING）：第一个 / 最后一个元素，空列表时输出空字符串；
- ``列表文本``（STRING）：用「连接符」把所有元素拼成一段文本（默认 ``", "``）。

元素为 ``None`` 时按空字符串参与拼接与首末项输出。
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


class ListInfoNode:
    """输出列表的元素数量、是否为空、首项、末项与拼接文本。"""

    CATEGORY = "YTmmi/list"
    DESCRIPTION = "获取列表信息：输出元素数量、是否为空、首项、末项与按连接符拼接的列表文本"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "列表": (LIST_TYPE,),
            },
            "optional": {
                "连接符": ("STRING", {"default": ", ", "multiline": False}),
            },
        }

    RETURN_TYPES = ("INT", "BOOLEAN", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("元素数量", "是否为空", "首项", "末项", "列表文本")
    FUNCTION = "list_info"
    OUTPUT_NODE = False
    OUTPUT_IS_LIST = (False, False, False, False, False)
    SEARCH_ALIASES = [
        "list info",
        "list length",
        "获取列表信息",
        "列表长度",
        "列表元素数量",
    ]

    def list_info(self, **kwargs):
        items = ensure_list(kwargs.get("列表"))
        joiner = kwargs.get("连接符", ", ")
        joiner = "" if joiner is None else str(joiner)

        texts = [item_to_string(item) for item in items]
        count = len(texts)
        return (
            count,
            count == 0,
            texts[0] if texts else "",
            texts[-1] if texts else "",
            joiner.join(texts),
        )


NODE_CLASS_MAPPINGS = {
    "ListInfoNode": ListInfoNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ListInfoNode": "获取列表信息",
}

__all__ = [
    "ListInfoNode",
    "ensure_list",
    "item_to_string",
    "LIST_TYPE",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
