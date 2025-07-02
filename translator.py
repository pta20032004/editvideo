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
        Dịch file phụ đề - ĐÃ SỬA ĐỂ XỬ LÝ TIẾNG TRUNG TỐT HƠN
        """
        try:
            print(f"🌐 Đang dịch phụ đề từ {source_lang} sang {target_lang}...")
            
            # ✅ THÊM: Test connection trước khi dịch
            if not self.test_connection():
                print("⚠️ Google Translate connection failed, keeping original subtitles")
                # Copy original file as fallback
                import shutil
                shutil.copy2(input_subtitle_path, output_subtitle_path)
                return
            
            # Đọc file phụ đề gốc
            with open(input_subtitle_path, 'r', encoding='utf-8') as f:
                srt_content = f.read()
            
            # ✅ THÊM: Log sample content để debug
            lines = srt_content.split('\n')
            sample_lines = [line for line in lines[:20] if line.strip() and not line.strip().isdigit() and '-->' not in line]
            if sample_lines:
                print(f"📋 Sample subtitle content: '{sample_lines[0][:50]}...'")
            
            # Phân tích và dịch từng đoạn phụ đề
            translated_srt = self._translate_srt_content(
                srt_content, source_lang, target_lang
            )
            
            # Lưu file phụ đề đã dịch
            with open(output_subtitle_path, 'w', encoding='utf-8') as f:
                f.write(translated_srt)
            
            print(f"✅ Dịch phụ đề thành công: {output_subtitle_path}")
            
        except Exception as e:
            print(f"❌ Lỗi dịch phụ đề: {str(e)}")
            # Fallback: Copy original file
            try:
                import shutil
                shutil.copy2(input_subtitle_path, output_subtitle_path)
                print(f"📋 Fallback: Copied original subtitle to output")
            except Exception as e2:
                raise Exception(f"Translation failed and fallback failed: {str(e2)}")
    
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
        Dịch một đoạn văn bản - ĐÃ SỬA ĐỂ HỖ TRỢ TIẾNG TRUNG
        """
        if not text.strip():
            return text
        
        # ✅ SỬA: Map ngôn ngữ cho Google Translate
        language_mapping = {
            'zh': 'zh-cn',      # Tiếng Trung generic → Giản thể
            'zh-cn': 'zh-cn',   # Giản thể → Giản thể  
            'zh-tw': 'zh-tw',   # Phồn thể → Phồn thể
            'vi': 'vi',         # Tiếng Việt
            'en': 'en',         # Tiếng Anh
            'ja': 'ja',         # Tiếng Nhật
            'ko': 'ko',         # Tiếng Hàn
            'es': 'es',         # Tiếng Tây Ban Nha
            'fr': 'fr',         # Tiếng Pháp
            'de': 'de'          # Tiếng Đức
        }
        
        # Convert language codes
        google_source_lang = language_mapping.get(source_lang, source_lang)
        google_target_lang = language_mapping.get(target_lang, target_lang)
        
        print(f"🌐 Language mapping: {source_lang} → {google_source_lang}, {target_lang} → {google_target_lang}")
        
        # Thử dịch với Google Translate
        if self.google_translator:
            try:
                result = self.google_translator.translate(
                    text, 
                    src=google_source_lang,  # ✅ SỬA: Sử dụng mapped language
                    dest=google_target_lang  # ✅ SỬA: Sử dụng mapped language
                )
                
                if result and hasattr(result, 'text') and result.text:
                    print(f"✅ Translated: '{text[:30]}...' → '{result.text[:30]}...'")
                    return result.text
                else:
                    print(f"⚠️ Empty translation result for: '{text[:30]}...'")
                    return text
                    
            except Exception as e:
                print(f"⚠️ Google Translate error: {e}")
                
                # ✅ THÊM: Thử fallback với auto detection
                try:
                    print(f"🔄 Trying auto-detection fallback...")
                    result = self.google_translator.translate(
                        text,
                        src='auto',  # Auto detect source
                        dest=google_target_lang
                    )
                    
                    if result and hasattr(result, 'text') and result.text:
                        print(f"✅ Auto-translate success: '{text[:30]}...' → '{result.text[:30]}...'")
                        return result.text
                        
                except Exception as e2:
                    print(f"⚠️ Auto-detection also failed: {e2}")
        
        # Fallback: Trả về text gốc
        print(f"⚠️ Translation failed, keeping original: '{text[:50]}...'")
        return text
    
    def test_translation(self):
        """Test Google Translate với tiếng Trung"""
        test_cases = [
            ("你好世界", "zh", "vi"),
            ("你好世界", "zh-cn", "vi"), 
            ("你好世界", "zh-cn", "en"),
            ("Hello world", "en", "zh-cn")
        ]
        
        print("🧪 Testing translation with Chinese:")
        for text, src, dest in test_cases:
            try:
                result = self._translate_text(text, src, dest)
                print(f"  {src}→{dest}: '{text}' → '{result}'")
            except Exception as e:
                print(f"  {src}→{dest}: ERROR - {e}")

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
        Kiểm tra kết nối dịch thuật - ĐÃ SỬA ĐỂ TEST TIẾNG TRUNG
        """
        try:
            # Test với tiếng Anh đơn giản trước
            test_text = "Hello"
            result = self._translate_text(test_text, 'en', 'vi')
            
            if result != test_text and len(result) > 0:
                print("✅ Google Translate connection OK")
                
                # ✅ THÊM: Test thêm với tiếng Trung
                chinese_test = "你好"
                chinese_result = self._translate_text(chinese_test, 'zh-cn', 'en')
                if chinese_result != chinese_test:
                    print("✅ Chinese translation also OK")
                else:
                    print("⚠️ Chinese translation may have issues")
                
                return True
            else:
                print("⚠️ Google Translate not working properly")
                return False
                
        except Exception as e:
            print(f"❌ Translation test failed: {e}")
            return False