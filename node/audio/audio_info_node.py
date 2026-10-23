# 获取音频信息
"""获取音频信息节点。

读取音频文件（或已解码的 AUDIO 输入），输出文件名、时长、完整路径与信息汇总文本。

只连了 AUDIO 输入、没有填「文件名」时，节点会沿工作流连线向上游追踪，
从音频加载节点（如原生「加载音频」）读取它选中的文件名，自动补全
「文件名」与「完整路径」，不再显示「未知」。

元数据优先由 PyAV 读取；PyAV 不可用或读取失败时，对 WAV 退回标准库
``wave``；若只有 AUDIO 输入，则用波形长度与采样率推算时长。
"""

from __future__ import annotations

import os
import wave

try:
    import folder_paths  # type: ignore
except Exception:  # pragma: no cover - 单测/独立运行环境
    folder_paths = None

try:
    import av  # type: ignore
except Exception:  # pragma: no cover - 未安装 PyAV 时降级
    av = None


# ── 常量 ──────────────────────────────────────────────────────────
# 支持的文件后缀（仅用于提示与文档，实际解析交给 PyAV）
AUDIO_EXTENSIONS = (
    ".wav",
    ".mp3",
    ".flac",
    ".m4a",
    ".aac",
    ".ogg",
    ".opus",
    ".wma",
    ".aiff",
    ".aif",
    ".amr",
    ".webm",
)

# PyAV 返回的容器名是逗号分隔的格式别名，这里映射成更友好的写法
_CONTAINER_ALIASES = {
    "mov,mp4,m4a,3gp,3g2,mj2": "mp4/m4a",
    "matroska,webm": "mkv/webm",
    "aac": "aac(adts)",
}

# 上游节点里这些输入名最可能是音频文件（分值越高越优先）
_FILENAME_KEY_SCORES = {
    "audio": 100,
    "音频": 100,
    "filename": 90,
    "文件名": 90,
    "path": 90,
    "路径": 90,
    "文件路径": 90,
    "音频路径": 90,
}

# 上游追踪的最大层数与最大节点数，避免异常工作流里无限遍历
_MAX_TRACE_DEPTH = 16
_MAX_TRACE_NODES = 256


# ── 路径解析 ──────────────────────────────────────────────────────
def _clean_filename(raw) -> str:
    """去掉文件名两侧的空白与引号。"""
    if not isinstance(raw, str):
        return ""
    return raw.strip().strip('"').strip("'")


def _is_within(base: str, target: str) -> bool:
    """判断 target 是否位于 base 目录内（防路径穿越）。"""
    try:
        base_abs = os.path.abspath(base)
        target_abs = os.path.abspath(target)
        return os.path.commonpath([base_abs, target_abs]) == base_abs
    except Exception:
        return False


def resolve_audio_path(raw) -> str | None:
    """把「文件名」输入解析成绝对路径，无法解析时返回 None。

    依次尝试：绝对路径 → ComfyUI 标注路径（``[input]``/``[output]``/``[temp]``
    后缀）→ ComfyUI input 目录。相对路径一律按 input 目录解析。
    """
    name = _clean_filename(raw)
    if not name:
        return None

    if os.path.isabs(name) and os.path.isfile(name):
        return os.path.abspath(name)

    if folder_paths is not None:
        try:
            path = folder_paths.get_annotated_filepath(name)
        except Exception:
            path = None
        if path and os.path.isfile(path):
            return os.path.abspath(path)

        try:
            input_dir = folder_paths.get_input_directory()
        except Exception:
            input_dir = None
        if input_dir:
            candidate = os.path.join(input_dir, name)
            if _is_within(input_dir, candidate) and os.path.isfile(candidate):
                return os.path.abspath(candidate)

    return None


# ── 上游追踪 ──────────────────────────────────────────────────────
def _link_target(value):
    """把工作流里的连线 ``[节点id, 输出序号]`` 解析成元组，不是连线返回 None。"""
    if isinstance(value, (list, tuple)) and len(value) == 2:
        node_id, index = value
        if isinstance(index, int) and not isinstance(index, bool):
            if isinstance(node_id, (str, int)) and not isinstance(node_id, bool):
                return str(node_id), index
    return None


