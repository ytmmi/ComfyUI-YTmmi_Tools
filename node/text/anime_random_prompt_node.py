# 随机提示词(Anime)
"""随机提示词(Anime)节点。

用**参数配置（下拉）+ 文本输入命中**两种方式，从合并词库里随机生成 Anima 用的
英文 Danbooru 标签提示词。

词库（离线，随插件分发在 ``node/text/data/``）：

- ``anime_prompt_tags.json``      18 个槽位的候选词（Prompt Forge + 造型台 V5 合并）
- ``anime_prompt_levels.json``    逐标签 NSFW 档位表（造型台 V5 登记表）
- ``anime_prompt_characters.json`` 2894 位角色（Prompt Forge 507 + V5 2390）
- ``anime_prompt_scenes.json``     297 条场景搭配（V5 271 + Prompt Forge 26）

分级闸门：五级（``sfw`` / ``L1`` 擦边 / ``L2`` 成人 / ``L3`` 过激 / ``L4`` 极端 /
``不限``），**候选池先按档位收敛再抽**——低档位根本抽不到高档词。

节点行为要点：

- 每个槽位一个下拉，首项恒为「随机」；**空值 / 随机 = 随机命中**。
- 「角色」是文本输入：用字符串在角色库里命中（中文名 / 英文名 / trigger 都行），
  **留空 = 随机命中一位角色**。
- 「场景搭配」是独立下拉（造型台的 271 条场景预设）；预设只填补**用户没有显式指定**
  的槽位，用户显式选的值优先。
- 「详细程度」开关：详细 = 18 个槽位，简略 = 8 个槽位（质量 / 画师 / 服装 / 姿势 /
  场景 / 光影 / 镜头 / 构图）；简略模式下其余槽位不参与，报告里标注「未启用」。
- 三个输出端口：提示词 / 命中情况 / 负向提示词。

⚠️ 词库里含成人向内容（用户明确要求包含 nsfw 词库），默认分级为「全年龄」。
"""

from __future__ import annotations

import json
import os
import random
import re
import unicodedata
from collections import OrderedDict

# ---------------------------------------------------------------------------
# 一、路径与加载
# ---------------------------------------------------------------------------

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
TAGS_FILE = os.path.join(DATA_DIR, "anime_prompt_tags.json")
LEVELS_FILE = os.path.join(DATA_DIR, "anime_prompt_levels.json")
CHARS_FILE = os.path.join(DATA_DIR, "anime_prompt_characters.json")
SCENES_FILE = os.path.join(DATA_DIR, "anime_prompt_scenes.json")

_CACHE = {}


def _load_json(path):
    key = os.path.abspath(path)
    if key not in _CACHE:
        if not os.path.isfile(path):
            raise FileNotFoundError(
                "随机提示词(Anime) 缺少词库文件：%s\n"
                "请用 tools/build_anime_prompt_lib.py 重建词库。" % path
            )
        with open(path, "r", encoding="utf-8") as fh:
            _CACHE[key] = json.load(fh)
    return _CACHE[key]


def tag_slots():
    """槽位候选词：``{slot_key: {"name": 中文名, "items": [{en, zh, level}]}}``。"""
    return _load_json(TAGS_FILE)["slots"]


def tag_levels():
    """造型台登记的逐标签档位表（``{英文标签: 0~4}``）。"""
    return _load_json(LEVELS_FILE).get("tag_levels", {})


def characters():
    """角色库（2894 位）。"""
    return _load_json(CHARS_FILE)["characters"]


def cjk_map() -> dict:
    """繁简 / 日文新字体 → 简体的单字映射（构建期烘焙进词库）。

    有了它，用户输入 ``阿爾托莉雅`` / ``博麗霊夢`` 这类写法也能命中
    简体词库里的角色。
    """
    return _load_json(CHARS_FILE).get("cjk_map") or {}


def scenes():
    """场景搭配预设（297 条）。"""
    return _load_json(SCENES_FILE)["scenes"]


# ---------------------------------------------------------------------------
# 二、槽位定义
# ---------------------------------------------------------------------------

# 槽位 key → 中文显示名（= 前端控件名）
SLOT_LABELS = OrderedDict(
    [
        ("quality", "质量"),
        ("artist", "画师"),
        ("count", "人数"),
        ("hair", "发型"),
        ("face", "面部"),
        ("expression", "表情"),
        ("body", "体型"),
        ("clothing", "服装"),
        ("accessory", "配饰"),
        ("pose", "姿势"),
        ("environment", "场景"),
        ("weather", "天气"),
        ("props", "道具"),
        ("lighting", "光影"),
        ("camera", "镜头"),
        ("composition", "构图"),
        ("text", "文本描述"),
        ("negative", "负向"),
    ]
)

# 简略模式的 8 个槽位
BRIEF_SLOTS = ("quality", "artist", "clothing", "pose", "environment", "lighting", "camera", "composition")

# 正向提示词的拼接顺序（质量 → 画师 → 角色 → 人物 → 服装 → 动作 → 场景 → 光影 → 镜头）
POSITIVE_ORDER = (
    "quality",
    "artist",
    "count",
    "hair",
    "face",
    "expression",
    "body",
    "clothing",
    "accessory",
    "pose",
    "environment",
    "weather",
    "props",
    "lighting",
    "camera",
    "composition",
    "text",
)

