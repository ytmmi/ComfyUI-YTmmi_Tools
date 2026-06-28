try:
    from .node.image_to_png_node import (
        ImageToPngNode,
        NODE_CLASS_MAPPINGS as IMAGE_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as IMAGE_NODE_DISPLAY_NAME_MAPPINGS,
    )
    from .node.pixel_size_to_ratio_node import (
        PixelSizeToRatioNode,
        NODE_CLASS_MAPPINGS as PIXEL_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as PIXEL_NODE_DISPLAY_NAME_MAPPINGS,
    )
    from .node.save_json_file_node import (
        SaveJsonFileNode,
        NODE_CLASS_MAPPINGS as JSON_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as JSON_NODE_DISPLAY_NAME_MAPPINGS,
    )
    from .node.save_jpg_node import (
        SaveJPGNode,
        NODE_CLASS_MAPPINGS as JPG_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as JPG_NODE_DISPLAY_NAME_MAPPINGS,
    )
    from .node.text_watermark_node import (
        TextWatermarkNode,
        NODE_CLASS_MAPPINGS as WATERMARK_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as WATERMARK_NODE_DISPLAY_NAME_MAPPINGS,
    )
    from .node.create_solid_color_node import (
        CreateSolidColorNode,
        NODE_CLASS_MAPPINGS as SOLID_COLOR_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as SOLID_COLOR_NODE_DISPLAY_NAME_MAPPINGS,
    )
    from .node.qr_code_decode_node import (
        QrCodeDecodeNode,
        NODE_CLASS_MAPPINGS as QR_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as QR_NODE_DISPLAY_NAME_MAPPINGS,
    )
    from .node.qr_code_create_node import (
        CreateQrCodeNode,
        NODE_CLASS_MAPPINGS as QR_GEN_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as QR_GEN_NODE_DISPLAY_NAME_MAPPINGS,
    )
except ImportError:  # pragma: no cover - fallback for direct module loading
    from node.image_to_png_node import (
        ImageToPngNode,
        NODE_CLASS_MAPPINGS as IMAGE_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as IMAGE_NODE_DISPLAY_NAME_MAPPINGS,
    )
    from node.pixel_size_to_ratio_node import (
        PixelSizeToRatioNode,
        NODE_CLASS_MAPPINGS as PIXEL_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as PIXEL_NODE_DISPLAY_NAME_MAPPINGS,
    )
    from node.save_json_file_node import (
        SaveJsonFileNode,
        NODE_CLASS_MAPPINGS as JSON_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as JSON_NODE_DISPLAY_NAME_MAPPINGS,
    )
    from node.save_jpg_node import (
        SaveJPGNode,
        NODE_CLASS_MAPPINGS as JPG_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as JPG_NODE_DISPLAY_NAME_MAPPINGS,
    )
    from node.text_watermark_node import (
        TextWatermarkNode,
        NODE_CLASS_MAPPINGS as WATERMARK_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as WATERMARK_NODE_DISPLAY_NAME_MAPPINGS,
    )
    from node.create_solid_color_node import (
        CreateSolidColorNode,
        NODE_CLASS_MAPPINGS as SOLID_COLOR_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as SOLID_COLOR_NODE_DISPLAY_NAME_MAPPINGS,
    )
    from node.qr_code_decode_node import (
        QrCodeDecodeNode,
        NODE_CLASS_MAPPINGS as QR_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as QR_NODE_DISPLAY_NAME_MAPPINGS,
    )
    from node.qr_code_create_node import (
        CreateQrCodeNode,
        NODE_CLASS_MAPPINGS as QR_GEN_NODE_CLASS_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as QR_GEN_NODE_DISPLAY_NAME_MAPPINGS,
    )

NODE_CLASS_MAPPINGS = {
    **IMAGE_NODE_CLASS_MAPPINGS,
    **PIXEL_NODE_CLASS_MAPPINGS,
    **JSON_NODE_CLASS_MAPPINGS,
    **JPG_NODE_CLASS_MAPPINGS,
    **WATERMARK_NODE_CLASS_MAPPINGS,
    **SOLID_COLOR_NODE_CLASS_MAPPINGS,
    **QR_NODE_CLASS_MAPPINGS,
    **QR_GEN_NODE_CLASS_MAPPINGS,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    **IMAGE_NODE_DISPLAY_NAME_MAPPINGS,
    **PIXEL_NODE_DISPLAY_NAME_MAPPINGS,
    **JSON_NODE_DISPLAY_NAME_MAPPINGS,
    **JPG_NODE_DISPLAY_NAME_MAPPINGS,
    **WATERMARK_NODE_DISPLAY_NAME_MAPPINGS,
    **SOLID_COLOR_NODE_DISPLAY_NAME_MAPPINGS,
    **QR_NODE_DISPLAY_NAME_MAPPINGS,
    **QR_GEN_NODE_DISPLAY_NAME_MAPPINGS,
}

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "ImageToPngNode",
    "SaveJsonFileNode",
    "SaveJPGNode",
    "PixelSizeToRatioNode",
    "TextWatermarkNode",
    "CreateSolidColorNode",
    "QrCodeDecodeNode",
    "CreateQrCodeNode",
]
