import os
import zipfile

# 設定分類好的資料夾路徑
classified_folder = "NCKU/data/filter"
output_folder = "NCKU/data/zip"

# 確保輸出資料夾存在
os.makedirs(output_folder, exist_ok=True)

# 遍歷分類資料夾中的所有子資料夾
for folder_name in os.listdir(classified_folder):
    folder_path = os.path.join(classified_folder, folder_name)
    
    if os.path.isdir(folder_path):  # 確保是資料夾
        # 壓縮檔案的輸出路徑
        zip_path = os.path.join(output_folder, f"{folder_name}.zip")
        
        # 創建壓縮檔
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    # 添加檔案到壓縮檔，並保留相對路徑
                    arcname = os.path.relpath(file_path, start=folder_path)
                    zipf.write(file_path, arcname)
        
        print(f"壓縮完成：{folder_name}.zip")

print("所有資料夾已壓縮完成！")
