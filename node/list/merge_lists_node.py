# 合并列表
"""合并列表节点。

把多个列表按端口顺序首尾相接合并为一个列表：

- 输入端口 ``列表0`` ~ ``列表8``（最多 ``MAX_INPUTS`` 个）；
- 合并顺序严格等于端口顺序（``列表0`` 的元素在前，``列表1`` 的元素紧随其后……）；
- 未连接的端口被忽略，不影响其余端口的顺序；
- 元素保持原样（不做类型转换）。
"""

# 列表端口使用的类型名（本插件 6 个列表节点统一使用该类型，保证可互连）
LIST_TYPE = "LIST"

# 输入端口上限（前端 JS 需与此保持一致）
MAX_INPUTS = 9


def ensure_list(value):
    """把输入规整为列表：None → []，列表/元组 → list，其它标量 → 单元素列表。"""
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


class MergeListsNode:
    """把多个列表按端口顺序合并为一个列表。"""

    CATEGORY = "YTmmi/list"
    DESCRIPTION = "合并列表：把多个列表按端口顺序首尾相接合并为一个列表（最多 9 个），未连接的端口忽略"

    @classmethod
    def INPUT_TYPES(cls):
        optional = {}
        for i in range(MAX_INPUTS):
            # 与「视频拼接」一致，只声明 optional 分组
            optional[f"列表{i}"] = (LIST_TYPE,)
        return {"optional": optional}

    RETURN_TYPES = (LIST_TYPE,)
    RETURN_NAMES = ("列表",)
    FUNCTION = "merge_lists"
    OUTPUT_NODE = False
    OUTPUT_IS_LIST = (False,)
    SEARCH_ALIASES = [
        "merge lists",
        "concat lists",
        "合并列表",
        "列表拼接",
        "连接列表",
    ]

    def merge_lists(self, **kwargs):
        merged = []
        for i in range(MAX_INPUTS):
            key = f"列表{i}"
            if key not in kwargs:
                continue  # 未连接的端口：忽略
            value = kwargs.get(key)
            if value is None:
                continue
            merged.extend(ensure_list(value))
        return (merged,)


NODE_CLASS_MAPPINGS = {
    "MergeListsNode": MergeListsNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MergeListsNode": "合并列表",
}

__all__ = [
    "MergeListsNode",
    "ensure_list",
    "MAX_INPUTS",
    "LIST_TYPE",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
