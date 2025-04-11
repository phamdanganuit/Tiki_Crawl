# final1.py (Multithreaded Version)
import pandas as pd
import time
import os
import logging
import threading # Thêm thư viện threading
from queue import Queue # Thêm thư viện queue
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
    ElementClickInterceptedException,
    WebDriverException, # Bắt lỗi WebDriver chung
)
from webdriver_manager.chrome import ChromeDriverManager
from typing import List, Dict, Optional, Tuple

# --- Constants ---
URL_FILE = "url_final_5.csv"
OUTPUT_FILE = "raw_data.csv"
DEFAULT_WAIT_TIME = 15 # Tăng thời gian chờ một chút khi chạy đa luồng
SHORT_WAIT_TIME = 3
URL_COLUMN_NAME = "URL" 
DETAIL_COLUMN_NAME = "detail" 
OUTPUT_COLUMNS = ['title', 'content', 'type'] 
MAX_WORKERS = 4  # !!! ĐIỀU CHỈNH SỐ LUỒNG PHÙ HỢP VỚI MÁY CỦA BẠN !!!

# Selectors
REVIEWS_SECTION_ID = "customer-review-widget-id" 
REVIEW_CONTAINER_CSS = "div.review-comment"
REVIEW_TITLE_CSS = "div.review-comment__title"
REVIEW_CONTENT_CSS = "div.review-comment__content"
SHOW_MORE_CONTENT_CSS = "span.show-more-content" 
NEXT_PAGE_BUTTON_CSS = "a.btn.next:not(.disabled)" 

# --- Logging Setup ---
# Log cơ bản, có thể bị xen kẽ giữa các luồng
if os.path.exists("scraper_multithread.log"):
    os.remove("scraper_multithread.log")
    
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s', # Thêm tên luồng vào log
                    handlers=[
                        logging.FileHandler("scraper_multithread.log", mode='w', encoding='utf-8'), 
                        logging.StreamHandler() 
                    ])

# --- Shared Resources ---
url_queue = Queue() # Queue để chứa các cặp (url, detail) cần xử lý
results_list = [] # List chung để lưu kết quả từ các luồng
results_lock = threading.Lock() # Lock để bảo vệ việc ghi vào results_list

# --- Functions (Giữ nguyên hoặc sửa đổi nhỏ) ---

def setup_driver() -> Optional[webdriver.Chrome]:
    """Initializes and configures the Chrome WebDriver."""
    # (Giữ nguyên phần lớn hàm setup_driver, nhưng thêm return Optional và xử lý lỗi)
    chrome_options = Options()
    # Các options giống như trước
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--log-level=3") 
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging']) 
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36") 
    chrome_options.add_argument("--headless") # Chạy headless thường ổn định hơn khi đa luồng
    chrome_options.add_argument("--disable-gpu") 
    chrome_options.add_argument("--no-sandbox") # Có thể cần trên một số hệ thống Linux/Docker
    chrome_options.add_argument("--disable-dev-shm-usage") # Có thể cần trên một số hệ thống Linux/Docker

    try:
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        logging.debug("WebDriver setup successfully for thread.")
        return driver
    except Exception as e:
        # Ghi log lỗi cụ thể cho luồng này
        logging.error(f"Error setting up WebDriver in thread: {e}", exc_info=True)
        return None # Trả về None nếu không khởi tạo được driver

# click_all_show_more_in_reviews và extract_review_data giữ nguyên như phiên bản trước
def click_all_show_more_in_reviews(driver: webdriver.Chrome):
    """Finds and clicks all 'Xem thêm' buttons within review content."""
    try:
        show_more_buttons = driver.find_elements(By.CSS_SELECTOR, f"{REVIEW_CONTENT_CSS} {SHOW_MORE_CONTENT_CSS}")
        if not show_more_buttons: return
        clicked_count = 0
        for button in show_more_buttons:
            try:
                if button.is_displayed():
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", button)
                    time.sleep(0.2) 
                    driver.execute_script("arguments[0].click();", button)
                    clicked_count += 1
                    time.sleep(0.5) 
            except StaleElementReferenceException: logging.debug("Stale 'Xem thêm' button.")
            except ElementClickInterceptedException: logging.warning("Intercepted 'Xem thêm' click.")
            except Exception as e: logging.warning(f"Click 'Xem thêm' error: {e}")
        if clicked_count > 0: logging.debug(f"Clicked {clicked_count} 'Xem thêm' buttons.")
    except Exception as e: logging.error(f"Find/Click 'Xem thêm' error: {e}", exc_info=False)

