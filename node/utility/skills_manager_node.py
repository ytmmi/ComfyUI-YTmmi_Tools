# skills管理器
"""skills管理器节点。

管理并读取插件根目录下的 skills/（内置）与 custom_skills/（自定义）目录中的
skills，输出所选 skills 的完整指导文本，供「自定义LLM」等节点的 skills 输入
接口使用。

skills 目录约定（与上游 ComfyUI_Qwen_H3_Prompt 保持一致）：
- 每个 skills 为 skills 根目录下的一个子目录，目录名即 skills id；
- 子目录中必须包含 SKILL.md（skills 正文）；
- SKILL.md 顶部可选 YAML front matter：name / description / display_name / version / tags；
- 子目录可选 meta.yaml：提供 display_name_en/zh、summary_en、desc_en、version、tags 等元数据；
- references/ 子目录下的 .md / .txt 作为参考资料一并读取（受「最大字符数」限制）。

发现规则：
- skills id 只能包含小写字母、数字、点、下划线与连字符，且不能为 auto；
- 内置 skills 优先，custom_skills/ 中同 id 的 skills 不覆盖内置；
- skills 内容仅作为模型提示词指导，不会执行其中声明的脚本、工具或网络调用。

输出：
- skills：所选 skills 的完整指导文本（含参考资料），可直接接入自定义LLM的 skills 接口；
- skills名称：所选 skills 的 id；
- skills目录：全部已发现 skills 的清单（id: 描述），便于人工查看与手动选择。
"""

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

try:
    from server import PromptServer
    from aiohttp import web
except Exception:
    PromptServer = None
    web = None

# 插件根目录（本文件位于 node/utility/ 下，parents[2] 为插件根目录）
_PLUGIN_ROOT = Path(__file__).resolve().parents[2]

# 内置 skills 目录（随插件分发）与自定义 skills 目录（用户自行添加）
BUILTIN_SKILLS_DIR = _PLUGIN_ROOT / "skills"
CUSTOM_SKILLS_DIR = _PLUGIN_ROOT / "custom_skills"

# skills id 命名规则：小写字母/数字开头，允许小写字母、数字、点、下划线、连字符
SKILL_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")

# 参考资料允许的扩展名
REFERENCE_SUFFIXES = {".md", ".txt"}

# 优先选用的默认 skills（与上游默认一致）
DEFAULT_SKILL_ID = "h3-prompt-writing"

# H3 模式选项：auto 时同时提供基础模式与全参考模式两份指南
MODE_OPTIONS = ("auto", "t2va", "i2va", "fl2va", "l2va", "ref2va")

# 读取参考资料时的默认字符上限
MAX_CHARS_DEFAULT = 72000


@dataclass(frozen=True)
class SkillSpec:
    """一个已发现的 skills（仅提示词指导，可安全读取本地文件）。"""

    id: str
    path: Path
    description: str
    source: str
    display_name: str = ""
    version: str = ""
    tags: tuple = ()


# ── 元数据解析（仅解析发现所需的少量 YAML 子集，避免引入额外依赖）──────────


def _scalar(value: str) -> str:
    """去除标量两侧引号。"""
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _list_values(value) -> tuple:
    """将 YAML 列表/逗号串/单值统一为字符串元组。"""
    if isinstance(value, tuple):
        return tuple(item for item in value if str(item).strip())
    if not isinstance(value, str) or not value.strip():
        return ()
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1]
        return tuple(
            item for item in (_scalar(part) for part in value.split(",")) if item.strip()
        )
    return (value,)


