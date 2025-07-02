# insert_img.py

from PIL import Image
import os

# --- Hàm insert_image không thay đổi ---
def insert_image(base_image_path: str,
                 overlay_image_path: str,
                 position: str = 'center',
                 resize_percentage: int = 100):
    try:
        base_image = Image.open(base_image_path).convert("RGBA")
        overlay_image = Image.open(overlay_image_path).convert("RGBA")
        base_width, base_height = base_image.size

        if resize_percentage != 100:
            original_overlay_width, original_overlay_height = overlay_image.size
            new_width = int(original_overlay_width * resize_percentage / 100)
            new_height = int(original_overlay_height * resize_percentage / 100)
            if new_width > 0 and new_height > 0:
                overlay_image = overlay_image.resize((new_width, new_height), Image.LANCZOS)

        overlay_width, overlay_height = overlay_image.size

        if position == 'center':
            x = (base_width - overlay_width) // 2
            y = (base_height - overlay_height) // 2
        elif position == 'top_left':
            x = 0; y = 0
        elif position == 'top_right':
            x = base_width - overlay_width; y = 0
        elif position == 'bottom_left':
            x = 0; y = base_height - overlay_height
        elif position == 'bottom_right':
            x = base_width - overlay_width; y = base_height - overlay_height
        elif position == 'center_top':
            x = (base_width - overlay_width) // 2; y = 0
        elif position == 'center_bottom':
            x = (base_width - overlay_width) // 2; y = base_height - overlay_height
        else:
            x = (base_width - overlay_width) // 2
            y = (base_height - overlay_height) // 2

        combined_image = base_image.copy()
        combined_image.paste(overlay_image, (x, y), overlay_image)
        return combined_image
    except Exception as e:
        print(f"Lỗi khi xử lý ảnh đơn: {e}")
        return None

# --- CẬP NHẬT HÀM BATCH_INSERT_IMAGE ---
def batch_insert_image(base_folder_path: str,
                       overlay_image_path: str,
                       output_folder_path: str,
                       position: str = 'center',
                       resize_percentage: int = 100,
                       proportional_resize: bool = False,
                       preview_base_image_path: str = None):
    """
    Chèn ảnh overlay vào tất cả ảnh trong thư mục với tùy chọn resize tỷ lệ.
    """
    if not os.path.isdir(base_folder_path) or not os.path.isfile(overlay_image_path):
        return 0

    os.makedirs(output_folder_path, exist_ok=True)
    valid_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp')
    image_files = [f for f in os.listdir(base_folder_path) if f.lower().endswith(valid_extensions)]

    width_ratio = None
    overlay_original_width = None

    # Nếu bật chế độ resize tỷ lệ, tính toán tỷ lệ dựa trên ảnh preview
    if proportional_resize and preview_base_image_path and os.path.exists(preview_base_image_path):
        try:
            preview_base_img = Image.open(preview_base_image_path)
            overlay_img = Image.open(overlay_image_path)
            
            preview_base_width, _ = preview_base_img.size
            overlay_original_width, _ = overlay_img.size

            # Tính chiều rộng của overlay trên ảnh preview
            preview_overlay_width = overlay_original_width * (resize_percentage / 100)
            
            # Tính tỷ lệ chính
            width_ratio = preview_overlay_width / preview_base_width
        except Exception as e:
            print(f"Lỗi khi tính toán tỷ lệ: {e}")
            proportional_resize = False # Tắt chế độ nếu có lỗi

    success_count = 0
    for filename in image_files:
        current_base_path = os.path.join(base_folder_path, filename)
        current_resize_percentage = resize_percentage

        # Nếu đang ở chế độ tỷ lệ, tính lại % resize cho ảnh hiện tại
        if proportional_resize and width_ratio and overlay_original_width:
            try:
                current_base_img = Image.open(current_base_path)
                current_base_width, _ = current_base_img.size
                
                # Tính chiều rộng overlay mong muốn cho ảnh hiện tại
                target_overlay_width = current_base_width * width_ratio
                
                # Tính ra % resize mới để đạt được chiều rộng đó
                current_resize_percentage = (target_overlay_width / overlay_original_width) * 100
            except Exception:
                # Nếu có lỗi đọc ảnh, dùng % mặc định
                pass

        # Gọi hàm xử lý ảnh đơn với % resize đã được tính toán
        result_image = insert_image(
            base_image_path=current_base_path,
            overlay_image_path=overlay_image_path,
            position=position,
            resize_percentage=current_resize_percentage
        )

        if result_image:
            # --- THAY ĐỔI TẠI ĐÂY ---
            # Tách tên file và phần mở rộng
            file_name_without_ext, _ = os.path.splitext(filename)
            # Tạo tên file mới
            output_filename = f"{file_name_without_ext}_processed.png"
            # --- KẾT THÚC THAY ĐỔI ---
            
            output_path = os.path.join(output_folder_path, output_filename)
            result_image.save(output_path)
            success_count += 1
            print(f"Đã xử lý: {filename} -> {output_filename}")

    return success_count