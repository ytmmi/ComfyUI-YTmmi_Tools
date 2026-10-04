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

任务家族（「模式」仅在「选择skills」= 自动 时生效，用于筛选清单）：
- H3-*：MiniMax H3 视频（排除 Qwen-Image 与 Anima 家族）；
- qwen-image-t2i / qwen-image-edit：Qwen-Image 2.1 图像提示词改写（各只列本家族 1 个）；
- Anima：Anima（CircleStone Labs × Comfy Org）二次元插画提示词家族，
  清单只列 id 以 anima 开头的 skills（11 个 Anima skills 同属该家族）。

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

# 模式选项：既用于选择 h3-prompt-writing 的参考资料，也用于按「任务家族」筛选
# 「自动」清单中列出的 skills（见 filter_registry_for_mode）。
#
# - auto：不筛选，列出全部 skills；h3-prompt-writing 同时提供两份指南；
# - H3-*：H3 视频任务家族（h3-prompt-writing + 8 个风格类 skills），
#   且按具体生成模式只提供对应的一份指南（ref2va 用全参考，其余用基础）；
# - qwen-image-*：Qwen-Image 2.1 图像提示词改写家族（文生图 / 图像编辑）；
# - Anima：Anima 二次元插画任务家族（11 个 anima-* skills）。
#
# 解析时同时兼容带前缀与不带前缀的旧写法（旧工作流仍可加载）。
MODE_PREFIX = "H3-"
MODE_AUTO = "auto"
MODE_QWEN_T2I = "qwen-image-t2i"
MODE_QWEN_EDIT = "qwen-image-edit"
MODE_ANIMA = "Anima"
MODE_OPTIONS = (
    MODE_AUTO,
    "H3-t2va",
    "H3-i2va",
    "H3-fl2va",
    "H3-l2va",
    "H3-ref2va",
    MODE_QWEN_T2I,
    MODE_QWEN_EDIT,
    MODE_ANIMA,
)

# Qwen-Image 提示词改写类 skills 的 id 标记（用于区分任务家族）
QWEN_IMAGE_MARKERS = ("qwen-image",)

# Anima 二次元插画类 skills 的 id 前缀（anima-prompt-format 等），
# 与 normalize_mode 的 anima- 前缀剥离保持一致（见 _canonical_id）。
ANIMA_SKILL_MARKERS = ("anima",)

# Anima 家族 skills 的固定「附加说明」：该家族统一采用「默认只出正面提示词」的输出
# 契约，负面提示词只在用户明确要求时才追加，因此不能沿用只输出单一交付物的通用强调。
ANIMA_FORMAT_NOTE = (
    "【输出要求】只输出 Anima 提示词正文本身：**默认只给正面提示词**，"
    "不要输出负面提示词、不要加 `Positive prompt` 之类的标题行、不要加 Markdown 代码块围栏。"
    "只有当用户明确要求负面词 / negative prompt，或表示自己那边没有设置负面词时，"
    "才追加第二段 `Negative prompt`。"
    "不要输出开头说明、结尾建议、解释、总结、前言或后记；"
    "不要把分辨率、宽高比、种子、CFG、步数、采样器或模型文件名写进提示词"
    "（用户明确索要参数建议时，才另起一段 `Suggested settings` 单列），"
    "也不要复述本条要求。"
)

# 各「任务家族」模式允许出现在「自动」清单中的 skills。
# 未在此表且非 H3-* 的模式（即 auto）不做筛选。
MODE_SKILL_ALLOWLIST = {
    MODE_QWEN_T2I: ("qwen-image-t2i-prompt",),
    MODE_QWEN_EDIT: ("qwen-image-edit-prompt",),
}

# 「选择skills」中的自动选项：选择后不预先加载任何 skills 正文，
# 改由下游节点（自定义LLM）与模型多轮按需读取（渐进式披露）
AUTO_SELECTION = "自动"

