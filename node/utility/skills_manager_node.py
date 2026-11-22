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

任务家族（「模式」仅在「选择skills」= 自动 时生效，用于筛选清单；
除 Auto 外每个选项都是首字母大写的 TitleCase 家族名）：
- H3-video：MiniMax H3 视频（五个旧生成模式合并为一档，排除各图像家族）；
- Qwen-image-t2i / Qwen-image-edit：Qwen-Image 2.1 图像提示词改写（各只列本家族 1 个）；
- Anima：Anima（CircleStone Labs × Comfy Org）二次元插画提示词家族，
  清单只列 id 以 anima 开头的 skills（12 个 Anima skills 同属该家族）；
- Moss：MOSS-Image 图像提示词增强家族（moss-image-prompt-enhancer：
  caption / 像素级 Layout 两种交付物 + 本地编译脚本，不生成图片）；
- Krea2：Krea 2（Krea-2 / K2，单流 DiT + 自然语言 caption）图像提示词家族，
  清单只列 id 以 krea2 开头的 skills（基础写作 / 二次元 / 编辑级长文三支）；
- H3-image：MiniMax-H3-Image（33.1B DiT，6 步无 CFG，无负面词，约 16 MP）图像家族，
  清单只列 id 以 h3-image 开头的 skills（文生图 / 参考图编辑两支）；
- Z-image：Z-Image（造相，通义 6B S3-DiT）图像家族，清单只列 id 以 z-image 开头的
  skills（基础写作 / 双语文字版式两支）。Turbo 8 步无 CFG、Base 30–50 步 CFG 3–5。

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
# **命名约定（首字母大写）**：除保留字 `Auto` 外，每个选项都是 TitleCase 家族名：
# `Auto` / `H3-video` / `Qwen-image-t2i` / `Qwen-image-edit` / `Anima` / `Moss` / `Krea2`。
#
# - Auto：不筛选，列出全部 skills；h3-prompt-writing 同时提供两份指南；
# - H3-video：H3 视频任务家族的**合并档**（原本 t2va/i2va/fl2va/l2va/ref2va 五个
#   生成模式合并为一项），列出 h3-prompt-writing + 8 个风格类 skills，并把
#   基础指南与全参考指南**两份一起**加载（合并后不再按生成模式二选一）；
# - Qwen-image-t2i / Qwen-image-edit：Qwen-Image 2.1 图像提示词改写家族；
# - Anima：Anima 二次元插画任务家族（12 个 anima-* skills）；
# - Moss：MOSS-Image 图像提示词增强家族（默认交付 JSON Layout：全局描述 + 局部方框）；
# - Krea2：Krea 2 自然语言 caption 家族（基础写作 / 二次元 / 编辑级长文）；
# - H3-image：MiniMax-H3-Image 图像家族（文生图 / 参考图编辑）；
# - Z-image：Z-Image（造相，通义 6B S3-DiT）图像家族（基础写作 / 双语文字版式）。
#
# 另外，id 以 image- 开头的「图像通用 skills」（构图 / 配色等与模型无关的图像工艺）
# **在所有模式下都会并入自动清单**（见 filter_registry_for_mode）。
#
# 解析时同时兼容旧写法（旧工作流仍可加载）：`auto`、`H3-t2va` 等五个生成模式、
# 以及小写的 qwen-image-* / moss。
MODE_AUTO = "Auto"
MODE_H3_VIDEO = "H3-video"
MODE_QWEN_T2I = "Qwen-image-t2i"
MODE_QWEN_EDIT = "Qwen-image-edit"
MODE_ANIMA = "Anima"
MODE_MOSS = "Moss"
MODE_KREA2 = "Krea2"
MODE_H3_IMAGE = "H3-image"
MODE_Z_IMAGE = "Z-image"
MODE_OPTIONS = (
    MODE_AUTO,
    MODE_H3_VIDEO,
    MODE_QWEN_T2I,
    MODE_QWEN_EDIT,
    MODE_ANIMA,
    MODE_MOSS,
    MODE_KREA2,
    MODE_H3_IMAGE,
    MODE_Z_IMAGE,
)

# H3 家族的「合并档」：旧的五个生成模式（t2va/i2va/fl2va/l2va/ref2va）在
# normalize_mode 里一律归并为 MODE_H3_VIDEO，旧工作流保存的值仍然可用。
H3_GENERATION_MODES = ("t2va", "i2va", "fl2va", "l2va", "ref2va")

# Qwen-Image 提示词改写类 skills 的 id 标记（用于区分任务家族）
QWEN_IMAGE_MARKERS = ("qwen-image",)

# Anima 二次元插画类 skills 的 id 前缀（anima-prompt-format 等），
# 与 normalize_mode 的 anima- 前缀剥离保持一致（见 _canonical_id）。
ANIMA_SKILL_MARKERS = ("anima",)

# MOSS-Image 图像提示词增强类 skills 的 id 前缀（moss-image-prompt-enhancer 等），
# 与 normalize_mode 的 moss- 前缀归并保持一致。
MOSS_SKILL_MARKERS = ("moss",)

# Krea 2 提示词类 skills 的 id 前缀（krea2-prompt-writing / krea2-anime-prompt /
# krea2-editorial-longform 等），与 normalize_mode 的 krea2- 前缀归并保持一致。
# 该家族的提示词体系是**自然语言 caption**，与 Anima / MOSS / Qwen-Image 的写法
# 互不通用（见各 SKILL.md 的「不适用」一节）。
KREA2_SKILL_MARKERS = ("krea2",)

# MiniMax-H3-Image 图像类 skills 的 id 前缀（h3-image-prompt-writing /
# h3-image-edit-prompt），与 normalize_mode 的 h3-image 归并保持一致。
# 注意：必须排在 H3 视频判定**之前**——h3-image-* 也以 h3 开头，先判 image 才不会
# 被当成 H3-video 家族。
H3_IMAGE_SKILL_MARKERS = ("h3-image",)

# Z-Image（造相，阿里通义 6B S3-DiT）图像类 skills 的 id 前缀
# （z-image-prompt-writing / z-image-bilingual-text），与 normalize_mode 的
# z-image 归并保持一致。
Z_IMAGE_SKILL_MARKERS = ("z-image",)

# 「图像通用」skills 的 id 前缀（image-composition / image-color-harmony 等）。
# 这类 skills 承载与具体模型无关的七层美学工艺（构图 / 对比 / 光影明度 / 空间虚实 /
# 配色 / 主题叙事 / 情感意境 + 入口），**每一组、每个模式的清单都会完整加载**，
# 是跨家族的常驻基线；清单里单独成组并置顶（见 build_skills_manifest）。
# 只用前缀匹配，避免把 qwen-image-t2i-prompt / moss-image-prompt-enhancer 误判进来。
GENERAL_SKILL_MARKERS = ("image",)

