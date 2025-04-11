from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
import pandas as pd
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import os

# Đường dẫn thư mục
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Thư mục gốc của dự án
DATA_DIR = os.path.join(BASE_DIR, "data")  # Thư mục chứa dữ liệu

# Đảm bảo thư mục data tồn tại
os.makedirs(DATA_DIR, exist_ok=True)

options = Options()

driver = webdriver.Chrome()

url = "https://tiki.vn/"

driver.get(url)

wait = WebDriverWait(driver, 10)

try:
    close_button_selector = "img[alt='close-icon']"
    close_button = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, close_button_selector))
    )
    close_button.click()
    print("Đã click nút đóng pop-up.")
except TimeoutException:
    print(
        "Không tìm thấy hoặc không thể click nút đóng pop-up "
        "trong thời gian chờ."
    )
except Exception as e:
    print(f"Lỗi khi click nút đóng: {e}")

xpath_expression = (
    "//div[@class='sc-cffe1c5-0 bKBPyH']"
    "[.//div[normalize-space(.)='Danh mục']]//a"
)
urls_list = []
elements = driver.find_elements(
    By.XPATH,
    "//div[@class='sc-cffe1c5-0 bKBPyH'][div[text()='Danh mục']]//a"
)
hrefs = [el.get_attribute('href') for el in elements]
for href in hrefs:
    if href not in urls_list:
        urls_list.append(href)
print(urls_list)
df = pd.DataFrame(urls_list, columns=['URL'])
# Lưu vào thư mục data
output_file = os.path.join(DATA_DIR, 'urls.csv')
df.to_csv(output_file, index=False)
print(f"Đã lưu danh sách URL vào {output_file}")

# Đóng trình duyệt khi hoàn thành
driver.quit()
