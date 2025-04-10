from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
import pandas as pd
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

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
df.to_csv('urls.csv', index=False)