def extract_review_data(driver: webdriver.Chrome) -> List[Dict[str, str]]:
    """Extracts title and content data from review elements on the current page."""
    reviews_on_page = []
    try:
        review_containers = driver.find_elements(By.CSS_SELECTOR, REVIEW_CONTAINER_CSS) # Dùng find_elements để tránh lỗi nếu không có review nào
        if not review_containers: return []

        for container in review_containers:
            title = "N/A"
            content = "N/A"
            try:
                title_element = container.find_element(By.CSS_SELECTOR, REVIEW_TITLE_CSS)
                title = title_element.text.strip()
            except NoSuchElementException: pass 
            except StaleElementReferenceException: pass
                 
            try:
                content_element = container.find_element(By.CSS_SELECTOR, REVIEW_CONTENT_CSS)
                content = content_element.text.strip() 
            except NoSuchElementException: pass 
            except StaleElementReferenceException: pass

            reviews_on_page.append({"title": title, "content": content})

    except Exception as e: logging.error(f"Extract reviews error: {e}", exc_info=False)
    return reviews_on_page

def navigate_and_scrape_reviews(driver: webdriver.Chrome, url: str, detail_type: str) -> List[Dict[str, str]]:
    """Navigates, paginates, scrapes reviews for a single URL, and adds type."""
    # (Hàm này gần như giữ nguyên logic cốt lõi, chỉ thêm logging rõ hơn)
    all_reviews_for_url = []
    try:
        logging.info(f"Navigating to: {url}")
        driver.get(url)
        WebDriverWait(driver, DEFAULT_WAIT_TIME).until(EC.presence_of_element_located((By.TAG_NAME, "main")))
        logging.debug(f"Page loaded: {url}")

        # Scroll to Reviews Section
        try:
            reviews_section_element = WebDriverWait(driver, DEFAULT_WAIT_TIME).until(EC.presence_of_element_located((By.ID, REVIEWS_SECTION_ID)))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", reviews_section_element)
            WebDriverWait(driver, SHORT_WAIT_TIME).until(EC.visibility_of_element_located((By.CSS_SELECTOR, REVIEW_CONTAINER_CSS)))
            logging.debug(f"Scrolled to reviews section '{REVIEWS_SECTION_ID}'.")
        except TimeoutException:
            logging.warning(f"Reviews section '{REVIEWS_SECTION_ID}'/'{REVIEW_CONTAINER_CSS}' not found/visible after scroll. Proceeding without specific scroll.")
            # Có thể thử cuộn chung chung nếu cần, nhưng có thể bỏ qua để xem có load không
            # driver.execute_script("window.scrollBy(0, 1200);") 
            # time.sleep(SHORT_WAIT_TIME) 

        page_num = 1
        while True:
            logging.debug(f"Processing page {page_num} for URL: {url}")
            click_all_show_more_in_reviews(driver)
            page_reviews_raw = extract_review_data(driver)
            
            reviews_processed_count = 0
            for review in page_reviews_raw:
                review['type'] = detail_type 
                all_reviews_for_url.append(review)
                reviews_processed_count += 1

            if reviews_processed_count > 0:
                logging.debug(f"Extracted {reviews_processed_count} reviews from page {page_num}.")
            else:
                 # Nếu trang đầu không có review thì dừng luôn cho URL này
                 if page_num == 1:
                     logging.warning(f"No reviews found on first page for {url}. Skipping rest of this URL.")
                     break
                 else: # Nếu các trang sau không có review thì coi như hết trang
                     logging.debug(f"No reviews found on page {page_num}, likely end for {url}.")
                     break 

            # Find and Click Next
            try:
                next_button = WebDriverWait(driver, SHORT_WAIT_TIME).until(EC.element_to_be_clickable((By.CSS_SELECTOR, NEXT_PAGE_BUTTON_CSS)))
                driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", next_button)
                time.sleep(0.3) 
                driver.execute_script("arguments[0].click();", next_button)
                
                # Wait for next page load (wait for *any* review container)
                try:
                    WebDriverWait(driver, DEFAULT_WAIT_TIME).until(EC.presence_of_element_located((By.CSS_SELECTOR, REVIEW_CONTAINER_CSS)))
                except TimeoutException:
                     logging.warning(f"Timeout waiting for reviews on page {page_num + 1}. Assuming end.")
                     break 
                page_num += 1
                time.sleep(0.5) 
            except TimeoutException: logging.debug(f"No clickable 'Next' button. End of pagination for {url}."); break 
            except StaleElementReferenceException: logging.warning("Next button stale. Stopping pagination."); break
            except ElementClickInterceptedException: logging.error("Next button click intercepted. Stopping."); break
            except Exception as e: logging.error(f"Next page error: {e}", exc_info=False); break 
    
    except WebDriverException as e:
         logging.error(f"WebDriver error during processing {url}: {e}", exc_info=False)
         # Có thể cần khởi tạo lại driver ở đây nếu lỗi nghiêm trọng, nhưng trong worker thì nên thoát
    except Exception as e:
        logging.error(f"Critical error processing {url}: {e}", exc_info=True) # Log full traceback cho lỗi lạ
    
    logging.info(f"Finished processing {url}. Found {len(all_reviews_for_url)} reviews.")
    return all_reviews_for_url

