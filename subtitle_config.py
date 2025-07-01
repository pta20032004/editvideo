#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module tổng hợp tất cả cấu hình phụ đề - Style + Position + Language
"""

from subtitle_styles import (
    SUBTITLE_COLORS, SUBTITLE_BOX_STYLES, SUBTITLE_PRESETS,
    get_subtitle_style_string, get_preset_style
)
from subtitle_position import (
    SUBTITLE_POSITIONS, get_subtitle_position_string, get_all_positions
)

class SubtitleConfig:
    """Class quản lý tổng hợp cấu hình phụ đề"""
    
    def __init__(self):
        # Default values
        self.text_color = "black"
        self.box_style = "box"
        self.box_color = "white"
        self.font_name = "Arial"
        self.font_size = 10
        self.position = "bottom_center"
        self.custom_margin_v = 50
        self.custom_margin_l = 0
        self.custom_margin_r = 0
        self.preset = "default"
        
        # Language support
        self.language_configs = {
            'vi': {'words_per_line': 7, 'font_size_adjust': 0},
            'en': {'words_per_line': 6, 'font_size_adjust': 0},
            'zh': {'words_per_line': 10, 'font_size_adjust': 2},     # ✅ Tiếng Trung
            'zh-cn': {'words_per_line': 10, 'font_size_adjust': 2},  # ✅ Trung Giản thể
            'zh-tw': {'words_per_line': 10, 'font_size_adjust': 2},  # ✅ Trung Phồn thể
            'ja': {'words_per_line': 8, 'font_size_adjust': 1},
            'ko': {'words_per_line': 8, 'font_size_adjust': 1},
            'es': {'words_per_line': 6, 'font_size_adjust': 0},
            'fr': {'words_per_line': 6, 'font_size_adjust': 0},
            'de': {'words_per_line': 5, 'font_size_adjust': 0}
        }
    
    def get_language_config(self, language):
        """Lấy cấu hình cho ngôn ngữ cụ thể"""
        return self.language_configs.get(language, self.language_configs['en'])
    
    def get_adjusted_font_size(self, language):
        """Lấy font size đã điều chỉnh cho ngôn ngữ"""
        lang_config = self.get_language_config(language)
        return self.font_size + lang_config['font_size_adjust']
    
    def get_words_per_line(self, language):
        """Lấy số từ/ký tự mỗi dòng cho ngôn ngữ"""
        lang_config = self.get_language_config(language)
        return lang_config['words_per_line']
    
    def apply_preset(self, preset_name):
        """Áp dụng preset có sẵn"""
        if preset_name in SUBTITLE_PRESETS:
            preset = SUBTITLE_PRESETS[preset_name]
            self.text_color = preset.get("text_color", self.text_color)
            self.box_style = preset.get("box_style", self.box_style)
            self.box_color = preset.get("box_color", self.box_color)
            self.font_name = preset.get("font_name", self.font_name)
            self.font_size = preset.get("font_size", self.font_size)
            self.preset = preset_name
    
    def get_full_style_string(self, language='vi'):
        """Tạo chuỗi style hoàn chỉnh với language support"""
        # Điều chỉnh font size theo ngôn ngữ
        adjusted_font_size = self.get_adjusted_font_size(language)
        
        # Lấy position config
        position_config = get_subtitle_position_string(
            self.position, 
            self.custom_margin_v, 
            self.custom_margin_l, 
            self.custom_margin_r
        )
        
        # Tạo style string với position
        style_parts = [
            f"FontName={self.font_name}",
            f"FontSize={adjusted_font_size}",
            f"PrimaryColour={SUBTITLE_COLORS.get(self.text_color.lower(), SUBTITLE_COLORS['black'])}",
            f"Alignment={position_config['alignment']}",
            f"MarginV={position_config['margin_v']}",
            f"MarginL={position_config['margin_l']}",
            f"MarginR={position_config['margin_r']}"
        ]
        
        # Thêm BackColour cho style có nền
        if self.box_style.lower() in ["box", "rounded_box", "shadow_box"]:
            style_parts.append(f"BackColour={SUBTITLE_COLORS.get(self.box_color.lower(), SUBTITLE_COLORS['white'])}")
        
        # Thêm box style parameters
        box_params = SUBTITLE_BOX_STYLES.get(self.box_style.lower(), SUBTITLE_BOX_STYLES["box"]).copy()
        for key, value in box_params.items():
            if key != "BackColour":
                style_parts.append(f"{key}={value}")
        
        return ",".join(style_parts)
    
    def to_dict(self):
        """Chuyển config thành dictionary"""
        return {
            "text_color": self.text_color,
            "box_style": self.box_style,
            "box_color": self.box_color,
            "font_name": self.font_name,
            "font_size": self.font_size,
            "position": self.position,
            "custom_margin_v": self.custom_margin_v,
            "custom_margin_l": self.custom_margin_l,
            "custom_margin_r": self.custom_margin_r,
            "preset": self.preset
        }
    
    def from_dict(self, config_dict):
        """Load config từ dictionary"""
        for key, value in config_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def get_available_colors(self):
        """Lấy danh sách màu có sẵn"""
        return list(SUBTITLE_COLORS.keys())
    
    def get_available_box_styles(self):
        """Lấy danh sách kiểu nền có sẵn"""
        return list(SUBTITLE_BOX_STYLES.keys())
    
    def get_available_positions(self):
        """Lấy danh sách vị trí có sẵn"""
        return get_all_positions()
    
    def get_available_presets(self):
        """Lấy danh sách preset có sẵn"""
        return list(SUBTITLE_PRESETS.keys())

# ✅ THÊM: Hàm tiện ích để tạo SubtitleConfig từ GUI variables
def create_subtitle_config_from_gui(gui_vars):
    """
    Tạo SubtitleConfig từ các biến GUI
    
    Args:
        gui_vars (dict): Dictionary chứa các tkinter variables từ GUI
            {
                'text_color': StringVar,
                'box_style': StringVar,
                'box_color': StringVar,
                'font_size': IntVar,
                'position': StringVar,
                'custom_margin_v': IntVar,
                'custom_margin_l': IntVar,
                'custom_margin_r': IntVar,
                'preset': StringVar
            }
    
    Returns:
        SubtitleConfig: Configured subtitle config object
    """
    config = SubtitleConfig()
    
    # Apply values from GUI
    if 'preset' in gui_vars and gui_vars['preset'].get():
        config.apply_preset(gui_vars['preset'].get())
    else:
        # Custom configuration
        config.text_color = gui_vars.get('text_color', config.text_color).get() if hasattr(gui_vars.get('text_color'), 'get') else config.text_color
        config.box_style = gui_vars.get('box_style', config.box_style).get() if hasattr(gui_vars.get('box_style'), 'get') else config.box_style
        config.box_color = gui_vars.get('box_color', config.box_color).get() if hasattr(gui_vars.get('box_color'), 'get') else config.box_color
        config.font_size = gui_vars.get('font_size', config.font_size).get() if hasattr(gui_vars.get('font_size'), 'get') else config.font_size
        config.position = gui_vars.get('position', config.position).get() if hasattr(gui_vars.get('position'), 'get') else config.position
        config.custom_margin_v = gui_vars.get('custom_margin_v', config.custom_margin_v).get() if hasattr(gui_vars.get('custom_margin_v'), 'get') else config.custom_margin_v
        config.custom_margin_l = gui_vars.get('custom_margin_l', config.custom_margin_l).get() if hasattr(gui_vars.get('custom_margin_l'), 'get') else config.custom_margin_l
        config.custom_margin_r = gui_vars.get('custom_margin_r', config.custom_margin_r).get() if hasattr(gui_vars.get('custom_margin_r'), 'get') else config.custom_margin_r
    
    return config

# ✅ THÊM: Hàm để tạo style legacy format (backward compatibility)
def get_legacy_subtitle_style(subtitle_config, language='vi'):
    """
    Tạo dictionary style theo format cũ để tương thích với code hiện tại
    
    Args:
        subtitle_config (SubtitleConfig): Config object
        language (str): Ngôn ngữ
    
    Returns:
        dict: Style dictionary theo format cũ
    """
    return {
        "text_color": subtitle_config.text_color,
        "box_style": subtitle_config.box_style,
        "box_color": subtitle_config.box_color,
        "font_name": subtitle_config.font_name,
        "font_size": subtitle_config.get_adjusted_font_size(language),
        "position": subtitle_config.position,
        "custom_margin_v": subtitle_config.custom_margin_v,
        "custom_margin_l": subtitle_config.custom_margin_l,
        "custom_margin_r": subtitle_config.custom_margin_r,
        "preset": subtitle_config.preset if subtitle_config.preset != "default" else None
    }