# 自动模式的协议标记：下游节点据此识别「按需读取」模式。
# 该标记必须出现在 skills 文本的最前面，且 skills id 不含尖括号，不会冲突。
AUTO_MARKER = "<<<YTMMI_SKILLS_AUTO>>>"

# 按需读取允许的文件扩展名（仅文本类指导文件，不执行任何内容）
READABLE_SUFFIXES = {".md", ".txt", ".yaml", ".yml", ".json"}

# 「附加说明」的默认强调提示词。
#
# 设计要点：**提示词正文不只指散文，JSON 等结构化结果同样是「正文」的一种形态**，
# 因此这里不重复规定输出格式（格式归所选 skills 的输出契约管），只做一件事——
# 抑制无关元素：开头的说明、结尾的建议、解释、总结、代码块围栏等。
# 这样一条强调即可通用于散文类与 JSON 类 skills，不必按格式分叉。
#
# 该默认值填充在「附加说明」文本框中，用户可自行删除或改写；前端 JS 在切换 skills
# 时会按新 skills 的默认值替换（用户自定义内容不动）。skills 也可在 SKILL.md
# front matter / meta.yaml 中用 `extra-note` 自行声明，优先级高于此默认值。
OUTPUT_ONLY_NOTE = (
    "【输出要求】只输出所选 skills 规定格式的最终内容本身（提示词正文、JSON 等，"
    "以 skills 的格式契约为准）；不要输出任何开头说明、结尾建议、解释、总结、前言、"
    "后记或 Markdown 代码块围栏，也不要复述本条要求。"
)

# 「提示词类」skills 的 id 识别标记：这类 skills 的产出是单一交付物（提示词正文或
# JSON），适合套用「只输出最终内容」的强调。
# 注意：风格类 skills（3d-animation-*、brand-promo-* 等）不在此列——它们会输出分镜、
# 制作方案，且可能包含澄清提问与方案选项，强加「只输出最终内容」会破坏其交互设计。
PROMPT_SKILL_MARKERS = ("prompt",)

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
    extra_note: str = ""


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
    # skills 可在元数据中自带默认「附加说明」（extra-note / extra_note）
    extra_note = (
        front.get("extra_note", "").strip()
        or front.get("extra-note", "").strip()
        or str(meta.get("extra_note", "")).strip()
        or str(meta.get("extra-note", "")).strip()
    )

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
    return (
        skill_id,
        description,
        display_name,
        version,
        tuple(dict.fromkeys(raw_tags)),
        extra_note,
    )


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
        skill_id, description, display_name, version, tags, extra_note = _metadata(
            skill_path
        )
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
                extra_note=extra_note,
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


def is_prompt_skill(skill_id) -> bool:
    """判断某个 skills 是否产出单一交付物（提示词正文 / JSON 等）。

    按 id 中的 `prompt` 标记识别（如 h3-prompt-writing、qwen-image-t2i-prompt），
    这类 skills 适合套用「只输出最终内容」的强调说明；风格类 skills（会输出分镜、
    制作方案，甚至含澄清提问）不适用。
    """
    value = str(skill_id or "").strip().casefold()
    if not value:
        return False
    return any(marker in value for marker in PROMPT_SKILL_MARKERS)


def is_anima_skill(skill_id) -> bool:
    """判断某个 skills 是否属于 Anima 二次元插画家族（id 以 anima 开头）。

    与 normalize_mode 的 anima- 前缀剥离保持一致：`Anima` 模式只列这一家族；
    `H3-*` 模式排除这一家族。Anima 家族统一采用「Positive prompt /
    Negative prompt」两段式输出契约，因此需要专属的「附加说明」。
    """
    value = str(skill_id or "").strip().casefold()
    if not value:
        return False
    return any(
        value == marker or value.startswith(f"{marker}-") or f"-{marker}-" in value
        for marker in ANIMA_SKILL_MARKERS
    )


