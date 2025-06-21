#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Batch GUI - Giao diện xử lý hàng loạt nâng cao
Hỗ trợ xử lý 100+ video với monitoring chi tiết
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import time
import psutil
from datetime import datetime, timedelta
from .advanced_batch_processor import AdvancedBatchProcessor, process_large_batch

class AdvancedBatchGUI:
    """GUI nâng cao cho batch processing"""
    
    def __init__(self, parent):
        self.parent = parent
        self.processor = None
        self.processing = False
        self.monitoring_thread = None
        
        # UI Variables
        self.input_folder = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.max_workers = tk.IntVar(value=psutil.cpu_count())
        self.memory_limit = tk.IntVar(value=8)
        self.priority_mode = tk.BooleanVar(value=True)
        self.priority_by_size = tk.BooleanVar(value=True)
        
        # Language settings
        self.source_lang = tk.StringVar(value='vi')
        self.target_lang = tk.StringVar(value='en')
        self.custom_timeline = tk.BooleanVar(value=False)
        
        # Progress tracking
        self.progress_var = tk.DoubleVar()
        self.status_text = tk.StringVar(value="Sẵn sàng")
        
        self.create_advanced_window()
        
    def create_advanced_window(self):
        """Tạo cửa sổ batch processing nâng cao"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("🚀 Advanced Batch Processing - Xử lý 100+ Video")
        self.window.geometry("1000x800")
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Center window
        self.window.geometry("+%d+%d" % (
            self.parent.winfo_rootx() + 50,
            self.parent.winfo_rooty() + 50
        ))
        
        # Handle close event
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.create_widgets()
        self.update_system_info()
        
    def create_widgets(self):
        """Tạo các widget"""
        # Main container
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = ttk.Label(
            title_frame,
            text="🚀 Advanced Batch Processing",
            font=("Arial", 18, "bold")
        )
        title_label.pack(side=tk.LEFT)
        
        # System info
        self.system_label = ttk.Label(
            title_frame,
            text="💻 System Info",
            font=("Arial", 10)
        )
        self.system_label.pack(side=tk.RIGHT)
        
        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Configuration
        config_frame = ttk.Frame(notebook, padding="10")
        notebook.add(config_frame, text="⚙️ Cấu hình")
        self.create_config_tab(config_frame)
        
        # Tab 2: Advanced Settings
        advanced_frame = ttk.Frame(notebook, padding="10")
        notebook.add(advanced_frame, text="🔧 Nâng cao")
        self.create_advanced_tab(advanced_frame)
        
        # Tab 3: Monitoring
        monitor_frame = ttk.Frame(notebook, padding="10")
        notebook.add(monitor_frame, text="📊 Giám sát")
        self.create_monitor_tab(monitor_frame)
        
        # Tab 4: Results
        results_frame = ttk.Frame(notebook, padding="10")
        notebook.add(results_frame, text="📋 Kết quả")
        self.create_results_tab(results_frame)
        
        # Bottom control panel
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(10, 0))
        self.create_control_panel(control_frame)
        
    def create_config_tab(self, parent):
        """Tab cấu hình cơ bản"""
        # Folder selection
        folder_frame = ttk.LabelFrame(parent, text="📁 Thư mục", padding="10")
        folder_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Input folder
        ttk.Label(folder_frame, text="Thư mục video input:").grid(row=0, column=0, sticky=tk.W, pady=2)
        input_frame = ttk.Frame(folder_frame)
        input_frame.grid(row=0, column=1, sticky=tk.EW, padx=(10, 0), pady=2)
        
        ttk.Entry(input_frame, textvariable=self.input_folder, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(input_frame, text="Chọn", command=self.select_input_folder).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Output folder
        ttk.Label(folder_frame, text="Thư mục output:").grid(row=1, column=0, sticky=tk.W, pady=2)
        output_frame = ttk.Frame(folder_frame)
        output_frame.grid(row=1, column=1, sticky=tk.EW, padx=(10, 0), pady=2)
        
        ttk.Entry(output_frame, textvariable=self.output_folder, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(output_frame, text="Chọn", command=self.select_output_folder).pack(side=tk.RIGHT, padx=(5, 0))
        
        folder_frame.grid_columnconfigure(1, weight=1)
        
        # Language settings
        lang_frame = ttk.LabelFrame(parent, text="🌐 Ngôn ngữ", padding="10")
        lang_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(lang_frame, text="Ngôn ngữ gốc:").grid(row=0, column=0, sticky=tk.W, pady=2)
        source_combo = ttk.Combobox(lang_frame, textvariable=self.source_lang, values=['vi', 'en', 'zh', 'ja'], width=10)
        source_combo.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        ttk.Label(lang_frame, text="Ngôn ngữ đích:").grid(row=0, column=2, sticky=tk.W, padx=(20, 0), pady=2)
        target_combo = ttk.Combobox(lang_frame, textvariable=self.target_lang, values=['en', 'vi', 'zh', 'ja'], width=10)
        target_combo.grid(row=0, column=3, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Features
        features_frame = ttk.LabelFrame(parent, text="🎯 Tính năng", padding="10")
        features_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Checkbutton(features_frame, text="Custom Timeline (3 ảnh)", variable=self.custom_timeline).grid(row=0, column=0, sticky=tk.W, pady=2)
        
        # Quick presets
        preset_frame = ttk.LabelFrame(parent, text="⚡ Preset nhanh", padding="10")
        preset_frame.pack(fill=tk.X)
        
        ttk.Button(preset_frame, text="🎬 TikTok/Instagram", command=lambda: self.apply_preset('tiktok')).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(preset_frame, text="📺 YouTube Shorts", command=lambda: self.apply_preset('youtube')).pack(side=tk.LEFT, padx=5)
        ttk.Button(preset_frame, text="🌟 Full Features", command=lambda: self.apply_preset('full')).pack(side=tk.LEFT, padx=5)
        
    def create_advanced_tab(self, parent):
        """Tab cấu hình nâng cao"""
        # Performance settings
        perf_frame = ttk.LabelFrame(parent, text="⚡ Hiệu năng", padding="10")
        perf_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Workers
        ttk.Label(perf_frame, text="Số workers:").grid(row=0, column=0, sticky=tk.W, pady=2)
        worker_frame = ttk.Frame(perf_frame)
        worker_frame.grid(row=0, column=1, sticky=tk.EW, padx=(10, 0), pady=2)
        
        worker_scale = ttk.Scale(worker_frame, from_=1, to=16, variable=self.max_workers, orient=tk.HORIZONTAL)
        worker_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.worker_label = ttk.Label(worker_frame, text=f"{self.max_workers.get()}")
        self.worker_label.pack(side=tk.RIGHT, padx=(5, 0))
        
        worker_scale.configure(command=self.update_worker_label)
        
        # Memory limit
        ttk.Label(perf_frame, text="Giới hạn RAM (GB):").grid(row=1, column=0, sticky=tk.W, pady=2)
        memory_frame = ttk.Frame(perf_frame)
        memory_frame.grid(row=1, column=1, sticky=tk.EW, padx=(10, 0), pady=2)
        
        memory_scale = ttk.Scale(memory_frame, from_=2, to=32, variable=self.memory_limit, orient=tk.HORIZONTAL)
        memory_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.memory_label = ttk.Label(memory_frame, text=f"{self.memory_limit.get()}GB")
        self.memory_label.pack(side=tk.RIGHT, padx=(5, 0))
        
        memory_scale.configure(command=self.update_memory_label)
        
        perf_frame.grid_columnconfigure(1, weight=1)
        
        # Processing options
        options_frame = ttk.LabelFrame(parent, text="🔧 Tùy chọn xử lý", padding="10")
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Checkbutton(options_frame, text="Priority mode (xử lý video nhỏ trước)", variable=self.priority_mode).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(options_frame, text="Sắp xếp theo kích thước", variable=self.priority_by_size).pack(anchor=tk.W, pady=2)
        
        # System recommendations
        rec_frame = ttk.LabelFrame(parent, text="💡 Khuyến nghị hệ thống", padding="10")
        rec_frame.pack(fill=tk.X)
        
        self.rec_text = tk.Text(rec_frame, height=6, wrap=tk.WORD, state=tk.DISABLED)
        self.rec_text.pack(fill=tk.BOTH, expand=True)
        
        rec_scroll = ttk.Scrollbar(rec_frame, orient=tk.VERTICAL, command=self.rec_text.yview)
        rec_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.rec_text.configure(yscrollcommand=rec_scroll.set)
        
    def create_monitor_tab(self, parent):
        """Tab giám sát tiến độ"""
        # Progress section
        progress_frame = ttk.LabelFrame(parent, text="📊 Tiến độ", padding="10")
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, length=400)
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))
        
        # Status label
        self.status_label = ttk.Label(progress_frame, textvariable=self.status_text, font=("Arial", 10))
        self.status_label.pack(pady=2)
        
        # Stats frame
        stats_frame = ttk.Frame(progress_frame)
        stats_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Create stats labels
        self.stats_labels = {}
        stats_info = [
            ('total', 'Tổng cộng'),
            ('completed', 'Hoàn thành'),
            ('failed', 'Thất bại'),
            ('processing', 'Đang xử lý'),
            ('queued', 'Đang chờ')
        ]
        
        for i, (key, label) in enumerate(stats_info):
            ttk.Label(stats_frame, text=f"{label}:").grid(row=i//3, column=(i%3)*2, sticky=tk.W, padx=(0, 5), pady=1)
            self.stats_labels[key] = ttk.Label(stats_frame, text="0", font=("Arial", 10, "bold"))
            self.stats_labels[key].grid(row=i//3, column=(i%3)*2+1, sticky=tk.W, padx=(0, 15), pady=1)
        
        # System monitoring
        system_frame = ttk.LabelFrame(parent, text="💻 Hệ thống", padding="10")
        system_frame.pack(fill=tk.X, pady=(0, 10))
        
        # System info labels
        self.system_labels = {}
        system_info = [
            ('cpu', 'CPU'),
            ('memory', 'RAM'),
            ('disk', 'Disk'),
            ('speed', 'Tốc độ')
        ]
        
        for i, (key, label) in enumerate(system_info):
            ttk.Label(system_frame, text=f"{label}:").grid(row=i//2, column=(i%2)*2, sticky=tk.W, padx=(0, 5), pady=2)
            self.system_labels[key] = ttk.Label(system_frame, text="--", font=("Arial", 10))
            self.system_labels[key].grid(row=i//2, column=(i%2)*2+1, sticky=tk.W, padx=(0, 20), pady=2)
        
        # Time estimation
        time_frame = ttk.LabelFrame(parent, text="⏱️ Thời gian", padding="10")
        time_frame.pack(fill=tk.X)
        
        self.time_labels = {}
        time_info = [
            ('elapsed', 'Đã trôi qua'),
            ('remaining', 'Còn lại'),
            ('eta', 'Hoàn thành lúc'),
            ('avg_time', 'TB/video')
        ]
        
        for i, (key, label) in enumerate(time_info):
            ttk.Label(time_frame, text=f"{label}:").grid(row=i//2, column=(i%2)*2, sticky=tk.W, padx=(0, 5), pady=2)
            self.time_labels[key] = ttk.Label(time_frame, text="--", font=("Arial", 10))
            self.time_labels[key].grid(row=i//2, column=(i%2)*2+1, sticky=tk.W, padx=(0, 20), pady=2)
        
    def create_results_tab(self, parent):
        """Tab kết quả"""
        # Results list
        results_frame = ttk.LabelFrame(parent, text="📋 Kết quả chi tiết", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Create treeview
        columns = ('File', 'Status', 'Duration', 'Size', 'Thread')
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=15)
        
        # Define headings
        self.results_tree.heading('File', text='File')
        self.results_tree.heading('Status', text='Trạng thái')
        self.results_tree.heading('Duration', text='Thời gian')
        self.results_tree.heading('Size', text='Kích thước')
        self.results_tree.heading('Thread', text='Thread')
        
        # Define column widths
        self.results_tree.column('File', width=200)
        self.results_tree.column('Status', width=80)
        self.results_tree.column('Duration', width=80)
        self.results_tree.column('Size', width=100)
        self.results_tree.column('Thread', width=60)
        
        # Scrollbars
        tree_scroll_y = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        tree_scroll_x = ttk.Scrollbar(results_frame, orient=tk.HORIZONTAL, command=self.results_tree.xview)
        
        self.results_tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)
        
        # Grid layout
        self.results_tree.grid(row=0, column=0, sticky=tk.NSEW)
        tree_scroll_y.grid(row=0, column=1, sticky=tk.NS)
        tree_scroll_x.grid(row=1, column=0, sticky=tk.EW)
        
        results_frame.grid_rowconfigure(0, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)
        
        # Export buttons
        export_frame = ttk.Frame(parent)
        export_frame.pack(fill=tk.X)
        
        ttk.Button(export_frame, text="📄 Xuất báo cáo JSON", command=self.export_json_report).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(export_frame, text="📊 Xuất Excel", command=self.export_excel_report).pack(side=tk.LEFT, padx=5)
        ttk.Button(export_frame, text="🔄 Refresh", command=self.refresh_results).pack(side=tk.RIGHT)
        
    def create_control_panel(self, parent):
        """Panel điều khiển"""
        # Progress bar
        self.main_progress = ttk.Progressbar(parent, variable=self.progress_var, length=300)
        self.main_progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # Control buttons
        self.start_button = ttk.Button(parent, text="🚀 Bắt đầu", command=self.start_processing)
        self.start_button.pack(side=tk.RIGHT, padx=5)
        
        self.stop_button = ttk.Button(parent, text="🛑 Dừng", command=self.stop_processing, state=tk.DISABLED)
        self.stop_button.pack(side=tk.RIGHT, padx=5)
        
        self.pause_button = ttk.Button(parent, text="⏸️ Tạm dừng", command=self.pause_processing, state=tk.DISABLED)
        self.pause_button.pack(side=tk.RIGHT, padx=5)
        
    def select_input_folder(self):
        """Chọn thư mục input"""
        folder = filedialog.askdirectory(title="Chọn thư mục chứa video")
        if folder:
            self.input_folder.set(folder)
            self.scan_input_folder()
            
    def select_output_folder(self):
        """Chọn thư mục output"""
        folder = filedialog.askdirectory(title="Chọn thư mục lưu video đã xử lý")
        if folder:
            self.output_folder.set(folder)
            
    def scan_input_folder(self):
        """Quét thư mục input"""
        input_dir = self.input_folder.get()
        if not input_dir or not os.path.exists(input_dir):
            return
            
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']
        video_files = []
        total_size = 0
        
        for filename in os.listdir(input_dir):
            name, ext = os.path.splitext(filename.lower())
            if ext in video_extensions:
                file_path = os.path.join(input_dir, filename)
                file_size = os.path.getsize(file_path)
                video_files.append((filename, file_size))
                total_size += file_size
        
        # Update status
        count = len(video_files)
        size_gb = total_size / (1024**3)
        self.status_text.set(f"Tìm thấy {count} video ({size_gb:.2f}GB)")
        
        # Update recommendations
        self.update_recommendations(count, size_gb)
        
    def update_recommendations(self, video_count, total_size_gb):
        """Cập nhật khuyến nghị"""
        self.rec_text.configure(state=tk.NORMAL)
        self.rec_text.delete(1.0, tk.END)
        
        # Calculate recommendations
        system_ram = psutil.virtual_memory().total / (1024**3)
        cpu_cores = psutil.cpu_count()
        
        recommendations = []
        
        if video_count > 100:
            recommendations.append("🎬 Batch lớn (100+ video) - sử dụng priority mode")
            
        if total_size_gb > 10:
            recommendations.append(f"💾 Dữ liệu lớn ({total_size_gb:.1f}GB) - đảm bảo đủ dung lượng disk")
            
        if video_count > 50:
            optimal_workers = min(cpu_cores, video_count // 10, int(system_ram // 2))
            recommendations.append(f"⚡ Khuyến nghị {optimal_workers} workers cho hiệu suất tối ưu")
            
        if system_ram < 8:
            recommendations.append("⚠️ RAM thấp - giảm số workers và memory limit")
            
        if total_size_gb / video_count > 0.5:  # Large files
            recommendations.append("📹 Video lớn - tăng memory limit, giảm workers")
            
        # Estimate time
        avg_time_per_video = 60  # seconds
        estimated_total_time = (video_count * avg_time_per_video) / max(1, self.max_workers.get())
        estimated_hours = estimated_total_time / 3600
        
        recommendations.append(f"⏱️ Thời gian ước tính: {estimated_hours:.1f} giờ")
        
        # Write recommendations
        for rec in recommendations:
            self.rec_text.insert(tk.END, rec + "\n")
            
        self.rec_text.configure(state=tk.DISABLED)
        
    def update_worker_label(self, value):
        """Cập nhật label số workers"""
        self.worker_label.configure(text=f"{int(float(value))}")
        
    def update_memory_label(self, value):
        """Cập nhật label memory limit"""
        self.memory_label.configure(text=f"{int(float(value))}GB")
        
    def apply_preset(self, preset_type):
        """Áp dụng preset cấu hình"""
        if preset_type == 'tiktok':
            self.source_lang.set('vi')
            self.target_lang.set('en')
            self.custom_timeline.set(True)
            self.priority_mode.set(True)
            
        elif preset_type == 'youtube':
            self.source_lang.set('vi')
            self.target_lang.set('en')
            self.custom_timeline.set(False)
            self.priority_mode.set(True)
            
        elif preset_type == 'full':
            self.custom_timeline.set(True)
            self.priority_mode.set(True)
            self.priority_by_size.set(True)
            
        messagebox.showinfo("Preset", f"Đã áp dụng preset {preset_type.upper()}")
        
    def update_system_info(self):
        """Cập nhật thông tin hệ thống"""
        try:
            # CPU and Memory
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            
            # Update system label
            self.system_label.configure(
                text=f"💻 CPU: {cpu_percent:.1f}% | RAM: {memory.percent:.1f}% | Available: {memory.available/1024**3:.1f}GB"
            )
            
            # Schedule next update
            self.window.after(5000, self.update_system_info)  # Update every 5 seconds
            
        except Exception as e:
            print(f"Error updating system info: {e}")
            
    def start_processing(self):
        """Bắt đầu xử lý"""
        # Validate inputs
        if not self.input_folder.get():
            messagebox.showerror("Lỗi", "Vui lòng chọn thư mục input")
            return
            
        if not self.output_folder.get():
            messagebox.showerror("Lỗi", "Vui lòng chọn thư mục output")
            return
            
        if not os.path.exists(self.input_folder.get()):
            messagebox.showerror("Lỗi", "Thư mục input không tồn tại")
            return
            
        # Create config
        config = {
            'source_language': self.source_lang.get(),
            'target_language': self.target_lang.get(),
            'custom_timeline': self.custom_timeline.get()
        }
        
        # Update UI
        self.start_button.configure(state=tk.DISABLED)
        self.stop_button.configure(state=tk.NORMAL)
        self.pause_button.configure(state=tk.NORMAL)
        self.processing = True
        
        # Start processing in thread
        self.processing_thread = threading.Thread(
            target=self._process_videos,
            args=(config,),
            daemon=True
        )
        self.processing_thread.start()
        
        # Start monitoring
        self.start_monitoring()
        
    def _process_videos(self, config):
        """Xử lý video trong thread riêng"""
        try:
            # Create processor
            self.processor = AdvancedBatchProcessor(
                max_workers=self.max_workers.get(),
                memory_limit_gb=self.memory_limit.get(),
                priority_mode=self.priority_mode.get()
            )
            
            # Add videos
            task_ids = self.processor.add_folder_videos(
                input_folder=self.input_folder.get(),
                output_folder=self.output_folder.get(),
                config=config,
                priority_by_size=self.priority_by_size.get()
            )
            
            # Start processing
            self.processor.start_processing()
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi xử lý: {str(e)}")
        finally:
            self.processing = False
            self.window.after(0, self.processing_finished)
            
    def start_monitoring(self):
        """Bắt đầu monitoring"""
        if not self.processing:
            return
            
        self.monitoring_thread = threading.Thread(target=self._monitor_progress, daemon=True)
        self.monitoring_thread.start()
        
    def _monitor_progress(self):
        """Monitor tiến độ trong thread riêng"""
        while self.processing and self.processor:
            try:
                progress = self.processor.get_progress()
                
                # Update UI in main thread
                self.window.after(0, self.update_progress_ui, progress)
                
                time.sleep(2)  # Update every 2 seconds
                
            except Exception as e:
                print(f"Monitor error: {e}")
                time.sleep(1)
                
    def update_progress_ui(self, progress):
        """Cập nhật UI tiến độ"""
        try:
            # Update progress bar
            self.progress_var.set(progress['percentage'])
            
            # Update status
            self.status_text.set(
                f"Tiến độ: {progress['percentage']:.1f}% | "
                f"Hoàn thành: {progress['completed']}/{progress['total']}"
            )
            
            # Update stats labels
            for key in self.stats_labels:
                if key in progress:
                    self.stats_labels[key].configure(text=str(progress[key]))
            
            # Update system labels
            system_info = progress.get('system_info', {})
            if system_info:
                self.system_labels['cpu'].configure(text=f"{system_info.get('cpu_percent', 0):.1f}%")
                self.system_labels['memory'].configure(text=f"{system_info.get('memory_usage_gb', 0):.1f}GB")
                self.system_labels['disk'].configure(text=f"{system_info.get('disk_free_gb', 0):.1f}GB")
            
            # Update time labels
            if progress['estimated_remaining_seconds'] > 0:
                remaining_time = str(timedelta(seconds=int(progress['estimated_remaining_seconds'])))
                self.time_labels['remaining'].configure(text=remaining_time)
                
                # ETA
                eta = datetime.now() + timedelta(seconds=progress['estimated_remaining_seconds'])
                self.time_labels['eta'].configure(text=eta.strftime("%H:%M:%S"))
            
            # Update results tree
            self.refresh_results()
            
        except Exception as e:
            print(f"UI update error: {e}")
            
    def refresh_results(self):
        """Refresh bảng kết quả"""
        if not self.processor:
            return
            
        # Clear existing items
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
            
        # Add completed tasks
        for task in self.processor.completed_tasks:
            filename = os.path.basename(task['input_path'])
            status = "✅ Thành công"
            duration = f"{task['duration']:.1f}s"
            size = f"{task.get('input_size', 0) / 1024 / 1024:.1f}MB"
            thread_id = str(task.get('thread_id', '-'))
            
            self.results_tree.insert('', tk.END, values=(filename, status, duration, size, thread_id))
            
        # Add failed tasks
        for task in self.processor.failed_tasks:
            filename = os.path.basename(task['input_path'])
            status = "❌ Thất bại"
            duration = f"{task.get('duration', 0):.1f}s"
            size = "-"
            thread_id = str(task.get('thread_id', '-'))
            
            self.results_tree.insert('', tk.END, values=(filename, status, duration, size, thread_id))
            
    def stop_processing(self):
        """Dừng xử lý"""
        if self.processor:
            self.processor.stop_processing()
        self.processing = False
        
    def pause_processing(self):
        """Tạm dừng xử lý"""
        # Implementation for pause/resume
        pass
        
    def processing_finished(self):
        """Xử lý hoàn thành"""
        self.start_button.configure(state=tk.NORMAL)
        self.stop_button.configure(state=tk.DISABLED)
        self.pause_button.configure(state=tk.DISABLED)
        
        if self.processor:
            stats = self.processor.get_statistics()
            messagebox.showinfo(
                "Hoàn thành",
                f"Batch processing hoàn thành!\n\n"
                f"✅ Thành công: {stats['completed']}\n"
                f"❌ Thất bại: {stats['failed']}\n"
                f"📈 Tổng cộng: {stats['total']}"
            )
            
    def export_json_report(self):
        """Xuất báo cáo JSON"""
        if not self.processor:
            messagebox.showwarning("Cảnh báo", "Không có dữ liệu để xuất")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            title="Lưu báo cáo JSON"
        )
        
        if filename:
            self.processor.export_report(filename)
            messagebox.showinfo("Thành công", f"Đã xuất báo cáo: {filename}")
            
    def export_excel_report(self):
        """Xuất báo cáo Excel"""
        messagebox.showinfo("Thông báo", "Tính năng xuất Excel sẽ được thêm trong phiên bản tiếp theo")
        
    def on_closing(self):
        """Xử lý khi đóng cửa sổ"""
        if self.processing:
            if messagebox.askokcancel("Xác nhận", "Đang xử lý video. Bạn có muốn dừng và thoát?"):
                self.stop_processing()
                self.window.destroy()
        else:
            self.window.destroy()

# Test function
def test_advanced_gui():
    """Test Advanced Batch GUI"""
    root = tk.Tk()
    root.withdraw()  # Hide root window
    
    app = AdvancedBatchGUI(root)
    root.mainloop()

if __name__ == "__main__":
    test_advanced_gui()
