#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module định nghĩa các kiểu phụ đề
"""

# Màu sắc phụ đề
SUBTITLE_COLORS = {
    "white": "&Hffffff",
    "black": "&H000000",
    "yellow": "&Hffff00",
    "red": "&Hff0000",
    "green": "&H00ff00", 
    "blue": "&H0000ff",
    "cyan": "&H00ffff",
    "magenta": "&Hff00ff",
    "orange": "&Hff8c00",
    "purple": "&H8a2be2",
    "pink": "&Hffc0cb"
}

# Kiểu nền phụ đề - ĐÃ SỬA ĐỘ DÀY
SUBTITLE_BOX_STYLES = {
    "none": {
        "BoxStyle": "0"  # Không có khung nền
    },
    "outline": {
        "BorderStyle": "1",  # Viền
        "Outline": "1",      # ĐÃ GIẢM: Độ dày viền từ 2 xuống 1
        "Shadow": "1"        # ĐÃ GIẢM: Bóng đổ từ 2 xuống 1
    },
    "box": {
        "BorderStyle": "4",  # Khung nền
        "Outline": "0",      # ĐÃ GIẢM: Viền từ 1 xuống 0 (không viền)
        "Shadow": "0"        # Không bóng
    },
    "rounded_box": {
        "BorderStyle": "4",  # Khung nền
        "Outline": "0",      # ĐÃ GIẢM: Viền từ 1 xuống 0
        "Shadow": "0",       # Không bóng
        "BorderColour": "0"  # Viền trong suốt
    },
    "shadow_box": {
        "BorderStyle": "1",  # Viền
        "Outline": "1",      # ĐÃ GIẢM: Độ dày viền từ 2 xuống 1
        "Shadow": "2"        # ĐÃ GIẢM: Bóng đổ từ 3 xuống 2
    }
}

# Các bộ kiểu mẫu - CHỈ GIỮ LẠI DEFAULT
SUBTITLE_PRESETS = {
    "default": {
        "text_color": "black",
        "box_style": "box",
        "box_color": "white",
        "font_name": "Arial",
        "font_size": 10  # ĐÃ THAY ĐỔI: Từ 24 xuống 10
    }
    # ĐÃ XÓA: Tất cả preset khác (tiktok, youtube, instagram, modern, classic)
}

def get_subtitle_style_string(text_color="black", box_style="box", box_color="white", 
                             font_name="Arial", font_size=10, margin_v=50, opacity=255):  # ĐÃ THAY ĐỔI: font_size từ 12 xuống 10
    """
    Tạo chuỗi kiểu phụ đề cho FFmpeg
    
    Args:
        text_color (str): Màu chữ phụ đề
        box_style (str): Kiểu khung ('none', 'outline', 'box', 'rounded_box', 'shadow_box')
        box_color (str): Màu nền khung
        font_name (str): Tên font chữ
        font_size (int): Cỡ chữ
        margin_v (int): Khoảng cách lề dưới
        opacity (int): Độ trong suốt (0-255)
        
    Returns:
        str: Chuỗi kiểu phụ đề
    """
    # Lấy mã màu từ tên
    text_color_code = SUBTITLE_COLORS.get(text_color.lower(), SUBTITLE_COLORS["black"])  # ĐÃ THAY ĐỔI: Mặc định từ white thành black
    box_color_code = SUBTITLE_COLORS.get(box_color.lower(), SUBTITLE_COLORS["white"])    # ĐÃ THAY ĐỔI: Mặc định từ black thành white
    
    # Lấy kiểu khung nền
    box_style_params = SUBTITLE_BOX_STYLES.get(box_style.lower(), SUBTITLE_BOX_STYLES["box"])  # ĐÃ THAY ĐỔI: Mặc định từ outline thành box
    
    # Xây dựng chuỗi kiểu
    style_parts = [
        f"FontName={font_name}",
        f"FontSize={font_size}",
        f"PrimaryColour={text_color_code}",
        f"BackColour={box_color_code}",
        f"MarginV={margin_v}",
        f"Alpha={hex(255-opacity)[2:].zfill(2)}"
    ]
    
    # Thêm các tham số kiểu khung nền
    for key, value in box_style_params.items():
        style_parts.append(f"{key}={value}")
    
    # Ghép thành chuỗi cuối cùng
    return ",".join(style_parts)

def get_preset_style(preset_name="default"):
    """
    Lấy kiểu phụ đề từ preset có sẵn
    
    Args:
        preset_name (str): Tên preset
        
    Returns:
        str: Chuỗi kiểu phụ đề
    """
    preset = SUBTITLE_PRESETS.get(preset_name.lower(), SUBTITLE_PRESETS["default"])
    
    return get_subtitle_style_string(
        text_color=preset["text_color"],
        box_style=preset["box_style"],
        box_color=preset["box_color"],
        font_name=preset["font_name"],
        font_size=preset["font_size"]
    )