def _front_matter(path: Path) -> dict:
    """读取 SKILL.md 顶部的 YAML front matter（仅发现所需的标量与块标量）。"""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return {}
    if not lines or lines[0].strip() != "---":
        return {}

    end = next(
        (
            index
            for index in range(1, len(lines))
            if lines[index].strip() == "---" and not lines[index].startswith((" ", "\t"))
        ),
        None,
    )
    if end is None:
        return {}

    values: dict = {}
    index = 1
    while index < end:
        match = re.match(
            r"^(?P<indent>\s*)(?P<key>[A-Za-z0-9_-]+):\s*(?P<value>.*)$", lines[index]
        )
        if not match or match.group("indent"):
            index += 1
            continue

        key = match.group("key").replace("-", "_").casefold()
        value = match.group("value").strip()
        if value.startswith(("|", ">")):
            # 块标量：收集后续缩进行，按 | / > 语义拼接
            block = []
            cursor = index + 1
            while cursor < end:
                candidate = lines[cursor]
                if candidate.strip() and not candidate.startswith((" ", "\t")):
                    break
                block.append(candidate)
                cursor += 1
            non_empty = [line for line in block if line.strip()]
            indent = min(
                (len(line) - len(line.lstrip()) for line in non_empty), default=0
            )
            block = [line[indent:] if line.strip() else "" for line in block]
            values[key] = ("\n" if value.startswith("|") else " ").join(block).strip()
            index = cursor
            continue
        if value:
            values[key] = _scalar(value)
        index += 1
    return values


def _meta_yaml(path: Path) -> dict:
    """读取 meta.yaml 中的标量与简单列表元数据。"""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return {}

    values: dict = {}
    index = 0
    while index < len(lines):
        match = re.match(r"^(?P<key>[A-Za-z0-9_-]+):\s*(?P<value>.*)$", lines[index])
        if not match:
            index += 1
            continue
        key = match.group("key").replace("-", "_").casefold()
        value = match.group("value").strip()
        if value:
            values[key] = _scalar(value)
            index += 1
            continue

        # 值为空 → 尝试读取其后的 "- 项" 列表
        items = []
        cursor = index + 1
        while cursor < len(lines):
            item = re.match(r"^\s*-\s*(.+?)\s*$", lines[cursor])
            if not item:
                break
            items.append(_scalar(item.group(1)))
            cursor += 1
        if items:
            values[key] = tuple(items)
        index = cursor
    return values


def _metadata(skill_root: Path) -> tuple:
    """汇总 SKILL.md front matter 与 meta.yaml 的元数据。"""
    front = _front_matter(skill_root / "SKILL.md")
    meta = _meta_yaml(skill_root / "meta.yaml")

    skill_id = front.get("name", "").strip() or skill_root.name
    description = (
        front.get("description", "").strip()
        or str(meta.get("summary_en", "")).strip()
        or str(meta.get("summary_cn", "")).strip()
        or str(meta.get("desc_en", "")).strip()
        or str(meta.get("desc_cn", "")).strip()
        or skill_id
    )
    description = " ".join(description.split())
    display_name = (
        front.get("display_name", "").strip()
        or front.get("display_name_en", "").strip()
        or front.get("display_name_zh", "").strip()
        or str(meta.get("display_name_en", "")).strip()
        or str(meta.get("display_name_zh", "")).strip()
    )
    version = front.get("version", "").strip() or str(meta.get("version", "")).strip()

    raw_tags = []
    for values in (
        _list_values(front.get("tags")),
        _list_values(front.get("tag_en")),
        _list_values(front.get("tag_cn")),
        _list_values(meta.get("tags")),
        _list_values(meta.get("tag_en")),
        _list_values(meta.get("tag_cn")),
        _list_values(meta.get("complete_tags_en")),
        _list_values(meta.get("complete_tags_cn")),
    ):
        raw_tags.extend(values)
    return skill_id, description, display_name, version, tuple(dict.fromkeys(raw_tags))


# ── skills 发现 ────────────────────────────────────────────────────────────