# 造型台字段 → 本节点槽位（场景搭配预设落位用）
FIELD_TO_SLOT = {
    "count": "count",
    "hair_len": "hair",
    "hair_color": "hair",
    "hair_curl": "hair",
    "eyes_color": "face",
    "makeup": "face",
    "emotion": "expression",
    "eye_gaze": "expression",
    "figure": "body",
    "skin": "body",
    "leg": "body",
    "outfit": "clothing",
    "cloth_color": "clothing",
    "cloth_mat": "clothing",
    "n_state": "clothing",
    "n_exposure": "clothing",
    "n_body": "clothing",
    "n_theme": "clothing",
    "n_extra": "clothing",
    "pose_base": "pose",
    "arms_hands": "pose",
    "action": "pose",
    "n_act": "pose",
    "n_pos": "pose",
    "n_orgasm": "pose",
    "shot_size": "camera",
    "viewpoint": "camera",
    "dof": "camera",
    "place": "environment",
    "prop": "props",
    "texture_fx": "props",
    "weather": "weather",
    "light_fx": "lighting",
    "nl": "text",
}

# ---------------------------------------------------------------------------
# 三、分级（对齐造型台 V5 的五级闸门）
# ---------------------------------------------------------------------------

# 控件值 → (内部 key, 数字档位, 中文名)
LEVEL_OPTIONS = OrderedDict(
    [
        ("全年龄", ("sfw", 0, "全年龄")),
        ("L1 擦边", ("suggestive", 1, "擦边")),
        ("L2 成人", ("explicit", 2, "成人")),
        ("L3 过激", ("hardcore", 3, "过激")),
        ("L4 极端", ("extreme", 4, "极端")),
        ("不限", ("any", 99, "不限")),
        ("随机", (None, None, "随机")),
    ]
)

RANDOM_LABEL = "随机"

# Anima 专用质量前缀（对齐 skills/anima-prompt-format/references/anima-prompt-baseline.md）
ANIMA_QUALITY_PRESETS = [
    "masterpiece, best quality, score_7, safe",
    "masterpiece, best quality, score_8, score_7, safe",
    "masterpiece, best quality, safe",
    "masterpiece, best quality, highres, absurdres, score_7, safe",
    "masterpiece, very aesthetic, best quality, score_9, score_8, highres, absurdres, newest, year 2025",
    "best quality, safe",
]

# 质量前缀的中文显示名（下拉里只显示中文，输出仍为英文原串）
ANIMA_QUALITY_PRESET_LABELS = OrderedDict(
    [
        ("预设：杰作+最佳+7分+安全", ANIMA_QUALITY_PRESETS[0]),
        ("预设：杰作+最佳+8分7分+安全", ANIMA_QUALITY_PRESETS[1]),
        ("预设：杰作+最佳+安全", ANIMA_QUALITY_PRESETS[2]),
        ("预设：杰作+最佳+高分辨率+7分+安全", ANIMA_QUALITY_PRESETS[3]),
        ("预设：大师杰作+9分8分+高分辨率+2025", ANIMA_QUALITY_PRESETS[4]),
        ("预设：最佳+安全", ANIMA_QUALITY_PRESETS[5]),
    ]
)

# 负向提示词的固定基线（词库 negative 槽里必然存在的条目）
BASELINE_NEGATIVES = [
    "worst quality",
    "low quality",
    "lowres",
    "bad anatomy",
    "bad hands",
    "blurry",
    "jpeg artifacts",
    "watermark",
    "extra fingers",
]

# 角色外观里不取的标签（人数类，与「人数」槽位重复）
_COUNT_TAGS = {"1girl", "2girls", "3girls", "1boy", "2boys", "solo", "multiple girls", "multiple boys"}


# ---------------------------------------------------------------------------
# 四、工具函数
# ---------------------------------------------------------------------------


def normalize(text) -> str:
    """规范化：去首尾空白 + 压空格 + 小写。

    额外做三件事：

    - 全角字符转半角（NFKC）
    - 下划线 / 连字符统一成空格 → ``hatsune-miku`` ≡ ``hatsune_miku`` ≡ ``hatsune miku``
    - 繁体 / 日文新字体汉字转简体（用词库里烘焙的 ``cjk_map``）→
      ``阿爾托莉雅`` ≡ ``阿尔托莉雅``、``博麗霊夢`` ≡ ``博丽灵梦``
    """
    text = unicodedata.normalize("NFKC", str(text or "")).strip().lower()
    text = re.sub(r"[\s_]+", " ", text)
    text = re.sub(r"\s*-\s*", " ", text)
    text = re.sub(r"\s+", " ", text)
    return _apply_cjk_map(text)


_CJK_MAP_CACHE = None


def _apply_cjk_map(text):
    """把繁体 / 日文新字体汉字替换成简体（词库烘焙的映射表）。"""
    global _CJK_MAP_CACHE
    if not text:
        return text
    if _CJK_MAP_CACHE is None:
        try:
            _CJK_MAP_CACHE = cjk_map()
        except Exception:
            _CJK_MAP_CACHE = {}
    if not _CJK_MAP_CACHE:
        return text
    return "".join(_CJK_MAP_CACHE.get(ch, ch) for ch in text)


