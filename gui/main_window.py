#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main Window GUI Module
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import AutoVideoEditor
from .config_dialogs import OverlayConfigDialog, VideoOverlayConfigDialog
from batch.batch_gui import show_batch_processing_dialog
from batch.advanced_batch_gui import AdvancedBatchGUI

class VideoEditorMainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("🎬 Video Editor - Chỉnh sửa Video Tự động")
        self.root.geometry("800x600")
        
        # Variables        self.input_video_path = tk.StringVar()
        self.output_video_path = tk.StringVar()
        self.img_folder_path = tk.StringVar()
        self.video_folder_path = tk.StringVar()
        self.source_language = tk.StringVar(value="vi")
        self.target_language = tk.StringVar(value="en")
        self.custom_timeline_var = tk.BooleanVar()
        self.words_per_line = tk.IntVar(value=7)  # Số từ mỗi dòng phụ đề
        
        # Processing state
        self.processing = False
        self.overlay_times = {}
        self.video_overlay_settings = {'enabled': False}
        
        self.setup_ui()
        
    def setup_ui(self):
        """Thiết lập giao diện chính"""
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
            text="🎬 Ứng dụng Chỉnh sửa Video với Overlay",
            font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        row = 1
        
        # Input/Output section
        self._create_file_selection_section(main_frame, row)
        row += 4
        
        # Language selection
        self._create_language_section(main_frame, row)
        row += 1
        
        # Folder selection
        self._create_folder_section(main_frame, row)
        row += 2
        
        # Configuration buttons
        self._create_config_section(main_frame, row)
        row += 2
        
        # Custom timeline checkbox
        self._create_custom_timeline_section(main_frame, row)
        row += 1
        
        # Status section
        self._create_status_section(main_frame, row)
        row += 2
        
        # Process button
        self._create_process_section(main_frame, row)
        row += 1
        
        # Log section
        self._create_log_section(main_frame, row)
        row += 1
        
        # Subtitle configuration section
        self._create_subtitle_config_section(main_frame, row)
        
    def _create_file_selection_section(self, parent, start_row):
        """Tạo phần chọn file input/output"""
        # Input video
        ttk.Label(parent, text="📁 Video đầu vào:").grid(row=start_row, column=0, sticky=tk.W, pady=5)
        input_entry = ttk.Entry(parent, textvariable=self.input_video_path)
        input_entry.grid(row=start_row, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=5)
        ttk.Button(parent, text="Chọn file", command=self.select_input_video).grid(row=start_row, column=2, padx=(5, 0), pady=5)
        
        # Output video
        ttk.Label(parent, text="💾 Video đầu ra:").grid(row=start_row+1, column=0, sticky=tk.W, pady=5)
        output_entry = ttk.Entry(parent, textvariable=self.output_video_path)
        output_entry.grid(row=start_row+1, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=5)
        ttk.Button(parent, text="Chọn vị trí", command=self.select_output_video).grid(row=start_row+1, column=2, padx=(5, 0), pady=5)
        
    def _create_language_section(self, parent, row):
        """Tạo phần chọn ngôn ngữ"""
        lang_frame = ttk.Frame(parent)
        lang_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(lang_frame, text="🌐 Ngôn ngữ gốc:").pack(side=tk.LEFT)
        language_combo = ttk.Combobox(
            lang_frame, 
            textvariable=self.source_language,
            values=["vi", "en", "ja", "ko", "zh", "es", "fr", "de"],
            state="readonly",
            width=10
        )
        language_combo.pack(side=tk.LEFT, padx=(10, 20))
        
        ttk.Label(lang_frame, text="🎯 Ngôn ngữ đích:").pack(side=tk.LEFT)
        target_language_combo = ttk.Combobox(
            lang_frame, 
            textvariable=self.target_language,
            values=["en", "vi", "ja", "ko", "zh", "es", "fr", "de"],
            state="readonly",
            width=10
        )
        target_language_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # Subtitle words per line
        ttk.Label(lang_frame, text="📝 Từ/dòng:").pack(side=tk.LEFT, padx=(20, 5))
        words_spinbox = ttk.Spinbox(
            lang_frame,
            from_=4, to=12,
            textvariable=self.words_per_line,
            width=5,
            state="readonly"
        )
        words_spinbox.pack(side=tk.LEFT)
        
        # Tooltip
        ttk.Label(lang_frame, text="(4-12 từ, khuyến nghị 6-7)", 
                 font=("Arial", 8), foreground="gray").pack(side=tk.LEFT, padx=(5, 0))
        
    def _create_folder_section(self, parent, start_row):
        """Tạo phần chọn thư mục"""
        # Image folder
        ttk.Label(parent, text="🖼️ Thư mục ảnh overlay:").grid(row=start_row, column=0, sticky=tk.W, pady=5)
        img_entry = ttk.Entry(parent, textvariable=self.img_folder_path)
        img_entry.grid(row=start_row, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=5)
        ttk.Button(parent, text="Chọn thư mục", command=self.select_img_folder).grid(row=start_row, column=2, padx=(5, 0), pady=5)
        
        # Video folder
        ttk.Label(parent, text="🎭 Thư mục video overlay:").grid(row=start_row+1, column=0, sticky=tk.W, pady=5)
        video_entry = ttk.Entry(parent, textvariable=self.video_folder_path)
        video_entry.grid(row=start_row+1, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=5)
        ttk.Button(parent, text="Chọn thư mục", command=self.select_video_folder).grid(row=start_row+1, column=2, padx=(5, 0), pady=5)
        
    def _create_config_section(self, parent, start_row):
        """Tạo phần cấu hình overlay"""
        config_frame = ttk.Frame(parent)
        config_frame.grid(row=start_row, column=0, columnspan=3, pady=(10, 10), sticky=(tk.W, tk.E))
        ttk.Button(config_frame, text="⏰ Cấu hình Overlay Ảnh", command=self.configure_overlay_timing).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(config_frame, text="🎬 Cấu hình Video Overlay", command=self.configure_video_overlay).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(config_frame, text="🎭 Animation Text", command=self.configure_text_animation).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(config_frame, text="📦 Batch Processing", command=self.open_batch_processing).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(config_frame, text="🚀 Advanced Batch (100+ Videos)", command=self.open_advanced_batch).pack(side=tk.LEFT, padx=(0, 10))
        
        # Status labels
        self.timing_status = ttk.Label(parent, text="Chưa cấu hình overlay ảnh", foreground="gray")
        self.timing_status.grid(row=start_row+1, column=0, columnspan=3, sticky=tk.W)
        
        self.video_overlay_status = ttk.Label(parent, text="Chưa cấu hình video overlay", foreground="gray")
        self.video_overlay_status.grid(row=start_row+2, column=0, columnspan=3, sticky=tk.W)
        
    def _create_custom_timeline_section(self, parent, row):
        """Tạo phần custom timeline"""
        custom_timeline_frame = ttk.Frame(parent)
        custom_timeline_frame.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=5)
        ttk.Checkbutton(
            custom_timeline_frame, 
            text="🎯 Sử dụng Custom Timeline (3 ảnh: 1.png=5-6s Y=865, 2.png=6-7s Y=900, 3.png=7-8s Y=900)",
            variable=self.custom_timeline_var
        ).pack(side=tk.LEFT)
        
    def _create_status_section(self, parent, start_row):
        """Tạo phần hiển thị trạng thái"""
        ttk.Label(parent, text="📊 Trạng thái:").grid(row=start_row, column=0, sticky=tk.W, pady=5)
        self.status_label = ttk.Label(parent, text="Sẵn sàng", foreground="green")
        self.status_label.grid(row=start_row, column=1, columnspan=2, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(parent, mode='indeterminate')
        self.progress_bar.grid(row=start_row+1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
    def _create_process_section(self, parent, row):
        """Tạo phần xử lý"""
        self.process_button = ttk.Button(
            parent, 
            text="🚀 Bắt đầu xử lý",
            command=self.start_processing,
            style="Accent.TButton"
        )
        self.process_button.grid(row=row, column=0, columnspan=3, pady=20)
        
    def _create_log_section(self, parent, row):
        """Tạo phần log"""
        ttk.Label(parent, text="📝 Log:").grid(row=row, column=0, sticky=(tk.W, tk.N), pady=5)
        
        log_frame = ttk.Frame(parent)
        log_frame.grid(row=row+1, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.log_text = tk.Text(log_frame, height=8, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        parent.rowconfigure(row+1, weight=1)
        
    
        """Tạo phần cấu hình phụ đề nâng cao"""
        subtitle_frame = ttk.LabelFrame(parent, text="📝 Cấu hình Phụ đề Nâng cao", padding="10")
        subtitle_frame.grid(row=start_row, column=0, columnspan=3, pady=(10, 10), sticky=(tk.W, tk.E))
        
        # Words per line configuration
        words_config_frame = ttk.Frame(subtitle_frame)
        words_config_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(words_config_frame, text="📱 Từ mỗi dòng phụ đề:", 
                 font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        
        words_spinbox = ttk.Spinbox(
            words_config_frame,
            from_=4, to=12,
            textvariable=self.words_per_line,
            width=5,
            state="readonly"
        )
        words_spinbox.pack(side=tk.LEFT, padx=(10, 5))
        
        # Preview button
        def preview_subtitle_split():
            """Preview cách chia dòng phụ đề"""
            self.show_subtitle_preview()
        
        ttk.Button(words_config_frame, text="👁️ Xem trước", 
                  command=preview_subtitle_split).pack(side=tk.LEFT, padx=(10, 0))
        
        # Info label
        info_text = "💡 6-7 từ tối ưu cho TikTok/Instagram • 4-5 từ cho video nhanh • 8+ từ cho desktop"
        ttk.Label(subtitle_frame, text=info_text, 
                 font=("Arial", 9), foreground="blue").pack(pady=(5, 0))
        
        # Benefits
        benefits_text = "✨ Dễ đọc trên mobile • Tăng engagement • Tự động phân bổ thời gian"
        ttk.Label(subtitle_frame, text=benefits_text, 
                 font=("Arial", 9), foreground="green").pack()

    # File selection methods
    def select_input_video(self):
        """Chọn file video đầu vào"""
        filename = filedialog.askopenfilename(
            title="Chọn video đầu vào",
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv"), ("All files", "*.*")]
        )
        if filename:
            self.input_video_path.set(filename)
            
    def select_output_video(self):
        """Chọn vị trí lưu video đầu ra"""
        filename = filedialog.asksaveasfilename(
            title="Chọn vị trí lưu video",
            defaultextension=".mp4",
            filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")]
        )
        if filename:
            self.output_video_path.set(filename)

            
    def select_video_folder(self):
        """Chọn thư mục chứa video overlay"""
        folder = filedialog.askdirectory(title="Chọn thư mục video overlay")
        if folder:
            self.video_folder_path.set(folder)
            
    # Configuration methods
    def configure_overlay_timing(self):
        """Cấu hình thời gian overlay ảnh"""
        if not self.img_folder_path.get():
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn thư mục ảnh overlay trước!")
            return
            
        dialog = OverlayConfigDialog(self.root, self.img_folder_path.get())
        if dialog.result:
            self.overlay_times = dialog.result
            self.timing_status.config(text=f"Đã cấu hình {len(self.overlay_times)} ảnh", foreground="green")
            
    def configure_video_overlay(self):
        """Cấu hình video overlay"""
        if not self.video_folder_path.get():
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn thư mục video overlay trước!")
            return
            
        dialog = VideoOverlayConfigDialog(self.root, self.video_folder_path.get())
        if dialog.result:
            self.video_overlay_settings = dialog.result
            self.video_overlay_status.config(text="Đã cấu hình video overlay", foreground="green")
            
    def configure_text_animation(self):
        """Cấu hình animation text"""
        messagebox.showinfo("Thông tin", "Chức năng Animation Text đang được phát triển.\\n\\nHiện tại bạn có thể sử dụng Custom Timeline để áp dụng 3 ảnh với animation:\\n- Ảnh 1: fade in/out\\n- Ảnh 2: slide left\\n- Ảnh 3: zoom in")
        
    
    def _create_subtitle_config_section(self, parent, start_row):
        """Tạo phần cấu hình phụ đề nâng cao"""
        subtitle_frame = ttk.LabelFrame(parent, text="📝 Cấu hình Phụ đề Nâng cao", padding="10")
        subtitle_frame.grid(row=start_row, column=0, columnspan=3, pady=(10, 10), sticky=(tk.W, tk.E))
        
        # Words per line configuration
        words_config_frame = ttk.Frame(subtitle_frame)
        words_config_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(words_config_frame, text="📱 Từ mỗi dòng phụ đề:", 
                font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        
        words_spinbox = ttk.Spinbox(
            words_config_frame,
            from_=4, to=12,
            textvariable=self.words_per_line,
            width=5,
            state="readonly"
        )
        words_spinbox.pack(side=tk.LEFT, padx=(10, 5))
        
        # Preview button
        def preview_subtitle_split():
            """Preview cách chia dòng phụ đề"""
            self.show_subtitle_preview()
        
        ttk.Button(words_config_frame, text="👁️ Xem trước", 
                command=preview_subtitle_split).pack(side=tk.LEFT, padx=(10, 0))
        
        # Subtitle style settings
        style_frame = ttk.Frame(subtitle_frame)
        style_frame.pack(fill=tk.X, pady=(10, 5))
        
        # Khởi tạo biến cho style phụ đề (nếu chưa có)
        if not hasattr(self, 'subtitle_preset'):
            self.subtitle_preset = tk.StringVar(value="default")
        if not hasattr(self, 'subtitle_text_color'):
            self.subtitle_text_color = tk.StringVar(value="black")
        if not hasattr(self, 'subtitle_box_style'):
            self.subtitle_box_style = tk.StringVar(value="box")
        if not hasattr(self, 'subtitle_box_color'):
            self.subtitle_box_color = tk.StringVar(value="white")
        if not hasattr(self, 'subtitle_font_size'):
            self.subtitle_font_size = tk.IntVar(value=24)
        
        # Preset selector
        ttk.Label(style_frame, text="🎨 Kiểu phụ đề:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        preset_combo = ttk.Combobox(
            style_frame,
            textvariable=self.subtitle_preset,
            values=["default", "tiktok", "youtube", "instagram", "modern", "classic"],
            state="readonly",
            width=12
        )
        preset_combo.pack(side=tk.LEFT, padx=(10, 20))
        
        # Advanced style button
        ttk.Button(style_frame, text="⚙️ Tùy chỉnh nâng cao", command=self.configure_subtitle_style).pack(side=tk.LEFT)
        
        # Info label
        info_text = "💡 6-7 từ tối ưu cho TikTok/Instagram • 4-5 từ cho video nhanh • 8+ từ cho desktop"
        ttk.Label(subtitle_frame, text=info_text, 
                font=("Arial", 9), foreground="blue").pack(pady=(5, 0))
        
        # Benefits
        benefits_text = "✨ Dễ đọc trên mobile • Tăng engagement • Tự động phân bổ thời gian"
        ttk.Label(subtitle_frame, text=benefits_text, 
                font=("Arial", 9), foreground="green").pack()
        
        # Style preview
        self.style_preview_label = ttk.Label(subtitle_frame, text="👉 Mẫu: Chữ đen, nền trắng", font=("Arial", 10))
        self.style_preview_label.pack(pady=(5, 0))
        
        # Update preview when preset changes
        def update_style_preview(*args):
            preset = self.subtitle_preset.get()
            if preset == "default":
                self.style_preview_label.config(text="👉 Mẫu: Chữ đen, nền trắng")
            elif preset == "tiktok":
                self.style_preview_label.config(text="👉 Mẫu: Chữ trắng, nền đen lớn")
            elif preset == "youtube":
                self.style_preview_label.config(text="👉 Mẫu: Chữ trắng, viền đen")
            elif preset == "instagram":
                self.style_preview_label.config(text="👉 Mẫu: Chữ trắng, nền trong suốt")
            elif preset == "modern":
                self.style_preview_label.config(text="👉 Mẫu: Chữ trắng, nền xanh")
            elif preset == "classic":
                self.style_preview_label.config(text="👉 Mẫu: Chữ vàng, viền đen")
                
        self.subtitle_preset.trace_add("write", update_style_preview)
        update_style_preview()

    def configure_subtitle_style(self):
        """Hiển thị dialog cấu hình kiểu phụ đề tùy chỉnh"""
        dialog = tk.Toplevel(self.root)
        dialog.title("🎨 Tùy chỉnh kiểu phụ đề")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(main_frame, text="🎨 Tùy chỉnh kiểu phụ đề", font=("Arial", 14, "bold")).pack(pady=(0, 20))
        
        # Màu chữ
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.X, pady=5)
        ttk.Label(text_frame, text="Màu chữ:").pack(side=tk.LEFT)
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
        box_frame = ttk.Frame(main_frame)
        box_frame.pack(fill=tk.X, pady=5)
        ttk.Label(box_frame, text="Kiểu nền:").pack(side=tk.LEFT)
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
        box_color_frame = ttk.Frame(main_frame)
        box_color_frame.pack(fill=tk.X, pady=5)
        ttk.Label(box_color_frame, text="Màu nền:").pack(side=tk.LEFT)
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
        font_frame = ttk.Frame(main_frame)
        font_frame.pack(fill=tk.X, pady=5)
        ttk.Label(font_frame, text="Cỡ chữ:").pack(side=tk.LEFT)
        font_size_spinbox = ttk.Spinbox(
            font_frame,
            from_=12, to=36, increment=2,
            textvariable=self.subtitle_font_size,
            width=5
        )
        font_size_spinbox.pack(side=tk.LEFT, padx=(10, 0))
        
        # Preview
        preview_frame = ttk.LabelFrame(main_frame, text="Xem trước", padding="10")
        preview_frame.pack(fill=tk.X, pady=(20, 10))
        
        preview_canvas = tk.Canvas(preview_frame, width=400, height=100, bg="black")
        preview_canvas.pack()
        
        preview_text_id = preview_canvas.create_text(
            200, 50, 
            text="Đây là mẫu phụ đề", 
            fill="white", 
            font=("Arial", 18)
        )
        
        # Preview background
        preview_bg_id = preview_canvas.create_rectangle(
            0, 0, 0, 0,  # Will be updated
            fill="black", outline="", state="hidden"
        )
        
        # Move background behind text
        preview_canvas.tag_lower(preview_bg_id, preview_text_id)
        
        # Update preview function
        def update_preview(*args):
            # Update text color
            text_color = self.subtitle_text_color.get()
            preview_canvas.itemconfig(preview_text_id, fill=text_color)
            
            # Update text size
            font_size = self.subtitle_font_size.get()
            preview_canvas.itemconfig(preview_text_id, font=("Arial", font_size))
            
            # Update background
            box_style = self.subtitle_box_style.get()
            box_color = self.subtitle_box_color.get()
            
            if box_style == "none":
                preview_canvas.itemconfig(preview_bg_id, state="hidden")
            else:
                # Get text bounds
                bbox = preview_canvas.bbox(preview_text_id)
                if bbox:
                    # Add padding
                    padding = 10
                    x1, y1, x2, y2 = bbox
                    x1 -= padding
                    y1 -= padding
                    x2 += padding
                    y2 += padding
                    
                    preview_canvas.coords(preview_bg_id, x1, y1, x2, y2)
                    preview_canvas.itemconfig(preview_bg_id, fill=box_color, state="normal")
                    
                    # For outline style, use outline instead of fill
                    if box_style == "outline":
                        preview_canvas.itemconfig(preview_bg_id, fill="", outline=box_color, width=2)
                    else:
                        preview_canvas.itemconfig(preview_bg_id, fill=box_color, outline="")
        
        # Track changes to update preview
        self.subtitle_text_color.trace_add("write", update_preview)
        self.subtitle_box_style.trace_add("write", update_preview)
        self.subtitle_box_color.trace_add("write", update_preview)
        self.subtitle_font_size.trace_add("write", update_preview)
        
        # Initial preview update
        update_preview()
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        def apply_style():
            # Disable preset when using custom style
            self.subtitle_preset.set("")
            
            # Update main window preview
            self.style_preview_label.config(text=f"👉 Tùy chỉnh: Chữ {self.subtitle_text_color.get()}, kiểu {self.subtitle_box_style.get()}")
            
            dialog.destroy()
        
        ttk.Button(button_frame, text="Áp dụng", command=apply_style).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Hủy", command=dialog.destroy).pack(side=tk.RIGHT)

    def get_subtitle_style(self):
        """Lấy cấu hình kiểu phụ đề hiện tại"""
        preset = self.subtitle_preset.get()
        if preset:
            # Dùng preset có sẵn
            return {"preset": preset}
        else:
            # Dùng kiểu tùy chỉnh
            return {
                "text_color": self.subtitle_text_color.get(),
                "box_style": self.subtitle_box_style.get(),
                "box_color": self.subtitle_box_color.get(),
                "font_size": self.subtitle_font_size.get()
            }

    def start_processing(self):
        """Bắt đầu xử lý video - Cập nhật với tùy chọn phụ đề"""
        if self.processing:
            messagebox.showwarning("Cảnh báo", "Đã có quá trình xử lý đang chạy!")
            return
        
        # Validation
        if not self.input_video_path.get():
            messagebox.showerror("Lỗi", "Vui lòng chọn file video đầu vào!")
            return
        
        if not self.output_video_path.get():
            messagebox.showerror("Lỗi", "Vui lòng chọn vị trí lưu video đầu ra!")
            return
        
        # Lấy cấu hình phụ đề
        subtitle_style = self.get_subtitle_style()
        
        # Start processing
        self.processing = True
        self.progress_bar.start()
        self.process_button.config(state="disabled")
        
        thread = threading.Thread(target=lambda: self.process_video_thread(subtitle_style))
        thread.daemon = True
        thread.start()

    def process_video_thread(self, subtitle_style=None):
        """Thread xử lý video với tùy chọn phụ đề"""
        try:
            self.update_status("Đang xử lý video...")
            self.log_message("🚀 Bắt đầu xử lý video với overlay...")
            
            # Create editor
            editor = AutoVideoEditor()
            
            # Prepare parameters
            img_folder = self.img_folder_path.get() if self.img_folder_path.get() else None
            overlay_times = self.overlay_times if self.overlay_times else None
            
            # Process video
            editor.process_video(
                input_video_path=self.input_video_path.get(),
                output_video_path=self.output_video_path.get(),
                source_language=self.source_language.get(),
                target_language=self.target_language.get(),
                img_folder=img_folder,
                overlay_times=overlay_times,
                video_overlay_settings=getattr(self, 'video_overlay_settings', None),
                custom_timeline=self.custom_timeline_var.get(),
                words_per_line=self.words_per_line.get(),
                subtitle_style=subtitle_style
            )
            
            self.update_status("✅ Xử lý hoàn thành!")
            self.log_message("🎉 Xử lý video thành công!")
            messagebox.showinfo("Thành công", f"Video đã được lưu tại:\n{self.output_video_path.get()}")
            
        except Exception as e:
            error_msg = f"Lỗi xử lý video: {str(e)}"
            self.update_status("❌ Lỗi xử lý")
            self.log_message(f"❌ {error_msg}")
            messagebox.showerror("Lỗi", error_msg)
        
        finally:
            self.processing = False
            self.progress_bar.stop()
            self.process_button.config(state="normal")
        
    
            
    def open_batch_processing(self):
        """Mở cửa sổ batch processing"""
        try:
            show_batch_processing_dialog(self.root)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể mở Batch Processing: {str(e)}")
            
    def open_advanced_batch(self):
        """Mở Advanced Batch Processing cho 100+ video"""
        try:
            AdvancedBatchGUI(self.root)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể mở Advanced Batch Processing: {str(e)}")
    
    # Utility methods
    def update_status(self, message):
        """Cập nhật trạng thái"""
        self.status_label.config(text=message)
        self.root.update_idletasks()
        
    def log_message(self, message):
        """Thêm message vào log"""
        self.log_text.insert(tk.END, f"{message}\\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
