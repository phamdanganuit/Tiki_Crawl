# d:\University\SEM6_2024-2025\DS108\crawl-ttdd-main-2\extract_reviews.py

import pandas as pd
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager

# --- Đường dẫn thư mục ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Thư mục gốc của dự án
DATA_DIR = os.path.join(BASE_DIR, "data")  # Thư mục chứa dữ liệu
LOGS_DIR = os.path.join(BASE_DIR, "logs")  # Thư mục chứa log
BROWSER_PROFILES_DIR = os.path.join(BASE_DIR, "browser_profiles")  # Thư mục chứa profile trình duyệt

# Đảm bảo các thư mục tồn tại
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# --- Constants ---
URL_FILE = os.path.join(DATA_DIR, "url_final.csv")  # Cập nhật đường dẫn
OUTPUT_FILE = os.path.join(DATA_DIR, "raw_data.csv")  # Cập nhật đường dẫn

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")
    
    # Sử dụng chrome_data từ thư mục browser_profiles nếu có
    chrome_data_path = os.path.join(BROWSER_PROFILES_DIR, "chrome_data")
    if os.path.exists(chrome_data_path):
        chrome_options.add_argument(f"--user-data-dir={chrome_data_path}")
        print(f"Using Chrome profile from {chrome_data_path}")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def click_show_more_buttons(driver):
    try:
        show_more_buttons = driver.find_elements(By.XPATH, "//span[@class='show-more-content' and text()='Xem thêm']")
        for button in show_more_buttons:
            try:
                driver.execute_script("arguments[0].click();", button)
                time.sleep(0.5)
            except Exception:
                pass
    except Exception as e:
        print(f"Error clicking show more buttons: {e}")

def extract_review_data(driver):
    reviews = []
    try:
        review_containers = driver.find_elements(By.CSS_SELECTOR, "div.review-comment")
        
        for container in review_containers:
            try:
                # Extract title
                title = "N/A"
                try:
                    title_element = container.find_element(By.CSS_SELECTOR, "div.review-comment__title")
                    title = title_element.text.strip()
                except NoSuchElementException:
                    pass
                
                # Extract content
                content = "N/A"
                try:
                    content_element = container.find_element(By.CSS_SELECTOR, "div.review-comment__content")
                    content = content_element.text.strip()
                except NoSuchElementException:
                    pass
                
                reviews.append({"title": title, "content": content})
                
            except Exception as e:
                print(f"Error extracting review data: {e}")
                continue
                
    except Exception as e:
        print(f"Error finding review containers: {e}")
    
    return reviews

def navigate_through_reviews(driver, url):
    all_reviews = []
    
    try:
        driver.get(url)
        time.sleep(3)  # Wait for page to load
        
        # Scroll to reviews section
        try:
            reviews_section = driver.find_element(By.ID, "productReviews")
            driver.execute_script("arguments[0].scrollIntoView();", reviews_section)
            time.sleep(2)
        except NoSuchElementException:
            print("Reviews section not found, scrolling down anyway")
            driver.execute_script("window.scrollBy(0, 800);")
            time.sleep(2)
        
        page_num = 1
        while True:
            print(f"Processing review page {page_num}")
            
            # Click on any "Show more" buttons to expand review content
            click_show_more_buttons(driver)
            
            # Extract review data from current page
            page_reviews = extract_review_data(driver)
            if page_reviews:
                all_reviews.extend(page_reviews)
                print(f"Extracted {len(page_reviews)} reviews from page {page_num}")
            
            # Find and click the next page button
            try:
                next_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a.btn.next"))
                )
                
                # Check if the next button is disabled
                if next_button.get_attribute("class") and "disabled" in next_button.get_attribute("class"):
                    print("Reached last page")
                    break
                
                driver.execute_script("arguments[0].click();", next_button)
                time.sleep(2)  # Wait for next page to load
                page_num += 1
            except (TimeoutException, StaleElementReferenceException):
                print("No next button found or reached last page")
                break
            except Exception as e:
                print(f"Error navigating to next page: {e}")
                break
    
    except Exception as e:
        print(f"Error processing URL {url}: {e}")
    
    return all_reviews

def process_urls_and_save_reviews():
    # Check if url_final.csv exists
    if not os.path.exists(URL_FILE):
        print(f"Error: {URL_FILE} file not found")
        return
    
    # Read URLs from CSV file
    try:
        urls_df = pd.read_csv(URL_FILE)
        print(f"Read {len(urls_df)} URLs from {URL_FILE}")
    except Exception as e:
        print(f"Error reading {URL_FILE}: {e}")
        return
    
    # Find the URL column
    url_column = None
    for col in urls_df.columns:
        if 'url' in col.lower():
            url_column = col
            break
    
    if not url_column:
        print(f"Error: Could not find URL column in {URL_FILE}")
        return
    
    driver = setup_driver()
    all_reviews = []
    
    try:
        # Process each URL
        for index, row in urls_df.iterrows():
            url = row[url_column]
            print(f"\nProcessing URL {index+1}/{len(urls_df)}: {url}")
            
            reviews = navigate_through_reviews(driver, url)
            all_reviews.extend(reviews)
            
            # Save intermediate results after each URL
            reviews_df = pd.DataFrame(all_reviews)
            temp_output = os.path.join(DATA_DIR, f"raw_data_temp_{index+1}.csv")
            reviews_df.to_csv(temp_output, index=False)
            
            print(f"Processed URL {index+1}/{len(urls_df)}. Total reviews so far: {len(all_reviews)}")
    
    except Exception as e:
        print(f"Error during processing: {e}")
    
    finally:
        driver.quit()
        
        # Save final results
        if all_reviews:
            reviews_df = pd.DataFrame(all_reviews)
            reviews_df.to_csv(OUTPUT_FILE, index=False)
            print(f"All done! Extracted {len(all_reviews)} reviews and saved to {OUTPUT_FILE}")
        else:
            print("No reviews extracted")

if __name__ == "__main__":
    print(f"Data directory: {DATA_DIR}")
    print(f"Input file: {URL_FILE}")
    print(f"Output file: {OUTPUT_FILE}")
    process_urls_and_save_reviews()