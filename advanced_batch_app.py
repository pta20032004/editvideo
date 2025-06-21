#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Batch App - Entry point cho Advanced Batch Processing
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from batch.advanced_batch_gui import AdvancedBatchGUI
    from batch.advanced_batch_processor import AdvancedBatchProcessor
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Vui lòng đảm bảo tất cả dependencies đã được cài đặt")
    sys.exit(1)

class AdvancedBatchApp:
    """Advanced Batch Processing Application"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🚀 Advanced Video Batch Processor")
        self.root.geometry("400x300")
        
        # Center window
        self.center_window()
        
        self.create_main_menu()
        
    def center_window(self):
        """Center window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
    def create_main_menu(self):
        """Tạo menu chính"""
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(
            main_frame,
            text="🚀 Advanced Video Batch Processor",
            font=("Arial", 18, "bold"),
            bg='#f0f0f0',
            fg='#2c3e50'
        )
        title_label.pack(pady=(0, 10))
        
        # Subtitle
        subtitle_label = tk.Label(
            main_frame,
            text="Xử lý hàng loạt 100+ video với hiệu năng cao",
            font=("Arial", 12),
            bg='#f0f0f0',
            fg='#7f8c8d'
        )
        subtitle_label.pack(pady=(0, 30))
        
        # Features
        features_frame = tk.Frame(main_frame, bg='#f0f0f0')
        features_frame.pack(pady=(0, 30))
        
        features = [
            "🎬 Xử lý hàng loạt 100+ video",
            "⚡ Multi-threading tối ưu",
            "💾 Quản lý bộ nhớ thông minh",
            "📊 Giám sát tiến độ chi tiết",
            "🔄 Resume khi bị gián đoạn",
            "📈 Priority queue"
        ]
        
        for feature in features:
            feature_label = tk.Label(
                features_frame,
                text=feature,
                font=("Arial", 10),
                bg='#f0f0f0',
                fg='#34495e',
                anchor='w'
            )
            feature_label.pack(fill=tk.X, pady=2)
        
        # Buttons
        button_frame = tk.Frame(main_frame, bg='#f0f0f0')
        button_frame.pack(pady=(20, 0))
        
        # Advanced GUI button
        gui_button = tk.Button(
            button_frame,
            text="🚀 Mở Advanced GUI",
            font=("Arial", 12, "bold"),
            bg='#3498db',
            fg='white',
            relief='flat',
            padx=20,
            pady=10,
            command=self.open_advanced_gui
        )
        gui_button.pack(pady=5, fill=tk.X)
        
        # Test button
        test_button = tk.Button(
            button_frame,
            text="🧪 Chạy Test System",
            font=("Arial", 12),
            bg='#2ecc71',
            fg='white',
            relief='flat',
            padx=20,
            pady=10,
            command=self.run_system_test
        )
        test_button.pack(pady=5, fill=tk.X)
        
        # Info button
        info_button = tk.Button(
            button_frame,
            text="ℹ️ Thông tin hệ thống",
            font=("Arial", 12),
            bg='#f39c12',
            fg='white',
            relief='flat',
            padx=20,
            pady=10,
            command=self.show_system_info
        )
        info_button.pack(pady=5, fill=tk.X)
        
        # Quit button
        quit_button = tk.Button(
            button_frame,
            text="❌ Thoát",
            font=("Arial", 12),
            bg='#e74c3c',
            fg='white',
            relief='flat',
            padx=20,
            pady=10,
            command=self.root.quit
        )
        quit_button.pack(pady=(20, 0), fill=tk.X)
        
    def open_advanced_gui(self):
        """Mở Advanced GUI"""
        try:
            # Hide main window
            self.root.withdraw()
            
            # Open advanced GUI
            advanced_gui = AdvancedBatchGUI(self.root)
            
            # Show main window when advanced GUI closes
            self.root.deiconify()
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể mở Advanced GUI: {str(e)}")
            self.root.deiconify()
            
    def run_system_test(self):
        """Chạy test hệ thống"""
        try:
            import psutil
            
            # Create processor to test
            processor = AdvancedBatchProcessor()
            resources = processor.check_system_resources()
            
            # Show results
            test_results = f"""🧪 KẾT QUẢ TEST HỆ THỐNG
            
💻 CPU:
   - Cores: {psutil.cpu_count()}
   - Usage: {resources['cpu_percent']:.1f}%
   
💾 Memory:
   - Total: {psutil.virtual_memory().total / 1024**3:.1f}GB
   - Available: {resources['memory_available_gb']:.1f}GB
   - Usage: {resources['memory_usage_gb']:.1f}GB
   
💿 Disk:
   - Free space: {resources['disk_free_gb']:.1f}GB
   
⚡ Khuyến nghị:
   - Max workers: {min(16, max(2, int(psutil.cpu_count() * 0.7)))}
   - Memory limit: {int(resources['memory_available_gb'] * 0.8)}GB
   
✅ System ready: {'Có' if resources['can_process'] else 'Không'}"""
            
            messagebox.showinfo("Test Results", test_results)
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi test hệ thống: {str(e)}")
            
    def show_system_info(self):
        """Hiển thị thông tin hệ thống"""
        try:
            import psutil
            import platform
            
            # Get system info
            system_info = f"""💻 THÔNG TIN HỆ THỐNG
            
🖥️ Hệ điều hành:
   - OS: {platform.system()} {platform.release()}
   - Architecture: {platform.architecture()[0]}
   
⚡ CPU:
   - Model: {platform.processor() or 'Unknown'}
   - Cores: {psutil.cpu_count()} cores
   - Frequency: {psutil.cpu_freq().current:.0f}MHz (hiện tại)
   
💾 Memory:
   - Total RAM: {psutil.virtual_memory().total / 1024**3:.1f}GB
   - Available: {psutil.virtual_memory().available / 1024**3:.1f}GB
   - Used: {psutil.virtual_memory().percent:.1f}%
   
💿 Disk:
   - Free space: {psutil.disk_usage('.').free / 1024**3:.1f}GB
   - Total space: {psutil.disk_usage('.').total / 1024**3:.1f}GB
   
🐍 Python:
   - Version: {platform.python_version()}
   - Implementation: {platform.python_implementation()}"""
            
            messagebox.showinfo("System Info", system_info)
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi lấy thông tin hệ thống: {str(e)}")
            
    def run(self):
        """Chạy ứng dụng"""
        self.root.mainloop()

def main():
    """Main function"""
    print("🚀 Advanced Video Batch Processor")
    print("=" * 50)
    
    try:
        app = AdvancedBatchApp()
        app.run()
        
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        messagebox.showerror("Error", f"Application error: {str(e)}")

if __name__ == "__main__":
    main()
