#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch GUI Module - Giao diện xử lý hàng loạt
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import time
from datetime import datetime
from .batch_processor import BatchProcessor, create_batch_config

class BatchProcessingGUI:
    """GUI cho batch processing"""
    
    def __init__(self, parent):
        self.parent = parent
        self.processor = None
        self.processing = False
        
        self.create_batch_window()
        
    def create_batch_window(self):
        """Tạo cửa sổ batch processing"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("🎬 Batch Processing - Xử lý hàng loạt Video")
        self.window.geometry("800x700")
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Center window
        self.window.geometry("+%d+%d" % (
            self.parent.winfo_rootx() + 50,
            self.parent.winfo_rooty() + 50
        ))
        
        self.create_widgets()
        
    def create_widgets(self):
        """Tạo các widget"""
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text="🎬 Batch Processing - Xử lý hàng loạt Video",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Input/Output section
        self.create_folder_selection(main_frame)
        
        # Configuration section
        self.create_config_section(main_frame)
        
        # Processing settings
        self.create_processing_settings(main_frame)
        
        # Progress section
        self.create_progress_section(main_frame)
        
        # Control buttons
        self.create_control_buttons(main_frame)
        
        # Results log
        self.create_results_section(main_frame)
        
    def create_folder_selection(self, parent):
        """Tạo phần chọn thư mục"""
        folder_frame = ttk.LabelFrame(parent, text="📁 Thư mục Input/Output", padding="10")
        folder_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Input folder
        ttk.Label(folder_frame, text="🎥 Thư mục video input:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.input_folder_var = tk.StringVar()
        input_entry = ttk.Entry(folder_frame, textvariable=self.input_folder_var, width=50)
        input_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=5)
        ttk.Button(folder_frame, text="Chọn", command=self.select_input_folder).grid(row=0, column=2, padx=(5, 0), pady=5)
        
        # Output folder
        ttk.Label(folder_frame, text="💾 Thư mục output:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.output_folder_var = tk.StringVar()
        output_entry = ttk.Entry(folder_frame, textvariable=self.output_folder_var, width=50)
        output_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=5)
        ttk.Button(folder_frame, text="Chọn", command=self.select_output_folder).grid(row=1, column=2, padx=(5, 0), pady=5)
        
        folder_frame.columnconfigure(1, weight=1)
        
    def create_config_section(self, parent):
        """Tạo phần cấu hình"""
        config_frame = ttk.LabelFrame(parent, text="⚙️ Cấu hình xử lý", padding="10")
        config_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Language settings
        lang_frame = ttk.Frame(config_frame)
        lang_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(lang_frame, text="🌐 Ngôn ngữ gốc:").pack(side=tk.LEFT)
        self.source_lang_var = tk.StringVar(value="vi")
        lang_combo = ttk.Combobox(
            lang_frame,
            textvariable=self.source_lang_var,
            values=["vi", "en", "ja", "ko", "zh", "es", "fr", "de"],
            state="readonly",
            width=10
        )
        lang_combo.pack(side=tk.LEFT, padx=(10, 20))
        
        ttk.Label(lang_frame, text="🎯 Ngôn ngữ đích:").pack(side=tk.LEFT)
        self.target_lang_var = tk.StringVar(value="en")
        target_combo = ttk.Combobox(
            lang_frame,
            textvariable=self.target_lang_var,
            values=["en", "vi", "ja", "ko", "zh", "es", "fr", "de"],
            state="readonly",
            width=10
        )
        target_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # Overlay settings
        overlay_frame = ttk.Frame(config_frame)
        overlay_frame.pack(fill=tk.X, pady=5)
        
        self.custom_timeline_var = tk.BooleanVar()
        ttk.Checkbutton(
            overlay_frame,
            text="🎯 Sử dụng Custom Timeline (3 ảnh)",
            variable=self.custom_timeline_var
        ).pack(side=tk.LEFT)
        
        # Image folder
        img_frame = ttk.Frame(config_frame)
        img_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(img_frame, text="🖼️ Thư mục ảnh overlay:").pack(side=tk.LEFT)
        self.img_folder_var = tk.StringVar()
        img_entry = ttk.Entry(img_frame, textvariable=self.img_folder_var, width=30)
        img_entry.pack(side=tk.LEFT, padx=(10, 5))
        ttk.Button(img_frame, text="Chọn", command=self.select_img_folder).pack(side=tk.LEFT)
        
    def create_processing_settings(self, parent):
        """Tạo phần cài đặt xử lý"""
        settings_frame = ttk.LabelFrame(parent, text="⚡ Cài đặt xử lý", padding="10")
        settings_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Workers count
        workers_frame = ttk.Frame(settings_frame)
        workers_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(workers_frame, text="👥 Số worker đồng thời:").pack(side=tk.LEFT)
        self.workers_var = tk.IntVar(value=3)
        workers_spin = ttk.Spinbox(
            workers_frame,
            from_=1, to=8, increment=1,
            textvariable=self.workers_var,
            width=10
        )
        workers_spin.pack(side=tk.LEFT, padx=(10, 20))
        
        ttk.Label(workers_frame, text="(Khuyến nghị: 2-4 workers)", foreground="gray").pack(side=tk.LEFT)
        
        # Video extensions
        ext_frame = ttk.Frame(settings_frame)
        ext_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(ext_frame, text="📼 Định dạng video:").pack(side=tk.LEFT)
        self.extensions_var = tk.StringVar(value=".mp4,.avi,.mov,.mkv")
        ext_entry = ttk.Entry(ext_frame, textvariable=self.extensions_var, width=30)
        ext_entry.pack(side=tk.LEFT, padx=(10, 0))
        
    def create_progress_section(self, parent):
        """Tạo phần hiển thị tiến độ"""
        progress_frame = ttk.LabelFrame(parent, text="📊 Tiến độ xử lý", padding="10")
        progress_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Status
        self.status_label = ttk.Label(progress_frame, text="Sẵn sàng", font=("Arial", 10, "bold"))
        self.status_label.pack(pady=5)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            length=400
        )
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # Statistics
        stats_frame = ttk.Frame(progress_frame)
        stats_frame.pack(fill=tk.X, pady=5)
        
        self.stats_labels = {}
        stats_info = [
            ("total", "📊 Tổng:"),
            ("completed", "✅ Hoàn thành:"),
            ("failed", "❌ Thất bại:"),
            ("remaining", "⏳ Còn lại:")
        ]
        
        for i, (key, text) in enumerate(stats_info):
            ttk.Label(stats_frame, text=text).grid(row=0, column=i*2, sticky=tk.W, padx=(0, 5))
            label = ttk.Label(stats_frame, text="0", font=("Arial", 10, "bold"))
            label.grid(row=0, column=i*2+1, sticky=tk.W, padx=(0, 20))
            self.stats_labels[key] = label
            
    def create_control_buttons(self, parent):
        """Tạo nút điều khiển"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.scan_button = ttk.Button(
            button_frame,
            text="🔍 Quét video",
            command=self.scan_videos
        )
        self.scan_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.start_button = ttk.Button(
            button_frame,
            text="🚀 Bắt đầu xử lý",
            command=self.start_processing,
            state="disabled"
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(
            button_frame,
            text="⏹️ Dừng",
            command=self.stop_processing,
            state="disabled"
        )
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.export_button = ttk.Button(
            button_frame,
            text="📄 Xuất báo cáo",
            command=self.export_report,
            state="disabled"
        )
        self.export_button.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="❌ Đóng", command=self.window.destroy).pack(side=tk.RIGHT)
        
    def create_results_section(self, parent):
        """Tạo phần hiển thị kết quả"""
        results_frame = ttk.LabelFrame(parent, text="📝 Log xử lý", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        # Text widget with scrollbar
        text_frame = ttk.Frame(results_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(text_frame, height=10, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    # Event handlers
    def select_input_folder(self):
        """Chọn thư mục input"""
        folder = filedialog.askdirectory(title="Chọn thư mục chứa video")
        if folder:
            self.input_folder_var.set(folder)
            
    def select_output_folder(self):
        """Chọn thư mục output"""
        folder = filedialog.askdirectory(title="Chọn thư mục lưu video đã xử lý")
        if folder:
            self.output_folder_var.set(folder)
            
    def select_img_folder(self):
        """Chọn thư mục ảnh"""
        folder = filedialog.askdirectory(title="Chọn thư mục ảnh overlay")
        if folder:
            self.img_folder_var.set(folder)
            
    def scan_videos(self):
        """Quét video trong thư mục"""
        input_folder = self.input_folder_var.get()
        if not input_folder:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn thư mục input!")
            return
            
        if not os.path.exists(input_folder):
            messagebox.showerror("Lỗi", "Thư mục input không tồn tại!")
            return
            
        try:
            # Get extensions
            extensions = [ext.strip() for ext in self.extensions_var.get().split(',')]
            
            # Scan videos
            video_files = []
            for filename in os.listdir(input_folder):
                name, ext = os.path.splitext(filename.lower())
                if ext in extensions:
                    video_files.append(filename)
                    
            self.log_message(f"🔍 Tìm thấy {len(video_files)} video trong thư mục:")
            for video in video_files[:10]:  # Show first 10
                self.log_message(f"   📼 {video}")
            if len(video_files) > 10:
                self.log_message(f"   ... và {len(video_files) - 10} video khác")
                
            if video_files:
                self.start_button.config(state="normal")
                self.stats_labels['total'].config(text=str(len(video_files)))
            else:
                self.log_message("❌ Không tìm thấy video nào!")
                
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi quét video: {str(e)}")
            
    def start_processing(self):
        """Bắt đầu xử lý hàng loạt"""
        # Validation
        if not self.input_folder_var.get() or not self.output_folder_var.get():
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn thư mục input và output!")
            return
            
        try:
            # Create processor
            self.processor = BatchProcessor(max_workers=self.workers_var.get())
            
            # Create config
            config = create_batch_config(
                source_lang=self.source_lang_var.get(),
                target_lang=self.target_lang_var.get(),
                img_folder=self.img_folder_var.get() if self.img_folder_var.get() else None,
                custom_timeline=self.custom_timeline_var.get()
            )
            
            # Add videos
            extensions = [ext.strip() for ext in self.extensions_var.get().split(',')]
            count = self.processor.add_folder_videos(
                self.input_folder_var.get(),
                self.output_folder_var.get(),
                config,
                extensions
            )
            
            if count == 0:
                messagebox.showwarning("Cảnh báo", "Không có video nào để xử lý!")
                return
                
            # Update UI
            self.processing = True
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            self.scan_button.config(state="disabled")
            
            # Start processing
            self.processor.start_processing(progress_callback=self.update_progress)
            
            self.log_message(f"🚀 Bắt đầu xử lý {count} video với {self.workers_var.get()} workers")
            
            # Start monitoring thread
            monitor_thread = threading.Thread(target=self.monitor_completion)
            monitor_thread.daemon = True
            monitor_thread.start()
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi bắt đầu xử lý: {str(e)}")
            
    def stop_processing(self):
        """Dừng xử lý"""
        if self.processor:
            self.processor.stop_processing()
            
        self.processing = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.scan_button.config(state="normal")
        self.export_button.config(state="normal")
        
        self.log_message("⏹️ Đã dừng xử lý")
        
    def update_progress(self, progress):
        """Cập nhật tiến độ"""
        self.progress_var.set(progress['percentage'])
        self.status_label.config(text=f"Đang xử lý... {progress['percentage']:.1f}%")
        
        # Update stats
        for key in ['total', 'completed', 'failed', 'remaining']:
            if key in progress:
                self.stats_labels[key].config(text=str(progress[key]))
                
    def monitor_completion(self):
        """Monitor hoàn thành"""
        while self.processing and self.processor:
            # Check if completed
            stats = self.processor.get_statistics()
            total_processed = stats['completed'] + stats['failed']
            
            if total_processed >= stats['total']:
                # Completed
                self.window.after(100, self.on_completion)
                break
                
            time.sleep(1)
            
    def on_completion(self):
        """Khi hoàn thành xử lý"""
        self.stop_processing()
        
        if self.processor:
            stats = self.processor.get_statistics()
            self.log_message(f"🎉 Hoàn thành xử lý!")
            self.log_message(f"   ✅ Thành công: {stats['completed']}")
            self.log_message(f"   ❌ Thất bại: {stats['failed']}")
            self.log_message(f"   📊 Tổng cộng: {stats['total']}")
            
            if 'total_duration' in stats:
                self.log_message(f"   ⏱️ Thời gian: {stats['total_duration']:.1f}s")
                
        messagebox.showinfo("Hoàn thành", "Batch processing đã hoàn thành!")
        
    def export_report(self):
        """Xuất báo cáo"""
        if not self.processor:
            messagebox.showwarning("Cảnh báo", "Chưa có dữ liệu để xuất!")
            return
            
        filename = filedialog.asksaveasfilename(
            title="Lưu báo cáo",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                self.processor.export_report(filename)
                self.log_message(f"📄 Đã xuất báo cáo: {filename}")
                messagebox.showinfo("Thành công", f"Đã xuất báo cáo ra file:\\n{filename}")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Lỗi xuất báo cáo: {str(e)}")
                
    def log_message(self, message):
        """Thêm message vào log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\\n")
        self.log_text.see(tk.END)
        self.window.update_idletasks()

def show_batch_processing_dialog(parent):
    """Hiển thị dialog batch processing"""
    BatchProcessingGUI(parent)