def _word_tokens(text) -> set:
    """把名字切成可比较的词元。

    - ASCII 字母 / 数字：按连续段切（``hatsune miku`` → ``{"hatsune", "miku"}``）
    - 汉字：按**整段**切（``初音未来`` → ``{"初音未来"}``），
      这样 ``蕾姆`` 不会命中 ``拉姆蕾萨尔·瓦伦泰``（逐字切就会误判）
    - 假名：按**单字**切（``初音ミク`` → ``{"初音", "ミ", "ク"}``），
      这样 ``ミク`` 能命中 ``初音ミク``

    用来做**词边界匹配**：``ame`` 不应该命中 ``camellya``，
    ``miku`` 应该命中 ``hatsune miku``。
    """
    text = _apply_cjk_map(unicodedata.normalize("NFKC", str(text or "")).lower())
    out = set(re.findall(r"[a-z0-9]+", text))
    out.update(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff]+", text))
    out.update(re.findall(r"[\u3040-\u30ff]", text))
    return out


def _token_subset(needle_tokens, haystack_tokens) -> bool:
    """词元集合是否被完全包含（且 needle 非空）。"""
    if not needle_tokens:
        return False
    return needle_tokens.issubset(haystack_tokens)


_HAN_RUN = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]+")
_KANA_RUN = re.compile(r"[\u3040-\u30ff]+")


def _cjk_runs(text):
    """取出文本里的汉字整段与假名整段（用于前缀 / 后缀的温和匹配）。"""
    text = unicodedata.normalize("NFKC", str(text or ""))
    return _HAN_RUN.findall(text) + _KANA_RUN.findall(text)


def _cjk_affix_match(needle, value) -> bool:
    """汉字 / 假名的**前缀或后缀**匹配（比整词包含弱一档）。

    只在 needle 恰好是一段汉字（或假名）时启用，避免把
    ``蕾姆`` 匹配到 ``拉姆蕾萨尔·瓦伦泰`` 这种同字不同词的情况。
    """
    runs = _cjk_runs(needle)
    if len(runs) != 1:
        return False
    query = runs[0]
    if len(query) < 2:
        return False
    for run in _cjk_runs(value):
        if run.startswith(query) or run.endswith(query):
            return True
    return False


def resolve_level(value):
    """分级控件值 → ``(key, num, 中文名)``。

    ``随机`` 返回 ``(None, None, "随机")``（调用方自行抽档）。
    """
    if value is None:
        value = "全年龄"
    text = str(value).strip()
    if text in LEVEL_OPTIONS:
        return LEVEL_OPTIONS[text]
    for name, info in LEVEL_OPTIONS.items():
        if normalize(name) == normalize(text):
            return info
    return LEVEL_OPTIONS["全年龄"]


def slot_candidates(slot_key, level_num):
    """按档位收敛后的候选池。

    ``level_num >= 99``（不限）时返回全部候选；否则只留档位 ``<= level_num`` 的词。
    词库自带的 ``level`` 由构建脚本正则生成，会漏判大量擦边词（泳装 / 比基尼 /
    情趣内衣 / 巨乳 / 出汗等都被标成 0），因此这里统一走 ``_tag_level()`` 的
    三级判定（词库 → 登记表 → 本地启发式），而不是只信词库字段。
    """
    data = tag_slots().get(slot_key)
    if not data:
        return []
    items = data.get("items", [])
    if level_num is not None and level_num < 99:
        items = [it for it in items if _tag_level(it.get("en", "")) <= level_num]
    return items


def _unique_values(items, extra=()):
    """保序去重（按显示值）。"""
    seen = set()
    out = []
    for it in items:
        val = it["en"] if isinstance(it, dict) else str(it)
        if not val or val in seen:
            continue
        seen.add(val)
        out.append(val)
    for val in extra:
        if val and val not in seen:
            seen.add(val)
            out.append(val)
    return out


def slot_display_items(slot_key):
    """槽位候选项的 ``(中文显示值, 英文标签)`` 列表。

    下拉里**只显示中文**（用户要求），但生成的提示词仍然是英文标签。
    中文缺失时退回英文，保证任何一条候选都有可显示的名字。
    """
    items = tag_slots().get(slot_key, {}).get("items", [])
    out = []
    seen = set()
    for item in items:
        en = str(item.get("en") or "").strip()
        if not en:
            continue
        zh = str(item.get("zh") or "").strip() or en
        if zh in seen:
            continue
        seen.add(zh)
        out.append((zh, en))
    return out


def slot_display_map(slot_key):
    """显示值 → 英文标签 的反查表。

    同一显示值对应多个英文标签时取第一个（构建脚本已保证同槽位中文唯一）。
    """
    mapping = {}
    for zh, en in slot_display_items(slot_key):
        mapping.setdefault(zh, en)
    if slot_key == "quality":
        for label, preset in ANIMA_QUALITY_PRESET_LABELS.items():
            mapping.setdefault(label, preset)
    return mapping


def _quality_label(preset):
    """Anima 质量前缀 → 中文显示名（找不到就回显英文）。"""
    for label, value in ANIMA_QUALITY_PRESET_LABELS.items():
        if value == preset:
            return label
    return str(preset)


def _slot_hit_text(slot_key, english):
    """命中情况的展示文本：``中文（英文）``。

    中文与英文相同时只回显英文（避免「brown hair（brown hair）」这种噪声）。
    """
    english = str(english or "")
    if slot_key == "quality":
        zh = _quality_label(english)
        if zh == english:
            # 不是整条 Anima 前缀，而是候选表里的单个质量标签 → 查候选表的中文名
            for display, en in slot_display_items(slot_key):
                if en == english:
                    zh = display
                    break
        if zh == english:
            return english
        return "%s（%s）" % (zh, english)
    zh = ""
    for display, en in slot_display_items(slot_key):
        if en == english:
            zh = display
            break
    if not zh or zh == english:
        return english
    return "%s（%s）" % (zh, english)


