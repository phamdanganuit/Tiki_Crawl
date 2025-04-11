import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException
from urllib.parse import urljoin
import time
import os

# --- Cấu hình ---
input_csv_file = 'urls.csv'
output_csv_file = 'url_final.csv'
so_lan_nhap_xem_them_toi_da = 0
base_url = "https://tiki.vn"

xem_them_button_selector = "div[data-view-id='category_infinity_view.more']"
product_link_selector = "a.product-item" 

# --- Khởi tạo WebDriver ---
print("Đang khởi tạo WebDriver...")
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(options=options)
driver.maximize_window()
print("WebDriver đã sẵn sàng.")

# --- Danh sách để lưu tất cả kết quả ---
all_results = []

# --- Đọc file CSV đầu vào ---
try:
    with open(input_csv_file, mode='r', newline='', encoding='utf-8') as infile:
        reader = csv.reader(infile)
        header = next(reader)
        category_urls = [row[0] for row in reader if row]
    print(f"Đã đọc {len(category_urls)} URL danh mục từ {input_csv_file}")
except FileNotFoundError:
    print(f"LỖI: Không tìm thấy file {input_csv_file}. Vui lòng tạo file này.")
    driver.quit()
    exit()
except Exception as e:
    print(f"LỖI khi đọc file {input_csv_file}: {e}")
    driver.quit()
    exit()

# --- Xử lý từng URL danh mục ---
for index, category_url in enumerate(category_urls):
    print(f"\n--- Đang xử lý URL danh mục {index + 1}/{len(category_urls)}: {category_url} ---")
    driver.get(category_url)
    time.sleep(2)

    # --- Nhấp nút "Xem thêm" ---
    so_lan_nhap_thuc_te = 0
    for i in range(so_lan_nhap_xem_them_toi_da):
        try:
            wait = WebDriverWait(driver, 10)
            # Di chuyển tới cuối trang trước khi tìm nút
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.8)

            xem_them_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, xem_them_button_selector)))
            driver.execute_script("arguments[0].click();", xem_them_button)
            so_lan_nhap_thuc_te += 1
            print(f"  -> Đã nhấp 'Xem thêm' lần thứ {so_lan_nhap_thuc_te}")
            time.sleep(3)

        except (TimeoutException, NoSuchElementException,
                ElementNotInteractableException):
            print("  -> Không tìm thấy hoặc không thể nhấp 'Xem thêm' nữa.")
            break
        except Exception as e:
            print(f"  -> Lỗi khi nhấp 'Xem thêm': {e}")
            break

    print(f"  -> Đã nhấp 'Xem thêm' tổng cộng {so_lan_nhap_thuc_te} lần.")

    # --- Thu thập link sản phẩm sau khi đã nhấp "Xem thêm" ---
    category_product_links = set()
    print("  -> Bắt đầu thu thập link sản phẩm...")
    try:
        time.sleep(2)
        # Tìm tất cả các phần tử link sản phẩm
        product_elements = driver.find_elements(By.CSS_SELECTOR, product_link_selector)
        print(f"  -> Tìm thấy {len(product_elements)}"
              " phần tử sản phẩm tiềm năng.")

        for element in product_elements:
            try:
                href = element.get_attribute('href')
                if href:
                    full_url = urljoin(base_url, href)
                    category_product_links.add(full_url)
            except Exception as e_inner:
                print(f"    -> Lỗi nhỏ khi lấy href: {e_inner}")

        print(f"  -> Thu thập được {len(category_product_links)} "
              "link sản phẩm duy nhất cho danh mục này.")

        # Thêm kết quả vào danh sách tổng
        for product_url in category_product_links:
            all_results.append({'URL': product_url, 'detail': category_url})

    except Exception as e:
        print(f"  -> LỖI khi thu thập link sản phẩm cho {category_url}: {e}")

# --- Đóng trình duyệt ---
print("\nĐang đóng trình duyệt...")
driver.quit()

# --- Ghi kết quả ra file CSV đầu ra ---
if all_results:
    print(f"\nĐang ghi {len(all_results)} kết quả vào file {output_csv_file}...")
    try:
        with open(output_csv_file, mode='w', newline='',
                  encoding='utf-8') as outfile:
            fieldnames = ['URL', 'detail'] # Tên cột
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)

            writer.writeheader() # Ghi dòng tiêu đề
            writer.writerows(all_results) # Ghi tất cả dữ liệu
        print(f"Đã ghi kết quả thành công vào: {os.path.join(os.getcwd(),
              output_csv_file)}")
    except Exception as e:
        print(f"LỖI khi ghi vào file {output_csv_file}: {e}")
else:
    print("\nKhông có kết quả nào để ghi ra file.")

print("\n--- Hoàn tất ---")