def _filename_key_score(key) -> int:
    """给上游输入名打分：越像音频文件名得分越高，无关输入返回 0。"""
    text = str(key).strip()
    if text in _FILENAME_KEY_SCORES:
        return _FILENAME_KEY_SCORES[text]
    lowered = text.lower()
    if "audio" in lowered or "音频" in text:
        return 80
    if "file" in lowered or "文件" in text or "path" in lowered or "路径" in text:
        return 60
    return 0


def find_upstream_audio_file(prompt, node_id, max_depth: int = _MAX_TRACE_DEPTH):
    """沿工作流连线向上游查找音频文件名，返回解析出的绝对路径或 None。

    ``prompt`` 是 ComfyUI 通过 hidden ``PROMPT`` 传入的原始工作流字典，
    ``node_id`` 是本节点的 id。遍历时优先采用名为 ``audio`` / ``音频`` 等
    的字符串输入，其次才是文件名、路径类输入；只有能解析成真实文件的
    值才会被采用。
    """
    if not isinstance(prompt, dict) or node_id is None:
        return None
    start = str(node_id)
    if start not in prompt:
        return None

    best_path = None
    best_score = -1
    best_depth = _MAX_TRACE_DEPTH + 1

    seen = {start}
    queue = [(start, 0)]
    visited = 0
    while queue and visited < _MAX_TRACE_NODES:
        current_id, depth = queue.pop(0)
        if depth >= max_depth:
            continue
        node = prompt.get(current_id)
        if not isinstance(node, dict):
            continue
        inputs = node.get("inputs")
        if not isinstance(inputs, dict):
            continue
        visited += 1
        for key, value in inputs.items():
            target = _link_target(value)
            if target is not None:
                upstream_id = target[0]
                if upstream_id not in seen and upstream_id in prompt:
                    seen.add(upstream_id)
                    queue.append((upstream_id, depth + 1))
                continue
            if not isinstance(value, str) or not value.strip():
                continue
            score = _filename_key_score(key)
            if score <= 0:
                continue
            path = resolve_audio_path(value)
            if not path:
                continue
            if score > best_score or (score == best_score and depth < best_depth):
                best_score = score
                best_depth = depth
                best_path = path
    return best_path