def _discover_skills(root: Path, source: str) -> list:
    """扫描单个 skills 根目录，返回合法的 SkillSpec 列表。"""
    if not root.is_dir():
        return []
    resolved_root = root.resolve()
    discovered = []
    for candidate in sorted(root.iterdir(), key=lambda item: item.name.casefold()):
        if not candidate.is_dir():
            continue
        skill_path = candidate.resolve()
        # 安全校验：skills 必须直接位于根目录下，防止符号链接越界
        if skill_path.parent != resolved_root:
            continue
        skill_file = skill_path / "SKILL.md"
        if not skill_file.is_file() or skill_file.resolve().parent != skill_path:
            continue
        skill_id, description, display_name, version, tags = _metadata(skill_path)
        if not SKILL_ID_RE.fullmatch(skill_id) or skill_id == "auto":
            continue
        discovered.append(
            SkillSpec(
                id=skill_id,
                path=skill_path,
                description=description,
                source=source,
                display_name=display_name,
                version=version,
                tags=tags,
            )
        )
    return discovered


def _dir_signature(root: Path) -> tuple:
    """目录签名：用于缓存失效与 IS_CHANGED（skills 变更后自动重新发现）。"""
    if not root.is_dir():
        return ()
    entries = []
    for child in sorted(root.iterdir(), key=lambda item: item.name.casefold()):
        if not child.is_dir():
            continue
        stamps = []
        for filename in ("SKILL.md", "meta.yaml"):
            path = child / filename
            try:
                stat = path.stat()
                stamps.append((filename, stat.st_mtime_ns, stat.st_size))
            except OSError:
                stamps.append((filename, None, None))
        entries.append((child.name, tuple(stamps)))
    return tuple(entries)


def skill_signature(builtin_root=None, custom_root=None) -> str:
    """返回两个 skills 根目录的内容签名（目录结构 + 关键文件 mtime/大小）。"""
    builtin = Path(builtin_root) if builtin_root is not None else BUILTIN_SKILLS_DIR
    custom = Path(custom_root) if custom_root is not None else CUSTOM_SKILLS_DIR
    payload = repr((_dir_signature(builtin), _dir_signature(custom)))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# 发现结果缓存：{根目录对: (签名, registry)}，签名变化时自动重建
_REGISTRY_CACHE: dict = {}


def discover_skill_registry(builtin_root=None, custom_root=None) -> tuple:
    """发现全部 skills：内置优先，custom_skills 中同 id 不覆盖内置。"""
    builtin = Path(builtin_root) if builtin_root is not None else BUILTIN_SKILLS_DIR
    custom = Path(custom_root) if custom_root is not None else CUSTOM_SKILLS_DIR

    cache_key = (str(builtin), str(custom))
    signature = skill_signature(builtin, custom)
    cached = _REGISTRY_CACHE.get(cache_key)
    if cached is not None and cached[0] == signature:
        return cached[1]

    registry = []
    seen = set()
    for spec in (*_discover_skills(builtin, "builtin"), *_discover_skills(custom, "custom")):
        key = spec.id.casefold()
        if key in seen:
            continue
        seen.add(key)
        registry.append(spec)

    result = tuple(registry)
    _REGISTRY_CACHE[cache_key] = (signature, result)
    return result


def skill_names(builtin_root=None, custom_root=None) -> list:
    """返回全部 skills id 列表。"""
    return [spec.id for spec in discover_skill_registry(builtin_root, custom_root)]


def skill_catalog(builtin_root=None, custom_root=None) -> str:
    """返回 skills 清单文本（每行「- id: 描述」），供查看与手动选择。"""
    registry = discover_skill_registry(builtin_root, custom_root)
    if not registry:
        return "（未发现任何 skills，请在 skills/ 或 custom_skills/ 下添加含 SKILL.md 的子目录）"
    return "\n".join(f"- {spec.id}: {spec.description}" for spec in registry)


def default_skill_id(builtin_root=None, custom_root=None) -> str:
    """默认选中的 skills id：优先 h3-prompt-writing，否则第一个。"""
    names = skill_names(builtin_root, custom_root)
    if DEFAULT_SKILL_ID in names:
        return DEFAULT_SKILL_ID
    return names[0] if names else ""