def default_extra_note(skill_id=None, builtin_root=None, custom_root=None) -> str:
    """「附加说明」的默认值。

    取值优先级：
    1. skills 自身在 SKILL.md front matter / meta.yaml 中声明的 `extra-note`；
    2. Anima 家族 skills（id 含 `anima`）→ ANIMA_FORMAT_NOTE
       （两段式 Positive/Negative 契约，不能只输出单一交付物）；
    3. 产出单一交付物的 skills（id 含 `prompt`，含散文与 JSON 两类）→ OUTPUT_ONLY_NOTE；
    4. 「自动」→ OUTPUT_ONLY_NOTE（不预设具体 skills，用同一套通用强调）；
    5. 其余风格类 skills → 空（它们会输出分镜/制作方案，强加会误导模型）。

    注意：这里**不按输出格式分叉**——JSON 与散文都只是「正文」的不同形态，
    格式由所选 skills 的输出契约规定，本强调只负责抑制无关元素。
    """
    value = str(skill_id or "").strip()
    if not value or value == AUTO_SELECTION:
        return OUTPUT_ONLY_NOTE

    # 1. skills 自带声明优先
    found = False
    try:
        for spec in discover_skill_registry(builtin_root, custom_root):
            if spec.id.casefold() == value.casefold():
                found = True
                if spec.extra_note:
                    return spec.extra_note
                break
    except Exception:
        pass

    # 2. Anima 家族：两段式输出契约
    if is_anima_skill(value):
        return ANIMA_FORMAT_NOTE

    if not found:
        # 3. 未发现的 id：按通用「单一交付物」规则兜底（不静默丢强调）
        return OUTPUT_ONLY_NOTE if is_prompt_skill(value) else ""

    # 4. 产出单一交付物的 skills
    return OUTPUT_ONLY_NOTE if is_prompt_skill(value) else ""


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def normalize_mode(mode: str) -> str:
    """规范化模式取值：转小写并去掉 H3- 前缀，返回规范化的模式名。

    - `H3-t2va` → `t2va`（H3 生成模式：t2va/i2va/fl2va/l2va/ref2va）
    - `qwen-image-t2i` / `qwen-image-edit` → 原样保留
    - `Anima` / `anima-text2image` → `Anima`（家族模式，大小写与 anima- 子模式均兼容）
    - 空 → `auto`

    兼容带前缀（H3-t2va）、不带前缀（t2va）与带家族前缀（anima-text2image）
    等多种写法，旧工作流保存的值仍可用。
    """
    value = str(mode or "").strip().casefold()
    if value in (MODE_QWEN_T2I, MODE_QWEN_EDIT):
        return value
    if value == MODE_ANIMA.casefold() or value.startswith(f"{MODE_ANIMA.casefold()}-"):
        return MODE_ANIMA
    if value.startswith(MODE_PREFIX.casefold()):
        value = value[len(MODE_PREFIX):]
    return value or MODE_AUTO


def is_qwen_image_mode(mode: str) -> bool:
    """判断模式是否属于 Qwen-Image 提示词改写任务家族。"""
    return normalize_mode(mode) in (MODE_QWEN_T2I, MODE_QWEN_EDIT)


def is_anima_mode(mode: str) -> bool:
    """判断模式是否属于 Anima 二次元插画任务家族。"""
    return normalize_mode(mode) == MODE_ANIMA


def is_h3_mode(mode: str) -> bool:
    """判断模式是否属于 H3 视频任务家族（含 auto 之外的 H3-* 生成模式）。"""
    return normalize_mode(mode) in {"t2va", "i2va", "fl2va", "l2va", "ref2va"}


