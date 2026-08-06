# 视频拼接
"""视频拼接节点。

将多段视频（ComfyUI 原生 VIDEO 类型，值为 VideoInput 对象）按输入接口
0, 1, 2 ... 的顺序首尾拼接为一段视频，输出 VIDEO 类型。

设计说明：
- 与原生「加载视频 LoadVideo」「创建视频 CreateVideo」等节点兼容，输入输出均为
  ComfyUI 0.26+ 的 VIDEO 类型（见 comfy_extras/nodes_video.py）。
- 节点默认暴露 2 个视频输入接口 video_0、video_1，前端 JS 扩展会在末尾接口被
  连接时自动添加下一个接口（video_2、video_3 ...），最多支持 MAX_INPUTS 路输入。
- 未连接的中间接口会被自动跳过，拼接顺序始终按接口序号递增。

性能优化（VideoConcatInput）：
- 节点执行时不做任何解码，O(1) 构建拼接视图；
- 帧数/时长/帧率/尺寸等元数据走快速路径（文件型视频只读容器头，不解码）；
- save_to() 逐段流式解码+编码，内存峰值从「全部视频总帧数」降为「单段帧数」。
"""

import io
import json

import numpy as np
import torch

try:
    from comfy_api.latest import (
        VideoCodec,
        VideoComponents,
        VideoContainer,
        VideoFromFile,
        VideoInput,
    )
except Exception:  # 环境不支持 V3 视频类型时降级为 None / object
    VideoCodec = None
    VideoComponents = None
    VideoContainer = None
    VideoFromFile = None
    VideoInput = object

try:
    import av
except Exception:
    av = None

# 支持的最大视频输入路数（前端 JS 需与此保持一致）
MAX_INPUTS = 10


