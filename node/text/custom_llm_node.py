# 自定义LLM
"""自定义LLM节点。

调用任意 OpenAI 兼容格式的在线大模型接口（如 OpenAI、DeepSeek、通义千问、
Kimi、本地 vLLM/Ollama 等），传入系统提示词与用户提示词，返回模型生成的文本。

请求格式为 OpenAI /chat/completions 规范：
    POST {base_url}/chat/completions
    Authorization: Bearer {api_key}

模型选择：
- model 为下拉菜单，可点击节点上的「获取模型」按钮，从接口
  GET {base_url}/models 拉取可用模型列表并填充下拉选项；
- 后端提供 POST /ytmmi/llm/models 路由完成模型列表拉取。

输入说明：
- api_key：接口密钥
- base_url：接口地址（OpenAI 格式，如 https://api.openai.com/v1）
- model：模型名称（下拉选择，可点击「获取模型」刷新）
- skills：skills 指导文本（可选，字符串端口）。接入「skills管理器」节点的 skills 输出，
  或任意文本源（如手写 skills 内容）；接入后作为系统消息的一部分发送给模型
- system_prompt：系统提示词（可选）
- prompt：用户提示词（要求、问题等）
- temperature：采样温度（0~2）
- max_tokens：生成的最大 token 数
- top_p：核采样（可选，默认 1.0）
- seed：随机种子（可选，-1 表示不设置，由服务端随机）。
  该输入带官方 control_after_generate 标记，前端会自动在「种子」旁生成「生成后控制」
  下拉（固定值/递增值/递减值/随机值），纯客户端控制种子的变化，详见下方说明
- 图片0~图片8：可选图像输入（IMAGE 类型，最多 9 张）。前端默认只显示「图片0」，
  连接后自动显现下一张；接入图片后，用户消息按 OpenAI 多模态格式发送（content 为
  数组，图片编码为 JPEG base64 data URL），兼容 DeepSeek V4.1 Flash（模型 id：
  deepseek-flash）等支持视觉输入的模型。

完整请求参数（均为可选，默认值保持「不发送」以兼容只实现部分字段的中转接口）：
- 输出格式（response_format）：text（默认，不发送）/ json_object
- 频率惩罚 / 存在惩罚（frequency_penalty / presence_penalty）：-2~2，0 不发送
- 候选数量（n）：1~10，1 不发送（节点只取第 1 个候选作为输出）
- top_k：0~200，0 不发送（非 OpenAI 官方字段，部分接口支持）
- 推理强度（reasoning_effort）：空 / low / medium / high，空不发送
- 超时秒数：默认 120；空输出重试次数：默认 2（仅 finish_reason 正常结束时重试）

多轮会话（默认关闭，节点后台维护）：
- 启用多轮对话：BOOLEAN，默认 False。开启后节点自动把本节点此前的对话轮次
  （用户提示词 + 最终回复）拼到本轮之前，**不需要手工填写历史对话**
- 最大会话轮数：0 = 不限制；大于 0 时，达到该轮数后下一轮自动开新会话
- 关闭再开启「启用多轮对话」、或 ComfyUI 重启，都会自动开新会话；
  一个节点只维护一个会话（一份上下文），会话保存在进程内存中
- 历史里只保留纯文本轮次（图片只随当前轮发送，不进入历史）

工具调用（内置工具，后台声明、自动执行）：
- 节点内置 `read_skill` 工具（读取 skills 目录中的文件），在 skills 自动清单
  （多轮按需读取）时自动随请求声明 tools + tool_choice=auto，无需人工配置
- 模型返回 tool_calls 时，节点自动执行内置工具并把结果作为 tool 消息回注，
  继续下一轮；等价于 READ: 文本协议，但走 OpenAI 原生函数调用通道
- 未知工具名不会被执行，只回注一条错误说明；节点**绝不执行任意代码**
- 能力约束：只有 skills 输入确实是 skills管理器 的「自动」清单（带自动标记且
  至少解析出 1 个 skills 名称）时才声明工具、进入多轮读取；且无论走原生
  tool_calls 还是 READ: 文本协议，都只能读取**本次清单内**的 skills，清单外的
  skills 一律拒绝——因此必须由 skills管理器 节点提供 skills 输入

生成后控制（control_after_generate）：
「种子」使用 ComfyUI 官方的 control_after_generate 机制（与 KSampler 等节点完全
一致），**仅控制种子本身**，节点后端不参与：

- 后端只在「种子」输入上声明 ``"control_after_generate": True``；
- 前端据此自动生成配套的「生成后控制」下拉（固定值/递增值/递减值/随机值），
  该下拉 ``serialize: false``，**不会出现在发给后端的 prompt 里**；
- 生成结束后由前端在本地按所选模式改写「种子」控件值（下一次执行即用新种子），
  因此节点无需状态缓存、无需回填 ui、也无需 IS_CHANGED。

输出：
- 输出文本：模型返回的文本字符串；
- 简略上下文：本次运行轨迹的纯文本记录（步数、输入的 skills 名称、实际读取的
  skills、每一步的思考与动作、最终输出，以及接口返回 usage 时的「用量统计」：
  输入/输出/合计 token、接口耗时、输出速度、工具调用数）。该文本**完全由节点代码
  拼装，不调用模型做任何总结**，便于事后核对「跑了几步、读了哪些 skills、最终产出了什么」。
"""

import base64
import io
import json
import re
import threading
import time
from dataclasses import dataclass, field

import torch

try:
    from PIL import Image
except Exception:
    Image = None

try:
    import requests
except Exception:
    requests = None

try:
    from server import PromptServer
    import aiohttp
    from aiohttp import web
except Exception:
    PromptServer = None
    aiohttp = None
    web = None

# 复用密钥储存器的密钥库读取能力（多级导入兜底，兼容不同加载方式）：
# - 包内相对导入（ComfyUI 以插件包方式加载）
# - node.utility 绝对导入（根目录在 sys.path 时）
# - 直接模块导入（测试环境）
try:
    from ..utility.key_storage_node import vault_names, load_vault
except Exception:
    try:
        from node.utility.key_storage_node import vault_names, load_vault
    except Exception:
        try:
            from key_storage_node import vault_names, load_vault
        except Exception:
            vault_names = None
            load_vault = None

# 复用 skills管理器的按需读取能力（渐进式披露），同样做多级导入兜底
try:
    from ..utility.skills_manager_node import (
        is_auto_skills_text,
        read_skill_file,
        skill_files,
        skill_names,
    )
except Exception:
    try:
        from node.utility.skills_manager_node import (
            is_auto_skills_text,
            read_skill_file,
            skill_files,
            skill_names,
        )
    except Exception:
        try:
            from skills_manager_node import (
                is_auto_skills_text,
                read_skill_file,
                skill_files,
                skill_names,
            )
        except Exception:
            is_auto_skills_text = None
            read_skill_file = None
            skill_files = None
            skill_names = None

# 预设模型列表：默认不预设（空），模型列表完全由「获取模型」按钮从接口拉取。
# 之前预设的 gpt-4o/deepseek-chat 等 12 个模型已按用户要求移除。
DEFAULT_MODELS: list = []

# 图片输入口总数：图片0 ~ 图片8，前端 JS 按此值同步动态端口（默认只显示 1 个）
MAX_IMAGES = 9

# ── 渐进式披露（文本协议多轮按需读取）────────────────────────────────────
# 当 skills 输入为「自动」清单时，模型可输出单行 READ: 指令请求读取某个
# skills 的正文或参考文件，节点读取后追加到对话中继续请求，直到模型给出
# 最终答案。不依赖接口的 tools/function calling 支持，兼容性最好。
READ_DIRECTIVE_RE = re.compile(
    r"^\s*READ\s*[:：]\s*(?P<target>[^\s]+)\s*$", re.IGNORECASE | re.MULTILINE
)
# 单次执行允许的最大往返轮数（防止模型不守协议导致死循环）
MAX_SKILLS_ROUNDS_DEFAULT = 8
# 单次读取的字符上限
SKILLS_READ_MAX_CHARS_DEFAULT = 72000
# 累计注入的 skills 内容上限（防止上下文无限膨胀）
SKILLS_TOTAL_CHARS_DEFAULT = 300000

# 空响应自动重试次数（仅针对 finish_reason 正常结束的瞬时空响应）
EMPTY_OUTPUT_RETRIES = 2
# 「空输出重试次数」控件允许的上限
EMPTY_OUTPUT_RETRIES_MAX = 5

# 种子取值范围（与「种子」控件 min/max 一致）
SEED_MIN = -1
SEED_MAX = 0x7FFFFFFF

# ── 完整请求参数（可选，默认全部「不发送」）──────────────────────────────
# 默认值一律取「不发送」语义（text / 0 / 空串），因此旧工作流与只实现部分字段的
# 中转接口行为完全不变；只有用户显式改动控件才会往请求体里加字段。
OUTPUT_FORMAT_TEXT = "text"
OUTPUT_FORMAT_JSON_OBJECT = "json_object"
OUTPUT_FORMAT_OPTIONS = (
    OUTPUT_FORMAT_TEXT,
    OUTPUT_FORMAT_JSON_OBJECT,
)