# Anima 家族 skills 的固定「附加说明」：该家族统一采用「默认只出正面提示词」的输出
# 契约，负面提示词只在用户明确要求时才追加，因此不能沿用只输出单一交付物的通用强调。
ANIMA_FORMAT_NOTE = (
    "【输出要求】只输出 Anima 提示词正文本身：**默认只给正面提示词**，"
    "不要输出负面提示词、不要加 `Positive prompt` 之类的标题行、不要加 Markdown 代码块围栏。"
    "只有当用户明确要求负面词 / negative prompt，或表示自己那边没有设置负面词时，"
    "才追加第二段 `Negative prompt`。"
    "不要输出开头说明、结尾建议、解释、总结、前言或后记；"
    "不要把分辨率、宽高比、种子、CFG、步数、采样器或模型文件名写进提示词，"
    "也不要另附 `Suggested settings` 或任何参数数值"
    "（被问到参数时只回一句「由工作流设置决定」），"
    "也不要复述本条要求。"
)

# 「图像通用 skills」的家族提示：它们**在所有模式下都会并入清单**，
# 必须在家族提示里说明，否则模型会把清单里的 image-* 当成「混入的其它家族」而不敢用。
GENERAL_SKILL_HINT = (
    "清单里单独成组的 `image-*` 是**图像通用基线层**（与具体模型无关的七层美学工艺）。"
    "**这一组在每个模式的清单里都会加载**，属于跨家族的常驻基线，不是混进来的其它家族："
    "`image-aesthetics`（入口与七层路由：先判问题在哪层、按什么顺序修）、"
    "`image-composition`（构图：景别 / 机位 / 位置 / 分层）、"
    "`image-contrast`（对比：先看什么、什么被压下去）、"
    "`image-light-and-value`（光影与明度：光源 / 软硬 / 影子落点 / 明度键）、"
    "`image-space-and-depth`（空间与虚实：五层深度、遮挡、大气透视）、"
    "`image-color-harmony`（色彩理论：色相关系 / 明度饱和度 / 暗部色）、"
    "`image-subject-and-story`（主题与叙事：这张图在说什么、冻结在哪一刻）、"
    "`image-mood-and-atmosphere`（情感与意境：色温 / 空气 / 明度键 / 反面参照）。"
    "需要这些通用工艺时直接读取，**不要因为它们是通用 skills 就跳过**；"
    "**一次只改一层**，多层同时拉满会让画面重新变平（叠加纪律见 `image-aesthetics`）。"
    "其中 `image-artist-chain`（画师串）**只在二次元 / 动漫插画风格下生效**："
    "写实、3D、实景、产品类需求请忽略它，不要把它写进提示词。"
)

# 各「任务家族」模式允许出现在「自动」清单中的 skills。
# 未在此表且非 H3-video 的模式（即 Auto）不做筛选。
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


def _skill_file_stamps(skill_root: Path) -> tuple:
    """收集单个 skills 目录内**全部**文件的 (相对路径, mtime_ns, size)。

    必须覆盖 `references/` 等子目录，而不是只签 `SKILL.md` / `meta.yaml`：
    参考资料同样是交付内容的一部分（渐进式披露时由模型 `READ:` 按需读取），
    只签两个固定文件会让「改了参考资料、签名却不变」——节点缓存不失效、
    `IS_CHANGED` 也不变，用户读到的仍是旧内容且没有任何提示。

    跳过符号链接（防止越界与目录环），单个文件读取失败时跳过而非中断。
    """
    stamps = []
    stack = [skill_root]
    while stack:
        current = stack.pop()
        try:
            children = sorted(current.iterdir(), key=lambda item: item.name.casefold())
        except OSError:
            continue
        for child in children:
            try:
                if child.is_symlink():
                    continue
                if child.is_dir():
                    stack.append(child)
                    continue
                if not child.is_file():
                    continue
                stat = child.stat()
            except OSError:
                continue
            stamps.append(
                (child.relative_to(skill_root).as_posix(), stat.st_mtime_ns, stat.st_size)
            )
    stamps.sort(key=lambda item: item[0])
    return tuple(stamps)


def _dir_signature(root: Path) -> tuple:
    """目录签名：用于缓存失效与 IS_CHANGED（skills 变更后自动重新发现）。"""
    if not root.is_dir():
        return ()
    entries = []
    for child in sorted(root.iterdir(), key=lambda item: item.name.casefold()):
        if not child.is_dir():
            continue
        entries.append((child.name, _skill_file_stamps(child)))
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


def is_moss_skill(skill_id) -> bool:
    """判断某个 skills 是否属于 MOSS-Image 图像提示词增强家族（id 以 moss 开头）。

    与 normalize_mode 的 moss- 前缀归并保持一致：`moss` 模式只列这一家族；
    其他模式（H3-* / qwen-image-* / Anima）排除这一家族。判定只用前缀/段内匹配，
    不用裸子串，避免把含 "moss" 的无关 id 误判。
    """
    value = str(skill_id or "").strip().casefold()
    if not value:
        return False
    return any(
        value == marker or value.startswith(f"{marker}-") or f"-{marker}-" in value
        for marker in MOSS_SKILL_MARKERS
    )


def is_krea2_skill(skill_id) -> bool:
    """判断某个 skills 是否属于 Krea 2 图像提示词家族（id 以 krea2 开头）。

    与 normalize_mode 的 krea2- 前缀归并保持一致：`Krea2` 模式只列这一家族；
    其他模式（H3-* / qwen-image-* / Anima / moss）排除这一家族。判定只用前缀/
    段内匹配，不用裸子串，避免把含 "krea2" 的无关 id 误判。
    """
    value = str(skill_id or "").strip().casefold()
    if not value:
        return False
    return any(
        value == marker or value.startswith(f"{marker}-") or f"-{marker}-" in value
        for marker in KREA2_SKILL_MARKERS
    )


def is_h3_image_skill(skill_id) -> bool:
    """判断某个 skills 是否属于 MiniMax-H3-Image 图像家族（id 以 h3-image 开头）。

    与 normalize_mode 的 h3-image 归并保持一致：`H3-image` 模式只列这一家族；
    其他模式（H3-video / qwen-image-* / Anima / moss / Krea2）排除这一家族。
    判定**先于** H3 视频家族，避免 h3-image-* 被当成 h3-* 视频 skills。
    """
    value = str(skill_id or "").strip().casefold()
    if not value:
        return False
    return any(
        value == marker or value.startswith(f"{marker}-") or f"-{marker}-" in value
        for marker in H3_IMAGE_SKILL_MARKERS
    )