class VideoConcatInput(VideoInput):
    """多段视频的拼接视图：延迟解码 + 元数据快速路径 + 逐段流式保存。"""

    def __init__(self, inputs, bit_depth=8):
        self._inputs = list(inputs)
        self._bit_depth = int(bit_depth)

    # ---------- 懒拼接：仅在真正需要帧数据时解码 ----------

    def get_components(self):
        if VideoComponents is None:
            raise RuntimeError("视频拼接：当前环境不支持 VIDEO 类型，请升级 ComfyUI")
        components = [video.get_components() for video in self._inputs]

        # 帧尺寸（H, W）必须一致
        ref_hw = components[0].images.shape[1:3]
        for i, component in enumerate(components):
            if component.images.shape[1:3] != ref_hw:
                raise ValueError(
                    f"视频拼接：所有视频帧尺寸必须一致，第 {i} 段的尺寸 "
                    f"{list(component.images.shape[1:3])} 与第 0 段的尺寸 "
                    f"{list(ref_hw)} 不一致"
                )

        # 沿 batch（帧）维拼接，统一 dtype/device
        images = torch.cat(
            [
                component.images.to(
                    dtype=torch.float32, device=components[0].images.device
                )
                for component in components
            ],
            dim=0,
        )
        return VideoComponents(
            images=images,
            frame_rate=components[0].frame_rate,
            audio=self._collect_audio(components),
        )

    # ---------- 元数据快速路径：文件型视频只读容器头，不解码 ----------

    def get_frame_count(self):
        return sum(video.get_frame_count() for video in self._inputs)

    def get_duration(self):
        return sum(video.get_duration() for video in self._inputs)

    def get_frame_rate(self):
        return self._inputs[0].get_frame_rate()

    def get_dimensions(self):
        return self._inputs[0].get_dimensions()

    def get_bit_depth(self):
        return self._bit_depth

    def get_container_format(self):
        return self._inputs[0].get_container_format()

    def get_active_trim_window(self):
        return 0.0, 0.0

    # ---------- 逐段流式保存：内存峰值 = 单段帧数 ----------

    def save_to(
        self,
        path,
        format=None,
        codec=None,
        metadata=None,
        bit_depth=None,
    ):
        if av is None or VideoContainer is None or VideoCodec is None:
            raise RuntimeError("视频拼接：当前环境不支持 VIDEO 类型，请升级 ComfyUI")

        if format is None:
            format = VideoContainer.AUTO
        if codec is None:
            codec = VideoCodec.AUTO
        if isinstance(format, str):
            format = VideoContainer(format)
        if format not in (VideoContainer.AUTO, VideoContainer.MP4):
            raise ValueError("视频拼接：仅支持 MP4 格式输出")
        if isinstance(codec, str):
            codec = VideoCodec(codec)
        if codec not in (VideoCodec.AUTO, VideoCodec.H264):
            raise ValueError("视频拼接：仅支持 H264 编码输出")

        if bit_depth is None:
            bit_depth = self._bit_depth
        is_10bit = bit_depth >= 10

        # 尺寸一致性校验（快速路径）
        ref_hw = self._inputs[0].get_dimensions()
        for video in self._inputs[1:]:
            if video.get_dimensions() != ref_hw:
                raise ValueError(
                    f"视频拼接：所有视频帧尺寸必须一致，{video.get_dimensions()} 与 {ref_hw} 不一致"
                )

        extra_kwargs = {}
        if format == VideoContainer.MP4:
            extra_kwargs["format"] = format.value
        elif isinstance(path, io.BytesIO):
            # BytesIO 无扩展名，av 无法推断格式
            extra_kwargs["format"] = "mp4"

        frame_rate = self.get_frame_rate()
        frame_rate = VideoConcatInput._normalize_fraction(frame_rate)
        width, height = ref_hw

        with av.open(
            path, mode="w", options={"movflags": "use_metadata_tags"}, **extra_kwargs
        ) as output:
            if metadata is not None:
                for key, value in metadata.items():
                    output.metadata[key] = json.dumps(value, ensure_ascii=False)

            pix_fmt = "yuv420p10le" if is_10bit else "yuv420p"
            video_stream = output.add_stream("h264", rate=frame_rate)
            video_stream.width = width
            video_stream.height = height
            video_stream.pix_fmt = pix_fmt

            # 音频：逐段收集（内存占用远小于视频帧），最后统一编码
            audio_parts = []
            audio_sample_rate = None
            audio_layout = None

            # 逐段解码并编码视频帧，段结束后立即释放该段帧内存
            for video in self._inputs:
                components = video.get_components()
                if components.audio is not None:
                    if audio_sample_rate is None:
                        audio_sample_rate = int(components.audio["sample_rate"])
                    if audio_sample_rate == int(components.audio["sample_rate"]):
                        audio_parts.append(components.audio)
                    else:
                        # 采样率不一致：丢弃后续音频，避免错误混音
                        audio_parts = []
                        audio_sample_rate = None
                for frame in components.images:
                    if is_10bit:
                        img = (
                            frame.float() * 65535
                        ).clamp(0, 65535).cpu().numpy().astype(np.uint16)
                        out_frame = av.VideoFrame.from_ndarray(img, format="rgb48le")
                    else:
                        img = (frame * 255).clamp(0, 255).byte().cpu().numpy()
                        out_frame = av.VideoFrame.from_ndarray(img, format="rgb24")
                    out_frame = out_frame.reformat(format=pix_fmt)
                    packet = video_stream.encode(out_frame)
                    output.mux(packet)
                # 释放该段 components，降低峰值内存
                components = None

            # 刷新视频编码器
            output.mux(video_stream.encode(None))

            # 编码拼接后的音频（全部存在且采样率一致时）
            if audio_parts:
                waveform = torch.cat([part["waveform"] for part in audio_parts], dim=2)
                layout = {1: "mono", 2: "stereo", 6: "5.1"}.get(
                    waveform.shape[1], "stereo"
                )
                audio_stream = output.add_stream(
                    "aac", rate=audio_sample_rate, layout=layout
                )
                audio_frame = av.AudioFrame.from_ndarray(
                    waveform.float().cpu().contiguous().numpy(),
                    format="fltp",
                    layout=layout,
                )
                audio_frame.sample_rate = audio_sample_rate
                audio_frame.pts = 0
                output.mux(audio_stream.encode(audio_frame))
                output.mux(audio_stream.encode(None))

    def as_trimmed(self, start_time=0.0, duration=0.0, strict_duration=True):
        if VideoFromFile is None:
            raise RuntimeError("视频拼接：当前环境不支持 VIDEO 类型，请升级 ComfyUI")
        trimmed = VideoFromFile(
            self.get_stream_source(),
            start_time=start_time,
            duration=duration,
        )
        if trimmed.get_duration() < duration and strict_duration:
            return None
        return trimmed

    # ---------- 内部工具 ----------

    @staticmethod
    def _collect_audio(components):
        """拼接各段音频；任一段无音频或采样率不一致时返回 None（忽略音频）。"""
        audios = [component.audio for component in components]
        if any(audio is None for audio in audios):
            return None
        sample_rate = audios[0]["sample_rate"]
        for audio in audios:
            if audio["sample_rate"] != sample_rate:
                return None
        waveform = torch.cat([audio["waveform"] for audio in audios], dim=2)
        return {"waveform": waveform, "sample_rate": sample_rate}

    @staticmethod
    def _normalize_fraction(rate):
        """将帧率统一为适合 av 的分数形式。"""
        from fractions import Fraction

        if isinstance(rate, Fraction):
            return Fraction(round(float(rate) * 1000), 1000)
        try:
            return Fraction(round(float(rate) * 1000), 1000)
        except Exception:
            return Fraction(30, 1)