def dropdown_values(slot_key):
    """某个槽位下拉的完整选项（首项恒为「随机」，其余是中文显示值）。"""
    values = [RANDOM_LABEL]
    values += [zh for zh, _en in slot_display_items(slot_key)]
    if slot_key == "quality":
        values += [label for label in ANIMA_QUALITY_PRESET_LABELS if label not in values]
    return values


def scene_preset_values():
    """「场景搭配」下拉的选项：首项「随机」，其余是造型台场景名。"""
    values = [RANDOM_LABEL]
    seen = set()
    for sc in scenes():
        name = (sc.get("name") or "").strip()
        if not name or sc.get("source") == "prompt_forge":
            continue
        if name in seen:
            continue
        seen.add(name)
        values.append(name)
    return values


def find_scene_preset(name):
    """按名字找场景搭配预设。"""
    wanted = str(name or "").strip()
    if not wanted:
        return None
    for sc in scenes():
        if (sc.get("name") or "").strip() == wanted:
            return sc
    return None


def match_character(query, library=None):
    """用字符串在角色库里命中。

    返回 ``(命中列表, 未命中列表)``；命中项是角色字典，未命中项是原始字符串。

    可命中的写法：

    - 中文名（简体）、中文名的繁体 / 连字符变体
    - 英文名、英文 tag、去作品括号的英文名
    - **日文名**（假名 / 日文汉字，来自词库的 ``aliases`` 字段）
    - 英文名的**词边界部分匹配**：``miku`` → ``hatsune miku``，
      ``gura`` → ``gawr gura``；但 ``ame`` **不会**命中 ``camellya``
      （词元不完全一致）
    """
    library = characters() if library is None else library
    text = str(query or "").strip()
    if not text:
        return [], []
    hits = []
    misses = []
    for part in re.split(r"[,，、;；]+", text):
        part = part.strip()
        if not part:
            continue
        needle = normalize(part)
        needle_tokens = _word_tokens(part)
        best = None
        best_score = 0
        for rec in library:
            score = 0
            # 逐字段比对：完全相等 > 词边界包含 > 汉字前后缀包含
            for field in ("name_zh", "char_zh", "name_en", "tag", "trigger"):
                value = normalize(rec.get(field))
                if not value:
                    continue
                if value == needle:
                    score = max(score, 5)
                elif _token_subset(needle_tokens, _word_tokens(value)):
                    score = max(score, 4)
                elif _cjk_affix_match(needle, value):
                    score = max(score, 3)
            # 别名（日文名 / 繁简 / 连字符变体）
            if score < 5:
                for alias in rec.get("aliases") or []:
                    value = normalize(alias)
                    if not value:
                        continue
                    if value == needle:
                        score = max(score, 5)
                    elif _token_subset(needle_tokens, _word_tokens(alias)):
                        score = max(score, 4)
                    elif _cjk_affix_match(needle, value):
                        score = max(score, 3)
            if score > best_score:
                best_score = score
                best = rec
        if best is not None:
            hits.append(best)
        else:
            misses.append(part)
    return hits, misses


def random_character(rng, library=None):
    """随机命中一位角色。"""
    library = characters() if library is None else library
    if not library:
        return None
    return library[rng.randrange(len(library))]


def character_appearance(rec, chosen_values, level_num, limit=3):
    """取角色的外观标签（发色 / 瞳色等），跳过与已选槽位重复的、人数类、超档的。

    ⚠️ 角色外观在词库里**不带档位字段**，所以这里统一走 ``_tag_level()`` 判定，
    否则 ``huge breasts`` / ``loli`` 这类词会绕过分级闸门。
    """
    if not rec:
        return []
    taken = {normalize(v) for v in chosen_values}
    out = []
    for item in rec.get("appearance") or []:
        en = (item.get("en") if isinstance(item, dict) else str(item)) or ""
        en = en.strip()
        if not en:
            continue
        norm = normalize(en)
        if norm in taken or norm in _COUNT_TAGS:
            continue
        if not _level_ok(en, level_num):
            continue
        out.append(en)
        taken.add(norm)
        if len(out) >= limit:
            break
    return out


def _preset_required_level(preset, tag):
    """场景搭配里某个标签实际需要的档位。

    取「预设自身的档位」与「标签自身档位」的**较大者**——预设是整体成人场景，
    里面的标签（``ahegao`` / ``clitoris`` 等）常常不在造型台的逐标签登记表里，
    单独看会当成 0 档放行。
    """
    preset_level = int(preset.get("level", 0) or 0)
    return max(preset_level, _tag_level(tag))


def preset_slot_values(preset, level_num=None):
    """场景搭配预设 → ``{slot_key: [标签, ...]}``。

    多个造型台字段可能落到同一槽位（例如 shot_size 与 viewpoint 都属镜头），
    这里**累加**而不是覆盖。

    ``level_num`` 不为 None 且 < 99 时，**超档标签直接剔除**——场景搭配是
    绕过槽位候选池的一条独立通路，不设闸门就会让全年龄档抽出成人内容。
    """
    out = OrderedDict()
    if not preset:
        return out
    for field, value in (preset.get("tags") or {}).items():
        slot = FIELD_TO_SLOT.get(field)
        if not slot or not value:
            continue
        for tag in split_tags(value):
            if level_num is not None and level_num < 99:
                if _preset_required_level(preset, tag) > level_num:
                    continue
            out.setdefault(slot, []).append(tag)
    return out