def is_z_image_skill(skill_id) -> bool:
    """判断某个 skills 是否属于 Z-Image（造相）图像家族（id 以 z-image 开头）。

    与 normalize_mode 的 z-image 归并保持一致：`Z-image` 模式只列这一家族；
    其他模式（H3-video / H3-image / qwen-image-* / Anima / moss / Krea2）排除这一家族。
    """
    value = str(skill_id or "").strip().casefold()
    if not value:
        return False
    return any(
        value == marker or value.startswith(f"{marker}-") or f"-{marker}-" in value
        for marker in Z_IMAGE_SKILL_MARKERS
    )


def is_general_skill(skill_id) -> bool:
    """判断某个 skills 是否属于「图像通用」家族（id 以 image- 开头）。

    这类 skills 承载与具体模型无关的图像工艺（构图、配色等），因此在**所有模式**
    下都会并入自动清单（见 filter_registry_for_mode）：无论用户选的是 H3 视频、
    Qwen-Image、Anima 还是 MOSS-Image，都能读到同一套通用工艺基线。

    判定只用**前缀**匹配（`image-`），不做段内匹配：否则 `qwen-image-t2i-prompt`
    与 `moss-image-prompt-enhancer` 会被误判成通用家族。
    """
    value = str(skill_id or "").strip().casefold()
    if not value:
        return False
    return value == "image" or value.startswith("image-")


