#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video Editor Application - Main Entry Point
Sử dụng GUI modular
"""

import tkinter as tk
from tkinter import ttk
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gui.main_window import VideoEditorMainWindow

def main():
    """Main function"""
    # Create root window
    root = tk.Tk()
    
    # Configure style
    style = ttk.Style()
    style.theme_use('clam')  # Modern theme
    
    # Create main application
    app = VideoEditorMainWindow(root)
    
    try:
        # Start GUI event loop
        root.mainloop()
    except KeyboardInterrupt:
        print("Ứng dụng đã bị dừng bởi người dùng")
    except Exception as e:
        print(f"Lỗi không mong muốn: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
