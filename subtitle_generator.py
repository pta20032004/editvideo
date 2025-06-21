#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module tạo phụ đề từ audio sử dụng Speech-to-Text
"""

import os
import tempfile
import subprocess
from pathlib import Path

try:
    import speech_recognition as sr
    import pydub
    from pydub import AudioSegment
    import wave
    HAS_SPEECH_RECOGNITION = True
except ImportError:
    HAS_SPEECH_RECOGNITION = False

try:
    import whisper
    HAS_WHISPER = True
except ImportError:
    HAS_WHISPER = False

class SubtitleGenerator:
    def __init__(self):
        self.recognizer = None
        self.whisper_model = None
        
        # Ưu tiên sử dụng Whisper nếu có
        if HAS_WHISPER:
            print("🤖 Sử dụng OpenAI Whisper để tạo phụ đề")
            try:
                self.whisper_model = whisper.load_model("base")
            except Exception as e:
                print(f"⚠️ Không thể tải Whisper model: {e}")
                self.whisper_model = None
        
        if HAS_SPEECH_RECOGNITION and not self.whisper_model:
            print("🎙️ Sử dụng SpeechRecognition để tạo phụ đề")
            self.recognizer = sr.Recognizer()
        
        if not HAS_WHISPER and not HAS_SPEECH_RECOGNITION:
            raise ImportError(
                "Cần cài đặt ít nhất một trong các thư viện: "
                "openai-whisper hoặc SpeechRecognition"
            )
    
    def generate_subtitle(self, audio_path, subtitle_output_path, language='vi', words_per_line=7):
        """
        Tạo phụ đề từ file audio
        
        Args:
            audio_path (str): Đường dẫn đến file audio
            subtitle_output_path (str): Đường dẫn lưu file phụ đề .srt
            language (str): Mã ngôn ngữ (vi, en, etc.)        """
        if self.whisper_model:            self._generate_with_whisper(audio_path, subtitle_output_path, language, words_per_line)
        elif self.recognizer:
            self._generate_with_speech_recognition(audio_path, subtitle_output_path, language, words_per_line)
        else:
            raise Exception("Không có engine nào để tạo phụ đề")
    
    def _generate_with_whisper(self, audio_path, subtitle_output_path, language, words_per_line=7):
        """Tạo phụ đề sử dụng OpenAI Whisper"""
        try:
            print("🤖 Đang tạo phụ đề với Whisper...")
            
            # Kiểm tra file audio có tồn tại và có nội dung không
            if not os.path.exists(audio_path):
                raise Exception(f"File audio không tồn tại: {audio_path}")
            
            # Kiểm tra kích thước file audio
            audio_size = os.path.getsize(audio_path)
            if audio_size < 1024:  # File quá nhỏ (< 1KB)
                print("⚠️ File audio trống hoặc quá nhỏ, tạo phụ đề mặc định...")
                self._create_default_subtitle(subtitle_output_path)
                return
            
            # Whisper xử lý trực tiếp file audio
            result = self.whisper_model.transcribe(
                audio_path, 
                language=language if language != 'vi' else 'vietnamese'
            )
            
            # Kiểm tra kết quả
            if not result.get('segments') or len(result['segments']) == 0:
                print("⚠️ Không phát hiện được giọng nói, tạo phụ đề mặc định...")
                self._create_default_subtitle(subtitle_output_path)
                return
            
            # Chuyển đổi kết quả thành format SRT
            srt_content = self._whisper_result_to_srt(result, words_per_line)
            
            # Lưu file SRT
            with open(subtitle_output_path, 'w', encoding='utf-8') as f:
                f.write(srt_content)
            
            print(f"✅ Tạo phụ đề thành công với {len(result['segments'])} đoạn")
            
        except Exception as e:
            print(f"⚠️ Lỗi tạo phụ đề với Whisper: {str(e)}, tạo phụ đề mặc định...")
            try:
                self._create_default_subtitle(subtitle_output_path)
            except Exception as e2:
                raise Exception(f"Không thể tạo phụ đề: {str(e2)}")
    
    def _create_default_subtitle(self, subtitle_output_path):
        """Tạo phụ đề mặc định cho video không có audio"""
        default_srt = """1
00:00:01,000 --> 00:00:05,000
[Video không có âm thanh]

