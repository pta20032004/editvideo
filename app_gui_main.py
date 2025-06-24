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
        self.img_folder_path = tk.StringVar(value="img")
        self.video_folder_path = tk.StringVar(value="videoinput")
        self.words_per_line = tk.IntVar(value=7)  # Số từ mỗi dòng phụ đề
        self.processing = False
          # Overlay settings
        self.overlay_times = {}
        self.animation_config = {}  # Cấu hình animation cho ảnh
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
            title="Chọn thư mục chứa ảnh overlay",
            initialdir=self.img_folder_path.get() if self.img_folder_path.get() else "."
        )
        if folder_path:
            self.img_folder_path.set(folder_path)
            self.log_message(f"📁 Đã chọn thư mục ảnh: {folder_path}")
    
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
                self.log_message(f"🎬 Tìm thấy {len(video_files)} file video: {[os.path.basename(f) for f in video_files]}")
            else:
                self.log_message("⚠️ Không tìm thấy file video nào trong thư mục")

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
        dialog.title("⏰✨ Cấu hình Overlay Ảnh + Animation")
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
        """Dialog cấu hình video overlay"""
        
        dialog = tk.Toplevel(self.root)
        dialog.title("🎬 Cấu hình Video Overlay + Chroma Key")
        dialog.geometry("550x600")
        dialog.transient(self.root)
        dialog.grab_set()
        
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # --- Các biến control ---
        video_var = tk.StringVar()
        start_var = tk.StringVar(value="2")
        duration_var = tk.StringVar(value="10")
        position_var = tk.StringVar(value="top-right")
        size_var = tk.StringVar(value="25")
        chroma_enabled_var = tk.BooleanVar(value=True)
        chroma_color_var = tk.StringVar(value="no select")
        sensitivity_var = tk.StringVar(value="no select")

        # --- Nạp lại cấu hình đã lưu nếu có ---
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
            if prev.get('position'):
                position_var.set(prev['position'])
            if prev.get('size_percent') is not None:
                size_var.set(str(prev['size_percent']))
            if prev.get('chroma_key') is not None:
                chroma_enabled_var.set(prev['chroma_key'])
            if prev.get('chroma_color'):
                chroma_color_var.set(prev['chroma_color'])
            if prev.get('chroma_sensitivity'):
                sensitivity_var.set(prev['chroma_sensitivity'])

        # --- Widgets ---
        ttk.Label(main_frame, text="🎭 Chọn video overlay:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        video_combo = ttk.Combobox(main_frame, textvariable=video_var, 
                                values=[os.path.basename(f) for f in video_files], 
                                state="readonly")
        video_combo.pack(fill=tk.X, pady=(0, 10))
        if video_var.get() == "" and video_files:
            video_combo.current(0)

        timing_frame = ttk.LabelFrame(main_frame, text="⏰ Thời gian", padding="10")
        timing_frame.pack(fill=tk.X, pady=(0, 10))
        timing_grid = ttk.Frame(timing_frame)
        timing_grid.pack(fill=tk.X)
        ttk.Label(timing_grid, text="Bắt đầu (giây):").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(timing_grid, textvariable=start_var, width=10).grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        ttk.Label(timing_grid, text="Thời lượng (giây):").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Entry(timing_grid, textvariable=duration_var, width=10).grid(row=1, column=1, sticky=tk.W, padx=(10, 0))
        
        layout_frame = ttk.LabelFrame(main_frame, text="📍 Vị trí & Kích thước", padding="10")
        layout_frame.pack(fill=tk.X, pady=(0, 10))
        layout_grid = ttk.Frame(layout_frame)
        layout_grid.pack(fill=tk.X)
        ttk.Label(layout_grid, text="Vị trí:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Combobox(layout_grid, textvariable=position_var, 
                    values=["center", "top-left", "top-right", "bottom-left", "bottom-right"], 
                    state="readonly", width=15).grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        ttk.Label(layout_grid, text="Kích thước (% chiều cao):").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Entry(layout_grid, textvariable=size_var, width=10).grid(row=1, column=1, sticky=tk.W, padx=(10, 0))
        
        chroma_frame = ttk.LabelFrame(main_frame, text="🔥 Chroma Key", padding="10")
        chroma_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Checkbutton(chroma_frame, text="Bật chroma key (xóa nền)", variable=chroma_enabled_var).pack(anchor=tk.W)
        chroma_grid = ttk.Frame(chroma_frame)
        chroma_grid.pack(fill=tk.X, pady=(5, 0))
        ttk.Label(chroma_grid, text="Màu nền:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Combobox(chroma_grid, textvariable=chroma_color_var,
                    values=["green", "blue", "cyan", "red", "magenta", "black", "yellow"],
                    state="readonly", width=10).grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        ttk.Label(chroma_grid, text="Độ nhạy:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Combobox(chroma_grid, textvariable=sensitivity_var,
                    values=["loose", "normal", "strict", "very_strict (Black)", "ultra_strict", "custom (Green)"],
                    state="readonly", width=12).grid(row=1, column=1, sticky=tk.W, padx=(10, 0))
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        def save_video_overlay():
            try:
                selected_video = video_var.get()
                if not selected_video:
                    messagebox.showerror("Lỗi", "Vui lòng chọn video!")
                    return
                # Tìm đường dẫn video gốc từ tên file
                video_path = None
                for f in video_files:
                    if os.path.basename(f) == selected_video:
                        video_path = f
                        break
                start_time = float(start_var.get())
                duration = float(duration_var.get()) if duration_var.get().strip() else None
                size = int(size_var.get())
                self.video_overlay_settings = {
                    'enabled': True,
                    'video_path': video_path,
                    'start_time': start_time,
                    'duration': duration,
                    'position': position_var.get(),
                    'size_percent': size,
                    'chroma_key': chroma_enabled_var.get(),
                    'chroma_color': chroma_color_var.get(),
                    'chroma_sensitivity': sensitivity_var.get()
                }
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Lỗi", f"Giá trị không hợp lệ: {e}")

        ttk.Button(button_frame, text="✅ Lưu", command=save_video_overlay).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="❌ Hủy", command=dialog.destroy).pack(side=tk.RIGHT)


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
            img_folder = self.img_folder_path.get()
            video_overlay_settings = self.video_overlay_settings
            overlay_times = self.overlay_times if self.overlay_times else None
            words_per_line = self.words_per_line.get()

            # Kiểm tra đầu vào
            if not input_video_path or not output_video_path:
                messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn file video đầu vào và vị trí lưu file đầu ra.")
                return

            # --- BỔ SUNG LOGIC TỰ ĐỘNG ÁP DỤNG CHROMA CUSTOM ---
            if not video_overlay_settings or not video_overlay_settings.get('enabled', False):
                # Có thể chỉ định sẵn một video overlay mặc định nếu muốn, hoặc để None
                self.video_overlay_settings = {
                    'enabled': True,
                    'video_path': None,       # Nếu muốn mặc định là None, hoặc chỉ định path overlay video
                    'start_time': 2,
                    'duration': 8,
                    'position': 'top-right',
                    'size_percent': 25,
                    'chroma_key': True,
                    'chroma_color': 'green',
                    'chroma_sensitivity': 'custom'
                }
                video_overlay_settings = self.video_overlay_settings
            # --- END ---

            self.status_label.config(text="⏳ Đang xử lý... Vui lòng chờ.")
            self.progress_var.set(0)
            self.progress_bar.start()

            # Thực hiện xử lý trong thread riêng để không block GUI
            def worker():
                try:
                    self.log_message("🚀 Bắt đầu xử lý video tự động...")
                    editor = AutoVideoEditor()  # import ở đầu file: from main import AutoVideoEditor
                    editor.process_video(
                        input_video_path=input_video_path,
                        output_video_path=output_video_path,
                        source_language=source_language,
                        target_language=target_language,
                        img_folder=img_folder,
                        overlay_times=overlay_times,
                        video_overlay_settings=video_overlay_settings,
                        words_per_line=words_per_line
                    )
                    self.status_label.config(text="✅ Hoàn thành!")
                    self.log_message("✅ Xử lý xong! File kết quả đã lưu.")
                except Exception as e:
                    self.status_label.config(text="❌ Lỗi xử lý!")
                    self.log_message(f"❌ Lỗi: {e}")
                finally:
                    self.progress_bar.stop()
                    self.progress_var.set(0)

            threading.Thread(target=worker, daemon=True).start()

        except Exception as e:
            self.status_label.config(text="❌ Lỗi xử lý!")
            self.log_message(f"❌ Lỗi: {e}")


def main():
    root = tk.Tk()
    app = VideoEditorGUI(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