def preset_extra_tags(preset, level_num):
    """场景搭配预设的额外自由标签（``extra`` + ``scene_nl``），按档位过滤。"""
    extra = []
    if not preset:
        return extra
    for tag in split_tags(preset.get("extra") or ""):
        if level_num is not None and level_num < 99:
            if _preset_required_level(preset, tag) > level_num:
                continue
        extra.append(tag)
    nl = str(preset.get("scene_nl") or "").strip()
    if nl and (level_num is None or level_num >= 99 or _preset_required_level(preset, nl) <= level_num):
        extra.append(nl)
    return extra


def _level_index():
    """标签 → 档位 的倒排索引（缓存）。"""
    idx = _CACHE.get("__level_index__")
    if idx is None:
        idx = {}
        for slot in tag_slots().values():
            for item in slot.get("items", []):
                key = normalize(item.get("en"))
                if not key:
                    continue
                # 同一英文标签可能出现在多个槽位且档位不同（例如 heart-shaped
                # pupils 在 face 是 0、在 pose 是 3）。取最高档，否则全年龄档会
                # 因为「首写胜出」抽到实际属于高等级的词。
                idx[key] = max(idx.get(key, 0), int(item.get("level", 0)))
        _CACHE["__level_index__"] = idx
    return idx


def _tag_level(tag):
    """查标签的 NSFW 档位。

    取「词库 / 登记表里登记的基础档位」与「本地启发式判定」的**较大者**。

    词库自带的 ``level`` 由构建脚本正则生成，会漏判大量擦边词（泳装 / 情趣内衣 /
    巨乳等被标成 0）；如果像旧实现那样「首命中即返回」，一个 0 档词库条目会直接
    遮蔽登记表里的非 0 档和本地启发式的判定，让全年龄档漏出成人词。故这里把本地
    启发式作为**兜底底线**，无论基础档位来自词库还是登记表，都再与它取 max。

    注意：登记表本身含噪声（``1girl`` 被登记成 4、`pov` 3、`trembling` 3 等），
    所以**不**把登记表无条件 max 进基础档位——只有关键词库里根本没有、才退而
    使用登记表的值；本地启发式专门针对明显成人词，不会误伤这些中性词。
    """
    key = normalize(tag)
    if not key:
        return 0
    base = _level_index().get(key)
    if base is None:
        base = tag_levels().get(key)
    if base is None:
        return _local_grade(tag)
    return max(int(base), _local_grade(tag))


def _level_ok(tag, level_num):
    """标签是否在当前分级内（``level_num`` 为 None 或 ≥99 时一律放行）。"""
    if level_num is None or level_num >= 99:
        return True
    return _tag_level(tag) <= level_num


# 本地启发式：词库里没登记过的标签（如场景搭配的 extra）用它判档
# 词库由构建脚本的正则判档，但它漏掉了大量 NSFW 词（泳装 / 比基尼 / 情趣内衣 /
# 巨乳 / 臀部特写 / 出汗 等被标成 level=0），全年龄档因此照常输出成人内容。
# 外部数据源缺失、词库不可重建 → 这些补判必须落在运行时启发式里。
# 注意：新增词一律用「精确词」或带上下文的组合，避免误伤中性词
#（``analog photo`` 含 ``anal``、``hololive`` 含 ``loli``、``gothic lolita`` 含 ``loli``）。
# 整组用 \b(...)\b 包住，单个词都是「独立单词」匹配，不会误伤
# ``analog photo`` / ``hololive`` / ``gothic lolita`` / ``class`` 这类中性词。
_LOCAL_EXPLICIT = re.compile(
    r"\b(nude|naked|topless|bottomless|nipples?|areola|pussy|vagina|penis|anal|"
    r"cum|semen|masturbat\w*|fellatio|cunnilingus|handjob|paizuri|dildo|vibrator|"
    r"bondage|shibari|slut|whore|creampie|panties|nsfw|explicit|pasties|cameltoe|"
    r"pubic hair|underboob|sideboob|crotchless|upskirt|genitals|sex\w*|fuck\w*|"
    r"loli|lolicon|childlike|"
    # 构建脚本正则漏判、词库里被错标成 level=0 的成人向词
    r"ass|butt|lingerie|ecchi|gigantic breasts|gigantic tits|"
    r"heart-shaped pupils|exposed breasts?|breasts? out|one breast out)\b",
    re.I,
)
_LOCAL_SUGGESTIVE = re.compile(
    r"\b(see-through|transparent|translucent|sheer|revealing|cleavage|unbuttoned|"
    r"open shirt|open jacket|large breasts?|big breasts?|huge breasts?|"
    r"medium breasts?|small breasts?|thighhighs|stockings|thigh strap|"
    r"wet clothes|wet shirt|strapless|short skirt|miniskirt|sensitive|"
    # 构建脚本正则漏判、词库里被错标成 level=0 的擦边词
    r"swimsuits?|bikinis?|swim shorts|wetsuit|"
    r"sweating|sweatdrop|wet hair|wet body|"
    r"garter belt|garter straps|corset|babydoll|pantyhose|chemise|underwear|bra)\b",
    re.I,
)