def filter_registry_for_mode(registry, mode: str):
    """按模式的任务家族筛选 skills 列表（auto 返回原列表）。

    任务家族筛选的意义：模式已表明任务类型时，清单里不应再出现无关家族的
    skills，避免模型路由到错误家族（如选 qwen-image-t2i 却读到 H3 视频 skills）。

    - qwen-image-t2i / qwen-image-edit：仅该家族对应 skills；
    - Anima：仅 Anima 家族（id 以 anima 开头的 11 个 skills）；
    - H3-*：H3 家族（h3-prompt-writing + 风格类 skills，排除 Qwen-Image 与 Anima）；
    - auto：不筛选，返回全部。
    """
    normalized = normalize_mode(mode)
    allow = MODE_SKILL_ALLOWLIST.get(normalized)
    if allow is not None:
        return tuple(spec for spec in registry if spec.id in allow)
    if is_anima_mode(normalized):
        return tuple(spec for spec in registry if is_anima_skill(spec.id))
    if is_h3_mode(normalized):
        # H3 家族：排除 Qwen-Image 与 Anima 两个图像提示词家族
        return tuple(
            spec
            for spec in registry
            if not any(m in spec.id.casefold() for m in QWEN_IMAGE_MARKERS)
            and not is_anima_skill(spec.id)
        )
    return tuple(registry)


def mode_family_hint(mode: str = MODE_AUTO) -> str:
    """返回当前模式的「任务家族」说明，用于自动清单提示模型按家族路由。

    auto 时返回空串（清单不做家族提示，保持中性）。
    """
    normalized = normalize_mode(mode)
    if normalized == MODE_AUTO:
        return ""
    if is_anima_mode(normalized):
        return (
            "当前模式：Anima（二次元插画）——本清单仅列出 Anima 家族的 skills，"
            "请只在本家族内选择；不要路由到 H3 视频或 Qwen-Image 家族的写法。"
            "动手前请**先读取共同基准** `anima-prompt-format/references/anima-prompt-baseline.md`"
            "（其中的「高杠杆规则」是全家族通用硬规则：主画师必选、权重用大数且加权标签总数 ≤4、"
            "取景对抗自然语言漂移、Hybrid 三层混合、动作与天气要有可见后果），"
            "再按需读取具体 skills 的 SKILL.md。"
        )
    if is_qwen_image_mode(normalized):
        return (
            "当前模式：Qwen-Image 提示词改写——本清单仅列出该家族的 skills，"
            "请只在本家族内选择；不要路由到 H3 视频或 Anima 家族的写法。"
        )
    if is_h3_mode(normalized):
        return (
            "当前模式：MiniMax H3 视频——本清单已排除 Qwen-Image 与 Anima 图像提示词"
            "家族的 skills；图像提示词需求请改用对应的图像家族模式。"
        )
    return ""


def resolve_effective_mode(skill_id, mode) -> str:
    """联动规则：**只有「选择skills」为「自动」时，「模式」才生效**。

    - `选择skills` = 自动 → 返回规范化后的模式（用于按任务家族筛选清单）；
    - `选择skills` = 具体 skills（或为空，将回退到默认 skills）→ 返回 `auto`，
      即模式被中和：不筛选，且加载该 skills 的全部参考资料。

    这样「模式」在语义上始终只描述「自动」模式下的任务家族；手动指定 skills 时
    由该 skills 自身决定输出，不受模式干扰。
    """
    if str(skill_id or "").strip() == AUTO_SELECTION:
        return normalize_mode(mode)
    return MODE_AUTO


def _h3_guides(mode: str) -> tuple:
    """h3-prompt-writing 的参考资料选择：全参考模式用 ref-en，其余用 base-en。"""
    normalized = normalize_mode(mode)
    if normalized == "ref2va":
        return ("ref-en.txt",)
    if normalized in {"t2va", "i2va", "fl2va", "l2va"}:
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


def skill_files(skill_id: str, builtin_root=None, custom_root=None) -> list:
    """列出某个 skills 目录下可被按需读取的文件（相对路径，正斜杠分隔）。"""
    root = _skill_path(skill_id, builtin_root, custom_root)
    files = []
    for path in sorted(root.glob("**/*"), key=lambda item: item.as_posix()):
        if not path.is_file() or path.suffix.lower() not in READABLE_SUFFIXES:
            continue
        resolved = path.resolve()
        # 安全校验：文件必须位于该 skills 目录内
        if root not in resolved.parents:
            continue
        files.append(path.relative_to(root).as_posix())
    return files


