#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module chuyển đổi tỉ lệ khung hình video thành 9:16
"""

import os
import subprocess
from pathlib import Path

class AspectRatioConverter:
    def __init__(self):
        self.ffmpeg_path = self._find_ffmpeg()
    
    def _find_ffmpeg(self):
        """Tìm đường dẫn FFmpeg trên hệ thống"""
        try:
            # Thử chạy ffmpeg để kiểm tra
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return 'ffmpeg'
        except FileNotFoundError:
            pass
        
        # Kiểm tra các đường dẫn phổ biến
        common_paths = [
            'C:\\ffmpeg\\bin\\ffmpeg.exe',
            'C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe',
            'ffmpeg.exe'
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        raise FileNotFoundError(
            "FFmpeg không được tìm thấy. Vui lòng cài đặt FFmpeg và thêm vào PATH"
        )
    
    def convert_to_9_16(self, input_video_path, output_video_path, 
                       target_width=1080, background_color='black'):
        """
        Chuyển đổi video thành tỉ lệ 9:16
        
        Args:
            input_video_path (str): Đường dẫn video đầu vào
            output_video_path (str): Đường dẫn lưu video đầu ra
            target_width (int): Chiều rộng đích (mặc định 1080)
            background_color (str): Màu nền ('black', 'white', etc.)
        """
        try:
            # Tính toán chiều cao cho tỉ lệ 9:16
            target_height = int(target_width * 16 / 9)
            
            print(f"📱 Đang chuyển đổi video thành tỉ lệ 9:16 ({target_width}x{target_height})...")
            
            # Lấy thông tin video gốc
            video_info = self._get_video_info(input_video_path)
            original_width = video_info['width']
            original_height = video_info['height']
            original_ratio = original_width / original_height
            target_ratio = target_width / target_height
            
            print(f"📊 Video gốc: {original_width}x{original_height} (tỉ lệ: {original_ratio:.2f})")
            print(f"📊 Video đích: {target_width}x{target_height} (tỉ lệ: {target_ratio:.2f})")
            
            # Xác định phương pháp chuyển đổi
            if abs(original_ratio - target_ratio) < 0.01:
                # Video đã có tỉ lệ gần đúng, chỉ cần resize
                self._simple_resize(input_video_path, output_video_path, 
                                  target_width, target_height)
            elif original_ratio > target_ratio:
                # Video rộng hơn mục tiêu, cần cắt hoặc thêm thanh đen
                self._convert_wide_video(input_video_path, output_video_path,
                                       target_width, target_height, background_color)
            else:
                # Video hẹp hơn mục tiêu, cần thêm thanh đen
                self._convert_narrow_video(input_video_path, output_video_path,
                                         target_width, target_height, background_color)
            
            print(f"✅ Chuyển đổi tỉ lệ khung hình thành công: {output_video_path}")
            
        except Exception as e:
            raise Exception(f"Lỗi chuyển đổi tỉ lệ khung hình: {str(e)}")
    
    def _simple_resize(self, input_path, output_path, width, height):
        """Resize đơn giản video"""
        cmd = [
            self.ffmpeg_path,
            '-i', input_path,
            '-vf', f'scale={width}:{height}',
            '-c:a', 'copy',
            '-y',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Lỗi resize video: {result.stderr}")
    
    def _convert_wide_video(self, input_path, output_path, target_width, target_height, bg_color):
        """
        Chuyển đổi video rộng thành 9:16
        Có thể cắt hoặc thêm thanh đen tùy chọn
        """
        # Phương pháp 1: Cắt video để vừa khung hình 9:16 (crop center)
        crop_filter = f"crop={target_width}:{target_height}:(iw-{target_width})/2:(ih-{target_height})/2"
        
        # Phương pháp 2: Scale video và thêm thanh đen
        scale_filter = f"scale={target_width}:-1"
        pad_filter = f"pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2:{bg_color}"
        
        # Sử dụng phương pháp scale + pad để giữ toàn bộ nội dung
        video_filter = f"{scale_filter},{pad_filter}"
        
        cmd = [
            self.ffmpeg_path,
            '-i', input_path,
            '-vf', video_filter,
            '-c:a', 'copy',
            '-y',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Lỗi chuyển đổi video rộng: {result.stderr}")
    
    def _convert_narrow_video(self, input_path, output_path, target_width, target_height, bg_color):
        """
        Chuyển đổi video hẹp thành 9:16
        Thêm thanh đen ở hai bên
        """
        # Scale video theo chiều cao và thêm thanh đen hai bên
        scale_filter = f"scale=-1:{target_height}"
        pad_filter = f"pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2:{bg_color}"
        
        video_filter = f"{scale_filter},{pad_filter}"
        
        cmd = [
            self.ffmpeg_path,
            '-i', input_path,
            '-vf', video_filter,
            '-c:a', 'copy',
            '-y',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Lỗi chuyển đổi video hẹp: {result.stderr}")
    
    def _get_video_info(self, video_path):
        """
        Lấy thông tin cơ bản của video
        
        Args:
            video_path (str): Đường dẫn video
            
        Returns:
            dict: Thông tin video
        """
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_streams',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"Lỗi lấy thông tin video: {result.stderr}")
            
            import json
            info = json.loads(result.stdout)
            
            # Tìm stream video
            video_stream = None
            for stream in info['streams']:
                if stream['codec_type'] == 'video':
                    video_stream = stream
                    break
            
            if not video_stream:
                raise Exception("Không tìm thấy stream video")
            
            return {
                'width': int(video_stream['width']),
                'height': int(video_stream['height']),
                'fps': eval(video_stream.get('r_frame_rate', '30/1')),
                'duration': float(video_stream.get('duration', 0))
            }
            
        except Exception as e:
            raise Exception(f"Không thể lấy thông tin video: {str(e)}")
    
    def create_custom_aspect_ratio(self, input_path, output_path, 
                                  aspect_width, aspect_height, 
                                  target_resolution_width=1080,
                                  background_color='black'):
        """
        Tạo video với tỉ lệ khung hình tùy chỉnh
        
        Args:
            input_path (str): Đường dẫn video đầu vào
            output_path (str): Đường dẫn video đầu ra
            aspect_width (int): Tỉ lệ chiều rộng
            aspect_height (int): Tỉ lệ chiều cao
            target_resolution_width (int): Độ phân giải chiều rộng mục tiêu
            background_color (str): Màu nền
        """
        target_resolution_height = int(target_resolution_width * aspect_height / aspect_width)
        
        print(f"🎯 Chuyển đổi thành tỉ lệ {aspect_width}:{aspect_height} "
              f"({target_resolution_width}x{target_resolution_height})")
        
        self.convert_to_9_16(
            input_path, 
            output_path,
            target_width=target_resolution_width,
            background_color=background_color
        )