def default_extra_note(skill_id=None, builtin_root=None, custom_root=None) -> str:
    """「附加说明」的默认值。

    取值优先级：
    1. skills 自身在 SKILL.md front matter / meta.yaml 中声明的 `extra-note`；
    2. Anima 家族 skills（id 含 `anima`）→ ANIMA_FORMAT_NOTE
       （两段式 Positive/Negative 契约，不能只输出单一交付物）；
    3. 图像通用家族 skills（id 以 `image-` 开头）→ OUTPUT_ONLY_NOTE
       （它们产出单一交付物：提示词正文 / 配色方案）；
    3b. Krea 2 家族 skills（id 以 `krea2-` 开头）→ OUTPUT_ONLY_NOTE
       （该家族无论短句档、二次元还是编辑级长文，交付物都是**可直接粘贴的 caption 正文**）；
    3c. Z-Image 家族 skills（id 以 `z-image-` 开头）→ OUTPUT_ONLY_NOTE
       （基础写作与双语版式两支的交付物都是可直接粘贴的提示词正文）；
    4. 产出单一交付物的 skills（id 含 `prompt`，含散文与 JSON 两类）→ OUTPUT_ONLY_NOTE；
    5. 「自动」→ OUTPUT_ONLY_NOTE（不预设具体 skills，用同一套通用强调）；
    6. 其余风格类 skills → 空（它们会输出分镜/制作方案，强加会误导模型）。

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

    # 3. 图像通用家族（image-*）：产出同样是单一交付物
    if is_general_skill(value):
        return OUTPUT_ONLY_NOTE

    # 3b. Krea 2 家族（krea2-*）：交付物恒为可直接粘贴的 caption 正文
    if is_krea2_skill(value):
        return OUTPUT_ONLY_NOTE

    # 3c. Z-Image 家族（z-image-*）：基础写作与双语版式都是单一交付物
    if is_z_image_skill(value):
        return OUTPUT_ONLY_NOTE

    if not found:
        # 4. 未发现的 id：按通用「单一交付物」规则兜底（不静默丢强调）
        return OUTPUT_ONLY_NOTE if is_prompt_skill(value) else ""

    # 5. 产出单一交付物的 skills
    return OUTPUT_ONLY_NOTE if is_prompt_skill(value) else ""


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def normalize_mode(mode: str) -> str:
    """规范化模式取值，返回 TitleCase 的规范家族名。

    规范值（首字母大写，与「模式」下拉的选项一一对应）：

    - `Auto`：不筛选，列出全部 skills；
    - `H3-video`：H3 视频家族**合并档**——旧的 `H3-t2va` / `H3-i2va` /
      `H3-fl2va` / `H3-l2va` / `H3-ref2va` 与不带前缀的 `t2va` 等一律归并到这里；
    - `Qwen-image-t2i` / `Qwen-image-edit`：Qwen-Image 提示词改写家族；
    - `Anima` / `anima-text2image` → `Anima`（家族模式，anima- 子模式均归并）；
    - `Moss` / `moss-image-prompt-enhancer` → `Moss`（moss- 子模式均归并）；
    - `Krea2` / `krea2-prompt-writing` → `Krea2`（krea2- 子模式均归并）；
    - 空 → `Auto`。

    大小写不敏感：旧工作流保存的 `auto` / `moss` / `qwen-image-t2i` 等写法
    仍会映射到对应的 TitleCase 家族名，不会失效。
    """
    value = str(mode or "").strip().casefold()
    if not value:
        return MODE_AUTO
    # 兼容下划线写法（H3_VIDEO / qwen_image_t2i 等）
    value = value.replace("_", "-")
    if value in (MODE_QWEN_T2I.casefold(), MODE_QWEN_EDIT.casefold()):
        return MODE_QWEN_T2I if value == MODE_QWEN_T2I.casefold() else MODE_QWEN_EDIT
    if value == MODE_ANIMA.casefold() or value.startswith(f"{MODE_ANIMA.casefold()}-"):
        return MODE_ANIMA
    if value == MODE_MOSS.casefold() or value.startswith(f"{MODE_MOSS.casefold()}-"):
        return MODE_MOSS
    if value == MODE_KREA2.casefold() or value.startswith(f"{MODE_KREA2.casefold()}-"):
        return MODE_KREA2
    # Z-image 图像家族（造相）：放在 H3 判定之前，避免与 h3-* 前缀混淆
    if value in (MODE_Z_IMAGE.casefold(), "z-image", "zimage", "z_image"):
        return MODE_Z_IMAGE
    if value.startswith(f"{MODE_Z_IMAGE.casefold()}-"):
        return MODE_Z_IMAGE
    # H3-image 图像家族：必须先于 H3-video 判定，否则 h3-image-* 会被吞进视频家族
    if value in (MODE_H3_IMAGE.casefold(), "h3-image", "h3image"):
        return MODE_H3_IMAGE
    if value.startswith(f"{MODE_H3_IMAGE.casefold()}-"):
        return MODE_H3_IMAGE
    # H3 视频家族：合并档 + 五个旧生成模式（带不带 H3- 前缀都认）
    if value in (MODE_H3_VIDEO.casefold(), "h3-video", "h3"):
        return MODE_H3_VIDEO
    for generation in H3_GENERATION_MODES:
        if value == generation or value == f"{MODE_H3_VIDEO.split('-')[0].casefold()}-{generation}":
            return MODE_H3_VIDEO
    return MODE_AUTO


def is_qwen_image_mode(mode: str) -> bool:
    """判断模式是否属于 Qwen-Image 提示词改写任务家族。"""
    return normalize_mode(mode) in (MODE_QWEN_T2I, MODE_QWEN_EDIT)


def is_anima_mode(mode: str) -> bool:
    """判断模式是否属于 Anima 二次元插画任务家族。"""
    return normalize_mode(mode) == MODE_ANIMA


def is_moss_mode(mode: str) -> bool:
    """判断模式是否属于 MOSS-Image 图像提示词增强任务家族。"""
    return normalize_mode(mode) == MODE_MOSS


def is_krea2_mode(mode: str) -> bool:
    """判断模式是否属于 Krea 2 图像提示词任务家族。"""
    return normalize_mode(mode) == MODE_KREA2


def is_h3_image_mode(mode: str) -> bool:
    """判断模式是否属于 MiniMax-H3-Image 图像任务家族。"""
    return normalize_mode(mode) == MODE_H3_IMAGE


def is_z_image_mode(mode: str) -> bool:
    """判断模式是否属于 Z-Image（造相）图像任务家族。"""
    return normalize_mode(mode) == MODE_Z_IMAGE


def is_h3_mode(mode: str) -> bool:
    """判断模式是否属于 H3 视频任务家族（合并档 H3-video，兼容旧生成模式写法）。"""
    return normalize_mode(mode) == MODE_H3_VIDEO


def filter_registry_for_mode(registry, mode: str):
    """按模式的任务家族筛选 skills 列表（Auto 返回原列表）。

    任务家族筛选的意义：模式已表明任务类型时，清单里不应再出现无关家族的
    skills，避免模型路由到错误家族（如选 qwen-image-t2i 却读到 H3 视频 skills）。

    **图像通用 skills（id 以 image- 开头，见 is_general_skill）是唯一例外：
    它们在所有模式下都会并入清单**，作为跨家族常驻的图像工艺基线。

    - Qwen-image-t2i / Qwen-image-edit：该家族对应 skills + 全部通用 skills；
    - Anima：Anima 家族（id 以 anima 开头的 12 个 skills）+ 全部通用 skills；
    - Moss：MOSS-Image 家族（id 以 moss 开头的 skills）+ 全部通用 skills；
    - Krea2：Krea 2 家族（id 以 krea2 开头的 skills）+ 全部通用 skills；
    - H3-image：MiniMax-H3-Image 家族（id 以 h3-image 开头的 skills）+ 全部通用 skills；
    - Z-image：Z-Image（造相）家族（id 以 z-image 开头的 skills）+ 全部通用 skills；
    - H3-video：H3 视频家族（h3-prompt-writing + 风格类 skills，排除 Qwen-Image、Anima、
      MOSS、Krea2、H3-image 与 Z-image）+ 全部通用 skills；
    - Auto：不筛选，返回全部（通用 skills 自然在内）。
    """
    normalized = normalize_mode(mode)
    allow = MODE_SKILL_ALLOWLIST.get(normalized)

    def keep(spec) -> bool:
        # 通用 skills 永远保留：所有模式都暴露同一套图像工艺基线
        if is_general_skill(spec.id):
            return True
        if allow is not None:
            return spec.id in allow
        if is_anima_mode(normalized):
            return is_anima_skill(spec.id)
        if is_moss_mode(normalized):
            return is_moss_skill(spec.id)
        if is_krea2_mode(normalized):
            return is_krea2_skill(spec.id)
        if is_h3_image_mode(normalized):
            return is_h3_image_skill(spec.id)
        if is_z_image_mode(normalized):
            return is_z_image_skill(spec.id)
        if is_h3_mode(normalized):
            # H3 视频家族：排除 Qwen-Image、Anima、MOSS、Krea2、H3-image 与
            # Z-image 六个图像家族
            return (
                not any(m in spec.id.casefold() for m in QWEN_IMAGE_MARKERS)
                and not is_anima_skill(spec.id)
                and not is_moss_skill(spec.id)
                and not is_krea2_skill(spec.id)
                and not is_h3_image_skill(spec.id)
                and not is_z_image_skill(spec.id)
            )
        return True

    return tuple(spec for spec in registry if keep(spec))


def mode_family_hint(mode: str = MODE_AUTO) -> str:
    """返回当前模式的「任务家族」说明，用于自动清单提示模型按家族路由。

    Auto 时返回空串（清单不做家族提示，保持中性）。
    """
    normalized = normalize_mode(mode)
    if normalized == MODE_AUTO:
        return ""
    if is_anima_mode(normalized):
        return (
            "当前模式：Anima（二次元插画）——本清单列出 Anima 家族的 skills"
            "（另含 image-* 图像通用 skills），请在这两类里选择；"
            "不要路由到 H3 视频、Qwen-Image、MOSS-Image、Krea2、H3-image 或 Z-image 家族的写法。"
            "动手前请**先读取共同基准** `anima-prompt-format/references/anima-prompt-baseline.md`"
            "（其中的「高杠杆规则」是全家族通用硬规则：主画师必选、权重用大数且加权标签总数 ≤4、"
            "取景对抗自然语言漂移、Hybrid 三层混合、动作与天气要有可见后果），"
            "再按需读取具体 skills 的 SKILL.md。"
            "涉及**配色 / 色调 / 颜色关系**（发灰、刺眼、主体陷进背景、整张只剩一个调子，"
            "或用户点名 pastel / neon / sepia / duotone / 电影感调色）时，"
            "先读通用基线 `image-color-harmony`（与模型无关的配色骨架、明度×饱和度结构、"
            "主体-背景分色、光的颜色），再叠加 Anima 专属的 `anima-color-harmony`"
            "（Anima 权重语法与家族路由细节）。"
            "涉及**画师串 / 画师混合 / 锁画风**（用户点名画师、要求模仿某种画风、"
            "或抱怨画面风格平庸、AI 感重）时，先读通用基线 `image-artist-chain`"
            "（与模型无关的画师串构建法：模型语法适配、数量决策、权重主次、"
            "位置与顺序、转义与冲突清理），再叠加 Anima 专属的 `anima-prompt-artist`"
            "（`@` 前缀与家族权重档位）；只有用户明确要**融合 / 混合**多位画师时"
            "才做多画师串，否则保持单个主画师。"
            + GENERAL_SKILL_HINT
        )
    if is_moss_mode(normalized):
        return (
            "当前模式：MOSS-Image 图像提示词增强——本清单列出 MOSS-Image 家族的 skills"
            "（另含 image-* 图像通用 skills），请在这两类里选择；"
            "不要路由到 H3 视频、Qwen-Image、Anima、Krea2、H3-image 或 Z-image 家族的写法。"
            "该家族现在有 2 个 skills，先按需求类型选一个来读："
            "**动画 / 二次元风格需求优先读 `moss-anime-prompt-template`**——"
            "二次元人物、IP 同人、场景插画、多人互动、海报、漫画等动画风格需求走这一支，"
            "它是中文模板，画风独立首句、人数与属性绑定、镜头与空间、光照因果、"
            "Layout 细则与输出前检查都已内联成硬规则；"
            "**通用图像创意扩写、只需 caption、或需要像素级 Layout 与坐标编译时读 "
            "`moss-image-prompt-enhancer`**。"
            "该家族的产出是**可直接粘贴的 MOSS-Image 正向提示词**，"
            "**默认交付物是 JSON Layout**，核心思想是**「全局描述 + 局部方框」**——"
            "`summary.caption` 写整张图的全局描述，扁平 `items` 里每个局部对象各占一个方框；"
            "（1）Caption——写 UTF-8 JSON `{\"caption\":\"...\"}`，正文是连贯散文，"
            "空间关系用文字表达，可见文字逐字保留原语言；"
            "只有用户明确要 caption / 极简散文，或画面确实没有任何需要定位的元素时，才用这种 Caption；"
            "其余情况一律用 Layout；**写 Layout 前必须先读 `moss-image-prompt-enhancer/references/layout.md`**，"
            "草稿用 `summary` + 扁平 `items`（每项 label/caption/bbox）+ `width`/`height`"
            "（必须是 16 的正整数倍）+ `bbox_coord_space=\"abs\"` + `bbox_format=\"xyxy\"`，"
            "bbox 用画布左上角起算的绝对像素，不要手动居中或量化，"
            "再用随附脚本 `scripts/compile_prompt.py draft.json --output prompt.txt` 编译，"
            "把编译结果作为最终交付（不要手写居中 JSON 绕过校验）。"
            "注意：本节点只读取文本指导、**不执行任何脚本**；若下游运行环境没有 shell，"
            "请按 `references/layout.md` 的换算规则自行换算为 `abs_centralized` / `yxyx` "
            "整数单行 JSON，换算方式必须与脚本一致。"
            "**二次元美学要点**（官方 USERGUIDE + 同 seed 社区实测）：① **画种词整组替换**——"
            "开头放一整组画种词（anime screencap / manga page / watercolor / impasto / chibi …）"
            "并**同步删掉冲突词**，任何一个写实词残留（pores / camera flash / film grain）都会"
            "把画面推回照片，单独一个 `cel shading` 也切不动；"
            "② **精修与松弛按部位分配**——脸与发丝精修、衣服与背景保留笔触并写 "
            "`Zero rough sketch lines`，可同时避开「草稿脸」与「塑料页游立绘」；"
            "③ **LoRA 触发词是结构 token**——文本编码器为冻结的 Qwen3.5-9B，"
            "`<|artist|>fkey<|/artist|>` 必须整行放在第一行、无空格、无句尾句号，"
            "部分二次元 LoRA 反而**不用触发词**更稳（正文写 `anime character`）；"
            "强度 / 步数 / CFG / Shift 一律不进提示词。"
            "④ **走 Layout 时**：画风锚句只放 `summary.caption` 第一句、item caption 只写自身可见属性；"
            "**`summary.palette` 未经验证**——默认降级为在 caption 里用自然语言写 2–3 个色名，"
            "要用该字段时必须在 caption 里同时写同一组色（详见 §13.1）。"
            "细化规则在 `moss-anime-prompt-template` 的 §9.1–§9.2、§13.1 与其 "
            "`references/moss-anime-aesthetics.md`。"
            "该家族不生成图片、不调用外部 API。"
            + GENERAL_SKILL_HINT
        )
    if is_krea2_mode(normalized):
        return (
            "当前模式：Krea 2（Krea-2 / K2）图像提示词——本清单列出 Krea 2 家族的 skills"
            "（另含 image-* 图像通用 skills），请在这两类里选择；"
            "不要路由到 H3 视频、Qwen-Image、Anima、MOSS-Image 或 H3-image 家族的写法。"
            "该家族共 7 个 skills：3 个通用 + 4 个二次元专用，先按需求类型选一个来读："
            "**普通画面 / 短需求扩写读 `krea2-prompt-writing`**——"
            "六层骨架（媒介与风格锚句 → 主体身份 → 服装材质 → 动作因果 → 空间机位景深 → "
            "材质分区与色盘与光位 → 画内文字），短句档 / 标准档 / 长文档三档按需求体量选；"
            "**二次元 / 动漫 / 插画 / IP 同人 / 画师画风读 `krea2-anime-prompt`**——"
            "单一主画风锚句、场景重构而非专有名词、带可见后果的动作节点、"
            "能在当前景别看见的身份锚点；"
            "**海报级 / 主视觉 / 编辑级长文读 `krea2-editorial-longform`**——"
            "「母题整块 + 有限替换位」（身份 / 画幅 / 服装部位 / 画内文字四类），"
            "1500–2700 词、25 段骨架、色盘百分比、五层景深。"
            "**二次元 / 动漫 / 插画需求再细分四支**：写完整 caption 用 `krea2-anime-prompt`；"
            "**画风发漂、要锁死某个工作室或时代**（官方点名被训练得最扎实的五个牵引是 "
            "Ghibli / 新海诚 CoMix Wave / 京都动画 / Madhouse / 90 年代 Sunrise）读 "
            "`krea2-anime-style`——四维锚句、五个流派的视觉指纹、防漂移四道锁、"
            "混合画风的主锚+偏移写法、风格 LoRA 触发词的正确摆法；"
            "**同一角色多图一致 / 三视图 / 表情表**读 `krea2-anime-character`——"
            "五段式身份块（轮廓 / 发型 / 眼与标记 / 服装层次 / 识别物）与不变量 vs 可变量；"
            "**主视觉 / 海报 / 漫画分镜 / 草图转成品**读 `krea2-anime-keyvisual`——"
            "三层焦点与缩略图测试、预留文字带、行列式格位与阅读方向、气泡与拟声词逐字写法。"
            "四支共用**同一句画风锚句**，不要各立一个。"
            "**画面很「AI」（塑料感 / 过度干净 / 平 / 只有默认色）或用户只给了调性词"
            "（编辑感 / 电影感 / 静谧 / 奢华 / 赛博 / 复古）时，先读 "
            "`krea2-aesthetic-direction`**——美学五层（主方向 / 光 / 材质 / 色盘 / 质感）、"
            "反「AI 感」十条硬规则、12 条调性配方，以及**把 Krea 2 界面的 Creativity 四档"
            "（Raw / Low / Medium / High）、Intensity / Complexity / Movement 滑杆、"
            "最多 4 张风格参考与情绪板翻译成文字等效写法**的对照表（工作流只有文本框时靠措辞预演）；"
            "它只加美学层，不另立第二个画风锚句。"
            "三条硬规则：① Krea 2 读**自然语言稠密 caption**，"
            "**禁止** Danbooru tag 串、`masterpiece` / `best quality` / `score_9` / `8k`、"
            "`(tag:1.2)` 权重语法与 `@artist`——这些在自然语言编码器里只会引入噪声；"
            "② **忠实优先**：不新增用户没暗示的物体、角色或道具，用户已写死的媒介"
            "（photo / illustration / 3D render）必须保留；"
            "③ **风格与画师要翻译成视觉属性**（媒介 / 线条 / 上色 / 色盘 / 时代），"
            "只写名字等于没写。"
            "写 Krea 2 提示词前如需官方原文规则，先读 "
            "`krea2-prompt-writing/references/official-krea2-guidelines.md`；"
            "涉及构图 / 配色时叠加 image-* 通用 skills 即可，不要用 Anima 的 tag 语法。"
            "该家族只产出文本，不生成图片、不调用外部 API。"
            + GENERAL_SKILL_HINT
        )
    if is_qwen_image_mode(normalized):
        return (
            "当前模式：Qwen-Image 提示词改写——本清单列出该家族的 skills"
            "（另含 image-* 图像通用 skills），请在这两类里选择；"
            "不要路由到 H3 视频、Anima、MOSS-Image、Krea2、H3-image 或 Z-image 家族的写法。"
            + GENERAL_SKILL_HINT
        )
    if is_z_image_mode(normalized):
        return (
            "当前模式：Z-Image（造相，阿里通义 6B S3-DiT）——本清单列出 Z-image 家族的 skills"
            "（另含 image-* 图像通用 skills），请在这两类里选择；"
            "不要路由到 H3 视频、H3-Image、Qwen-Image、Anima、MOSS-Image 或 Krea2 家族的写法。"
            "该家族有 2 个 skills："
            "**普通画面 / 写实 / 风格化需求读 `z-image-prompt-writing`**——"
            "六段骨架（媒介 → 主体身份 → 动作因果 → 空间机位 → 光与材质 → 文字与收束），"
            "并**先判断变体**；"
            "**文字是主体（海报 / 招牌 / 包装 / 书封 / 菜单 / 标签 / 中英双语版式）读 "
            "`z-image-bilingual-text`**——五要素文字层（内容 · 位置 · 层级 · 字体气质 · 材质）、"
            "中英各自成行的混排三分行规则与版式骨架。"
            "三条硬规则：① **先分变体再写提示词**——Z-Image-Turbo 是 8 步蒸馏版、"
            "**没有 CFG，负面提示词不生效**；Z-Image（Base）/ Omni-Base / Edit 有 CFG"
            "（官方参考 30–50 步、CFG 3–5），负面词有效，但官方明确它**对负面词敏感**，"
            "所以负面词要短而准，堆长串会削画面；"
            "② **自然语言顺序语义**：S3-DiT 把文本与图像 token 在序列级拼接，"
            "提示词按自然语言顺序被整体理解，**禁止** Danbooru tag 串、"
            "`masterpiece` / `best quality` / `8k` 与 `(tag:1.2)` 权重语法；"
            "③ **画面文字逐字加引号**并给位置 / 层级 / 字体气质 / 材质；"
            "文字是主体时控制字数（中文 2–6 字、英文 1–3 词最稳），"
            "不需要文字就明说「画面中没有文字」。"
            "Z-Image 的文本编码器是 Qwen3-4B，**中英双语**都支持，"
            "所以画面内中文可以直接写中文；但描述正文用英文更稳。"
            "步数 / CFG / 分辨率属于工作流参数，**不要写进提示词**。"
            "写之前如需官方原文规则与变体表，先读 "
            "`z-image-prompt-writing/references/z-image-official-guidelines.md`；"
            "构图 / 配色叠加 image-* 通用 skills 即可。"
            "该家族只产出文本，不生成图片、不调用外部 API。"
            + GENERAL_SKILL_HINT
        )
    if is_h3_image_mode(normalized):
        return (
            "当前模式：MiniMax-H3-Image（开源权重图像模型：33.1B DiT，蒸馏 6 步、"
            "guidance 固定 1，原生约 16 MP）——本清单列出 H3-image 家族的 skills"
            "（另含 image-* 图像通用 skills），请在这两类里选择；"
            "不要路由到 H3 视频、Qwen-Image、Anima、MOSS-Image、Krea2 或 Z-image 家族的写法。"
            "该家族有 2 个 skills，先按有没有参考图选一个来读："
            "**纯文生图（海报 / 信息图 / 图表 / 仪表盘 / 产品图 / UI / 场景 / 分镜 / 宫格）"
            "读 `h3-image-prompt-writing`**——官方四层顺序：任务与交付物 → 版式与阅读顺序 → "
            "主体状态与动作 → 用可见的材质 / 颜色 / 光写风格；"
            "**有参考图要改 / 合成 / 换风格（最多 16 张）读 `h3-image-edit-prompt`**——"
            "一段连续文本，固定三段：`<Picture N>` → `<Subject N>` 定义 → 目标总述与"
            "各源关系（完全保留 / 部分保留 / 属性迁移 / 弱参考）→ 变化与新增内容。"
            "三条硬规则：① **没有负面提示词**——guidance 固定 1，没有 CFG，"
            "官方 API 与本地服务都拒绝 `negative_prompt`；要排除什么就**正面写出来**"
            "（例如 `The image contains no text, letters or numbers.`），"
            "沿用 SD 的 `worst quality` 之类负面串只会被拒或变成画面内容；"
            "② **画面上出现的每个字都要逐字加引号**并写明位置与层级；"
            "不需要文字时**必须显式声明无文字**，否则模型会自己补标题与标签；"
            "③ 数据要给精确数值 / 单位 / 刻度且推导结果自己算，"
            "**不要把编造的数字当真实数据**（示例数据标 `illustrative`）。"
            "分辨率（4–20 MP、边长 32 倍数、16 MP 最佳）与 6 步 / CFG 1 属于工作流参数，"
            "**不要写进提示词**。写之前如需官方原文规则，先读 "
            "`h3-image-prompt-writing/references/official-h3-image-guidelines.md`；"
            "构图 / 配色叠加 image-* 通用 skills 即可。"
            "该家族只产出文本，不生成图片、不调用外部 API。"
            + GENERAL_SKILL_HINT
        )
    if is_h3_mode(normalized):
        return (
            "当前模式：MiniMax H3 视频（合并档，已含原 t2va / i2va / fl2va / l2va / ref2va "
            "五种生成写法）——本清单已排除 Qwen-Image、Anima、MOSS-Image、Krea2、"
            "H3-image 与 Z-image 图像提示词家族的 skills（image-* 图像通用 skills 仍保留）；"
            "h3-prompt-writing 的**基础指南与全参考指南两份都已提供**，"
            "按用户实际要做的任务取用：纯文生视频用基础指南，带参考素材用全参考指南；"
            "图像提示词需求请改用对应的图像家族模式；"
            "分镜的画面构图与配色可以直接借助 image-* 通用 skills。"
            + GENERAL_SKILL_HINT
        )
    return ""


def resolve_effective_mode(skill_id, mode) -> str:
    """联动规则：**只有「选择skills」为「自动」时，「模式」才生效**。

    - `选择skills` = 自动 → 返回规范化后的模式（用于按任务家族筛选清单）；
    - `选择skills` = 具体 skills（或为空，将回退到默认 skills）→ 返回 `Auto`，
      即模式被中和：不筛选，且加载该 skills 的全部参考资料。

    这样「模式」在语义上始终只描述「自动」模式下的任务家族；手动指定 skills 时
    由该 skills 自身决定输出，不受模式干扰。

    ⚠️ 这里只做**计算上的中和**，绝不改写控件值：前端也**不会**把「模式」控件切回
    Auto（早期版本会，导致「选了模式，下次运行又回到自动」）。用户选的模式会原样
    随工作流保存，切回「自动」后立即重新生效。
    """
    if str(skill_id or "").strip() == AUTO_SELECTION:
        return normalize_mode(mode)
    return MODE_AUTO


def _h3_guides(mode: str) -> tuple:
    """h3-prompt-writing 的参考资料选择。

    合并档 `H3-video` 把原先的 t2va/i2va/fl2va/l2va/ref2va 五个生成模式并成一项，
    不再按生成模式二选一：**基础指南与全参考指南两份一起给**，由模型按用户实际
    要做的任务（纯文生视频 / 带参考素材）自行取用。Auto 档同理给两份。
    """
    # 合并后不再按生成模式分叉：H3-video 与 Auto 都给两份指南
    return ("base-en.txt", "ref-en.txt")


def skill_instructions(
    skill_id: str,
    mode: str = MODE_AUTO,
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


# 「自动」清单里每条描述的长度上限：清单只负责让模型**路由**到对的 skills，
# 正文由 READY 协议按需读取。描述过长会把清单撑到与正文同量级，削弱渐进式披露。
MANIFEST_DESC_LIMIT = 240


def _manifest_description(description: str, limit: int = MANIFEST_DESC_LIMIT) -> str:
    """把描述压到清单可接受的长度：优先截在第一个句号，否则硬截断并加省略号。"""
    text = " ".join(str(description or "").split())
    if len(text) <= limit:
        return text
    cut = text[:limit]
    for mark in ("。", ". ", "；", "; "):
        index = cut.rfind(mark)
        if index >= limit // 2:
            return cut[: index + len(mark)].strip()
    return cut.rstrip(" ,，、;；") + "…"


def build_skills_manifest(
    builtin_root=None,
    custom_root=None,
    max_chars: int = MAX_CHARS_DEFAULT,
    mode: str = MODE_AUTO,
) -> str:
    """构建「自动」模式下发给模型的 skills 清单与读取协议说明。

    只包含 skills 的 id 与描述（不含正文），由模型按需请求读取正文，
    实现渐进式披露（progressive disclosure）。

    模式为非 Auto 时按「任务家族」筛选清单（见 filter_registry_for_mode），
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

    # 清单分两组：**图像通用基线（全组都加载）** 与 **本模式的家族 skills**。
    # 通用层是跨家族的常驻基线，所有模式都会并入，因此在清单里单独成组并置顶，
    # 让模型明确「这一组每个模式都有、是必读基线」，而不是当成混进来的其它家族。
    general = [spec for spec in registry if is_general_skill(spec.id)]
    family = [spec for spec in registry if not is_general_skill(spec.id)]

    def _row(spec) -> str:
        label = f"（{spec.display_name}）" if spec.display_name else ""
        return f"- {spec.id}{label}: {_manifest_description(spec.description)}"

    if general:
        lines.extend(
            [
                f"# 图像通用基线（{len(general)} 个｜所有模式都会加载）",
                "",
                "这一组是**跨模型的图像工艺基线**，不属于任何单一家族，"
                "**每个模式的清单里都会出现**；需要构图 / 对比 / 光影 / 空间 / 配色 /",
                "叙事 / 情绪等通用工艺时直接按下面的 id 读取：",
                "",
            ]
        )
        lines.extend(_row(spec) for spec in general)
        lines.append("")

    if family:
        lines.extend(
            [
                f"# 家族 skills（{len(family)} 个｜当前模式）",
                "",
            ]
        )
        lines.extend(_row(spec) for spec in family)
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
            "**一轮可以同时读取多个 skills**（需要组合多份指导时不必逐个等往返）：",
            "- 每行一条：`READ: a` 换行 `READ: b`；",
            "- 一行多条：`READ: a b` / `READ: a、b` / `READ: a, b`。",
            "同一轮请求的目标会被一次性全部读取并回注；某个目标读不到时，",
            "其余目标照常注入，失败的目标会单独提示，可下一轮重试。",
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
    DESCRIPTION = 'skills管理器：管理并读取插件 skills/（内置）与 custom_skills/（自定义）目录中的 skills；选「自动」时只输出 skills 清单与读取协议，由自定义LLM与模型多轮按需读取（渐进式披露），选具体 skills 时输出其完整指导文本；模式可选 Auto / H3-video / Qwen-image-t2i / Qwen-image-edit / Anima / Moss / Krea2 / H3-image / Z-image（非 Auto 时按任务家族筛选自动清单；H3-video 为原 t2va/i2va/fl2va/l2va/ref2va 五档合并）；image-* 图像通用 skills（构图 / 配色等模型无关工艺）在所有模式下都会并入清单'

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
                        "所选值与模式都会随工作流保存，不会被自动刷新改动；"
                        "点击节点上的「刷新skills」按钮可重新扫描",
                    },
                ),
                "模式": (
                    list(MODE_OPTIONS),
                    {
                        "default": MODE_AUTO,
                        "tooltip": "任务模式，仅在「选择skills」为「自动」时生效"
                        "（选具体 skills 时自动失效，但模式值本身会被保留，"
                        "切回「自动」后立即重新生效，不会被自动刷新改动）。"
                        "Auto：不筛选，列出全部 skills，h3-prompt-writing 同时提供基础与全参考两份指南；"
                        "H3-video：MiniMax H3 视频家族合并档"
                        "（原 t2va / i2va / fl2va / l2va / ref2va 五种生成写法合为一档，"
                        "基础指南与全参考指南两份一起给）；"
                        "Qwen-image-t2i / Qwen-image-edit：Qwen-Image 2.1 图像提示词改写家族；"
                        "Anima：Anima（CircleStone Labs × Comfy Org）二次元插画家族"
                        "（列出 anima-* 的 12 个 skills）；"
                        "Moss：MOSS-Image 图像提示词增强家族"
                        "（列出 moss-* 的 skills，默认交付 JSON Layout：全局描述 + 局部方框）；"
                        "Z-image：Z-Image（造相，通义 6B S3-DiT）图像家族"
                        "（列出 z-image-* 的 skills；Turbo 8 步无 CFG 不写负面词，Base 30–50 步 CFG 3–5 负面词才生效）；"
                        "H3-image：MiniMax-H3-Image 图像家族"
                        "（列出 h3-image-* 的 skills：文生图 / 参考图编辑，6 步无 CFG、无负面词、约 16 MP）；"
                        "Krea2：Krea 2（Krea-2 / K2）自然语言 caption 家族"
                        "（列出 krea2-* 的 skills：基础写作 / 二次元 / 编辑级长文）；"
                        "所有模式下都会并入 image-* 图像通用 skills（构图 / 配色 / 画师串等模型无关工艺，"
                        "其中画师串 image-artist-chain 仅二次元 / 动漫风格生效）",
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
        "anima",
        "二次元",
        "配色",
        "颜色搭配",
        "color harmony",
        "palette",
        "moss",
        "MOSS-Image",
        "图像提示词增强",
        "caption",
        "layout",
        "版面",
        "bbox",
        "二次元提示词模板",
        "anime prompt",
        "moss anime",
        "z image",
        "Z-Image",
        "z-image",
        "造相",
        "zimage",
        "通义图像",
        "双语文字",
        "文字版式",
        "bilingual text",
        "typography",
        "h3 image",
        "H3-Image",
        "h3-image",
        "minimax image",
        "文生图提示词",
        "信息图",
        "infographic",
        "dashboard",
        "海报提示词",
        "krea",
        "krea2",
        "Krea 2",
        "K2",
        "krea2 prompt",
        "krea2 aesthetic",
        "krea2 anime style",
        "二次元画风",
        "anime style lock",
        "画风锁定",
        "吉卜力",
        "ghibli",
        "新海诚",
        "京都动画",
        "kyoto animation",
        "madhouse",
        "角色一致性",
        "character sheet",
        "三视图",
        "表情表",
        "expression sheet",
        "漫画分镜",
        "manga panel",
        "主视觉",
        "key visual",
        "skybox",
        "美学方向",
        "art direction",
        "调性",
        "AI感",
        "plastic look",
        "creativity slider",
        "moodboard",
        "情绪板",
        "风格参考",
        "style reference",
        "自然语言提示词",
        "编辑级长文",
        "长文提示词",
        "editorial prompt",
        "漫画",
        "海报",
        "图像通用",
        "通用 skills",
        "美学",
        "aesthetics",
        "七层美学",
        "对比",
        "contrast",
        "光影",
        "明度",
        "lighting",
        "value",
        "空间",
        "虚实",
        "景深",
        "depth",
        "叙事",
        "story",
        "情绪",
        "氛围",
        "mood",
        "atmosphere",
        "构图",
        "图像构图",
        "composition",
        "image composition",
        "图像配色",
        "image color harmony",
        "画师串",
        "画师混合",
        "artist chain",
        "artist string",
        "artist mixing",
        "image artist chain",
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
        # 模式为非 Auto 时按任务家族筛选清单。
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
    "MODE_H3_VIDEO",
    "H3_GENERATION_MODES",
    "MODE_AUTO",
    "MODE_QWEN_T2I",
    "MODE_QWEN_EDIT",
    "MODE_ANIMA",
    "MODE_MOSS",
    "MODE_KREA2",
    "MODE_H3_IMAGE",
    "MODE_Z_IMAGE",
    "QWEN_IMAGE_MARKERS",
    "ANIMA_SKILL_MARKERS",
    "MOSS_SKILL_MARKERS",
    "KREA2_SKILL_MARKERS",
    "H3_IMAGE_SKILL_MARKERS",
    "Z_IMAGE_SKILL_MARKERS",
    "GENERAL_SKILL_MARKERS",
    "GENERAL_SKILL_HINT",
    "MODE_SKILL_ALLOWLIST",
    "normalize_mode",
    "is_qwen_image_mode",
    "is_anima_mode",
    "is_moss_mode",
    "is_krea2_mode",
    "is_h3_image_mode",
    "is_z_image_mode",
    "is_h3_mode",
    "filter_registry_for_mode",
    "mode_family_hint",
    "resolve_effective_mode",
    "OUTPUT_ONLY_NOTE",
    "ANIMA_FORMAT_NOTE",
    "PROMPT_SKILL_MARKERS",
    "is_prompt_skill",
    "is_anima_skill",
    "is_moss_skill",
    "is_krea2_skill",
    "is_h3_image_skill",
    "is_z_image_skill",
    "is_general_skill",
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