def read_skill_file(
    skill_id: str,
    relative_path: str,
    max_chars: int = MAX_CHARS_DEFAULT,
    builtin_root=None,
    custom_root=None,
) -> str:
    """按需读取某个 skills 内的单个文件（渐进式披露用）。

    仅允许读取该 skills 目录内的文本类文件，且拒绝路径穿越（如 ../）。
    """
    root = _skill_path(skill_id, builtin_root, custom_root)

    rel = str(relative_path or "").strip().replace("\\", "/").lstrip("/")
    if not rel:
        raise ValueError("skills管理器：未指定要读取的文件路径")

    candidate = (root / rel).resolve()
    # 安全校验：解析后的真实路径必须位于该 skills 目录内（防 ../ 穿越与符号链接越界）
    if candidate != root and root not in candidate.parents:
        raise PermissionError(
            f"skills管理器：拒绝读取 skills 目录之外的文件「{relative_path}」"
        )
    if not candidate.is_file():
        raise FileNotFoundError(
            f"skills管理器：skills「{skill_id}」中不存在文件「{relative_path}」"
        )
    if candidate.suffix.lower() not in READABLE_SUFFIXES:
        raise ValueError(
            f"skills管理器：不支持读取该类型文件「{relative_path}」"
            f"（仅支持 {'/'.join(sorted(READABLE_SUFFIXES))}）"
        )

    text = _read(candidate)
    limit = max(1, int(max_chars))
    if len(text) > limit:
        text = text[:limit] + f"\n\n…（文件超过 {limit} 字符，已截断）"
    return text


def build_skills_manifest(
    builtin_root=None,
    custom_root=None,
    max_chars: int = MAX_CHARS_DEFAULT,
    mode: str = MODE_AUTO,
) -> str:
    """构建「自动」模式下发给模型的 skills 清单与读取协议说明。

    只包含 skills 的 id 与描述（不含正文），由模型按需请求读取正文，
    实现渐进式披露（progressive disclosure）。

    模式为非 auto 时按「任务家族」筛选清单（见 filter_registry_for_mode），
    避免模型路由到无关家族的 skills。
    """
    registry = filter_registry_for_mode(
        discover_skill_registry(builtin_root, custom_root), mode
    )
    if not registry:
        return (
            f"{AUTO_MARKER}\n\n# skills\n\n"
            "（未发现任何 skills，请在 skills/ 或 custom_skills/ 下添加含 SKILL.md 的子目录）"
        )

    lines = [
        AUTO_MARKER,
        "",
        "# skills",
        "",
        "你可以使用以下 skills 来完成用户的请求。下方只列出 skills 的名称与用途，"
        "正文并未加载。",
        "",
    ]
    family_hint = mode_family_hint(mode)
    if family_hint:
        lines.extend([family_hint, ""])
    for spec in registry:
        label = f"（{spec.display_name}）" if spec.display_name else ""
        lines.append(f"- {spec.id}{label}: {spec.description}")
    lines.extend(
        [
            "",
            "# 按需读取协议",
            "",
            "当你需要某个 skills 的正文时，**单独输出一行**以下指令（不要加其它内容）：",
            "",
            "READ: <skills名称>",
            "",
            "当你需要读取该 skills 内的某个参考文件时，**单独输出一行**：",
            "",
            "READ: <skills名称>/<相对路径>",
            "",
            "每次只读取一个文件。系统会返回文件内容，然后你可以继续请求或直接给出最终答案。",
            "如果你已经可以直接完成用户的请求，就不需要读取任何 skills，直接输出结果即可。",
            "",
            f"读取内容单次上限：{max(1, int(max_chars))} 字符。",
        ]
    )
    return "\n".join(lines)