# 推理强度（OpenAI reasoning_effort / 部分推理模型支持）；空串 = 不发送
REASONING_EFFORT_OPTIONS = ("", "low", "medium", "high")

# 请求超时（秒）
REQUEST_TIMEOUT_DEFAULT = 120
REQUEST_TIMEOUT_MIN = 1
REQUEST_TIMEOUT_MAX = 1800

# 图片缩放：最长边上限（0 = 不缩放）。默认 1568 与主流视觉模型的推荐边长一致，
# 既能保住细节，又能避免大图把 token / 请求体撑爆。
IMAGE_MAX_SIDE_DEFAULT = 1568
IMAGE_MAX_SIDE_MIN = 0
IMAGE_MAX_SIDE_MAX = 4096
# 图片细节档位（OpenAI image_url.detail）；auto 为接口默认，不显式发送
IMAGE_DETAIL_OPTIONS = ("auto", "low", "high")

# ── 多轮会话（节点后台维护，默认关闭）──────────────────────────────────
# 「启用多轮对话」开启后，节点自动把本节点此前的对话轮次拼到本轮之前；关闭再开启、
# 或 ComfyUI 重启都会自动开新会话。一个节点只维护一个会话（上下文）。
SESSION_MAX_ROUNDS_DEFAULT = 0  # 0 = 不限制
SESSION_MAX_ROUNDS_MAX = 200

# ── 内置工具（后台声明，自动管理，不暴露给用户配置）──────────────────────
# 节点只声明自己真正能执行的工具：读取 skills 文件。模型通过原生 tool_calls 请求
# 读取时，节点自动读取文件并把内容作为 tool 消息回注，等价于 READ: 文本协议，
# 但走的是 OpenAI 标准函数调用通道（对支持原生工具调用的模型更自然）。
BUILTIN_TOOL_READ_SKILL = "read_skill"
BUILTIN_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": BUILTIN_TOOL_READ_SKILL,
            "description": (
                "读取 skills 目录中的文件内容。当你需要某个 skills 的完整说明或"
                "参考资料时调用；同一文件不必重复读取。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "skill": {
                        "type": "string",
                        "description": "skills 名称，例如 h3-prompt-writing",
                    },
                    "path": {
                        "type": "string",
                        "description": "相对该 skills 目录的文件路径，默认 SKILL.md",
                    },
                },
                "required": ["skill"],
            },
        },
    }
]
BUILTIN_TOOL_NAMES = tuple(item["function"]["name"] for item in BUILTIN_TOOLS)

# ── 「简略上下文」输出端口 ────────────────────────────────────────────────
# 把本次运行的轨迹用代码拼装成纯文本：步数、输入的 skills 名称、实际读取了哪些
# skills、每一步的思考与动作、最终输出。**不做任何模型总结**，因此内容与请求/响应
# 一一对应，可直接用于事后核对。
CONTEXT_TITLE = "# 简略上下文（本次运行，由节点代码拼装，未经模型总结）"

# 「自动」清单中的 skills 行：`- <id>（<显示名>）: <描述>`
_MANIFEST_SKILL_RE = re.compile(
    r"^-\s+(?P<id>[a-z0-9][a-z0-9._-]*)(?:（[^）]*）)?\s*[:：]"
)
# 手动选择具体 skills 时指导文本的首行：`# 已选 skills：<id>`
_SELECTED_SKILL_RE = re.compile(r"^#\s*已选 skills\s*[:：]\s*(?P<id>\S+)")


def input_skill_names(skills_text, auto) -> tuple:
    """从 skills 输入文本中提取 skills 名称（只要名称，不含描述与正文）。

    - auto=True（「自动」清单）：逐行解析 `- <id>（<显示名>）: <描述>`；
    - auto=False（手动选具体 skills）：解析首行 `# 已选 skills：<id>`。

    只做确定性解析，识别不到时返回空元组（不臆造名称）；名称按出现顺序去重。
    注意：手动选择时正文里也可能出现 `- xxx: ...` 形式的列表项，因此该分支
    只认首行标题，不逐行扫描，避免把正文条目误当成 skills 名称。
    """
    text = str(skills_text or "")
    names = []
    if auto:
        for line in text.splitlines():
            match = _MANIFEST_SKILL_RE.match(line)
            if match:
                names.append(match.group("id"))
    else:
        match = _SELECTED_SKILL_RE.search(text)
        if match:
            names.append(match.group("id"))
    return tuple(dict.fromkeys(names))


def skills_manifest_ids(skills_text) -> tuple:
    """从 skills管理器 的「自动」清单里解析出 skills 名称（白名单来源）。"""
    return input_skill_names(skills_text, auto=True)


def is_skills_manager_manifest(skills_text) -> bool:
    """判断 skills 输入是否确实是 skills管理器 输出的「自动」清单。

    必须同时满足：① 带自动标记（`<<<YTMMI_SKILLS_AUTO>>>`）；② 至少解析出
    1 个 skills 名称。只有满足这两条才启用渐进式披露与内置工具，保证「工作流
    接入了 skills管理器」才具备读取 skills 的能力；普通字符串（哪怕恰好带标记
    但没有清单条目）不会触发任何文件读取。
    """
    if is_auto_skills_text is None or not is_auto_skills_text(skills_text):
        return False
    return bool(skills_manifest_ids(skills_text))


def _normalize_allowed_skills(allowed_skills):
    """把允许读取的 skills 名称归一化为小写集合；None 表示不限制。"""
    if allowed_skills is None:
        return None
    return {
        str(item).strip().casefold()
        for item in allowed_skills
        if str(item).strip()
    }


def _labelled_block(label: str, text) -> list:
    """渲染「- 标签：」+ 缩进多行内容；空内容渲染为「（无）」。"""
    body = str(text or "").strip()
    if not body:
        return [f"- {label}：（无）"]
    return [f"- {label}："] + [f"  {line}" for line in body.splitlines()]


# ── 可选请求参数的解析（全部纯函数，便于单测）────────────────────────────


def build_response_format(output_format):
    """构造 response_format；text 返回 None（不发送该字段）。"""
    fmt = str(output_format or OUTPUT_FORMAT_TEXT).strip().lower()
    if fmt in ("", OUTPUT_FORMAT_TEXT):
        return None
    if fmt == OUTPUT_FORMAT_JSON_OBJECT:
        return {"type": OUTPUT_FORMAT_JSON_OBJECT}
    raise ValueError(
        f"自定义LLM：未知的输出格式「{output_format}」，"
        f"可选 {'/'.join(OUTPUT_FORMAT_OPTIONS)}"
    )


def extract_tool_calls(message) -> list:
    """提取响应 message 中的 tool_calls（OpenAI 规范），无则返回 []。"""
    if not isinstance(message, dict):
        return []
    calls = message.get("tool_calls")
    return calls if isinstance(calls, list) else []


def build_optional_fields(
    output_format=OUTPUT_FORMAT_TEXT,
    frequency_penalty=0.0,
    presence_penalty=0.0,
    n=1,
    top_k=0,
    reasoning_effort="",
) -> dict:
    """把「完整请求参数」控件值转成要并入请求体的字段。

    只返回用户**显式启用**的字段（默认值一律不发送），因此旧工作流行为不变。
    参数非法时抛 ValueError（中文说明 + 定位信息）。
    """
    fields = {}

    response_format = build_response_format(output_format)
    if response_format is not None:
        fields["response_format"] = response_format

    frequency = float(frequency_penalty or 0.0)
    if frequency:
        fields["frequency_penalty"] = frequency
    presence = float(presence_penalty or 0.0)
    if presence:
        fields["presence_penalty"] = presence

    count = int(n or 1)
    if count != 1:
        fields["n"] = count
    top_k_value = int(top_k or 0)
    if top_k_value:
        fields["top_k"] = top_k_value

    effort = str(reasoning_effort or "").strip().lower()
    if effort:
        if effort not in REASONING_EFFORT_OPTIONS:
            raise ValueError(
                f"自定义LLM：「推理强度」不支持「{reasoning_effort}」，"
                f"可选 {'/'.join(x for x in REASONING_EFFORT_OPTIONS if x)} 或留空"
            )
        fields["reasoning_effort"] = effort

    return fields


# ── 多轮会话（节点后台维护，进程内存）────────────────────────────────────

_SESSION_LOCK = threading.Lock()
# key -> {"messages": [{"role":..., "content":...}, ...], "rounds": int}
_SESSIONS: dict = {}


def session_key(unique_id) -> str:
    """把隐藏输入 unique_id 归一化为会话键（缺失时用 default）。"""
    if isinstance(unique_id, (list, tuple)):
        unique_id = unique_id[0] if unique_id else ""
    key = str(unique_id or "").strip()
    return key or "default"


def session_history(key, max_rounds=SESSION_MAX_ROUNDS_DEFAULT) -> list:
    """取会话历史消息副本；达到「最大会话轮数」时自动开新会话（返回空列表）。"""
    limit = max(0, int(max_rounds or 0))
    with _SESSION_LOCK:
        session = _SESSIONS.get(key)
        if not session:
            return []
        if limit and session["rounds"] >= limit:
            _SESSIONS.pop(key, None)
            return []
        return [dict(item) for item in session["messages"]]


