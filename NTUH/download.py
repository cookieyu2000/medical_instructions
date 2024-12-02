import os
import json
import time
import re
import random
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# 儲存進度的檔案
PROGRESS_FILE = "NTUH/data/progress.json"
FAILED_FILE = "NTUH/data/failed.json"

# 初始化進度追蹤
def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_progress(progress):
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=4)

def save_failed_item(item):
    failed_items = []
    if os.path.exists(FAILED_FILE):
        with open(FAILED_FILE, "r", encoding="utf-8") as f:
            failed_items = json.load(f)
    failed_items.append(item)
    with open(FAILED_FILE, "w", encoding="utf-8") as f:
        json.dump(failed_items, f, ensure_ascii=False, indent=4)

# 清理檔案名稱
def clean_filename(filename):
    filename = re.sub(r'[\\/*?:"<>|]', "_", filename)  # 替換非法字元
    filename = filename.replace("\n", "").strip()      # 去除換行符
    return filename

# 初始化 WebDriver
def initialize_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    options.add_argument('--headless')  # 無頭模式
    options.add_argument('--disable-gpu')  # 避免 GPU 問題
    options.add_argument('--no-sandbox')  # 避免沙盒限制
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

driver = initialize_driver()
wait = WebDriverWait(driver, 20)

# 儲存路徑設定
base_dir = "NTUH/data"
categories = ["A", "B", "C", "D", "X"]
for category in categories:
    os.makedirs(os.path.join(base_dir, category, "用藥教育"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, category, "仿單"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, category, "詳細資料"), exist_ok=True)

# 打開目標頁面
driver.get("https://www.ntuh.gov.tw/phr/Fpage.action?muid=2077&fid=1939")
iframe = wait.until(EC.presence_of_element_located((By.XPATH, "//iframe[@title='藥品綜合查詢']")))
driver.switch_to.frame(iframe)

progress = load_progress()

# 處理每個分類
for category in categories:
    print(f"正在處理分類：{category}")
    try:
        # 檢查分類是否已完成
        if progress.get(category) == "completed":
            print(f"分類 {category} 已完成，跳過")
            continue

        # 選擇分類並點擊搜尋
        dropdown = wait.until(EC.presence_of_element_located((By.ID, "DrugInfoQueryBox_ddlPregnancyFactor")))
        dropdown.click()
        option = driver.find_element(By.XPATH, f"//option[@value='{category}']")
        option.click()
        search_button = driver.find_element(By.ID, "DrugInfoQueryBox_btnQueryByPregnancyFactor")
        search_button.click()
        time.sleep(1)

        # 抓取學名清單
        rows = wait.until(
            EC.presence_of_all_elements_located((By.XPATH, "//table[@id='DrugListBox_grvDrugList']/tbody/tr"))
        )
        if len(rows) <= 1:
            print(f"分類 {category} 沒有有效資料，跳過。")
            progress[category] = "completed"
            save_progress(progress)
            continue

        print(f"找到 {len(rows) - 1} 筆資料")

        for index in range(1, len(rows)):
            try:
                # 確保切回主頁的 iframe
                driver.switch_to.default_content()
                iframe = wait.until(EC.presence_of_element_located((By.XPATH, "//iframe[@title='藥品綜合查詢']")))
                driver.switch_to.frame(iframe)

                rows = wait.until(
                    EC.presence_of_all_elements_located((By.XPATH, "//table[@id='DrugListBox_grvDrugList']/tbody/tr"))
                )
                row = rows[index]

                # 取得學名
                generic_name = row.find_element(By.XPATH, "./td[1]").text.strip()
                safe_generic_name = clean_filename(generic_name)

                # 檢查學名是否已處理
                if progress.get(category, {}).get(safe_generic_name) == "completed":
                    print(f"藥品 {generic_name} 已處理，跳過")
                    continue

                print(f"正在處理藥品：{generic_name}")

                # 處理用藥教育 PDF
                try:
                    education_link = row.find_element(By.XPATH, ".//a[contains(@id, '_lnkEDU')]")
                    education_url = education_link.get_attribute("href")
                    response = requests.get(education_url)
                    if response.status_code == 200:
                        file_path = os.path.join(base_dir, category, "用藥教育", f"{safe_generic_name}.pdf")
                        with open(file_path, "wb") as f:
                            f.write(response.content)
                        print(f"成功下載用藥教育檔案：{file_path}")
                except NoSuchElementException:
                    print(f"用藥教育檔案不存在：{generic_name}")
                except Exception as e:
                    print(f"用藥教育下載失敗：{e}")

                # 處理仿單 PDF
                try:
                    instruction_link = row.find_element(By.XPATH, ".//a[contains(@id, '_lnkInstructions')]")
                    instruction_url = instruction_link.get_attribute("href")
                    response = requests.get(instruction_url)
                    if response.status_code == 200:
                        file_path = os.path.join(base_dir, category, "仿單", f"{safe_generic_name}.pdf")
                        with open(file_path, "wb") as f:
                            f.write(response.content)
                        print(f"成功下載仿單檔案：{file_path}")
                except NoSuchElementException:
                    print(f"仿單檔案不存在：{generic_name}")
                except Exception as e:
                    print(f"仿單下載失敗：{e}")

                # 抓取詳細資料
                try:
                    link = row.find_element(By.XPATH, "./td[1]/a")
                    link.click()
                    driver.switch_to.default_content()
                    new_iframe = wait.until(EC.presence_of_element_located((By.XPATH, "//iframe[@id='MSOPageViewerWebPart_WebPartWPQ3']")))
                    driver.switch_to.frame(new_iframe)

                    table_rows = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//table[@id='DrugInfoDetailBox_dtvDrugInfo']/tbody/tr")))
                    details = {}
                    for tr in table_rows:
                        try:
                            title = tr.find_element(By.CLASS_NAME, "tableTitle").text.strip()
                            content = tr.find_element(By.XPATH, "./td[2]").text.strip()
                            details[title] = content
                        except NoSuchElementException:
                            continue

                    # 儲存詳細資料
                    file_path = os.path.join(base_dir, category, "詳細資料", f"{safe_generic_name}.json")
                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(details, f, ensure_ascii=False, indent=4)
                    print(f"成功儲存詳細資料：{file_path}")
                except Exception as e:
                    print(f"詳細資料處理失敗：{e}")

                # 更新進度
                if category not in progress:
                    progress[category] = {}
                progress[category][safe_generic_name] = "completed"
                save_progress(progress)

                # 返回列表
                driver.switch_to.default_content()
                iframe = wait.until(EC.presence_of_element_located((By.XPATH, "//iframe[@title='藥品綜合查詢']")))
                driver.switch_to.frame(iframe)
                back_button = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@value='回上一頁']")))
                back_button.click()
                time.sleep(random.uniform(1, 2))  # 隨機延遲

            except Exception as e:
                print(f"處理藥品 {generic_name} 時發生錯誤：{e}")
                save_failed_item({"category": category, "generic_name": generic_name, "error": str(e)})

        # 更新分類為完成
        progress[category] = "completed"
        save_progress(progress)

    except Exception as e:
        print(f"處理分類 {category} 時發生錯誤：{e}")
        save_failed_item({"category": category, "error": str(e)})

# 關閉瀏覽器
driver.quit()
