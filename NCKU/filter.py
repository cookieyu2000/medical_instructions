import os
import shutil 
from collections import defaultdict

# 設定資料夾路徑
source_folder = "NCKU/data/downloaded_files"
output_folder = "NCKU/data/filter"

# 確保輸出資料夾存在
os.makedirs(output_folder, exist_ok=True)

# 創建分類的字典
categories = defaultdict(list)

# 遍歷檔案並分類
for filename in os.listdir(source_folder):
    if filename.endswith(".pdf"):  # 確保只處理 PDF 檔案
        # 根據數字前的中文部分進行分類
        category_name = ''.join(filter(str.isalpha, filename.split('第')[0])).strip()
        categories[category_name].append(filename)

# 為每個分類創建資料夾並複製檔案
for category, files in categories.items():
    category_folder = os.path.join(output_folder, category)
    os.makedirs(category_folder, exist_ok=True)
    for file in files:
        source_path = os.path.join(source_folder, file)
        target_path = os.path.join(category_folder, file)
        shutil.copy2(source_path, target_path)

print("檔案分類並複製完成！")