# --- Worker Function ---
def worker():
    """Function executed by each thread."""
    driver = setup_driver() # Mỗi luồng tự khởi tạo driver
    if driver is None:
        logging.error("Thread failed to initialize WebDriver. Exiting worker.")
        return # Thoát luồng nếu không tạo được driver

    while not url_queue.empty():
        try:
            url, detail_type = url_queue.get(timeout=1) # Lấy task từ queue
        except Queue.Empty:
            continue # Queue trống, luồng tiếp tục kiểm tra

        logging.info(f"Starting scrape for: {url} (Type: {detail_type})")
        scraped_data = [] 
        try:
             scraped_data = navigate_and_scrape_reviews(driver, url, detail_type)
        except Exception as e:
             logging.error(f"Unhandled exception during scraping {url}: {e}", exc_info=True)
             # Đảm bảo driver được đóng ngay cả khi có lỗi nghiêm trọng trong scrape
             try:
                 driver.quit()
             except: pass
             driver = setup_driver() # Thử khởi động lại driver cho task tiếp theo
             if driver is None:
                 logging.critical("Failed to restart driver after error. Worker exiting.")
                 url_queue.task_done() # Đánh dấu task lỗi là hoàn thành để queue không bị treo
                 # Có thể xem xét đưa task lỗi trở lại queue hoặc bỏ qua
                 break # Thoát worker nếu không restart được driver


        # --- Append results safely ---
        if scraped_data:
            with results_lock: # Sử dụng lock để đảm bảo chỉ một luồng ghi vào list tại một thời điểm
                results_list.extend(scraped_data)
                logging.debug(f"Added {len(scraped_data)} results from {url}. Total results: {len(results_list)}")

        url_queue.task_done() # Báo cho queue biết task này đã hoàn thành
        time.sleep(1) # Delay nhỏ giữa các URL trong cùng một luồng

    # --- Cleanup for the thread ---
    if driver:
        try:
            driver.quit()
            logging.debug("WebDriver closed for thread.")
        except Exception as e:
            logging.error(f"Error closing WebDriver in thread: {e}")

