#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module xử lý video overlay (chèn video và ảnh)
"""

import os
import subprocess
import glob



# Màu chroma key phổ biến
CHROMA_COLORS = {
    "green": "0x00ff00",      # Xanh lá cây (phổ biến nhất)
    "blue": "0x0000ff",       # Xanh dương
    "cyan": "0x00ffff",       # Xanh cyan
    "red": "0xff0000",        # Đỏ
    "magenta": "0xff00ff",    # Tím/Magenta
    "yellow": "0xffff00",     # Vàng
    "white": "0xffffff",      # Trắng
    "black": "0x000000"       # Đen
}

# Không cần thiết nữa
CHROMA_PRESETS = {
    "loose": (0.3, 0.3),         # Độ nhạy thấp - loại bỏ ít màu
    "custom": (0.2, 0.2),        # Độ nhạy lí tưởng cho GREEN
    "normal": (0.1, 0.1),        # Độ nhạy bình thường - cân bằng
    "strict": (0.05, 0.05),      # Độ nhạy cao - loại bỏ nhiều màu
    "very_strict": (0.01, 0.01), # Độ nhạy rất cao - rất nghiêm ngặt BLACK
    "ultra_strict": (0.005, 0.005), # Độ nhạy cực cao - khử hoàn toàn
    "perfect": (0.001, 0.001)    # Độ nhạy hoàn hảo - khử tuyệt đối
}

def test_get_video_duration(video_path):
    """Test function to debug video duration detection"""
    print(f"Testing video duration for: {video_path}")
    
    # Method 1: Try ffprobe
    try:
        cmd = ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'csv=p=0', video_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            duration = float(result.stdout.strip())
            print(f"Method 1 (ffprobe): {duration:.2f}s")
            return duration
    except Exception as e:
        print(f"Method 1 failed: {e}")
    
    # Method 2: Try ffmpeg
    try:
        ffmpeg_path = find_ffmpeg()
        ffprobe_path = ffmpeg_path.replace('ffmpeg', 'ffprobe') if 'ffmpeg' in ffmpeg_path else 'ffprobe'
        cmd = [ffprobe_path, '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'csv=p=0', video_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            duration = float(result.stdout.strip())
            print(f"Method 2 (ffprobe from ffmpeg path): {duration:.2f}s")
            return duration
    except Exception as e:
        print(f"Method 2 failed: {e}")
    
    # Method 3: Try ffmpeg info
    try:
        ffmpeg_path = find_ffmpeg()
        cmd = [ffmpeg_path, '-i', video_path, '-f', 'null', '-']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Parse duration from stderr
        import re
        duration_match = re.search(r'Duration: (\d+):(\d+):(\d+)\.(\d+)', result.stderr)
        if duration_match:
            hours, minutes, seconds, milliseconds = duration_match.groups()
            total_seconds = int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(milliseconds) / 100
            print(f"Method 3 (ffmpeg parse): {total_seconds:.2f}s")
            return total_seconds
    except Exception as e:
        print(f"Method 3 failed: {e}")
    
    print("All methods failed!")
    return None

def get_video_duration(video_path):
    """Lấy duration của video bằng ffprobe"""
    try:
        # Method 1: Try ffprobe directly
        try:
            cmd = ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'csv=p=0', video_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and result.stdout.strip():
                duration = float(result.stdout.strip())
                print(f"Video duration for {os.path.basename(video_path)}: {duration:.2f}s")
                return duration
        except Exception as e:
            print(f"ffprobe direct failed: {e}")
        
        # Method 2: Try ffprobe from ffmpeg path
        try:
            ffmpeg_path = find_ffmpeg()
            ffprobe_path = ffmpeg_path.replace('ffmpeg', 'ffprobe') if 'ffmpeg' in ffmpeg_path else 'ffprobe'
            cmd = [ffprobe_path, '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'csv=p=0', video_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and result.stdout.strip():
                duration = float(result.stdout.strip())
                print(f"Video duration for {os.path.basename(video_path)}: {duration:.2f}s")
                return duration
        except Exception as e:
            print(f"ffprobe from ffmpeg path failed: {e}")
        
        # Method 3: Parse from ffmpeg output
        try:
            ffmpeg_path = find_ffmpeg()
            cmd = [ffmpeg_path, '-i', video_path, '-f', 'null', '-']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            # Parse duration from stderr
            import re
            duration_match = re.search(r'Duration: (\d+):(\d+):(\d+)\.(\d+)', result.stderr)
            if duration_match:
                hours, minutes, seconds, milliseconds = duration_match.groups()
                total_seconds = int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(milliseconds) / 100
                print(f"Video duration for {os.path.basename(video_path)}: {total_seconds:.2f}s (parsed)")
                return total_seconds
        except Exception as e:
            print(f"ffmpeg parse failed: {e}")
        
        print(f"Could not get video duration for {video_path}")
        return None
        
    except Exception as e:
        print(f"Could not get video duration: {e}")
        return None
    
def add_video_overlay_with_chroma(main_video_path, overlay_video_path, output_path, 
                                 start_time=0, duration=None, position="center", 
                                 size_percent=30, chroma_key=True, chroma_color="0x00ff00",
                                 chroma_similarity=0.2, chroma_blend=0.2, 
                                 color=None, similarity=None, auto_hide=True,
                                 # NEW: Custom position and size parameters
                                 position_mode="preset", custom_x=None, custom_y=None,
                                 size_mode="percentage", custom_width=None, custom_height=None):
    """
    Chèn video overlay vào video chính với tùy chọn chroma key và vị trí/kích thước tùy chỉnh
    
    Args:
        main_video_path (str): Đường dẫn video chính
        overlay_video_path (str): Đường dẫn video overlay
        output_path (str): Đường dẫn lưu kết quả
        start_time (float): Thời gian bắt đầu (giây)
        duration (float): Thời lượng hiển thị tối đa (None = toàn bộ video)
        position (str): Vị trí preset ('center', 'top-left', 'top-right', 'bottom-left', 'bottom-right')
        size_percent (int): Kích thước theo % chiều cao video chính
        chroma_key (bool): Có áp dụng chroma key không
        chroma_color (str): Màu chroma key (hex format)
        chroma_similarity (float): Độ tương tự màu (0.01-0.5)
        chroma_blend (float): Độ mờ biên (0.01-0.5)
        auto_hide (bool): Tự động ẩn khi video overlay kết thúc
        
        # NEW: Custom positioning
        position_mode (str): "preset" hoặc "custom"
        custom_x (int): Tọa độ X tùy chỉnh (nếu position_mode="custom")
        custom_y (int): Tọa độ Y tùy chỉnh (nếu position_mode="custom")
        
        # NEW: Custom sizing
        size_mode (str): "percentage" hoặc "custom"
        custom_width (int): Chiều rộng tùy chỉnh (nếu size_mode="custom")
        custom_height (int): Chiều cao tùy chỉnh (nếu size_mode="custom")
    """
    
    # Support for backward compatibility aliases
    if color is not None:
        chroma_color = color
    if similarity is not None:
        chroma_similarity = similarity
        chroma_blend = similarity

    # Validation
    try:
        chroma_similarity = float(chroma_similarity)
        chroma_blend = float(chroma_blend)
        chroma_similarity = max(0.0005, min(0.5, chroma_similarity))
        chroma_blend = max(0.0005, min(0.5, chroma_blend))
    except (ValueError, TypeError):
        print(f"Invalid chroma values, using defaults")
        chroma_similarity = 0.1
        chroma_blend = 0.1

    try:
        ffmpeg_path = find_ffmpeg()
        
        # Calculate overlay duration with auto_hide
        if auto_hide:
            overlay_duration = get_video_duration(overlay_video_path)
            if overlay_duration:
                if duration:
                    actual_duration = min(duration, overlay_duration)
                else:
                    actual_duration = overlay_duration
                print(f"Auto-hide enabled: overlay duration={overlay_duration:.2f}s, using duration={actual_duration:.2f}s")
            else:
                actual_duration = duration
                print(f"Could not get overlay duration, using user duration={duration}")
        else:
            actual_duration = duration
            print(f"Auto-hide disabled, using user duration={duration}")
        
        # Determine position based on mode
        if position_mode == "custom" and custom_x is not None and custom_y is not None:
            x_pos = str(custom_x)
            y_pos = str(custom_y)
            print(f"📍 Using custom position: X={custom_x}, Y={custom_y}")
        else:
            # Use preset positions
            if position == "center":
                x_pos = "(main_w-overlay_w)/2"
                y_pos = "(main_h-overlay_h)/2"
            elif position == "top-left":
                x_pos = "10"
                y_pos = "10"
            elif position == "top-right":
                x_pos = "main_w-overlay_w-10"
                y_pos = "10"
            elif position == "bottom-left":
                x_pos = "10"
                y_pos = "main_h-overlay_h-10"
            elif position == "bottom-right":
                x_pos = "main_w-overlay_w-10"
                y_pos = "main_h-overlay_h-10"
            else:
                x_pos = "(main_w-overlay_w)/2"
                y_pos = "(main_h-overlay_h)/2"
            print(f"📍 Using preset position: {position}")
        
        # Create filter complex
        filter_parts = []
        
        # Determine scaling method based on size mode
        if size_mode == "custom" and custom_width is not None and custom_height is not None:
            scale_filter = f"[1:v]scale={custom_width}:{custom_height}[scaled]"
            print(f"📏 Using custom size: W={custom_width}, H={custom_height}")
        else:
            # Use percentage scaling
            scale_factor = size_percent / 100.0
            scale_filter = f"[1:v]scale=-1:ih*{scale_factor}[scaled]"
            print(f"📏 Using percentage size: {size_percent}%")
        
        filter_parts.append(scale_filter)
        
        # ===== ĐIỂM THAY ĐỔI 1: THÊM FILTER SETPTS ĐỂ RESET TIMELINE =====
        # Reset timeline của overlay video bằng setpts để luôn bắt đầu từ frame đầu
        setpts_filter = f"[scaled]setpts=PTS-STARTPTS+{start_time}/TB[timed_scaled]"
        filter_parts.append(setpts_filter)
        
        # Apply chroma key if needed
        if chroma_key:
            chromakey_filter = f"[timed_scaled]chromakey={chroma_color}:{chroma_similarity}:{chroma_blend}[keyed]"
            filter_parts.append(chromakey_filter)
            overlay_input = "keyed"
        else:
            overlay_input = "timed_scaled"
        
        # Create overlay with timing
        if actual_duration:
            end_time = start_time + actual_duration
            time_condition = f"enable='between(t,{start_time},{end_time})'"
        else:
            time_condition = f"enable='gte(t,{start_time})'"
        
        overlay_filter = f"[0:v][{overlay_input}]overlay={x_pos}:{y_pos}:{time_condition}"
        filter_parts.append(overlay_filter)
        
        filter_complex = ";".join(filter_parts)
        
        # Create FFmpeg command
        cmd = [
            ffmpeg_path,
            '-i', main_video_path,
            '-i', overlay_video_path,
            '-filter_complex', filter_complex,
            '-c:a', 'copy',
            '-y',
            output_path
        ]
        
        print(f"🎬 Đang chèn video overlay...")
        print(f"📂 Video chính: {main_video_path}")
        print(f"🎭 Video overlay: {overlay_video_path}")
        if auto_hide and actual_duration:
            print(f"⏰ Thời gian: {start_time}s - {start_time + actual_duration:.2f}s (auto-hide)")
        else:
            print(f"⏰ Thời gian: {start_time}s - {start_time + (actual_duration or 0):.2f}s")
        
        if position_mode == "custom":
            print(f"📍 Vị trí tùy chỉnh: X={custom_x}, Y={custom_y}")
        else:
            print(f"📍 Vị trí preset: {position}")
            
        if size_mode == "custom":
            print(f"📏 Kích thước tùy chỉnh: {custom_width}x{custom_height}")
        else:
            print(f"📏 Kích thước: {size_percent}%")
            
        print(f"🔥 Chroma key: {'Có' if chroma_key else 'Không'}")
        if chroma_key:
            print(f"🎨 Màu chroma: {chroma_color}")
            print(f"🔧 Độ nhạy: {chroma_similarity}/{chroma_blend}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Lỗi chèn video overlay: {result.stderr}")
        
        print(f"✅ Chèn video overlay thành công: {output_path}")
        
    except Exception as e:
        raise Exception(f"Không thể chèn video overlay: {str(e)}")
    
def add_image_overlay(main_video_path, image_path, output_path, 
                     start_time=0, duration=5, position="center", size_percent=20):
    """
    Chèn ảnh overlay vào video
    """
    try:
        ffmpeg_path = find_ffmpeg()
        
        # Tính toán vị trí
        if position == "center":
            x_pos = "(main_w-overlay_w)/2"
            y_pos = "(main_h-overlay_h)/2"
        elif position == "top-left":
            x_pos = "10"
            y_pos = "10"
        elif position == "top-right":
            x_pos = "main_w-overlay_w-10"
            y_pos = "10"
        elif position == "bottom-left":
            x_pos = "10"
            y_pos = "main_h-overlay_h-10"
        elif position == "bottom-right":
            x_pos = "main_w-overlay_w-10"
            y_pos = "main_h-overlay_h-10"
        else:
            x_pos = "(main_w-overlay_w)/2"
            y_pos = "(main_h-overlay_h)/2"
        
        # Scale ảnh
        scale_factor = size_percent / 100.0
        scale_filter = f"[1:v]scale=iw*{scale_factor}:ih*{scale_factor}[scaled]"
        
        # Overlay với thời gian
        end_time = start_time + duration
        overlay_filter = f"[0:v][scaled]overlay={x_pos}:{y_pos}:enable='between(t,{start_time},{end_time})'"
        
        filter_complex = f"{scale_filter};{overlay_filter}"
        
        cmd = [
            ffmpeg_path,
            '-i', main_video_path,
            '-i', image_path,
            '-filter_complex', filter_complex,
            '-c:a', 'copy',
            '-y',
            output_path
        ]
        
        print(f"🖼️ Đang chèn ảnh overlay...")
        print(f"📂 Video: {main_video_path}")
        print(f"🖼️ Ảnh: {image_path}")
        print(f"⏰ Thời gian: {start_time}s - {end_time}s")
        print(f"📍 Vị trí: {position}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Lỗi chèn ảnh overlay: {result.stderr}")
        
        print(f"✅ Chèn ảnh overlay thành công!")
        
    except Exception as e:
        raise Exception(f"Không thể chèn ảnh overlay: {str(e)}")



def find_ffmpeg():
    """Tìm đường dẫn FFmpeg"""
    import shutil
    
    ffmpeg_path = shutil.which('ffmpeg')
    if ffmpeg_path:
        return ffmpeg_path
    
    # Thử các đường dẫn phổ biến
    common_paths = [
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",
        os.path.join(os.getcwd(), "ffmpeg", "bin", "ffmpeg.exe"),
        os.path.join(os.getcwd(), "ffmpeg.exe")
    ]
    
    for path in common_paths:
        if os.path.exists(path):
            return path
    
    raise FileNotFoundError("FFmpeg không được tìm thấy")

def get_chroma_color(color_name):
    """
    Lấy mã màu hex từ tên màu
    
    Args:
        color_name (str): Tên màu ('green', 'blue', 'cyan', etc.)
        
    Returns:
        str: Mã màu hex
    """
    return CHROMA_COLORS.get(color_name.lower(), "0x00ff00")

def get_chroma_preset(preset_name):
    """
    Lấy preset độ nhạy chroma key
    
    Args:
        preset_name (str): Tên preset ('loose', 'normal', 'strict', 'very_strict')
        
    Returns:
        tuple: (similarity, blend)
    """
    return CHROMA_PRESETS.get(preset_name.lower(), (0.2, 0.2))

def add_video_overlay_easy_chroma(main_video_path, overlay_video_path, output_path,
                                 start_time=0, duration=None, position="center", 
                                 size_percent=30, chroma_color_name="green", 
                                 chroma_preset="normal"):
    """
    Chèn video overlay với chroma key đơn giản sử dụng tên màu và preset
    
    Args:
        main_video_path (str): Đường dẫn video chính
        overlay_video_path (str): Đường dẫn video overlay
        output_path (str): Đường dẫn lưu kết quả
        start_time (float): Thời gian bắt đầu (giây)
        duration (float): Thời lượng hiển thị
        position (str): Vị trí overlay
        size_percent (int): Kích thước %
        chroma_color_name (str): Tên màu ('green', 'blue', 'cyan', etc.)
        chroma_preset (str): Preset độ nhạy ('loose', 'normal', 'strict', 'very_strict')
    """
    chroma_color = get_chroma_color(chroma_color_name)
    similarity, blend = get_chroma_preset(chroma_preset)
    
    return add_video_overlay_with_chroma(
        main_video_path=main_video_path,
        overlay_video_path=overlay_video_path,
        output_path=output_path,
        start_time=start_time,
        duration=duration,
        position=position,
        size_percent=size_percent,
        chroma_key=True,
        chroma_color=chroma_color,
        chroma_similarity=similarity,
        chroma_blend=blend
    )

def add_image_overlay_with_animation(main_video_path, image_path, output_path,
                                   start_time=0, duration=5, position="center", 
                                   size_percent=20, animation="fade_in", 
                                   animation_duration=1.0):
    """
    Chèn ảnh overlay với hiệu ứng animation
    
    Args:
        main_video_path (str): Đường dẫn video chính
        image_path (str): Đường dẫn ảnh overlay
        output_path (str): Đường dẫn kết quả
        start_time (float): Thời gian bắt đầu (giây)
        duration (float): Thời lượng hiển thị (giây)
        position (str): Vị trí ('center', 'top-left', 'top-right', 'bottom-left', 'bottom-right')
        size_percent (int): Kích thước theo % 
        animation (str): Loại animation ('fade_in', 'fade_out', 'fade_in_out', 'slide_left', 
                        'slide_right', 'slide_up', 'slide_down', 'zoom_in', 'zoom_out', 
                        'rotate_in', 'bounce', 'pulse')
        animation_duration (float): Thời lượng animation (giây)
    """
    try:
        ffmpeg_path = find_ffmpeg()
        
        # Tính toán vị trí
        position_map = {
            "center": ("(main_w-overlay_w)/2", "(main_h-overlay_h)/2"),
            "top-left": ("20", "20"),
            "top-right": ("main_w-overlay_w-20", "20"),
            "bottom-left": ("20", "main_h-overlay_h-20"),
            "bottom-right": ("main_w-overlay_w-20", "main_h-overlay_h-20")
        }
        x_pos, y_pos = position_map.get(position, position_map["center"])
        
        # Tạo animation filters
        animation_filter = _create_animation_filter(animation, start_time, duration, animation_duration, size_percent)
        
        # Scale ảnh
        scale_factor = size_percent / 100.0
        scale_filter = f"[1:v]scale=iw*{scale_factor}:ih*{scale_factor}[scaled]"
        
        # Kết hợp filters
        end_time = start_time + duration
        overlay_filter = f"[0:v][animated]overlay={x_pos}:{y_pos}:enable='between(t,{start_time},{end_time})'"
        
        filter_complex = f"{scale_filter};{animation_filter};{overlay_filter}"
        
        cmd = [
            ffmpeg_path,
            '-i', main_video_path,
            '-i', image_path,
            '-filter_complex', filter_complex,
            '-c:a', 'copy',
            '-y',
            output_path
        ]
        
        print(f"✨ Đang chèn ảnh với animation {animation}...")
        print(f"📂 Video: {main_video_path}")
        print(f"🖼️ Ảnh: {image_path}")
        print(f"⏰ Thời gian: {start_time}s - {end_time}s")
        print(f"📍 Vị trí: {position}")
        print(f"🎬 Animation: {animation} ({animation_duration}s)")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Lỗi chèn ảnh với animation: {result.stderr}")
        
        print(f"✅ Chèn ảnh với animation thành công!")
        return True
        
    except Exception as e:
        print(f"❌ Lỗi: {str(e)}")
        return False

def _create_animation_filter(animation, start_time, duration, animation_duration, size_percent):
    """Tạo filter animation cho ảnh"""
    
    # Animation timings
    fade_start = start_time
    fade_end = start_time + animation_duration
    main_start = fade_end
    main_end = start_time + duration - animation_duration
    fade_out_start = main_end
    fade_out_end = start_time + duration
    
    if animation == "fade_in":
        return f"[scaled]fade=t=in:st={fade_start}:d={animation_duration}:alpha=1[animated]"
    
    elif animation == "fade_out":
        return f"[scaled]fade=t=out:st={fade_out_start}:d={animation_duration}:alpha=1[animated]"
    
    elif animation == "fade_in_out":
        return f"[scaled]fade=t=in:st={fade_start}:d={animation_duration}:alpha=1,fade=t=out:st={fade_out_start}:d={animation_duration}:alpha=1[animated]"
    
    elif animation == "slide_left":
        return f"[scaled]overlay=x='if(lt(t,{fade_end}),w-(w*(t-{fade_start})/{animation_duration}),0)':y=0[animated]"
    
    elif animation == "slide_right":
        return f"[scaled]overlay=x='if(lt(t,{fade_end}),-w+(w*(t-{fade_start})/{animation_duration}),0)':y=0[animated]"
    
    elif animation == "slide_up":
        return f"[scaled]overlay=x=0:y='if(lt(t,{fade_end}),h-(h*(t-{fade_start})/{animation_duration}),0)'[animated]"
    
    elif animation == "slide_down":
        return f"[scaled]overlay=x=0:y='if(lt(t,{fade_end}),-h+(h*(t-{fade_start})/{animation_duration}),0)'[animated]"
    
    elif animation == "zoom_in":
        zoom_factor = f"if(lt(t,{fade_end}),0.1+0.9*(t-{fade_start})/{animation_duration},1)"
        return f"[scaled]scale=iw*{zoom_factor}:ih*{zoom_factor}[animated]"
    
    elif animation == "zoom_out":
        zoom_factor = f"if(gt(t,{fade_out_start}),1-0.9*(t-{fade_out_start})/{animation_duration},1)"
        return f"[scaled]scale=iw*{zoom_factor}:ih*{zoom_factor}[animated]"
    
    elif animation == "rotate_in":
        angle = f"if(lt(t,{fade_end}),2*PI*(t-{fade_start})/{animation_duration},0)"
        return f"[scaled]rotate={angle}:fillcolor=none[animated]"
    
    elif animation == "bounce":
        # Tạo hiệu ứng bounce đơn giản
        y_offset = f"if(lt(t,{fade_end}),abs(sin(4*PI*(t-{fade_start})/{animation_duration}))*50,0)"
        return f"[scaled]overlay=x=0:y={y_offset}[animated]"
    
    elif animation == "pulse":
        # Hiệu ứng pulse (thay đổi kích thước)
        pulse_scale = f"1+0.2*sin(4*PI*(t-{fade_start})/{animation_duration})"
        return f"[scaled]scale=iw*{pulse_scale}:ih*{pulse_scale}[animated]"
    
    else:
        # Mặc định: fade_in
        return f"[scaled]fade=t=in:st={fade_start}:d={animation_duration}:alpha=1[animated]"

def _create_animation_filter_for_multiple(animation, start_time, duration, animation_duration, input_label, output_label):
    """Tạo animation filter cho multiple overlay"""
    
    fade_start = start_time
    fade_end = start_time + animation_duration
    fade_out_start = start_time + duration - animation_duration
    
    if animation == "fade_in":
        return f"[{input_label}]fade=t=in:st={fade_start}:d={animation_duration}:alpha=1[{output_label}]"
    
    elif animation == "fade_out":
        return f"[{input_label}]fade=t=out:st={fade_out_start}:d={animation_duration}:alpha=1[{output_label}]"
    
    elif animation == "fade_in_out":
        return f"[{input_label}]fade=t=in:st={fade_start}:d={animation_duration}:alpha=1,fade=t=out:st={fade_out_start}:d={animation_duration}:alpha=1[{output_label}]"
    
    elif animation == "zoom_in":
        zoom_factor = f"if(lt(t,{fade_end}),0.3+0.7*(t-{fade_start})/{animation_duration},1)"
        return f"[{input_label}]scale=iw*{zoom_factor}:ih*{zoom_factor}[{output_label}]"
    
    elif animation == "pulse":
        pulse_scale = f"1+0.3*sin(6*PI*(t-{fade_start})/2)"
        return f"[{input_label}]scale=iw*{pulse_scale}:ih*{pulse_scale}[{output_label}]"
    
    else:
        # Mặc định
        return f"[{input_label}]fade=t=in:st={fade_start}:d={animation_duration}:alpha=1[{output_label}]"


def add_multiple_overlays(main_video_path, subtitle_path, output_path, overlay_folder, overlay_times):
    """
    Chèn nhiều video/ảnh overlay cùng lúc - ĐÃ SỬA STYLES
    """
    try:
        ffmpeg_path = find_ffmpeg()
        
        # Tìm tất cả file media
        media_files = []
        for ext in ['*.png', '*.jpg', '*.jpeg', '*.gif', '*.bmp', '*.mp4', '*.avi', '*.mov', '*.mkv', '*.wmv']:
            media_files.extend(glob.glob(os.path.join(overlay_folder, ext)))
        
        if not media_files:
            print("⚠️ Không tìm thấy file overlay nào")
            return False
        
        # Chuẩn bị inputs
        inputs = ['-i', main_video_path]
        overlay_configs = []
        
        for media_file in media_files:
            filename = os.path.basename(media_file)
            if filename in overlay_times:
                inputs.extend(['-i', media_file])
                overlay_configs.append({
                    'file': media_file,
                    'filename': filename,
                    'start': overlay_times[filename]['start'],
                    'duration': overlay_times[filename]['duration'],
                    'is_video': media_file.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.wmv'))
                })
        
        if not overlay_configs:
            print("⚠️ Không có file overlay nào được cấu hình thời gian")
            return False
        
        # Tạo filter complex
        filter_parts = []
        
        # Bước 1: Thêm subtitles - ĐÃ SỬA
        subtitle_path_escaped = subtitle_path.replace('\\', '/').replace(':', '\\:')
        
        # SỬA: Sử dụng style system thay vì hardcode
        from subtitle_styles import get_preset_style
        style_string = get_preset_style("default")
        
        # BEFORE: 
        # subtitle_filter = f"[0:v]subtitles='{subtitle_path_escaped}':force_style='FontName=Arial,FontSize=8,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=1,Shadow=1,MarginV=50'[sub]"
        
        # AFTER:
        subtitle_filter = f"[0:v]subtitles='{subtitle_path_escaped}':force_style='{style_string}'[sub]"
        filter_parts.append(subtitle_filter)
        
        # Bước 2: Xử lý overlay
        current_input = "sub"
        for i, config in enumerate(overlay_configs):
            input_index = i + 1
            
            if config['is_video']:
                # Video overlay với chroma key
                scale_filter = f"[{input_index}:v]scale=-1:ih*0.3[scaled{i}]"
                filter_parts.append(scale_filter)
                
                chromakey_filter = f"[scaled{i}]chromakey=0x00ff00:0.1:0.1[chroma{i}]"
                filter_parts.append(chromakey_filter)
                
                end_time = config['start'] + config['duration']
                overlay_filter = f"[{current_input}][chroma{i}]overlay=(main_w-overlay_w)/2:(main_h-overlay_h)/2:enable='between(t,{config['start']},{end_time})'"
            else:
                # Ảnh overlay
                scale_filter = f"[{input_index}]scale=iw*0.1:ih*0.1[img{i}]"
                filter_parts.append(scale_filter)
                
                end_time = config['start'] + config['duration']
                overlay_filter = f"[{current_input}][img{i}]overlay=(main_w-overlay_w)/2:(main_h-overlay_h)/2:enable='between(t,{config['start']},{end_time})'"
            
            if i < len(overlay_configs) - 1:
                overlay_filter += f"[tmp{i}]"
                current_input = f"tmp{i}"
            
            filter_parts.append(overlay_filter)
        
        filter_complex = ";".join(filter_parts)
        
        cmd = [
            ffmpeg_path,
            *inputs,
            '-filter_complex', filter_complex,
            '-c:a', 'copy',
            '-y',
            output_path
        ]
        
        print(f"🎭 Đang chèn {len(overlay_configs)} overlay...")
        for config in overlay_configs:
            media_type = "Video" if config['is_video'] else "Ảnh"
            print(f"  {media_type}: {config['filename']} ({config['start']}s, {config['duration']}s)")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Lỗi chèn multiple overlay: {result.stderr}")
        
        print(f"✅ Chèn multiple overlay thành công!")
        return True
        
    except Exception as e:
        print(f"❌ Lỗi: {str(e)}")
        return False

def add_multiple_images_with_animations(main_video_path, subtitle_path, output_path, 
                                       img_folder, overlay_times, animations=None):
    """
    Chèn nhiều ảnh với animation khác nhau - ĐÃ SỬA STYLES
    
    Args:
        animations (dict): {filename: {'type': 'fade_in', 'duration': 1.0}}
    """
    try:
        ffmpeg_path = find_ffmpeg()
        
        # Tìm ảnh
        image_files = []
        for ext in ['*.png', '*.jpg', '*.jpeg', '*.gif', '*.bmp']:
            image_files.extend(glob.glob(os.path.join(img_folder, ext)))
        
        if not image_files:
            print("⚠️ Không tìm thấy ảnh nào")
            return False
        
        # Chuẩn bị inputs và configs
        inputs = ['-i', main_video_path]
        overlay_configs = []
        
        for img_file in image_files:
            filename = os.path.basename(img_file)
            if filename in overlay_times:
                inputs.extend(['-i', img_file])
                
                # Lấy animation config
                anim_config = animations.get(filename, {'type': 'fade_in', 'duration': 1.0}) if animations else {'type': 'fade_in', 'duration': 1.0}
                
                overlay_configs.append({
                    'file': img_file,
                    'filename': filename,
                    'start': overlay_times[filename]['start'],
                    'duration': overlay_times[filename]['duration'],
                    'position': overlay_times[filename].get('position', 'center'),
                    'scale': overlay_times[filename].get('scale', 0.2),
                    'animation': anim_config['type'],
                    'animation_duration': anim_config['duration']
                })
        
        if not overlay_configs:
            print("⚠️ Không có ảnh nào được cấu hình")
            return False
        
        # Tạo filter complex với animations
        filter_parts = []
        
        # Subtitle filter - ĐÃ SỬA
        subtitle_path_escaped = subtitle_path.replace('\\', '/').replace(':', '\\:')
        
        # SỬA: Sử dụng style system với font size lớn hơn cho animations
        from subtitle_styles import get_subtitle_style_string
        style_string = get_subtitle_style_string(
            text_color="black",      # Sử dụng màu mới
            box_style="box",         # Sử dụng box thay vì outline
            box_color="white",       # Nền trắng
            font_size=10,            # Font size lớn hơn một chút cho animation
            margin_v=50
        )
        
        # BEFORE:
        # subtitle_filter = f"[0:v]subtitles='{subtitle_path_escaped}':force_style='FontName=Arial,FontSize=12,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=2,Shadow=1,MarginV=50'[sub]"
        
        # AFTER:
        subtitle_filter = f"[0:v]subtitles='{subtitle_path_escaped}':force_style='{style_string}'[sub]"
        filter_parts.append(subtitle_filter)
        
        # Xử lý từng ảnh
        current_input = "sub"
        for i, config in enumerate(overlay_configs):
            input_index = i + 1
            
            # Scale ảnh
            scale_filter = f"[{input_index}]scale=iw*{config['scale']}:ih*{config['scale']}[scaled{i}]"
            filter_parts.append(scale_filter)
            
            # Animation
            anim_filter = _create_animation_filter_for_multiple(
                config['animation'], 
                config['start'], 
                config['duration'], 
                config['animation_duration'],
                f"scaled{i}",
                f"anim{i}"
            )
            filter_parts.append(anim_filter)
            
            # Position
            position_map = {
                "center": ("(main_w-overlay_w)/2", "(main_h-overlay_h)/2"),
                "top-left": ("20", "20"),
                "top-right": ("main_w-overlay_w-20", "20"),
                "bottom-left": ("20", "main_h-overlay_h-20"),
                "bottom-right": ("main_w-overlay_w-20", "main_h-overlay_h-20")
            }
            x_pos, y_pos = position_map.get(config['position'], position_map["center"])
            
            # Overlay
            end_time = config['start'] + config['duration']
            overlay_filter = f"[{current_input}][anim{i}]overlay={x_pos}:{y_pos}:enable='between(t,{config['start']},{end_time})'"
            
            if i < len(overlay_configs) - 1:
                overlay_filter += f"[tmp{i}]"
                current_input = f"tmp{i}"
            
            filter_parts.append(overlay_filter)
        
        filter_complex = ";".join(filter_parts)
        
        cmd = [
            ffmpeg_path,
            *inputs,
            '-filter_complex', filter_complex,
            '-c:a', 'copy',
            '-y',
            output_path
        ]
        
        print(f"✨ Đang chèn {len(overlay_configs)} ảnh với animation...")
        for config in overlay_configs:
            print(f"  🖼️ {config['filename']}: {config['animation']} ({config['start']}s, {config['duration']}s)")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Lỗi: {result.stderr}")
        
        print(f"✅ Hoàn thành tất cả animation!")
        return True
        
    except Exception as e:
        print(f"❌ Lỗi: {str(e)}")
        return False

def add_images_with_custom_timeline(main_video_path, subtitle_path, output_path, img_folder):
    """
    Thêm 3 ảnh với timeline và vị trí tùy chỉnh theo yêu cầu của bạn - ĐÃ SỬA STYLES
    """
    try:
        ffmpeg_path = find_ffmpeg()
        
        # Cấu hình ảnh theo yêu cầu mới
        image_configs = [
            {
                "image": "1.png",  # Ảnh 1
                "start_time": 5,   # Bắt đầu ở giây thứ 5
                "end_time": 6,     # Kết thúc ở giây thứ 6
                "y_offset": 865,   # Vị trí Y
                "animation": "fade_in_out"
            },
            {
                "image": "2.png",  # Ảnh 2
                "start_time": 6,   # Bắt đầu ở giây thứ 6
                "end_time": 7,     # Kết thúc ở giây thứ 7
                "y_offset": 900,   # Vị trí Y (giống ảnh 3)
                "animation": "slide_left"
            },
            {
                "image": "3.png",  # Ảnh 3 
                "start_time": 7,   # Bắt đầu ở giây thứ 7
                "end_time": 8,     # Kết thúc ở giây thứ 8
                "y_offset": 900,   # Vị trí Y (giống ảnh 2)
                "animation": "zoom_in"
            }
        ]
        
        # Kiểm tra file ảnh
        inputs = ['-i', main_video_path]
        filter_parts = []
        
        # Thêm subtitle trước - ĐÃ SỬA
        if subtitle_path and os.path.exists(subtitle_path):
            subtitle_path_escaped = subtitle_path.replace('\\', '/').replace(':', '\\:')
            
            # SỬA: Sử dụng style system
            from subtitle_styles import get_subtitle_style_string
            style_string = get_subtitle_style_string(
                text_color="black",      # Màu mới
                box_style="box",         # Box thay vì outline
                box_color="white",       # Nền trắng
                font_size=10,            # Font size phù hợp
                margin_v=50
            )
            
            # BEFORE: 
            # subtitle_filter = f"[0:v]subtitles='{subtitle_path_escaped}':force_style='FontName=Arial,FontSize=12,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=2,Shadow=1,MarginV=50'[sub]"
            
            # AFTER:
            subtitle_filter = f"[0:v]subtitles='{subtitle_path_escaped}':force_style='{style_string}'[sub]"
            filter_parts.append(subtitle_filter)
            current_input = "sub"
        else:
            current_input = "0:v"
        
        # Xử lý từng ảnh
        valid_configs = []
        for i, config in enumerate(image_configs):
            img_path = os.path.join(img_folder, config["image"])
            if os.path.exists(img_path):
                inputs.extend(['-i', img_path])
                # input_index là số thứ tự của input (0=main_video, 1=image1, 2=image2, 3=image3)
                valid_configs.append({**config, 'input_index': len(inputs)//2 - 1})
                print(f"📋 Ảnh {i+1}: {config['image']} ({config['start_time']}s-{config['end_time']}s, Y={config['y_offset']})")
            else:
                print(f"⚠️ Không tìm thấy: {img_path}")
        
        if not valid_configs:
            print("❌ Không tìm thấy ảnh nào!")
            return False
        
        # Tạo filter overlay cho từng ảnh
        for i, config in enumerate(valid_configs):
            input_idx = config['input_index']
            
            # Scale ảnh (kích thước nhỏ 20% chiều cao video)
            scale_filter = f"[{input_idx}]scale=-1:ih*0.2[scaled{i}]"
            filter_parts.append(scale_filter)
            
            # Animation filter
            anim_duration = 0.5  # Thời gian animation ngắn
            if config['animation'] == 'fade_in_out':
                anim_filter = f"[scaled{i}]fade=t=in:st={config['start_time']}:d={anim_duration}:alpha=1,fade=t=out:st={config['end_time']-anim_duration}:d={anim_duration}:alpha=1[anim{i}]"
            elif config['animation'] == 'slide_left':
                # Slide từ phải sang trái
                x_expr = f"if(lt(t,{config['start_time']+anim_duration}),w-(w*(t-{config['start_time']})/{anim_duration}),0)"
                anim_filter = f"[scaled{i}]fade=t=in:st={config['start_time']}:d={anim_duration}:alpha=1,fade=t=out:st={config['end_time']-anim_duration}:d={anim_duration}:alpha=1[anim{i}]"
            elif config['animation'] == 'zoom_in':
                # Zoom từ nhỏ lên bình thường
                anim_filter = f"[scaled{i}]fade=t=in:st={config['start_time']}:d={anim_duration}:alpha=1,fade=t=out:st={config['end_time']-anim_duration}:d={anim_duration}:alpha=1[anim{i}]"
            else:
                anim_filter = f"[scaled{i}]fade=t=in:st={config['start_time']}:d={anim_duration}:alpha=1,fade=t=out:st={config['end_time']-anim_duration}:d={anim_duration}:alpha=1[anim{i}]"
            
            filter_parts.append(anim_filter)
            
            # Overlay với vị trí Y tùy chỉnh
            x_pos = "(main_w-overlay_w)/2"  # Căn giữa theo chiều ngang
            y_pos = str(config['y_offset'])  # Vị trí Y cố định
            
            overlay_filter = f"[{current_input}][anim{i}]overlay={x_pos}:{y_pos}:enable='between(t,{config['start_time']},{config['end_time']})'"
            
            if i < len(valid_configs) - 1:
                overlay_filter += f"[tmp{i}]"
                current_input = f"tmp{i}"
            
            filter_parts.append(overlay_filter)
        
        # Tạo command FFmpeg
        filter_complex = ";".join(filter_parts)
        
        print(f"🔍 Debug Filter Complex:")
        print(f"📋 Inputs: {inputs}")
        print(f"🎛️ Filter: {filter_complex}")
        print()
        
        cmd = [
            ffmpeg_path,
            *inputs,
            '-filter_complex', filter_complex,
            '-c:a', 'copy',
            '-y',
            output_path
        ]
        
        print(f"🎬 Đang xử lý {len(valid_configs)} ảnh với timeline tùy chỉnh...")
        print(f"📂 Video đầu vào: {main_video_path}")
        print(f"📁 Thư mục ảnh: {img_folder}")
        print(f"💾 Video đầu ra: {output_path}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Lỗi FFmpeg: {result.stderr}")
            return False
        
        print(f"✅ Hoàn thành! Video với 3 ảnh animation đã được tạo: {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ Lỗi: {str(e)}")
        return False

def _create_animation_filter_for_multiple(animation, start_time, duration, animation_duration, input_label, output_label):
    """Tạo animation filter cho multiple overlay"""
    
    fade_start = start_time
    fade_end = start_time + animation_duration
    fade_out_start = start_time + duration - animation_duration
    
    if animation == "fade_in":
        return f"[{input_label}]fade=t=in:st={fade_start}:d={animation_duration}:alpha=1[{output_label}]"
    
    elif animation == "fade_out":
        return f"[{input_label}]fade=t=out:st={fade_out_start}:d={animation_duration}:alpha=1[{output_label}]"
    
    elif animation == "fade_in_out":
        return f"[{input_label}]fade=t=in:st={fade_start}:d={animation_duration}:alpha=1,fade=t=out:st={fade_out_start}:d={animation_duration}:alpha=1[{output_label}]"
    
    elif animation == "zoom_in":
        zoom_factor = f"if(lt(t,{fade_end}),0.3+0.7*(t-{fade_start})/{animation_duration},1)"
        return f"[{input_label}]scale=iw*{zoom_factor}:ih*{zoom_factor}[{output_label}]"
    
    elif animation == "pulse":
        pulse_scale = f"1+0.3*sin(6*PI*(t-{fade_start})/2)"
        return f"[{input_label}]scale=iw*{pulse_scale}:ih*{pulse_scale}[{output_label}]"
    
    else:
        # Mặc định
        return f"[{input_label}]fade=t=in:st={fade_start}:d={animation_duration}:alpha=1[{output_label}]"

if __name__ == "__main__":
    # Test function
    print("📹 Module Video Overlay đã sẵn sàng!")