class VideoConcatNode:
    """按接口顺序拼接多段视频（延迟解码，O(1) 构建拼接视图）。"""

    CATEGORY = "YTmmi/video"
    DESCRIPTION = '视频拼接：将多段视频（原生 VIDEO 类型）按接口顺序拼接为一段，连接末尾输入自动增加接口，最多 10 路'

    @classmethod
    def INPUT_TYPES(cls):
        inputs = {"optional": {}}
        for i in range(MAX_INPUTS):
            inputs["optional"][f"视频{i}"] = ("VIDEO",)
        return inputs

    RETURN_TYPES = ("VIDEO",)
    RETURN_NAMES = ("拼接视频",)
    FUNCTION = "concat_videos"
    OUTPUT_NODE = False
    OUTPUT_IS_LIST = (False,)
    SEARCH_ALIASES = ["video concat", "视频拼接", "拼接视频", "merge video"]

    def concat_videos(self, **kwargs):
        # 按接口顺序收集已连接的视频（未连接接口不在 kwargs 中，或值为 None）
        videos = [
            kwargs.get(f"视频{i}")
            for i in range(MAX_INPUTS)
            if kwargs.get(f"视频{i}") is not None
        ]
        if not videos:
            raise ValueError("视频拼接：至少需要连接一个视频输入")

        # 尺寸一致性快速校验（文件型视频 O(1)，不解码）
        ref_hw = videos[0].get_dimensions()
        for i, video in enumerate(videos):
            if video.get_dimensions() != ref_hw:
                raise ValueError(
                    f"视频拼接：所有视频帧尺寸必须一致，视频{i} 的尺寸 "
                    f"{video.get_dimensions()} 与 视频0 的尺寸 {ref_hw} 不一致"
                )

        bit_depth = videos[0].get_bit_depth()
        # 延迟拼接：此处不调用 get_components()，真正需要帧时才解码
        return (VideoConcatInput(videos, bit_depth=bit_depth),)


NODE_CLASS_MAPPINGS = {
    "VideoConcatNode": VideoConcatNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VideoConcatNode": "视频拼接",
}

__all__ = [
    "VideoConcatNode",
    "VideoConcatInput",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
