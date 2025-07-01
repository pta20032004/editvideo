#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module quản lý vị trí phụ đề
"""

# Định nghĩa các vị trí preset
SUBTITLE_POSITIONS = {
    "bottom_center": {
        "alignment": 2,  # Bottom center
        "margin_v": 50,
        "margin_l": 0,
        "margin_r": 0,
        "description": "Dưới cùng giữa (mặc định)"
    },
    "bottom_left": {
        "alignment": 1,  # Bottom left
        "margin_v": 50,
        "margin_l": 50,
        "margin_r": 0,
        "description": "Dưới cùng trái"
    },
    "bottom_right": {
        "alignment": 3,  # Bottom right
        "margin_v": 50,
        "margin_l": 0,
        "margin_r": 50,
        "description": "Dưới cùng phải"
    },
    "center": {
        "alignment": 5,  # Center
        "margin_v": 0,
        "margin_l": 0,
        "margin_r": 0,
        "description": "Chính giữa màn hình"
    },
    "top_center": {
        "alignment": 8,  # Top center
        "margin_v": 50,
        "margin_l": 0,
        "margin_r": 0,
        "description": "Trên cùng giữa"
    },
    "top_left": {
        "alignment": 7,  # Top left
        "margin_v": 50,
        "margin_l": 50,
        "margin_r": 0,
        "description": "Trên cùng trái"
    },
    "top_right": {
        "alignment": 9,  # Top right
        "margin_v": 50,
        "margin_l": 0,
        "margin_r": 50,
        "description": "Trên cùng phải"
    },
    "custom": {
        "alignment": 2,  # Default to bottom center
        "margin_v": 50,
        "margin_l": 0,
        "margin_r": 0,
        "description": "Tùy chỉnh"
    }
}

def get_subtitle_position_string(position="bottom_center", custom_margin_v=None, 
                                custom_margin_l=None, custom_margin_r=None):
    """
    Tạo chuỗi cấu hình vị trí cho subtitle
    
    Args:
        position (str): Vị trí preset
        custom_margin_v (int): Khoảng cách từ trên/dưới (tùy chỉnh)
        custom_margin_l (int): Khoảng cách từ trái (tùy chỉnh)
        custom_margin_r (int): Khoảng cách từ phải (tùy chỉnh)
    
    Returns:
        dict: Thông tin vị trí
    """
    if position not in SUBTITLE_POSITIONS:
        position = "bottom_center"
    
    pos_config = SUBTITLE_POSITIONS[position].copy()
    
    # Áp dụng custom values nếu có
    if position == "custom":
        if custom_margin_v is not None:
            pos_config["margin_v"] = custom_margin_v
        if custom_margin_l is not None:
            pos_config["margin_l"] = custom_margin_l
        if custom_margin_r is not None:
            pos_config["margin_r"] = custom_margin_r
    
    return pos_config

def get_all_positions():
    """Lấy danh sách tất cả vị trí có sẵn"""
    return {key: value["description"] for key, value in SUBTITLE_POSITIONS.items()}

# Tích hợp vào subtitle_styles.py
def get_subtitle_style_with_position(text_color="black", box_style="box", box_color="white", 
                                   font_name="Arial", font_size=10, position="bottom_center",
                                   custom_margin_v=None, custom_margin_l=None, custom_margin_r=None,
                                   opacity=255):
    """
    Tạo chuỗi kiểu phụ đề hoàn chỉnh với vị trí
    """
    from subtitle_styles import SUBTITLE_COLORS, SUBTITLE_BOX_STYLES
    
    # Lấy mã màu
    text_color_code = SUBTITLE_COLORS.get(text_color.lower(), SUBTITLE_COLORS["black"])
    box_color_code = SUBTITLE_COLORS.get(box_color.lower(), SUBTITLE_COLORS["white"])
    
    # Lấy kiểu khung nền
    box_style_params = SUBTITLE_BOX_STYLES.get(box_style.lower(), SUBTITLE_BOX_STYLES["box"]).copy()
    
    # Lấy vị trí
    position_config = get_subtitle_position_string(position, custom_margin_v, custom_margin_l, custom_margin_r)
    
    # Xây dựng chuỗi kiểu
    style_parts = [
        f"FontName={font_name}",
        f"FontSize={font_size}",
        f"PrimaryColour={text_color_code}",
        f"Alignment={position_config['alignment']}",
        f"MarginV={position_config['margin_v']}",
        f"MarginL={position_config['margin_l']}",
        f"MarginR={position_config['margin_r']}"
    ]
    
    # Thêm BackColour cho các style có nền
    if box_style.lower() in ["box", "rounded_box", "shadow_box"]:
        style_parts.append(f"BackColour={box_color_code}")
    
    # Thêm các tham số kiểu khung nền
    for key, value in box_style_params.items():
        if key != "BackColour":
            style_parts.append(f"{key}={value}")
    
    return ",".join(style_parts)