def remember_session_turn(key, prompt, reply_text) -> None:
    """把本轮「用户提示词 + 最终回复」追加到会话。"""
    with _SESSION_LOCK:
        session = _SESSIONS.setdefault(key, {"messages": [], "rounds": 0})
        session["messages"].append({"role": "user", "content": str(prompt)})
        session["messages"].append({"role": "assistant", "content": str(reply_text)})
        session["rounds"] += 1


def reset_session(key) -> None:
    """清空指定会话（下次从空上下文开始）。"""
    with _SESSION_LOCK:
        _SESSIONS.pop(key, None)


def clear_sessions() -> None:
    """清空全部会话（测试与排查用）。"""
    with _SESSION_LOCK:
        _SESSIONS.clear()


@dataclass
class LLMReply:
    """一次 chat/completions 请求的解析结果。"""

    text: str  # 节点实际采用的文本（content 为空时已回退到思考内容）
    reasoning: str  # 模型思考内容（reasoning_content / reasoning），可能为空
    source: str  # "content" / "reasoning_content" / "tool_calls" / ""
    tool_calls: list = field(default_factory=list)  # 模型请求的工具调用
    usage: dict = field(default_factory=dict)  # 接口返回的 usage 统计
    finish_reason: str = ""  # 接口返回的 finish_reason
    elapsed: float = 0.0  # 本次请求耗时（秒）


@dataclass
class RunStep:
    """一次接口请求（一步）的运行记录。"""

    index: int
    action: str = ""
    reasoning: str = ""
    reply: str = ""
    source: str = "content"
    is_final: bool = False
    usage: dict = field(default_factory=dict)  # 该步接口返回的 usage
    elapsed: float = 0.0  # 该步耗时（秒）
    tool_calls: list = field(default_factory=list)  # 该步模型请求的工具调用


@dataclass
class RunTrace:
    """本次运行的轨迹，「简略上下文」端口据此渲染纯文本。"""

    model: str = ""
    mode: str = ""
    input_skills: tuple = ()
    steps: list = field(default_factory=list)
    reads: list = field(default_factory=list)  # (读取路径, skills id, 字符数)
    injected_chars: int = 0
    final_text: str = ""

    def usage_totals(self) -> dict:
        """汇总所有步骤的 usage（prompt / completion / total tokens 与耗时）。"""
        totals = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "elapsed": 0.0,
        }
        for step in self.steps:
            usage = step.usage if isinstance(step.usage, dict) else {}
            for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
                value = usage.get(key)
                if isinstance(value, (int, float)):
                    totals[key] += int(value)
            totals["elapsed"] += float(step.elapsed or 0.0)
        return totals

    def skill_usage(self) -> list:
        """按 skills id 汇总读取次数：[(id, 次数), ...]（按首次出现顺序）。"""
        counts = {}
        for _path, skill_id, _chars in self.reads:
            counts[skill_id] = counts.get(skill_id, 0) + 1
        return list(counts.items())

    def render(self) -> str:
        """渲染为纯文本（确定性拼装，全程无模型参与）。"""
        lines = [CONTEXT_TITLE, ""]
        lines.append(f"- 模型：{self.model or '（未指定）'}")
        lines.append(f"- 模式：{self.mode}")
        lines.append(f"- 步数：{len(self.steps)} 步（每步 = 一次接口请求）")

        if self.input_skills:
            lines.append(
                f"- 输入 skills（仅名称，共 {len(self.input_skills)} 个）："
                + "、".join(self.input_skills)
            )
        else:
            lines.append(
                "- 输入 skills（仅名称）：无（未从输入文本中识别到 skills 名称）"
            )

        usage = self.skill_usage()
        if usage:
            summary = "、".join(f"{sid}（{n} 次）" for sid, n in usage)
            lines.append(f"- 调用的 skills：{summary}")
            lines.append(
                f"- 读取明细（共 {len(self.reads)} 个文件，"
                f"注入 {self.injected_chars:,} 字符）："
            )
            for path, _sid, chars in self.reads:
                lines.append(f"  - {path}（{chars:,} 字符）")
        else:
            lines.append("- 调用的 skills：无（本次未按需读取任何 skills 文件）")

        for step in self.steps:
            lines.append("")
            lines.append(f"## 第 {step.index} 步")
            if step.action:
                lines.append(f"- 动作：{step.action}")
            lines.extend(_labelled_block("思考", step.reasoning))
            if step.source == "reasoning_content":
                lines.append(
                    "- 说明：本轮接口未返回 content，节点按既有规则回退使用思考内容"
                )
            if step.tool_calls:
                lines.append(
                    f"- 工具调用：模型请求了 {len(step.tool_calls)} 个工具"
                    "（本节点不执行工具，已把 tool_calls 原样作为输出文本返回）"
                )
            # 最终步的回复即「最终输出」，不在此处重复
            if not step.is_final:
                lines.extend(_labelled_block("回复", step.reply))

        lines.append("")
        lines.append("## 最终输出")
        lines.append("")
        lines.append(str(self.final_text) if str(self.final_text).strip() else "（空）")

        # 用量统计（接口返回 usage 时才输出，避免在纯文本里堆无意义的 0）
        totals = self.usage_totals()
        if totals["total_tokens"] or totals["elapsed"]:
            completion = totals["completion_tokens"]
            elapsed = totals["elapsed"]
            lines.append("")
            lines.append("## 用量统计")
            lines.append("")
            lines.append(
                f"- token：输入 {totals['prompt_tokens']:,} / "
                f"输出 {completion:,} / 合计 {totals['total_tokens']:,}"
            )
            lines.append(f"- 接口耗时：{elapsed:.2f} 秒（{len(self.steps)} 步合计）")
            if completion > 0 and elapsed > 0:
                lines.append(f"- 输出速度：{completion / elapsed:.2f} token/秒")
            tool_steps = [step for step in self.steps if step.tool_calls]
            if tool_steps:
                lines.append(
                    f"- 工具调用：{sum(len(s.tool_calls) for s in tool_steps)} 个"
                    f"（涉及 {len(tool_steps)} 步）"
                )
        return "\n".join(lines)


class EmptyLLMOutputError(RuntimeError):
    """接口返回 200 但内容为空。

    retryable=True 表示该空响应可能是瞬时的（如网关抖动、模型偶发空回复），
    可安全重试一次；截断/内容过滤/工具调用等属于确定性原因，重试无意义。
    """

    def __init__(self, message, retryable=False):
        super().__init__(message)
        self.retryable = bool(retryable)

# 获取模型成功后的接口模型列表缓存（进程内）。
# 作用：ComfyUI 后端会校验 COMBO 输入值必须存在于 INPUT_TYPES 的选项列表中，
# 因此把「获取模型」得到的真实模型并入选项，保证 deepseek-v4-pro 这类
# 接口返回的模型也能通过校验。
_MODEL_LIST_CACHE: set = set()


def combo_model_options() -> list:
    """「选择模型」下拉选项 = 已获取的接口模型（默认无预设，去重排序）。"""
    return sorted(set(DEFAULT_MODELS) | _MODEL_LIST_CACHE, key=str.casefold)


def parse_models(data):
    """从 OpenAI /models 兼容响应中提取模型 id 列表。

    兼容两种常见结构：
    - {"object": "list", "data": [{"id": "gpt-4o-mini", ...}, ...]}
    - {"models": ["model-a", ...]} 或 {"models": [{"name": ...}, ...]}
    """
    models = []
    if isinstance(data, dict):
        items = data.get("data")
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    mid = item.get("id") or item.get("name") or item.get("model")
                    if mid:
                        models.append(str(mid))
        if not models and isinstance(data.get("models"), list):
            for item in data["models"]:
                if isinstance(item, str):
                    models.append(item)
                elif isinstance(item, dict):
                    mid = item.get("id") or item.get("name") or item.get("model")
                    if mid:
                        models.append(str(mid))
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, str):
                models.append(item)
            elif isinstance(item, dict):
                mid = item.get("id") or item.get("name") or item.get("model")
                if mid:
                    models.append(str(mid))
    # 去重并保持顺序
    seen = set()
    return [m for m in models if not (m in seen or seen.add(m))]


