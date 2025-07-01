# ===== TOÀN BỘ FILE subtitle_styles.py MỚI =====

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module định nghĩa các kiểu phụ đề - ĐÃ SỬA ĐỂ CÓ NỀN ĐÚNG
"""

# Màu sắc phụ đề - BGR format cho ASS
SUBTITLE_COLORS = {
    "white": "&Hffffff&",
    "black": "&H000000&", 
    "yellow": "&H00ffff&",     # BGR: blue=00, green=ff, red=ff
    "red": "&H0000ff&",        # BGR: blue=00, green=00, red=ff
    "green": "&H00ff00&",      # BGR: blue=00, green=ff, red=00
    "blue": "&Hff0000&",       # BGR: blue=ff, green=00, red=00
    "cyan": "&Hffff00&",       # BGR: blue=ff, green=ff, red=00
    "magenta": "&Hff00ff&",    # BGR: blue=ff, green=00, red=ff
    "orange": "&H008cff&",     # BGR: blue=00, green=8c, red=ff
    "purple": "&He22b8a&",     # BGR: blue=e2, green=2b, red=8a
    "pink": "&Hcbc0ff&"        # BGR: blue=cb, green=c0, red=ff
}

# Kiểu nền phụ đề - ĐÃ SỬA ĐỂ CÓ NỀN
SUBTITLE_BOX_STYLES = {
    "none": {
        "BorderStyle": "0",  # Không có nền
        "Outline": "0",
        "Shadow": "0"
    },
    "outline": {
        "BorderStyle": "1",  # Chỉ viền, không nền
        "Outline": "2",      
        "Shadow": "0"        
    },
    "box": {
        "BorderStyle": "4",  # ĐÃ SỬA: 4 = có nền box
        "Outline": "0",      # Không viền
        "Shadow": "0",       # Không đổ bóng
        "BackColour": "auto" # Sẽ được set trong function
    },
    "rounded_box": {
        "BorderStyle": "4",  # Có nền
        "Outline": "0",      
        "Shadow": "0",
        "BackColour": "auto"
    },
    "shadow_box": {
        "BorderStyle": "4",  # Có nền + shadow nhẹ
        "Outline": "0",      
        "Shadow": "1",
        "BackColour": "auto"
    }
}

# Các bộ kiểu mẫu
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
    Tạo chuỗi kiểu phụ đề cho FFmpeg - ĐÃ SỬA ĐỂ CÓ NỀN
    """
    # Lấy mã màu từ tên
    text_color_code = SUBTITLE_COLORS.get(text_color.lower(), SUBTITLE_COLORS["black"])
    box_color_code = SUBTITLE_COLORS.get(box_color.lower(), SUBTITLE_COLORS["white"])
    
    # Lấy kiểu khung nền
    box_style_params = SUBTITLE_BOX_STYLES.get(box_style.lower(), SUBTITLE_BOX_STYLES["box"]).copy()
    
    # Xây dựng chuỗi kiểu
    style_parts = [
        f"FontName={font_name}",
        f"FontSize={font_size}",
        f"PrimaryColour={text_color_code}",
        f"MarginV={margin_v}",
        f"Alignment=2"  # Bottom center
    ]
    
    # Thêm BackColour cho các style có nền
    if box_style.lower() in ["box", "rounded_box", "shadow_box"]:
        style_parts.append(f"BackColour={box_color_code}")
    
    # Thêm các tham số kiểu khung nền (bỏ BackColour vì đã xử lý riêng)
    for key, value in box_style_params.items():
        if key != "BackColour":  # Đã thêm riêng ở trên
            style_parts.append(f"{key}={value}")
    
    return ",".join(style_parts)

def get_preset_style(preset_name="default"):
    """
    Lấy kiểu phụ đề từ preset có sẵn
    """
    preset = SUBTITLE_PRESETS.get(preset_name.lower(), SUBTITLE_PRESETS["default"])
    
    return get_subtitle_style_string(
        text_color=preset["text_color"],
        box_style=preset["box_style"],
        box_color=preset["box_color"],
        font_name=preset["font_name"],
        font_size=preset["font_size"]
    )

