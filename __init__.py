try:
    from .node.image.image_to_png_node import (
        ImageToPngNode,
        NODE_CLASS_MAPPINGS as IMAGE_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as IMAGE_NODE_DISPLAY_NAME_MAPPINGS,
    )
    from .node.utility.pixel_size_to_ratio_node import (
        PixelSizeToRatioNode,
        NODE_CLASS_MAPPINGS as PIXEL_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as PIXEL_NODE_DISPLAY_NAME_MAPPINGS,
    )
    from .node.text.save_json_file_node import (
        SaveJsonFileNode,
        NODE_CLASS_MAPPINGS as JSON_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as JSON_NODE_DISPLAY_NAME_MAPPINGS,
    )
    from .node.text.custom_llm_node import (
        CustomLLMNode,
        NODE_CLASS_MAPPINGS as CUSTOM_LLM_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as CUSTOM_LLM_NODE_DISPLAY_NAME_MAPPINGS,
    )
    from .node.image.save_jpg_node import (
        SaveJPGNode,
        NODE_CLASS_MAPPINGS as JPG_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as JPG_NODE_DISPLAY_NAME_MAPPINGS,
    )
    from .node.image.text_watermark_node import (
        TextWatermarkNode,
        NODE_CLASS_MAPPINGS as WATERMARK_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as WATERMARK_NODE_DISPLAY_NAME_MAPPINGS,
    )
    from .node.image.create_solid_color_node import (
        CreateSolidColorNode,
        NODE_CLASS_MAPPINGS as SOLID_COLOR_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as SOLID_COLOR_NODE_DISPLAY_NAME_MAPPINGS,
    )
    from .node.image.qr_code_decode_node import (
        QrCodeDecodeNode,
        NODE_CLASS_MAPPINGS as QR_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as QR_NODE_DISPLAY_NAME_MAPPINGS,
    )
    from .node.image.qr_code_create_node import (
        CreateQrCodeNode,
        NODE_CLASS_MAPPINGS as QR_GEN_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as QR_GEN_NODE_DISPLAY_NAME_MAPPINGS,
    )
    from .node.image.batch_load_images_node import (
        BatchLoadImagesNode,
        NODE_CLASS_MAPPINGS as BATCH_LOAD_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as BATCH_LOAD_NODE_DISPLAY_NAME_MAPPINGS,
    )
    from .node.video.video_concat_node import (
        VideoConcatNode,
        NODE_CLASS_MAPPINGS as VIDEO_CONCAT_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as VIDEO_CONCAT_NODE_DISPLAY_NAME_MAPPINGS,
    )
    from .node.video.preview_video_node import (
        PreviewVideoNode,
        NODE_CLASS_MAPPINGS as PREVIEW_VIDEO_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as PREVIEW_VIDEO_NODE_DISPLAY_NAME_MAPPINGS,
    )
    from .node.utility.display_text_node import (
        DisplayTextNode,
        NODE_CLASS_MAPPINGS as DISPLAY_TEXT_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as DISPLAY_TEXT_NODE_DISPLAY_NAME_MAPPINGS,
    )
    from .node.utility.key_storage_node import (
        KeyStorageNode,
        NODE_CLASS_MAPPINGS as KEY_STORAGE_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as KEY_STORAGE_NODE_DISPLAY_NAME_MAPPINGS,
    )
