# 分离字符串到列表
"""分离字符串到列表节点。

按自定义分隔符把输入字符串切分为列表：

- 关闭「保留分隔符」（默认）：等价 Python 的 ``str.split``，分隔符被丢弃，
  例如 ``111---222---333`` → ``['111', '222', '333']``；
- 打开「保留分隔符」：分隔符被保留并置于**后一项的开头**，
  例如 ``111---222---333`` → ``['111', '---222', '---333']``；
- 分隔符为空串时退化为按空白切分（等价 ``str.split()``，会去掉首尾空白）。

切分使用**字面量**分隔符（不做正则解析），因此 ``.`` ``|`` ``*`` ``(`` 等字符无需转义。
空字段按 Python 语义保留，例如 ``a------b`` 按 ``---`` 切分为 ``['a', '', 'b']``。
"""

# 列表端口使用的类型名（本插件 6 个列表节点统一使用该类型，保证可互连）
LIST_TYPE = "LIST"


def split_text_to_list(text, separator, keep_separator=False):
    """把 text 按 separator 切分为字符串列表（字面量切分，非正则）。

    Args:
        text: 待切分的字符串，None 视为空串。
        separator: 分隔符字面量，None 视为空串（空串 → 按空白切分）。
        keep_separator: 为 True 时保留分隔符，并置于后一项开头。

    Returns:
        list[str]: 切分结果。
    """
    text = "" if text is None else str(text)
    separator = "" if separator is None else str(separator)

    if separator == "":
        # 空分隔符无意义：退化为按空白切分，避免 str.split("") 抛 ValueError
        return text.split()

    parts = text.split(separator)
    if not keep_separator:
        return parts

    # 保留分隔符：分隔符跟在上一项之后、置于下一项之前（如 ---222）
    return [parts[0]] + [separator + part for part in parts[1:]]


class SplitStringNode:
    """按自定义分隔符把字符串切分为列表。"""

    CATEGORY = "YTmmi/list"
    DESCRIPTION = "分离字符串到列表：按自定义分隔符把输入字符串切分为列表，可保留分隔符（保留时分隔符置于后一项开头，如 ---222）"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "字符串": ("STRING", {"default": "", "multiline": False}),
                "分隔符": ("STRING", {"default": ",", "multiline": False}),
                "保留分隔符": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = (LIST_TYPE,)
    RETURN_NAMES = ("列表",)
    FUNCTION = "split_string"
    OUTPUT_NODE = False
    OUTPUT_IS_LIST = (False,)
    SEARCH_ALIASES = [
        "split string",
        "separate string",
        "string to list",
        "分离字符串到列表",
        "分离字符串",
        "切分字符串",
        "分隔符",
    ]

    def split_string(self, **kwargs):
        text = kwargs.get("字符串", "")
        separator = kwargs.get("分隔符", ",")
        keep_separator = bool(kwargs.get("保留分隔符", False))
        return (split_text_to_list(text, separator, keep_separator),)


NODE_CLASS_MAPPINGS = {
    "SplitStringNode": SplitStringNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SplitStringNode": "分离字符串到列表",
}

__all__ = [
    "SplitStringNode",
    "split_text_to_list",
    "LIST_TYPE",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
