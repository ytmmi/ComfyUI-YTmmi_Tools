# -*- coding: utf-8 -*-
"""构建「随机提示词(Anime)」节点用的离线词库。

数据来源（两个外部词库，运行时**不联网**）：

1. ``D:\\下载\\Edge下载\\提示词生成器.html``（Prompt Forge，单文件标签工作台）
   —— 19 个分类的「英文|中文」标签表、507 个游戏角色（带 auto 外观标签）、
   26 个场景预设、中文词典。
2. ``https://github.com/lingdongbudong/Comfyui-Anima-Wardrobe-V5``（v5.0.8，GPL-3.0）
   —— 15 段 / 57 字段 / 1134 选项的造型台词库、逐标签档位表（levels.json）、
   2390 位角色库、271 条场景搭配。档位表与词库**只取数据**，不复制其代码。

输出（全部落在 ``node/text/data/``，随插件分发）：

- ``anime_prompt_tags.json``      合并后的槽位候选词（按槽位分组，带中文标签）
- ``anime_prompt_levels.json``    逐标签 / 逐选项的 NSFW 档位表
- ``anime_prompt_characters.json`` 合并后的角色库（含中英文名 / trigger / 外观）
- ``anime_prompt_scenes.json``     场景搭配预设（V5 271 条 + Prompt Forge 26 条）

用法（一次性，需要本机存在上面两个源）::

    python tools/build_anime_prompt_lib.py --html "D:\\下载\\Edge下载\\提示词生成器.html" \\
        --wardrobe "C:\\path\\to\\Comfyui-Anima-Wardrobe-V5"

脚本**不参与运行时**：节点只读生成好的 JSON。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT_DIR = os.path.join(ROOT, "node", "text", "data")

# ---------------------------------------------------------------------------
# 一、槽位定义（详细 18 槽 / 简略 8 槽）
# ---------------------------------------------------------------------------

# 槽位 id → 中文显示名（前端控件名用这些）
SLOTS = OrderedDict(
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

# 简略模式生效的 8 个槽位（其余槽位走「角色外观带出 / 自动随机」）
BRIEF_SLOTS = ("quality", "artist", "clothing", "pose", "environment", "lighting", "camera", "composition")

# Prompt Forge 分类 → 槽位（PF 独有分类，一一对应）
PF_CATEGORY_TO_SLOT = {
    "style": None,          # 质量槽单独取前 16 条
    "artist": "artist",
    "composition": "composition",
    "camera": "camera",
    "lighting": "lighting",
    "base": "count",
    "body": "body",
    "pose": "pose",
    "expression": "expression",
    "hair": "hair",
    "face": "face",
    "clothing": "clothing",
    "accessory": "accessory",
    "environment": "environment",
    "weather": "weather",
    "props": "props",
    "negative": "negative",
    "extra": "clothing",
    "text": "text",
}

# PF「人物基础」分类是**混装**的：人数 / 种族职业 / 基础外貌混在一起。
# 直接当「人数」槽用会抽出「dark skin」「animal ears」这种明显错位的词，
# 所以这里按词表把它拆开，各归各槽。
PF_BASE_COUNT_TAGS = {
    "1girl", "1boy", "2girls", "2boys", "3girls",
    "multiple girls", "multiple boys", "solo",
    "male focus", "female focus", "androgynous",
    "mature female", "mature male", "child", "teen", "adult", "elderly",
    "solo focus", "couple", "twins", "siblings",
}

PF_BASE_LOOK_TAGS = {
    "glasses", "freckles", "tan", "pale skin", "dark skin", "tall", "short",
}

# 剩下的（种族 / 职业 / 身份）归到「体型」槽（身份与体态同属人物基本面）
PF_BASE_IDENTITY_SLOT = "body"

# ---------------------------------------------------------------------------
# 中文标签修正表
# ---------------------------------------------------------------------------
# 1) Prompt Forge 里有一批画师笔名，中文列直接写的是英文原名（没有可译中文），
#    这里统一加「画师」前缀，保证每个选项都有中文标识；
# 2) 有一批**同槽位中文重名**的选项（例如 slip dress / camisole dress 都是
#    「吊带裙」），下拉里会出现两个一模一样的条目、无法分辨对应哪个英文标签，
#    这里给它们分别起可区分的中文名。
ZH_OVERRIDES = {
    # —— 画师笔名（源数据的中文列 == 英文原名）——
    "wlop": "画师WLOP",
    "artgerm": "画师Artgerm",
    "huke": "画师huke",
    "redjuice": "画师redjuice",
    "ask (artist)": "画师ask",
    "pako": "画师pako",
    "lack": "画师lack",
    "noodle": "画师noodle",
    "ciloranko": "画师ciloranko",
    "modare": "画师modare",
    "rossdraws": "画师RossDraws",
    "sakimichan": "画师Sakimichan",
    "yuumei": "画师Yuumei",
    "loish": "画师Loish",
    "clamp": "画师CLAMP",
    "neco": "画师neco",
    "lpip": "画师Lpip",
    "mika pikazo": "画师Mika Pikazo",
    "saitom": "画师saitom",
    "rurudo": "画师rurudo",
    "anmi": "画师anmi",
    "hisasi": "画师hisasi",
    "tony taka": "画师Tony Taka",
    "atey ghailan": "画师Atey Ghailan",
    "sam yang": "画师Sam Yang",
    # —— 数字组合（源数据写的是「3P」「4P」）——
    "threesome": "三人同框",
    "foursome": "四人同框",
    # —— 同槽位中文重名：拆成可区分的中文名 ——
    "face paint": "面部油彩",
    "facepaint": "面部彩绘",
    "smirk": "坏笑",
    "evil smile": "邪笑",
    "disgusted": "厌恶",
    "disgust": "嫌恶",
    "slip dress": "吊带长裙",
    "camisole dress": "吊带连衣裙",
    "sundress": "太阳裙",
    "pinafore": "围裙式连衣裙",
    "suspender skirt": "背带裙",
    "maid outfit": "女仆装束",
    "maid": "女仆",
    "nurse uniform": "护士制服",
    "nurse": "护士",
    "qipao": "旗袍",
    "china dress": "中式连衣裙",
    "ruffles": "荷叶边",
    "frills": "褶边",
    "frilled": "带褶边的",
    "peace sign": "比耶手势",
    "v": "V手势",
    "covering mouth": "遮住嘴巴",
    "covering own mouth": "捂住自己的嘴",
    "looking down": "视线向下",
    "head down": "低着头",
    "gymnasium": "室内体育馆",
    "stadium": "体育场",
    "locker room": "储物更衣室",
    "changing room": "更衣间",
    "cinema": "电影院",
    "movie theater": "电影放映厅",
    "rim light": "轮廓光",
    "rim lighting": "边缘轮廓光",
    "fisheye lens": "鱼眼镜头",
    "fisheye": "鱼眼效果",
}


# 造型台字段 → 槽位
V5_FIELD_TO_SLOT = {
    "count": "count",
    "hair_len": "hair",
    "hair_color": "hair",
    "hair_curl": "hair",
    "eyes_color": "face",
    "emotion": "expression",
    "eye_gaze": "expression",
    "figure": "body",
    "skin": "body",
    "leg": "body",
    "makeup": "face",
    "nails": "accessory",
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
    "weather": "weather",
    "light_fx": "lighting",
    "nl": "text",
}

# 造型台里与「人数」同段的 role 字段：角色走角色库，不进候选词
V5_SKIP_FIELDS = {"role", "n_canon"}

# ---------------------------------------------------------------------------
# 二、自研 NSFW 档位判定（与造型台的判定表**互不依赖**，只兜底未登记的标签）
# ---------------------------------------------------------------------------

EXPLICIT_PATTERNS = [
    r"\bnude\b", r"\bnaked\b", r"\btopless\b", r"\bbottomless\b", r"\bnipples?\b",
    r"\bareola\b", r"\bpussy\b", r"\bvagina\b", r"\bpenis\b", r"\banal\b",
    r"\bcum\b", r"\bsemen\b", r"\bmasturbat", r"\bfellatio\b", r"\bcunnilingus\b",
    r"\bhandjob\b", r"\bpaizuri\b", r"\bdildo\b", r"\bvibrator\b", r"\bbondage\b",
    r"\bshibari\b", r"\bslut\b", r"\bwhore\b", r"\bcreampie\b", r"\bpanties\b",
    r"\bspread legs\b", r"\bspread pussy\b", r"\bsex(ual)?\b", r"\bfuck",
    r"\bpussy juice\b", r"\bchastity\b", r"\bpasties\b", r"\bcameltoe\b",
    r"\bpubic hair\b", r"\bunderboob\b", r"\bsideboob\b", r"\bcrotchless\b",
    r"\bbreasts? out\b", r"\bone breast out\b", r"\bupskirt\b", r"\bgenitals\b",
    r"\bnsfw\b", r"\bexplicit\b", r"\brating\b",
]

SUGGESTIVE_PATTERNS = [
    r"\bsee-through\b", r"\btransparent\b", r"\btranslucent\b", r"\bsheer\b",
    r"\brevealing\b", r"\bcleavage\b", r"\bunbuttoned\b", r"\bopen shirt\b",
    r"\bopen jacket\b", r"\bsee through\b", r"\blarge breasts?\b", r"\bbig breasts?\b",
    r"\bhuge breasts?\b", r"\bmedium breasts?\b", r"\bsmall breasts?\b",
    r"\bbig breasts\b", r"\bsmall breasts\b", r"\bmedium breasts\b",
    r"\bthighhighs\b", r"\bstockings\b", r"\bthigh strap\b",
    r"\bwet clothes\b", r"\bwet shirt\b", r"\bstrapless\b",
    r"\bshort skirt\b", r"\bminiskirt\b", r"\bsensitive\b",
]

HARDCORE_PATTERNS = [
    r"\borgasm\b", r"\borgasmic\b", r"\bcreampie\b", r"\bmasturbat",
    r"\bfellatio\b", r"\bpenetrat", r"\bdeepthroat\b", r"\banal sex\b",
    r"\bsex act\b", r"\bsexual intercourse\b", r"\bdildo\b", r"\bvibrator\b",
    r"\bbondage\b", r"\bshibari\b", r"\bstrapp-on\b", r"\bstrap-on\b",
    r"\btentacle\b", r"\bgangbang\b", r"\bcreampie\b",
]

EXTREME_PATTERNS = [
    r"\borgy\b", r"\bgroup sex\b", r"\bmultiple girls\b", r"\bmultiple boys\b",
    r"\bgangbang\b", r"\bwhore\b", r"\bslut\b", r"\bsex slave\b",
    r"\bextreme insert\b", r"\btentacle\b", r"\bdeep penetration\b",
]

_EXPL_RE = re.compile("|".join(EXPLICIT_PATTERNS))
_SUGG_RE = re.compile("|".join(SUGGESTIVE_PATTERNS))
_HARD_RE = re.compile("|".join(HARDCORE_PATTERNS))
_EXTREME_RE = re.compile("|".join(EXTREME_PATTERNS))


def self_grade(text: str) -> int:
    """自研档位判定：0 全年龄 / 1 擦边 / 2 成人 / 3 过激 / 4 极端。

    ⚠️ 只用于**兜底**：造型台 ``levels.json`` 已登记的标签优先用它的判定，
    这里只补登记表之外的词（Prompt Forge 词库基本都不在造型台表里）。
    """
    low = (text or "").lower()
    if _EXTREME_RE.search(low):
        return 4
    if _HARD_RE.search(low):
        return 3
    if _EXPL_RE.search(low):
        return 2
    if _SUGG_RE.search(low):
        return 1
    return 0


# ---------------------------------------------------------------------------
# 三、Prompt Forge HTML 解析
# ---------------------------------------------------------------------------

PF_TAG_BLOCK = re.compile(
    r"window\.PG_TAGS\s*=\s*\(window\.PG_TAGS\s*\|\|\s*\[\]\)\.concat\(\[(.*?)\]\);",
    re.S,
)
PF_CAT_DQ = re.compile(r'\{\s*id\s*:\s*"([^"]*)"\s*,\s*name\s*:\s*"([^"]*)"\s*,\s*icon\s*:\s*"([^"]*)"\s*,\s*tags\s*:\s*`([^`]*)`\s*\}')
PF_CAT_SQ = re.compile(r"\{\s*id\s*:\s*'([^']*)'\s*,\s*name\s*:\s*'([^']*)'\s*,\s*icon\s*:\s*'([^']*)'\s*,\s*tags\s*:\s*`([^`]*)`\s*\}")
PF_CHAR_BLOCK = re.compile(
    r"window\.PG_CHARACTERS\s*=\s*\(window\.PG_CHARACTERS\s*\|\|\s*\[\]\)\.concat\(\[(.*?)\]\);",
    re.S,
)
PF_CHAR_OBJ = re.compile(
    r'\{game:"([^"]*)",\s*gameTag:"([^"]*)",\s*name:"([^"]*)",\s*tag:"([^"]*)",'
    r'\s*charZh:"([^"]*)",\s*auto:"([^"]*)"\}'
)
PF_PRESET_BLOCK = re.compile(
    r"window\.PG_PRESETS\s*=\s*\(window\.PG_PRESETS\s*\|\|\s*\[\]\)\.concat\(\[(.*?)\]\);",
    re.S,
)
PF_PRESET_OBJ = re.compile(r'\{name:"([^"]*)",\s*desc:"([^"]*)",\s*tags:"([^"]*)"\}')


def _split_tag_lines(body: str):
    for line in body.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        if "|" not in line:
            yield line, ""
            continue
        en, zh = line.split("|", 1)
        yield en.strip(), zh.strip()


def parse_prompt_forge(html_path: str):
    raw = open(html_path, encoding="utf-8").read()

    categories = OrderedDict()
    for block in PF_TAG_BLOCK.findall(raw):
        for cm in list(PF_CAT_DQ.finditer(block)) + list(PF_CAT_SQ.finditer(block)):
            cid, cname, icon, body = cm.groups()
            items = list(_split_tag_lines(body))
            if cid in categories:
                categories[cid]["items"].extend(items)
            else:
                categories[cid] = {"name": cname, "icon": icon, "items": items}

    characters = []
    for block in PF_CHAR_BLOCK.findall(raw):
        for game, game_tag, name, tag, char_zh, auto in PF_CHAR_OBJ.findall(block):
            auto_items = []
            for chunk in auto.split(";"):
                chunk = chunk.strip()
                if not chunk:
                    continue
                if "|" in chunk:
                    en, zh = chunk.split("|", 1)
                    auto_items.append({"en": en.strip(), "zh": zh.strip()})
                else:
                    auto_items.append({"en": chunk, "zh": ""})
            characters.append(
                {
                    "name_zh": name,
                    "char_zh": char_zh,
                    "name_en": tag.split(" (")[0] if tag else "",
                    "tag": tag,
                    "work": game,
                    "work_tag": game_tag,
                    "source": "prompt_forge",
                    "appearance": auto_items,
                }
            )

    presets = []
    for block in PF_PRESET_BLOCK.findall(raw):
        for name, desc, tags in PF_PRESET_OBJ.findall(block):
            items = []
            for chunk in tags.split(";"):
                chunk = chunk.strip()
                if not chunk:
                    continue
                if "|" in chunk:
                    en, zh = chunk.split("|", 1)
                    items.append({"en": en.strip(), "zh": zh.strip()})
                else:
                    items.append({"en": chunk, "zh": ""})
            presets.append({"name": name, "desc": desc, "items": items, "source": "prompt_forge"})

    return categories, characters, presets


# ---------------------------------------------------------------------------
# 四、造型台（V5）解析
# ---------------------------------------------------------------------------


def parse_wardrobe(repo: str):
    def load(rel):
        with open(os.path.join(repo, rel), "r", encoding="utf-8") as fh:
            return json.load(fh)

    pools = load(os.path.join("presets", "anima_v4_pools.json"))
    levels = load(os.path.join("presets", "anima_v4_levels.json"))
    chars = load(os.path.join("presets", "anima_v4_characters.json"))
    scenes = load(os.path.join("presets", "anima_v4_scenes.json"))

    v5_options = []  # [{slot, field, zh, en, level}]
    for sec in pools.get("sections", []):
        for fld in sec.get("fields", []):
            key = fld.get("key", "")
            if key in V5_SKIP_FIELDS:
                continue
            slot = V5_FIELD_TO_SLOT.get(key)
            if slot is None:
                continue
            field_levels = levels.get("option_levels", {}).get(key, {})
            for opt in fld.get("opts", []) or []:
                if not opt:
                    continue
                zh = opt[0] if len(opt) > 0 else ""
                en = opt[1] if len(opt) > 1 else ""
                en = (en or "").strip()
                if not en:
                    continue
                v5_options.append(
                    {
                        "slot": slot,
                        "field": key,
                        "zh": (zh or "").strip(),
                        "en": en,
                        "level": int(field_levels.get(en, 0)),
                    }
                )

    tag_levels = {str(k): int(v) for k, v in (levels.get("tag_levels") or {}).items()}

    v5_characters = []
    for rec in chars.get("characters", []) or []:
        v5_characters.append(
            {
                "name_zh": rec.get("zh") or "",
                "char_zh": rec.get("zh") or "",
                "name_en": rec.get("name") or "",
                "tag": rec.get("tag") or "",
                "trigger": rec.get("trigger") or "",
                "work": rec.get("work") or "",
                "source": "anima_wardrobe_v5",
                "hair": rec.get("hair") or "",
                "eyes": rec.get("eyes") or "",
                "appearance": [
                    {"en": t, "zh": ""} for t in (rec.get("tags") or []) if isinstance(t, str)
                ],
            }
        )

    v5_scenes = []
    for rec in scenes.get("scenes", []) or []:
        v5_scenes.append(
            {
                "id": rec.get("id") or "",
                "name": rec.get("zh") or rec.get("id") or "",
                "desc": rec.get("desc") or "",
                "group": rec.get("group") or "",
                "level": int(rec.get("level") or 0),
                "tags": rec.get("tags") or {},
                "extra": rec.get("extra") or "",
                "source": "anima_wardrobe_v5",
            }
        )

    return v5_options, tag_levels, v5_characters, v5_scenes


# ---------------------------------------------------------------------------
# 五、合并
# ---------------------------------------------------------------------------


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def merge_tags(pf_categories, v5_options, tag_levels):
    """按槽位合并候选词。

    返回 ``{slot: {"name": 中文名, "items": [{"en","zh","level"}]}}``。
    """
    slot_items = OrderedDict((slot, []) for slot in SLOTS)

    # 1) 质量槽：Prompt Forge「质量与风格」的前 16 条（score_ / masterpiece / safe …）
    style = pf_categories.get("style")
    if style:
        for en, zh in style["items"][:16]:
            slot_items["quality"].append({"en": en, "zh": zh, "level": self_grade(en)})

    # 2) 其余分类（base 分类单独拆，见下）
    for cid, slot in PF_CATEGORY_TO_SLOT.items():
        if slot is None or cid == "style":
            continue
        cat = pf_categories.get(cid)
        if not cat:
            continue
        if cid == "base":
            continue
        for en, zh in cat["items"]:
            slot_items[slot].append({"en": en, "zh": zh, "level": self_grade(en)})

    # 2b) PF「人物基础」拆分：人数 / 基础外貌 / 种族职业身份
    base_cat = pf_categories.get("base")
    if base_cat:
        for en, zh in base_cat["items"]:
            key = _norm(en)
            if key in PF_BASE_COUNT_TAGS:
                slot_items["count"].append({"en": en, "zh": zh, "level": self_grade(en)})
            elif key in PF_BASE_LOOK_TAGS:
                slot_items["face"].append({"en": en, "zh": zh, "level": self_grade(en)})
            else:
                slot_items[PF_BASE_IDENTITY_SLOT].append(
                    {"en": en, "zh": zh, "level": self_grade(en)}
                )

    # 3) 造型台选项
    for opt in v5_options:
        slot_items[opt["slot"]].append(
            {
                "en": opt["en"],
                "zh": opt["zh"],
                "level": max(opt["level"], tag_levels.get(_norm(opt["en"]), 0)),
                "field": opt["field"],
            }
        )

    # 4) 去重（同一槽位内按规范化英文去重，保留首个出现的中文标签）
    result = OrderedDict()
    for slot, items in slot_items.items():
        seen = {}
        for item in items:
            key = _norm(item["en"])
            if not key:
                continue
            if key in seen:
                prev = seen[key]
                prev["level"] = max(prev.get("level", 0), item.get("level", 0))
                if not prev.get("zh") and item.get("zh"):
                    prev["zh"] = item["zh"]
                continue
            entry = {"en": item["en"], "zh": item.get("zh", ""), "level": int(item.get("level", 0))}
            seen[key] = entry
        result[slot] = {"name": SLOTS[slot], "items": list(seen.values())}

    # 5) 中文修正表覆盖（画师笔名补中文标识、同槽位重名拆开）
    for slot, data in result.items():
        for entry in data["items"]:
            override = ZH_OVERRIDES.get(_norm(entry.get("en", "")))
            if override:
                entry["zh"] = override
    return result


def merge_characters(pf_characters, v5_characters):
    result = []
    seen = set()
    for rec in list(pf_characters) + list(v5_characters):
        key = _norm(rec.get("tag") or rec.get("name_en") or rec.get("name_zh"))
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(rec)
    return result


# ---------------------------------------------------------------------------
# 角色别名（日文名 / 繁简变体 / 连字符写法）
# ---------------------------------------------------------------------------
# 词库原本只有简体中文名 + 英文名，用户输入「ミク」「初音ミク」这类写法命中不了。
# 这里把联网抓到的日文名（tools/anime_char_names_cache.json）以及繁简 / 连字符
# 变体一起烘焙进角色记录，运行时节点只做本地匹配，**不联网**。

# 日文假名 / 日文汉字
_JP_RE = re.compile(r"[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]")


def _opencc_converters():
    """繁简双向转换器（构建期用；没装 opencc 就返回空列表）。

    - ``t2s``：繁体 → 简体（把日文汉字写法转成简体，便于简体用户命中）
    - ``s2t``：简体 → 繁体（让繁体用户也能命中简体词库）
    """
    out = []
    try:
        from opencc import OpenCC  # type: ignore

        for config in ("t2s", "s2t"):
            try:
                out.append(OpenCC(config))
            except Exception:
                pass
    except Exception:
        pass
    return out


def build_cjk_map():
    """构建「繁体 / 日文新字体 → 简体」的单字映射表。

    运行时（节点侧）没有 opencc，所以把映射表烘焙进词库，节点加载后
    对**用户输入**和**词库名字**做同样的规范化，这样：

    - ``阿爾托莉雅`` → ``阿尔托莉雅`` → 命中 ``阿尔托莉雅·潘德拉贡``
    - ``博麗霊夢``  → ``博丽灵梦``  → 命中 ``博丽灵梦``

    映射来源：opencc ``t2s``（繁→简）+ ``JPVariants`` 的逆映射
    （日文新字体 ``霊`` → 繁体 ``靈`` → 简体 ``灵``）。
    """
    mapping = {}
    try:
        from opencc import OpenCC  # type: ignore

        t2s = OpenCC("t2s")
        for code in range(0x3400, 0xA000):
            ch = chr(code)
            try:
                simple = t2s.convert(ch)
            except Exception:
                continue
            if simple and simple != ch:
                mapping[ch] = simple
    except Exception:
        return mapping

    # 日文新字体 → 繁体 → 简体（opencc 的 JPVariants 是 繁体→日文，这里取逆）
    try:
        import opencc as _opencc_pkg
        import os as _os

        dict_dir = _os.path.join(_os.path.dirname(_opencc_pkg.__file__), "dictionary")
        jp_file = _os.path.join(dict_dir, "JPVariants.txt")
        if _os.path.isfile(jp_file):
            with open(jp_file, encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split("\t")
                    if len(parts) < 2:
                        continue
                    trad, jp = parts[0], parts[1].split(" ")[0]
                    if jp in mapping:
                        continue
                    try:
                        simple = t2s.convert(trad)
                    except Exception:
                        continue
                    if simple and simple != jp:
                        mapping[jp] = simple
    except Exception:
        pass
    return mapping


def _variants(value, converters):
    """一个名字的常见书写变体：繁体 / 简体 / 下划线 / 连字符。"""
    out = []
    text = str(value or "").strip()
    if not text:
        return out
    for converter in converters:
        try:
            converted = converter.convert(text)
        except Exception:
            continue
        if converted and converted != text:
            out.append(converted)
    for sep in ("_", "-"):
        if sep in text:
            out.append(text.replace(sep, " "))
    return out


# 社区常用中文别名 → 目标角色。
#
# 词库里的官方中文名和社区口头叫法经常不一致（官方「雷姆」/ 社区「蕾姆」，
# 官方「八意永琳」/ 社区「永琳八曜」，明日方舟干员的外号更是满天飞）。
# 这里人工维护一张对照表，构建期把别名烘焙进对应角色的 ``aliases`` 字段，
# 运行时节点直接查表，**不联网**。
#
# 目标写法是「角色 tag 里必须出现的片段」（大小写不敏感、下划线当空格）：
# 这样既能区分同名角色（例如 robin 有崩铁 / 火焰纹章 / summeretto 三条），
# 又能同时覆盖 Prompt Forge 的 ``xxx (work)`` 与造型台的 ``xxx_(work)`` 两种写法。
#
# 只收「目标确实存在且唯一」的条目：
# - 歧义别名（紫 / 蓝 / 黄 / 爱丽丝 / 博士 / 初雪 …）**不收**，
#   宁可让用户看到「未命中」，也不要把人导向错误的角色。
# - 词库里根本没有的角色（红豆 / 阿宽 / 梅洛 / 八雪 …）**不收**，
#   别名救不了「词库里没有这个角色」这件事。
COMMUNITY_ALIASES = {
    # --- re:zero ---
    "蕾姆": "rem (re:zero",
    "艾米莉亚": "emilia (re:zero",
    "艾米丽娅": "emilia (re:zero",
    # --- 东方 ---
    "永琳八曜": "yagokoro eirin",
    # --- 原神 ---
    "雷神": "raiden shogun",
    "雷电影": "raiden shogun",
    "雷鸣": "raiden shogun",
    "吉良吉影": "kaveh",
    "温蒂": "venti",
    # --- 崩铁 ---
    "歌姬": "robin (honkai",
    # --- 明日方舟 ---
    "小莫": "mostima",
    "蓝天使": "mostima",
    "卡涅利安": "nearl",
    "六边形战士": "nearl",
    "格拉斯": "saria",
    "莱茵拳皇": "saria",
    "暴行": "surtr",
    "银老板": "silverash",
    "鲨鲨": "specter",
    "拉狗": "lappland",
    "蒂蒂": "skadi",
    "虎鲸": "skadi",
    "小绵羊": "eyjafjalla",
    "小火龙": "ifrit|anima_wardrobe_v5",
    "咕咕": "ptilopsis",
    "白面": "ptilopsis",
    "洁哥": "angelina",
    "安心院": "angelina",
    "安洁": "angelina",
    "啊噗路派": "exusiai",
    "阿能": "exusiai",
    "鬼姐": "hoshiguma",
    "推王": "siege",
    "王小姐": "siege",
    "猫猫头": "jessica",
    "富婆": "jessica",
    "大尾巴狼": "provence",
    "葬哥": "executor",
    "小企鹅": "magallan",
    "阿米驴": "amiya",
    "小驴子": "amiya",
    "克天使": "kroos",
    "天鹅": "blue poison",
    "小刻": "ceobe",
    "小闹钟": "astesia",
    "吉祥物": "swire",
    "小老虎": "swire",
    "芙剑圣": "franka",
    "胖狐狸": "franka",
    "闪剑圣": "shining",
    "喜羊羊": "shining",
    "陈sir": "ch'en (arknights",
    "老陈": "ch'en (arknights",
    "龟龟": "w (arknights",
    "sola酱": "sora (arknights",
    "爱抖露": "sora (arknights",
    # --- 碧蓝档案 / NIKKE ---
    "优妮": "yuni (nikke",
}


def _normalized_tag(rec):
    """角色 tag 的归一化形式（下划线当空格、小写），用于别名表匹配。"""
    tag = str(rec.get("tag") or rec.get("name_en") or "").replace("_", " ")
    return re.sub(r"\s+", " ", tag).strip().lower()


def bake_aliases(characters, cache_path):
    """给角色记录补 ``aliases`` 字段（日文名 / 繁简 / 连字符变体 / 社区别名）。

    ``cache_path`` 是 ``tools/fetch_anime_char_names.py`` 抓出来的日文名缓存；
    文件不存在时只做繁简 / 连字符变体。
    """
    converters = _opencc_converters()
    cache = {}
    if cache_path and os.path.isfile(cache_path):
        with open(cache_path, encoding="utf-8") as fh:
            cache = json.load(fh)

    added = 0
    for rec in characters:
        aliases = []
        seen = set()

        def push(value):
            value = re.sub(r"\s+", " ", str(value or "").strip())
            if not value or len(value) > 24:
                return
            key = value.lower()
            if key in seen:
                return
            seen.add(key)
            aliases.append(value)

        # 1) 联网抓到的日文名
        entry = cache.get(rec.get("tag") or "")
        for jp in (entry or {}).get("jp_names") or []:
            push(jp)
        # 2) 中文名的繁简 / 连字符变体
        for field in ("name_zh", "char_zh"):
            for variant in _variants(rec.get(field), converters):
                push(variant)
        # 3) 英文名的下划线 / 连字符变体
        for field in ("name_en", "tag"):
            for variant in _variants(rec.get(field), converters):
                push(variant)
        # 4) 去掉作品括号的英文名
        base = re.sub(r"\s*\([^()]*\)\s*$", "", str(rec.get("name_en") or "").strip()).strip()
        if base and base.lower() != str(rec.get("name_en") or "").strip().lower():
            push(base)
        # 5) 社区中文别名（COMMUNITY_ALIASES 命中本条记录时）
        rec_tag = _normalized_tag(rec)
        rec_source = str(rec.get("source") or "")
        for alias, target in COMMUNITY_ALIASES.items():
            wanted, _, want_source = target.partition("|")
            wanted = wanted.strip().lower()
            if not wanted or wanted not in rec_tag:
                continue
            if want_source and want_source.strip() != rec_source:
                continue
            push(alias)

        # 排除与现有字段完全相同的别名（省空间）
        existing = {
            _norm(rec.get(f))
            for f in ("name_zh", "char_zh", "name_en", "tag", "trigger")
            if rec.get(f)
        }
        aliases = [a for a in aliases if _norm(a) not in existing]
        if aliases:
            rec["aliases"] = aliases
            added += 1
    return added


def merge_scenes(pf_presets, v5_scenes):
    scenes = []
    for rec in v5_scenes:
        scenes.append(rec)
    for rec in pf_presets:
        scenes.append(
            {
                "id": "pf_" + re.sub(r"\W+", "_", rec["name"]),
                "name": rec["name"],
                "desc": rec["desc"],
                "group": "prompt_forge",
                "level": 0,
                "tags": {},
                "items": rec["items"],
                "source": "prompt_forge",
            }
        )
    return scenes


# ---------------------------------------------------------------------------
# 六、入口
# ---------------------------------------------------------------------------


def main(argv=None):
    parser = argparse.ArgumentParser(description="构建随机提示词(Anime)节点的离线词库")
    parser.add_argument("--html", required=True, help="Prompt Forge 的 提示词生成器.html 路径")
    parser.add_argument("--wardrobe", required=True, help="Comfyui-Anima-Wardrobe-V5 仓库路径")
    args = parser.parse_args(argv)

    os.makedirs(OUT_DIR, exist_ok=True)

    pf_categories, pf_characters, pf_presets = parse_prompt_forge(args.html)
    v5_options, tag_levels, v5_characters, v5_scenes = parse_wardrobe(args.wardrobe)

    tags = merge_tags(pf_categories, v5_options, tag_levels)
    characters = merge_characters(pf_characters, v5_characters)
    scenes = merge_scenes(pf_presets, v5_scenes)

    # 角色别名（日文名 / 繁简 / 连字符变体）——联网抓的日文名缓存在 tools/ 下
    alias_cache = os.path.join(HERE, "anime_char_names_cache.json")
    with_alias = bake_aliases(characters, alias_cache)
    print("角色别名：%d 位带别名（缓存 %s）" % (with_alias, alias_cache))

    # 繁简 / 日文新字体 → 简体的单字映射（烘焙进词库，运行时无需 opencc）
    cjk_map = build_cjk_map()
    print("汉字规范化映射：%d 个字" % len(cjk_map))

    # 档位表：造型台登记表 + 自研判定（登记优先）
    levels = {"tag_levels": tag_levels}

    write_json(
        os.path.join(OUT_DIR, "anime_prompt_tags.json"),
        {
            "_meta": {
                "schema": "ytmmi/anime-prompt-tags@1",
                "sources": ["prompt_forge(提示词生成器.html)", "anima_wardrobe_v5(presets)"],
                "slots": list(SLOTS.keys()),
                "brief_slots": list(BRIEF_SLOTS),
            },
            "slots": tags,
        },
    )
    write_json(os.path.join(OUT_DIR, "anime_prompt_levels.json"), levels)
    write_json(
        os.path.join(OUT_DIR, "anime_prompt_characters.json"),
        {
            "_meta": {
                "schema": "ytmmi/anime-prompt-characters@2",
                "count": len(characters),
                "sources": ["prompt_forge", "anima_wardrobe_v5"],
            },
            "cjk_map": cjk_map,
            "characters": characters,
        },
    )
    write_json(
        os.path.join(OUT_DIR, "anime_prompt_scenes.json"),
        {
            "_meta": {
                "schema": "ytmmi/anime-prompt-scenes@1",
                "count": len(scenes),
                "sources": ["anima_wardrobe_v5", "prompt_forge"],
            },
            "scenes": scenes,
        },
    )

    print("槽位：")
    for slot, data in tags.items():
        print("  %-12s %-8s %4d 条" % (slot, data["name"], len(data["items"])))
    print("角色：%d 位    场景：%d 条    档位表：%d 标签" % (len(characters), len(scenes), len(tag_levels)))
    return 0


def write_json(path, payload):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, ensure_ascii=False, separators=(",", ":"))
    print("写出 %s（%d KB）" % (os.path.relpath(path, ROOT), os.path.getsize(path) // 1024))


if __name__ == "__main__":
    sys.exit(main())
