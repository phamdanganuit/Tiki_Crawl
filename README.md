# TikiReviewScraper - Dự án Thu thập Dữ liệu Đánh giá Tiki

Công cụ tự động thu thập dữ liệu đánh giá của người dùng từ website Tiki.vn, sử dụng Python và Selenium.

## Cấu trúc Workspace

- `src/`: Chứa mã nguồn Python
  - `auto_setup_and_run.py`: Script tự động cài đặt và chạy
  - `multiThreads4All.py`: Mã thu thập dữ liệu đa luồng
  - `singleThread.py`: Mã thu thập dữ liệu đơn luồng
  - `crawl url.py`: Script thu thập URL
  - `main.py`: Script chính

- `data/`: Chứa các file dữ liệu
  - `raw_data.csv`: Dữ liệu đánh giá đã thu thập
  - `url_final_5.csv`: Danh sách URL để thu thập
  - Các file CSV khác

- `notebooks/`: Chứa các Jupyter notebook
  - `eda.ipynb`: Phân tích khám phá dữ liệu
  - `1.ipynb`: Notebook khác

- `logs/`: Chứa các file log
  - `scraper_multithread.log`: Log của quá trình thu thập đa luồng

- `browser_profiles/`: Chứa các profile trình duyệt Chrome
  - `chrome_data/`: Dữ liệu Chrome WebDriver

## Cách sử dụng

1. Chạy file `start_data_collection.bat` để bắt đầu quá trình thu thập dữ liệu tự động.
2. Dữ liệu thu thập sẽ được lưu trong thư mục `data/`.

## Tính năng

- Thu thập dữ liệu đa luồng, cải thiện hiệu suất và tốc độ
- Tự động cài đặt các thư viện cần thiết
- Giao diện người dùng đơn giản với một nút bấm
- Xử lý lỗi và tự động thử lại
- Lưu trữ dữ liệu có cấu trúc trong file CSV
