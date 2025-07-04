#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI đơn giản với Video Overlay
"""


try:
    from gui_img import ImageInserterApp
    HAS_IMAGE_MODULE = True
except ImportError as e:
    print(f"⚠️ Không thể import gui_img: {e}")
    HAS_IMAGE_MODULE = False

try:
    from subtitle_config import SubtitleConfig, create_subtitle_config_from_gui, get_legacy_subtitle_style
    HAS_SUBTITLE_CONFIG = True
except ImportError as e:
    print(f"⚠️ Không thể import subtitle_config: {e}")
    HAS_SUBTITLE_CONFIG = False

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import sys
import glob
from pathlib import Path

OPTIMAL_CHROMA_REMOVAL = {
    "green": (0.2, 0.2),    # Green optimized từ testing
    "blue": (0.18, 0.18),    # Blue cần tolerance cao hơn
    "black": (0.01, 0.01),  # Black cần precision
    "white": (0.02, 0.02),   # White precision nhưng không khắt khe như black
    "cyan": (0.12, 0.12),    # Cyan dễ key
    "red": (0.25, 0.25),      # Red khó key nhất
    "magenta": (0.18, 0.18), # Tương tự blue
    "yellow": (0.22, 0.22)   # Khó vì conflict với skin tone
}
# Import main application
try:
    from main import AutoVideoEditor
except ImportError as e:
    print(f"❌ Lỗi import main application: {e}")
    sys.exit(1)

class VideoEditorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Ứng dụng Chỉnh sửa Video Tự động - Batch Processing + Chroma Key")
        self.root.geometry("900x850")
        self.root.resizable(True, True)
        
        # Variables - ĐỔI TỪ FILE SANG FOLDER VỚI DEFAULT PATHS
        self.input_folder_path = tk.StringVar(value="inputvideo")
        self.output_folder_path = tk.StringVar(value="output")
        self.source_language = tk.StringVar(value="vi")
        self.target_language = tk.StringVar(value="en")
        
        # THÊM OPTION CHO PHỤ ĐỀ
        self.enable_subtitle = tk.BooleanVar(value=True)
        
        self.video_folder_path = tk.StringVar(value="videooverlay")
        self.words_per_line = tk.IntVar(value=7)
        self.processing = False
        
        # ✅ SỬA: KHỞI TẠO SUBTITLE VARIABLES
        self.subtitle_preset = tk.StringVar(value="default")
        self.subtitle_text_color = tk.StringVar(value="black")
        self.subtitle_box_style = tk.StringVar(value="box")
        self.subtitle_box_color = tk.StringVar(value="white")
        self.subtitle_font_size = tk.IntVar(value=10)
        self.subtitle_position = tk.StringVar(value="bottom_center")
        self.custom_margin_v = tk.IntVar(value=50)
        self.custom_margin_l = tk.IntVar(value=0)
        self.custom_margin_r = tk.IntVar(value=0)
        
        # ✅ SỬA: Khởi tạo SubtitleConfig
        if HAS_SUBTITLE_CONFIG:
            self.subtitle_config = SubtitleConfig()
        else:
            self.subtitle_config = None
        
        # ✅ SỬA: BIND EVENTS CHO SUBTITLE VARIABLES
        self.subtitle_preset.trace_add("write", self._on_subtitle_change)
        self.subtitle_text_color.trace_add("write", self._on_subtitle_change)
        self.subtitle_box_style.trace_add("write", self._on_subtitle_change)
        self.subtitle_box_color.trace_add("write", self._on_subtitle_change)
        self.subtitle_font_size.trace_add("write", self._on_subtitle_change)
        self.source_language.trace_add("write", self._on_subtitle_change)
        self.target_language.trace_add("write", self._on_subtitle_change)
        
        # Overlay settings (giữ nguyên code cũ)
        self.overlay_times = {}
        self.animation_config = {}
        self.video_overlay_settings = {
            'enabled': True,
            'chroma_color': 'green',
            'chroma_similarity': 0.2,
            'chroma_blend': 0.2,
            'position_mode': 'custom',
            'position': 'custom',
            'custom_x': 300,
            'custom_y': 1200,
            'size_mode': 'percentage',
            'size_percent': 50,
            'start_time': 5,
            'duration': 15,
            'auto_hide': True
        }
        
        self.setup_ui()

    def _on_subtitle_change(self, *args):
        """Callback khi có thay đổi subtitle settings"""
        try:
            print(f"🔄 Subtitle setting changed")
            print(f"  text_color: {self.subtitle_text_color.get()}")
            print(f"  box_style: {self.subtitle_box_style.get()}")
            print(f"  box_color: {self.subtitle_box_color.get()}")
            print(f"  font_size: {self.subtitle_font_size.get()}")
            
            self.update_subtitle_preview()
            
        except Exception as e:
            print(f"❌ Error in subtitle change callback: {e}")

    def open_image_processor(self):
        """Mở Image Processing Tool trong cửa sổ riêng"""
        try:
            if not HAS_IMAGE_MODULE:
                messagebox.showerror("Lỗi", "Module Image Processing không khả dụng!\nVui lòng đảm bảo file gui_img.py tồn tại.")
                return
            
            # Tạo cửa sổ mới cho Image Processing
            image_window = tk.Toplevel(self.root)
            image_window.title("🖼️ Image Processing Tool")
            image_window.geometry("1000x700")
            
            # Khởi tạo ImageInserterApp trong cửa sổ mới
            image_app = ImageInserterApp(image_window)
            
            # Log message
            self.log_message("🖼️ Đã mở Image Processing Tool trong cửa sổ riêng")
            
            # Focus vào cửa sổ mới
            image_window.focus_set()
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể mở Image Processing Tool: {str(e)}")
            self.log_message(f"❌ Lỗi mở Image Processing: {str(e)}")  

    def open_subtitle_advanced_config(self):
        """Dialog cấu hình nâng cao với preview canvas hoạt động - ĐÃ SỬA KÍCH THƯỚC"""
        
        dialog = tk.Toplevel(self.root)
        dialog.title("🎨 Cấu hình Phụ đề Chi tiết")
        dialog.geometry("750x650")  # ✅ SỬA: Kích thước lớn hơn
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(main_frame, text="🎨 Cấu hình Kiểu dáng Phụ đề", 
                font=("Arial", 16, "bold")).pack(pady=(0, 20))
        
        # ✅ SỬA: Local variables cho dialog
        dialog_text_color = tk.StringVar(value=self.subtitle_text_color.get())
        dialog_box_style = tk.StringVar(value=self.subtitle_box_style.get())
        dialog_box_color = tk.StringVar(value=self.subtitle_box_color.get())
        dialog_font_size = tk.IntVar(value=self.subtitle_font_size.get())
        
        # Controls
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Text color
        text_frame = ttk.Frame(controls_frame)
        text_frame.pack(fill=tk.X, pady=5)
        ttk.Label(text_frame, text="Màu chữ:", width=15).pack(side=tk.LEFT)
        text_color_combo = ttk.Combobox(
            text_frame,
            textvariable=dialog_text_color,
            values=["black", "white", "red", "green", "blue", "yellow", "cyan", "magenta", "orange", "purple", "pink"],
            state="readonly",
            width=15
        )
        text_color_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # Box style
        box_frame = ttk.Frame(controls_frame)
        box_frame.pack(fill=tk.X, pady=5)
        ttk.Label(box_frame, text="Kiểu nền:", width=15).pack(side=tk.LEFT)
        box_style_combo = ttk.Combobox(
            box_frame,
            textvariable=dialog_box_style,
            values=["none", "outline", "box", "rounded_box", "shadow_box"],
            state="readonly",
            width=15
        )
        box_style_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # Box color
        box_color_frame = ttk.Frame(controls_frame)
        box_color_frame.pack(fill=tk.X, pady=5)
        ttk.Label(box_color_frame, text="Màu nền:", width=15).pack(side=tk.LEFT)
        box_color_combo = ttk.Combobox(
            box_color_frame,
            textvariable=dialog_box_color,
            values=["black", "white", "red", "green", "blue", "yellow", "cyan", "magenta", "orange", "purple", "pink"],
            state="readonly",
            width=15
        )
        box_color_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # Font size
        font_frame = ttk.Frame(controls_frame)
        font_frame.pack(fill=tk.X, pady=5)
        ttk.Label(font_frame, text="Cỡ chữ:", width=15).pack(side=tk.LEFT)
        font_size_spinbox = ttk.Spinbox(
            font_frame,
            from_=6, to=24, increment=1,
            textvariable=dialog_font_size,
            width=8
        )
        font_size_spinbox.pack(side=tk.LEFT, padx=(10, 0))
        
        # ✅ SỬA: Preview canvas HOẠT ĐỘNG THỰC SỰ
        preview_frame = ttk.LabelFrame(main_frame, text="🔍 Xem trước", padding="15")
        preview_frame.pack(fill=tk.X, pady=(0, 20))
        
        preview_canvas = tk.Canvas(preview_frame, width=600, height=100, bg="gray30")
        preview_canvas.pack(pady=10)
        
        # Canvas elements
        text_id = preview_canvas.create_text(
            300, 50,
            text="Đây là mẫu phụ đề",
            fill="black",
            font=("Arial", 12),
            anchor="center"
        )
        
        bg_id = preview_canvas.create_rectangle(
            0, 0, 0, 0,
            fill="white",
            outline="",
            state="hidden"
        )
        
        preview_canvas.tag_lower(bg_id, text_id)
        
        # ✅ SỬA: Preview update function HOẠT ĐỘNG
        def update_canvas_preview(*args):
            try:
                text_color = dialog_text_color.get()
                box_style = dialog_box_style.get()
                box_color = dialog_box_color.get()
                font_size = dialog_font_size.get()
                
                print(f"🔍 Canvas preview: {text_color} text, {box_style} {box_color} bg, font {font_size}")
                
                # Color mapping for canvas
                color_map = {
                    "black": "black", "white": "white", "red": "red",
                    "green": "green", "blue": "blue", "yellow": "yellow",
                    "cyan": "cyan", "magenta": "magenta", "orange": "orange",
                    "purple": "purple", "pink": "pink"
                }
                
                canvas_text_color = color_map.get(text_color, "black")
                canvas_box_color = color_map.get(box_color, "white")
                
                # Update text
                preview_canvas.itemconfig(text_id,
                                        fill=canvas_text_color,
                                        font=("Arial", max(8, min(20, font_size))))
                
                # Update background
                if box_style in ["box", "rounded_box", "shadow_box"]:
                    bbox = preview_canvas.bbox(text_id)
                    if bbox:
                        padding = 15
                        x1, y1, x2, y2 = bbox
                        x1 -= padding
                        y1 -= padding
                        x2 += padding
                        y2 += padding
                        
                        preview_canvas.coords(bg_id, x1, y1, x2, y2)
                        preview_canvas.itemconfig(bg_id,
                                                fill=canvas_box_color,
                                                state="normal")
                        
                        print(f"✅ Canvas updated: {canvas_text_color} text on {canvas_box_color} background")
                else:
                    preview_canvas.itemconfig(bg_id, state="hidden")
                    print(f"✅ Canvas updated: {canvas_text_color} text, no background")
                    
            except Exception as e:
                print(f"❌ Canvas preview error: {e}")
        
        # ✅ QUAN TRỌNG: BIND TẤT CẢ EVENTS
        dialog_text_color.trace_add("write", update_canvas_preview)
        dialog_box_style.trace_add("write", update_canvas_preview)
        dialog_box_color.trace_add("write", update_canvas_preview)
        dialog_font_size.trace_add("write", update_canvas_preview)
        
        text_color_combo.bind("<<ComboboxSelected>>", update_canvas_preview)
        box_style_combo.bind("<<ComboboxSelected>>", update_canvas_preview)
        box_color_combo.bind("<<ComboboxSelected>>", update_canvas_preview)
        
        font_size_spinbox.bind("<KeyRelease>", update_canvas_preview)
        font_size_spinbox.bind("<<Increment>>", update_canvas_preview)
        font_size_spinbox.bind("<<Decrement>>", update_canvas_preview)
        
        # Initial preview
        update_canvas_preview()
        
        # ✅ SỬA: Buttons cố định ở cuối dialog
        button_frame = ttk.Frame(dialog)  # ✅ SỬA: Gắn vào dialog, không phải main_frame
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=15, padx=20)
        
        def apply_settings():
            try:
                # Copy values về main GUI
                self.subtitle_text_color.set(dialog_text_color.get())
                self.subtitle_box_style.set(dialog_box_style.get())
                self.subtitle_box_color.set(dialog_box_color.get())
                self.subtitle_font_size.set(dialog_font_size.get())
                self.subtitle_preset.set("custom")  # Mark as custom
                
                print(f"✅ Applied: {dialog_text_color.get()} text, {dialog_box_style.get()} {dialog_box_color.get()} bg")
                
                # Update main preview
                self.update_subtitle_preview()
                
                dialog.destroy()
                
            except Exception as e:
                print(f"❌ Apply error: {e}")
                dialog.destroy()
        
        ttk.Button(button_frame, text="✓ Áp dụng", command=apply_settings).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="❌ Hủy", command=dialog.destroy).pack(side=tk.RIGHT)  

    def update_words_recommendation(self, *args):
        """Cập nhật words per line theo NGÔN NGỮ ĐÍCH (target_language)"""
        try:
            # ✅ SỬA: Dùng target_language thay vì source_language
            target_lang = self.target_language.get()  # Thay đổi từ source_language
            
            if HAS_SUBTITLE_CONFIG and hasattr(self, 'subtitle_config'):
                # ✅ SỬA: Lấy config cho ngôn ngữ đích
                lang_config = self.subtitle_config.get_language_config(target_lang)
                recommended = lang_config['words_per_line']
                
                # Auto-apply giá trị khuyến nghị
                self.words_per_line.set(recommended)
                
                # ✅ SỬA: Đơn vị dựa trên ngôn ngữ đích
                if target_lang.startswith(('zh', 'ja', 'ko')):
                    unit = "ký tự"
                else:
                    unit = "từ"
                    
                self.words_recommended_label.config(
                    text=f"(auto: {recommended} {unit} cho {target_lang.upper()})"
                )
                
                print(f"🔄 Updated words_per_line: {recommended} {unit} for target language: {target_lang}")
                
            else:
                self.words_recommended_label.config(text="(4-15)")
                
        except Exception as e:
            print(f"❌ Error updating words recommendation: {e}")
            self.words_recommended_label.config(text="(4-15)")

    def update_subtitle_preview(self, *args):
        """Cập nhật preview với words per line info"""
        try:
            if not hasattr(self, 'subtitle_preview_label') or not self.subtitle_preview_label:
                return
            
            current_lang = self.source_language.get()
            preset = self.subtitle_preset.get()
            text_color = self.subtitle_text_color.get()
            box_style = self.subtitle_box_style.get()
            box_color = self.subtitle_box_color.get()
            font_size = self.subtitle_font_size.get()
            words_per_line = self.words_per_line.get()  # ✅ THÊM: Actual value
            
            # ✅ THÊM: Get recommended value
            if HAS_SUBTITLE_CONFIG and hasattr(self, 'subtitle_config'):
                lang_config = self.subtitle_config.get_language_config(current_lang)
                recommended = lang_config['words_per_line']
                unit = "ký tự" if current_lang.startswith(('zh', 'ja', 'ko')) else "từ"
                
                words_info = f"{words_per_line} {unit}"
                if words_per_line != recommended:
                    words_info += f" (khuyến nghị: {recommended})"
            else:
                words_info = f"{words_per_line} từ"
            
            # Tạo preview text với words per line info
            if preset and preset != "custom":
                text = f"👉 {preset.title()}: {text_color} text, {box_style} {box_color} bg, {current_lang.upper()}→{self.target_language.get().upper()}, font {font_size}, {words_info}"
            else:
                text = f"👉 Tùy chỉnh: {text_color} text, {box_style} {box_color} bg, {current_lang.upper()}→{self.target_language.get().upper()}, font {font_size}, {words_info}"
            
            self.subtitle_preview_label.config(text=text)
            print(f"🔍 Preview updated with words info: {text}")
            
        except Exception as e:
            print(f"❌ Error updating preview: {e}")
            try:
                self.subtitle_preview_label.config(text="👉 Cấu hình phụ đề")
            except:
                pass

    def setup_ui(self):
        """Thiết lập giao diện người dùng - ĐÃ SỬA GỘP NGÔN NGỮ + SUBTITLE"""
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(
            main_frame, 
            text="🎬 Ứng dụng Batch Processing Video với Video Overlay",
            font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        row = 1
        
        # Input folder selection
        ttk.Label(main_frame, text="📁 Thư mục video đầu vào:").grid(row=row, column=0, sticky=tk.W, pady=5)
        input_entry = ttk.Entry(main_frame, textvariable=self.input_folder_path)
        input_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=5)
        ttk.Button(main_frame, text="Chọn thư mục", command=self.select_input_folder).grid(row=row, column=2, padx=(5, 0), pady=5)
        row += 1
        
        # Output folder selection
        ttk.Label(main_frame, text="💾 Thư mục đầu ra:").grid(row=row, column=0, sticky=tk.W, pady=5)
        output_entry = ttk.Entry(main_frame, textvariable=self.output_folder_path)
        output_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=5)
        ttk.Button(main_frame, text="Chọn thư mục", command=self.select_output_folder).grid(row=row, column=2, padx=(5, 0), pady=5)
        row += 1
        
        # ✅ GỘP: Ngôn ngữ + Phụ đề trong một khung (THAY THẾ phần cũ)
        subtitle_config_frame = ttk.LabelFrame(main_frame, text="🎨 Cấu hình Phụ đề & Ngôn ngữ", padding="10")
        subtitle_config_frame.grid(row=row, column=0, columnspan=3, pady=(10, 10), sticky=(tk.W, tk.E))
        subtitle_config_frame.columnconfigure(1, weight=1)
        
        # Dòng 1: Checkbox + Ngôn ngữ gốc + Ngôn ngữ đích + Từ/dòng
        lang_frame = ttk.Frame(subtitle_config_frame)
        lang_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Checkbutton(
            lang_frame, 
            text="📝 Tạo phụ đề", 
            variable=self.enable_subtitle
        ).pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(lang_frame, text="🌐 Ngôn ngữ gốc:").pack(side=tk.LEFT)
        language_combo = ttk.Combobox(
            lang_frame, 
            textvariable=self.source_language,
            values=["vi", "en", "zh", "zh-cn", "zh-tw", "ja", "ko", "es", "fr", "de"],
            state="readonly",
            width=10
        )
        language_combo.pack(side=tk.LEFT, padx=(10, 20))
        
        ttk.Label(lang_frame, text="🎯 Ngôn ngữ đích:").pack(side=tk.LEFT)
        target_language_combo = ttk.Combobox(
            lang_frame, 
            textvariable=self.target_language,
            values=["en", "vi", "zh", "zh-cn", "zh-tw", "ja", "ko", "es", "fr", "de"],
            state="readonly",
            width=10
        )
        target_language_combo.pack(side=tk.LEFT, padx=(10, 20))
        
        ttk.Label(lang_frame, text="📝 Từ/dòng:").pack(side=tk.LEFT, padx=(20, 5))

        # Frame cho words per line
        words_frame = ttk.Frame(lang_frame)
        words_frame.pack(side=tk.LEFT)

        # Spinbox cho manual override
        words_spinbox = ttk.Spinbox(
            words_frame,
            from_=4, to=15,  # Tăng range để cover tiếng Trung
            textvariable=self.words_per_line,
            width=5,
            state="normal"  # Cho phép edit
        )
        words_spinbox.pack(side=tk.LEFT)

        # Label hiển thị giá trị recommended
        self.words_recommended_label = ttk.Label(
            words_frame, 
            text="(4-15)", 
            font=("Arial", 8), 
            foreground="gray"
        )
        self.words_recommended_label.pack(side=tk.LEFT, padx=(5, 0))

        # Bind sự kiện - GỌI METHOD CỦA CLASS
        
        self.target_language.trace_add("write", self.update_words_recommendation)

        # Initial update - GỌI METHOD CỦA CLASS
        self.update_words_recommendation()
        
        # Dòng 2: Kiểu phụ đề + Nút cấu hình (BỎ phần vị trí)
        style_frame = ttk.Frame(subtitle_config_frame)
        style_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Label(style_frame, text="🎨 Kiểu phụ đề:").pack(side=tk.LEFT)
        preset_combo = ttk.Combobox(
            style_frame,
            textvariable=self.subtitle_preset,
            values=["default", "custom"],
            state="readonly",
            width=12
        )
        preset_combo.pack(side=tk.LEFT, padx=(10, 20))
        
        ttk.Button(style_frame, text="⚙️ Cấu hình Chi tiết", 
                command=self.open_subtitle_advanced_config).pack(side=tk.RIGHT)
        
        # Dòng 3: Preview (SỬA lỗi)
        try:
            self.subtitle_preview_label = ttk.Label(
                subtitle_config_frame, 
                text="👉 Mặc định: Chữ đen, nền trắng, dưới giữa, auto-adjust theo ngôn ngữ"
            )
            self.subtitle_preview_label.grid(row=2, column=0, columnspan=3, pady=5, sticky=tk.W)
            
        except Exception as e:
            print(f"Lỗi tạo preview label: {e}")
            # Fallback
            self.subtitle_preview_label = ttk.Label(
                subtitle_config_frame, 
                text="👉 Mặc định"
            )
            self.subtitle_preview_label.grid(row=2, column=0, columnspan=3, pady=5, sticky=tk.W)
        
        
        # Bind events để update preview khi thay đổi
        def update_preview_wrapper(*args):
            try:
                self.update_subtitle_preview()
            except Exception as e:
                print(f"Lỗi update preview: {e}")

        # Bind cho sự kiện chọn
        preset_combo.bind("<<ComboboxSelected>>", update_preview_wrapper)
        language_combo.bind("<<ComboboxSelected>>", update_preview_wrapper)
        target_language_combo.bind("<<ComboboxSelected>>", update_preview_wrapper)

        # Bind trace cho các StringVar để update realtime
        self.subtitle_preset.trace_add("write", update_preview_wrapper)
        self.source_language.trace_add("write", update_preview_wrapper)
        self.target_language.trace_add("write", update_preview_wrapper)


        row += 1
        
        # Video overlay folder selection
        ttk.Label(main_frame, text="🎭 Thư mục video overlay:").grid(row=row, column=0, sticky=tk.W, pady=5)
        video_entry = ttk.Entry(main_frame, textvariable=self.video_folder_path)
        video_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=5)
        ttk.Button(main_frame, text="Chọn thư mục", command=self.select_video_folder).grid(row=row, column=2, padx=(5, 0), pady=5)
        row += 1
        
        # Video overlay configuration
        overlay_frame = ttk.Frame(main_frame)
        overlay_frame.grid(row=row, column=0, columnspan=3, pady=(10, 10), sticky=(tk.W, tk.E))
        
        ttk.Button(overlay_frame, text="🎬 Cấu hình Video Overlay + Chroma Key", command=self.configure_video_overlay).pack(side=tk.LEFT, padx=(0, 10))
        row += 1
        
        # Status label
        self.video_overlay_status = ttk.Label(main_frame, text="✅ Sẵn sàng: Green chroma key (0.20, 0.20) | x=300, y=1200 | 50%", foreground="green")
        self.video_overlay_status.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=2)
        row += 1
        
        # ✅ THÊM: Image Processing button màu sắc nổi bật
        image_frame = ttk.Frame(main_frame)
        image_frame.grid(row=row, column=0, columnspan=3, pady=(15, 10), sticky=(tk.W, tk.E))
        
        if HAS_IMAGE_MODULE:
            # Tạo style cho nút đặc biệt
            try:
                style = ttk.Style()
                style.configure("ImageTool.TButton", 
                              foreground="blue", 
                              font=("Arial", 11, "bold"))
                
                image_button = ttk.Button(
                    image_frame, 
                    text="🖼️ Mở Image Processing Tool", 
                    command=self.open_image_processor,
                    style="ImageTool.TButton"
                )
                image_button.pack(side=tk.LEFT, padx=(0, 15), ipady=8)
                
                # Label mô tả với màu sắc
                desc_label = ttk.Label(
                    image_frame, 
                    text="✨ Chèn logo/watermark vào ảnh hàng loạt ✨", 
                    font=("Arial", 10, "italic"),
                    foreground="orange"
                )
                desc_label.pack(side=tk.LEFT, padx=(10, 0))
                
                # Thêm icon decorator
                decorator_frame = ttk.Frame(image_frame)
                decorator_frame.pack(side=tk.RIGHT, padx=(10, 0))
                
                ttk.Label(decorator_frame, text="🎨", font=("Arial", 16)).pack(side=tk.LEFT, padx=2)
                ttk.Label(decorator_frame, text="📸", font=("Arial", 16)).pack(side=tk.LEFT, padx=2)
                ttk.Label(decorator_frame, text="✂️", font=("Arial", 16)).pack(side=tk.LEFT, padx=2)
                
            except Exception as e:
                print(f"Lỗi tạo image button: {e}")
                # Fallback button đơn giản
                ttk.Button(
                    image_frame, 
                    text="🖼️ Mở Image Processing Tool", 
                    command=self.open_image_processor
                ).pack(side=tk.LEFT)
                
        else:
            error_label = ttk.Label(
                image_frame, 
                text="⚠️ Image Processing không khả dụng (thiếu module gui_img)", 
                foreground="red",
                font=("Arial", 10, "bold")
            )
            error_label.pack(side=tk.LEFT)
        
        row += 1
        
        # Process button
        self.process_button = ttk.Button(
            main_frame,
            text="🚀 Bắt đầu xử lý hàng loạt (Phụ đề + Video Overlay + 9:16)",
            command=self.start_processing,
            style="Accent.TButton"
        )
        self.process_button.grid(row=row, column=0, columnspan=3, pady=(20, 10))
        row += 1
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            main_frame,
            variable=self.progress_var,
            mode='indeterminate'
        )
        self.progress_bar.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        row += 1
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Sẵn sàng xử lý hàng loạt")
        self.status_label.grid(row=row, column=0, columnspan=3, pady=(0, 10))
        row += 1
        
        # Log output
        ttk.Label(main_frame, text="📋 Nhật ký xử lý:").grid(row=row, column=0, sticky=tk.W, pady=(10, 5))
        row += 1
        
        self.log_text = scrolledtext.ScrolledText(
            main_frame,
            height=15,
            width=80,
            wrap=tk.WORD
        )
        self.log_text.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Configure row weight for log text
        main_frame.rowconfigure(row, weight=1)
        
        # Initial log
        self.log_message("🎬 GUI Batch Video Processing đã sẵn sàng!")
        self.log_message("💡 Đã hỗ trợ tiếng Trung Quốc (zh, zh-cn, zh-tw)")
        self.log_message("🎨 Đã gộp cấu hình ngôn ngữ + phụ đề vào một chỗ")
        self.log_message("🖼️ Thêm Image Processing Tool riêng biệt")
        self.log_message("📁 Hướng dẫn: Chọn thư mục input, output, sau đó bắt đầu xử lý")

    def _create_subtitle_style_section(self, parent, row):
        """Tạo phần cấu hình kiểu phụ đề - ĐÃ ĐƠN GIẢN HÓA"""
        subtitle_frame = ttk.LabelFrame(parent, text="🎨 Kiểu phụ đề", padding="10")
        subtitle_frame.grid(row=row, column=0, columnspan=3, pady=(10, 5), sticky=(tk.W, tk.E))
        
        # Preset selector - CHỈ CÒN 2 LỰA CHỌN
        preset_frame = ttk.Frame(subtitle_frame)
        preset_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(preset_frame, text="🎨 Kiểu phụ đề:").pack(side=tk.LEFT)
        preset_combo = ttk.Combobox(
            preset_frame,
            textvariable=self.subtitle_preset,
            values=["default"],  # ĐÃ BỎ: tất cả preset khác
            state="readonly",
            width=12
        )
        preset_combo.pack(side=tk.LEFT, padx=(10, 20))
        
        # Mô tả kiểu - CẬP NHẬT
        self.style_preview_label = ttk.Label(preset_frame, text="👉 Mặc định: Chữ đen, nền trắng, cỡ 10")  # ĐÃ CẬP NHẬT
        self.style_preview_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Custom style button
        ttk.Button(preset_frame, text="⚙️ Tùy chỉnh nâng cao", 
                command=self.configure_subtitle_style).pack(side=tk.RIGHT)
        
        # Update preview when preset changes - ĐƠN GIẢN HÓA
        def update_style_preview(*args):
            preset = self.subtitle_preset.get()
            if preset == "default":
                self.style_preview_label.config(text="👉 Mặc định: Chữ đen, nền trắng, cỡ 10")
            else:
                self.style_preview_label.config(text="👉 Tùy chỉnh")
                
        self.subtitle_preset.trace_add("write", update_style_preview)
        update_style_preview()

    def configure_subtitle_style(self):
        """Hiển thị dialog cấu hình kiểu phụ đề tùy chỉnh - ĐÃ SỬA UI VÀ PREVIEW"""
        dialog = tk.Toplevel(self.root)
        dialog.title("🎨 Tùy chỉnh kiểu phụ đề")
        dialog.geometry("750x500")  # Tăng kích thước
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
            command=apply_style
        )
        apply_button.pack(side=tk.LEFT, padx=(0, 10))

        cancel_button = ttk.Button(
            button_frame,
            text="❌ Hủy",
            command=dialog.destroy
        )
        cancel_button.pack(side=tk.RIGHT)

    def get_subtitle_style(self):
        """Lấy cấu hình subtitle để truyền cho video processor - ĐÃ SỬA ĐÚNG"""
        
        print(f"\n🔍 ==> GET_SUBTITLE_STYLE DEBUG <==")
        
        # Lấy values hiện tại từ GUI
        text_color = self.subtitle_text_color.get()
        box_style = self.subtitle_box_style.get()  
        box_color = self.subtitle_box_color.get()
        font_size = self.subtitle_font_size.get()
        preset = self.subtitle_preset.get()
        
        print(f"📋 GUI Values:")
        print(f"  text_color: {text_color}")
        print(f"  box_style: {box_style}")
        print(f"  box_color: {box_color}")
        print(f"  font_size: {font_size}")
        print(f"  preset: {preset}")
        
        # Kiểm tra xem có sử dụng preset không
        if preset and preset != "custom":
            print(f"✅ Using preset: {preset}")
            result = {
                "preset": preset,
                "use_preset": True
            }
        else:
            print(f"✅ Using custom settings")
            result = {
                "text_color": text_color,
                "box_style": box_style,
                "box_color": box_color,
                "font_size": font_size,
                "margin_v": getattr(self, 'custom_margin_v', tk.IntVar(value=50)).get(),
                "use_preset": False
            }
        
        print(f"📤 Returning to video processor: {result}")
        return result

    
    def force_update_subtitle_config(self):
        """Force update subtitle config từ GUI - Debug helper"""
        if HAS_SUBTITLE_CONFIG and hasattr(self, 'subtitle_config'):
            print("🔄 Force updating subtitle config from GUI...")
            
            # Clear current config
            self.subtitle_config = SubtitleConfig()
            
            # Apply values từ GUI
            self.subtitle_config.text_color = self.subtitle_text_color.get()
            self.subtitle_config.box_style = self.subtitle_box_style.get()  
            self.subtitle_config.box_color = self.subtitle_box_color.get()
            self.subtitle_config.font_size = self.subtitle_font_size.get()
            
            print(f"✅ Updated config: color={self.subtitle_config.text_color}, style={self.subtitle_config.box_style}")
            
            # Update preview
            self.update_subtitle_preview()

    def select_input_folder(self):
        """Chọn thư mục video đầu vào - MỚI"""
        folder_path = filedialog.askdirectory(
            title="Chọn thư mục chứa video đầu vào"
        )
        if folder_path:
            self.input_folder_path.set(folder_path)
            
            # Kiểm tra và hiển thị file video
            video_files = []
            for ext in ['*.mp4', '*.avi', '*.mov', '*.mkv', '*.wmv', '*.flv']:
                video_files.extend(glob.glob(os.path.join(folder_path, ext)))
            
            if video_files:
                self.log_message(f" Đã chọn thư mục input: {folder_path}")
                self.log_message(f" Tìm thấy {len(video_files)} video: {[os.path.basename(f) for f in video_files[:5]]}")
                if len(video_files) > 5:
                    self.log_message(f"   ... và {len(video_files) - 5} video khác")
            else:
                self.log_message(" Không tìm thấy video nào trong thư mục")

    def select_output_folder(self):
        """Chọn thư mục đầu ra - MỚI"""
        folder_path = filedialog.askdirectory(
            title="Chọn thư mục lưu video đã xử lý"
        )
        if folder_path:
            self.output_folder_path.set(folder_path)
            self.log_message(f"💾 Đã chọn thư mục output: {folder_path}")

    def select_input_video(self):
        """Chọn file video đầu vào"""
        file_path = filedialog.askopenfilename(
            title="Chọn file video đầu vào",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.input_video_path.set(file_path)
            # Tự động đặt tên file đầu ra
            input_path = Path(file_path)
            output_name = f"{input_path.stem}_with_overlay{input_path.suffix}"
            output_path = input_path.parent / output_name
            self.output_video_path.set(str(output_path))
            self.log_message(f"📁 Đã chọn video: {os.path.basename(file_path)}")
    
    def select_output_video(self):
        """Chọn vị trí lưu video đầu ra"""
        file_path = filedialog.asksaveasfilename(
            title="Lưu video đầu ra",
            defaultextension=".mp4",
            filetypes=[
                ("MP4 files", "*.mp4"),
                ("AVI files", "*.avi"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.output_video_path.set(file_path)
            self.log_message(f"💾 Đã chọn vị trí lưu: {os.path.basename(file_path)}")
    
    
    def select_video_folder(self):
        """Chọn thư mục chứa video overlay - ĐÃ SỬA STATUS Y=1200"""
        folder_path = filedialog.askdirectory(
            title="Chọn thư mục chứa video overlay",
            initialdir=self.video_folder_path.get() if self.video_folder_path.get() else "."
        )
        if folder_path:
            self.video_folder_path.set(folder_path)
            self.log_message(f"📁 Đã chọn thư mục video overlay: {folder_path}")
            
            # Kiểm tra file video trong thư mục
            video_files = []
            for ext in ['*.mp4', '*.avi', '*.mov', '*.mkv', '*.wmv']:
                video_files.extend(glob.glob(os.path.join(folder_path, ext)))
            
            if video_files:
                self.log_message(f"🎭 Tìm thấy {len(video_files)} file video: {[os.path.basename(f) for f in video_files[:3]]}")
                if len(video_files) > 3:
                    self.log_message(f"   ... và {len(video_files) - 3} file khác")
                
                # Cập nhật settings với file đầu tiên
                self.video_overlay_settings['video_path'] = video_files[0]
                self.video_overlay_settings['enabled'] = True
                
                # Cập nhật status hiển thị - ĐÃ SỬA Y=1200
                overlay_name = os.path.basename(video_files[0])
                self.video_overlay_status.config(
                    text=f"✅ Sẵn sàng: {overlay_name} | Green chroma (0.2, 0.2) | X=300, Y=1200 | 50%", 
                    foreground="green"
                )
            else:
                self.log_message("⚠️ Không tìm thấy file video nào trong thư mục")
                self.video_overlay_settings['enabled'] = False
                self.video_overlay_status.config(
                    text="⚠️ Không có video overlay | Chỉ xử lý phụ đề + 9:16", 
                    foreground="orange"
                )
        else:
            # User cancel, disable overlay nhưng vẫn hiển thị settings mặc định
            self.video_overlay_settings['enabled'] = False
            self.video_overlay_status.config(
                text="ℹ️ Không chọn video overlay | Chỉ xử lý phụ đề + 9:16", 
                foreground="blue"
            )

    def configure_video_overlay(self):
        """Cấu hình video overlay với chroma key"""
        if not self.video_folder_path.get():
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn thư mục video overlay trước!")
            return
        
        # Tìm file video
        video_files = []
        folder_path = self.video_folder_path.get()
        
        for ext in ['*.mp4', '*.avi', '*.mov', '*.mkv', '*.wmv']:
            video_files.extend(glob.glob(os.path.join(folder_path, ext)))
        
        if not video_files:
            messagebox.showwarning("Cảnh báo", "Không tìm thấy file video nào trong thư mục!")
            return
        
        self.show_video_overlay_dialog(video_files)
    
    def show_video_overlay_dialog(self, video_files):
        """Dialog cấu hình video overlay với giao diện động - ĐÃ SỬA Y=1200"""
        
        dialog = tk.Toplevel(self.root)
        dialog.title("🎬 Cấu hình Video Overlay + Chroma Key")
        dialog.geometry("600x800")
        dialog.transient(self.root)
        dialog.grab_set()
        
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # --- Các biến control ---
        video_var = tk.StringVar()
        start_var = tk.StringVar(value="0")
        duration_var = tk.StringVar(value="10")
        
        # Position settings - ĐÃ SỬA Y=1200
        position_mode_var = tk.StringVar(value="preset")
        position_preset_var = tk.StringVar(value="center")
        custom_x_var = tk.StringVar(value="300")
        custom_y_var = tk.StringVar(value="1200")  # ĐÃ SỬA: từ 1600 thành 1200
        
        # Size settings
        size_mode_var = tk.StringVar(value="percentage")
        size_percent_var = tk.StringVar(value="25")
        custom_width_var = tk.StringVar(value="500")
        custom_height_var = tk.StringVar(value="600")
        
        # Chroma settings
        chroma_enabled_var = tk.BooleanVar(value=True)
        chroma_color_var = tk.StringVar(value="black")
        advanced_mode_var = tk.BooleanVar(value=False)
        auto_hide_var = tk.BooleanVar(value=True)
        
        # Advanced controls
        custom_similarity_var = tk.StringVar(value="0.010")
        custom_blend_var = tk.StringVar(value="0.005")

        # --- Load saved settings ---
        if self.video_overlay_settings.get('enabled', False):
            prev = self.video_overlay_settings
            if prev.get('video_path'):
                video_basename = os.path.basename(prev['video_path'])
                all_basenames = [os.path.basename(f) for f in video_files]
                if video_basename in all_basenames:
                    video_var.set(video_basename)
            if prev.get('start_time') is not None:
                start_var.set(str(prev['start_time']))
            if prev.get('duration') is not None:
                duration_var.set(str(prev['duration']))
            
            # Load settings
            if prev.get('position_mode'):
                position_mode_var.set(prev['position_mode'])
            if prev.get('position'):
                position_preset_var.set(prev['position'])
            if prev.get('custom_x') is not None:
                custom_x_var.set(str(prev['custom_x']))
            if prev.get('custom_y') is not None:
                custom_y_var.set(str(prev['custom_y']))
            else:
                custom_y_var.set("1200")  # Default nếu không có
                
            if prev.get('size_mode'):
                size_mode_var.set(prev['size_mode'])
            if prev.get('size_percent') is not None:
                size_percent_var.set(str(prev['size_percent']))
            if prev.get('custom_width') is not None:
                custom_width_var.set(str(prev['custom_width']))
            if prev.get('custom_height') is not None:
                custom_height_var.set(str(prev['custom_height']))
            if prev.get('chroma_key') is not None:
                chroma_enabled_var.set(prev['chroma_key'])
            if prev.get('chroma_color'):
                chroma_color_var.set(prev['chroma_color'])
            if prev.get('auto_hide') is not None:
                auto_hide_var.set(prev['auto_hide'])

        # --- Video selection ---
        ttk.Label(main_frame, text="Chọn video overlay:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        video_combo = ttk.Combobox(main_frame, textvariable=video_var, 
                                values=[os.path.basename(f) for f in video_files], 
                                state="readonly")
        video_combo.pack(fill=tk.X, pady=(0, 10))
        if video_var.get() == "" and video_files:
            video_combo.current(0)

        # --- Timing section ---
        timing_frame = ttk.LabelFrame(main_frame, text="⏰ Thời gian", padding="10")
        timing_frame.pack(fill=tk.X, pady=(0, 10))
        
        start_frame = ttk.Frame(timing_frame)
        start_frame.pack(fill=tk.X, pady=2)
        ttk.Label(start_frame, text="Bắt đầu (giây):").pack(side=tk.LEFT)
        ttk.Entry(start_frame, textvariable=start_var, width=10).pack(side=tk.LEFT, padx=(10, 0))
        
        duration_frame = ttk.Frame(timing_frame)
        duration_frame.pack(fill=tk.X, pady=2)
        ttk.Label(duration_frame, text="Thời lượng tối đa (giây):").pack(side=tk.LEFT)
        ttk.Entry(duration_frame, textvariable=duration_var, width=10).pack(side=tk.LEFT, padx=(10, 0))
        
        auto_hide_frame = ttk.Frame(timing_frame)
        auto_hide_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Checkbutton(auto_hide_frame, 
                    text="Tự động ẩn khi video overlay chạy hết", 
                    variable=auto_hide_var).pack(anchor=tk.W)

        # --- Position section with dynamic controls ---
        position_frame = ttk.LabelFrame(main_frame, text="📍 Vị trí", padding="10")
        position_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Position mode selection
        mode_frame = ttk.Frame(position_frame)
        mode_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Radiobutton(mode_frame, text="Tùy chỉnh X,Y", variable=position_mode_var, 
                    value="custom").pack(side=tk.LEFT, padx=(0, 20))
        ttk.Radiobutton(mode_frame, text="Vị trí mặc định", variable=position_mode_var, 
                    value="preset").pack(side=tk.LEFT)
        
        # Container for dynamic position controls
        position_controls_frame = ttk.Frame(position_frame)
        position_controls_frame.pack(fill=tk.X, pady=5)
        
        # Custom position frame - ĐÃ SỬA TOOLTIP Y=1200
        custom_pos_frame = ttk.Frame(position_controls_frame)
        ttk.Label(custom_pos_frame, text="X:").pack(side=tk.LEFT)
        ttk.Entry(custom_pos_frame, textvariable=custom_x_var, width=8).pack(side=tk.LEFT, padx=(5, 15))
        ttk.Label(custom_pos_frame, text="Y:").pack(side=tk.LEFT)
        ttk.Entry(custom_pos_frame, textvariable=custom_y_var, width=8).pack(side=tk.LEFT, padx=(5, 15))
        ttk.Label(custom_pos_frame, text="(mặc định: X=300, Y=1200)", 
                font=("Arial", 8), foreground="gray").pack(side=tk.LEFT)  # ĐÃ SỬA: Y=1200
        
        # Preset positions frame
        preset_frame = ttk.Frame(position_controls_frame)
        ttk.Label(preset_frame, text="Vị trí:").pack(side=tk.LEFT)
        position_combo = ttk.Combobox(preset_frame, textvariable=position_preset_var, 
                                    values=["center", "top-left", "top-right", "bottom-left", "bottom-right"], 
                                    state="readonly", width=15)
        position_combo.pack(side=tk.LEFT, padx=(10, 0))

        # --- Size section with dynamic controls ---
        size_frame = ttk.LabelFrame(main_frame, text="📏 Kích thước", padding="10")
        size_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Size mode selection
        size_mode_frame = ttk.Frame(size_frame)
        size_mode_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Radiobutton(size_mode_frame, text="Theo phần trăm", variable=size_mode_var, 
                    value="percentage").pack(side=tk.LEFT, padx=(0, 20))
        ttk.Radiobutton(size_mode_frame, text="Tùy chỉnh W,H", variable=size_mode_var, 
                    value="custom").pack(side=tk.LEFT)
        
        # Container for dynamic size controls
        size_controls_frame = ttk.Frame(size_frame)
        size_controls_frame.pack(fill=tk.X, pady=5)
        
        # Percentage size frame
        percent_frame = ttk.Frame(size_controls_frame)
        ttk.Label(percent_frame, text="Phần trăm (% chiều cao):").pack(side=tk.LEFT)
        ttk.Entry(percent_frame, textvariable=size_percent_var, width=8).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Label(percent_frame, text="(mặc định: 50%)", 
                font=("Arial", 8), foreground="gray").pack(side=tk.LEFT, padx=(5, 0))
        
        # Custom size frame
        custom_size_frame = ttk.Frame(size_controls_frame)
        ttk.Label(custom_size_frame, text="Width:").pack(side=tk.LEFT)
        ttk.Entry(custom_size_frame, textvariable=custom_width_var, width=8).pack(side=tk.LEFT, padx=(5, 15))
        ttk.Label(custom_size_frame, text="Height:").pack(side=tk.LEFT)
        ttk.Entry(custom_size_frame, textvariable=custom_height_var, width=8).pack(side=tk.LEFT, padx=(5, 15))
        ttk.Label(custom_size_frame, text="(mặc định: W=500, H=600)", 
                font=("Arial", 8), foreground="gray").pack(side=tk.LEFT)

        # --- Dynamic show/hide functions ---
        def update_position_controls(*args):
            """Hiển thị controls phù hợp cho position mode"""
            if position_mode_var.get() == "preset":
                custom_pos_frame.pack_forget()
                preset_frame.pack(fill=tk.X)
            else:
                preset_frame.pack_forget()
                custom_pos_frame.pack(fill=tk.X)
        
        def update_size_controls(*args):
            """Hiển thị controls phù hợp cho size mode"""
            if size_mode_var.get() == "percentage":
                custom_size_frame.pack_forget()
                percent_frame.pack(fill=tk.X)
            else:
                percent_frame.pack_forget()
                custom_size_frame.pack(fill=tk.X)
        
        # Bind mode changes
        position_mode_var.trace('w', update_position_controls)
        size_mode_var.trace('w', update_size_controls)
        
        # Initial setup
        update_position_controls()
        update_size_controls()

        # --- Chroma Key section ---
        chroma_frame = ttk.LabelFrame(main_frame, text="🎨 Xóa nền (Chroma Key)", padding="10")
        chroma_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Checkbutton(chroma_frame, text="Xóa nền video overlay", variable=chroma_enabled_var).pack(anchor=tk.W, pady=(0, 10))
        
        color_frame = ttk.Frame(chroma_frame)
        color_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(color_frame, text="Chọn màu nền cần xóa:").pack(side=tk.LEFT)
        color_combo = ttk.Combobox(color_frame, textvariable=chroma_color_var,
                    values=["green", "blue", "black", "white", "cyan", "red", "magenta", "yellow"],
                    state="readonly", width=12)
        color_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        settings_label = ttk.Label(chroma_frame, text="", font=("Arial", 9), foreground="blue")
        settings_label.pack(anchor=tk.W)
        
        def update_settings_display(*args):
            color = chroma_color_var.get()
            if color in OPTIMAL_CHROMA_REMOVAL:
                similarity, blend = OPTIMAL_CHROMA_REMOVAL[color]
                settings_label.config(text=f"Tự động áp dụng: Similarity={similarity}, Blend={blend}")
                custom_similarity_var.set(f"{similarity:.3f}")
                custom_blend_var.set(f"{blend:.3f}")
            else:
                settings_label.config(text="Sử dụng settings mặc định")
                custom_similarity_var.set("0.150")
                custom_blend_var.set("0.150")
        
        chroma_color_var.trace('w', update_settings_display)
        update_settings_display()
        
        ttk.Checkbutton(chroma_frame, text="Hiển thị cài đặt nâng cao", variable=advanced_mode_var).pack(anchor=tk.W, pady=(10, 0))
        
        # Advanced controls frame với Entry thay vì Scale
        advanced_frame = ttk.Frame(chroma_frame)
        
        # Similarity control
        sim_frame = ttk.Frame(advanced_frame)
        sim_frame.pack(fill=tk.X, pady=5)
        ttk.Label(sim_frame, text="Similarity:").pack(side=tk.LEFT)
        similarity_entry = ttk.Entry(sim_frame, textvariable=custom_similarity_var, width=10)
        similarity_entry.pack(side=tk.LEFT, padx=(10, 5))
        ttk.Label(sim_frame, text="(0.001-0.500)", font=("Arial", 8), foreground="gray").pack(side=tk.LEFT, padx=(5, 0))
        
        # Blend control
        blend_frame = ttk.Frame(advanced_frame)
        blend_frame.pack(fill=tk.X, pady=5)
        ttk.Label(blend_frame, text="Blend:").pack(side=tk.LEFT)
        blend_entry = ttk.Entry(blend_frame, textvariable=custom_blend_var, width=10)
        blend_entry.pack(side=tk.LEFT, padx=(10, 5))
        ttk.Label(blend_frame, text="(0.001-0.500)", font=("Arial", 8), foreground="gray").pack(side=tk.LEFT, padx=(5, 0))
        
        # Help text
        help_frame = ttk.Frame(advanced_frame)
        help_frame.pack(fill=tk.X, pady=(10, 0))
        help_text = ttk.Label(help_frame, 
                            text="💡 Số càng nhỏ = khử màu càng nghiêm ngặt\n"
                                "   Số càng lớn = khử màu càng lỏng lẻo", 
                            font=("Arial", 8), foreground="blue")
        help_text.pack(anchor=tk.W)
        
        def toggle_advanced_mode(*args):
            if advanced_mode_var.get():
                advanced_frame.pack(fill=tk.X, pady=(5, 0))
            else:
                advanced_frame.pack_forget()
                update_settings_display()
        
        advanced_mode_var.trace('w', toggle_advanced_mode)

        # --- Control buttons ---
        button_frame = ttk.Frame(dialog)  # Gắn vào dialog, không phải main_frame
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10, padx=20)

        def save_video_overlay():
            try:
                selected_video = video_var.get()
                if not selected_video:
                    messagebox.showerror("Lỗi", "Vui lòng chọn video!")
                    return
                    
                # Find video path
                video_path = None
                for f in video_files:
                    if os.path.basename(f) == selected_video:
                        video_path = f
                        break
                        
                start_time = float(start_var.get())
                duration = float(duration_var.get()) if duration_var.get().strip() else None
                
                # Process position settings
                position_mode = position_mode_var.get()
                if position_mode == "preset":
                    position = position_preset_var.get()
                    custom_x = None
                    custom_y = None
                else:
                    position = "custom"
                    custom_x = int(custom_x_var.get())
                    custom_y = int(custom_y_var.get())
                
                # Process size settings
                size_mode = size_mode_var.get()
                if size_mode == "percentage":
                    size_percent = int(size_percent_var.get())
                    custom_width = None
                    custom_height = None
                else:
                    size_percent = None
                    custom_width = int(custom_width_var.get())
                    custom_height = int(custom_height_var.get())
                
                # Chroma settings
                chroma_color = chroma_color_var.get()
                
                if advanced_mode_var.get():
                    # Validate user input
                    try:
                        similarity = float(custom_similarity_var.get())
                        blend = float(custom_blend_var.get())
                        
                        # Clamp values
                        similarity = max(0.001, min(0.500, similarity))
                        blend = max(0.001, min(0.500, blend))
                        
                    except ValueError:
                        messagebox.showerror("Lỗi", "Similarity và Blend phải là số từ 0.001 đến 0.500")
                        return
                else:
                    similarity, blend = OPTIMAL_CHROMA_REMOVAL.get(chroma_color, (0.15, 0.1))
                
                self.video_overlay_settings = {
                    'enabled': True,
                    'video_path': video_path,
                    'start_time': start_time,
                    'duration': duration,
                    'position_mode': position_mode,
                    'position': position,
                    'custom_x': custom_x,
                    'custom_y': custom_y,
                    'size_mode': size_mode,
                    'size_percent': size_percent,
                    'custom_width': custom_width,
                    'custom_height': custom_height,
                    'chroma_key': chroma_enabled_var.get(),
                    'chroma_color': chroma_color,
                    'chroma_similarity': similarity,
                    'chroma_blend': blend,
                    'auto_hide': auto_hide_var.get()
                }
                
                # Update status message - ĐÃ SỬA HIỂN THỊ Y=1200
                if position_mode == "custom":
                    pos_text = f"X={custom_x}, Y={custom_y}"
                else:
                    pos_text = position
                    
                if size_mode == "custom":
                    size_text = f"W={custom_width}, H={custom_height}"
                else:
                    size_text = f"{size_percent}%"
                    
                auto_hide_text = " (auto-hide)" if auto_hide_var.get() else " (freeze)"
                
                self.video_overlay_status.config(
                    text=f"✅ {selected_video} | {pos_text} | {size_text} | {chroma_color} ({similarity:.3f}, {blend:.3f}){auto_hide_text}", 
                    foreground="green"
                )
                
                self.log_message(f"🎬 Cấu hình video overlay: {selected_video}")
                self.log_message(f"   📍 Vị trí: {pos_text}")
                self.log_message(f"   📏 Kích thước: {size_text}")
                self.log_message(f"   🎨 Chroma: {chroma_color} ({similarity:.3f}, {blend:.3f})")
                
                dialog.destroy()
                
            except Exception as e:
                messagebox.showerror("Lỗi", f"Giá trị không hợp lệ: {e}")

        ttk.Button(button_frame, text="✅ Lưu", command=save_video_overlay).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="❌ Hủy", command=dialog.destroy).pack(side=tk.RIGHT)

    
    def _get_chroma_values_for_preset(self, color, preset):
        """Convert color + preset thành similarity, blend values"""
        
        # Tham số tối ưu cho từng màu
        color_settings = {
            "green": {
                "loose": (0.3, 0.3),
                "normal": (0.15, 0.15),
                "custom": (0.2, 0.2),  # Green optimized
                "strict": (0.08, 0.08),
                "very_strict": (0.03, 0.03),
                "ultra_strict": (0.01, 0.01)
            },
            "black": {
                "loose": (0.05, 0.05),
                "normal": (0.02, 0.02),
                "custom": (0.01, 0.01),  # Black precision
                "strict": (0.005, 0.005),
                "very_strict": (0.001, 0.001),
                "ultra_strict": (0.0005, 0.0005)
            },
            "blue": {
                "loose": (0.35, 0.35),
                "normal": (0.2, 0.2),
                "custom": (0.25, 0.25),   # Blue optimized
                "strict": (0.1, 0.1),
                "very_strict": (0.05, 0.05),
                "ultra_strict": (0.02, 0.02)
            },
            "cyan": {
                "loose": (0.25, 0.25),
                "normal": (0.12, 0.12),
                "custom": (0.15, 0.15),   # Cyan optimized
                "strict": (0.06, 0.06),
                "very_strict": (0.03, 0.03),
                "ultra_strict": (0.01, 0.01)
            },
            "red": {
                "loose": (0.4, 0.4),
                "normal": (0.25, 0.25),
                "custom": (0.3, 0.3),   # Red optimized (harder to key)
                "strict": (0.15, 0.15),
                "very_strict": (0.08, 0.08),
                "ultra_strict": (0.03, 0.03)
            },
            "magenta": {
                "loose": (0.3, 0.3),
                "normal": (0.18, 0.18),
                "custom": (0.22, 0.22),  # Magenta optimized
                "strict": (0.1, 0.1),
                "very_strict": (0.05, 0.05),
                "ultra_strict": (0.02, 0.02)
            },
            "yellow": {
                "loose": (0.35, 0.35),
                "normal": (0.22, 0.22),
                "custom": (0.28, 0.28),  # Yellow optimized (skin tone conflict)
                "strict": (0.12, 0.12),
                "very_strict": (0.06, 0.06),
                "ultra_strict": (0.03, 0.03)
            }
        }
        
        # Default fallback cho màu khác
        default_settings = {
            "loose": (0.3, 0.3),
            "normal": (0.15, 0.5),
            "custom": (0.2, 0.2),
            "strict": (0.05, 0.05),
            "very_strict": (0.01, 0.01),
            "ultra_strict": (0.005, 0.005)
        }
        
        color_map = color_settings.get(color.lower(), default_settings)
        return color_map.get(preset.lower(), (0.2, 0.2))

    def create_multiple_overlays(self, selected_video):
        """Tạo cấu hình multiple video overlay giống ảnh 2, 3"""
        if not selected_video:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn video trước!")
            return
        
        # Tìm đường dẫn video
        video_path = None
        video_files = []
        folder_path = self.video_folder_path.get()
        
        for ext in ['*.mp4', '*.avi', '*.mov', '*.mkv', '*.wmv']:
            video_files.extend(glob.glob(os.path.join(folder_path, ext)))
        
        for f in video_files:
            if os.path.basename(f) == selected_video:
                video_path = f
                break
        
        if not video_path:
            messagebox.showerror("Lỗi", "Không tìm thấy file video!")
            return
          # Tạo 3 cấu hình overlay giống ảnh 2, 3 với chroma key tối ưu
        overlays = [
            {
                'video_path': video_path,
                'start_time': 2.0,
                'duration': 8.0,
                'position': 'top-right',
                'size_percent': 25,
                'chroma_key': True,
                'chroma_color': '0x32CD32',  # Lime green - tối ưu cho chroma key
                'chroma_similarity': 0.25    # Giá trị tối ưu từ test_chroma_key.py
            },
            {
                'video_path': video_path,
                'start_time': 12.0,
                'duration': 8.0,
                'position': 'bottom-left',
                'size_percent': 20,
                'chroma_key': True,
                'chroma_color': '0x32CD32',
                'chroma_similarity': 0.25
            },
            {
                'video_path': video_path,
                'start_time': 22.0,
                'duration': 8.0,
                'position': 'center',
                'size_percent': 30,
                'chroma_key': True,
                'chroma_color': '0x32CD32',
                'chroma_similarity': 0.25
            }
        ]
        
        # Lưu tất cả overlay vào settings
        self.video_overlay_settings = {
            'enabled': True,
            'multiple_overlays': overlays
        }
        
        self.video_overlay_status.config(
            text=f"✅ 3 overlay từ {selected_video} (2s-7s, 8s-13s, 15s-20s)", 
            foreground="green"
        )
        
        self.log_message(f"🎬 Đã tạo 3 video overlay từ: {selected_video}")
        self.log_message("   • Overlay 1: 2s-7s (top-right, 25%)")
        self.log_message("   • Overlay 2: 8s-13s (bottom-left, 20%)")
        self.log_message("   • Overlay 3: 15s-20s (center, 30%)")
        self.log_message("   • Chroma key: Rất nghiêm ngặt để khử xanh lá hoàn toàn")
        
        messagebox.showinfo("Thành công", "Đã tạo 3 video overlay với thời gian và vị trí khác nhau!\n\nChroma key đã được tối ưu để khử xanh lá hoàn toàn.")

    def log_message(self, message):
        """Thêm thông điệp vào log"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def update_status(self, status):
        """Cập nhật trạng thái"""
        self.status_label.config(text=status)
        self.root.update_idletasks()

    def start_processing(self):
        """Bắt đầu xử lý hàng loạt"""
        if self.processing:
            messagebox.showwarning("Cảnh báo", "Đã có quá trình xử lý đang chạy!")
            return
        
        # Validation
        input_folder_path = self.input_folder_path.get()
        output_folder_path = self.output_folder_path.get()
        
        if not input_folder_path or not output_folder_path:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn thư mục video đầu vào và thư mục đầu ra.")
            return

        # Tìm tất cả file video trong thư mục input
        video_files = []
        for ext in ['*.mp4', '*.avi', '*.mov', '*.mkv', '*.wmv', '*.flv']:
            video_files.extend(glob.glob(os.path.join(input_folder_path, ext)))

        if not video_files:
            messagebox.showwarning("Không có video", f"Không tìm thấy file video nào trong thư mục: {input_folder_path}\n\nVui lòng thêm video vào thư mục hoặc chọn thư mục khác.")
            return

        # CHUẨN BỊ VIDEO OVERLAY SETTINGS - SỬ DỤNG FOLDER MẶC ĐỊNH
        video_overlay_settings = self.video_overlay_settings.copy()
        
        # Kiểm tra thư mục video overlay
        overlay_folder_path = self.video_folder_path.get()
        if overlay_folder_path and os.path.exists(overlay_folder_path):
            overlay_files = []
            for ext in ['*.mp4', '*.avi', '*.mov', '*.mkv', '*.wmv']:
                overlay_files.extend(glob.glob(os.path.join(overlay_folder_path, ext)))
            
            if overlay_files:
                # Sử dụng file đầu tiên làm default overlay
                video_overlay_settings['video_path'] = overlay_files[0]
                video_overlay_settings['enabled'] = True
                self.log_message(f"🎭 Sử dụng video overlay: {os.path.basename(overlay_files[0])} từ {overlay_folder_path}")
            else:
                # Không có file overlay, disable
                video_overlay_settings['enabled'] = False
                self.log_message(f"⚠️ Thư mục {overlay_folder_path} trống, tắt chức năng overlay")
        else:
            # Không có thư mục overlay, disable
            video_overlay_settings['enabled'] = False
            self.log_message("ℹ️ Không có thư mục video overlay, chỉ xử lý phụ đề + 9:16")

        # Lấy cấu hình phụ đề
        subtitle_style = self.get_subtitle_style()
        
        # Log thông tin xử lý
        print("🎯 Cấu hình batch processing:")
        print(f"    Input folder: {input_folder_path}")
        print(f"    Output folder: {output_folder_path}")
        print(f"    Overlay folder: {overlay_folder_path}")
        print(f"    Số video: {len(video_files)}")
        print(f"    Ngôn ngữ: {self.source_language.get()} → {self.target_language.get()}")
        print(f"    Tạo phụ đề: {self.enable_subtitle.get()}")
        print(f"    Kiểu phụ đề: {subtitle_style}")
        print(f"    Video overlay: {video_overlay_settings.get('enabled', False)}")
        
        if video_overlay_settings.get('enabled', False):
            print(f"    Overlay path: {video_overlay_settings.get('video_path', 'N/A')}")

        self.status_label.config(text=f"🎬 Đang xử lý {len(video_files)} video... Vui lòng chờ.")
        self.progress_var.set(0)
        self.progress_bar.start()

        # Thực hiện xử lý trong thread riêng
        def worker():
            try:
                self.log_message(f"🎬 Bắt đầu xử lý hàng loạt {len(video_files)} video...")
                editor = AutoVideoEditor()
                
                total_files = len(video_files)
                success_count = 0
                error_count = 0
                
                for i, input_video_path in enumerate(video_files):
                    try:
                        # Tạo tên file output
                        video_name = os.path.splitext(os.path.basename(input_video_path))[0]
                        output_video_path = os.path.join(output_folder_path, f"{video_name}_processed.mp4")
                        
                        self.log_message(f"📹 ({i+1}/{total_files}) Đang xử lý: {os.path.basename(input_video_path)}")
                        
                        # Xử lý video với kiểu phụ đề
                        editor.process_video(
                            input_video_path=input_video_path,
                            output_video_path=output_video_path,
                            source_language=self.source_language.get(),
                            target_language=self.target_language.get(),
                            video_overlay_settings=video_overlay_settings,
                            words_per_line=self.words_per_line.get(),
                            enable_subtitle=self.enable_subtitle.get(),
                            subtitle_style=subtitle_style
                        )
                        
                        success_count += 1
                        self.log_message(f"✅ ({i+1}/{total_files}) Hoàn thành: {os.path.basename(output_video_path)}")
                        
                    except Exception as e:
                        error_count += 1
                        self.log_message(f"❌ ({i+1}/{total_files}) Lỗi: {os.path.basename(input_video_path)} - {str(e)}")
                
                # Kết quả cuối cùng
                self.status_label.config(text=f"✅ Hoàn thành! {success_count} thành công, {error_count} lỗi")
                self.log_message(f"🎉 Kết quả batch processing:")
                self.log_message(f"   ✅ Thành công: {success_count}")
                self.log_message(f"   ❌ Lỗi: {error_count}")
                self.log_message(f"   📁 Thư mục output: {output_folder_path}")
                
            except Exception as e:
                self.status_label.config(text="❌ Lỗi xử lý!")
                self.log_message(f"❌ Lỗi batch processing: {e}")
                import traceback
                self.log_message(f"Chi tiết lỗi: {traceback.format_exc()}")
            finally:
                self.progress_bar.stop()
                self.progress_var.set(0)

        threading.Thread(target=worker, daemon=True).start()
    
    


def main():
    root = tk.Tk()
    app = VideoEditorGUI(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
