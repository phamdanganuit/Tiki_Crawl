#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tự động cài đặt và chạy công cụ thu thập dữ liệu Tiki
Chỉ cần nhấn nút "Bắt đầu thu thập dữ liệu" và mọi thứ sẽ được tự động

Tính năng:
- Tự động cài đặt các thư viện cần thiết nếu chưa có
- Tự động thiết lập môi trường
- Chạy quá trình thu thập dữ liệu đa luồng
- Hiển thị tiến trình và kết quả
"""

import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import importlib
import importlib.util
from io import StringIO
import contextlib

# Đường dẫn thư mục
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(BASE_DIR, "src")
DATA_DIR = os.path.join(BASE_DIR, "data")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Danh sách các thư viện cần thiết
REQUIRED_PACKAGES = [
    "pandas",
    "selenium",
    "webdriver-manager",
    "tkinter",
    "requests",
]

class RedirectOutput:
    """Lớp để chuyển hướng đầu ra từ console sang text widget"""
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.buffer = StringIO()
        
    def write(self, string):
        self.buffer.write(string)
        self.text_widget.configure(state="normal")
        self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END)
        self.text_widget.configure(state="disabled")
        
    def flush(self):
        pass

class AutomationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Công cụ thu thập dữ liệu tự động")
        self.root.geometry("800x600")
        
        # Đặt biểu tượng nếu có
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass
        
        # Đảm bảo các thư mục tồn tại
        os.makedirs(DATA_DIR, exist_ok=True)
        os.makedirs(LOGS_DIR, exist_ok=True)
        
        # Tạo và cấu hình các widget
        self.create_widgets()
        
        # Hiển thị thông tin khởi động
        self.log("Khởi động công cụ tự động thu thập dữ liệu...")
        self.log(f"Thư mục gốc: {BASE_DIR}")
        self.log("Đang kiểm tra môi trường...")
        
        # Kiểm tra môi trường khi khởi động
        self.check_environment()
    
    def create_widgets(self):
        """Tạo giao diện người dùng với các widget cần thiết"""
        # Frame chính
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Nhãn tiêu đề
        title_label = ttk.Label(
            main_frame, 
            text="Công cụ thu thập dữ liệu tự động", 
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=10)
        
        # Khung log
        log_frame = ttk.LabelFrame(main_frame, text="Nhật ký hoạt động", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Widget hiển thị log
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.configure(state="disabled")
        
        # Thanh tiến độ
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(progress_frame, text="Tiến độ:").pack(side=tk.LEFT)
        
        self.progress = ttk.Progressbar(
            progress_frame, orient=tk.HORIZONTAL, length=500, mode='indeterminate'
        )
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Nút bấm
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.start_button = ttk.Button(
            button_frame, 
            text="Bắt đầu thu thập dữ liệu", 
            command=self.start_data_collection,
            style="Accent.TButton"
        )
        self.start_button.pack(side=tk.RIGHT)
        
        ttk.Button(
            button_frame, 
            text="Kiểm tra môi trường", 
            command=self.check_environment
        ).pack(side=tk.RIGHT, padx=10)

        # Tạo style cho nút bấm
        style = ttk.Style()
        style.configure("Accent.TButton", font=("Arial", 11, "bold"))
    
    def log(self, message):
        """Ghi thông báo vào khung log"""
        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state="disabled")
        # Cập nhật giao diện
        self.root.update_idletasks()
    
    def check_environment(self):
        """Kiểm tra môi trường và cài đặt thư viện nếu cần"""
        self.log("Đang kiểm tra các thư viện cần thiết...")
        missing_packages = []
        
        for package in REQUIRED_PACKAGES:
            try:
                # Thử import thư viện để kiểm tra
                if package == "tkinter":  # tkinter đã được import ở đầu file
                    continue
                importlib.import_module(package)
                self.log(f"✓ Thư viện {package} đã được cài đặt")
            except ImportError:
                self.log(f"✗ Thư viện {package} chưa được cài đặt")
                missing_packages.append(package)
        
        # Cài đặt các thư viện còn thiếu
        if missing_packages:
            self.log(f"\nĐang cài đặt {len(missing_packages)} thư viện còn thiếu...")
            self.install_packages(missing_packages)
        else:
            self.log("\nMôi trường đã sẵn sàng! Bấm 'Bắt đầu thu thập dữ liệu' để tiếp tục.")
        
        # Kiểm tra các file CSV cần thiết
        self.check_data_files()
    
    def check_data_files(self):
        """Kiểm tra các file dữ liệu cần thiết"""
        url_file = os.path.join(DATA_DIR, "url_final_5.csv")
        
        if not os.path.exists(url_file):
            # Tìm kiếm trong thư mục gốc
            old_url_file = os.path.join(BASE_DIR, "url_final_5.csv")
            if os.path.exists(old_url_file):
                # Sao chép file vào thư mục data
                try:
                    import shutil
                    shutil.copy2(old_url_file, url_file)
                    self.log(f"✓ Đã sao chép file URL từ thư mục gốc vào {DATA_DIR}")
                except Exception as e:
                    self.log(f"✗ Lỗi khi sao chép file URL: {e}")
            else:
                self.log(f"✗ Không tìm thấy file URL cần thiết (url_final_5.csv)")
    
    def install_packages(self, packages):
        """Cài đặt các thư viện Python bằng pip"""
        try:
            for package in packages:
                self.log(f"Đang cài đặt {package}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                self.log(f"✓ Đã cài đặt thành công {package}")
            
            self.log("\nĐã cài đặt tất cả thư viện cần thiết!")
            self.log("Môi trường đã sẵn sàng! Bấm 'Bắt đầu thu thập dữ liệu' để tiếp tục.")
        except subprocess.CalledProcessError as e:
            self.log(f"Lỗi khi cài đặt thư viện: {e}")
            messagebox.showerror(
                "Lỗi cài đặt", 
                "Không thể cài đặt một số thư viện. Vui lòng thử cài đặt thủ công."
            )
    
    def start_data_collection(self):
        """Khởi động quá trình thu thập dữ liệu"""
        self.log("\n=== BẮT ĐẦU QUÁ TRÌNH THU THẬP DỮ LIỆU ===")
        
        # Vô hiệu hóa nút bấm để tránh chạy nhiều lần
        self.start_button.configure(state="disabled")
        
        # Bắt đầu thanh tiến độ
        self.progress.start()
        
        # Tạo luồng riêng cho quá trình thu thập dữ liệu
        collection_thread = threading.Thread(target=self.run_data_collection)
        collection_thread.daemon = True  # Luồng sẽ thoát khi chương trình chính thoát
        collection_thread.start()
    
    def modify_script_paths(self, script_code):
        """Điều chỉnh các đường dẫn trong mã nguồn để phù hợp với cấu trúc thư mục mới"""
        # Thay đổi URL_FILE và OUTPUT_FILE để trỏ đến thư mục data
        script_code = script_code.replace(
            'URL_FILE = "url_final_5.csv"', 
            f'URL_FILE = os.path.join("{DATA_DIR}", "url_final_5.csv")'
        )
        script_code = script_code.replace(
            'OUTPUT_FILE = "raw_data.csv"',
            f'OUTPUT_FILE = os.path.join("{DATA_DIR}", "raw_data.csv")'
        )
        
        # Điều chỉnh đường dẫn file log
        script_code = script_code.replace(
            'logging.FileHandler("scraper_multithread.log"',
            f'logging.FileHandler(os.path.join("{LOGS_DIR}", "scraper_multithread.log")'
        )
        
        return script_code
    
    def run_data_collection(self):
        """Chạy quá trình thu thập dữ liệu từ multiThreads4All.py"""
        try:
            # Chuyển hướng đầu ra từ console sang widget hiển thị log
            original_stdout = sys.stdout
            original_stderr = sys.stderr
            
            sys.stdout = RedirectOutput(self.log_text)
            sys.stderr = RedirectOutput(self.log_text)
            
            # Xác định đường dẫn đến file chính
            script_path = os.path.join(SRC_DIR, "multiThreads4All.py")
            
            if not os.path.exists(script_path):
                self.log(f"Lỗi: Không tìm thấy file {script_path}")
                raise FileNotFoundError(f"Không tìm thấy file {script_path}")
            
            self.log(f"Bắt đầu chạy {script_path}")
            
            # Đọc mã nguồn
            with open(script_path, 'r', encoding='utf-8') as file:
                script_code = file.read()
            
            # Điều chỉnh đường dẫn trong mã nguồn
            script_code = self.modify_script_paths(script_code)
            
            # Tạo namespace để chạy mã
            namespace = {}
            
            # Thực thi mã và bắt lỗi
            try:
                exec(script_code, namespace)
                
                # Kiểm tra xem có hàm process_urls_and_save_multithreaded không
                if 'process_urls_and_save_multithreaded' in namespace:
                    self.log("\nBắt đầu thu thập dữ liệu đa luồng...")
                    start_time = time.time()
                    namespace['process_urls_and_save_multithreaded']()
                    end_time = time.time()
                    self.log(f"\nHoàn thành! Tổng thời gian: {end_time - start_time:.2f} giây")
                else:
                    self.log("Lỗi: Không tìm thấy hàm process_urls_and_save_multithreaded trong mã nguồn")
            
            except Exception as e:
                self.log(f"\nLỗi khi thực thi mã: {e}")
                import traceback
                self.log(traceback.format_exc())
            
            # Khôi phục stdout và stderr
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Đã xảy ra lỗi: {e}")
        finally:
            # Dừng thanh tiến độ và kích hoạt lại nút bấm
            self.progress.stop()
            self.start_button.configure(state="normal")
            
            # Thông báo hoàn thành
            self.log("\n=== QUÁ TRÌNH THU THẬP DỮ LIỆU ĐÃ HOÀN THÀNH ===")
            messagebox.showinfo("Hoàn thành", "Quá trình thu thập dữ liệu đã hoàn thành!")

def main():
    """Hàm chính khởi động ứng dụng"""
    root = tk.Tk()
    app = AutomationApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()