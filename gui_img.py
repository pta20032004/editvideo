# gui_img.py

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
# Giả sử file insert_img.py chứa 2 hàm này và nằm cùng thư mục
from insert_img import insert_image, batch_insert_image
import os

class ImageInserterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Kiểm thử Chèn ảnh")
        self.root.geometry("1000x700")

        self.image_file_types = [
            ("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif;*.webp"),
            ("All files", "*.*")
        ]
        self.save_file_types = [
            ("PNG file", "*.png"),
            ("JPEG file", "*.jpg"),
            ("WEBP file", "*.webp")
        ]

        # Biến lưu trạng thái
        self.base_image_path = tk.StringVar()
        self.base_folder_path = tk.StringVar()
        self.overlay_image_path = tk.StringVar()
        # --- THÊM MỚI 1: Biến lưu đường dẫn thư mục đầu ra ---
        self.output_folder_path = tk.StringVar(value="output_img")
        self.position = tk.StringVar(value='bottom_right')
        self.resize_percentage = tk.DoubleVar(value=5.0)
        self.proportional_resize = tk.BooleanVar(value=True)
        self.preview_photo_image = None
        self.current_result_image = None

        # --- Giao diện ---
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Tăng chiều rộng để có không gian cho widget mới
        controls_frame = ttk.Frame(main_frame, width=300)
        controls_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        controls_frame.pack_propagate(False)

        single_mode_frame = ttk.LabelFrame(controls_frame, text="Chế độ xử lý đơn")
        single_mode_frame.pack(fill=tk.X, pady=5)
        ttk.Button(single_mode_frame, text="1. Chọn ảnh nền", command=self.load_base_image).pack(fill=tk.X, padx=5, pady=5)
        
        base_image_frame = ttk.Frame(single_mode_frame)
        base_image_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        self.base_path_label = ttk.Label(base_image_frame, text="Chưa chọn ảnh", wraplength=250)
        self.base_path_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(base_image_frame, text="X", width=2, command=self.clear_base_image_selection).pack(side=tk.RIGHT)

        batch_mode_frame = ttk.LabelFrame(controls_frame, text="Chế độ xử lý hàng loạt")
        batch_mode_frame.pack(fill=tk.X, pady=10)
        ttk.Button(batch_mode_frame, text="1. Chọn thư mục ảnh nền", command=self.load_base_folder).pack(fill=tk.X, padx=5, pady=5)

        base_folder_frame = ttk.Frame(batch_mode_frame)
        base_folder_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        self.base_folder_label = ttk.Label(base_folder_frame, text="Chưa chọn thư mục", wraplength=250)
        self.base_folder_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(base_folder_frame, text="X", width=2, command=self.clear_base_folder_selection).pack(side=tk.RIGHT)
        
        proportional_check = ttk.Checkbutton(batch_mode_frame, text="Tự động điều chỉnh kích thước theo ảnh gốc", variable=self.proportional_resize)
        proportional_check.pack(padx=5, pady=5, anchor='w')
        
        common_config_frame = ttk.LabelFrame(controls_frame, text="Cấu hình chung")
        common_config_frame.pack(fill=tk.X, pady=5)
        ttk.Button(common_config_frame, text="2. Chọn ảnh chèn", command=self.load_overlay_image).pack(fill=tk.X, padx=5, pady=5)

        overlay_image_frame = ttk.Frame(common_config_frame)
        overlay_image_frame.pack(fill=tk.X, padx=5, pady=(0, 10))
        self.overlay_path_label = ttk.Label(overlay_image_frame, text="Chưa chọn ảnh", wraplength=250)
        self.overlay_path_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(overlay_image_frame, text="X", width=2, command=self.clear_overlay_image_selection).pack(side=tk.RIGHT)

        ttk.Label(common_config_frame, text="3. Chọn vị trí:").pack(fill=tk.X, padx=5)
        positions = ['center', 'top_left', 'top_right', 'bottom_left', 'bottom_right', 'center_top', 'center_bottom']
        position_combo = ttk.Combobox(common_config_frame, textvariable=self.position, values=positions, state="readonly")
        position_combo.pack(fill=tk.X, padx=5, pady=(0, 10))
        position_combo.bind("<<ComboboxSelected>>", self.update_preview)

        ttk.Label(common_config_frame, text="4. Thay đổi kích thước (%):").pack(fill=tk.X, padx=5, anchor='w')
        resize_frame = ttk.Frame(common_config_frame)
        resize_frame.pack(fill=tk.X, padx=5, pady=(0, 10))
        resize_spinbox = tk.Spinbox(
            resize_frame, from_=0.0, to=100.0, textvariable=self.resize_percentage,
            width=5, increment=0.1, format="%.1f", command=self.update_preview
        )
        resize_spinbox.pack(side=tk.RIGHT, padx=(5, 0))
        resize_scale = ttk.Scale(
            resize_frame, from_=0.0, to=100.0, orient=tk.HORIZONTAL,
            variable=self.resize_percentage, command=self.update_preview
        )
        resize_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.resize_percentage.trace_add("write", self.update_preview)

        # --- THÊM MỚI 2: Khung chọn thư mục đầu ra ---
        output_config_frame = ttk.LabelFrame(controls_frame, text="Cấu hình đầu ra (hàng loạt)")
        output_config_frame.pack(fill=tk.X, pady=5)

        ttk.Button(output_config_frame, text="5. Chọn thư mục lưu ảnh", command=self.select_output_folder).pack(fill=tk.X, padx=5, pady=5)
        
        output_folder_frame = ttk.Frame(output_config_frame)
        output_folder_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        self.output_folder_label = ttk.Label(output_folder_frame, text="Thư mục mặc định: output_img", wraplength=250)
        self.output_folder_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(output_folder_frame, text="X", width=2, command=self.clear_output_folder_selection).pack(side=tk.RIGHT)
        # --- KẾT THÚC THÊM MỚI ---

        self.style = ttk.Style()
        self.style.configure("Accent.TButton", foreground="blue", background="forest green")

        ttk.Button(controls_frame, text="🚀 Bắt đầu xử lý hàng loạt", command=self.start_batch_processing, style="Accent.TButton").pack(fill=tk.X, pady=(15, 5))
        
        preview_frame = ttk.LabelFrame(main_frame, text="Xem trước")
        preview_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.preview_label = ttk.Label(preview_frame, text="\n\nVui lòng chọn ảnh để xem trước", anchor='center')
        self.preview_label.pack(fill=tk.BOTH, expand=True)

    def clear_preview(self):
        self.preview_label.config(image=None, text="\n\nVui lòng chọn ảnh để xem trước")
        self.preview_photo_image = None
        self.current_result_image = None

    def clear_base_image_selection(self):
        self.base_image_path.set("")
        self.base_path_label.config(text="Chưa chọn ảnh")
        self.clear_preview()
        
    def clear_base_folder_selection(self):
        self.base_folder_path.set("")
        self.base_folder_label.config(text="Chưa chọn thư mục")
        self.clear_base_image_selection()

    def clear_overlay_image_selection(self):
        self.overlay_image_path.set("")
        self.overlay_path_label.config(text="Chưa chọn ảnh")
        self.update_preview() # Cập nhật lại preview

    # --- THÊM MỚI 3: Các hàm xử lý cho thư mục đầu ra ---
    def select_output_folder(self):
        path = filedialog.askdirectory(title="Chọn thư mục để lưu ảnh")
        if path:
            self.output_folder_path.set(path)
            self.output_folder_label.config(text=path)
    
    def clear_output_folder_selection(self):
        default_path = "output_img"
        self.output_folder_path.set(default_path)
        self.output_folder_label.config(text=f"Thư mục mặc định: {default_path}")
    # --- KẾT THÚC THÊM MỚI ---

    def find_first_image_in_folder(self, folder_path):
        valid_extensions = tuple(ext.replace('*', '') for ext in self.image_file_types[0][1].split(';'))
        try:
            for filename in sorted(os.listdir(folder_path)):
                if filename.lower().endswith(valid_extensions):
                    return os.path.join(folder_path, filename)
        except OSError: return None
        return None

    def load_base_image(self):
        path = filedialog.askopenfilename(filetypes=self.image_file_types)
        if path:
            self.base_image_path.set(path)
            self.base_path_label.config(text=os.path.basename(path))
            self.base_folder_path.set("")
            self.base_folder_label.config(text="Chưa chọn thư mục")
            self.update_preview()

    def load_base_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.base_folder_path.set(path)
            self.base_folder_label.config(text=path)
            first_image_for_preview = self.find_first_image_in_folder(path)
            if first_image_for_preview:
                self.base_image_path.set(first_image_for_preview)
                self.update_preview()
            else:
                self.base_image_path.set("")
                self.clear_preview()
                messagebox.showwarning("Không tìm thấy ảnh", "Thư mục bạn chọn không chứa file ảnh nào được hỗ trợ.")

    def load_overlay_image(self):
        path = filedialog.askopenfilename(filetypes=self.image_file_types)
        if path:
            self.overlay_image_path.set(path)
            self.overlay_path_label.config(text=os.path.basename(path))
            self.update_preview()

    def update_preview(self, *args):
        try:
            current_value = self.resize_percentage.get()
        except (tk.TclError, ValueError): return
        rounded_value = round(current_value, 1)
        if abs(current_value - rounded_value) > 1e-6:
            self.resize_percentage.set(rounded_value)
            return

        base_path = self.base_image_path.get()
        overlay_path = self.overlay_image_path.get()

        if not base_path:
            self.clear_preview()
            return

        result_image = None
        try:
            if overlay_path and os.path.exists(overlay_path):
                 result_image = insert_image(
                    base_image_path=base_path,
                    overlay_image_path=overlay_path,
                    position=self.position.get(),
                    resize_percentage=rounded_value
                )
            else:
                # Nếu không có ảnh chèn, chỉ hiển thị ảnh nền
                result_image = Image.open(base_path)

            if result_image:
                self.current_result_image = result_image
                preview_width = self.preview_label.winfo_width()
                preview_height = self.preview_label.winfo_height()
                if preview_width < 50 or preview_height < 50:
                    preview_width, preview_height = 700, 650
                display_image = result_image.copy()
                display_image.thumbnail((preview_width - 20, preview_height - 20), Image.LANCZOS)
                self.preview_photo_image = ImageTk.PhotoImage(display_image)
                self.preview_label.config(image=self.preview_photo_image, text="")
        except Exception as e:
            print(f"Lỗi khi cập nhật preview: {e}")
            self.clear_preview()
            self.preview_label.config(text=f"\n\nLỗi hiển thị ảnh:\n{os.path.basename(base_path)}")


    # --- CẬP NHẬT 4: Hàm xử lý hàng loạt ---
    def start_batch_processing(self):
        folder_path = self.base_folder_path.get()
        overlay_path = self.overlay_image_path.get()
        if not folder_path or not overlay_path:
            messagebox.showerror("Thiếu thông tin", "Vui lòng chọn cả 'Thư mục ảnh nền' và 'Ảnh chèn' để xử lý hàng loạt.")
            return
            
        # Lấy đường dẫn thư mục đầu ra từ biến
        output_dir = self.output_folder_path.get()
        if not output_dir:
            output_dir = "output_img" # Fallback nếu rỗng

        try:
            preview_path = self.base_image_path.get()
            if self.proportional_resize.get() and (not preview_path or not os.path.exists(preview_path)):
                 preview_path = self.find_first_image_in_folder(folder_path)
                 if not preview_path:
                     messagebox.showerror("Lỗi", "Không tìm thấy ảnh nào để làm tham chiếu cho việc resize tỷ lệ.")
                     return

            count = batch_insert_image(
                base_folder_path=folder_path,
                overlay_image_path=overlay_path,
                output_folder_path=output_dir, # Sử dụng đường dẫn đã chọn
                position=self.position.get(),
                resize_percentage=self.resize_percentage.get(),
                proportional_resize=self.proportional_resize.get(),
                preview_base_image_path=preview_path
            )
            if count > 0:
                messagebox.showinfo("Hoàn thành", f"Đã xử lý thành công {count} ảnh.\nKết quả được lưu tại thư mục:\n'{os.path.abspath(output_dir)}'.")
            else:
                messagebox.showwarning("Không có ảnh nào được xử lý", "Không tìm thấy file ảnh hợp lệ trong thư mục đã chọn hoặc đã có lỗi xảy ra.")
        except Exception as e:
            messagebox.showerror("Lỗi xử lý hàng loạt", f"Đã xảy ra lỗi: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageInserterApp(root)
    root.mainloop()