def _skill_spec(skill_id: str, builtin_root=None, custom_root=None) -> SkillSpec:
    """按 id 查找 SkillSpec（大小写不敏感）。"""
    key = str(skill_id).strip().casefold()
    for spec in discover_skill_registry(builtin_root, custom_root):
        if spec.id.casefold() == key:
            return spec
    raise ValueError(
        f"skills管理器：未找到 skills「{skill_id}」，请确认该 skills 位于 skills/ 或 custom_skills/ 目录下"
    )


def _skill_path(skill_id: str, builtin_root=None, custom_root=None) -> Path:
    """返回 skills 根目录，并校验其位于允许的 skills 根目录之内。"""
    spec = _skill_spec(skill_id, builtin_root, custom_root)
    root = spec.path.resolve()
    allowed_roots = (
        (Path(builtin_root) if builtin_root is not None else BUILTIN_SKILLS_DIR).resolve(),
        (Path(custom_root) if custom_root is not None else CUSTOM_SKILLS_DIR).resolve(),
    )
    if not any(root.parent == allowed for allowed in allowed_roots):
        raise FileNotFoundError(
            f"skills管理器：skills「{spec.id}」不在允许的 skills 目录内"
        )
    skill_file = root / "SKILL.md"
    if not root.is_dir() or not skill_file.is_file() or skill_file.resolve().parent != root:
        raise FileNotFoundError(f"skills管理器：skills「{spec.id}」缺少 SKILL.md")
    return root


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _h3_guides(mode: str) -> tuple:
    """h3-prompt-writing 的参考资料选择：全参考模式用 ref-en，其余用 base-en。"""
    if mode == "ref2va":
        return ("ref-en.txt",)
    if mode in {"t2va", "i2va", "fl2va", "l2va"}:
        return ("base-en.txt",)
    return ("base-en.txt", "ref-en.txt")


def skill_instructions(
    skill_id: str,
    mode: str = "auto",
    max_chars: int = MAX_CHARS_DEFAULT,
    include_references: bool = True,
    builtin_root=None,
    custom_root=None,
) -> str:
    """组装所选 skills 的完整指导文本（SKILL.md + 参考资料，受字符上限约束）。"""
    spec = _skill_spec(skill_id, builtin_root, custom_root)
    root = _skill_path(spec.id, builtin_root, custom_root)

    parts = [f"# 已选 skills：{spec.id}\n\n{_read(root / 'SKILL.md')}"]
    used = len(parts[0])
    if not include_references:
        return parts[0]

    if spec.id == DEFAULT_SKILL_ID:
        # 官方 H3 提示词写作 skills：按模式提供对应指南
        candidates = [root / "references" / name for name in _h3_guides(mode)]
    else:
        references_dir = root / "references"
        candidates = (
            sorted(
                (
                    path
                    for path in references_dir.glob("**/*")
                    if path.is_file() and path.suffix.lower() in REFERENCE_SUFFIXES
                ),
                key=lambda path: path.as_posix(),
            )
            if references_dir.is_dir()
            else []
        )

    for path in candidates:
        if not path.is_file():
            continue
        resolved = path.resolve()
        # 安全校验：参考资料必须位于该 skills 目录内
        if root not in resolved.parents:
            continue
        addition = (
            f"# skills 参考资料：{path.relative_to(root).as_posix()}\n\n{_read(resolved)}"
        )
        if used + len(addition) > max(1, int(max_chars)):
            break
        parts.append(addition)
        used += len(addition)

    return "\n\n".join(parts)


# ── 后端路由：供前端「刷新skills」按钮更新下拉选项 ──────────────────────────

if (
    PromptServer is not None
    and web is not None
    and getattr(PromptServer, "instance", None) is not None
):

    @PromptServer.instance.routes.post("/ytmmi/skills/list")
    async def ytmmi_skills_list(request):
        """返回已发现的 skills 列表（id/描述/来源/版本），供前端刷新下拉。"""
        try:
            registry = discover_skill_registry()
            return web.json_response(
                {
                    "names": [spec.id for spec in registry],
                    "skills": [
                        {
                            "id": spec.id,
                            "description": spec.description,
                            "source": spec.source,
                            "display_name": spec.display_name,
                            "version": spec.version,
                            "tags": list(spec.tags),
                        }
                        for spec in registry
                    ],
                }
            )
        except Exception as exc:
            return web.json_response({"error": f"读取 skills 失败：{exc}"}, status=500)


