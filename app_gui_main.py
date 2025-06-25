#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI đơn giản với Video Overlay
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import sys
import glob
from pathlib import Path

OPTIMAL_CHROMA_REMOVAL = {
    "green": (0.2, 0.15),    # Green optimized từ testing
    "blue": (0.18, 0.12),    # Blue cần tolerance cao hơn
    "black": (0.01, 0.005),  # Black cần precision
    "white": (0.02, 0.01),   # White precision nhưng không khắt khe như black
    "cyan": (0.12, 0.08),    # Cyan dễ key
    "red": (0.25, 0.2),      # Red khó key nhất
    "magenta": (0.18, 0.12), # Tương tự blue
    "yellow": (0.22, 0.18)   # Khó vì conflict với skin tone
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
        self.root.title("Ứng dụng Chỉnh sửa Video Tự động - Có Video Overlay + Chroma Key")
        self.root.geometry("900x800")
        self.root.resizable(True, True)
        
        # Variables
        self.input_video_path = tk.StringVar()
        self.output_video_path = tk.StringVar()
        self.source_language = tk.StringVar(value="vi")
        self.target_language = tk.StringVar(value="en")
        
        # FIX: Đặt giá trị mặc định là rỗng thay vì "img"
        self.img_folder_path = tk.StringVar(value="")  # Thay đổi từ "img" thành ""
        self.video_folder_path = tk.StringVar(value="")  # Thay đổi từ "videoinput" thành ""
        
        self.words_per_line = tk.IntVar(value=7)
        self.processing = False
        
        # Overlay settings
        self.overlay_times = {}
        self.animation_config = {}
        self.video_overlay_settings = {'enabled': False}
        
        self.setup_ui()
        
    def setup_ui(self):
        """Thiết lập giao diện người dùng"""
        
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
            text="🎬 Ứng dụng Chỉnh sửa Video với Video Overlay",
            font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        row = 1
        
        # Input video selection
        ttk.Label(main_frame, text="📁 Video đầu vào:").grid(row=row, column=0, sticky=tk.W, pady=5)
        input_entry = ttk.Entry(main_frame, textvariable=self.input_video_path)
        input_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=5)
        ttk.Button(main_frame, text="Chọn file", command=self.select_input_video).grid(row=row, column=2, padx=(5, 0), pady=5)
        row += 1
        
        # Output video path
        ttk.Label(main_frame, text="💾 Video đầu ra:").grid(row=row, column=0, sticky=tk.W, pady=5)
        output_entry = ttk.Entry(main_frame, textvariable=self.output_video_path)
        output_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=5)
        ttk.Button(main_frame, text="Chọn vị trí", command=self.select_output_video).grid(row=row, column=2, padx=(5, 0), pady=5)
        row += 1
        
        # Language selection
        lang_frame = ttk.Frame(main_frame)
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
        
        # Words per line setting
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
        
        row += 1
        
        # Image folder selection
        ttk.Label(main_frame, text="🖼️ Thư mục ảnh:").grid(row=row, column=0, sticky=tk.W, pady=5)
        img_entry = ttk.Entry(main_frame, textvariable=self.img_folder_path)
        img_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=5)
        ttk.Button(main_frame, text="Chọn thư mục", command=self.select_img_folder).grid(row=row, column=2, padx=(5, 0), pady=5)
        row += 1
        
        # Video overlay folder selection
        ttk.Label(main_frame, text="🎭 Thư mục video overlay:").grid(row=row, column=0, sticky=tk.W, pady=5)
        video_entry = ttk.Entry(main_frame, textvariable=self.video_folder_path)
        video_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=5)
        ttk.Button(main_frame, text="Chọn thư mục", command=self.select_video_folder).grid(row=row, column=2, padx=(5, 0), pady=5)
        row += 1        # Overlay configuration
        overlay_frame = ttk.Frame(main_frame)
        overlay_frame.grid(row=row, column=0, columnspan=3, pady=(10, 10), sticky=(tk.W, tk.E))
        
        ttk.Button(overlay_frame, text="⏰ Cấu hình thời gian Overlay Ảnh", command=self.configure_overlay_timing).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(overlay_frame, text="🎬 Cấu hình Video Overlay + Chroma Key", command=self.configure_video_overlay).pack(side=tk.LEFT, padx=(0, 10))
        row += 1
        
        # Status labels
        self.timing_status = ttk.Label(main_frame, text="Chưa cấu hình overlay ảnh", foreground="gray")
        self.timing_status.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=2)
        row += 1
        
        self.video_overlay_status = ttk.Label(main_frame, text="Chưa cấu hình video overlay", foreground="gray")
        self.video_overlay_status.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=2)
        row += 1
          # Process button
        self.process_button = ttk.Button(
            main_frame,
            text="🚀 Bắt đầu xử lý (Phụ đề + Ảnh + Video Overlay + 9:16)",
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
        self.status_label = ttk.Label(main_frame, text="Sẵn sàng xử lý")
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
        self.log_message("🎬 GUI Video Overlay đã sẵn sàng!")
        self.log_message("💡 Hướng dẫn: Chọn video, cấu hình overlay, bắt đầu xử lý")

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
    
    def select_img_folder(self):
        """Chọn thư mục chứa ảnh overlay"""
        folder_path = filedialog.askdirectory(
            title="Chọn thư mục chứa ảnh overlay"
        )
        if folder_path:
            self.img_folder_path.set(folder_path)
            self.log_message(f" Đã chọn thư mục ảnh: {folder_path}")
            
            # Kiểm tra và hiển thị file ảnh
            image_files = []
            for ext in ['*.png', '*.jpg', '*.jpeg', '*.gif', '*.bmp']:
                image_files.extend(glob.glob(os.path.join(folder_path, ext)))
            
            if image_files:
                self.log_message(f"🖼️ Tìm thấy {len(image_files)} ảnh: {[os.path.basename(f) for f in image_files]}")
            else:
                self.log_message("⚠️ Không tìm thấy ảnh nào trong thư mục")
        else:
            # FIX: Nếu user cancel dialog, clear folder path
            self.img_folder_path.set("")
            self.log_message("❌ Đã hủy chọn thư mục ảnh")
    
    def select_video_folder(self):
        """Chọn thư mục chứa video overlay"""
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
                self.log_message(f" Tìm thấy {len(video_files)} file video: {[os.path.basename(f) for f in video_files]}")
            else:
                self.log_message(" Không tìm thấy file video nào trong thư mục")

    def configure_overlay_timing(self):
        """Cấu hình thời gian overlay ảnh"""
        if not self.img_folder_path.get():
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn thư mục ảnh trước!")
            return
            
        # Tìm file ảnh trong thư mục
        img_files = []
        folder_path = self.img_folder_path.get()
        
        for ext in ['*.png', '*.jpg', '*.jpeg', '*.gif', '*.bmp']:
            img_files.extend(glob.glob(os.path.join(folder_path, ext)))
        
        if not img_files:
            messagebox.showwarning("Cảnh báo", "Không tìm thấy file ảnh nào trong thư mục!")
            return
        self.show_overlay_timing_dialog(img_files)
    
    def show_overlay_timing_dialog(self, img_files):
        """Dialog cấu hình thời gian overlay ảnh với animation"""
        dialog = tk.Toplevel(self.root)
        dialog.title(" Cấu hình Overlay Ảnh + Animation")
        dialog.geometry("700x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="🎬 Cấu hình thời gian và animation cho từng ảnh:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 10))
        
        # Scrollable frame
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Header
        header_frame = ttk.Frame(scrollable_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header_frame, text="Ảnh", width=20).grid(row=0, column=0, padx=5)
        ttk.Label(header_frame, text="Bắt đầu(s)", width=10).grid(row=0, column=1, padx=5)
        ttk.Label(header_frame, text="Thời lượng(s)", width=10).grid(row=0, column=2, padx=5)
        ttk.Label(header_frame, text="Vị trí", width=12).grid(row=0, column=3, padx=5)
        ttk.Label(header_frame, text="Animation", width=12).grid(row=0, column=4, padx=5)
        ttk.Label(header_frame, text="Thời gian Anim(s)", width=10).grid(row=0, column=5, padx=5)
        
        # Tạo entry cho mỗi file ảnh
        entries = {}
        animations = {}
        for i, img_file in enumerate(img_files):
            filename = os.path.basename(img_file)
            
            frame = ttk.Frame(scrollable_frame)
            frame.pack(fill=tk.X, pady=2)
            
            # Tên file
            ttk.Label(frame, text=f"🖼️ {filename[:15]}...", width=20).grid(row=0, column=0, padx=5, sticky=tk.W)
            
            # Thời gian bắt đầu
            start_var = tk.StringVar(value=str(i * 3))
            start_entry = ttk.Entry(frame, textvariable=start_var, width=8)
            start_entry.grid(row=0, column=1, padx=5)
            
            # Thời lượng
            duration_var = tk.StringVar(value="4")
            duration_entry = ttk.Entry(frame, textvariable=duration_var, width=8)
            duration_entry.grid(row=0, column=2, padx=5)
            
            # Vị trí
            position_var = tk.StringVar(value="center")
            position_combo = ttk.Combobox(frame, textvariable=position_var, 
                                        values=["center", "top-left", "top-right", "bottom-left", "bottom-right"], 
                                        state="readonly", width=10)
            position_combo.grid(row=0, column=3, padx=5)
            
            # Animation type
            animation_var = tk.StringVar(value="fade_in_out")
            animation_combo = ttk.Combobox(frame, textvariable=animation_var,
                                         values=["fade_in", "fade_out", "fade_in_out", "slide_left", "slide_right", 
                                                "slide_up", "slide_down", "zoom_in", "zoom_out", "rotate_in", 
                                                "bounce", "pulse"],
                                         state="readonly", width=10)
            animation_combo.grid(row=0, column=4, padx=5)
            
            # Animation duration
            anim_duration_var = tk.StringVar(value="1.0")
            anim_duration_entry = ttk.Entry(frame, textvariable=anim_duration_var, width=8)
            anim_duration_entry.grid(row=0, column=5, padx=5)
            
            entries[filename] = {
                'start': start_var, 
                'duration': duration_var,
                'position': position_var
            }
            animations[filename] = {
                'type': animation_var,
                'duration': anim_duration_var
            }
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Quick presets
        preset_frame = ttk.LabelFrame(main_frame, text="🎭 Presets nhanh", padding="10")
        preset_frame.pack(fill=tk.X, pady=(10, 0))
        
        def apply_preset(preset_type):
            if preset_type == "fade_sequence":
                for i, (filename, vars) in enumerate(entries.items()):
                    vars['start'].set(str(i * 3))
                    vars['duration'].set("4")
                    vars['position'].set("center")
                    animations[filename]['type'].set("fade_in_out")
                    animations[filename]['duration'].set("1.0")
            
            elif preset_type == "slide_show":
                positions = ["top-left", "top-right", "bottom-left", "bottom-right", "center"]
                slides = ["slide_left", "slide_right", "slide_up", "slide_down", "zoom_in"]
                for i, (filename, vars) in enumerate(entries.items()):
                    vars['start'].set(str(i * 4))
                    vars['duration'].set("5")
                    vars['position'].set(positions[i % len(positions)])
                    animations[filename]['type'].set(slides[i % len(slides)])
                    animations[filename]['duration'].set("1.5")
            
            elif preset_type == "zoom_burst":
                for i, (filename, vars) in enumerate(entries.items()):
                    vars['start'].set(str(i * 2))
                    vars['duration'].set("3")
                    vars['position'].set("center")
                    animations[filename]['type'].set("zoom_in")
                    animations[filename]['duration'].set("0.8")
        
        ttk.Button(preset_frame, text="🌊 Fade Sequence", command=lambda: apply_preset("fade_sequence")).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(preset_frame, text="🎢 Slide Show", command=lambda: apply_preset("slide_show")).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(preset_frame, text="💥 Zoom Burst", command=lambda: apply_preset("zoom_burst")).pack(side=tk.LEFT)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        def save_timing():
            try:
                timing = {}
                anim_config = {}
                for filename, vars in entries.items():
                    start = float(vars['start'].get())
                    duration = float(vars['duration'].get())
                    position = vars['position'].get()
                    
                    timing[filename] = {
                        'start': start, 
                        'duration': duration,
                        'position': position,
                        'scale': 0.3  # Kích thước mặc định
                    }
                    
                    anim_config[filename] = {
                        'type': animations[filename]['type'].get(),
                        'duration': float(animations[filename]['duration'].get())
                    }
                
                self.overlay_times = timing
                self.animation_config = anim_config  # Lưu cấu hình animation
                
                self.timing_status.config(text=f"✅ Đã cấu hình {len(timing)} ảnh với animation", foreground="green")
                self.log_message(f"✨ Đã cấu hình {len(timing)} ảnh overlay với animation")
                for filename in timing:
                    anim_type = anim_config[filename]['type']
                    self.log_message(f"   🖼️ {filename}: {anim_type}")
                dialog.destroy()
                
            except ValueError:
                messagebox.showerror("Lỗi", "Vui lòng nhập số hợp lệ cho thời gian!")
        
        ttk.Button(button_frame, text="✅ Lưu cấu hình", command=save_timing).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="❌ Hủy", command=dialog.destroy).pack(side=tk.RIGHT)

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
        """Dialog cấu hình video overlay với giao diện động"""
        
        dialog = tk.Toplevel(self.root)
        dialog.title("🎬 Cấu hình Video Overlay + Chroma Key")
        dialog.geometry("600x800")
        dialog.transient(self.root)
        dialog.grab_set()
        
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # --- Các biến control ---
        video_var = tk.StringVar()
        start_var = tk.StringVar(value="2")
        duration_var = tk.StringVar(value="10")
        
        # Position settings
        position_mode_var = tk.StringVar(value="preset")
        position_preset_var = tk.StringVar(value="top-right")
        custom_x_var = tk.StringVar(value="300")
        custom_y_var = tk.StringVar(value="1600")
        
        # Size settings  
        size_mode_var = tk.StringVar(value="percentage")
        size_percent_var = tk.StringVar(value="25")
        custom_width_var = tk.StringVar(value="500")
        custom_height_var = tk.StringVar(value="600")
        
        # Chroma settings
        chroma_enabled_var = tk.BooleanVar(value=True)
        chroma_color_var = tk.StringVar(value="green")
        advanced_mode_var = tk.BooleanVar(value=False)
        auto_hide_var = tk.BooleanVar(value=True)
        
        # Advanced controls - sử dụng StringVar thay vì DoubleVar để user nhập trực tiếp
        custom_similarity_var = tk.StringVar(value="0.200")
        custom_blend_var = tk.StringVar(value="0.150")

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
        
        ttk.Radiobutton(mode_frame, text="Vị trí mặc định", variable=position_mode_var, 
                    value="preset").pack(side=tk.LEFT, padx=(0, 20))
        ttk.Radiobutton(mode_frame, text="Tùy chỉnh X,Y", variable=position_mode_var, 
                    value="custom").pack(side=tk.LEFT)
        
        # Container for dynamic position controls
        position_controls_frame = ttk.Frame(position_frame)
        position_controls_frame.pack(fill=tk.X, pady=5)
        
        # Preset positions frame
        preset_frame = ttk.Frame(position_controls_frame)
        ttk.Label(preset_frame, text="Vị trí:").pack(side=tk.LEFT)
        position_combo = ttk.Combobox(preset_frame, textvariable=position_preset_var, 
                                    values=["center", "top-left", "top-right", "bottom-left", "bottom-right"], 
                                    state="readonly", width=15)
        position_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # Custom position frame
        custom_pos_frame = ttk.Frame(position_controls_frame)
        ttk.Label(custom_pos_frame, text="X:").pack(side=tk.LEFT)
        ttk.Entry(custom_pos_frame, textvariable=custom_x_var, width=8).pack(side=tk.LEFT, padx=(5, 15))
        ttk.Label(custom_pos_frame, text="Y:").pack(side=tk.LEFT)
        ttk.Entry(custom_pos_frame, textvariable=custom_y_var, width=8).pack(side=tk.LEFT, padx=(5, 15))
        ttk.Label(custom_pos_frame, text="(mặc định: X=300, Y=1600)", 
                font=("Arial", 8), foreground="gray").pack(side=tk.LEFT)

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
                custom_blend_var.set("0.100")
        
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
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
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
                
                # Update status message
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
                "loose": (0.3, 0.25),
                "normal": (0.15, 0.1),
                "custom": (0.2, 0.15),  # Green optimized
                "strict": (0.08, 0.05),
                "very_strict": (0.03, 0.02),
                "ultra_strict": (0.01, 0.005)
            },
            "black": {
                "loose": (0.05, 0.03),
                "normal": (0.02, 0.015),
                "custom": (0.01, 0.005),  # Black precision
                "strict": (0.005, 0.003),
                "very_strict": (0.001, 0.001),
                "ultra_strict": (0.0005, 0.0005)
            },
            "blue": {
                "loose": (0.35, 0.3),
                "normal": (0.2, 0.15),
                "custom": (0.25, 0.2),   # Blue optimized
                "strict": (0.1, 0.08),
                "very_strict": (0.05, 0.03),
                "ultra_strict": (0.02, 0.01)
            },
            "cyan": {
                "loose": (0.25, 0.2),
                "normal": (0.12, 0.08),
                "custom": (0.15, 0.1),   # Cyan optimized
                "strict": (0.06, 0.04),
                "very_strict": (0.03, 0.02),
                "ultra_strict": (0.01, 0.005)
            },
            "red": {
                "loose": (0.4, 0.35),
                "normal": (0.25, 0.2),
                "custom": (0.3, 0.25),   # Red optimized (harder to key)
                "strict": (0.15, 0.1),
                "very_strict": (0.08, 0.05),
                "ultra_strict": (0.03, 0.02)
            },
            "magenta": {
                "loose": (0.3, 0.25),
                "normal": (0.18, 0.12),
                "custom": (0.22, 0.18),  # Magenta optimized
                "strict": (0.1, 0.08),
                "very_strict": (0.05, 0.03),
                "ultra_strict": (0.02, 0.01)
            },
            "yellow": {
                "loose": (0.35, 0.3),
                "normal": (0.22, 0.18),
                "custom": (0.28, 0.22),  # Yellow optimized (skin tone conflict)
                "strict": (0.12, 0.1),
                "very_strict": (0.06, 0.04),
                "ultra_strict": (0.03, 0.02)
            }
        }
        
        # Default fallback cho màu khác
        default_settings = {
            "loose": (0.3, 0.25),
            "normal": (0.15, 0.1),
            "custom": (0.2, 0.15),
            "strict": (0.05, 0.03),
            "very_strict": (0.01, 0.005),
            "ultra_strict": (0.005, 0.003)
        }
        
        color_map = color_settings.get(color.lower(), default_settings)
        return color_map.get(preset.lower(), (0.2, 0.15))

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
        """Bắt đầu xử lý video với các tuỳ chọn hiện tại"""
        try:
            # Lấy thông tin từ GUI
            input_video_path = self.input_video_path.get()
            output_video_path = self.output_video_path.get()
            source_language = self.source_language.get()
            target_language = self.target_language.get()
            
            # FIX: Kiểm tra thư mục ảnh có được chọn thực sự không
            img_folder_raw = self.img_folder_path.get().strip()
            img_folder = img_folder_raw if img_folder_raw and os.path.exists(img_folder_raw) else None
            
            video_overlay_settings = self.video_overlay_settings
            overlay_times = self.overlay_times if self.overlay_times else None
            words_per_line = self.words_per_line.get()

            # Kiểm tra đầu vào
            if not input_video_path or not output_video_path:
                messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn file video đầu vào và vị trí lưu file đầu ra.")
                return

            # Log thông tin xử lý
            print(" Cấu hình xử lý:")
            print(f"    Video input: {input_video_path}")
            print(f"    Video output: {output_video_path}")
            print(f"    Ngôn ngữ: {source_language} → {target_language}")
            
            if img_folder:
                print(f"    Thư mục ảnh: {img_folder}")
                if overlay_times:
                    print(f"    Overlay times: {len(overlay_times)} ảnh")
                else:
                    print(f"    Không có cấu hình overlay times")
            else:
                print(f"    Không sử dụng ảnh overlay")
                
            if video_overlay_settings and video_overlay_settings.get('enabled', False):
                print(f"    Video overlay: Có")
            else:
                print(f"    Video overlay: Không")

            self.status_label.config(text=" Đang xử lý... Vui lòng chờ.")
            self.progress_var.set(0)
            self.progress_bar.start()

            # Thực hiện xử lý trong thread riêng
            def worker():
                try:
                    self.log_message(" Bắt đầu xử lý video tự động...")
                    editor = AutoVideoEditor()
                    editor.process_video(
                        input_video_path=input_video_path,
                        output_video_path=output_video_path,
                        source_language=source_language,
                        target_language=target_language,
                        img_folder=img_folder,  # Có thể là None
                        overlay_times=overlay_times,
                        video_overlay_settings=video_overlay_settings,
                        words_per_line=words_per_line
                    )
                    self.status_label.config(text=" Hoàn thành!")
                    self.log_message(" Xử lý xong! File kết quả đã lưu.")
                except Exception as e:
                    self.status_label.config(text=" Lỗi xử lý!")
                    self.log_message(f" Lỗi: {e}")
                    import traceback
                    self.log_message(f"Chi tiết lỗi: {traceback.format_exc()}")
                finally:
                    self.progress_bar.stop()
                    self.progress_var.set(0)

            threading.Thread(target=worker, daemon=True).start()

        except Exception as e:
            self.status_label.config(text=" Lỗi xử lý!")
            self.log_message(f" Lỗi: {e}")


def main():
    root = tk.Tk()
    app = VideoEditorGUI(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