except ImportError:  # pragma: no cover - fallback for direct module loading
    from node.image.image_to_png_node import (
        ImageToPngNode,
        NODE_CLASS_MAPPINGS as IMAGE_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as IMAGE_NODE_DISPLAY_NAME_MAPPINGS,
    )
    from node.utility.pixel_size_to_ratio_node import (
        PixelSizeToRatioNode,
        NODE_CLASS_MAPPINGS as PIXEL_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as PIXEL_NODE_DISPLAY_NAME_MAPPINGS,
    )
    from node.text.save_json_file_node import (
        SaveJsonFileNode,
        NODE_CLASS_MAPPINGS as JSON_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as JSON_NODE_DISPLAY_NAME_MAPPINGS,
    )
    from node.text.custom_llm_node import (
        CustomLLMNode,
        NODE_CLASS_MAPPINGS as CUSTOM_LLM_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as CUSTOM_LLM_NODE_DISPLAY_NAME_MAPPINGS,
    )
    from node.image.save_jpg_node import (
        SaveJPGNode,
        NODE_CLASS_MAPPINGS as JPG_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as JPG_NODE_DISPLAY_NAME_MAPPINGS,
    )
    from node.image.text_watermark_node import (
        TextWatermarkNode,
        NODE_CLASS_MAPPINGS as WATERMARK_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as WATERMARK_NODE_DISPLAY_NAME_MAPPINGS,
    )
    from node.image.create_solid_color_node import (
        CreateSolidColorNode,
        NODE_CLASS_MAPPINGS as SOLID_COLOR_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as SOLID_COLOR_NODE_DISPLAY_NAME_MAPPINGS,
    )
    from node.image.qr_code_decode_node import (
        QrCodeDecodeNode,
        NODE_CLASS_MAPPINGS as QR_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as QR_NODE_DISPLAY_NAME_MAPPINGS,
    )
    from node.image.qr_code_create_node import (
        CreateQrCodeNode,
        NODE_CLASS_MAPPINGS as QR_GEN_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as QR_GEN_NODE_DISPLAY_NAME_MAPPINGS,
    )
    from node.image.batch_load_images_node import (
        BatchLoadImagesNode,
        NODE_CLASS_MAPPINGS as BATCH_LOAD_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as BATCH_LOAD_NODE_DISPLAY_NAME_MAPPINGS,
    )
    from node.video.video_concat_node import (
        VideoConcatNode,
        NODE_CLASS_MAPPINGS as VIDEO_CONCAT_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as VIDEO_CONCAT_NODE_DISPLAY_NAME_MAPPINGS,
    )
    from node.video.preview_video_node import (
        PreviewVideoNode,
        NODE_CLASS_MAPPINGS as PREVIEW_VIDEO_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as PREVIEW_VIDEO_NODE_DISPLAY_NAME_MAPPINGS,
    )
    from node.utility.display_text_node import (
        DisplayTextNode,
        NODE_CLASS_MAPPINGS as DISPLAY_TEXT_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as DISPLAY_TEXT_NODE_DISPLAY_NAME_MAPPINGS,
    )
    from node.utility.key_storage_node import (
        KeyStorageNode,
        NODE_CLASS_MAPPINGS as KEY_STORAGE_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as KEY_STORAGE_NODE_DISPLAY_NAME_MAPPINGS,
    )

# 声明前端 JS 文件目录，ComfyUI 会自动加载该目录下的所有 .js 文件
WEB_DIRECTORY = "./js"

NODE_CLASS_MAPPINGS = {
    **IMAGE_NODE_CLASS_MAPPINGS,
    **PIXEL_NODE_CLASS_MAPPINGS,
    **JSON_NODE_CLASS_MAPPINGS,
    **CUSTOM_LLM_NODE_CLASS_MAPPINGS,
    **JPG_NODE_CLASS_MAPPINGS,
    **WATERMARK_NODE_CLASS_MAPPINGS,
    **SOLID_COLOR_NODE_CLASS_MAPPINGS,
    **QR_NODE_CLASS_MAPPINGS,
    **QR_GEN_NODE_CLASS_MAPPINGS,
    **BATCH_LOAD_NODE_CLASS_MAPPINGS,
    **VIDEO_CONCAT_NODE_CLASS_MAPPINGS,
    **PREVIEW_VIDEO_NODE_CLASS_MAPPINGS,
    **DISPLAY_TEXT_NODE_CLASS_MAPPINGS,
    **KEY_STORAGE_NODE_CLASS_MAPPINGS,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    **IMAGE_NODE_DISPLAY_NAME_MAPPINGS,
    **PIXEL_NODE_DISPLAY_NAME_MAPPINGS,
    **JSON_NODE_DISPLAY_NAME_MAPPINGS,
    **CUSTOM_LLM_NODE_DISPLAY_NAME_MAPPINGS,
    **JPG_NODE_DISPLAY_NAME_MAPPINGS,
    **WATERMARK_NODE_DISPLAY_NAME_MAPPINGS,
    **SOLID_COLOR_NODE_DISPLAY_NAME_MAPPINGS,
    **QR_NODE_DISPLAY_NAME_MAPPINGS,
    **QR_GEN_NODE_DISPLAY_NAME_MAPPINGS,
    **BATCH_LOAD_NODE_DISPLAY_NAME_MAPPINGS,
    **VIDEO_CONCAT_NODE_DISPLAY_NAME_MAPPINGS,
    **PREVIEW_VIDEO_NODE_DISPLAY_NAME_MAPPINGS,
    **DISPLAY_TEXT_NODE_DISPLAY_NAME_MAPPINGS,
    **KEY_STORAGE_NODE_DISPLAY_NAME_MAPPINGS,
}

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "WEB_DIRECTORY",
    "ImageToPngNode",
    "SaveJsonFileNode",
    "CustomLLMNode",
    "SaveJPGNode",
    "PixelSizeToRatioNode",
    "TextWatermarkNode",
    "CreateSolidColorNode",
    "QrCodeDecodeNode",
    "CreateQrCodeNode",
    "BatchLoadImagesNode",
    "VideoConcatNode",
    "PreviewVideoNode",
    "DisplayTextNode",
    "KeyStorageNode",
]
