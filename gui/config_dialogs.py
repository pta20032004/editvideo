#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration Dialogs Module
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import glob

class OverlayConfigDialog:
    """Dialog cấu hình overlay ảnh"""
    
    def __init__(self, parent, img_folder):
        self.parent = parent
        self.img_folder = img_folder
        self.result = None
        self.overlay_configs = {}
        
        self.show_dialog()
        
    def show_dialog(self):
        """Hiển thị dialog cấu hình"""
        # Tìm file ảnh
        img_files = []
        for ext in ['*.png', '*.jpg', '*.jpeg', '*.gif', '*.bmp']:
            img_files.extend(glob.glob(os.path.join(self.img_folder, ext)))
        
        if not img_files:
            messagebox.showwarning("Cảnh báo", "Không tìm thấy file ảnh nào trong thư mục!")
            return
        
        # Tạo dialog
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("⏰✨ Cấu hình Overlay Ảnh")
        self.dialog.geometry("800x600")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.geometry("+%d+%d" % (
            self.parent.winfo_rootx() + 50, 
            self.parent.winfo_rooty() + 50
        ))
        
        self._create_dialog_content(img_files)
        
    def _create_dialog_content(self, img_files):
        """Tạo nội dung dialog"""
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            main_frame, 
            text="⏰ Cấu hình thời gian hiển thị cho từng ảnh",
            font=("Arial", 14, "bold")
        )
        title_label.pack(pady=(0, 20))
        
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
        
        # Create config for each image
        for i, img_file in enumerate(img_files):
            self._create_image_config(scrollable_frame, img_file, i)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Button(button_frame, text="Hủy", command=self.cancel).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(button_frame, text="OK", command=self.ok).pack(side=tk.RIGHT)
        
    def _create_image_config(self, parent, img_file, index):
        """Tạo cấu hình cho một ảnh"""
        img_name = os.path.basename(img_file)
        
        # Frame cho mỗi ảnh
        img_frame = ttk.LabelFrame(parent, text=f"🖼️ {img_name}", padding="10")
        img_frame.pack(fill=tk.X, pady=5)
        
        # Tạo variables
        start_time_var = tk.DoubleVar(value=index * 2)
        end_time_var = tk.DoubleVar(value=(index + 1) * 2)
        x_pos_var = tk.StringVar(value="center")
        y_pos_var = tk.IntVar(value=100)
        scale_var = tk.DoubleVar(value=1.0)
        animation_var = tk.StringVar(value="fade_in_out")
        
        # Time controls
        time_frame = ttk.Frame(img_frame)
        time_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(time_frame, text="⏰ Thời gian:").pack(side=tk.LEFT)
        ttk.Label(time_frame, text="Bắt đầu:").pack(side=tk.LEFT, padx=(20, 5))
        start_spin = ttk.Spinbox(time_frame, from_=0, to=300, increment=0.5, width=8, textvariable=start_time_var)
        start_spin.pack(side=tk.LEFT)
        
        ttk.Label(time_frame, text="Kết thúc:").pack(side=tk.LEFT, padx=(10, 5))
        end_spin = ttk.Spinbox(time_frame, from_=0, to=300, increment=0.5, width=8, textvariable=end_time_var)
        end_spin.pack(side=tk.LEFT)
        
        # Position controls  
        pos_frame = ttk.Frame(img_frame)
        pos_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(pos_frame, text="📍 Vị trí:").pack(side=tk.LEFT)
        ttk.Label(pos_frame, text="X:").pack(side=tk.LEFT, padx=(20, 5))
        x_combo = ttk.Combobox(pos_frame, textvariable=x_pos_var, values=["left", "center", "right"], width=8)
        x_combo.pack(side=tk.LEFT)
        
        ttk.Label(pos_frame, text="Y:").pack(side=tk.LEFT, padx=(10, 5))
        y_spin = ttk.Spinbox(pos_frame, from_=0, to=2000, increment=10, width=8, textvariable=y_pos_var)
        y_spin.pack(side=tk.LEFT)
        
        # Scale and animation
        extra_frame = ttk.Frame(img_frame)
        extra_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(extra_frame, text="📏 Scale:").pack(side=tk.LEFT)
        scale_spin = ttk.Spinbox(extra_frame, from_=0.1, to=3.0, increment=0.1, width=8, textvariable=scale_var)
        scale_spin.pack(side=tk.LEFT, padx=(5, 20))
        
        ttk.Label(extra_frame, text="🎭 Animation:").pack(side=tk.LEFT)
        anim_combo = ttk.Combobox(
            extra_frame, 
            textvariable=animation_var,
            values=["fade_in_out", "slide_left", "slide_right", "zoom_in", "zoom_out", "pulse"],
            width=12
        )
        anim_combo.pack(side=tk.LEFT, padx=(5, 0))
        
        # Store variables
        self.overlay_configs[img_name] = {
            'start_time': start_time_var,
            'end_time': end_time_var,
            'x_position': x_pos_var,
            'y_position': y_pos_var,
            'scale': scale_var,
            'animation': animation_var
        }
        
    def ok(self):
        """Xác nhận cấu hình"""
        result = {}
        for img_name, config in self.overlay_configs.items():
            result[img_name] = {
                'start_time': config['start_time'].get(),
                'end_time': config['end_time'].get(),
                'x_position': config['x_position'].get(),
                'y_position': config['y_position'].get(),
                'scale': config['scale'].get(),
                'animation': config['animation'].get()
            }
        
        self.result = result
        self.dialog.destroy()
        
    def cancel(self):
        """Hủy cấu hình"""
        self.dialog.destroy()