if (
    PromptServer is not None
    and web is not None
    and getattr(PromptServer, "instance", None) is not None
):

    @PromptServer.instance.routes.post("/ytmmi/llm/models")
    async def ytmmi_llm_models(request):
        """拉取 OpenAI 兼容接口的模型列表，供前端「获取模型」按钮调用。

        支持两种凭据来源：
        1. body 携带「密钥名称」→ 从密钥储存器解密取密钥/接口地址
           （解决 API密钥/接口地址 为端口连接时前端读不到值的问题）；
        2. body 携带 api_key / base_url（手动填写场景）。
        """
        try:
            body = await request.json()
        except Exception:
            return web.json_response({"error": "请求体不是有效 JSON"}, status=400)

        api_key = str(body.get("api_key", "")).strip()
        base_url = str(body.get("base_url", "")).strip()

        # 优先使用密钥储存器中保存的凭据
        key_name = str(body.get("密钥名称", "")).strip()
        if key_name:
            if load_vault is None:
                return web.json_response(
                    {"error": "无法访问密钥储存器（密钥库模块不可用）"}, status=500
                )
            vault = load_vault()
            if key_name not in vault:
                return web.json_response(
                    {"error": f"未找到已保存的密钥「{key_name}」，请先在密钥储存器中保存"},
                    status=404,
                )
            entry = vault[key_name]
            api_key = str(entry.get("密钥", "")).strip() or api_key
            base_url = str(entry.get("接口地址", "")).strip() or base_url

        if not api_key:
            return web.json_response(
                {"error": "请输入 API Key（或在「选择密钥」下拉中选择已保存的密钥）"},
                status=400,
            )
        if not base_url:
            return web.json_response(
                {"error": "请输入接口地址（base_url）"}, status=400
            )

        url = base_url.rstrip("/") + "/models"
        headers = {"Authorization": f"Bearer {api_key}"}
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers) as resp:
                    text = await resp.text()
                    if resp.status != 200:
                        return web.json_response(
                            {"error": f"接口返回 {resp.status}：{text[:300]}"},
                            status=400,
                        )
                    data = await resp.json(content_type=None)
        except Exception as exc:
            return web.json_response({"error": f"请求失败：{exc}"}, status=500)

        models = parse_models(data)
        if not models:
            return web.json_response(
                {"error": "未从接口响应中解析到模型列表"}, status=400
            )
        # 缓存获取到的模型，并入「选择模型」下拉选项（后端校验依赖 INPUT_TYPES 选项）
        _MODEL_LIST_CACHE.update(models)
        return web.json_response({"models": models})


