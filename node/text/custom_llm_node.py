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
- system_prompt：系统提示词（可选）
- prompt：用户提示词（要求、问题等）
- temperature：采样温度（0~2）
- max_tokens：生成的最大 token 数
- top_p：核采样（可选，默认 1.0）
- seed：随机种子（可选，-1 表示不设置，由服务端随机）
- response_format：输出格式 text / json_object（可选）

输出：模型返回的文本字符串。
"""

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

# 预设模型列表：默认不预设（空），模型列表完全由「获取模型」按钮从接口拉取。
# 之前预设的 gpt-4o/deepseek-chat 等 12 个模型已按用户要求移除。
DEFAULT_MODELS: list = []

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
    DESCRIPTION = '自定义LLM：调用任意 OpenAI 兼容格式的在线大模型接口，支持选择密钥储存器密钥、获取模型列表、温度/最大token/top_p/种子/JSON 输出'

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
                "最大token数": ("INT", {"default": 1024, "min": 1, "max": 32768}),
            },
            "optional": {
                "核采样（top_p）": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.05}),
                "种子": ("INT", {"default": -1, "min": -1, "max": 0x7FFFFFFF}),
                "输出格式": (["text", "json_object"], {"default": "text"}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("输出文本",)
    FUNCTION = "chat"
    OUTPUT_NODE = False
    OUTPUT_IS_LIST = (False,)
    SEARCH_ALIASES = ["llm", "chat", "大模型", "ai对话", "openai"]

    def chat(
        self,
        **kwargs,
    ):
        # 中文控件名在 kwargs 中接收，内部变量保持英文
        model = kwargs.get("选择模型", "")
        system_prompt = kwargs.get("系统提示词", "")
        prompt = kwargs.get("提示词", "")
        temperature = kwargs.get("温度", 0.7)
        max_tokens = kwargs.get("最大token数", 1024)
        top_p = kwargs.get("核采样（top_p）", 1.0)
        seed = kwargs.get("种子", -1)
        response_format = kwargs.get("输出格式", "text")

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
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        messages = []
        if str(system_prompt).strip():
            messages.append({"role": "system", "content": str(system_prompt)})
        messages.append({"role": "user", "content": str(prompt)})

        payload = {
            "model": str(model),
            "messages": messages,
            "temperature": float(temperature),
            "max_tokens": int(max_tokens),
            "top_p": float(top_p),
        }
        if int(seed) >= 0:
            payload["seed"] = int(seed)
        if response_format == "json_object":
            payload["response_format"] = {"type": "json_object"}

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=120)
        except Exception as exc:
            raise RuntimeError(f"自定义LLM：请求失败（{exc}）") from exc

        if response.status_code != 200:
            detail = response.text[:500] if response.text else "无响应内容"
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
        content = choices[0].get("message", {}).get("content", "")
        return (content,)


NODE_CLASS_MAPPINGS = {
    "CustomLLMNode": CustomLLMNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CustomLLMNode": "自定义LLM",
}

__all__ = [
    "CustomLLMNode",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
