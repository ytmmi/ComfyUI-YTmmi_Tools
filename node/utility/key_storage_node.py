# 密钥储存器
"""密钥储存器节点。

加密保存 API 密钥与接口地址，供其他节点（如自定义LLM）按名称读取。

使用方式：
1. 在「名称」「密钥」「接口地址」中填写内容，点击节点上的「保存」按钮，
   密钥将加密写入插件目录下的存储文件；
2. 「已保存名称」下拉菜单列出已保存的名称（保存后自动刷新），选择后
   自动回填「名称」；
3. 执行节点（名称已填）即输出该名称对应的密钥与接口地址。

加密方案：
- 以系统用户名的前 5 位为密码，拼接固定盐后经 SHA-256 派生 Fernet 密钥；
- 全部密钥数据整体加密（cryptography.fernet）后写入 data/keys_storage.dat；
- 插件目录被直接复制到其他机器后，因用户名不同无法解密，避免密钥明文泄露。
"""

import base64
import getpass
import hashlib
import json
from pathlib import Path

try:
    from cryptography.fernet import Fernet
except Exception:
    Fernet = None

try:
    from server import PromptServer
    from aiohttp import web
except Exception:
    PromptServer = None
    web = None

# 存储文件：插件根目录 / data / keys_storage.dat
# （本文件位于 node/utility/ 下，parents[2] 为插件根目录）
_DATA_DIR = Path(__file__).resolve().parents[2] / "data"
_STORAGE_FILE = _DATA_DIR / "keys_storage.dat"

# 派生盐（与密码共同参与密钥派生）
_PASSWORD_SALT = "ytmmi-key-vault-v1"


def _derive_fernet_key() -> bytes:
    """由系统用户名前 5 位派生 Fernet 密钥。"""
    password = (getpass.getuser()[:5] + _PASSWORD_SALT).encode("utf-8")
    return base64.urlsafe_b64encode(hashlib.sha256(password).digest())


def load_vault() -> dict:
    """读取并解密密钥库；文件不存在或密码不正确时返回空库。"""
    if Fernet is None or not _STORAGE_FILE.exists():
        return {}
    try:
        fernet = Fernet(_derive_fernet_key())
        raw = fernet.decrypt(_STORAGE_FILE.read_bytes())
        return json.loads(raw.decode("utf-8"))
    except Exception:
        # 解密失败（文件损坏/密码不匹配）视为空库，不泄露任何数据
        return {}


def save_vault(data: dict) -> None:
    """将密钥库加密后写入存储文件。"""
    if Fernet is None:
        raise RuntimeError("密钥储存器：缺少 cryptography 库，请先安装 cryptography")
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    fernet = Fernet(_derive_fernet_key())
    token = fernet.encrypt(json.dumps(data, ensure_ascii=False).encode("utf-8"))
    _STORAGE_FILE.write_bytes(token)


def vault_names() -> list:
    """返回密钥库中的名称列表（排序）。"""
    return sorted(load_vault().keys())


if (
    PromptServer is not None
    and web is not None
    and getattr(PromptServer, "instance", None) is not None
):

    @PromptServer.instance.routes.post("/ytmmi/keys/save")
    async def ytmmi_keys_save(request):
        """保存密钥（前端「保存」按钮调用）。"""
        try:
            body = await request.json()
        except Exception:
            return web.json_response({"error": "请求体不是有效 JSON"}, status=400)

        name = str(body.get("名称", "")).strip()
        key = str(body.get("密钥", "")).strip()
        base_url = str(body.get("接口地址", "")).strip()
        if not name:
            return web.json_response({"error": "请输入名称"}, status=400)
        if not key:
            return web.json_response({"error": "请输入密钥"}, status=400)
        if not base_url:
            return web.json_response({"error": "请输入接口地址"}, status=400)

        try:
            data = load_vault()
            data[name] = {"密钥": key, "接口地址": base_url}
            save_vault(data)
        except Exception as exc:
            return web.json_response({"error": f"保存失败：{exc}"}, status=500)
        return web.json_response({"names": sorted(data.keys())})

    @PromptServer.instance.routes.post("/ytmmi/keys/list")
    async def ytmmi_keys_list(request):
        """返回已保存的名称列表（前端刷新下拉菜单用）。"""
        return web.json_response({"names": vault_names()})

    @PromptServer.instance.routes.post("/ytmmi/keys/get")
    async def ytmmi_keys_get(request):
        """按名称返回明文密钥与接口地址。

        供自定义LLM的「选择密钥」下拉回填 API密钥/接口地址、
        以及「获取模型」按钮直接使用密钥库中的凭据。
        """
        try:
            body = await request.json()
        except Exception:
            return web.json_response({"error": "请求体不是有效 JSON"}, status=400)

        name = str(body.get("名称", "")).strip()
        if not name:
            return web.json_response({"error": "请输入名称"}, status=400)

        data = load_vault()
        if name not in data:
            return web.json_response(
                {"error": f"未找到已保存的「{name}」，请先在密钥储存器中保存"}, status=404
            )
        return web.json_response(data[name])


class KeyStorageNode:
    """密钥储存器：加密保存密钥并按名称输出。"""

    CATEGORY = "YTmmi/utility"
    DESCRIPTION = '密钥储存器：加密保存 API 密钥与接口地址（以系统用户名前 5 位派生密钥加密存储），按名称输出密钥与接口地址'

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "名称": ("STRING", {"default": "", "multiline": False, "placeholder": "输入名称或选择下方密钥"}),
                "密钥": ("STRING", {"default": "", "multiline": False, "placeholder": "sk-..."}),
                "接口地址": (
                    "STRING",
                    {"default": "https://api.openai.com/v1", "multiline": False},
                ),
            },
            "optional": {
                # 正式下拉：列出已保存密钥名称，选择后由前端回填「名称」
                "选择密钥": (vault_names() or [""], {"default": ""}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("密钥", "接口地址")
    FUNCTION = "load"
    OUTPUT_NODE = False
    OUTPUT_IS_LIST = (False, False)
    SEARCH_ALIASES = ["key storage", "密钥", "vault", "凭据", "密钥存储"]

    def load(self, **kwargs):
        name = str(kwargs.get("名称") or kwargs.get("选择密钥") or "").strip()
        if not name:
            raise ValueError("密钥储存器：请输入或选择名称")
        data = load_vault()
        if name not in data:
            raise ValueError(f"密钥储存器：未找到已保存的「{name}」，请先点击「保存」")
        entry = data[name]
        return (entry.get("密钥", ""), entry.get("接口地址", ""))


NODE_CLASS_MAPPINGS = {
    "KeyStorageNode": KeyStorageNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "KeyStorageNode": "密钥储存器",
}

__all__ = [
    "KeyStorageNode",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
