#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ứng dụng Chỉnh sửa Video Tự động với Phụ đề và Tỉ lệ 9:16
Tác giả: Video Editor Bot
Mô tả: Tự động tạo phụ đề, dịch sang tiếng Anh và chuyển đổi video sang tỉ lệ 9:16
"""

import os
import sys
import tempfile
import subprocess
from pathlib import Path
import argparse
from video_processor import VideoProcessor
from subtitle_generator import SubtitleGenerator
from translator import Translator
from aspect_ratio_converter import AspectRatioConverter

class AutoVideoEditor:
    def __init__(self):
        self.video_processor = VideoProcessor()
        self.subtitle_generator = SubtitleGenerator()
        self.translator = Translator()
        self.aspect_converter = AspectRatioConverter()
    def _get_chroma_color(self, color_name):
        """Chuyển đổi tên màu thành mã hex"""
        colors = {
            "green": "0x00ff00",
            "blue": "0x0000ff", 
            "cyan": "0x00ffff",
            "red": "0xff0000",
            "magenta": "0xff00ff",
            "yellow": "0xffff00",
            "black": "0x000000",
            "white": "0xffffff",
        }
        return colors.get(color_name.lower(), "0x00ff00")    
    
    def process_video(self, input_video_path, output_video_path, source_language='vi', target_language='en', 
                 img_folder=None, overlay_times=None, video_overlay_settings=None, 
                 custom_timeline=False, words_per_line=7, enable_subtitle=True, subtitle_style=None):
        """
        Xử lý video chính theo các bước - FIXED ORDER: Convert 9:16 TRƯỚC overlay
        
        Args:
            input_video_path (str): Đường dẫn video đầu vào
            output_video_path (str): Đường dẫn video đầu ra
            source_language (str): Ngôn ngữ gốc
            target_language (str): Ngôn ngữ đích cho phụ đề
            img_folder (str, optional): Thư mục chứa ảnh overlay
            overlay_times (dict, optional): Cấu hình thời gian cho overlay
            video_overlay_settings (dict, optional): Cấu hình video overlay
            custom_timeline (bool): Có sử dụng custom timeline (3 ảnh) hay không
            words_per_line (int): Số từ mỗi dòng phụ đề
            enable_subtitle (bool): Có tạo phụ đề hay không
            subtitle_style (dict, optional): Kiểu phụ đề 
                {
                    "text_color": "black",        # Màu chữ
                    "box_style": "box",           # Kiểu khung
                    "box_color": "white",         # Màu nền
                    "font_name": "Arial",         # Font chữ
                    "font_size": 24,              # Cỡ chữ
                    "preset": "default"           # Hoặc dùng preset có sẵn
                }
        """
        print("🎬 Bắt đầu xử lý video...")
        
        print("🎯 Cấu hình xử lý:")
        print(f"   📹 Input: {input_video_path}")
        print(f"   💾 Output: {output_video_path}")
        print(f"   🌐 Ngôn ngữ: {source_language} → {target_language}")
        print(f"   📝 Tạo phụ đề: {enable_subtitle}")
        
        if video_overlay_settings and video_overlay_settings.get('enabled', False):
            print(f"   🎬 Video overlay: Có")
        else:
            print(f"   🎬 Video overlay: Không")
        
        print(f"   📄 Words per line: {words_per_line}")
        
        if subtitle_style:
            if subtitle_style.get("preset"):
                print(f"   🎨 Kiểu phụ đề: {subtitle_style['preset']}")
            else:
                print(f"   🎨 Kiểu phụ đề: Tùy chỉnh")
        else:
            print(f"   🎨 Kiểu phụ đề: Mặc định (chữ đen nền trắng)")
        
        print("=" * 50)
        
        try:
            # Tạo thư mục tạm
            temp_dir = tempfile.mkdtemp()
            print(f"📁 Thư mục tạm: {temp_dir}")
            
            translated_subtitle_path = None
            
            # BƯỚC 1-3: XỬ LÝ PHỤ ĐỀ (nếu enable)
            if enable_subtitle:
                # Bước 1: Trích xuất audio từ video
                print("🎵 Bước 1: Trích xuất audio từ video...")
                audio_path = os.path.join(temp_dir, "extracted_audio.wav")
                self.video_processor.extract_audio(input_video_path, audio_path)
                
                # Bước 2: Tạo phụ đề từ audio
                print("📝 Bước 2: Tạo phụ đề từ audio...")
                original_subtitle_path = os.path.join(temp_dir, "original_subtitle.srt")
                self.subtitle_generator.generate_subtitle(
                    audio_path, 
                    original_subtitle_path, 
                    language=source_language,
                    words_per_line=words_per_line
                )
                
                # Bước 3: Dịch phụ đề sang ngôn ngữ đích
                print(f"🌐 Bước 3: Dịch phụ đề từ {source_language} sang {target_language}...")
                translated_subtitle_path = os.path.join(temp_dir, f"{target_language}_subtitle.srt")
                self.translator.translate_subtitle(
                    original_subtitle_path,
                    translated_subtitle_path,
                    source_lang=source_language,
                    target_lang=target_language
                )
            else:
                print("📝 Bỏ qua tạo phụ đề (enable_subtitle=False)")
            
            # ⭐ BƯỚC 4: CHUYỂN ĐỔI 9:16 TRƯỚC (KEY CHANGE!)
            print("📱 Bước 4: Chuyển đổi tỉ lệ khung hình thành 9:16 TRƯỚC...")
            video_9_16_path = os.path.join(temp_dir, "video_9_16.mp4")
            self.aspect_converter.convert_to_9_16(
                input_video_path,
                video_9_16_path
            )
            
            # BƯỚC 5: CHÈN VIDEO OVERLAY (trên video 9:16)
            current_video = video_9_16_path  # Sử dụng video 9:16 làm base
            
            # Kiểm tra video overlay có hợp lệ không
            should_add_overlay = False
            overlay_video_path = None
            
            if video_overlay_settings and video_overlay_settings.get('enabled', False):
                overlay_video_path = video_overlay_settings.get('video_path', '')
                
                if overlay_video_path and os.path.exists(overlay_video_path):
                    should_add_overlay = True
                    print(f"🎬 Video overlay hợp lệ: {overlay_video_path}")
                else:
                    print("⚠️ Không có video overlay path hoặc file không tồn tại, bỏ qua video overlay")
            
            # Xử lý video overlay nếu có
            if should_add_overlay:
                print("🎞️ Bước 5: Chèn video overlay (trên video 9:16)...")
                
                try:
                    video_with_overlay_path = os.path.join(temp_dir, "video_9_16_with_overlay.mp4")
                    
                    # Kiểm tra nếu có multiple overlays
                    if 'multiple_overlays' in video_overlay_settings:
                        # Xử lý multiple overlays
                        overlays = video_overlay_settings['multiple_overlays']
                        print(f"🎬 Xử lý {len(overlays)} video overlay...")
                        self._process_multiple_video_overlays(
                            current_video,  # Sử dụng video 9:16
                            video_with_overlay_path, 
                            overlays, 
                            temp_dir
                        )
                    else:
                        # Xử lý single overlay
                        from video_overlay import add_video_overlay_with_chroma
                        settings = video_overlay_settings
                        
                        # Lấy chroma parameters từ GUI settings
                        chroma_color = settings.get('chroma_color', 'black')
                        chroma_similarity = settings.get('chroma_similarity', 0.01)
                        chroma_blend = settings.get('chroma_blend', 0.005)
                        
                        # Convert color name to hex
                        if not str(chroma_color).startswith('0x'):
                            chroma_color = self._get_chroma_color(chroma_color)
                        
                        # Extract position and size parameters
                        position_mode = settings.get('position_mode', 'preset')
                        custom_x = settings.get('custom_x')
                        custom_y = settings.get('custom_y')
                        size_mode = settings.get('size_mode', 'percentage')
                        custom_width = settings.get('custom_width')
                        custom_height = settings.get('custom_height')
                        
                        print(f"🎨 Chroma key: {chroma_color} (similarity={chroma_similarity}, blend={chroma_blend})")
                        
                        # Gọi hàm overlay với video 9:16
                        add_video_overlay_with_chroma(
                            main_video_path=current_video,  # Video 9:16
                            overlay_video_path=overlay_video_path,
                            output_path=video_with_overlay_path,
                            start_time=settings.get('start_time', 2),
                            duration=settings.get('duration', 10),
                            position=settings.get('position', 'center'),
                            size_percent=settings.get('size_percent', 25),
                            chroma_key=settings.get('chroma_key', True),
                            chroma_color=chroma_color,
                            chroma_similarity=chroma_similarity,
                            chroma_blend=chroma_blend,
                            auto_hide=settings.get('auto_hide', True),
                            position_mode=position_mode,
                            custom_x=custom_x,
                            custom_y=custom_y,
                            size_mode=size_mode,
                            custom_width=custom_width,
                            custom_height=custom_height
                        )
                    
                    current_video = video_with_overlay_path  # Update current video
                    
                except Exception as e:
                    print(f"⚠️ Lỗi video overlay: {e}")
                    print("🔄 Fallback: Tiếp tục với video 9:16 không có overlay...")
                    # current_video vẫn là video_9_16_path
            
            # Xử lý custom timeline nếu được bật
            if custom_timeline and img_folder and os.path.exists(img_folder):
                print("🎞️ Bước 5.5: Áp dụng custom timeline (3 ảnh)...")
                try:
                    from video_overlay import add_images_with_custom_timeline
                    
                    video_with_timeline_path = os.path.join(temp_dir, "video_with_timeline.mp4")
                    
                    # Nếu có subtitle, sử dụng nó cho custom timeline
                    subtitle_for_timeline = translated_subtitle_path if translated_subtitle_path else None
                    
                    # Thêm 3 ảnh với timeline
                    success = add_images_with_custom_timeline(
                        current_video,
                        subtitle_for_timeline,
                        video_with_timeline_path,
                        img_folder
                    )
                    
                    if success:
                        current_video = video_with_timeline_path
                        print("✅ Áp dụng custom timeline thành công!")
                    else:
                        print("⚠️ Không thể áp dụng custom timeline, tiếp tục với video hiện tại")
                    
                except Exception as e:
                    print(f"⚠️ Lỗi custom timeline: {e}")
                    print("🔄 Fallback: Tiếp tục với video hiện tại...")
            
            # BƯỚC 6: THÊM PHỤ ĐỀ (trên video 9:16 + overlay)
            if enable_subtitle and translated_subtitle_path:
                print("📝 Bước 6: Thêm phụ đề (trên video 9:16 + overlay)...")
                self.video_processor.add_subtitle_to_video(
                    current_video,  # Video 9:16 (có thể có overlay)
                    translated_subtitle_path,
                    output_video_path,
                    subtitle_style=subtitle_style
                )
            else:
                # Không có phụ đề, copy video hiện tại ra output
                print("📝 Bước 6: Không có phụ đề, copy video ra output...")
                import shutil
                shutil.copy2(current_video, output_video_path)
            
            print(f"✅ Hoàn thành! Video đã được lưu tại: {output_video_path}")
            
            # Dọn dẹp thư mục tạm
            import shutil
            shutil.rmtree(temp_dir)
            print("🧹 Đã dọn dẹp thư mục tạm")
            
        except Exception as e:
            print(f"❌ Lỗi trong quá trình xử lý: {str(e)}")
            import traceback
            print(f"Chi tiết lỗi: {traceback.format_exc()}")
            raise
def _process_multiple_video_overlays(self, input_video_path, output_path, settings_list, temp_dir):
    """Xử lý nhiều video overlay với custom position và size - UPDATED for 9:16"""
    current_video = input_video_path  # Đây giờ là video 9:16
    
    for i, settings in enumerate(settings_list):
        temp_output = os.path.join(temp_dir, f"temp_overlay_{i}.mp4")
        
        print(f"🎬 Áp dụng video overlay {i+1}/{len(settings_list)} (trên video 9:16)...")
        
        from video_overlay import add_video_overlay_with_chroma
        
        # Xử lý chroma parameters từ GUI
        chroma_color = settings.get('chroma_color', 'green')
        chroma_similarity = settings.get('chroma_similarity', 0.2)
        chroma_blend = settings.get('chroma_blend', 0.15)
        
        print(f"Processing chroma: color={chroma_color}, similarity={chroma_similarity}, blend={chroma_blend}")
        
        # Convert color name to hex nếu cần
        if not str(chroma_color).startswith('0x'):
            chroma_color = self._get_chroma_color(chroma_color)
        
        # Đảm bảo similarity và blend là số
        try:
            if isinstance(chroma_similarity, str):
                chroma_similarity = float(chroma_similarity)
            if isinstance(chroma_blend, str):
                chroma_blend = float(chroma_blend)
        except (ValueError, TypeError):
            print(f"Invalid chroma values, using defaults")
            chroma_similarity = 0.2
            chroma_blend = 0.15
        
        # Extract position and size parameters cho multiple overlays
        position_mode = settings.get('position_mode', 'preset')
        custom_x = settings.get('custom_x')
        custom_y = settings.get('custom_y')
        size_mode = settings.get('size_mode', 'percentage')
        custom_width = settings.get('custom_width')
        custom_height = settings.get('custom_height')
        
        add_video_overlay_with_chroma(
            main_video_path=current_video,  # Video 9:16
            overlay_video_path=settings['video_path'],
            output_path=temp_output,
            start_time=settings.get('start_time', 0),
            duration=settings.get('duration'),
            position=settings.get('position', 'top-right'),
            size_percent=settings.get('size_percent', 25),
            chroma_key=settings.get('chroma_key', True),
            color=chroma_color,  # Sử dụng alias từ test_chroma_key.py
            similarity=chroma_similarity,  # Sử dụng alias từ test_chroma_key.py
            auto_hide=settings.get('auto_hide', True),
            # Pass custom parameters for multiple overlays
            position_mode=position_mode,
            custom_x=custom_x,
            custom_y=custom_y,
            size_mode=size_mode,
            custom_width=custom_width,
            custom_height=custom_height
        )
        
        current_video = temp_output
    
    # Copy kết quả cuối cùng
    import shutil
    shutil.copy2(current_video, output_path)
    return True

def _get_chroma_color(self, color_name):
    """Chuyển đổi tên màu thành mã hex"""
    colors = {
        "green": "0x00ff00",
        "blue": "0x0000ff", 
        "cyan": "0x00ffff",
        "red": "0xff0000",
        "magenta": "0xff00ff",
        "yellow": "0xffff00",
        "black": "0x000000",
        "white": "0xffffff",
    }
    return colors.get(color_name.lower(), "0x00ff00")

def _get_chroma_sensitivity(self, preset_name):
    """Chuyển đổi preset độ nhạy thành giá trị"""
    presets = {
        "loose": (0.3, 0.3),
        "normal": (0.1, 0.1),
        "custom": (0.2, 0.2), #Green
        "strict": (0.05, 0.05),
        "very_strict": (0.01, 0.01), #Black
        "ultra_strict": (0.005, 0.005)
    }
    return presets.get(preset_name.lower(), (0.01, 0.01))


def main():
    parser = argparse.ArgumentParser(
        description="Ứng dụng Chỉnh sửa Video Tự động với Phụ đề và Tỉ lệ 9:16"
    )
    parser.add_argument(
        "input_video_path", 
        help="Đường dẫn đến file video đầu vào"
    )
    parser.add_argument(
        "output_video_path", 
        help="Đường dẫn để lưu file video đầu ra"
    )
    parser.add_argument(
        "--source-lang", 
        default="vi", 
        help="Ngôn ngữ gốc của video (mặc định: vi - tiếng Việt)"
    )
    parser.add_argument(
        "--target-lang", 
        default="en", 
        help="Ngôn ngữ đích cho phụ đề (mặc định: en - English)"
    )
    
    args = parser.parse_args()
    
    # Kiểm tra file đầu vào có tồn tại
    if not os.path.exists(args.input_video_path):
        print(f"❌ File video đầu vào không tồn tại: {args.input_video_path}")
        sys.exit(1)
    
    # Tạo thư mục đầu ra nếu chưa tồn tại
    output_dir = os.path.dirname(args.output_video_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Khởi tạo và chạy ứng dụng
    editor = AutoVideoEditor()
    editor.process_video(
        input_video_path=args.input_video_path, 
        output_video_path=args.output_video_path, 
        source_language=args.source_lang,
        target_language=args.target_lang
    )

if __name__ == "__main__":
    main()
