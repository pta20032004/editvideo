#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI Utilities Module
"""

import tkinter as tk
from tkinter import ttk
import os

class GUIUtils:
    """Các tiện ích hỗ trợ GUI"""
    
    @staticmethod
    def center_window(window, parent=None):
        """Căn giữa cửa sổ"""
        window.update_idletasks()
        
        if parent:
            x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (window.winfo_width() // 2)
            y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (window.winfo_height() // 2)
        else:
            x = (window.winfo_screenwidth() // 2) - (window.winfo_width() // 2)
            y = (window.winfo_screenheight() // 2) - (window.winfo_height() // 2)
        
        window.geometry(f"+{x}+{y}")
    
    @staticmethod
    def create_scrollable_frame(parent):
        """Tạo frame có thể scroll"""
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        return canvas, scrollbar, scrollable_frame
    
    @staticmethod
    def validate_number_input(value, min_val=0, max_val=None):
        """Validate số input"""
        try:
            num = float(value)
            if num < min_val:
                return False
            if max_val is not None and num > max_val:
                return False
            return True
        except ValueError:
            return False
    
    @staticmethod
    def format_time(seconds):
        """Format thời gian thành mm:ss"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    @staticmethod
    def get_file_size_mb(file_path):
        """Lấy kích thước file theo MB"""
        try:
            size_bytes = os.path.getsize(file_path)
            size_mb = size_bytes / (1024 * 1024)
            return round(size_mb, 1)
        except:
            return 0
    
    @staticmethod
    def create_tooltip(widget, text):
        """Tạo tooltip cho widget"""
        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = tk.Label(
                tooltip, 
                text=text, 
                background="lightyellow", 
                relief="solid", 
                borderwidth=1,
                font=("Arial", 9)
            )
            label.pack()
            
            def hide_tooltip():
                tooltip.destroy()
            
            tooltip.after(3000, hide_tooltip)  # Auto hide after 3s
        
        widget.bind("<Enter>", show_tooltip)
    
    @staticmethod
    def create_progress_dialog(parent, title="Đang xử lý..."):
        """Tạo dialog hiển thị progress"""
        dialog = tk.Toplevel(parent)
        dialog.title(title)
        dialog.geometry("400x150")
        dialog.transient(parent)
        dialog.grab_set()
        
        # Center dialog
        GUIUtils.center_window(dialog, parent)
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Status label
        status_label = ttk.Label(frame, text="Đang khởi tạo...", font=("Arial", 10))
        status_label.pack(pady=(0, 20))
        
        # Progress bar
        progress_bar = ttk.Progressbar(frame, mode='indeterminate')
        progress_bar.pack(fill=tk.X, pady=(0, 20))
        progress_bar.start()
        
        # Cancel button
        cancel_var = tk.BooleanVar()
        def cancel():
            cancel_var.set(True)
            dialog.destroy()
        
        cancel_btn = ttk.Button(frame, text="Hủy", command=cancel)
        cancel_btn.pack()
        
        return dialog, status_label, progress_bar, cancel_var
    
    @staticmethod
    def show_error_dialog(parent, title, message, details=None):
        """Hiển thị dialog lỗi chi tiết"""
        dialog = tk.Toplevel(parent)
        dialog.title(title)
        dialog.geometry("500x300")
        dialog.transient(parent)
        dialog.grab_set()
        
        GUIUtils.center_window(dialog, parent)
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Error icon and message
        header_frame = ttk.Frame(frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(header_frame, text="❌", font=("Arial", 24)).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(header_frame, text=message, font=("Arial", 11), wraplength=400).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Details (if provided)
        if details:
            ttk.Label(frame, text="Chi tiết:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
            
            text_frame = ttk.Frame(frame)
            text_frame.pack(fill=tk.BOTH, expand=True)
            
            text_widget = tk.Text(text_frame, wrap=tk.WORD, height=8)
            scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)
            
            text_widget.insert("1.0", details)
            text_widget.config(state=tk.DISABLED)
            
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # OK button
        ttk.Button(frame, text="OK", command=dialog.destroy).pack(pady=(20, 0))
    
    @staticmethod
    def ask_yes_no(parent, title, message):
        """Hỏi Yes/No với dialog tùy chỉnh"""
        result = tk.BooleanVar()
        
        dialog = tk.Toplevel(parent)
        dialog.title(title)
        dialog.geometry("400x150")
        dialog.transient(parent)
        dialog.grab_set()
        
        GUIUtils.center_window(dialog, parent)
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Question
        ttk.Label(frame, text="❓", font=("Arial", 24)).pack(pady=(0, 10))
        ttk.Label(frame, text=message, font=("Arial", 11), wraplength=350, justify=tk.CENTER).pack(pady=(0, 20))
        
        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack()
        
        def yes():
            result.set(True)
            dialog.destroy()
        
        def no():
            result.set(False)
            dialog.destroy()
        
        ttk.Button(button_frame, text="Có", command=yes).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Không", command=no).pack(side=tk.LEFT)
        
        # Wait for result
        dialog.wait_window()
        return result.get()
