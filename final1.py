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

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")
    
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
    if not os.path.exists("url_final.csv"):
        print("Error: url_final.csv file not found")
        return
    
    # Read URLs from CSV file
    try:
        urls_df = pd.read_csv("url_final.csv")
    except Exception as e:
        print(f"Error reading url_final.csv: {e}")
        return
    
    # Find the URL column
    url_column = None
    for col in urls_df.columns:
        if 'url' in col.lower():
            url_column = col
            break
    
    if not url_column:
        print("Error: Could not find URL column in url_final.csv")
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
            reviews_df.to_csv("raw_data.csv", index=False)
            
            print(f"Processed URL {index+1}/{len(urls_df)}. Total reviews so far: {len(all_reviews)}")
    
    except Exception as e:
        print(f"Error during processing: {e}")
    
    finally:
        driver.quit()
        
        # Save final results
        if all_reviews:
            reviews_df = pd.DataFrame(all_reviews)
            reviews_df.to_csv("raw_data.csv", index=False)
            print(f"All done! Extracted {len(all_reviews)} reviews and saved to raw_data.csv")
        else:
            print("No reviews extracted")

if __name__ == "__main__":
    process_urls_and_save_reviews()