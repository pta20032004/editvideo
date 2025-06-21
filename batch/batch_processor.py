#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch Processing Module - Xử lý hàng loạt video
"""

import os
import threading
import queue
import time
from datetime import datetime
import json
from main import AutoVideoEditor

class BatchProcessor:
    """Xử lý hàng loạt video với multi-threading"""
    
    def __init__(self, max_workers=3):
        self.max_workers = max_workers
        self.video_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.workers = []
        self.is_processing = False
        self.stats = {
            'total': 0,
            'completed': 0,
            'failed': 0,
            'start_time': None,
            'end_time': None
        }
        
    def add_video_task(self, input_path, output_path, config=None):
        """Thêm video vào hàng đợi xử lý"""
        task = {
            'input_path': input_path,
            'output_path': output_path,
            'config': config or {},
            'added_time': datetime.now()
        }
        self.video_queue.put(task)
        self.stats['total'] += 1
        
    def add_folder_videos(self, input_folder, output_folder, config=None, 
                         video_extensions=['.mp4', '.avi', '.mov', '.mkv']):
        """Thêm tất cả video trong thư mục vào hàng đợi"""
        if not os.path.exists(input_folder):
            raise Exception(f"Thư mục input không tồn tại: {input_folder}")
        
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        video_files = []
        for filename in os.listdir(input_folder):
            name, ext = os.path.splitext(filename.lower())
            if ext in video_extensions:
                input_path = os.path.join(input_folder, filename)
                output_path = os.path.join(output_folder, f"{name}_processed{ext}")
                video_files.append((input_path, output_path))
                
        print(f"🎬 Tìm thấy {len(video_files)} video trong thư mục")
        
        for input_path, output_path in video_files:
            self.add_video_task(input_path, output_path, config)
            
        return len(video_files)
        
    def worker_thread(self, worker_id):
        """Worker thread xử lý video"""
        editor = AutoVideoEditor()
        
        while self.is_processing:
            try:
                # Lấy task từ queue với timeout
                task = self.video_queue.get(timeout=1)
                
                start_time = time.time()
                print(f"🔄 Worker {worker_id}: Bắt đầu xử lý {os.path.basename(task['input_path'])}")
                
                try:
                    # Xử lý video
                    editor.process_video(
                        input_video_path=task['input_path'],
                        output_video_path=task['output_path'],
                        source_language=task['config'].get('source_language', 'vi'),
                        target_language=task['config'].get('target_language', 'en'),
                        img_folder=task['config'].get('img_folder'),
                        overlay_times=task['config'].get('overlay_times'),
                        video_overlay_settings=task['config'].get('video_overlay_settings'),
                        custom_timeline=task['config'].get('custom_timeline', False)
                    )
                    
                    end_time = time.time()
                    duration = end_time - start_time
                    
                    result = {
                        'status': 'success',
                        'input_path': task['input_path'],
                        'output_path': task['output_path'],
                        'duration': duration,
                        'worker_id': worker_id,
                        'completed_time': datetime.now()
                    }
                    
                    self.stats['completed'] += 1
                    print(f"✅ Worker {worker_id}: Hoàn thành {os.path.basename(task['input_path'])} ({duration:.1f}s)")
                    
                except Exception as e:
                    result = {
                        'status': 'failed',
                        'input_path': task['input_path'],
                        'error': str(e),
                        'worker_id': worker_id,
                        'completed_time': datetime.now()
                    }
                    
                    self.stats['failed'] += 1
                    print(f"❌ Worker {worker_id}: Lỗi xử lý {os.path.basename(task['input_path'])}: {str(e)}")
                
                self.result_queue.put(result)
                self.video_queue.task_done()
                
            except queue.Empty:
                # Không có task nào, tiếp tục loop
                continue
            except Exception as e:
                print(f"❌ Worker {worker_id} gặp lỗi: {str(e)}")
                
    def start_processing(self, progress_callback=None):
        """Bắt đầu xử lý hàng loạt"""
        if self.is_processing:
            raise Exception("Batch processing đang chạy!")
        
        if self.video_queue.empty():
            raise Exception("Không có video nào để xử lý!")
        
        self.is_processing = True
        self.stats['start_time'] = datetime.now()
        self.stats['completed'] = 0
        self.stats['failed'] = 0
        
        print(f"🚀 Bắt đầu batch processing với {self.max_workers} workers")
        print(f"📊 Tổng số video: {self.stats['total']}")
        
        # Tạo worker threads
        for i in range(self.max_workers):
            worker = threading.Thread(target=self.worker_thread, args=(i+1,))
            worker.daemon = True
            worker.start()
            self.workers.append(worker)
        
        # Thread theo dõi tiến độ
        if progress_callback:
            progress_thread = threading.Thread(target=self._progress_monitor, args=(progress_callback,))
            progress_thread.daemon = True
            progress_thread.start()
            
    def stop_processing(self):
        """Dừng xử lý hàng loạt"""
        self.is_processing = False
        self.stats['end_time'] = datetime.now()
        
        # Đợi workers hoàn thành
        for worker in self.workers:
            worker.join(timeout=5)
        
        self.workers.clear()
        print("🛑 Đã dừng batch processing")
        
    def wait_completion(self):
        """Đợi hoàn thành tất cả video"""
        self.video_queue.join()
        self.stop_processing()
        
    def _progress_monitor(self, callback):
        """Monitor tiến độ và gọi callback"""
        while self.is_processing:
            progress = {
                'total': self.stats['total'],
                'completed': self.stats['completed'],
                'failed': self.stats['failed'],
                'remaining': self.stats['total'] - self.stats['completed'] - self.stats['failed'],
                'percentage': (self.stats['completed'] + self.stats['failed']) / self.stats['total'] * 100 if self.stats['total'] > 0 else 0
            }
            
            callback(progress)
            
            if progress['remaining'] <= 0:
                break
                
            time.sleep(1)
            
    def get_results(self):
        """Lấy tất cả kết quả"""
        results = []
        while not self.result_queue.empty():
            results.append(self.result_queue.get())
        return results
        
    def get_statistics(self):
        """Lấy thống kê"""
        stats = self.stats.copy()
        
        if stats['start_time'] and stats['end_time']:
            duration = stats['end_time'] - stats['start_time']
            stats['total_duration'] = duration.total_seconds()
            stats['avg_time_per_video'] = stats['total_duration'] / stats['total'] if stats['total'] > 0 else 0
        
        return stats
        
    def export_report(self, output_path):
        """Xuất báo cáo ra file JSON"""
        report = {
            'statistics': self.get_statistics(),
            'results': self.get_results(),
            'export_time': datetime.now().isoformat()
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"📄 Đã xuất báo cáo: {output_path}")

# Utility functions
def create_batch_config(source_lang='vi', target_lang='en', img_folder=None, 
                       custom_timeline=False, video_overlay_settings=None):
    """Tạo cấu hình cho batch processing"""
    return {
        'source_language': source_lang,
        'target_language': target_lang,
        'img_folder': img_folder,
        'custom_timeline': custom_timeline,
        'video_overlay_settings': video_overlay_settings
    }

def quick_batch_process(input_folder, output_folder, config=None, max_workers=3):
    """Xử lý nhanh tất cả video trong thư mục"""
    processor = BatchProcessor(max_workers=max_workers)
    
    try:
        # Thêm tất cả video
        count = processor.add_folder_videos(input_folder, output_folder, config)
        
        if count == 0:
            print("❌ Không tìm thấy video nào để xử lý!")
            return
        
        # Bắt đầu xử lý
        processor.start_processing()
        
        # Đợi hoàn thành
        processor.wait_completion()
        
        # In kết quả
        stats = processor.get_statistics()
        print("\n📊 KẾT QUẢ BATCH PROCESSING:")
        print(f"   ✅ Thành công: {stats['completed']}")
        print(f"   ❌ Thất bại: {stats['failed']}")
        print(f"   📈 Tổng cộng: {stats['total']}")
        
        if 'total_duration' in stats:
            print(f"   ⏱️ Thời gian: {stats['total_duration']:.1f}s")
            print(f"   📊 Trung bình: {stats['avg_time_per_video']:.1f}s/video")
        
        return processor
        
    except Exception as e:
        print(f"❌ Lỗi batch processing: {str(e)}")
        processor.stop_processing()
        return None

if __name__ == "__main__":
    # Test batch processing
    print("🧪 Test Batch Processing Module")
    
    # Tạo config mẫu
    config = create_batch_config(
        source_lang='vi',
        target_lang='en',
        custom_timeline=True
    )
    
    print("✅ Batch processing module sẵn sàng!")
