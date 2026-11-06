# -*- coding: utf-8 -*-
"""抓取角色日文名 / 别名，生成离线缓存。

用途
----
「随机提示词(Anime)」节点的角色库原本只有简体中文名与英文名，
日文名（假名 / 日文汉字）完全缺失，用户输入 ``ミク`` / ``初音ミク``
这类写法无法命中。本脚本联网从 AniList GraphQL 抓每个角色的
原名与其他写法，结果写进离线缓存；**运行时完全离线**
（节点只读烘焙好的 JSON，不联网）。

两级抓取策略
------------
1. **作品级扫描（主）**：按角色所属作品搜 AniList 的 media，
   取该 media 的 characters 列表，在列表里按英文名词元**完全相等**匹配。
   好处：同一作品里的同名角色不会串（明日方舟的 ``dusk`` 不会被
   匹配到别的作品里的 ``Dusk``）。
2. **全局搜索（补）**：作品级没命中的角色，用
   ``characters(search: 英文名)`` 全局搜，并要求候选角色
   **出场作品与我们的作品相交**才采纳（避免 ``w`` 命中别的作品的
   同名角色）。全局搜索走**批量别名查询**（一次 GraphQL 请求查
   20 个角色），否则 2894 次单查要跑一个多小时。

作品 key 的取法：优先取角色 tag 括号里的作品名
（``akaza (kimetsu no yaiba)`` → ``kimetsu no yaiba``），
因为它比 ``work`` 字段（大量是「热门番剧」这种无信息值）更精确。

用法
----
    python tools/fetch_anime_char_names.py \
        --library node/text/data/anime_prompt_characters.json \
        --out tools/anime_char_names_cache.json

可选：
    --limit N        只处理前 N 个角色（调试用）
    --works N        只处理前 N 个作品（调试用）
    --no-global      只做作品级扫描，不做全局补漏
    --retry-empty    重试已抓过但日文名为空的条目
    --resume        复用已有缓存，只补缺失条目
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request

try:  # opencc 只在构建期用得到，缺失时跳过繁简别名
    from opencc import OpenCC  # type: ignore

    _T2S = OpenCC("t2s")
except Exception:  # pragma: no cover - 构建环境差异
    _T2S = None

ANILIST_URL = "https://graphql.anilist.co"
UA = "ComfyUI-YTmmi-Tools/anime-prompt-builder (offline name cache)"
BATCH_SIZE = 20

MEDIA_QUERY = """
query ($s: String, $t: MediaType) {
  Page(perPage: 5) {
    media(search: $s, type: $t) {
      id
      title { romaji english native }
      characters(perPage: 50) {
        edges { node { name { full native alternative } } }
      }
    }
  }
}
"""

CHAR_QUERY = """
query ($s: String) {
  Page(perPage: 8) {
    characters(search: $s) {
      id
      name { full native alternative }
      media(sort: [POPULARITY_DESC], perPage: 10) {
        nodes { title { romaji english native } }
      }
    }
  }
}
"""

KANA_RE = re.compile(r"[\u3040-\u309f\u30a0-\u30ff]")
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\u3005\u3007]")
# 作品名里没有信息量的词，做匹配时忽略
STOP_WORDS = {
    "the", "a", "an", "of", "and", "no", "to", "in", "on", "de", "la", "le",
    "game", "series", "project", "official", "il", "el", "s", "vs",
}


# ---------------------------------------------------------------------------
# 文本工具
# ---------------------------------------------------------------------------


def nfkc(text: str) -> str:
    """全角 → 半角，统一宽度。"""
    return unicodedata.normalize("NFKC", str(text or ""))


def tokens(text: str) -> list:
    """把名字切成可比较的词元（ASCII 字母数字 + 单个 CJK 字）。"""
    text = nfkc(text).lower()
    out = re.findall(r"[a-z0-9]+", text)
    out.extend(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff\u3040-\u30ff]", text))
    return [t for t in out if t not in STOP_WORDS]


def token_set(text: str) -> set:
    return set(tokens(text))


def cjk_only(text: str) -> str:
    """只保留 CJK 字（用于繁简转换）。"""
    return "".join(CJK_RE.findall(nfkc(text)))


def to_simplified(text: str) -> str:
    """繁体 → 简体；没装 opencc 时返回空串。"""
    if _T2S is None:
        return ""
    value = cjk_only(text)
    if not value:
        return ""
    try:
        return _T2S.convert(value)
    except Exception:
        return ""


def clean_alias(value: str) -> str:
    """去掉日文名字中间的间隔号与多余空白。"""
    value = nfkc(value or "").replace("\u30fb", "").replace("\u00b7", "")
    value = value.replace("（", "(").replace("）", ")")
    return re.sub(r"\s+", " ", value).strip()


def alias_is_clean(value: str) -> bool:
    """别名是否值得入库：纯名字，不带括号注释、不太长。"""
    if not value:
        return False
    if len(value) > 20:
        return False
    if any(ch in value for ch in "(),，"):
        return False
    return True


def strip_paren(text: str) -> str:
    """去掉结尾的作品括号：``hu tao (genshin impact)`` → ``hu tao``。"""
    return re.sub(r"\s*\([^()]*\)\s*$", "", str(text or "")).strip()


def name_of(rec) -> str:
    """角色在 AniList 上应该用的英文名（去掉作品括号）。"""
    return strip_paren(str(rec.get("name_en") or rec.get("tag") or ""))


def work_key(rec) -> str:
    """角色所属作品 key：优先 tag 括号里的作品名。"""
    tag = str(rec.get("tag") or "")
    match = re.search(r"\(([^()]+)\)\s*$", tag)
    if match:
        key = match.group(1).strip().lower()
        if key and key not in ("1st_costume", "2nd_costume", "3rd_costume"):
            return _norm_work(key)
    for field in ("work_tag", "work"):
        value = str(rec.get(field) or "").strip().lower()
        if value:
            return _norm_work(value)
    return ""


# 常见中文作品名 → AniList 上能搜到的英文名（AniList 对游戏 IP 收录很少）
WORK_ALIASES = {
    "原神": "genshin impact",
    "genshin impact": "genshin impact",
    "genshin_impact": "genshin impact",
    "崩坏：星穹铁道": "honkai star rail",
    "honkai: star rail": "honkai star rail",
    "崩坏3": "honkai 3rd",
    "明日方舟": "arknights",
    "蔚蓝档案": "blue archive",
    "碧蓝航线": "azur lane",
    "赛马娘": "umamusume pretty derby",
    "舰队collection": "kancolle",
    "kantai collection": "kancolle",
    "鸣潮": "wuthering waves",
    "绝区零": "zenless zone zero",
    "明日方舟": "arknights",
    "公主连结re:dive": "princess connect",
    "公主连结": "princess connect",
    "少女前线": "girls frontline",
    "战双帕弥什": "punishing gray raven",
    "phigros": "phigros",
    "光与夜之恋": "light and night",
    "时空中的绘旅人": "for All Time",
    "花亦山心之月": "huanxiangshan",
    "nominal": "nominal",
    "热门番剧": "",
    "anime": "",
}


def _norm_work(text: str) -> str:
    """作品 key 归一化：下划线/连字符 → 空格，并套用别名表。"""
    key = re.sub(r"[\s_]+", " ", str(text or "").strip().lower())
    key = re.sub(r"\s*:\s*", ": ", key)
    if key in WORK_ALIASES:
        return WORK_ALIASES[key]
    return key


# ---------------------------------------------------------------------------
# AniList
# ---------------------------------------------------------------------------


def gq(query: str, variables=None, retries: int = 6):
    body = json.dumps({"query": query, "variables": variables or {}}).encode("utf-8")
    req = urllib.request.Request(
        ANILIST_URL, data=body, headers={"Content-Type": "application/json", "User-Agent": UA}
    )
    delay = 4
    for _ in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=40) as resp:
                payload = json.load(resp)
            if payload.get("errors"):
                raise RuntimeError(payload["errors"][0].get("message", "anilist error"))
            return payload
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                time.sleep(delay)
                delay = min(delay * 2, 40)
                continue
            raise
        except Exception:
            time.sleep(delay)
            delay = min(delay * 2, 40)
    raise RuntimeError("anilist retries exhausted")


def gq_batch(items):
    """一次 GraphQL 请求批量查多个角色名。

    ``items`` 是名字列表，返回 ``{名字: [候选角色列表]}``。
    """
    if not items:
        return {}
    parts = []
    for index, name in enumerate(items):
        parts.append(
            'c%d: Page(perPage: 8) { characters(search: %s) { id name { full native alternative } '
            "media(sort: [POPULARITY_DESC], perPage: 10) { nodes { title { romaji english native } } } } }"
            % (index, json.dumps(str(name)))
        )
    payload = gq("{ " + " ".join(parts) + " }")
    data = payload.get("data") or {}
    out = {}
    for index, name in enumerate(items):
        out[name] = (data.get("c%d" % index) or {}).get("characters") or []
    return out


def media_pool(work: str):
    """取某个作品在 AniList 上的 media 候选（ANIME / MANGA 两种类型）。"""
    out = []
    for media_type in ("ANIME", "MANGA"):
        try:
            payload = gq(MEDIA_QUERY, {"s": work, "t": media_type})
        except Exception:
            continue
        for media in (payload.get("data") or {}).get("Page", {}).get("media") or []:
            out.append(media)
        time.sleep(0.6)
    return out


def chars_of_media(media):
    edges = (media.get("characters") or {}).get("edges") or []
    out = []
    for edge in edges:
        node = edge.get("node") or {}
        name = node.get("name") or {}
        out.append(
            {
                "full": clean_alias(name.get("full") or ""),
                "native": clean_alias(name.get("native") or ""),
                "alternative": [clean_alias(a) for a in (name.get("alternative") or [])],
            }
        )
    return out


def cand_token_sets(cand):
    """候选角色的全部英文名（full + alternative）的词元集合。"""
    out = []
    full = clean_alias(cand.get("full") or "")
    if full:
        out.append(token_set(full))
    for alt in cand.get("alternative") or []:
        alt = clean_alias(alt)
        if alt:
            out.append(token_set(alt))
    return [s for s in out if s]


def pick_exact(lib_tokens: set, candidates):
    """在候选里挑英文名词元与库记录**完全相等**的那个（保守，宁可漏也不错配）。"""
    for cand in candidates:
        if lib_tokens and lib_tokens in cand_token_sets(cand):
            return cand
    return None


def media_titles(cand):
    """出场作品的词元集合列表（每个作品一个 set）。"""
    titles = []
    for node in (cand.get("media") or {}).get("nodes") or []:
        title = node.get("title") or {}
        for key in ("romaji", "english", "native"):
            value = title.get(key)
            if value:
                titles.append(token_set(value))
    return titles


def collect_jp(cand):
    """从 AniList 候选里取出值得保留的日文写法。"""
    if not cand:
        return []
    names = []
    native = clean_alias(cand.get("native") or "")
    if native and (KANA_RE.search(native) or CJK_RE.search(native)):
        names.append(native)
    for alt in cand.get("alternative") or []:
        alt = clean_alias(alt)
        if alias_is_clean(alt) and (KANA_RE.search(alt) or CJK_RE.search(alt)):
            names.append(alt)
        # AniList 经常把日文写在括号里：``Saber (セイバー)``
        for inner in re.findall(r"[（(]([^（()）]+)[)）]", alt):
            inner = inner.strip()
            if inner and len(inner) <= 16 and (KANA_RE.search(inner) or CJK_RE.search(inner)):
                names.append(inner)
    return names


# ---------------------------------------------------------------------------
# 别名加工
# ---------------------------------------------------------------------------


def build_aliases(rec, jp_names):
    """整理一个角色的别名：日文原名 + 其他写法 + 繁简变体。"""
    aliases = []
    zh = str(rec.get("name_zh") or "")
    if zh:
        simp = to_simplified(zh)
        if simp and simp != zh:
            aliases.append(simp)
    en = str(rec.get("name_en") or "")
    if en:
        for sep in ("_", "-", "."):
            if sep in en:
                aliases.append(en.replace(sep, " "))
    for value in jp_names:
        if alias_is_clean(value):
            aliases.append(value)
            simp = to_simplified(value)
            if simp and simp != value:
                aliases.append(simp)
    out = []
    seen = set()
    for value in aliases:
        value = re.sub(r"\s+", " ", str(value or "").strip())
        if not value:
            continue
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(value)
    return out


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------


def fetch_work(work, records):
    """作品级扫描：返回 {tag: jp_names}。"""
    pool = []
    for media in media_pool(work):
        pool.extend(chars_of_media(media))
    if not pool:
        return {}
    out = {}
    for rec in records:
        lib_tokens = token_set(name_of(rec))
        if not lib_tokens:
            continue
        cand = pick_exact(lib_tokens, pool)
        if cand is None:
            continue
        names = collect_jp(cand)
        if names:
            out[rec.get("tag") or rec.get("name_en")] = names
    return out


def match_global(rec, cands):
    """在全局搜索结果里挑出我们的角色，返回日文写法列表。

    采纳条件（任一）：
    - 候选原名 == 我们的中文名（极强信号）
    - 候选出场作品与我们的作品词元相交
    - 该英文名在全部候选里**唯一**（游戏 IP 在 AniList 收录少，
      常常只有一个同名角色；此时作品无从核对，唯一性即可采信）
    """
    name = name_of(rec)
    zh = str(rec.get("name_zh") or "").strip()
    lib_tokens = token_set(name)
    work_tokens = token_set(work_key(rec))
    same = []
    for cand in cands:
        nm = cand.get("name") or {}
        cand_full = clean_alias(nm.get("full") or "")
        if lib_tokens and lib_tokens in cand_token_sets(cand):
            same.append((cand, cand_full))
    unique = len(same) == 1
    for cand, cand_full in same:
        nm = cand.get("name") or {}
        cand_native = clean_alias(nm.get("native") or "")
        strong = bool(zh) and cand_native == zh
        if not strong and work_tokens:
            titles = media_titles(cand)
            if not any(title & work_tokens for title in titles):
                if not unique:
                    continue
        names = collect_jp(
            {
                "full": cand_full,
                "native": cand_native,
                "alternative": [clean_alias(a) for a in (nm.get("alternative") or [])],
            }
        )
        if names:
            return names
    return []


def save_cache(cache, path):
    out_dir = os.path.dirname(path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with io.open(path, "w", encoding="utf-8", newline="\n") as fp:
        json.dump(cache, fp, ensure_ascii=False, indent=1, sort_keys=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description="抓取角色日文名与别名（离线缓存）")
    parser.add_argument("--library", default="node/text/data/anime_prompt_characters.json")
    parser.add_argument("--out", default="tools/anime_char_names_cache.json")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--works", type=int, default=0)
    parser.add_argument("--no-global", action="store_true")
    parser.add_argument("--retry-empty", action="store_true", help="重试已抓过但日文名为空的条目")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args(argv)

    with io.open(args.library, encoding="utf-8") as fp:
        lib = json.load(fp)
    records = lib.get("characters") if isinstance(lib, dict) else lib
    if args.limit:
        records = records[: args.limit]

    cache = {}
    if args.resume and os.path.exists(args.out):
        with io.open(args.out, encoding="utf-8") as fp:
            cache = json.load(fp)
        print("resume: 已缓存 %d 条" % len(cache), flush=True)

    groups = {}
    for rec in records:
        work = work_key(rec)
        if not work:
            continue
        groups.setdefault(work, []).append(rec)

    work_list = sorted(groups)
    if args.works:
        work_list = work_list[: args.works]
    print("作品 %d 个，角色 %d 位（缓存已有 %d）" % (len(work_list), len(records), len(cache)), flush=True)

    def pending(rec):
        """还没拿到日文名的条目才算待办。"""
        key = rec.get("tag") or rec.get("name_en")
        entry = cache.get(key)
        if entry is None:
            return True
        if entry.get("jp_names"):
            return False
        return args.retry_empty

    started = time.time()
    leftovers = []
    for index, work in enumerate(work_list, 1):
        recs = groups[work]
        todo = [r for r in recs if pending(r)]
        if not todo:
            continue
        found = fetch_work(work, todo)
        for rec in todo:
            key = rec.get("tag") or rec.get("name_en")
            names = found.get(key)
            if names:
                cache[key] = {"jp_names": names, "work": work}
            else:
                cache[key] = {"jp_names": [], "work": work}
                leftovers.append(rec)
        if index % 5 == 0 or index == len(work_list):
            el = time.time() - started
            with_jp = sum(1 for v in cache.values() if v.get("jp_names"))
            print(
                "  %d/%d 作品  %d 条缓存（有日文名 %d）  %.0fs"
                % (index, len(work_list), len(cache), with_jp, el),
                flush=True,
            )
            save_cache(cache, args.out)

    # --- 第二轮：批量全局搜索补漏 ---
    if leftovers and not args.no_global:
        names = sorted({name_of(r) for r in leftovers})
        names = [n for n in names if n]
        print("批量全局补漏 %d 个名字…" % len(names), flush=True)
        for start in range(0, len(names), BATCH_SIZE):
            chunk = names[start : start + BATCH_SIZE]
            try:
                result = gq_batch(chunk)
            except Exception as exc:
                print("  批量失败 %d-%d: %s" % (start, start + len(chunk), exc), flush=True)
                continue
            for rec in leftovers:
                name = name_of(rec)
                cands = result.get(name) or []
                jp = match_global(rec, cands)
                if jp:
                    key = rec.get("tag") or rec.get("name_en")
                    cache[key] = {"jp_names": jp, "work": work_key(rec)}
            el = time.time() - started
            with_jp = sum(1 for v in cache.values() if v.get("jp_names"))
            print(
                "  补漏 %d/%d  有日文名 %d  %.0fs"
                % (min(start + BATCH_SIZE, len(names)), len(names), with_jp, el),
                flush=True,
            )
            save_cache(cache, args.out)

    save_cache(cache, args.out)
    with_jp = sum(1 for v in cache.values() if v.get("jp_names"))
    print("完成：缓存 %d 条，其中有日文名 %d 条 → %s" % (len(cache), with_jp, args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