# ===== HÀM configure_subtitle_style TRONG app_gui_main.py ĐÃ SỬA UI =====

def configure_subtitle_style(self):
    """Hiển thị dialog cấu hình kiểu phụ đề tùy chỉnh - ĐÃ SỬA UI VÀ PREVIEW"""
    dialog = tk.Toplevel(self.root)
    dialog.title("🎨 Tùy chỉnh kiểu phụ đề")
    dialog.geometry("600x500")  # ĐÃ SỬA: Tăng kích thước
    dialog.transient(self.root)
    dialog.grab_set()
    
    # Main frame với scrollbar nếu cần
    main_frame = ttk.Frame(dialog, padding="20")
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Title
    ttk.Label(main_frame, text="🎨 Tùy chỉnh kiểu phụ đề", font=("Arial", 14, "bold")).pack(pady=(0, 20))
    
    # Controls frame
    controls_frame = ttk.Frame(main_frame)
    controls_frame.pack(fill=tk.X, pady=(0, 20))
    
    # Màu chữ
    text_frame = ttk.Frame(controls_frame)
    text_frame.pack(fill=tk.X, pady=5)
    ttk.Label(text_frame, text="Màu chữ:", width=12).pack(side=tk.LEFT)
    text_colors = ["black", "white", "yellow", "red", "green", "blue", "cyan", "magenta", "orange", "purple", "pink"]
    text_color_combo = ttk.Combobox(
        text_frame,
        textvariable=self.subtitle_text_color,
        values=text_colors,
        state="readonly",
        width=12
    )
    text_color_combo.pack(side=tk.LEFT, padx=(10, 0))
    
    # Kiểu nền
    box_frame = ttk.Frame(controls_frame)
    box_frame.pack(fill=tk.X, pady=5)
    ttk.Label(box_frame, text="Kiểu nền:", width=12).pack(side=tk.LEFT)
    box_styles = ["none", "outline", "box", "rounded_box", "shadow_box"]
    box_style_combo = ttk.Combobox(
        box_frame,
        textvariable=self.subtitle_box_style,
        values=box_styles,
        state="readonly",
        width=12
    )
    box_style_combo.pack(side=tk.LEFT, padx=(10, 0))
    
    # Màu nền
    box_color_frame = ttk.Frame(controls_frame)
    box_color_frame.pack(fill=tk.X, pady=5)
    ttk.Label(box_color_frame, text="Màu nền:", width=12).pack(side=tk.LEFT)
    box_colors = ["black", "white", "yellow", "red", "green", "blue", "cyan", "magenta", "orange", "purple", "pink"]
    box_color_combo = ttk.Combobox(
        box_color_frame,
        textvariable=self.subtitle_box_color,
        values=box_colors,
        state="readonly",
        width=12
    )
    box_color_combo.pack(side=tk.LEFT, padx=(10, 0))
    
    # Cỡ chữ
    font_frame = ttk.Frame(controls_frame)
    font_frame.pack(fill=tk.X, pady=5)
    ttk.Label(font_frame, text="Cỡ chữ:", width=12).pack(side=tk.LEFT)
    font_size_spinbox = ttk.Spinbox(
        font_frame,
        from_=6, to=24, increment=1,
        textvariable=self.subtitle_font_size,
        width=8
    )
    font_size_spinbox.pack(side=tk.LEFT, padx=(10, 0))
    
    # Preview - ĐÃ SỬA: HIỂN THỊ NỀN ĐÚNG
    preview_frame = ttk.LabelFrame(main_frame, text="Xem trước", padding="15")
    preview_frame.pack(fill=tk.X, pady=(20, 10))
    
    preview_canvas = tk.Canvas(preview_frame, width=500, height=120, bg="gray20")  # Nền xám đậm để thấy rõ
    preview_canvas.pack()
    
    # Text và background
    preview_text_id = preview_canvas.create_text(
        250, 60, 
        text="Đây là mẫu phụ đề", 
        fill="black",  # Sẽ thay đổi theo setting
        font=("Arial", 12),  # Sẽ thay đổi theo setting
        anchor="center"
    )
    
    # Background rectangle
    preview_bg_id = preview_canvas.create_rectangle(
        0, 0, 0, 0,
        fill="white", outline="", state="normal"  # Sẽ thay đổi theo setting
    )
    
    # Move background behind text
    preview_canvas.tag_lower(preview_bg_id, preview_text_id)
    
    # Update preview function - ĐÃ SỬA: HIỂN THỊ ĐÚNG MÀU VÀ NỀN
    def update_preview(*args):
        # Update text color
        text_color = self.subtitle_text_color.get()
        # Convert color name to RGB for canvas (not BGR)
        color_map = {
            "black": "black", "white": "white", "yellow": "yellow", 
            "red": "red", "green": "green", "blue": "blue",
            "cyan": "cyan", "magenta": "magenta", "orange": "orange",
            "purple": "purple", "pink": "pink"
        }
        canvas_text_color = color_map.get(text_color, "black")
        preview_canvas.itemconfig(preview_text_id, fill=canvas_text_color)
        
        # Update font size
        font_size = self.subtitle_font_size.get()
        preview_canvas.itemconfig(preview_text_id, font=("Arial", font_size))
        
        # Update background
        box_style = self.subtitle_box_style.get()
        box_color = self.subtitle_box_color.get()
        canvas_box_color = color_map.get(box_color, "white")
        
        if box_style in ["box", "rounded_box", "shadow_box"]:
            # Hiển thị nền
            bbox = preview_canvas.bbox(preview_text_id)
            if bbox:
                padding = 15
                x1, y1, x2, y2 = bbox
                x1 -= padding
                y1 -= padding
                x2 += padding
                y2 += padding
                
                preview_canvas.coords(preview_bg_id, x1, y1, x2, y2)
                preview_canvas.itemconfig(preview_bg_id, fill=canvas_box_color, state="normal")
        else:
            # Ẩn nền
            preview_canvas.itemconfig(preview_bg_id, state="hidden")
    
    # Track changes để update preview
    self.subtitle_text_color.trace_add("write", update_preview)
    self.subtitle_box_style.trace_add("write", update_preview)
    self.subtitle_box_color.trace_add("write", update_preview)
    self.subtitle_font_size.trace_add("write", update_preview)
    
    # Initial preview update
    update_preview()
    
    # Buttons frame - ĐÃ SỬA: ĐỂ KHÔNG BỊ CHE
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill=tk.X, pady=(30, 0))  # Tăng padding top
    
    def apply_style():
        # Disable preset when using custom style
        self.subtitle_preset.set("")
        
        # Update main window preview
        self.style_preview_label.config(text=f"👉 Tùy chỉnh: Chữ {self.subtitle_text_color.get()}, nền {self.subtitle_box_color.get()}, cỡ {self.subtitle_font_size.get()}")
        
        # Đóng dialog
        dialog.destroy()
    
    apply_button = ttk.Button(
        button_frame, 
        text="✓ Áp dụng", 
        command=apply_style,
        style="Accent.TButton"
    )
    apply_button.pack(side=tk.LEFT, padx=(0, 10))
    
    cancel_button = ttk.Button(
        button_frame, 
        text="❌ Hủy", 
        command=dialog.destroy
    )
    cancel_button.pack(side=tk.RIGHT)

print("✅ Đã sửa hoàn toàn:")
print("   1. BorderStyle = 4 cho box styles = CÓ NỀN")
print("   2. Preview hiển thị đúng màu chữ + nền")
print("   3. Tăng kích thước dialog: 600x500")
print("   4. Buttons không bị che nữa")
print("   5. BackColour được set đúng cho từng style")
print("   6. Màu BGR format đúng cho ASS output")