# 本地启发式 · 过激档（L3）：造型台只登记了 ``tentacles``（复数），
# 派生词（``tentacle hair`` 等）查不到登记 → 必须在这里兜住，
# 否则会漏进全年龄档（角色外观通路已实测泄漏）。
_LOCAL_HARDCORE = re.compile(
    r"\b(tentacle\w*|deep penetration|gangbang|group sex|ahegao|"
    r"orgasm\w*|squirting|netorare|after sex)\b",
    re.I,
)


def _local_grade(tag):
    """本地启发式档位判定（0 全年龄 / 1 擦边 / 2 成人 / 3 过激）。"""
    text = str(tag or "")
    if _LOCAL_HARDCORE.search(text):
        return 3
    if _LOCAL_EXPLICIT.search(text):
        return 2
    if _LOCAL_SUGGESTIVE.search(text):
        return 1
    return 0


def split_tags(text):
    """把逗号串拆成标签列表。"""
    return [t.strip() for t in re.split(r"[,，]+", str(text or "")) if t.strip()]


# ---------------------------------------------------------------------------
# 五、节点
# ---------------------------------------------------------------------------


class AnimeRandomPromptNode:
    """随机提示词(Anime)：按分级 + 参数配置 + 角色文本命中生成 Anima 提示词。"""

    CATEGORY = "YTmmi/text"
    DESCRIPTION = (
        "随机生成 Anima 用的英文 Danbooru 标签提示词：下拉配置 + 角色文本命中，"
        "五级 NSFW 闸门先收敛候选池再抽取，详细 18 槽位 / 简略 8 槽位"
    )

    @classmethod
    def INPUT_TYPES(cls):
        required = {
            "分级": (list(LEVEL_OPTIONS.keys()), {"default": "全年龄"}),
            "详细程度": (["详细（18 槽位）", "简略（8 槽位）"], {"default": "详细（18 槽位）"}),
            "角色": ("STRING", {"default": "", "multiline": False}),
            "种子": ("INT", {"default": 0, "min": 0, "max": 0xFFFFFFFF, "control_after_generate": True}),
            "场景搭配": (scene_preset_values(), {"default": RANDOM_LABEL}),
            "质量": (dropdown_values("quality"), {"default": RANDOM_LABEL}),
            "画师": (dropdown_values("artist"), {"default": RANDOM_LABEL}),
            "人数": (dropdown_values("count"), {"default": RANDOM_LABEL}),
            "发型": (dropdown_values("hair"), {"default": RANDOM_LABEL}),
            "面部": (dropdown_values("face"), {"default": RANDOM_LABEL}),
            "表情": (dropdown_values("expression"), {"default": RANDOM_LABEL}),
            "体型": (dropdown_values("body"), {"default": RANDOM_LABEL}),
            "服装": (dropdown_values("clothing"), {"default": RANDOM_LABEL}),
            "配饰": (dropdown_values("accessory"), {"default": RANDOM_LABEL}),
            "姿势": (dropdown_values("pose"), {"default": RANDOM_LABEL}),
            "场景": (dropdown_values("environment"), {"default": RANDOM_LABEL}),
            "天气": (dropdown_values("weather"), {"default": RANDOM_LABEL}),
            "道具": (dropdown_values("props"), {"default": RANDOM_LABEL}),
            "光影": (dropdown_values("lighting"), {"default": RANDOM_LABEL}),
            "镜头": (dropdown_values("camera"), {"default": RANDOM_LABEL}),
            "构图": (dropdown_values("composition"), {"default": RANDOM_LABEL}),
            "文本描述": (dropdown_values("text"), {"default": RANDOM_LABEL}),
            "负向": (dropdown_values("negative"), {"default": RANDOM_LABEL}),
        }
        return {"required": required}

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("提示词", "命中情况", "负向提示词")
    FUNCTION = "anime_random_prompt"
    OUTPUT_NODE = False
    OUTPUT_IS_LIST = (False, False, False)
    SEARCH_ALIASES = [
        "anime random prompt",
        "random prompt",
        "随机提示词",
        "随机提示词(Anime)",
        "anima prompt",
        "danbooru tags",
        "动漫提示词",
    ]

    # -- 槽位解析 ----------------------------------------------------------

    def _resolve_slot(self, slot_key, raw, rng, level_num, report_lines):
        """解析单个槽位。

        返回 ``{"values": [标签, ...], "explicit": bool}``；``explicit`` 表示
        用户显式指定（此时场景搭配预设不再覆盖它）。

        ``raw`` 可以是下拉里的**中文显示值**，也可以是英文标签本身
        （老工作流 / 手写英文都能用）；最终一律换算成英文标签输出。
        """
        label = SLOT_LABELS.get(slot_key, slot_key)
        value = "" if raw is None else str(raw).strip()

        if not value or value == RANDOM_LABEL:
            # 质量槽随机 → 抽一条 Anima 质量前缀（单标签不成段）
            if slot_key == "quality":
                preset = ANIMA_QUALITY_PRESETS[rng.randrange(len(ANIMA_QUALITY_PRESETS))]
                report_lines.append(
                    "[%s] 随机 → %s（%s）"
                    % (label, _quality_label(preset), preset)
                )
                return {"values": [preset], "explicit": False}
            pool = slot_candidates(slot_key, level_num)
            if not pool:
                report_lines.append("[%s] 无可用候选（当前分级下候选池为空）" % label)
                return {"values": [], "explicit": False}
            picked = pool[rng.randrange(len(pool))]
            english = picked.get("en", "")
            report_lines.append(
                "[%s] 随机 → %s" % (label, _slot_hit_text(slot_key, english))
            )
            return {"values": [english], "explicit": False}

        # 中文显示值 → 英文标签
        display_map = slot_display_map(slot_key)
        english = display_map.get(value)
        if english is None:
            english = value  # 用户直接写了英文标签
        # 质量槽允许直接选整条 Anima 前缀（不在候选表里）
        if slot_key == "quality" and english in ANIMA_QUALITY_PRESETS:
            report_lines.append(
                "[%s] 指定 → %s（%s）" % (label, _quality_label(english), english)
            )
            return {"values": [english], "explicit": True}

        # 指定值：在候选表里精确找（大小写不敏感）
        found = None
        for item in tag_slots().get(slot_key, {}).get("items", []):
            if normalize(item.get("en")) == normalize(english):
                found = item
                break
        if found is None:
            report_lines.append("[%s] 指定「%s」不在词库中 → 退回随机" % (label, value))
            return self._resolve_slot(slot_key, RANDOM_LABEL, rng, level_num, report_lines)

        # 与候选池一致：用 _tag_level() 的三级判定，而不是只信词库自带的
        # level 字段（该字段会漏判泳装 / 情趣内衣 / 巨乳等词，导致用户在
        # 全年龄档显式指定这些词时仍被放行）。
        level = _tag_level(english)
        if level_num is not None and level_num < 99 and level > level_num:
            report_lines.append(
                "[%s] 指定「%s」超出当前分级（需要 L%d）→ 已忽略，改随机"
                % (label, value, level)
            )
            return self._resolve_slot(slot_key, RANDOM_LABEL, rng, level_num, report_lines)

        report_lines.append("[%s] 指定 → %s" % (label, _slot_hit_text(slot_key, english)))
        return {"values": [english], "explicit": True}

    # -- 主流程 ------------------------------------------------------------

    def anime_random_prompt(self, **kwargs):
        level_key, level_num, level_zh = resolve_level(kwargs.get("分级"))
        seed = int(kwargs.get("种子") or 0)
        rng = random.Random(seed)

        if level_key is None:  # 「随机」分级
            level_num = rng.choice([0, 1, 2, 3, 4])
            level_key = {0: "sfw", 1: "suggestive", 2: "explicit", 3: "hardcore", 4: "extreme"}[level_num]
            level_zh = {0: "全年龄", 1: "擦边", 2: "成人", 3: "过激", 4: "极端"}[level_num]

        detailed = str(kwargs.get("详细程度", "")).startswith("详细")
        active_slots = list(SLOT_LABELS.keys()) if detailed else [s for s in SLOT_LABELS if s in BRIEF_SLOTS]

        report_lines = []
        report_lines.append("分级：%s（%s）" % (level_zh, level_key))
        report_lines.append("详细程度：%s（%d 个槽位）" % ("详细" if detailed else "简略", len(active_slots)))
        report_lines.append("种子：%d" % seed)
        report_lines.append("")

        # --- 场景搭配预设（独立控件）---
        preset_name = str(kwargs.get("场景搭配", "") or "").strip()
        preset = None
        if preset_name and preset_name != RANDOM_LABEL:
            preset = find_scene_preset(preset_name)
            if preset is None:
                report_lines.append("[场景搭配] 未找到「%s」→ 按随机处理" % preset_name)
            elif level_num is not None and level_num < 99 and int(preset.get("level", 0) or 0) > level_num:
                report_lines.append(
                    "[场景搭配] 指定「%s」需要 L%d，超出当前分级 → 已忽略"
                    % (preset.get("name"), int(preset.get("level", 0) or 0))
                )
                preset = None
            else:
                report_lines.append("[场景搭配] 指定 → %s" % preset.get("name"))
        else:
            pool = [
                sc
                for sc in scenes()
                if sc.get("source") != "prompt_forge"
                and (level_num is None or level_num >= 99 or int(sc.get("level", 0)) <= level_num)
            ]
            if pool:
                preset = pool[rng.randrange(len(pool))]
                report_lines.append("[场景搭配] 随机 → %s" % preset.get("name"))
            else:
                report_lines.append("[场景搭配] 当前分级下无可用预设 → 跳过")

        preset_slots = preset_slot_values(preset, level_num) if preset is not None else OrderedDict()

        # --- 逐槽位解析 ---
        chosen = OrderedDict()
        for slot_key in SLOT_LABELS:
            if slot_key not in active_slots:
                continue
            if slot_key == "negative":
                continue
            label = SLOT_LABELS[slot_key]
            hit = self._resolve_slot(slot_key, kwargs.get(label), rng, level_num, report_lines)
            values = list(hit["values"])
            # 场景搭配只填补「用户没有显式指定」的槽位，且不覆盖已选值
            if slot_key in preset_slots and not hit["explicit"]:
                for tag in preset_slots[slot_key]:
                    if normalize(tag) not in {normalize(v) for v in values}:
                        values.append(tag)
                        report_lines.append(
                            "[%s] 场景搭配「%s」→ %s" % (label, preset.get("name"), tag)
                        )
            if values:
                chosen[slot_key] = values

        if not detailed:
            report_lines.append(
                "（简略模式未启用槽位：%s）"
                % "、".join(SLOT_LABELS[s] for s in SLOT_LABELS if s not in active_slots)
            )
        report_lines.append("")

        # --- 角色：文本命中 / 空输入随机 ---
        role_query = str(kwargs.get("角色", "") or "").strip()
        role_parts = []
        role_rec = None
        if role_query:
            hits, misses = match_character(role_query)
            for rec in hits:
                label = rec.get("name_zh") or rec.get("name_en") or rec.get("tag")
                trigger = rec.get("trigger") or rec.get("tag") or rec.get("name_en") or ""
                if trigger:
                    role_parts.append(trigger)
                role_rec = rec
                report_lines.append("[角色] 文本命中「%s」→ %s" % (role_query, label))
            for miss in misses:
                report_lines.append("[角色] 未命中「%s」" % miss)
            if not hits:
                report_lines.append("[角色] 未命中任何角色 → 随机命中")
                role_rec = random_character(rng)
                if role_rec is not None:
                    trigger = role_rec.get("trigger") or role_rec.get("tag") or role_rec.get("name_en") or ""
                    if trigger:
                        role_parts.append(trigger)
                    report_lines.append(
                        "[角色] 随机 → %s"
                        % (role_rec.get("name_zh") or role_rec.get("name_en") or role_rec.get("tag"))
                    )
        else:
            role_rec = random_character(rng)
            if role_rec is not None:
                trigger = role_rec.get("trigger") or role_rec.get("tag") or role_rec.get("name_en") or ""
                if trigger:
                    role_parts.append(trigger)
                report_lines.append(
                    "[角色] 空输入随机 → %s"
                    % (role_rec.get("name_zh") or role_rec.get("name_en") or role_rec.get("tag"))
                )

        # 角色外观标签（发色 / 瞳色等），跳过与已选重复的
        chosen_values = [v for values in chosen.values() for v in values]
        appearance = character_appearance(role_rec, chosen_values, level_num)
        if appearance:
            role_parts.extend(appearance)
            report_lines.append("[角色] 外观 → %s" % ", ".join(appearance))
        report_lines.append("")

        # --- 组装正向提示词 ---
        parts = []
        for tag in role_parts:
            tag = str(tag).strip()
            if tag and tag not in parts:
                parts.append(tag)
        for slot_key in POSITIVE_ORDER:
            if slot_key not in active_slots:
                continue
            for value in chosen.get(slot_key, []):
                value = str(value).strip()
                if not value:
                    continue
                if slot_key == "artist" and not value.startswith("@"):
                    value = "@" + value  # Anima 画师标签必须带 @
                if value not in parts:
                    parts.append(value)
        for tag in preset_extra_tags(preset, level_num):
            tag = str(tag).strip()
            if tag and tag not in parts:
                parts.append(tag)

        # --- 统一总闸：拼串前逐段复核每个逗号子标签的档位 ---
        # 角色 trigger / 质量前缀 / 场景 extra / 画师 @标签 都会以「整串」进入
        # parts（例如 "shiroko (swimsuit), blue archive"、"masterpiece, ...,
        # safe"）。候选池与各条独立通路虽已各自设闸，但角色 trigger 是第四条
        # 未守闸通路、且整串因含逗号/括号查不到任何词表会被一律判 0 档。故在
        # 最终拼串前把每个 part 先按逗号拆成子标签，逐段 _level_ok() 复核，
        # 剔除超档子标签并写入报告；未超档的子标签原样拼回（保证质量前缀等
        # 整串输出的字面值不发生变化）。
        if level_num is None or level_num >= 99:
            gated_parts = list(parts)
        else:
            gated_parts = []
            for part in parts:
                kept = []
                for sub in split_tags(part):
                    if not _level_ok(sub, level_num):
                        report_lines.append("[分级闸门] 已剔除超档标签「%s」" % sub)
                        continue
                    kept.append(sub)
                if kept:
                    gated_parts.append(", ".join(kept))

        positive = ", ".join(gated_parts)

        # --- 负向提示词 ---
        negatives = list(BASELINE_NEGATIVES)
        if detailed:
            neg_hit = self._resolve_slot(
                "negative", kwargs.get("负向"), rng, level_num, report_lines
            )
            for value in neg_hit["values"]:
                if value not in negatives:
                    negatives.append(value)
        else:
            report_lines.append("[负向] 简略模式未启用 → 仅输出固定负向基线")
        negative = ", ".join(negatives)

        report_lines.append("")
        report_lines.append("正向标签数：%d" % len(gated_parts))
        report_lines.append("负向标签数：%d" % len(negatives))
        report = "\n".join(report_lines)

        return (positive, report, negative)


NODE_CLASS_MAPPINGS = {
    "AnimeRandomPromptNode": AnimeRandomPromptNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "AnimeRandomPromptNode": "随机提示词(Anime)",
}

__all__ = [
    "AnimeRandomPromptNode",
    "SLOT_LABELS",
    "BRIEF_SLOTS",
    "POSITIVE_ORDER",
    "FIELD_TO_SLOT",
    "LEVEL_OPTIONS",
    "ANIMA_QUALITY_PRESETS",
    "ANIMA_QUALITY_PRESET_LABELS",
    "BASELINE_NEGATIVES",
    "normalize",
    "resolve_level",
    "slot_candidates",
    "slot_display_items",
    "slot_display_map",
    "dropdown_values",
    "scene_preset_values",
    "find_scene_preset",
    "match_character",
    "random_character",
    "character_appearance",
    "preset_slot_values",
    "preset_extra_tags",
    "split_tags",
    "tag_slots",
    "tag_levels",
    "characters",
    "scenes",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
