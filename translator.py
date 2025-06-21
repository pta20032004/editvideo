#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module dịch phụ đề từ ngôn ngữ gốc sang tiếng Anh
"""

import re
import time
from pathlib import Path

try:
    from googletrans import Translator as GoogleTranslator
    HAS_GOOGLETRANS = True
except ImportError:
    HAS_GOOGLETRANS = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

class Translator:
    def __init__(self):
        self.google_translator = None
        
        if HAS_GOOGLETRANS:
            try:
                self.google_translator = GoogleTranslator()
                print("🌐 Sử dụng Google Translate API")
            except Exception as e:
                print(f"⚠️ Không thể khởi tạo Google Translator: {e}")
                self.google_translator = None
        
        if not HAS_GOOGLETRANS:
            print("⚠️ Cần cài đặt googletrans để sử dụng tính năng dịch")
    
    def translate_subtitle(self, input_subtitle_path, output_subtitle_path, 
                          source_lang='vi', target_lang='en'):
        """
        Dịch file phụ đề từ ngôn ngữ gốc sang ngôn ngữ đích
        
        Args:
            input_subtitle_path (str): Đường dẫn file phụ đề gốc
            output_subtitle_path (str): Đường dẫn lưu file phụ đề đã dịch
            source_lang (str): Mã ngôn ngữ gốc
            target_lang (str): Mã ngôn ngữ đích
        """
        try:
            print(f"🌐 Đang dịch phụ đề từ {source_lang} sang {target_lang}...")
            
            # Đọc file phụ đề gốc
            with open(input_subtitle_path, 'r', encoding='utf-8') as f:
                srt_content = f.read()
            
            # Phân tích và dịch từng đoạn phụ đề
            translated_srt = self._translate_srt_content(
                srt_content, source_lang, target_lang
            )
            
            # Lưu file phụ đề đã dịch
            with open(output_subtitle_path, 'w', encoding='utf-8') as f:
                f.write(translated_srt)
            
            print(f"✅ Dịch phụ đề thành công: {output_subtitle_path}")
            
        except Exception as e:
            raise Exception(f"Lỗi dịch phụ đề: {str(e)}")
    
    def _translate_srt_content(self, srt_content, source_lang, target_lang):
        """
        Dịch nội dung file SRT
        
        Args:
            srt_content (str): Nội dung file SRT
            source_lang (str): Ngôn ngữ gốc
            target_lang (str): Ngôn ngữ đích
            
        Returns:
            str: Nội dung SRT đã dịch
        """
        # Regex để tách các thành phần của SRT
        srt_pattern = r'(\d+)\s*\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\s*\n(.*?)(?=\n\d+\s*\n|\n*$)'
        
        matches = re.findall(srt_pattern, srt_content, re.DOTALL)
        
        if not matches:
            raise Exception("Không thể phân tích file SRT")
        
        translated_entries = []
        
        for i, (index, start_time, end_time, text) in enumerate(matches):
            try:
                # Dịch văn bản
                translated_text = self._translate_text(
                    text.strip(), source_lang, target_lang
                )
                
                # Tạo entry SRT mới
                entry = f"{index}\n{start_time} --> {end_time}\n{translated_text}\n"
                translated_entries.append(entry)
                
                # Thêm delay nhỏ để tránh rate limit
                if i > 0 and i % 10 == 0:
                    time.sleep(1)
                
            except Exception as e:
                print(f"⚠️ Lỗi dịch đoạn {index}: {e}")
                # Giữ nguyên văn bản gốc nếu không dịch được
                entry = f"{index}\n{start_time} --> {end_time}\n{text.strip()}\n"
                translated_entries.append(entry)
        
        return '\n'.join(translated_entries)
    
    def _translate_text(self, text, source_lang, target_lang):
        """
        Dịch một đoạn văn bản
        
        Args:
            text (str): Văn bản cần dịch
            source_lang (str): Ngôn ngữ gốc
            target_lang (str): Ngôn ngữ đích
            
        Returns:
            str: Văn bản đã dịch
        """
        if not text.strip():
            return text
        
        # Thử dịch với Google Translate
        if self.google_translator:
            try:
                result = self.google_translator.translate(
                    text, 
                    src=source_lang, 
                    dest=target_lang
                )
                return result.text
            except Exception as e:
                print(f"⚠️ Lỗi Google Translate: {e}")
        
        # Fallback: Dịch bằng cách sử dụng API khác hoặc trả về gốc
        return self._fallback_translate(text, source_lang, target_lang)
    
    def _fallback_translate(self, text, source_lang, target_lang):
        """
        Phương pháp dịch dự phòng
        """
        # Có thể tích hợp thêm các API dịch khác ở đây
        # Ví dụ: DeepL, Microsoft Translator, v.v.
        
        # Hiện tại chỉ trả về văn bản gốc
        print(f"⚠️ Không thể dịch: '{text[:50]}...' - Giữ nguyên")
        return text
    
    def _detect_language(self, text):
        """
        Phát hiện ngôn ngữ của văn bản
        
        Args:
            text (str): Văn bản cần phát hiện ngôn ngữ
            
        Returns:
            str: Mã ngôn ngữ
        """
        if self.google_translator:
            try:
                detection = self.google_translator.detect(text)
                return detection.lang
            except Exception as e:
                print(f"⚠️ Không thể phát hiện ngôn ngữ: {e}")
        
        return 'auto'
    
    def test_connection(self):
        """
        Kiểm tra kết nối dịch thuật
        
        Returns:
            bool: True nếu có thể dịch được
        """
        try:
            test_text = "Hello"
            result = self._translate_text(test_text, 'en', 'vi')
            return result != test_text
        except Exception:
            return False
