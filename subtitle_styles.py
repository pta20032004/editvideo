# ===== SỬA LẠI ĐÚNG FORMAT MÀU - subtitle_styles.py =====

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module định nghĩa các kiểu phụ đề - ĐÃ SỬA ĐÚNG FORMAT MÀU
"""

SUBTITLE_COLORS = {
    "white": "&H00ffffff",
    "black": "&H00000000", 
    "yellow": "&H0000ffff",     # BGR: 00 ff ff
    "red": "&H000000ff",        # BGR: 00 00 ff
    "green": "&H0000ff00",      # BGR: 00 ff 00
    "blue": "&H00ff0000",       # BGR: ff 00 00
    "cyan": "&H00ffff00",       # BGR: ff ff 00
    "magenta": "&H00ff00ff",    # BGR: ff 00 ff
    "orange": "&H000080ff",     # BGR: 00 80 ff
    "purple": "&H00800080",     # BGR: 80 00 80
    "pink": "&H00ff80ff"        # BGR: ff 80 ff
}

# Kiểu nền phụ đề - GIỮ NGUYÊN
SUBTITLE_BOX_STYLES = {
    "none": {
        "BorderStyle": "0",
        "Outline": "0",
        "Shadow": "0"
    },
    "outline": {
        "BorderStyle": "1",
        "Outline": "2",      
        "Shadow": "0"        
    },
    "box": {
        "BorderStyle": "4",  # Box style cho nền
        "Outline": "0",
        "Shadow": "0"
    },
    "rounded_box": {
        "BorderStyle": "4",
        "Outline": "0",      
        "Shadow": "0"
    },
    "shadow_box": {
        "BorderStyle": "4",
        "Outline": "0",      
        "Shadow": "1"
    }
}

# Preset - GIỮ NGUYÊN
SUBTITLE_PRESETS = {
    "default": {
        "text_color": "black",
        "box_style": "box",
        "box_color": "white",
        "font_name": "Arial",
        "font_size": 10
    }
}

def get_subtitle_style_string(text_color="black", box_style="box", box_color="white", 
                             font_name="Arial", font_size=10, margin_v=50, opacity=255):
    """
    Tạo chuỗi kiểu phụ đề cho FFmpeg - ĐÃ SỬA ĐÚNG FORMAT
    """
    # Lấy mã màu BGR với &H format
    text_color_code = SUBTITLE_COLORS.get(text_color.lower(), SUBTITLE_COLORS["black"])
    box_color_code = SUBTITLE_COLORS.get(box_color.lower(), SUBTITLE_COLORS["white"])
    
    print(f"🎨 Color mapping: {text_color} -> {text_color_code}, {box_color} -> {box_color_code}")
    
    # Lấy kiểu khung nền
    box_style_params = SUBTITLE_BOX_STYLES.get(box_style.lower(), SUBTITLE_BOX_STYLES["box"]).copy()
    
    # Xây dựng chuỗi kiểu
    style_parts = [
        f"FontName={font_name}",
        f"FontSize={font_size}",
        f"PrimaryColour={text_color_code}",  # ✅ ĐÚNG: &H format
        f"MarginV={margin_v}",
        f"Alignment=2"
    ]
    
    # Thêm BackColour cho các style có nền
    if box_style.lower() in ["box", "rounded_box", "shadow_box"]:
        style_parts.append(f"BackColour={box_color_code}")  # ✅ ĐÚNG: &H format
        print(f"🎨 Added background: {box_color_code}")
    
    # Thêm các tham số kiểu khung
    for key, value in box_style_params.items():
        style_parts.append(f"{key}={value}")
    
    result = ",".join(style_parts)
    print(f"🎨 Final style: {result}")
    return result

def get_preset_style(preset_name="default"):
    """Lấy kiểu preset"""
    preset = SUBTITLE_PRESETS.get(preset_name.lower(), SUBTITLE_PRESETS["default"])
    
    return get_subtitle_style_string(
        text_color=preset["text_color"],
        box_style=preset["box_style"],
        box_color=preset["box_color"],
        font_name=preset["font_name"],
        font_size=preset["font_size"]
    )

# Test function
def test_colors():
    """Test màu sắc"""
    print("🧪 Testing BGR color format:")
    for color_name, color_code in SUBTITLE_COLORS.items():
        print(f"  {color_name:10} -> {color_code}")
    
    print("\n🧪 Testing red text on yellow background:")
    test_style = get_subtitle_style_string("red", "box", "yellow", "Arial", 12)
    print(f"  Result: {test_style}")
    
    # Verify colors
    print(f"\n✅ Red should be: &H000000ff (actual: {SUBTITLE_COLORS['red']})")
    print(f"✅ Yellow should be: &H0000ffff (actual: {SUBTITLE_COLORS['yellow']})")

if __name__ == "__main__":
    test_colors()