# ── 格式化 ────────────────────────────────────────────────────────
def format_duration(seconds) -> str:
    """把秒数格式化为 ``mm:ss.mmm``（超过一小时则 ``hh:mm:ss.mmm``）。"""
    try:
        total_ms = int(round(float(seconds) * 1000))
    except (TypeError, ValueError):
        return "00:00.000"
    if total_ms < 0:
        total_ms = 0
    hours, rem = divmod(total_ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, millis = divmod(rem, 1000)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
    return f"{minutes:02d}:{secs:02d}.{millis:03d}"


def friendly_container(name) -> str:
    """把 PyAV 的容器名映射成友好写法。"""
    key = str(name or "").strip()
    return _CONTAINER_ALIASES.get(key, key)


# ── 元数据探测 ────────────────────────────────────────────────────
def _channels_of(codec_context) -> int:
    """取声道数：新版 PyAV 用 layout，旧版用 channels。"""
    channels = getattr(codec_context, "channels", None)
    if channels:
        return int(channels)
    layout = getattr(codec_context, "layout", None)
    nb_channels = getattr(layout, "nb_channels", None)
    if nb_channels:
        return int(nb_channels)
    return 0


def _container_duration(container) -> float:
    """取时长（秒）：优先容器时长，退回音频流时长 × 时基。"""
    duration = getattr(container, "duration", None)
    if duration:
        return float(duration) / 1_000_000.0
    stream = next((s for s in container.streams if s.type == "audio"), None)
    if stream is not None:
        stream_duration = getattr(stream, "duration", None)
        time_base = getattr(stream, "time_base", None)
        if stream_duration and time_base:
            try:
                return float(stream_duration * time_base)
            except Exception:
                return 0.0
    return 0.0


def probe_with_av(path: str) -> dict:
    """用 PyAV 读取音频元数据；未安装 PyAV 时返回空 dict。"""
    if av is None:
        return {}
    with av.open(path) as container:
        stream = next((s for s in container.streams if s.type == "audio"), None)
        if stream is None:
            raise ValueError(f"文件中没有音频流：{os.path.basename(path)}")
        codec_context = stream.codec_context
        bit_rate = getattr(codec_context, "bit_rate", None)
        if not bit_rate:
            bit_rate = getattr(container, "bit_rate", None)
        return {
            "时长秒": _container_duration(container),
            "采样率": int(getattr(codec_context, "sample_rate", 0) or 0),
            "声道数": _channels_of(codec_context),
            "编码": str(getattr(codec_context, "name", "") or ""),
            "容器格式": friendly_container(
                getattr(getattr(container, "format", None), "name", "")
            ),
            # PyAV 的码率单位是 bit/s，这里统一换算成 kbps
            "码率": int(round(int(bit_rate) / 1000)) if bit_rate else 0,
        }


def probe_with_wave(path: str) -> dict:
    """PyAV 不可用时，用标准库读取 WAV 头。"""
    try:
        with wave.open(path, "rb") as wav:
            sample_rate = wav.getframerate()
            channels = wav.getnchannels()
            frames = wav.getnframes()
            sample_width = wav.getsampwidth()
    except Exception:
        return {}
    duration = frames / float(sample_rate) if sample_rate else 0.0
    bit_rate = sample_rate * channels * sample_width * 8
    return {
        "时长秒": float(duration),
        "采样率": int(sample_rate),
        "声道数": int(channels),
        "编码": f"pcm_s{sample_width * 8}le",
        "容器格式": "wav",
        "码率": int(round(bit_rate / 1000)) if bit_rate else 0,
    }


def _fill_defaults(info: dict) -> dict:
    """补齐缺失字段并统一类型。"""
    result = dict(info or {})
    try:
        result["时长秒"] = float(result.get("时长秒") or 0.0)
    except (TypeError, ValueError):
        result["时长秒"] = 0.0
    for key in ("采样率", "声道数", "码率"):
        try:
            result[key] = int(result.get(key) or 0)
        except (TypeError, ValueError):
            result[key] = 0
    for key in ("编码", "容器格式"):
        result[key] = str(result.get(key) or "")
    return result


def probe_audio_file(path: str) -> dict:
    """读取音频文件元数据：PyAV 优先，失败退回标准库 WAV。"""
    errors = []
    if av is not None:
        try:
            info = probe_with_av(path)
        except Exception as exc:
            errors.append(f"PyAV: {exc}")
        else:
            if info:
                return _fill_defaults(info)
    info = probe_with_wave(path)
    if info:
        return _fill_defaults(info)
    errors.append("标准库: 不是可解析的 WAV")
    raise ValueError(
        f"无法解析音频文件「{os.path.basename(path)}」：" + "；".join(errors)
    )


def probe_audio_value(audio) -> dict:
    """从已解码的 AUDIO 值推算基本信息。

    ComfyUI 的 AUDIO 是普通 dict：``{"waveform": Tensor, "sample_rate": int}``，
    waveform 形状为 ``[B, C, T]``（也兼容 ``[C, T]`` / ``[T]``）。
    """
    if not isinstance(audio, dict):
        return {}
    info: dict = {}
    try:
        sample_rate = int(audio.get("sample_rate") or 0)
    except (TypeError, ValueError):
        sample_rate = 0
    info["采样率"] = sample_rate

    waveform = audio.get("waveform")
    shape = getattr(waveform, "shape", None)
    if shape is not None and len(shape) >= 1:
        samples = int(shape[-1])
        info["声道数"] = int(shape[-2]) if len(shape) >= 2 else 1
        if sample_rate:
            info["时长秒"] = samples / float(sample_rate)
    return info


def build_info_text(filename: str, full_path: str, info: dict, size_mb: float) -> str:
    """拼装多行信息汇总文本。"""
    duration = float(info.get("时长秒") or 0.0)
    sample_rate = int(info.get("采样率") or 0)
    channels = int(info.get("声道数") or 0)
    bit_rate = int(info.get("码率") or 0)
    lines = [
        f"文件名：{filename or '（未知）'}",
        f"完整路径：{full_path or '（未知）'}",
        f"时长：{format_duration(duration)}（{duration:.3f} 秒）",
        f"采样率：{sample_rate} Hz" if sample_rate else "采样率：未知",
        f"声道数：{channels}" if channels else "声道数：未知",
        f"编码：{info.get('编码') or '未知'}",
        f"容器格式：{info.get('容器格式') or '未知'}",
        f"码率：{bit_rate} kbps" if bit_rate else "码率：未知",
        f"文件大小：{size_mb:.3f} MB" if size_mb else "文件大小：未知",
    ]
    return "\n".join(lines)


class AudioInfoNode:
    """获取音频信息。"""

    CATEGORY = "YTmmi/audio"
    DESCRIPTION = (
        "获取音频信息：读取音频文件或 AUDIO 输入，输出文件名、时长、完整路径与"
        "信息汇总文本；只连音频时会沿连线向上游追踪文件名。"
    )
    FUNCTION = "audio_info"

    RETURN_TYPES = (
        "STRING",
        "FLOAT",
        "STRING",
        "STRING",
        "STRING",
    )
    RETURN_NAMES = (
        "文件名",
        "时长秒",
        "时长文本",
        "完整路径",
        "信息文本",
    )
    OUTPUT_NODE = False
    OUTPUT_IS_LIST = (
        False,
        False,
        False,
        False,
        False,
    )
    SEARCH_ALIASES = [
        "获取音频信息",
        "音频信息",
        "音频时长",
        "获取音频时长",
        "音频元数据",
        "Audio Info",
        "AudioInfo",
        "Audio Metadata",
        "audio duration",
    ]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "文件名": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": False,
                        "placeholder": "如 sample.wav（相对 input 目录）或绝对路径",
                    },
                ),
            },
            "optional": {
                "音频": ("AUDIO",),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
                "prompt": "PROMPT",
            },
        }

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        """音频文件未变化时复用缓存，其余情况强制重新执行。

        只能使用常量输入与 hidden 输入：连线输入（音频本身）在 IS_CHANGED
        阶段取不到值。手填「文件名」时直接按文件签名判断；只连音频时用
        hidden ``PROMPT`` 沿连线向上游追踪文件名，同样按文件签名判断。
        """
        raw = kwargs.get("文件名")
        path = None
        if isinstance(raw, str) and raw.strip():
            try:
                path = resolve_audio_path(raw)
            except Exception:
                path = None
        else:
            try:
                path = find_upstream_audio_file(
                    kwargs.get("prompt"), kwargs.get("unique_id")
                )
            except Exception:
                path = None
        if not path:
            return float("NaN")
        try:
            stat = os.stat(path)
        except OSError:
            return float("NaN")
        return f"{stat.st_size}:{stat.st_mtime_ns}"

    def audio_info(
        self,
        文件名: str = "",
        音频=None,
        unique_id=None,
        prompt=None,
        **kwargs,
    ):
        if 音频 is None:
            音频 = kwargs.get("音频")
        if unique_id is None:
            unique_id = kwargs.get("unique_id")
        if prompt is None:
            prompt = kwargs.get("prompt")

        name = _clean_filename(文件名)
        value_info = probe_audio_value(音频)

        path = resolve_audio_path(name)
        if path is None:
            if name:
                # 手填的文件名是明确意图，找不到就直接报错，避免静默取到别的文件
                raise ValueError(
                    f"找不到音频文件「{name}」：相对路径按 ComfyUI input 目录解析，"
                    "也可直接填写绝对路径"
                )
            # 只连了音频：沿连线向上游追踪音频加载节点选中的文件
            path = find_upstream_audio_file(prompt, unique_id)

        if path is not None:
            info = probe_audio_file(path)
            # 文件信息优先，缺失项用 AUDIO 波形补足
            for key, value in value_info.items():
                if not info.get(key):
                    info[key] = value
            display_name = os.path.basename(path)
            full_path = path
            try:
                size_mb = os.path.getsize(path) / (1024 * 1024)
            except OSError:
                size_mb = 0.0
        elif value_info:
            info = value_info
            display_name = ""
            full_path = ""
            size_mb = 0.0
        else:
            raise ValueError("请连接「音频」输入，或在「文件名」中填写音频文件")

        info = _fill_defaults(info)
        duration = float(info["时长秒"])

        return (
            display_name,
            round(duration, 3),
            format_duration(duration),
            full_path,
            build_info_text(display_name, full_path, info, size_mb),
        )


NODE_CLASS_MAPPINGS = {
    "AudioInfoNode": AudioInfoNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "AudioInfoNode": "获取音频信息",
}

__all__ = [
    "AudioInfoNode",
    "AUDIO_EXTENSIONS",
    "resolve_audio_path",
    "find_upstream_audio_file",
    "format_duration",
    "friendly_container",
    "probe_with_av",
    "probe_with_wave",
    "probe_audio_file",
    "probe_audio_value",
    "build_info_text",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