class VideoOverlayConfigDialog:
    """Dialog cấu hình video overlay"""
    
    def __init__(self, parent, video_folder):
        self.parent = parent
        self.video_folder = video_folder
        self.result = None
        
        self.show_dialog()
        
    def show_dialog(self):
        """Hiển thị dialog cấu hình video overlay"""
        # Tìm file video
        video_files = []
        for ext in ['*.mp4', '*.avi', '*.mov', '*.mkv']:
            video_files.extend(glob.glob(os.path.join(self.video_folder, ext)))
        
        if not video_files:
            messagebox.showwarning("Cảnh báo", "Không tìm thấy file video nào trong thư mục!")
            return
        
        # Tạo dialog
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("🎬 Cấu hình Video Overlay")
        self.dialog.geometry("600x500")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.geometry("+%d+%d" % (
            self.parent.winfo_rootx() + 50, 
            self.parent.winfo_rooty() + 50
        ))
        
        self._create_video_dialog_content(video_files)
        
    def _create_video_dialog_content(self, video_files):
        """Tạo nội dung dialog video overlay"""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            main_frame, 
            text="🎬 Cấu hình Video Overlay + Chroma Key",
            font=("Arial", 14, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Enable checkbox
        self.enabled_var = tk.BooleanVar()
        ttk.Checkbutton(main_frame, text="✅ Bật Video Overlay", variable=self.enabled_var).pack(anchor=tk.W, pady=5)
        
        # Video selection
        ttk.Label(main_frame, text="📹 Chọn video overlay:").pack(anchor=tk.W, pady=(10, 5))
        self.video_var = tk.StringVar()
        video_combo = ttk.Combobox(main_frame, textvariable=self.video_var, values=[os.path.basename(f) for f in video_files])
        video_combo.pack(fill=tk.X, pady=5)
        
        # Timing
        timing_frame = ttk.LabelFrame(main_frame, text="⏰ Thời gian", padding="10")
        timing_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(timing_frame, text="Bắt đầu (giây):").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.start_time_var = tk.DoubleVar(value=0)
        ttk.Spinbox(timing_frame, from_=0, to=300, increment=0.5, textvariable=self.start_time_var).grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(timing_frame, text="Thời lượng (giây):").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        self.duration_var = tk.DoubleVar(value=5)
        ttk.Spinbox(timing_frame, from_=0.1, to=300, increment=0.5, textvariable=self.duration_var).grid(row=1, column=1, sticky=tk.W, pady=(5, 0))
        
        # Position and size
        pos_frame = ttk.LabelFrame(main_frame, text="📍 Vị trí & Kích thước", padding="10")
        pos_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(pos_frame, text="Vị trí:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.position_var = tk.StringVar(value="top-right")
        pos_combo = ttk.Combobox(pos_frame, textvariable=self.position_var, 
                                values=["top-left", "top-right", "bottom-left", "bottom-right", "center"])
        pos_combo.grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(pos_frame, text="Kích thước (%):").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        self.size_var = tk.IntVar(value=25)
        ttk.Spinbox(pos_frame, from_=5, to=100, increment=5, textvariable=self.size_var).grid(row=1, column=1, sticky=tk.W, pady=(5, 0))
        
        # Chroma key
        chroma_frame = ttk.LabelFrame(main_frame, text="🎨 Chroma Key", padding="10")
        chroma_frame.pack(fill=tk.X, pady=10)
        
        self.chroma_enabled_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(chroma_frame, text="Bật Chroma Key", variable=self.chroma_enabled_var).grid(row=0, column=0, columnspan=2, sticky=tk.W)
        
        ttk.Label(chroma_frame, text="Màu:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        self.chroma_color_var = tk.StringVar(value="green")
        chroma_combo = ttk.Combobox(chroma_frame, textvariable=self.chroma_color_var,
                                   values=["green", "blue", "red", "cyan", "magenta", "yellow"])
        chroma_combo.grid(row=1, column=1, sticky=tk.W, pady=(5, 0))
        
        ttk.Label(chroma_frame, text="Độ nhạy:").grid(row=2, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        self.chroma_sensitivity_var = tk.StringVar(value="custom")
        sens_combo = ttk.Combobox(chroma_frame, textvariable=self.chroma_sensitivity_var,
                                 values=["loose", "normal", "strict", "very_strict"])
        sens_combo.grid(row=2, column=1, sticky=tk.W, pady=(5, 0))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Button(button_frame, text="Hủy", command=self.cancel).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(button_frame, text="OK", command=self.ok).pack(side=tk.RIGHT)
        
    def ok(self):
        """Xác nhận cấu hình video overlay"""
        if self.enabled_var.get() and not self.video_var.get():
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn video overlay!")
            return
        
        self.result = {
            'enabled': self.enabled_var.get(),
            'video_path': os.path.join(self.video_folder, self.video_var.get()) if self.video_var.get() else None,
            'start_time': self.start_time_var.get(),
            'duration': self.duration_var.get(),
            'position': self.position_var.get(),
            'size_percent': self.size_var.get(),
            'chroma_key': self.chroma_enabled_var.get(),
            'chroma_color': self.chroma_color_var.get(),
            'chroma_sensitivity': self.chroma_sensitivity_var.get()
        }
        
        self.dialog.destroy()
        
    def cancel(self):
        """Hủy cấu hình"""
        self.dialog.destroy()

class AnimationConfigDialog:
    """Dialog cấu hình animation (dự phòng cho tương lai)"""
    
    def __init__(self, parent):
        self.parent = parent
        self.result = None
        messagebox.showinfo("Thông tin", "Chức năng này sẽ được phát triển trong tương lai!")