class CustomLLMNode:
    """自定义在线 LLM（OpenAI 兼容接口）。"""

    CATEGORY = "YTmmi/text"
    DESCRIPTION = '自定义LLM：调用任意 OpenAI 兼容格式的在线大模型接口，支持选择密钥储存器密钥、获取模型列表、skills 输入接口（接入 skills管理器输出的指导文本，自动清单走多轮按需读取）、图片输入（最多9张，适配 DeepSeek V4.1 Flash 等视觉模型，可等比缩放并设置细节档位）、温度/最大token/top_p/种子（含官方生成后控制）、完整请求参数（输出格式/频率惩罚/存在惩罚/候选数量/top_k/推理强度/超时/空输出重试）、多轮会话（默认关闭，开启后节点后台自动维护上下文，可设最大会话轮数）、内置工具（后台声明 read_skill 并自动执行，无需人工配置）；输出文本之外另输出「简略上下文」（步数/输入skills名称/调用的skills/每步思考/最终输出/用量统计，纯代码拼装不调用模型总结）'

    @classmethod
    def INPUT_TYPES(cls):
        # 「选择密钥」选项 = 密钥储存器中已保存的名称列表
        try:
            key_names = list(vault_names()) if vault_names else []
        except Exception:
            key_names = []
        return {
            "required": {
                "API密钥": ("STRING", {"default": "", "multiline": False, "placeholder": "sk-..."}),
                "接口地址": (
                    "STRING",
                    {"default": "", "multiline": False, "placeholder": "https://api.openai.com/v1"},
                ),
                "选择模型": (combo_model_options() or [""], {"default": ""}),
                # 选择密钥储存器中已保存的密钥：自动填写 API密钥/接口地址（含「获取模型」）
                "选择密钥": (key_names or [""], {"default": ""}),
                "系统提示词": ("STRING", {"default": "", "multiline": True}),
                "提示词": ("STRING", {"default": "", "multiline": True, "placeholder": "输入要求或问题"}),
                "温度": ("FLOAT", {"default": 0.7, "min": 0.0, "max": 2.0, "step": 0.1}),
                "最大token数": (
                    "INT",
                    {
                        "default": 8192,
                        "min": 1,
                        "max": 32768,
                        "tooltip": "生成的最大 token 数。推理模型会先消耗大量 token 用于思考，"
                        "默认 8192；若出现「思考被截断」请继续调大",
                    },
                ),
            },
            "optional": {
                # skills 指导文本：由「skills管理器」节点的 skills 输出接入（字符串端口）。
                # 接入「自动」清单时进入多轮按需读取（渐进式披露）。
                "skills": ("STRING", {"forceInput": True}),
                "skills最大轮数": (
                    "INT",
                    {
                        "default": MAX_SKILLS_ROUNDS_DEFAULT,
                        "min": 1,
                        "max": 30,
                        "step": 1,
                        "tooltip": "skills 为「自动」时的最大读取往返轮数，防止模型不守协议导致死循环",
                    },
                ),
                "skills单次读取上限": (
                    "INT",
                    {
                        "default": SKILLS_READ_MAX_CHARS_DEFAULT,
                        "min": 1000,
                        "max": 400000,
                        "step": 1000,
                        "tooltip": "单次读取 skills 文件的字符上限，超出部分截断",
                    },
                ),
                "skills累计上限": (
                    "INT",
                    {
                        "default": SKILLS_TOTAL_CHARS_DEFAULT,
                        "min": 1000,
                        "max": 2000000,
                        "step": 1000,
                        "tooltip": "多轮累计注入的 skills 内容字符上限，防止上下文无限膨胀",
                    },
                ),
                "核采样（top_p）": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.05}),
                # ── 完整请求参数（默认值一律「不发送」，旧工作流行为不变）──
                "输出格式": (
                    list(OUTPUT_FORMAT_OPTIONS),
                    {
                        "default": OUTPUT_FORMAT_TEXT,
                        "tooltip": "text：不发送 response_format（默认）；"
                        "json_object：要求接口返回 JSON 对象",
                    },
                ),
                "频率惩罚": (
                    "FLOAT",
                    {
                        "default": 0.0,
                        "min": -2.0,
                        "max": 2.0,
                        "step": 0.1,
                        "tooltip": "frequency_penalty：按词频惩罚重复用词；0 = 不发送该字段",
                    },
                ),
                "存在惩罚": (
                    "FLOAT",
                    {
                        "default": 0.0,
                        "min": -2.0,
                        "max": 2.0,
                        "step": 0.1,
                        "tooltip": "presence_penalty：按是否出现过惩罚重复话题；0 = 不发送该字段",
                    },
                ),
                "候选数量": (
                    "INT",
                    {
                        "default": 1,
                        "min": 1,
                        "max": 10,
                        "step": 1,
                        "tooltip": "n：接口返回的候选数；节点只取第 1 个候选，1 = 不发送该字段",
                    },
                ),
                "top_k": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": 200,
                        "step": 1,
                        "tooltip": "top_k：非 OpenAI 官方字段，部分接口支持；0 = 不发送该字段",
                    },
                ),
                "推理强度": (
                    list(REASONING_EFFORT_OPTIONS),
                    {
                        "default": "",
                        "tooltip": "reasoning_effort：推理模型思考量档位；留空 = 不发送该字段",
                    },
                ),
                "超时秒数": (
                    "INT",
                    {
                        "default": REQUEST_TIMEOUT_DEFAULT,
                        "min": REQUEST_TIMEOUT_MIN,
                        "max": REQUEST_TIMEOUT_MAX,
                        "step": 1,
                        "tooltip": "单次接口请求超时（秒）；推理模型长输出需要调大",
                    },
                ),
                "空输出重试次数": (
                    "INT",
                    {
                        "default": EMPTY_OUTPUT_RETRIES,
                        "min": 0,
                        "max": EMPTY_OUTPUT_RETRIES_MAX,
                        "step": 1,
                        "tooltip": "接口返回 200 但内容为空且属正常结束时自动重试的次数；"
                        "截断/内容过滤/工具调用等确定性原因不重试",
                    },
                ),
                # ── 多轮会话（节点后台自动维护上下文，默认关闭）──
                "启用多轮对话": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "开启后节点自动把本节点此前的对话拼到本轮之前"
                        "（无需手工填写历史）；关闭再开启、或 ComfyUI 重启都会自动开新会话",
                    },
                ),
                "最大会话轮数": (
                    "INT",
                    {
                        "default": SESSION_MAX_ROUNDS_DEFAULT,
                        "min": 0,
                        "max": SESSION_MAX_ROUNDS_MAX,
                        "step": 1,
                        "tooltip": "会话保留的最大轮数；0 = 不限制，"
                        "达到上限后下一轮自动开新会话",
                    },
                ),
                # ── 图片增强 ──
                "图片最长边": (
                    "INT",
                    {
                        "default": IMAGE_MAX_SIDE_DEFAULT,
                        "min": IMAGE_MAX_SIDE_MIN,
                        "max": IMAGE_MAX_SIDE_MAX,
                        "step": 1,
                        "tooltip": "发送前把图片等比缩放到最长边不超过该值（0 = 不缩放）；"
                        "缩小可显著降低 token 与请求体体积",
                    },
                ),
                "图片细节": (
                    list(IMAGE_DETAIL_OPTIONS),
                    {
                        "default": "auto",
                        "tooltip": "image_url.detail：auto 不显式发送 / low 省 token / high 保细节",
                    },
                ),
                # 「种子」使用 ComfyUI 官方 control_after_generate 机制（与 KSampler 一致）：
                # 前端据此自动生成配套的「生成后控制」下拉（固定值/递增值/递减值/随机值），
                # 该下拉 serialize:false 不会发给后端，仅由前端在生成后改写种子控件值。
                "种子": (
                    "INT",
                    {
                        "default": -1,
                        "min": SEED_MIN,
                        "max": SEED_MAX,
                        "control_after_generate": True,
                        "tooltip": "随机种子；-1 表示不发送 seed（由服务端随机）。"
                        "旁边的「生成后控制」可让它在每次生成后自动变化",
                    },
                ),
                # 图片输入口：图片0 ~ 图片8（IMAGE 类型）。前端默认只显示「图片0」，
                # 连接后自动显现下一张，最多 9 张（与 MAX_IMAGES 一致）
                **{f"图片{i}": ("IMAGE",) for i in range(MAX_IMAGES)},
            },
            # 隐藏输入：ComfyUI 执行时注入节点 id，用作「多轮会话」的会话键。
            # 不占前端端口，也不写进工作流控件值。
            "hidden": {"unique_id": "UNIQUE_ID"},
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("输出文本", "简略上下文")
    FUNCTION = "chat"
    OUTPUT_NODE = False
    OUTPUT_IS_LIST = (False, False)
    SEARCH_ALIASES = [
        "llm",
        "chat",
        "大模型",
        "ai对话",
        "openai",
        "skills",
        "技能",
        "种子",
        "生成后控制",
        "简略上下文",
        "多轮对话",
        "多轮会话",
        "会话",
        "上下文",
        "工具调用",
        "function calling",
        "图片细节",
    ]

    def chat(
        self,
        **kwargs,
    ):
        # 中文控件名在 kwargs 中接收，内部变量保持英文
        model = kwargs.get("选择模型", "")
        system_prompt = kwargs.get("系统提示词", "")
        prompt = kwargs.get("提示词", "")
        skills = kwargs.get("skills", "")
        temperature = kwargs.get("温度", 0.7)
        max_tokens = kwargs.get("最大token数", 1024)
        top_p = kwargs.get("核采样（top_p）", 1.0)
        seed = kwargs.get("种子", -1)

        # ── 完整请求参数 / 多轮会话 / 图片增强 ──
        # 全部为可选控件，默认值即「不发送 / 不启用」，因此旧工作流行为不变。
        extra_fields = build_optional_fields(
            output_format=kwargs.get("输出格式", OUTPUT_FORMAT_TEXT),
            frequency_penalty=kwargs.get("频率惩罚", 0.0),
            presence_penalty=kwargs.get("存在惩罚", 0.0),
            n=kwargs.get("候选数量", 1),
            top_k=kwargs.get("top_k", 0),
            reasoning_effort=kwargs.get("推理强度", ""),
        )
        retries = int(kwargs.get("空输出重试次数", EMPTY_OUTPUT_RETRIES))
        timeout = int(kwargs.get("超时秒数", REQUEST_TIMEOUT_DEFAULT))
        image_max_side = int(kwargs.get("图片最长边", IMAGE_MAX_SIDE_DEFAULT))
        image_detail = str(kwargs.get("图片细节", "auto")).strip().lower()
        if image_detail not in IMAGE_DETAIL_OPTIONS:
            raise ValueError(
                f"自定义LLM：「图片细节」不支持「{image_detail}」，"
                f"可选 {'/'.join(IMAGE_DETAIL_OPTIONS)}"
            )

        # 多轮会话：节点后台维护上下文（默认关闭）。
        # 关闭时清空会话，因此「关闭再开启」自动从新会话开始；ComfyUI 重启后
        # 模块级会话表为空，同样自动开新会话。一个节点只维护一个会话。
        multi_turn = bool(kwargs.get("启用多轮对话", False))
        max_session_rounds = int(
            kwargs.get("最大会话轮数", SESSION_MAX_ROUNDS_DEFAULT) or 0
        )
        session = session_key(kwargs.get("unique_id"))
        if multi_turn:
            history_messages = session_history(session, max_session_rounds)
        else:
            history_messages = []
            reset_session(session)

        # 凭据规则：
        # 1. API密钥 与 接口地址 必须成对填写（两个都填 → 用手动组合，忽略「选择密钥」）；
        # 2. 只填了其中一个 → 报错，提示清空输入以应用「选择密钥」；
        # 3. 两个都为空 → 应用「选择密钥」对应的密钥库凭据。
        api_key = str(kwargs.get("API密钥", "")).strip()
        base_url = str(kwargs.get("接口地址", "")).strip()
        if bool(api_key) != bool(base_url):
            raise ValueError(
                "自定义LLM：API密钥 与 接口地址 必须成对填写（两个都填，或两个都留空）；"
                "若要使用「选择密钥」，请将两个输入框都清空"
            )

        selected_key = str(kwargs.get("选择密钥", "")).strip()
        if not api_key and not base_url:
            # 两个输入都为空 → 应用「选择密钥」的密钥库凭据
            if selected_key:
                if load_vault is None:
                    raise RuntimeError("自定义LLM：无法访问密钥储存器（密钥库模块不可用）")
                vault = load_vault()
                if selected_key not in vault:
                    raise ValueError(
                        f"自定义LLM：未找到已保存的密钥「{selected_key}」，请先在密钥储存器中保存"
                    )
                entry = vault[selected_key]
                api_key = str(entry.get("密钥", "")).strip()
                base_url = str(entry.get("接口地址", "")).strip()

        if requests is None:
            raise RuntimeError("自定义LLM：缺少 requests 库，请先安装 requests")

        if not str(api_key).strip():
            raise ValueError("自定义LLM：请输入 API Key")
        if not str(base_url).strip():
            raise ValueError("自定义LLM：请输入接口地址（base_url）")
        if not str(model).strip():
            raise ValueError("自定义LLM：请选择模型")
        if not str(prompt).strip():
            raise ValueError("自定义LLM：请输入提示词（prompt）")

        # 组装 OpenAI 兼容请求
        url = str(base_url).strip().rstrip("/") + "/chat/completions"
        # 防御：请求地址必须是 http(s) 接口地址。若 url 变成图片 data URL 等异常内容
        # （如端口误连接、变量污染），在此直接给出清晰报错而非底层 adapter 错误
        if not (url.startswith("http://") or url.startswith("https://")):
            raise ValueError(
                "自定义LLM：接口地址（base_url）格式异常，必须以 http:// 或 https:// 开头，"
                f"当前值：{url[:120]}"
            )
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        # 收集已连接的图片输入（图片0 ~ 图片8，未连接为 None）
        images = []
        for i in range(MAX_IMAGES):
            img = kwargs.get(f"图片{i}")
            if img is not None:
                images.append(img)

        messages = []
        # skills 指导文本与系统提示词合并为同一条 system 消息：
        # skills 在前（作为模型指导），系统提示词在后（用户自身设定优先）
        system_text = self._merge_system_text(skills, system_prompt)
        if system_text:
            messages.append({"role": "system", "content": system_text})
        # 会话历史插在 system 与本轮 user 之间（默认关闭时 history_messages 为空）
        if history_messages:
            messages.extend(history_messages)
        if images:
            # 多模态格式：content 为数组，文本 + 图片（JPEG base64 data URL）。
            # 适配 DeepSeek V4.1 Flash（模型 id：deepseek-flash）等支持图片输入的
            # OpenAI 兼容视觉模型；图片仅放在 user 消息中（与官方规范一致）。
            content = [{"type": "text", "text": str(prompt)}]
            for img in images:
                for data_url in self._image_tensor_to_data_urls(
                    img, max_side=image_max_side, detail=image_detail
                ):
                    content.append({"type": "image_url", "image_url": data_url})
            messages.append({"role": "user", "content": content})
        else:
            messages.append({"role": "user", "content": str(prompt)})

        # 输入的 skills 名称（仅名称），供「简略上下文」记录。
        # 只有 skills 输入确实是 skills管理器 的「自动」清单（带自动标记且至少
        # 解析出 1 个 skills 名称）才启用渐进式披露与内置工具——即「工作流接入了
        # skills管理器」才具备读取 skills 的能力，任意字符串都不会触发文件读取。
        is_auto_input = is_skills_manager_manifest(skills)
        input_skills = input_skill_names(skills, auto=is_auto_input)
        # 允许读取的 skills 白名单：只能读本次清单里列出的 skills，防止模型读取
        # 被模式筛选掉的其它家族 skills。
        allowed_skills = input_skills if is_auto_input else None

        # skills 为「自动」清单时，进入多轮按需读取（渐进式披露）循环；
        # 否则单轮请求，行为与之前一致。
        # 「生成后控制」由前端在生成后改写「种子」控件值实现，节点后端不参与。
        # 内置工具只在 skills 自动清单（多轮按需读取）时声明：此时节点确实能执行
        # read_skill，工具调用才有意义；单轮模式不发送 tools，避免接口不兼容。
        auto_extra_fields = dict(extra_fields)
        auto_extra_fields["tools"] = [dict(item) for item in BUILTIN_TOOLS]
        auto_extra_fields["tool_choice"] = "auto"

        if is_auto_input:
            final_text, context_text = self._chat_with_skills_disclosure(
                url=url,
                headers=headers,
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                seed=seed,
                images=images,
                max_rounds=int(kwargs.get("skills最大轮数", MAX_SKILLS_ROUNDS_DEFAULT)),
                read_max_chars=int(
                    kwargs.get("skills单次读取上限", SKILLS_READ_MAX_CHARS_DEFAULT)
                ),
                total_max_chars=int(
                    kwargs.get("skills累计上限", SKILLS_TOTAL_CHARS_DEFAULT)
                ),
                input_skills=input_skills,
                allowed_skills=allowed_skills,
                extra_fields=auto_extra_fields,
                retries=retries,
                timeout=timeout,
            )
            if multi_turn:
                remember_session_turn(session, str(prompt), final_text)
            return (final_text, context_text)

        reply = self._post_chat(
            url=url,
            headers=headers,
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            seed=seed,
            images=images,
            retries=retries,
            extra_fields=extra_fields,
            timeout=timeout,
        )
        # 「简略上下文」：单轮请求同样记录一步（思考 + 最终输出）
        trace = RunTrace(
            model=str(model),
            mode="单轮请求（未按需读取 skills）",
            input_skills=input_skills,
            steps=[
                RunStep(
                    index=1,
                    action="直接作答",
                    reasoning=reply.reasoning,
                    reply=reply.text,
                    source=reply.source,
                    is_final=True,
                    usage=reply.usage,
                    elapsed=reply.elapsed,
                    tool_calls=reply.tool_calls,
                )
            ],
            final_text=reply.text,
        )
        if multi_turn:
            remember_session_turn(session, str(prompt), reply.text)
        return (reply.text, trace.render())

    # ── 单轮请求与响应解析 ────────────────────────────────────────────────

    def _post_chat(
        self,
        url,
        headers,
        messages,
        model,
        temperature,
        max_tokens,
        top_p,
        seed,
        images,
        retries=EMPTY_OUTPUT_RETRIES,
        extra_fields=None,
        timeout=REQUEST_TIMEOUT_DEFAULT,
    ) -> "LLMReply":
        """发送一次 chat/completions 请求并返回助手文本（含思考内容）。

        当接口返回 200 但内容为空、且 finish_reason 属于正常结束时，自动重试
        （最多 retries 次），避免偶发空响应直接变成空输出。

        extra_fields 为「完整请求参数」构造出的附加字段（默认空 = 不发送），
        timeout 为单次请求超时秒数。
        """
        last_error = None
        for attempt in range(max(0, int(retries)) + 1):
            try:
                return self._post_chat_once(
                    url=url,
                    headers=headers,
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=top_p,
                    seed=seed,
                    images=images,
                    extra_fields=extra_fields,
                    timeout=timeout,
                )
            except EmptyLLMOutputError as exc:
                last_error = exc
                if not exc.retryable or attempt >= int(retries):
                    raise
        raise last_error  # pragma: no cover - 循环内必然 return 或 raise

    def _post_chat_once(
        self,
        url,
        headers,
        messages,
        model,
        temperature,
        max_tokens,
        top_p,
        seed,
        images,
        extra_fields=None,
        timeout=REQUEST_TIMEOUT_DEFAULT,
    ) -> "LLMReply":
        """发送单次 chat/completions 请求并解析响应（同时保留思考内容）。"""
        payload = {
            "model": str(model),
            "messages": messages,
            "temperature": float(temperature),
            "max_tokens": int(max_tokens),
            "top_p": float(top_p),
        }
        if int(seed) >= 0:
            payload["seed"] = int(seed)
        # 完整请求参数：只并入用户显式启用的字段（默认不发送，旧行为不变）
        for key, value in (extra_fields or {}).items():
            payload[key] = value

        started = time.monotonic()
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=max(1, int(timeout or REQUEST_TIMEOUT_DEFAULT)),
            )
        except Exception as exc:
            raise RuntimeError(f"自定义LLM：请求失败（{exc}）") from exc
        elapsed = time.monotonic() - started

        if response.status_code != 200:
            detail = response.text[:500] if response.text else "无响应内容"
            # 发送了图片但模型不支持：给出选模型建议（如 DeepSeek 需用 deepseek-flash）
            detail_lower = detail.lower()
            if images and (
                "does not support image" in detail_lower
                or "not support image" in detail_lower
                or "cannot read" in detail_lower
            ):
                raise RuntimeError(
                    f"自定义LLM：当前模型「{model}」不支持图片输入。"
                    "请选择支持视觉的模型（如 DeepSeek 的 deepseek-flash / DeepSeek V4.1 Flash）。"
                    f"接口返回 {response.status_code}：{detail}"
                )
            raise RuntimeError(
                f"自定义LLM：接口返回 {response.status_code}：{detail}"
            )

        try:
            data = response.json()
        except Exception as exc:
            raise RuntimeError(f"自定义LLM：响应解析失败（{exc}）") from exc

        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError("自定义LLM：接口返回结果中没有 choices 字段")

        choice = choices[0] if isinstance(choices[0], dict) else {}
        message = choice.get("message")
        if not isinstance(message, dict):
            message = {}
        finish_reason = str(choice.get("finish_reason") or "").strip().lower()
        usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}

        text, source = self._extract_message_text(message)
        reasoning = self._extract_reasoning_text(message)
        tool_calls = extract_tool_calls(message)

        if not text.strip():
            # 工具调用：模型只返回 tool_calls、没有正文。本节点不执行工具，
            # 因此把 tool_calls 序列化为输出文本（下游可自行解析），而不是报「空输出」。
            if tool_calls:
                text = json.dumps(
                    {"tool_calls": tool_calls}, ensure_ascii=False, indent=2
                )
                source = "tool_calls"
                return LLMReply(
                    text=text,
                    reasoning=reasoning,
                    source=source,
                    tool_calls=tool_calls,
                    usage=usage,
                    finish_reason=finish_reason,
                    elapsed=elapsed,
                )
            # 空输出不再静默返回空串（下游「展示文本（多重）」会看起来像没执行），
            # 而是抛出带明确原因的报错，便于定位是截断、过滤还是接口不兼容。
            # finish_reason 正常结束（stop/None）时视为可重试的瞬时抖动。
            retryable = finish_reason in ("", "stop", "null")
            raise EmptyLLMOutputError(
                self._empty_output_message(
                    model=model,
                    finish_reason=finish_reason,
                    usage=usage,
                    message=message,
                    images=images,
                    max_tokens=max_tokens,
                ),
                retryable=retryable,
            )

        if source == "reasoning_content" and finish_reason == "length":
            # 只有思考内容且被截断：说明 token 用尽在推理阶段，最终答案并未产生
            raise EmptyLLMOutputError(
                f"自定义LLM：模型「{model}」的思考过程被截断，未产生最终答案。"
                f"当前「最大token数」为 {int(max_tokens)}，推理模型会先消耗大量 token 用于思考，"
                "请调大「最大token数」后重试。"
            )

        return LLMReply(
            text=text,
            reasoning=reasoning,
            source=source,
            tool_calls=tool_calls,
            usage=usage,
            finish_reason=finish_reason,
            elapsed=elapsed,
        )

    @staticmethod
    def _parts_text(parts) -> str:
        """拼接 parts 数组中的文本（如 [{"type":"text","text":...}]）。"""
        chunks = []
        for part in parts:
            if isinstance(part, str):
                chunks.append(part)
            elif isinstance(part, dict):
                text = part.get("text")
                if isinstance(text, str):
                    chunks.append(text)
                elif isinstance(part.get("content"), str):
                    chunks.append(part["content"])
        return "".join(chunks)

    @staticmethod
    def _extract_message_text(message) -> tuple:
        """从响应 message 中提取文本，兼容多种 provider 形态。

        返回 (text, source)，source 取值 "content" / "reasoning_content" / ""：
        - content 为字符串 → 原样返回；
        - content 为 parts 数组（如 [{"type":"text","text":...}]）→ 拼接其中的文本；
        - content 为空但存在 reasoning_content → 回退到思考内容（部分推理模型
          会把答案放在该字段）。
        """
        if not isinstance(message, dict):
            return "", ""

        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content, "content"
        if isinstance(content, list):
            joined = CustomLLMNode._parts_text(content)
            if joined.strip():
                return joined, "content"

        # reasoning_content 为 DeepSeek 等推理模型的思考字段，reasoning 为部分网关的别名
        reasoning = CustomLLMNode._extract_reasoning_text(message)
        if reasoning.strip():
            return reasoning, "reasoning_content"

        return "", ""

    @staticmethod
    def _extract_reasoning_text(message) -> str:
        """提取模型的思考内容（reasoning_content / reasoning），无则返回空串。

        与 _extract_message_text 分开：即使 content 非空（正常作答），思考内容也要
        被独立保留，供「简略上下文」端口展示。
        """
        if not isinstance(message, dict):
            return ""
        for key in ("reasoning_content", "reasoning"):
            reasoning = message.get(key)
            if isinstance(reasoning, str) and reasoning.strip():
                return reasoning
            if isinstance(reasoning, list):
                joined = CustomLLMNode._parts_text(reasoning)
                if joined.strip():
                    return joined
        return ""

    @staticmethod
    def _empty_output_message(
        model, finish_reason, usage, message, images, max_tokens
    ) -> str:
        """构造空输出的诊断信息（含 finish_reason 与可执行的修复建议）。"""
        details = [f"接口返回了 200 但内容为空（模型「{model}」）"]
        if finish_reason:
            details.append(f"finish_reason={finish_reason}")

        completion_tokens = usage.get("completion_tokens")
        if completion_tokens is not None:
            details.append(f"completion_tokens={completion_tokens}")

        if isinstance(message.get("reasoning_content"), str) and message.get(
            "reasoning_content"
        ).strip():
            details.append("仅返回了 reasoning_content（思考内容）")
        if message.get("refusal"):
            details.append(f"refusal={str(message['refusal'])[:100]}")
        if "content" not in message:
            details.append("响应缺少 content 字段")

        hints = {
            "length": (
                f"输出被「最大token数」截断（当前 {int(max_tokens)}）。"
                "推理模型会先消耗大量 token 思考，请调大「最大token数」后重试。"
            ),
            "content_filter": "内容被接口安全策略过滤，请调整提示词或系统提示词。",
            "tool_calls": "模型尝试调用工具（tool_calls），而本节点未启用工具协议。",
            "function_call": "模型尝试调用函数（function_call），而本节点未启用工具协议。",
        }
        hint = hints.get(finish_reason)
        if hint is None:
            hint = (
                "常见原因：①「最大token数」过小导致输出被截断；"
                "②该模型为推理模型，需调大 token 上限；"
                "③接口/模型名不兼容或返回格式非 OpenAI 标准。"
            )
            if images:
                hint += " ④当前请求含图片，请确认所选模型支持视觉输入。"

        return "；".join(details) + "。" + hint

    # ── 渐进式披露：多轮按需读取 skills ───────────────────────────────────

    @staticmethod
    def parse_read_directive(text):
        """从模型输出中解析单行 READ: 指令。

        返回 (指令目标, 去掉指令后的剩余文本)：
        - 无指令 → (None, 原文)
        - 有指令 → (目标, 该行之外的其余内容)
        """
        if not isinstance(text, str):
            return None, ""
        match = READ_DIRECTIVE_RE.search(text)
        if not match:
            return None, text
        target = match.group("target").strip().strip("`\"'<>")
        remainder = (text[: match.start()] + text[match.end():]).strip()
        return (target or None), remainder

    @staticmethod
    def resolve_skill_read(target, allowed_skills=None):
        """将 READ 指令目标解析为 (skills id, 相对路径)。

        - "skills名称" → (id, "SKILL.md")
        - "skills名称/相对路径" → (id, 相对路径)

        allowed_skills 不为 None 时，解析出的 skills 必须在该白名单内（白名单来自
        本次 skills管理器 的「自动」清单），否则抛 ValueError 拒绝读取。
        """
        raw = str(target or "").strip().strip("/")
        if not raw:
            raise ValueError("自定义LLM：READ 指令未指定目标")

        names = list(skill_names() or []) if skill_names is not None else []
        by_lower = {name.casefold(): name for name in names}

        # 优先整体匹配 skills id（支持 id 内含点/下划线/连字符）
        if raw.casefold() in by_lower:
            skill_id, relative_path = by_lower[raw.casefold()], "SKILL.md"
        else:
            # 其次按 "/" 拆分：取最长能匹配到 skills id 的前缀
            skill_id, relative_path = "", ""
            parts = [part for part in raw.split("/") if part]
            for split in range(len(parts) - 1, 0, -1):
                prefix = "/".join(parts[:split])
                if prefix.casefold() in by_lower:
                    skill_id = by_lower[prefix.casefold()]
                    relative_path = "/".join(parts[split:])
                    break
            if not skill_id:
                raise ValueError(
                    f"自定义LLM：未找到 skills「{raw}」，"
                    f"可用 skills：{', '.join(names) or '（无）'}"
                )

        allowed = _normalize_allowed_skills(allowed_skills)
        if allowed is not None and skill_id.casefold() not in allowed:
            raise ValueError(
                f"自定义LLM：skills「{skill_id}」不在本次 skills 清单内，"
                "只能读取清单中列出的 skills"
            )
        return skill_id, relative_path

    def _chat_with_skills_disclosure(
        self,
        url,
        headers,
        messages,
        model,
        temperature,
        max_tokens,
        top_p,
        seed,
        images,
        max_rounds,
        read_max_chars,
        total_max_chars,
        input_skills=(),
        allowed_skills=None,
        extra_fields=None,
        retries=EMPTY_OUTPUT_RETRIES,
        timeout=REQUEST_TIMEOUT_DEFAULT,
    ) -> tuple:
        """多轮按需读取 skills，直到模型给出最终答案或达到轮数上限。

        文本协议：模型单独输出一行 `READ: <skills名称>[/相对路径]` 即请求读取，
        节点读取文件后以 user 消息回注，继续下一轮。

        allowed_skills 不为 None 时，只允许读取白名单内的 skills（白名单来自本次
        skills管理器 的「自动」清单），文本协议与内置工具两条通道都受同一约束。

        返回 (最终文本, 简略上下文)；简略上下文里每一步都与一次接口请求一一对应。
        """
        if read_skill_file is None or skill_names is None:
            raise RuntimeError(
                "自定义LLM：skills 按需读取不可用（skills管理器模块未加载）"
            )

        max_rounds = max(1, int(max_rounds))
        read_max_chars = max(1, int(read_max_chars))
        total_max_chars = max(1, int(total_max_chars))
        # 多轮对话内部使用副本，避免影响调用方传入的 messages
        convo = list(messages)
        injected = 0
        steps = []
        reads = []
        final_text = ""

        for _round_index in range(max_rounds):
            reply = self._post_chat(
                url=url,
                headers=headers,
                messages=convo,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                seed=seed,
                images=images,
                extra_fields=extra_fields,
                retries=retries,
                timeout=timeout,
            )
            step_index = len(steps) + 1

            # 内置工具调用（后台声明、自动执行）：模型通过原生 tool_calls 请求
            # 读取 skills 文件时，节点自动读取并回注，等价于 READ: 文本协议。
            if reply.tool_calls:
                tool_messages, tool_reads, tool_chars, note = self._run_builtin_tools(
                    reply.tool_calls,
                    read_max_chars=read_max_chars,
                    remaining_chars=max(0, total_max_chars - injected),
                    allowed_skills=allowed_skills,
                )
                injected += tool_chars
                reads.extend(tool_reads)
                steps.append(
                    RunStep(
                        index=step_index,
                        action=note,
                        reasoning=reply.reasoning,
                        reply="" if reply.source == "tool_calls" else reply.text,
                        source=reply.source,
                        usage=reply.usage,
                        elapsed=reply.elapsed,
                        tool_calls=reply.tool_calls,
                    )
                )
                convo.append(
                    {
                        "role": "assistant",
                        "content": "" if reply.source == "tool_calls" else reply.text,
                        "tool_calls": reply.tool_calls,
                    }
                )
                convo.extend(tool_messages)
                continue

            target, _remainder = self.parse_read_directive(reply.text)

            # 无读取指令 → 本轮即最终答案
            if not target:
                steps.append(
                    RunStep(
                        index=step_index,
                        action="直接作答（本轮未请求读取）",
                        reasoning=reply.reasoning,
                        reply=reply.text,
                        source=reply.source,
                        is_final=True,
                        usage=reply.usage,
                        elapsed=reply.elapsed,
                        tool_calls=reply.tool_calls,
                    )
                )
                final_text = reply.text
                break

            # 解析目标并读取文件
            try:
                skill_id, relative_path = self.resolve_skill_read(
                    target, allowed_skills=allowed_skills
                )
                file_text = read_skill_file(
                    skill_id, relative_path, max_chars=read_max_chars
                )
            except Exception as exc:
                steps.append(
                    RunStep(
                        index=step_index,
                        action=f"读取失败（{exc}）→ 已把错误回注给模型重试",
                        reasoning=reply.reasoning,
                        reply=reply.text,
                        source=reply.source,
                        usage=reply.usage,
                        elapsed=reply.elapsed,
                        tool_calls=reply.tool_calls,
                    )
                )
                # 读取失败：把错误回注给模型，让它改用正确的名称重试
                convo.append({"role": "assistant", "content": reply.text})
                convo.append(
                    {
                        "role": "user",
                        "content": f"READ 指令执行失败：{exc}\n请改用正确的 skills 名称或路径重试。",
                    }
                )
                continue

            # 累计上限保护：超出后不再注入，直接要求模型基于已有内容作答
            if injected + len(file_text) > total_max_chars:
                steps.append(
                    RunStep(
                        index=step_index,
                        action=(
                            f"已达累计上限（{total_max_chars:,} 字符），"
                            f"未注入 {skill_id}/{relative_path}"
                        ),
                        reasoning=reply.reasoning,
                        reply=reply.text,
                        source=reply.source,
                        usage=reply.usage,
                        elapsed=reply.elapsed,
                        tool_calls=reply.tool_calls,
                    )
                )
                convo.append({"role": "assistant", "content": reply.text})
                convo.append(
                    {
                        "role": "user",
                        "content": (
                            "已达到 skills 内容累计上限，请基于已获得的内容直接给出最终答案，"
                            "不要再请求读取。"
                        ),
                    }
                )
                continue

            injected += len(file_text)
            reads.append((f"{skill_id}/{relative_path}", skill_id, len(file_text)))
            steps.append(
                RunStep(
                    index=step_index,
                    action=(
                        f"读取 {skill_id}/{relative_path}"
                        f"（{len(file_text):,} 字符）并回注对话"
                    ),
                    reasoning=reply.reasoning,
                    reply=reply.text,
                    source=reply.source,
                    usage=reply.usage,
                    elapsed=reply.elapsed,
                    tool_calls=reply.tool_calls,
                )
            )

            convo.append({"role": "assistant", "content": reply.text})
            convo.append(
                {
                    "role": "user",
                    "content": (
                        f"# skills 内容：{skill_id}/{relative_path}\n\n{file_text}\n\n"
                        "如需继续读取其它文件，请单独输出一行 READ: 指令；"
                        "否则请直接给出最终答案。"
                    ),
                }
            )
        else:
            # 达到轮数上限仍未给出最终答案：再请求一次并要求直接作答
            convo.append(
                {
                    "role": "user",
                    "content": (
                        f"已达到最大读取轮数（{max_rounds}）。"
                        "请立即基于已获得的内容直接给出最终答案，不要再请求读取。"
                    ),
                }
            )
            reply = self._post_chat(
                url=url,
                headers=headers,
                messages=convo,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                seed=seed,
                images=images,
                extra_fields=extra_fields,
                retries=retries,
                timeout=timeout,
            )
            steps.append(
                RunStep(
                    index=len(steps) + 1,
                    action=f"达到最大读取轮数（{max_rounds}）后的强制收尾",
                    reasoning=reply.reasoning,
                    reply=reply.text,
                    source=reply.source,
                    is_final=True,
                    usage=reply.usage,
                    elapsed=reply.elapsed,
                    tool_calls=reply.tool_calls,
                )
            )
            final_text = reply.text

        trace = RunTrace(
            model=str(model),
            mode=f"skills 按需读取（渐进式披露，最多 {max_rounds} 轮）",
            input_skills=tuple(input_skills),
            steps=steps,
            reads=reads,
            injected_chars=injected,
            final_text=final_text,
        )
        return final_text, trace.render()

    def _run_builtin_tools(
        self, tool_calls, read_max_chars, remaining_chars, allowed_skills=None
    ) -> tuple:
        """执行模型请求的内置工具（后台声明，自动管理）。

        只执行白名单内的内置工具（当前仅 `read_skill`），绝不执行任意代码；
        未知工具名回注一条错误说明让模型自行纠正。

        allowed_skills 不为 None 时，只允许读取该集合内的 skills（来自本次
        skills管理器 的「自动」清单），清单外的 skills 一律拒绝。

        返回 (tool 消息列表, reads 明细, 注入字符数, 动作描述)。
        """
        allowed = _normalize_allowed_skills(allowed_skills)
        tool_messages = []
        reads = []
        injected = 0
        names = []
        for call in tool_calls:
            call = call if isinstance(call, dict) else {}
            call_id = str(call.get("id") or "")
            function = call.get("function")
            function = function if isinstance(function, dict) else {}
            name = str(function.get("name") or "").strip()
            names.append(name or "（未命名）")

            raw_args = function.get("arguments")
            if isinstance(raw_args, dict):
                args = raw_args
            else:
                try:
                    args = json.loads(str(raw_args or "{}"))
                except Exception:
                    args = {}
            args = args if isinstance(args, dict) else {}

            if name != BUILTIN_TOOL_READ_SKILL:
                tool_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call_id,
                        "content": (
                            f"错误：未知工具「{name}」。本节点只提供内置工具 "
                            f"{BUILTIN_TOOL_READ_SKILL}。"
                        ),
                    }
                )
                continue

            skill = str(args.get("skill") or "").strip()
            path = str(args.get("path") or "SKILL.md").strip() or "SKILL.md"
            if not skill:
                tool_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call_id,
                        "content": "错误：缺少 skill 参数（应为 skills 名称）。",
                    }
                )
                continue
            if allowed is not None and skill.casefold() not in allowed:
                tool_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call_id,
                        "content": (
                            f"错误：skills「{skill}」不在本次 skills 清单内，"
                            "只能读取清单中列出的 skills。"
                        ),
                    }
                )
                continue
            try:
                file_text = read_skill_file(skill, path, max_chars=read_max_chars)
            except Exception as exc:
                tool_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call_id,
                        "content": f"读取失败：{exc}",
                    }
                )
                continue
            if injected + len(file_text) > max(0, int(remaining_chars)):
                tool_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call_id,
                        "content": (
                            "已达到 skills 内容累计上限，未注入该文件。"
                            "请基于已获得的内容直接给出最终答案。"
                        ),
                    }
                )
                continue

            injected += len(file_text)
            reads.append((f"{skill}/{path}", skill, len(file_text)))
            tool_messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": (
                        f"# skills 内容：{skill}/{path}\n\n{file_text}\n\n"
                        "如需继续读取其它文件请继续调用 read_skill；"
                        "否则请直接给出最终答案。"
                    ),
                }
            )

        note = (
            f"调用内置工具 {'、'.join(names)}（{len(tool_calls)} 个）"
            "→ 已自动读取并回注"
        )
        return tool_messages, reads, injected, note

    @staticmethod
    def _merge_system_text(skills, system_prompt) -> str:
        """合并 skills 指导文本与系统提示词为一条 system 消息内容。

        - 两者都为空 → 返回空串（不发送 system 消息）
        - 仅其一非空 → 返回该内容
        - 都非空 → skills 在前，系统提示词在后，中间以分隔标题隔开
        """
        skills_text = str(skills).strip() if skills is not None else ""
        prompt_text = str(system_prompt).strip() if system_prompt is not None else ""
        if skills_text and prompt_text:
            return f"{skills_text}\n\n# 系统提示词\n\n{prompt_text}"
        return skills_text or prompt_text

    @staticmethod
    def _tensor_to_data_url(tensor, max_side=IMAGE_MAX_SIDE_DEFAULT, detail="auto"):
        """单张 [H,W,C] 0~1 RGB 张量 → image_url 对象 {url, detail?}。

        max_side > 0 时先把最长边等比缩放到不超过该值（缩小可显著降低 token）；
        detail 为 "auto" 时不发送 detail 字段，其余（low/high）显式写入。
        """
        if Image is None:
            raise RuntimeError(
                "自定义LLM：缺少 Pillow 库，请先安装 Pillow（pip install Pillow）"
            )
        arr = (
            tensor.detach().cpu().clamp(0.0, 1.0) * 255.0
        ).to(torch.uint8).numpy()
        img = Image.fromarray(arr, mode="RGB")
        limit = int(max_side or 0)
        if limit > 0 and max(img.size) > limit:
            scale = limit / float(max(img.size))
            new_size = (
                max(1, int(round(img.width * scale))),
                max(1, int(round(img.height * scale))),
            )
            img = img.resize(new_size, Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=95)
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        image_url = {"url": f"data:image/jpeg;base64,{b64}"}
        level = str(detail or "auto").strip().lower()
        if level in ("low", "high"):
            image_url["detail"] = level
        return image_url

    @staticmethod
    def _image_tensor_to_data_urls(image, max_side=IMAGE_MAX_SIDE_DEFAULT, detail="auto"):
        """IMAGE 张量 [B,H,W,C]（0~1 RGB）→ 逐帧 image_url 对象列表。"""
        if image.dim() == 3:
            image = image.unsqueeze(0)
        return [
            CustomLLMNode._tensor_to_data_url(frame, max_side=max_side, detail=detail)
            for frame in image
        ]


