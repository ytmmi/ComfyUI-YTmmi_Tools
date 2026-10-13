# 字符串到列表
"""字符串到列表节点。

把多个字符串输入按端口顺序合并为一个列表：

- 输入端口 ``字符串0`` ~ ``字符串19``（最多 ``MAX_INPUTS`` 个），前端按需显示
  （连接末尾端口后自动追加下一个端口）；
- 只收集**已连接**的端口，未连接的端口被忽略，因此列表顺序严格等于端口顺序；
- 已连接但内容为空串的端口会作为一个空字符串元素保留（与「未连接」区分）。
"""

# 列表端口使用的类型名（本插件 6 个列表节点统一使用该类型，保证可互连）
LIST_TYPE = "LIST"

# 输入端口上限（前端 JS 需与此保持一致）
MAX_INPUTS = 20


class StringsToListNode:
    """把多个字符串输入按端口顺序合并为列表。"""

    CATEGORY = "YTmmi/list"
    DESCRIPTION = "字符串到列表：把多个字符串输入按端口顺序合并为列表（最多 20 个，按需显示），未连接的端口忽略"

    @classmethod
    def INPUT_TYPES(cls):
        optional = {}
        for i in range(MAX_INPUTS):
            # forceInput：始终作为输入端口（不生成文本框控件），未连接时不在 kwargs 中。
            # 与「视频拼接」一致，只声明 optional 分组。
            optional[f"字符串{i}"] = ("STRING", {"forceInput": True})
        return {"optional": optional}

    RETURN_TYPES = (LIST_TYPE,)
    RETURN_NAMES = ("列表",)
    FUNCTION = "strings_to_list"
    OUTPUT_NODE = False
    OUTPUT_IS_LIST = (False,)
    SEARCH_ALIASES = [
        "strings to list",
        "join strings",
        "字符串到列表",
        "字符串转列表",
        "多字符串合并",
    ]

    def strings_to_list(self, **kwargs):
        values = []
        for i in range(MAX_INPUTS):
            key = f"字符串{i}"
            if key not in kwargs:
                continue  # 未连接的端口：忽略
            value = kwargs.get(key)
            if value is None:
                continue
            values.append(str(value))
        return (values,)


NODE_CLASS_MAPPINGS = {
    "StringsToListNode": StringsToListNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "StringsToListNode": "字符串到列表",
}

__all__ = [
    "StringsToListNode",
    "MAX_INPUTS",
    "LIST_TYPE",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
