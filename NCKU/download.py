import pandas as pd
import requests
import os
import time
from tqdm import tqdm
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

csv_path = 'NCKU/data/仿單圖檔連結.csv'
download_dir = 'NCKU/data/downloaded_files'
log_file_path = 'NCKU/data/download_log.txt'

if not os.path.exists(download_dir):
    os.makedirs(download_dir)

# 設定 headers，模擬瀏覽器行為
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

# 設定重試機制
session = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504, 429])
session.mount('https://', HTTPAdapter(max_retries=retries))

def download_file(permit_number, file_link):
    file_name = f"{permit_number}.pdf"
    file_path = os.path.join(download_dir, file_name)

    try:
        print(f"嘗試下載 {permit_number} 從 {file_link}")
        response = session.get(file_link, headers=headers, timeout=10)
        response.raise_for_status()
        
        with open(file_path, 'wb') as file:
            file.write(response.content)
        print(f"下載完成: {file_name}")
        return True
    except requests.exceptions.RequestException as e:
        error_message = f"下載失敗: {file_name}，錯誤: {e}"
        print(error_message)
        with open(log_file_path, 'a', encoding='utf-8') as log_file:
            log_file.write(error_message + '\n')
        return False

data = pd.read_csv(csv_path)

downloaded_files = set(f.split(".pdf")[0] for f in os.listdir(download_dir) if f.endswith(".pdf"))

# 篩選出尚未下載的檔案
data_to_download = data[~data['許可證字號'].isin(downloaded_files)]

# 清空舊的 log 檔案
open(log_file_path, 'w').close()

# 開始下載尚未下載的檔案
print("開始下載尚未下載的檔案...")
for index, row in tqdm(data_to_download.iterrows(), total=len(data_to_download), desc="下載進度"):
    permit_number = row['許可證字號']
    file_link = row['仿單圖檔連結']
    
    # 檢查空連結並記錄到日誌
    if pd.isna(file_link):
        error_message = f"{permit_number} 的連結為空，跳過"
        print(error_message)
        with open(log_file_path, 'a', encoding='utf-8') as log_file:
            log_file.write(error_message + '\n')
        continue

    # 嘗試下載檔案
    download_file(permit_number, file_link)
    time.sleep(0.5)  # 增加延遲，避免頻繁訪問

# 重新下載錯誤的檔案
with open(log_file_path, 'r', encoding='utf-8') as log_file:
    errors = log_file.readlines()

# 如果有錯誤記錄，重新嘗試下載
if errors:
    print("重新嘗試下載失敗的檔案...")
    open(log_file_path, 'w').close()  # 清空 log 檔案
    for error in tqdm(errors, desc="重新下載進度"):
        try:
            # 嘗試從錯誤訊息中解析出 permit_number 和 file_link
            permit_number = error.split(': ')[1].split('，')[0]
            file_link = data[data['許可證字號'] == permit_number]['仿單圖檔連結'].values
            if len(file_link) == 0:
                raise ValueError(f"找不到對應的連結: {permit_number}")
            file_link = file_link[0]
            
            # 檢查空連結並記錄到日誌
            if pd.isna(file_link):
                error_message = f"{permit_number} 的連結為空，跳過"
                print(error_message)
                with open(log_file_path, 'a', encoding='utf-8') as log_file:
                    log_file.write(error_message + '\n')
                continue

            download_file(permit_number, file_link)
            time.sleep(0.5)  # 增加延遲以減少伺服器壓力
        except Exception as e:
            # 如果解析或下載時出現問題，記錄到日誌
            error_message = f"重新下載失敗: {error.strip()}，錯誤: {e}"
            print(error_message)
            with open(log_file_path, 'a', encoding='utf-8') as log_file:
                log_file.write(error_message + '\n')