def is_auto_skills_text(text) -> bool:
    """判断 skills 文本是否为「自动」模式（渐进式披露）的清单。"""
    return isinstance(text, str) and text.lstrip().startswith(AUTO_MARKER)


# ── 后端路由：供前端「刷新skills」按钮更新下拉选项 ──────────────────────────

if (
    PromptServer is not None
    and web is not None
    and getattr(PromptServer, "instance", None) is not None
):

    @PromptServer.instance.routes.post("/ytmmi/skills/list")
    async def ytmmi_skills_list(request):
        """返回已发现的 skills 列表（id/描述/来源/版本/默认附加说明），供前端刷新下拉。

        前端据此在切换 skills 时套用对应的默认「附加说明」（用户自定义内容不动）。
        """
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
                            # 该 skills 对应的默认「附加说明」（可能为空）
                            "extra_note": default_extra_note(spec.id),
                        }
                        for spec in registry
                    ],
                    # 「自动」选项对应的通用强调说明
                    "auto_extra_note": OUTPUT_ONLY_NOTE,
                }
            )
        except Exception as exc:
            return web.json_response({"error": f"读取 skills 失败：{exc}"}, status=500)


class SkillsManagerNode:
    """skills管理器：管理并读取 skills/ 与 custom_skills/ 中的 skills，输出指导文本。"""

    CATEGORY = "YTmmi/utility"
    DESCRIPTION = 'skills管理器：管理并读取插件 skills/（内置）与 custom_skills/（自定义）目录中的 skills；选「自动」时只输出 skills 清单与读取协议，由自定义LLM与模型多轮按需读取（渐进式披露），选具体 skills 时输出其完整指导文本；模式可选 auto / H3-t2va / H3-i2va / H3-fl2va / H3-l2va / H3-ref2va / qwen-image-t2i / qwen-image-edit / Anima（非 auto 时按任务家族筛选自动清单）'

    @classmethod
    def INPUT_TYPES(cls):
        names = skill_names()
        # 「自动」置于首位：选择后不预先加载 skills 正文，交由下游节点与模型多轮按需读取
        options = [AUTO_SELECTION, *names]
        return {
            "required": {
                "选择skills": (
                    options,
                    {
                        "default": AUTO_SELECTION,
                        "tooltip": "选择「自动」时不预先加载任何 skills 正文，"
                        "由自定义LLM与模型多轮按需读取（渐进式披露，最省上下文），"
                        "此时「模式」生效（按任务家族筛选清单）；"
                        "选择具体 skills 则直接输出该 skills 的完整指导文本，"
                        "此时「模式」自动失效（不筛选、加载全部参考资料）；"
                        "点击节点上的「刷新skills」按钮可重新扫描",
                    },
                ),
                "模式": (
                    list(MODE_OPTIONS),
                    {
                        "default": MODE_AUTO,
                        "tooltip": "任务模式，仅在「选择skills」为「自动」时生效"
                        "（选具体 skills 时自动失效）。"
                        "auto：不筛选，列出全部 skills，h3-prompt-writing 同时提供基础与全参考两份指南；"
                        "H3-t2va / H3-i2va / H3-fl2va / H3-l2va / H3-ref2va：H3 视频家族"
                        "（H3-ref2va 只用全参考指南，其余只用基础指南）；"
                        "qwen-image-t2i / qwen-image-edit：Qwen-Image 2.1 图像提示词改写家族；"
                        "Anima：Anima（CircleStone Labs × Comfy Org）二次元插画家族"
                        "（只列 anima-* 的 11 个 skills）",
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
                        # 默认与「选择skills」的默认值（自动）对应：通用强调说明。
                        # 具体 skills 的强调说明由前端按 skills 自动套用（可删除或改写）。
                        "default": default_extra_note(AUTO_SELECTION),
                        "multiline": True,
                        "placeholder": "追加到 skills 文本末尾的补充说明（可清空）",
                        "tooltip": "默认已按所选 skills 填充对应的输出强调说明"
                        "（只输出最终内容、不要开头说明与结尾建议）；切换 skills 时前端自动替换，"
                        "也可手动删除或改写",
                    },
                ),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("skills", "skills名称", "skills目录")
    FUNCTION = "load_skills"
    OUTPUT_NODE = False
    OUTPUT_IS_LIST = (False, False, False)
    SEARCH_ALIASES = [
        "skills",
        "skills管理器",
        "技能",
        "skill manager",
        "h3 prompt",
        "qwen image prompt",
        "图像提示词",
    ]

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        """skills 目录内容变化时重新执行（返回目录签名，非固定值）。"""
        return skill_signature()

    def load_skills(self, **kwargs):
        # 中文控件名在 kwargs 中接收，内部变量保持英文
        skill_id = str(kwargs.get("选择skills", "") or "").strip()
        # 「模式」兼容旧键名「H3模式」（旧工作流保存的控件名）
        mode = str(
            kwargs.get("模式", kwargs.get("H3模式", MODE_AUTO)) or MODE_AUTO
        ).strip()
        include_references = bool(kwargs.get("包含参考文件", True))
        max_chars = int(kwargs.get("最大字符数", MAX_CHARS_DEFAULT))
        extra = str(kwargs.get("附加说明", "") or "").strip()

        # 联动：只有「选择skills」为「自动」时「模式」才生效；
        # 手动选具体 skills 时模式被中和（不筛选、加载该 skills 全部参考资料）。
        effective_mode = resolve_effective_mode(skill_id, mode)

        # 「自动」：只输出 skills 清单与读取协议，不加载任何正文（渐进式披露）。
        # 模式为非 auto 时按任务家族筛选清单。
        if skill_id == AUTO_SELECTION:
            text = build_skills_manifest(max_chars=max_chars, mode=effective_mode)
            if extra:
                text = f"{text}\n\n# 附加说明\n\n{extra}"
            return (text, AUTO_SELECTION, skill_catalog())

        if not skill_id:
            # 下拉为空（未选择）时回退到默认 skills，便于用户直接使用
            skill_id = default_skill_id()
        if not skill_id:
            raise ValueError(
                "skills管理器：未发现任何 skills，请在插件 skills/ 或 custom_skills/ 目录下"
                "添加包含 SKILL.md 的子目录"
            )

        text = skill_instructions(
            skill_id,
            mode=effective_mode,
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
    "AUTO_SELECTION",
    "AUTO_MARKER",
    "READABLE_SUFFIXES",
    "BUILTIN_SKILLS_DIR",
    "CUSTOM_SKILLS_DIR",
    "MODE_OPTIONS",
    "MODE_PREFIX",
    "MODE_AUTO",
    "MODE_QWEN_T2I",
    "MODE_QWEN_EDIT",
    "MODE_ANIMA",
    "QWEN_IMAGE_MARKERS",
    "ANIMA_SKILL_MARKERS",
    "MODE_SKILL_ALLOWLIST",
    "normalize_mode",
    "is_qwen_image_mode",
    "is_anima_mode",
    "is_h3_mode",
    "filter_registry_for_mode",
    "mode_family_hint",
    "resolve_effective_mode",
    "OUTPUT_ONLY_NOTE",
    "ANIMA_FORMAT_NOTE",
    "PROMPT_SKILL_MARKERS",
    "is_prompt_skill",
    "is_anima_skill",
    "default_extra_note",
    "MAX_CHARS_DEFAULT",
    "DEFAULT_SKILL_ID",
    "discover_skill_registry",
    "skill_names",
    "skill_catalog",
    "skill_signature",
    "skill_instructions",
    "skill_files",
    "read_skill_file",
    "build_skills_manifest",
    "is_auto_skills_text",
    "default_skill_id",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