class SkillsManagerNode:
    """skills管理器：管理并读取 skills/ 与 custom_skills/ 中的 skills，输出指导文本。"""

    CATEGORY = "YTmmi/utility"
    DESCRIPTION = 'skills管理器：管理并读取插件 skills/（内置）与 custom_skills/（自定义）目录中的 skills，输出所选 skills 的完整指导文本，供自定义LLM等节点的 skills 输入接口使用'

    @classmethod
    def INPUT_TYPES(cls):
        names = skill_names()
        return {
            "required": {
                "选择skills": (
                    names or [""],
                    {
                        "default": default_skill_id(),
                        "tooltip": "skills/ 与 custom_skills/ 中已发现的 skills；"
                        "点击节点上的「刷新skills」按钮可重新扫描",
                    },
                ),
                "H3模式": (
                    list(MODE_OPTIONS),
                    {
                        "default": "auto",
                        "tooltip": "h3-prompt-writing 的参考资料选择：auto 同时提供基础模式与全参考模式指南；"
                        "ref2va 只用全参考指南；其余模式只用基础指南",
                    },
                ),
                "包含参考文件": (
                    "BOOLEAN",
                    {"default": True, "tooltip": "是否一并读取 skills 的 references/ 参考资料"},
                ),
                "最大字符数": (
                    "INT",
                    {
                        "default": MAX_CHARS_DEFAULT,
                        "min": 1000,
                        "max": 400000,
                        "step": 1000,
                        "tooltip": "指导文本的字符上限，超出后不再追加参考资料",
                    },
                ),
            },
            "optional": {
                "附加说明": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "placeholder": "追加到 skills 文本末尾的补充说明（可选）",
                    },
                ),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("skills", "skills名称", "skills目录")
    FUNCTION = "load_skills"
    OUTPUT_NODE = False
    OUTPUT_IS_LIST = (False, False, False)
    SEARCH_ALIASES = ["skills", "skills管理器", "技能", "skill manager", "h3 prompt"]

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        """skills 目录内容变化时重新执行（返回目录签名，非固定值）。"""
        return skill_signature()

    def load_skills(self, **kwargs):
        # 中文控件名在 kwargs 中接收，内部变量保持英文
        skill_id = str(kwargs.get("选择skills", "") or "").strip()
        mode = str(kwargs.get("H3模式", "auto") or "auto").strip()
        include_references = bool(kwargs.get("包含参考文件", True))
        max_chars = int(kwargs.get("最大字符数", MAX_CHARS_DEFAULT))
        extra = str(kwargs.get("附加说明", "") or "").strip()

        if not skill_id:
            # 下拉为空时回退到默认 skills，便于用户直接使用
            skill_id = default_skill_id()
        if not skill_id:
            raise ValueError(
                "skills管理器：未发现任何 skills，请在插件 skills/ 或 custom_skills/ 目录下"
                "添加包含 SKILL.md 的子目录"
            )

        text = skill_instructions(
            skill_id,
            mode=mode,
            max_chars=max_chars,
            include_references=include_references,
        )
        if extra:
            text = f"{text}\n\n# 附加说明\n\n{extra}"

        return (text, _skill_spec(skill_id).id, skill_catalog())


NODE_CLASS_MAPPINGS = {
    "SkillsManagerNode": SkillsManagerNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SkillsManagerNode": "skills管理器",
}

__all__ = [
    "SkillsManagerNode",
    "SkillSpec",
    "BUILTIN_SKILLS_DIR",
    "CUSTOM_SKILLS_DIR",
    "MODE_OPTIONS",
    "MAX_CHARS_DEFAULT",
    "DEFAULT_SKILL_ID",
    "discover_skill_registry",
    "skill_names",
    "skill_catalog",
    "skill_signature",
    "skill_instructions",
    "default_skill_id",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
