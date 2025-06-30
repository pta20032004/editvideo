import os
import subprocess
import shutil
import traceback

class VideoProcessor:
    def __init__(self):
        self.ffmpeg_path = self._find_ffmpeg()
    
    def add_subtitle_to_video(self, video_path, subtitle_path, output_path, subtitle_style=None):
        """
        Chỉ ghép phụ đề vào video (không có overlay ảnh) - PUBLIC METHOD
        
        Args:
            video_path (str): Đường dẫn đến file video 
            subtitle_path (str): Đường dẫn đến file phụ đề .srt
            output_path (str): Đường dẫn lưu video có phụ đề
            subtitle_style (dict, optional): Các tùy chọn kiểu phụ đề
                {
                    "text_color": "black",       # Màu chữ
                    "box_style": "box",          # Kiểu khung ("none", "outline", "box", "rounded_box", "shadow_box")
                    "box_color": "white",        # Màu nền
                    "font_name": "Arial",        # Font chữ
                    "font_size": 10,             # Cỡ chữ
                    "margin_v": 50,              # Khoảng cách lề dưới
                    "opacity": 255,              # Độ đục (0-255)
                    "preset": "default"          # Hoặc dùng preset có sẵn
                }
        """
        try:
            print("📝 Ghép phụ đề vào video...")
            
            # Nếu sử dụng kiểu mặc định
            if subtitle_style is None:
                subtitle_style = {"preset": "default"}
                
            # Gọi hàm xử lý subtitle với style
            self._add_subtitle_only(video_path, subtitle_path, output_path, subtitle_style)
                
        except Exception as e:
            raise Exception(f"Không thể ghép phụ đề vào video: {str(e)}")
    
    def _find_ffmpeg(self):
        """
        Tìm đường dẫn FFmpeg
        """
        # Thử tìm FFmpeg trong PATH
        ffmpeg_path = shutil.which('ffmpeg')
        if ffmpeg_path:
            return ffmpeg_path
        
        # Thử các đường dẫn phổ biến trên Windows
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
        raise FileNotFoundError(
            "FFmpeg không được tìm thấy. Vui lòng cài đặt FFmpeg và thêm vào PATH"
        )
    
    def extract_audio(self, video_path, audio_output_path):
        """
        Trích xuất audio từ video
        
        Args:
            video_path (str): Đường dẫn đến file video
            audio_output_path (str): Đường dẫn lưu file audio
        """
        try:
            # Kiểm tra xem video có audio stream không
            check_cmd = [
                self.ffmpeg_path,
                '-i', video_path,
                '-hide_banner'
            ]
            
            print(f"🔍 Kiểm tra audio stream trong {video_path}...")
            check_result = subprocess.run(check_cmd, capture_output=True, text=True)
            
            # Kiểm tra xem có audio stream không
            if "Audio:" not in check_result.stderr:
                print("⚠️ Video không có audio stream, tạo file audio trống...")
                # Tạo audio trống với thời lượng video
                self._create_silent_audio(video_path, audio_output_path)
                return
            
            cmd = [
                self.ffmpeg_path,
                '-i', video_path,
                '-ab', '160k',
                '-ac', '2',
                '-ar', '44100',
                '-vn',
                '-y',
                audio_output_path
            ]
            
            print(f"🎵 Đang trích xuất audio từ {video_path}...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print("⚠️ Không thể trích xuất audio, tạo file audio trống...")
                self._create_silent_audio(video_path, audio_output_path)
            else:
                print(f"✅ Trích xuất audio thành công: {audio_output_path}")
            
        except Exception as e:
            print(f"⚠️ Lỗi khi trích xuất audio: {str(e)}, tạo file audio trống...")
            try:
                self._create_silent_audio(video_path, audio_output_path)
            except Exception as e2:
                raise Exception(f"Không thể tạo audio: {str(e2)}")
    
    def _create_silent_audio(self, video_path, audio_output_path):
        """
        Tạo file audio trống với thời lượng bằng video
        """
        try:
            # Lấy thời lượng video
            duration_cmd = [
                self.ffmpeg_path,
                '-i', video_path,
                '-f', 'null',
                '-'
            ]
            
            duration_result = subprocess.run(duration_cmd, capture_output=True, text=True)
            
            # Tạo audio trống
            silent_cmd = [
                self.ffmpeg_path,
                '-f', 'lavfi',
                '-i', 'anullsrc=channel_layout=stereo:sample_rate=44100',
                '-i', video_path,
                '-c:a', 'pcm_s16le',
                '-map', '0:a',
                '-shortest',
                '-y',
                audio_output_path
            ]
            
            result = subprocess.run(silent_cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                # Fallback: tạo audio trống 10 giây
                fallback_cmd = [
                    self.ffmpeg_path,
                    '-f', 'lavfi',
                    '-i', 'anullsrc=channel_layout=stereo:sample_rate=44100',
                    '-t', '10',
                    '-c:a', 'pcm_s16le',
                    '-y',
                    audio_output_path
                ]
                
                result = subprocess.run(fallback_cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    raise Exception(f"Không thể tạo audio trống: {result.stderr}")
            
            print(f"✅ Tạo file audio trống thành công: {audio_output_path}")
            
        except Exception as e:
            raise Exception(f"Không thể tạo audio trống: {str(e)}")

    
    def convert_aspect_ratio(self, input_path, output_path, target_width=1080, target_height=1920):
        """
        Chuyển đổi tỉ lệ khung hình video
        """
        try:
            # Lấy thông tin video gốc
            info = self.get_video_info(input_path)
            original_width = info['width']
            original_height = info['height']
            
            print(f"📏 Video gốc: {original_width}x{original_height}")
            print(f"📱 Target: {target_width}x{target_height}")
            
            # Tính toán scale để fit height và crop width nếu cần
            scale_factor = target_height / original_height
            new_width = int(original_width * scale_factor)
            
            if new_width >= target_width:
                # Crop từ giữa
                crop_x = int((new_width - target_width) / 2)
                vf_filter = f"scale={new_width}:{target_height},crop={target_width}:{target_height}:{crop_x}:0"
            else:
                # Pad các bên với blur background
                pad_x = int((target_width - new_width) / 2)
                vf_filter = f"scale={new_width}:{target_height},pad={target_width}:{target_height}:{pad_x}:0:color=black"
            
            cmd = [
                self.ffmpeg_path,
                '-i', input_path,
                '-vf', vf_filter,
                '-c:a', 'copy',
                '-y',
                output_path
            ]
            
            print(f"🔄 Đang chuyển đổi tỉ lệ khung hình...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"Lỗi chuyển đổi tỉ lệ: {result.stderr}")
            
            print(f"✅ Chuyển đổi tỉ lệ thành công: {output_path}")
            
        except Exception as e:
            raise Exception(f"Không thể chuyển đổi tỉ lệ khung hình: {str(e)}")
    
    def _parse_video_dimensions(self, ffmpeg_output):
        """
        Parse thông tin kích thước video từ output của FFmpeg
        """
        import re
        
        # Tìm pattern "1920x1080" trong output
        pattern = r'(\d+)x(\d+)'
        matches = re.findall(pattern, ffmpeg_output)
        
        if matches:
            # Lấy match cuối cùng (thường là thông tin video stream)
            width, height = matches[-1]
            return int(width), int(height)
        
        return None, None
    
    def get_video_info(self, video_path):
        """
        Lấy thông tin chi tiết về video
        """
        try:
            cmd = [
                self.ffmpeg_path,
                '-i', video_path,
                '-hide_banner'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            output = result.stderr  # FFmpeg ghi thông tin ra stderr
            
            # Parse thông tin
            info = {}
            
            # Tìm kích thước
            width, height = self._parse_video_dimensions(output)
            if width and height:
                info['width'] = width
                info['height'] = height
            
            # Tìm duration
            import re
            duration_match = re.search(r'Duration: (\d+):(\d+):(\d+)\.(\d+)', output)
            if duration_match:
                hours, minutes, seconds, milliseconds = duration_match.groups()
                total_seconds = int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(milliseconds) / 100
                info['duration'] = total_seconds
            
            return info
            
        except Exception as e:
            raise Exception(f"Không thể lấy thông tin video: {str(e)}")
    
    def _get_font_path(self):
        """
        Lấy đường dẫn đến thư mục fonts tùy chỉnh
        """
        import glob
        
        # Tìm font Plus Jakarta Sans
        font_files = glob.glob("fonts/*Jakarta*.ttf")
        if font_files:
            font_dir = os.path.dirname(font_files[0])
            return font_dir.replace('\\', '/')
        
        return None
        """
        Sử dụng filter để burn-in phụ đề và ghép ảnh cùng lúc vào video
        """
        try:
            # Chuyển đổi đường dẫn Windows cho phụ đề
            subtitle_path_escaped = subtitle_path.replace('\\', '/').replace(':', '\\:')
              # Định nghĩa ảnh và thời gian xuất hiện
            image_configs = [
                {
                    "image": "1.png",  # Ảnh 1
                    "start_time": 5,   # Bắt đầu ở giây thứ 5
                    "end_time": 6,     # Kết thúc ở giây thứ 7
                    "y_offset": 865   # Vị trí Y
                },
                {
                    "image": "2.png",  # Ảnh 2
                    "start_time": 6,   # Bắt đầu ở giây thứ 7
                    "end_time": 7,     # Kết thúc ở giây thứ 9
                    "y_offset": 900   # Vị trí Y (giống ảnh 3)
                },
                {
                    "image": "3.png",  # Ảnh 3 
                    "start_time": 7,   # Bắt đầu ở giây thứ 7
                    "end_time": 8,     # Kết thúc ở giây thứ 9
                    "y_offset": 900   # Vị trí Y
                }
            ]
            
            # Kiểm tra ảnh có tồn tại không
            existing_images = []
            for config in image_configs:
                img_path = os.path.join(img_folder, config["image"])
                if os.path.exists(img_path):
                    existing_images.append(config)
                else:
                    print(f"⚠️ Ảnh không tồn tại: {img_path}, bỏ qua...")
            
            # Tạo command FFmpeg
            inputs = ['-i', video_path]
            
            if existing_images:
                # Có ảnh để ghép
                for config in existing_images:
                    img_path = os.path.join(img_folder, config["image"])
                    img_path = img_path.replace('\\', '/')
                    inputs.extend(['-i', img_path])
                
                # Tạo filter complex: subtitles + overlay images
                filter_parts = []
                  # Bước 1: Thêm subtitles vào video với font tùy chỉnh
                font_path = self._get_font_path()
                if font_path:
                    subtitle_filter = f"[0:v]subtitles='{subtitle_path_escaped}':fontsdir='{font_path}':force_style='FontName=Plus Jakarta Sans,FontSize=8,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=1,Shadow=1,MarginV=100'[sub]"
                else:
                    # Fallback to Arial if custom font not found
                    subtitle_filter = f"[0:v]subtitles='{subtitle_path_escaped}':force_style='FontName=Arial,FontSize=8,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=1,Shadow=1,MarginV=50'[sub]"
                filter_parts.append(subtitle_filter)
                  # Bước 2: Thêm từng ảnh với scale 30%
                current_input = "sub"
                for i, config in enumerate(existing_images):
                    img_input = str(i + 1)  # Input index của ảnh
                      # Thêm filter scale để thu nhỏ ảnh xuống 10%
                    scale_filter = f"[{img_input}]scale=iw*0.1:ih*0.1[img{i}]"
                    filter_parts.append(scale_filter)
                    
                    # Tính toán vị trí overlay
                    x_pos = "(main_w-overlay_w)/2"  # Căn giữa
                    y_pos = str(config["y_offset"])
                    
                    # Overlay với ảnh đã scale
                    overlay_filter = f"[{current_input}][img{i}]overlay={x_pos}:{y_pos}:enable='between(t,{config['start_time']},{config['end_time']})'"
                    
                    if i < len(existing_images) - 1:
                        # Không phải ảnh cuối cùng
                        overlay_filter += f"[tmp{i}]"
                        current_input = f"tmp{i}"
                    
                    filter_parts.append(overlay_filter)
                
                filter_complex = ";".join(filter_parts)
                
                cmd = [
                    self.ffmpeg_path,
                    *inputs,
                    '-filter_complex', filter_complex,
                    '-c:a', 'copy',
                    '-y',
                    output_path
                ]
                
            else:
                # Không có ảnh, chỉ ghép subtitles
                cmd = [
                    self.ffmpeg_path,
                    '-i', video_path,
                    '-vf', f"subtitles='{subtitle_path_escaped}':force_style='FontName=Arial,FontSize=8,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=1,Shadow=1,MarginV=150'",
                    '-c:a', 'copy',
                    '-y',
                    output_path
                ]
            
            print(f"🎞️ Đang ghép phụ đề và ảnh vào video...")
            print(f"📂 Video: {video_path}")
            print(f"📂 Subtitle: {subtitle_path}")
            if existing_images:
                for config in existing_images:
                    print(f"🖼️ Ảnh: {config['image']} ({config['start_time']}s-{config['end_time']}s)")
            print(f"📂 Output: {output_path}")
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"Lỗi ghép phụ đề và ảnh: {result.stderr}")
            
            print(f"✅ Ghép phụ đề và ảnh thành công: {output_path}")
                
        except Exception as e:
            raise Exception(f"Không thể ghép phụ đề và ảnh với filter: {str(e)}")

    def convert_aspect_ratio(self, input_path, output_path, target_width=1080, target_height=1920):
        """
        Chuyển đổi video thành tỉ lệ 9:16 cho TikTok/Instagram Reels
        
        Args:
            input_path (str): Đường dẫn video đầu vào
            output_path (str): Đường dẫn video đầu ra
            target_width (int): Chiều rộng đích
            target_height (int): Chiều cao đích
        """
        try:
            # Lấy thông tin video gốc
            info_cmd = [
                self.ffmpeg_path,
                '-i', input_path,
                '-hide_banner'
            ]
            
            result = subprocess.run(info_cmd, capture_output=True, text=True)
            
            # Parse thông tin video từ stderr của ffmpeg
            width, height = self._parse_video_dimensions(result.stderr)
            
            print(f"📱 Đang chuyển đổi video thành tỉ lệ 9:16 ({target_width}x{target_height})...")
            print(f"📊 Video gốc: {width}x{height} (tỉ lệ: {width/height:.2f})")
            print(f"📊 Video đích: {target_width}x{target_height} (tỉ lệ: {target_width/target_height:.2f})")
            
            # Nếu video đã có tỉ lệ 9:16, chỉ cần scale
            original_ratio = width / height
            target_ratio = target_width / target_height
            
            if abs(original_ratio - target_ratio) < 0.01:
                # Video đã có tỉ lệ đúng, chỉ cần scale
                cmd = [
                    self.ffmpeg_path,
                    '-i', input_path,
                    '-vf', f'scale={target_width}:{target_height}',
                    '-c:a', 'copy',
                    '-y',
                    output_path
                ]
            else:
                # Video chưa đúng tỉ lệ, cần pad hoặc crop
                if original_ratio > target_ratio:
                    # Video rộng hơn, cần crop chiều rộng
                    new_width = int(height * target_ratio)
                    x_offset = (width - new_width) // 2
                    vf = f'crop={new_width}:{height}:{x_offset}:0,scale={target_width}:{target_height}'
                else:
                    # Video cao hơn, cần pad chiều rộng với blur background
                    vf = f'scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2:black'
                
                cmd = [
                    self.ffmpeg_path,
                    '-i', input_path,
                    '-vf', vf,
                    '-c:a', 'copy',
                    '-y',
                    output_path
                ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"Lỗi chuyển đổi tỉ lệ: {result.stderr}")
            
            print(f"✅ Chuyển đổi tỉ lệ khung hình thành công: {output_path}")
            
        except Exception as e:
            raise Exception(f"Không thể chuyển đổi tỉ lệ khung hình: {str(e)}")
    
    def _parse_video_dimensions(self, ffmpeg_output):
        """
        Parse kích thước video từ output của ffmpeg
        """
        import re
        
        # Tìm pattern như "1920x1080" hoặc "1280x720"
        pattern = r'(\d+)x(\d+)'
        match = re.search(pattern, ffmpeg_output)
        
        if match:
            width = int(match.group(1))
            height = int(match.group(2))
            return width, height
        else:
            # Mặc định nếu không parse được
            return 1920, 1080
    
    def get_video_info(self, video_path):
        """
        Lấy thông tin chi tiết về video
        
        Args:
            video_path (str): Đường dẫn đến file video
            
        Returns:
            dict: Thông tin video
        """
        try:
            cmd = [
                self.ffmpeg_path,
                '-i', video_path,
                '-hide_banner'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Parse thông tin từ stderr
            info = {
                'path': video_path,
                'exists': os.path.exists(video_path),
                'size_mb': round(os.path.getsize(video_path) / (1024*1024), 2) if os.path.exists(video_path) else 0,
                'ffmpeg_output': result.stderr
            }
            
            return info
            
        except Exception as e:
            return {
                'path': video_path,
                'exists': False,
                'error': str(e)
            }
    
    def _get_font_path(self):
        """
        Tìm đường dẫn font Plus Jakarta Sans
        """
        font_dir = "fonts"
        possible_fonts = [
            "PlusJakartaSans-Regular.ttf",
            "Plus_Jakarta_Sans-Regular.ttf",
            "PlusJakartaSans.ttf"
        ]
        
        for font_file in possible_fonts:
            font_path = os.path.join(font_dir, font_file)
            if os.path.exists(font_path):
                # Chuyển đổi đường dẫn Windows cho FFmpeg
                return font_path.replace('\\', '/')
        
        return None
    
 
    def _add_subtitle_only(self, video_path, subtitle_path, output_path, subtitle_style=None):
        """
        Chỉ ghép phụ đề vào video (không có overlay)
        
        Args:
            video_path (str): Đường dẫn video
            subtitle_path (str): Đường dẫn phụ đề
            output_path (str): Đường dẫn kết quả
            subtitle_style (dict): Kiểu phụ đề
        """
        try:
            from subtitle_styles import get_subtitle_style_string, get_preset_style
            
            # Chuẩn bị subtitle path
            subtitle_path_escaped = subtitle_path.replace('\\', '/').replace(':', '\\:')
            
            # Xác định style - ĐÃ CẬP NHẬT MẶC ĐỊNH
            if subtitle_style is None:
                subtitle_style = {
                    "text_color": "black",
                    "box_style": "box",
                    "box_color": "white", 
                    "font_size": 10
                }
                
            # Sử dụng preset hoặc tạo style tùy chỉnh
            if "preset" in subtitle_style and subtitle_style["preset"]:
                style_string = get_preset_style(subtitle_style["preset"])
            else:
                style_string = get_subtitle_style_string(
                    text_color=subtitle_style.get("text_color", "black"),     # ĐÃ ĐỔI
                    box_style=subtitle_style.get("box_style", "box"),         # ĐÃ ĐỔI
                    box_color=subtitle_style.get("box_color", "white"),       # ĐÃ ĐỔI
                    font_name=subtitle_style.get("font_name", "Arial"),
                    font_size=subtitle_style.get("font_size", 10),            # ĐÃ ĐỔI
                    margin_v=subtitle_style.get("margin_v", 50),
                    opacity=subtitle_style.get("opacity", 255)
                )
            
            # Tạo filter subtitle
            font_path = self._get_font_path()
            if font_path:
                subtitle_filter = f"subtitles='{subtitle_path_escaped}':fontsdir='{font_path}':force_style='{style_string}'"
            else:
                subtitle_filter = f"subtitles='{subtitle_path_escaped}':force_style='{style_string}'"
            
            # Tạo command
            cmd = [
                self.ffmpeg_path,
                '-i', video_path,
                '-vf', subtitle_filter,
                '-c:a', 'copy',
                '-y',
                output_path
            ]
            
            print(f"🎞️ Đang ghép phụ đề...")
            print(f"📂 Video: {video_path}")
            print(f"📝 Subtitle: {subtitle_path}")
            print(f"🎨 Style: {style_string}")
            print(f"💾 Output: {output_path}")
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"Lỗi ghép phụ đề: {result.stderr}")
            
            print(f"✅ Ghép phụ đề thành công!")
            
        except Exception as e:
            raise Exception(f"Không thể ghép phụ đề: {str(e)}")

    def _add_subtitle_and_media_overlay(self, video_path, subtitle_path, output_path, img_folder, overlay_times, subtitle_style=None):
        """
        Ghép phụ đề, ảnh và video overlay (với chroma key) vào video chính
        
        Args:
            video_path (str): Đường dẫn video chính
            subtitle_path (str): Đường dẫn phụ đề
            output_path (str): Đường dẫn kết quả
            img_folder (str): Thư mục chứa ảnh/video overlay
            overlay_times (dict): Thời gian hiển thị overlay
            subtitle_style (dict): Kiểu phụ đề
        """
        try:
            from subtitle_styles import get_subtitle_style_string, get_preset_style
            
            # Chuẩn bị subtitle path
            subtitle_path_escaped = subtitle_path.replace('\\', '/').replace(':', '\\:')
            
            # Tìm tất cả file media trong thư mục
            import glob
            media_files = []
            
            # Tìm ảnh
            for ext in ['*.png', '*.jpg', '*.jpeg', '*.gif', '*.bmp']:
                media_files.extend(glob.glob(os.path.join(img_folder, ext)))
            
            # Tìm video
            for ext in ['*.mp4', '*.avi', '*.mov', '*.mkv', '*.wmv']:
                media_files.extend(glob.glob(os.path.join(img_folder, ext)))
            
            if not media_files:
                print("⚠️ Không tìm thấy file media nào, chỉ ghép phụ đề...")
                return self._add_subtitle_only(video_path, subtitle_path, output_path, subtitle_style)
            
            # Chuẩn bị danh sách overlay
            overlay_configs = []
            for media_file in media_files:
                filename = os.path.basename(media_file)
                
                # Lấy thông tin thời gian từ overlay_times
                if overlay_times and filename in overlay_times:
                    start_time = overlay_times[filename]['start']
                    duration = overlay_times[filename]['duration']
                    
                    # Xác định loại file
                    is_video = any(media_file.lower().endswith(ext) for ext in ['.mp4', '.avi', '.mov', '.mkv', '.wmv'])
                    
                    overlay_configs.append({
                        'file': media_file,
                        'filename': filename,
                        'start_time': start_time,
                        'duration': duration,
                        'is_video': is_video
                    })
            
            if not overlay_configs:
                print("⚠️ Không có file nào trong overlay_times, chỉ ghép phụ đề...")
                return self._add_subtitle_only(video_path, subtitle_path, output_path, subtitle_style)
            
            # Tạo command FFmpeg
            inputs = ['-i', video_path]
            
            # Thêm tất cả file overlay vào inputs
            for config in overlay_configs:
                inputs.extend(['-i', config['file']])
            
            # Tạo filter complex
            filter_parts = []
            
            # Xác định style subtitle - ĐÃ CẬP NHẬT MẶC ĐỊNH
            if subtitle_style is None:
                subtitle_style = {
                    "text_color": "black",
                    "box_style": "box", 
                    "box_color": "white",
                    "font_size": 10
                }
                
            # Sử dụng preset hoặc tạo style tùy chỉnh
            if "preset" in subtitle_style and subtitle_style["preset"]:
                style_string = get_preset_style(subtitle_style["preset"])
            else:
                style_string = get_subtitle_style_string(
                    text_color=subtitle_style.get("text_color", "black"),     # ĐÃ ĐỔI: từ "white" thành "black"
                    box_style=subtitle_style.get("box_style", "box"),         # ĐÃ ĐỔI: từ "outline" thành "box"
                    box_color=subtitle_style.get("box_color", "white"),       # ĐÃ ĐỔI: từ "black" thành "white"
                    font_name=subtitle_style.get("font_name", "Arial"),
                    font_size=subtitle_style.get("font_size", 10),            # ĐÃ ĐỔI: từ 24 thành 10
                    margin_v=subtitle_style.get("margin_v", 50),
                    opacity=subtitle_style.get("opacity", 255)
                )
            
            # Bước 1: Thêm subtitles
            font_path = self._get_font_path()
            if font_path:
                subtitle_filter = f"[0:v]subtitles='{subtitle_path_escaped}':fontsdir='{font_path}':force_style='{style_string}'[sub]"
            else:
                subtitle_filter = f"[0:v]subtitles='{subtitle_path_escaped}':force_style='{style_string}'[sub]"
            filter_parts.append(subtitle_filter)
            
            # Bước 2: Xử lý từng overlay
            current_input = "sub"
            for i, config in enumerate(overlay_configs):
                input_index = i + 1  # Input index của overlay
                
                if config['is_video']:
                    # Xử lý video overlay với chroma key
                    # Scale video overlay xuống 30% chiều cao
                    scale_filter = f"[{input_index}:v]scale=-1:ih*0.3[scaled{i}]"
                    filter_parts.append(scale_filter)
                    
                    # Áp dụng chroma key để xóa phông xanh
                    chromakey_filter = f"[scaled{i}]chromakey=0x00ff00:0.1:0.1[chroma{i}]"
                    filter_parts.append(chromakey_filter)
                    
                    # Overlay video
                    end_time = config['start_time'] + config['duration']
                    overlay_filter = f"[{current_input}][chroma{i}]overlay=(main_w-overlay_w)/2:(main_h-overlay_h)/2:enable='between(t,{config['start_time']},{end_time})'"
                    
                else:
                    # Xử lý ảnh overlay
                    # Scale ảnh xuống 10%
                    scale_filter = f"[{input_index}]scale=iw*0.1:ih*0.1[img{i}]"
                    filter_parts.append(scale_filter)
                    
                    # Overlay ảnh
                    end_time = config['start_time'] + config['duration']
                    overlay_filter = f"[{current_input}][img{i}]overlay=(main_w-overlay_w)/2:(main_h-overlay_h)/2:enable='between(t,{config['start_time']},{end_time})'"
                
                if i < len(overlay_configs) - 1:
                    overlay_filter += f"[tmp{i}]"
                    current_input = f"tmp{i}"
                
                filter_parts.append(overlay_filter)
            
            filter_complex = ";".join(filter_parts)
            
            cmd = [
                self.ffmpeg_path,
                *inputs,
                '-filter_complex', filter_complex,
                '-c:a', 'copy',
                '-y',
                output_path
            ]
            
            print(f"🎞️ Đang ghép phụ đề và media overlay...")
            print(f"📂 Video: {video_path}")
            print(f"📂 Subtitle: {subtitle_path}")
            print(f"🎨 Style: {style_string}")
            for config in overlay_configs:
                media_type = "Video" if config['is_video'] else "Ảnh"
                print(f"🎭 {media_type}: {config['filename']} ({config['start_time']}s, {config['duration']}s)")
            print(f"📂 Output: {output_path}")
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ FFmpeg error: {result.stderr}")
                raise Exception(f"Lỗi ghép media overlay: {result.stderr}")
            
            print(f"✅ Ghép phụ đề và media overlay thành công!")
            
        except Exception as e:
            print(f"❌ Lỗi trong _add_subtitle_and_media_overlay: {str(e)}")
            raise Exception(f"Không thể ghép phụ đề và media overlay: {str(e)}")

    # ===== HÀM BỔ SUNG: SỬA CÁC HARDCODE STYLES KHÁC =====

    def add_subtitle_to_video_with_images_filter(self, video_path, subtitle_path, output_path, img_folder):
        """
        Sử dụng filter để burn-in phụ đề và ghép ảnh cùng lúc vào video - ĐÃ SỬA
        """
        try:
            from subtitle_styles import get_subtitle_style_string
            
            # Chuyển đổi đường dẫn Windows cho phụ đề
            subtitle_path_escaped = subtitle_path.replace('\\', '/').replace(':', '\\:')
            
            # Định nghĩa ảnh và thời gian xuất hiện
            image_configs = [
                {
                    "image": "1.png",  # Ảnh 1
                    "start_time": 5,   # Bắt đầu ở giây thứ 5
                    "end_time": 6,     # Kết thúc ở giây thứ 7
                    "y_offset": 865   # Vị trí Y
                },
                {
                    "image": "2.png",  # Ảnh 2
                    "start_time": 6,   # Bắt đầu ở giây thứ 7
                    "end_time": 7,     # Kết thúc ở giây thứ 9
                    "y_offset": 900   # Vị trí Y (giống ảnh 3)
                },
                {
                    "image": "3.png",  # Ảnh 3 
                    "start_time": 7,   # Bắt đầu ở giây thứ 7
                    "end_time": 8,     # Kết thúc ở giây thứ 9
                    "y_offset": 900   # Vị trí Y
                }
            ]
            
            # Kiểm tra ảnh có tồn tại không
            existing_images = []
            for config in image_configs:
                img_path = os.path.join(img_folder, config["image"])
                if os.path.exists(img_path):
                    existing_images.append(config)
                else:
                    print(f"⚠️ Ảnh không tồn tại: {img_path}, bỏ qua...")
            
            # Tạo command FFmpeg
            inputs = ['-i', video_path]
            
            if existing_images:
                # Có ảnh để ghép
                for config in existing_images:
                    img_path = os.path.join(img_folder, config["image"])
                    img_path = img_path.replace('\\', '/')
                    inputs.extend(['-i', img_path])
                
                # Tạo filter complex: subtitles + overlay images
                filter_parts = []
                
                # Bước 1: Thêm subtitles vào video với font tùy chỉnh - ĐÃ SỬA
                font_path = self._get_font_path()
                
                # SỬA: Sử dụng style system thay vì hardcode
                style_string = get_subtitle_style_string(
                    text_color="black",      # Màu mới
                    box_style="box",         # Box thay vì outline
                    box_color="white",       # Nền trắng
                    font_size=8,             # Font size nhỏ cho ảnh overlay
                    margin_v=100
                )
                
                if font_path:
                    subtitle_filter = f"[0:v]subtitles='{subtitle_path_escaped}':fontsdir='{font_path}':force_style='{style_string}'[sub]"
                else:
                    subtitle_filter = f"[0:v]subtitles='{subtitle_path_escaped}':force_style='{style_string}'[sub]"
                filter_parts.append(subtitle_filter)
                
                # Bước 2: Thêm từng ảnh với scale 10%
                current_input = "sub"
                for i, config in enumerate(existing_images):
                    img_input = str(i + 1)  # Input index của ảnh
                    
                    # Thêm filter scale để thu nhỏ ảnh xuống 10%
                    scale_filter = f"[{img_input}]scale=iw*0.1:ih*0.1[img{i}]"
                    filter_parts.append(scale_filter)
                    
                    # Tính toán vị trí overlay
                    x_pos = "(main_w-overlay_w)/2"  # Căn giữa
                    y_pos = str(config["y_offset"])
                    
                    # Overlay với ảnh đã scale
                    overlay_filter = f"[{current_input}][img{i}]overlay={x_pos}:{y_pos}:enable='between(t,{config['start_time']},{config['end_time']})'"
                    
                    if i < len(existing_images) - 1:
                        # Không phải ảnh cuối cùng
                        overlay_filter += f"[tmp{i}]"
                        current_input = f"tmp{i}"
                    
                    filter_parts.append(overlay_filter)
                
                filter_complex = ";".join(filter_parts)
                
                cmd = [
                    self.ffmpeg_path,
                    *inputs,
                    '-filter_complex', filter_complex,
                    '-c:a', 'copy',
                    '-y',
                    output_path
                ]
                
            else:
                # Không có ảnh, chỉ ghép subtitles - ĐÃ SỬA
                style_string = get_subtitle_style_string(
                    text_color="black",
                    box_style="box",
                    box_color="white", 
                    font_size=8,
                    margin_v=150
                )
                
                cmd = [
                    self.ffmpeg_path,
                    '-i', video_path,
                    '-vf', f"subtitles='{subtitle_path_escaped}':force_style='{style_string}'",
                    '-c:a', 'copy',
                    '-y',
                    output_path
                ]
            
            print(f"🎞️ Đang ghép phụ đề và ảnh vào video...")
            print(f"📂 Video: {video_path}")
            print(f"📂 Subtitle: {subtitle_path}")
            if existing_images:
                for config in existing_images:
                    print(f"🖼️ Ảnh: {config['image']} ({config['start_time']}s-{config['end_time']}s)")
            print(f"📂 Output: {output_path}")
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"Lỗi ghép phụ đề và ảnh: {result.stderr}")
            
            print(f"✅ Ghép phụ đề và ảnh thành công: {output_path}")
                
        except Exception as e:
            raise Exception(f"Không thể ghép phụ đề và ảnh với filter: {str(e)}")      