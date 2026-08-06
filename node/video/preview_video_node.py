# 预览视频
"""预览视频节点。

将 VIDEO 视频保存为临时文件并在 ComfyUI 中播放预览（预览面板）。

- 输入：ComfyUI 原生 VIDEO 类型（与「加载视频」「视频拼接」等节点兼容）；
- 输出：原样透传 VIDEO，可继续接入保存等下游节点；
- 输出节点（OUTPUT_NODE），保证始终执行；
- 预览文件保存到 ComfyUI temp 目录，ui 通过 images + animated 消息触发
  前端视频预览（与原生 SaveVideo 的 ui.PreviewVideo 结构一致）。
"""

import os
import uuid

try:
    import folder_paths
except Exception:
    folder_paths = None

try:
    from comfy_api.latest import VideoCodec, VideoContainer
except Exception:
    VideoCodec = None
    VideoContainer = None


class PreviewVideoNode:
    """预览视频。"""

    CATEGORY = "YTmmi/video"
    DESCRIPTION = '预览视频：将视频保存为 MP4 临时文件供前端预览播放，并原样透传视频'

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "optional": {
                "视频": ("VIDEO",),
            }
        }

    RETURN_TYPES = ("VIDEO",)
    RETURN_NAMES = ("视频",)
    FUNCTION = "preview"
    OUTPUT_NODE = True
    OUTPUT_IS_LIST = (False,)
    SEARCH_ALIASES = ["video preview", "预览视频", "preview video"]

    def preview(self, **kwargs):
        video = kwargs.get("视频")
        if video is None:
            raise ValueError("预览视频：请连接视频输入")
        if folder_paths is None or VideoContainer is None or VideoCodec is None:
            raise RuntimeError("预览视频：当前环境不支持 VIDEO 类型，请升级 ComfyUI")

        # 统一保存为 MP4/H264，保证前端可播放；文件放在 ComfyUI temp 目录
        filename = f"preview_{uuid.uuid4().hex}.mp4"
        full_path = os.path.join(folder_paths.get_temp_directory(), filename)
        video.save_to(
            full_path,
            format=VideoContainer.MP4,
            codec=VideoCodec.H264,
        )

        return {
            "ui": {
                "images": [
                    {"filename": filename, "subfolder": "", "type": "temp"}
                ],
                "animated": (True,),
            },
            "result": (video,),
        }


NODE_CLASS_MAPPINGS = {
    "PreviewVideoNode": PreviewVideoNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PreviewVideoNode": "预览视频",
}

__all__ = [
    "PreviewVideoNode",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