# --- Main Processing Logic ---
def process_urls_and_save_multithreaded(url_file: str = URL_FILE, output_file: str = OUTPUT_FILE):
    """Reads URLs, distributes them to worker threads, and saves final results."""
    if not os.path.exists(url_file):
        logging.error(f"Error: Input file '{url_file}' not found.")
        return

    try:
        urls_df = pd.read_csv(url_file)
        logging.info(f"Read {len(urls_df)} rows from '{url_file}'.")
        if URL_COLUMN_NAME not in urls_df.columns or DETAIL_COLUMN_NAME not in urls_df.columns:
             logging.error(f"Missing required columns '{URL_COLUMN_NAME}' or '{DETAIL_COLUMN_NAME}' in '{url_file}'.")
             return
    except Exception as e:
        logging.error(f"Error reading '{url_file}': {e}", exc_info=True)
        return

    # --- Populate the queue ---
    tasks_added = 0
    for index, row in urls_df.iterrows():
        url = row[URL_COLUMN_NAME]
        detail_value = row[DETAIL_COLUMN_NAME] 
        
        if not url or not isinstance(url, str) or not url.lower().startswith(('http://', 'https://')):
            logging.warning(f"Row {index+1}: Skipping invalid URL in input file: '{url}'")
            continue
        if pd.isna(detail_value):
           logging.warning(f"Row {index+1}: Missing detail for URL '{url}'. Using 'N/A'.")
           detail_value = "N/A"
        else:
           detail_value = str(detail_value) 

        url_queue.put((url, detail_value)) # Đưa tuple (url, detail) vào queue
        tasks_added += 1
        
    logging.info(f"Added {tasks_added} tasks to the queue.")
    if tasks_added == 0:
        logging.warning("No valid tasks found in the input file.")
        return

    # --- Create and start worker threads ---
    threads = []
    logging.info(f"Starting {MAX_WORKERS} worker threads...")
    for _ in range(MAX_WORKERS):
        thread = threading.Thread(target=worker, daemon=True) # daemon=True để luồng tự thoát nếu main thread thoát
        thread.start()
        threads.append(thread)

    # --- Wait for all tasks in the queue to be processed ---
    url_queue.join() # Chờ cho đến khi tất cả item trong queue được lấy ra và task_done() được gọi
    logging.info("All tasks processed by workers.")

    # --- Wait for worker threads to finish (optional but good practice) ---
    # Mặc dù queue.join() đã đảm bảo task xong, chờ thread kết thúc để chắc chắn driver được quit
    for thread in threads:
         thread.join(timeout=60) # Chờ tối đa 60s cho mỗi luồng kết thúc
         if thread.is_alive():
              logging.warning(f"Thread {thread.name} did not finish cleanly.")

    logging.info("All worker threads have completed.")

    # --- Final Save ---
    # Lưu ý: Không còn lưu trung gian trong phiên bản đa luồng này
    logging.info("Saving final results...")
    if results_list:
        try:
             # results_list giờ đã chứa tất cả dữ liệu từ các luồng
             final_df = pd.DataFrame(results_list, columns=OUTPUT_COLUMNS) 
             final_df.drop_duplicates(subset=['title', 'content', 'type'], inplace=True) 
             final_df.to_csv(output_file, index=False, encoding='utf-8-sig')
             logging.info(f"\n===== SCRAPING FINISHED (Multithreaded) =====")
             logging.info(f"Extracted {len(final_df)} unique reviews.")
             logging.info(f"Final data saved to '{output_file}'")
        except Exception as e:
            logging.error(f"Error saving final results to '{output_file}': {e}", exc_info=True)
    else:
        logging.info("\n===== SCRAPING FINISHED (Multithreaded) =====")
        logging.warning("No reviews were collected by any thread.")
        # Tạo file rỗng nếu chưa có
        if not os.path.exists(output_file):
            try:
                 empty_df = pd.DataFrame(columns=OUTPUT_COLUMNS) 
                 empty_df.to_csv(output_file, index=False, encoding='utf-8-sig')
                 logging.info(f"Output file '{output_file}' created with headers.")
            except Exception as e:
                 logging.error(f"Could not write empty header to {output_file}: {e}")

if __name__ == "__main__":
    start_time = time.time()
    process_urls_and_save_multithreaded()
    end_time = time.time()
    logging.info(f"Total execution time: {end_time - start_time:.2f} seconds")