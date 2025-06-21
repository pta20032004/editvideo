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
            
    def select_img_folder(self):
        """Chọn thư mục chứa ảnh overlay"""
        folder = filedialog.askdirectory(title="Chọn thư mục ảnh overlay")
        if folder:
            self.img_folder_path.set(folder)
            
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
        
    # Processing methods
    def start_processing(self):
        """Bắt đầu xử lý video"""
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
        
        # Start processing
        self.processing = True
        self.progress_bar.start()
        self.process_button.config(state="disabled")
        
        thread = threading.Thread(target=self.process_video_thread)
        thread.daemon = True
        thread.start()
        
    def process_video_thread(self):
        """Thread xử lý video"""
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
                words_per_line=self.words_per_line.get()
            )
            
            self.update_status("✅ Xử lý hoàn thành!")
            self.log_message("🎉 Xử lý video thành công!")
            messagebox.showinfo("Thành công", f"Video đã được lưu tại:\\n{self.output_video_path.get()}")
            
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
