#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Batch Processing Module - Xử lý hàng loạt video nâng cao
Hỗ trợ xử lý 100+ video cùng lúc với tối ưu hiệu năng
"""

import os
import threading
import queue
import time
import psutil
import json
import hashlib
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Callable
from main import AutoVideoEditor

@dataclass
class VideoTask:
    """Class đại diện cho một task xử lý video"""
    input_path: str
    output_path: str
    config: Dict
    priority: int = 0  # 0 = cao nhất
    file_size: int = 0
    estimated_time: float = 0
    retry_count: int = 0
    max_retries: int = 3
    task_id: str = ""
    created_time: datetime = None
    
    def __post_init__(self):
        if not self.task_id:
            self.task_id = hashlib.md5(self.input_path.encode()).hexdigest()[:8]
        if not self.created_time:
            self.created_time = datetime.now()
        if self.file_size == 0 and os.path.exists(self.input_path):
            self.file_size = os.path.getsize(self.input_path)

class AdvancedBatchProcessor:
    """Xử lý hàng loạt video nâng cao với tối ưu hiệu năng"""
    
    def __init__(self, max_workers=None, memory_limit_gb=8, priority_mode=True):
        # Tự động tính số workers tối ưu
        if max_workers is None:
            cpu_count = psutil.cpu_count()
            # Sử dụng 70% CPU, tối thiểu 2, tối đa 16
            max_workers = max(2, min(16, int(cpu_count * 0.7)))
        
        self.max_workers = max_workers
        self.memory_limit_gb = memory_limit_gb
        self.priority_mode = priority_mode
        
        # Task management
        self.task_queue = queue.PriorityQueue() if priority_mode else queue.Queue()
        self.completed_tasks = []
        self.failed_tasks = []
        self.processing_tasks = {}
        
        # Threading
        self.executor = None
        self.is_processing = False
        self.lock = threading.Lock()
        
        # Statistics
        self.stats = {
            'total': 0,
            'completed': 0,
            'failed': 0,
            'processing': 0,
            'queued': 0,
            'start_time': None,
            'end_time': None,
            'total_file_size': 0,
            'processed_file_size': 0
        }
        
        # Checkpoint for resume
        self.checkpoint_file = "batch_checkpoint.json"
        
        print(f"🔧 Advanced Batch Processor khởi tạo:")
        print(f"   💻 CPU cores: {psutil.cpu_count()}")
        print(f"   🧵 Max workers: {self.max_workers}")
        print(f"   💾 Memory limit: {self.memory_limit_gb}GB")
        print(f"   📊 Priority mode: {self.priority_mode}")
        
    def add_video_task(self, input_path: str, output_path: str, config: Dict = None, priority: int = 0):
        """Thêm video task với priority"""
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Video không tồn tại: {input_path}")
        
        task = VideoTask(
            input_path=input_path,
            output_path=output_path,
            config=config or {},
            priority=priority
        )
        
        # Estimate processing time based on file size (rough estimate)
        task.estimated_time = task.file_size / (50 * 1024 * 1024)  # ~50MB/s
        
        if self.priority_mode:
            # Priority queue: (priority, file_size, task)
            # Smaller files first within same priority
            self.task_queue.put((priority, task.file_size, task))
        else:
            self.task_queue.put(task)
        
        self.stats['total'] += 1
        self.stats['queued'] += 1
        self.stats['total_file_size'] += task.file_size
        
        print(f"➕ Thêm task: {os.path.basename(task.input_path)} ({task.file_size/1024/1024:.1f}MB)")
        
        return task.task_id
    
    def add_folder_videos(self, input_folder: str, output_folder: str, config: Dict = None,
                         video_extensions: List[str] = None, priority_by_size: bool = True):
        """Thêm tất cả video trong folder với smart priority"""
        if video_extensions is None:
            video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']
        
        if not os.path.exists(input_folder):
            raise FileNotFoundError(f"Thư mục không tồn tại: {input_folder}")
        
        os.makedirs(output_folder, exist_ok=True)
        
        # Scan all videos and sort by size if needed
        video_files = []
        for filename in os.listdir(input_folder):
            name, ext = os.path.splitext(filename.lower())
            if ext in video_extensions:
                input_path = os.path.join(input_folder, filename)
                output_path = os.path.join(output_folder, f"{name}_processed{ext}")
                file_size = os.path.getsize(input_path)
                video_files.append((input_path, output_path, file_size))
        
        # Sort by size (smaller first) if priority_by_size
        if priority_by_size:
            video_files.sort(key=lambda x: x[2])
        
        print(f"📁 Tìm thấy {len(video_files)} video trong {input_folder}")
        print(f"📊 Tổng dung lượng: {sum(f[2] for f in video_files) / 1024 / 1024 / 1024:.2f}GB")
        
        task_ids = []
        for i, (input_path, output_path, file_size) in enumerate(video_files):
            # Priority: smaller files get higher priority (lower number)
            priority = i if priority_by_size else 0
            task_id = self.add_video_task(input_path, output_path, config, priority)
            task_ids.append(task_id)
        
        return task_ids
    
    def check_system_resources(self):
        """Kiểm tra tài nguyên hệ thống"""
        # Memory check
        memory = psutil.virtual_memory()
        memory_usage_gb = (memory.total - memory.available) / 1024**3
        
        # CPU check
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Disk space check
        disk = psutil.disk_usage('.')
        disk_free_gb = disk.free / 1024**3
        
        return {
            'memory_usage_gb': memory_usage_gb,
            'memory_available_gb': memory.available / 1024**3,
            'cpu_percent': cpu_percent,
            'disk_free_gb': disk_free_gb,
            'can_process': (
                memory_usage_gb < self.memory_limit_gb and
                cpu_percent < 90 and
                disk_free_gb > 1
            )
        }
    
    def process_single_video(self, task: VideoTask) -> Dict:
        """Xử lý một video"""
        task_start = time.time()
        
        with self.lock:
            self.processing_tasks[task.task_id] = task
            self.stats['processing'] += 1
            self.stats['queued'] -= 1
        
        print(f"🔄 [{task.task_id}] Bắt đầu xử lý {os.path.basename(task.input_path)}")
        
        try:
            # Check system resources before processing
            resources = self.check_system_resources()
            if not resources['can_process']:
                raise Exception(f"Tài nguyên hệ thống không đủ: RAM {resources['memory_usage_gb']:.1f}GB, CPU {resources['cpu_percent']:.1f}%")
            
            # Create editor instance
            editor = AutoVideoEditor()
            
            # Process video
            editor.process_video(
                input_video_path=task.input_path,
                output_video_path=task.output_path,
                source_language=task.config.get('source_language', 'vi'),
                target_language=task.config.get('target_language', 'en'),
                img_folder=task.config.get('img_folder'),
                overlay_times=task.config.get('overlay_times'),
                video_overlay_settings=task.config.get('video_overlay_settings'),
                custom_timeline=task.config.get('custom_timeline', False)
            )
            
            duration = time.time() - task_start
            
            # Verify output file
            if not os.path.exists(task.output_path):
                raise Exception("File output không được tạo")
            
            output_size = os.path.getsize(task.output_path)
            if output_size < 1024:  # Less than 1KB is suspicious
                raise Exception("File output quá nhỏ, có thể bị lỗi")
            
            result = {
                'status': 'success',
                'task_id': task.task_id,
                'input_path': task.input_path,
                'output_path': task.output_path,
                'duration': duration,
                'input_size': task.file_size,
                'output_size': output_size,
                'completed_time': datetime.now(),
                'thread_id': threading.current_thread().ident
            }
            
            with self.lock:
                self.completed_tasks.append(result)
                self.stats['completed'] += 1
                self.stats['processing'] -= 1
                self.stats['processed_file_size'] += task.file_size
                del self.processing_tasks[task.task_id]
            
            print(f"✅ [{task.task_id}] Hoàn thành {os.path.basename(task.input_path)} ({duration:.1f}s)")
            return result
            
        except Exception as e:
            error_msg = str(e)
            
            # Retry logic
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                print(f"🔄 [{task.task_id}] Retry {task.retry_count}/{task.max_retries}: {error_msg}")
                
                # Add back to queue with lower priority
                if self.priority_mode:
                    self.task_queue.put((task.priority + 10, task.file_size, task))
                else:
                    self.task_queue.put(task)
                
                with self.lock:
                    self.stats['queued'] += 1
                    self.stats['processing'] -= 1
                    del self.processing_tasks[task.task_id]
                
                return None  # Will be processed again
            
            # Final failure
            result = {
                'status': 'failed',
                'task_id': task.task_id,
                'input_path': task.input_path,
                'error': error_msg,
                'retry_count': task.retry_count,
                'duration': time.time() - task_start,
                'completed_time': datetime.now(),
                'thread_id': threading.current_thread().ident
            }
            
            with self.lock:
                self.failed_tasks.append(result)
                self.stats['failed'] += 1
                self.stats['processing'] -= 1
                del self.processing_tasks[task.task_id]
            
            print(f"❌ [{task.task_id}] Thất bại {os.path.basename(task.input_path)}: {error_msg}")
            return result
    
    def start_processing(self, progress_callback: Optional[Callable] = None):
        """Bắt đầu xử lý với ThreadPoolExecutor"""
        if self.is_processing:
            raise Exception("Batch processing đang chạy!")
        
        if self.task_queue.empty():
            raise Exception("Không có video nào để xử lý!")
        
        self.is_processing = True
        self.stats['start_time'] = datetime.now()
        
        print(f"🚀 Bắt đầu Advanced Batch Processing")
        print(f"   🧵 Workers: {self.max_workers}")
        print(f"   📊 Tổng video: {self.stats['total']}")
        print(f"   💾 Tổng dung lượng: {self.stats['total_file_size'] / 1024**3:.2f}GB")
        
        # Create ThreadPoolExecutor
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        
        # Submit initial batch of tasks
        futures = []
        
        # Start progress monitoring thread
        if progress_callback:
            progress_thread = threading.Thread(target=self._progress_monitor, args=(progress_callback,))
            progress_thread.daemon = True
            progress_thread.start()
        
        # Process tasks
        try:
            while self.is_processing and (not self.task_queue.empty() or self.stats['processing'] > 0):
                # Submit new tasks if we have capacity
                while len(futures) < self.max_workers and not self.task_queue.empty():
                    try:
                        if self.priority_mode:
                            _, _, task = self.task_queue.get_nowait()
                        else:
                            task = self.task_queue.get_nowait()
                        
                        future = self.executor.submit(self.process_single_video, task)
                        futures.append(future)
                        
                    except queue.Empty:
                        break
                
                # Check completed tasks
                completed_futures = []
                for future in futures:
                    if future.done():
                        completed_futures.append(future)
                        try:
                            result = future.result()
                            # Result is already handled in process_single_video
                        except Exception as e:
                            print(f"❌ Future exception: {str(e)}")
                
                # Remove completed futures
                for future in completed_futures:
                    futures.remove(future)
                
                # Short sleep to prevent busy waiting
                time.sleep(0.1)
                
                # Save checkpoint periodically
                if len(self.completed_tasks) % 10 == 0:
                    self.save_checkpoint()
            
        except KeyboardInterrupt:
            print("⚠️ Nhận tín hiệu dừng, đang dọn dẹp...")
            self.stop_processing()
        
        # Final cleanup
        self.executor.shutdown(wait=True)
        self.stats['end_time'] = datetime.now()
        self.is_processing = False
        
        print(f"🏁 Hoàn thành batch processing!")
        self.print_final_stats()
    
    def stop_processing(self):
        """Dừng xử lý"""
        print("🛑 Đang dừng batch processing...")
        self.is_processing = False
        
        if self.executor:
            self.executor.shutdown(wait=False)
        
        self.save_checkpoint()
    
    def _progress_monitor(self, callback: Callable):
        """Monitor tiến độ"""
        while self.is_processing:
            progress = self.get_progress()
            callback(progress)
            
            if progress['remaining'] <= 0:
                break
            
            time.sleep(2)  # Update every 2 seconds
    
    def get_progress(self) -> Dict:
        """Lấy thông tin tiến độ"""
        with self.lock:
            total = self.stats['total']
            completed = self.stats['completed']
            failed = self.stats['failed']
            processing = self.stats['processing']
            queued = self.stats['queued']
            
            processed_size = self.stats['processed_file_size']
            total_size = self.stats['total_file_size']
        
        remaining = total - completed - failed
        percentage = ((completed + failed) / total * 100) if total > 0 else 0
        size_percentage = (processed_size / total_size * 100) if total_size > 0 else 0
        
        # Estimate remaining time
        if self.stats['start_time'] and completed > 0:
            elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
            avg_time = elapsed / completed
            estimated_remaining = avg_time * remaining
        else:
            estimated_remaining = 0
        
        return {
            'total': total,
            'completed': completed,
            'failed': failed,
            'processing': processing,
            'queued': queued,
            'remaining': remaining,
            'percentage': percentage,
            'size_percentage': size_percentage,
            'estimated_remaining_seconds': estimated_remaining,
            'system_info': self.check_system_resources()
        }
    
    def save_checkpoint(self):
        """Lưu checkpoint để resume"""
        checkpoint = {
            'stats': self.stats,
            'completed_tasks': [asdict(task) if hasattr(task, '__dict__') else task for task in self.completed_tasks],
            'failed_tasks': [asdict(task) if hasattr(task, '__dict__') else task for task in self.failed_tasks],
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(checkpoint, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            print(f"⚠️ Không thể lưu checkpoint: {str(e)}")
    
    def load_checkpoint(self) -> bool:
        """Load checkpoint để resume"""
        if not os.path.exists(self.checkpoint_file):
            return False
        
        try:
            with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                checkpoint = json.load(f)
            
            self.stats.update(checkpoint['stats'])
            self.completed_tasks = checkpoint['completed_tasks']
            self.failed_tasks = checkpoint['failed_tasks']
            
            print(f"📄 Loaded checkpoint from {checkpoint['timestamp']}")
            return True
            
        except Exception as e:
            print(f"⚠️ Không thể load checkpoint: {str(e)}")
            return False
    
    def print_final_stats(self):
        """In thống kê cuối cùng"""
        stats = self.get_statistics()
        
        print("\n" + "="*60)
        print(f"📊 KẾT QUẢ BATCH PROCESSING")
        print("="*60)
        print(f"✅ Thành công: {stats['completed']}")
        print(f"❌ Thất bại: {stats['failed']}")
        print(f"📈 Tổng cộng: {stats['total']}")
        
        if 'total_duration' in stats:
            print(f"⏱️ Thời gian: {stats['total_duration']:.1f}s ({stats['total_duration']/60:.1f} phút)")
            print(f"📊 Trung bình: {stats['avg_time_per_video']:.1f}s/video")
        
        if stats.get('total_file_size', 0) > 0:
            print(f"💾 Dung lượng xử lý: {stats['total_file_size'] / 1024**3:.2f}GB")
            print(f"🚀 Tốc độ: {stats['total_file_size'] / 1024**2 / stats.get('total_duration', 1):.1f}MB/s")
        
        print("="*60)
    
    def get_statistics(self) -> Dict:
        """Lấy thống kê chi tiết"""
        stats = self.stats.copy()
        
        if stats['start_time'] and stats['end_time']:
            duration = stats['end_time'] - stats['start_time']
            stats['total_duration'] = duration.total_seconds()
            stats['avg_time_per_video'] = stats['total_duration'] / stats['total'] if stats['total'] > 0 else 0
        
        return stats
    
    def export_report(self, output_path: str):
        """Xuất báo cáo chi tiết"""
        report = {
            'summary': self.get_statistics(),
            'progress': self.get_progress(),
            'completed_tasks': self.completed_tasks,
            'failed_tasks': self.failed_tasks,
            'system_info': self.check_system_resources(),
            'export_time': datetime.now().isoformat(),
            'processor_config': {
                'max_workers': self.max_workers,
                'memory_limit_gb': self.memory_limit_gb,
                'priority_mode': self.priority_mode
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"📄 Báo cáo chi tiết: {output_path}")

# Convenience functions
def process_large_batch(input_folder: str, output_folder: str, config: Dict = None, 
                       max_workers: int = None, memory_limit_gb: int = 8) -> AdvancedBatchProcessor:
    """Xử lý batch lớn (100+ video) với cấu hình tối ưu"""
    
    print(f"🎬 ADVANCED BATCH PROCESSING - LARGE SCALE")
    print(f"📁 Input: {input_folder}")
    print(f"📁 Output: {output_folder}")
    
    # Create processor
    processor = AdvancedBatchProcessor(
        max_workers=max_workers,
        memory_limit_gb=memory_limit_gb,
        priority_mode=True
    )
    
    # Add all videos with smart priority
    task_ids = processor.add_folder_videos(
        input_folder=input_folder,
        output_folder=output_folder,
        config=config,
        priority_by_size=True
    )
    
    print(f"📋 Đã thêm {len(task_ids)} video vào queue")
    
    # Progress callback
    def progress_callback(progress):
        print(f"📈 Tiến độ: {progress['percentage']:.1f}% | "
              f"Hoàn thành: {progress['completed']} | "
              f"Đang xử lý: {progress['processing']} | "
              f"Thất bại: {progress['failed']} | "
              f"RAM: {progress['system_info']['memory_usage_gb']:.1f}GB")
    
    # Start processing
    try:
        processor.start_processing(progress_callback=progress_callback)
        
        # Export report
        report_file = f"batch_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        processor.export_report(report_file)
        
        return processor
        
    except Exception as e:
        print(f"❌ Lỗi batch processing: {str(e)}")
        processor.stop_processing()
        return processor

if __name__ == "__main__":
    # Demo
    print("🧪 Advanced Batch Processor Demo")
    
    # Test system resources
    print("\n💻 Thông tin hệ thống:")
    processor = AdvancedBatchProcessor()
    resources = processor.check_system_resources()
    print(f"   💾 RAM khả dụng: {resources['memory_available_gb']:.1f}GB")
    print(f"   🔥 CPU: {resources['cpu_percent']:.1f}%")
    print(f"   💿 Disk trống: {resources['disk_free_gb']:.1f}GB")
    
    print("\n✅ Advanced Batch Processor sẵn sàng xử lý 100+ video!")