2
00:00:06,000 --> 00:00:10,000
[No audio detected]
"""
        
        with open(subtitle_output_path, 'w', encoding='utf-8') as f:
            f.write(default_srt)
        
        print(f"✅ Tạo phụ đề mặc định: {subtitle_output_path}")
    
    def _whisper_result_to_srt(self, result, words_per_line=7):
        """Chuyển đổi kết quả Whisper thành format SRT với giới hạn từ mỗi dòng"""
        srt_content = ""
        subtitle_index = 1
        
        for segment in result['segments']:
            start_time = segment['start']
            end_time = segment['end']
            text = segment['text'].strip()
            
            # Chia text thành các dòng ngắn với số từ tùy chỉnh
            lines = self._split_text_into_lines(text, max_words_per_line=words_per_line)
            
            if not lines:
                continue
                
            # Tính thời gian cho mỗi dòng
            segment_duration = end_time - start_time
            time_per_line = segment_duration / len(lines)
            
            for i, line in enumerate(lines):
                line_start = start_time + (i * time_per_line)
                line_end = start_time + ((i + 1) * time_per_line)
                
                srt_start_time = self._seconds_to_srt_time(line_start)
                srt_end_time = self._seconds_to_srt_time(line_end)
                
                srt_content += f"{subtitle_index}\n"
                srt_content += f"{srt_start_time} --> {srt_end_time}\n"
                srt_content += f"{line}\n\n"
                
                subtitle_index += 1
        
        return srt_content
    
    def _generate_with_speech_recognition(self, audio_path, subtitle_output_path, language, words_per_line=7):
        """Tạo phụ đề sử dụng SpeechRecognition (phương pháp dự phòng)"""
        try:
            print("🎙️ Đang tạo phụ đề với SpeechRecognition...")
            
            # Chuyển đổi audio thành wav nếu cần
            audio = AudioSegment.from_file(audio_path)
            
            # Chia audio thành các đoạn nhỏ (30 giây mỗi đoạn)
            chunk_length_ms = 30000  # 30 seconds
            chunks = [audio[i:i + chunk_length_ms] 
                     for i in range(0, len(audio), chunk_length_ms)]
            
            srt_content = ""
            
            for i, chunk in enumerate(chunks):
                try:
                    # Lưu chunk tạm thời
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                        chunk.export(temp_file.name, format="wav")
                        
                        # Nhận dạng giọng nói
                        with sr.AudioFile(temp_file.name) as source:
                            audio_data = self.recognizer.record(source)
                            
                        # Chọn engine dựa trên ngôn ngữ
                        if language == 'vi':
                            text = self.recognizer.recognize_google(
                                audio_data, language='vi-VN'
                            )
                        else:
                            text = self.recognizer.recognize_google(
                                audio_data, language=language
                            )
                          # Tính toán thời gian
                        start_seconds = i * 30
                        end_seconds = min((i + 1) * 30, len(audio) / 1000)
                          # Chia text thành các dòng ngắn với số từ tùy chỉnh
                        lines = self._split_text_into_lines(text, max_words_per_line=words_per_line)
                        
                        if lines:
                            # Phân bổ thời gian cho từng dòng
                            segment_duration = end_seconds - start_seconds
                            time_per_line = segment_duration / len(lines)
                            
                            for j, line in enumerate(lines):
                                line_start = start_seconds + (j * time_per_line)
                                line_end = start_seconds + ((j + 1) * time_per_line)
                                
                                line_start_time = self._seconds_to_srt_time(line_start)
                                line_end_time = self._seconds_to_srt_time(line_end)
                                
                                # Thêm vào nội dung SRT với index liên tục
                                subtitle_count = len([x for x in srt_content.split('\n\n') if x.strip()]) + 1
                                srt_content += f"{subtitle_count}\n"
                                srt_content += f"{line_start_time} --> {line_end_time}\n"
                                srt_content += f"{line}\n\n"
                        
                        # Xóa file tạm
                        os.unlink(temp_file.name)
                        
                except sr.UnknownValueError:
                    # Bỏ qua đoạn không nhận dạng được
                    continue
                except Exception as e:
                    print(f"⚠️ Lỗi xử lý đoạn {i}: {e}")
                    continue
            
            # Lưu file SRT
            with open(subtitle_output_path, 'w', encoding='utf-8') as f:
                f.write(srt_content)
            
            print(f"✅ Tạo phụ đề thành công với {len(chunks)} đoạn")
            
        except Exception as e:
            raise Exception(f"Lỗi tạo phụ đề với SpeechRecognition: {str(e)}")
    
    def _seconds_to_srt_time(self, seconds):
        """Chuyển đổi giây thành định dạng thời gian SRT (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"
    
    def _split_text_into_lines(self, text, max_words_per_line=7):
        """Chia text thành các dòng ngắn với tối đa số từ cho trước"""
        import re
        
        # Làm sạch text
        text = text.strip()
        if not text:
            return []
        
        # Tách thành từng từ
        words = re.findall(r'\S+', text)
        
        if not words:
            return []
        
        lines = []
        current_line = []
        
        for word in words:
            current_line.append(word)
            
            # Nếu đạt giới hạn từ hoặc gặp dấu câu, tạo dòng mới
            if (len(current_line) >= max_words_per_line or 
                word.endswith(('.', '!', '?', ',', ';'))):
                
                lines.append(' '.join(current_line))
                current_line = []
        
        # Thêm dòng cuối nếu còn từ
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def _optimize_subtitle_timing(self, lines, total_duration):
        """Tối ưu thời gian hiển thị cho từng dòng phụ đề"""
        if not lines:
            return []
        
        # Tính toán thời gian dựa trên độ dài text
        line_weights = []
        total_chars = 0
        
        for line in lines:
            char_count = len(line)
            line_weights.append(char_count)
            total_chars += char_count
        
        # Phân bổ thời gian theo tỷ lệ
        timings = []
        current_time = 0
        
        for weight in line_weights:
            if total_chars > 0:
                duration = (weight / total_chars) * total_duration
                # Đảm bảo thời gian tối thiểu 1 giây, tối đa 4 giây
                duration = max(1.0, min(4.0, duration))
            else:
                duration = total_duration / len(lines)
            
            timings.append({
                'start': current_time,
                'end': current_time + duration,
                'duration': duration
            })
            
            current_time += duration
        
        return timings