NODE_CLASS_MAPPINGS = {
    "CustomLLMNode": CustomLLMNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CustomLLMNode": "自定义LLM",
}

__all__ = [
    "CustomLLMNode",
    "LLMReply",
    "RunStep",
    "RunTrace",
    "EmptyLLMOutputError",
    "CONTEXT_TITLE",
    "input_skill_names",
    "skills_manifest_ids",
    "is_skills_manager_manifest",
    "build_response_format",
    "extract_tool_calls",
    "build_optional_fields",
    "session_key",
    "session_history",
    "remember_session_turn",
    "reset_session",
    "clear_sessions",
    "OUTPUT_FORMAT_TEXT",
    "OUTPUT_FORMAT_JSON_OBJECT",
    "OUTPUT_FORMAT_OPTIONS",
    "REASONING_EFFORT_OPTIONS",
    "REQUEST_TIMEOUT_DEFAULT",
    "REQUEST_TIMEOUT_MIN",
    "REQUEST_TIMEOUT_MAX",
    "EMPTY_OUTPUT_RETRIES",
    "EMPTY_OUTPUT_RETRIES_MAX",
    "IMAGE_MAX_SIDE_DEFAULT",
    "IMAGE_MAX_SIDE_MIN",
    "IMAGE_MAX_SIDE_MAX",
    "IMAGE_DETAIL_OPTIONS",
    "SESSION_MAX_ROUNDS_DEFAULT",
    "SESSION_MAX_ROUNDS_MAX",
    "BUILTIN_TOOL_READ_SKILL",
    "BUILTIN_TOOLS",
    "BUILTIN_TOOL_NAMES",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
