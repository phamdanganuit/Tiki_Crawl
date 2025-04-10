import csv

import time

import pandas as pd

from selenium import webdriver

from selenium.webdriver.chrome.service import Service

from selenium.webdriver.chrome.options import Options

from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import WebDriverWait

from selenium.webdriver.support import expected_conditions as EC

from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException



def setup_driver():

    """Setup and return the Chrome WebDriver"""

    chrome_options = Options()

    # Uncomment below line to run in headless mode if needed

    # chrome_options.add_argument("--headless")

    # chrome_options.add_argument("--no-sandbox")

    # chrome_options.add_argument("--disable-dev-shm-usage")

   

    driver = webdriver.Chrome(options=chrome_options)

    return driver



def extract_reviews_from_page(driver):

    """Extract review titles and content from current page"""

    reviews = []

   

    # Wait for reviews to load

    try:

        WebDriverWait(driver, 10).until(

            EC.presence_of_element_located((By.CLASS_NAME, "review-comment__title"))

        )

       

        # Find all review elements

        review_titles = driver.find_elements(By.CLASS_NAME, "review-comment__title")

        review_contents = driver.find_elements(By.CLASS_NAME, "review-comment__content")

       

        # Extract data

        for i in range(len(review_titles)):

            if i < len(review_contents):

                title = review_titles[i].text.strip()

                content = review_contents[i].text.strip()

                reviews.append({

                    'title': title,

                    'content': content

                })

               

    except TimeoutException:

        print("No reviews found or page took too long to load")

       

    return reviews



def has_next_page(driver):

    """Check if there's a next page button that's clickable"""

    try:

        next_button = driver.find_element(By.CSS_SELECTOR, "a.btn.next")

        # Check if the button exists and is not disabled

        return next_button.is_displayed() and "disabled" not in next_button.get_attribute("class")

    except NoSuchElementException:

        return False



def click_next_page(driver):

    """Click the next page button"""

    try:

        next_button = WebDriverWait(driver, 10).until(

            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.btn.next"))

        )

        driver.execute_script("arguments[0].click();", next_button)

        # Wait for the page to load

        time.sleep(2)

        return True

    except (NoSuchElementException, TimeoutException, StaleElementReferenceException):

        print("Next button not found or not clickable")

        return False



def crawl_product_reviews(driver, url):

    """Crawl all reviews for a given product URL"""

    all_reviews = []

    product_data = []

   

    try:

        driver.get(url)

        time.sleep(3)  # Allow page to load completely

       

        # Scroll to reviews section if available

        try:

            reviews_section = WebDriverWait(driver, 10).until(

                EC.presence_of_element_located((By.CLASS_NAME, "review-comment__title"))

            )

            driver.execute_script("arguments[0].scrollIntoView();", reviews_section)

        except TimeoutException:

            print(f"No reviews found for URL: {url}")

            return product_data

       

        page_num = 1

        while True:

            print(f"Processing page {page_num} for URL: {url}")

            reviews = extract_reviews_from_page(driver)

            all_reviews.extend(reviews)

           

            # Create product data entries

            for review in reviews:

                product_data.append({

                    'product_url': url,

                    'title': review['title'],

                    'content': review['content']

                })

           

            if has_next_page(driver):

                if not click_next_page(driver):

                    break

                page_num += 1

            else:

                break

               

    except Exception as e:

        print(f"Error processing URL {url}: {e}")

       

    return product_data



def main():

    # Read URLs from the csv file

    try:

        urls_df = pd.read_csv("url_final.csv")

        # Assuming the column with URLs is named 'url'

        # urls = urls_df['URL'].tolist()

        urls=['https://tiki.vn/may-tinh-casio-fx580vn-x-p104769768.html?spid=104769772']

    except Exception as e:

        print(f"Error reading URL file: {e}")

        return

   

    driver = setup_driver()

   

    # Initialize CSV file

    with open("raw_data.csv", 'w', newline='', encoding='utf-8') as f:

        writer = csv.DictWriter(f, fieldnames=['product_url', 'title', 'content'])

        writer.writeheader()

   

    # Process each URL

    for url in urls:

        print(f"Processing: {url}")

        review_data = crawl_product_reviews(driver, url)

       

        # Append data to CSV

        with open("raw_data.csv", 'a', newline='', encoding='utf-8') as f:

            writer = csv.DictWriter(f, fieldnames=['product_url', 'title', 'content'])

            writer.writerows(review_data)

   

    driver.quit()

    print("All reviews have been collected and saved to raw_data.csv")



if __name__ == "__main__":

    main()