from flask import Flask, render_template, send_from_directory, abort, request, jsonify, send_file
import os
import yaml
import zipfile
from io import BytesIO

app = Flask(__name__)

# 配置檔案路徑
CONFIG_PATH = "config.yaml"

# 加載 YAML 配置檔案
def load_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"配置檔案加載失敗: {e}")
        return {}

# 更新 YAML 配置檔案
def save_config(config):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            yaml.safe_dump(config, f, allow_unicode=True, indent=4)
    except Exception as e:
        print(f"配置檔案保存失敗: {e}")

# 動態渲染頁面
@app.route("/")
def index():
    config = load_config()
    data = {}
    for key, value in config.items():
        folder = value.get("folder")
        if not os.path.exists(folder):
            data[key] = {"error": f"{folder} 資料夾不存在"}
        else:
            files = [f for f in os.listdir(folder) if f.endswith(".zip")]
            folders = [f for f in os.listdir(folder) if os.path.isdir(os.path.join(folder, f))]
            data[key] = {"files": files, "folders": folders, "all_zip": value.get("all_zip")}
    return render_template("index.html", data=data)

# 動態文件下載
@app.route("/download/<category>/<filename>")
def download_file(category, filename):
    config = load_config()
    if category not in config:
        abort(404, description="分類未找到")
    folder = config[category].get("folder")
    file_path = os.path.join(folder, filename)
    if not os.path.exists(file_path):
        abort(404, description="檔案未找到")
    return send_from_directory(folder, filename, as_attachment=True)

# 下載所有壓縮包
@app.route("/download/<category>/all")
def download_all(category):
    config = load_config()
    if category not in config:
        abort(404, description="分類未找到")
    all_zip = config[category].get("all_zip")
    if not os.path.exists(all_zip):
        abort(404, description="壓縮檔案未找到")
    return send_from_directory(os.path.dirname(all_zip), os.path.basename(all_zip), as_attachment=True)

# 動態壓縮資料夾並提供下載
@app.route("/download_folder/<category>/<folder_name>")
def download_folder(category, folder_name):
    config = load_config()
    if category not in config:
        abort(404, description="分類未找到")
    folder_path = os.path.join(config[category].get("folder"), folder_name)
    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        abort(404, description="資料夾未找到")

    # 創建壓縮檔案到內存中
    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, folder_path)
                zf.write(abs_path, rel_path)
    memory_file.seek(0)

    # 提供壓縮檔案作為下載
    return send_file(memory_file, as_attachment=True, download_name=f"{folder_name}.zip")

# 後台 API: 新增資料路徑
@app.route("/admin/add_category", methods=["POST"])
def add_category():
    config = load_config()
    data = request.json
    category = data.get("category")
    folder = data.get("folder")
    all_zip = data.get("all_zip")
    if not category or not folder or not all_zip:
        return jsonify({"error": "缺少必要參數"}), 400
    if category in config:
        return jsonify({"error": "分類已存在"}), 400
    config[category] = {"folder": folder, "all_zip": all_zip}
    save_config(config)
    return jsonify({"message": f"分類 {category} 已新增成功"}), 200

# 後台 API: 更新資料路徑
@app.route("/admin/update_category", methods=["PUT"])
def update_category():
    config = load_config()
    data = request.json
    category = data.get("category")
    folder = data.get("folder")
    all_zip = data.get("all_zip")
    if not category or not folder or not all_zip:
        return jsonify({"error": "缺少必要參數"}), 400
    if category not in config:
        return jsonify({"error": "分類不存在"}), 400
    config[category] = {"folder": folder, "all_zip": all_zip}
    save_config(config)
    return jsonify({"message": f"分類 {category} 已更新成功"}), 200

# 後台 API: 刪除資料路徑
@app.route("/admin/delete_category", methods=["DELETE"])
def delete_category():
    config = load_config()
    data = request.json
    category = data.get("category")
    if not category:
        return jsonify({"error": "缺少分類參數"}), 400
    if category not in config:
        return jsonify({"error": "分類不存在"}), 400
    del config[category]
    save_config(config)
    return jsonify({"message": f"分類 {category} 已刪除成功"}), 200

if __name__ == "__main__":
    app.run(debug=True, host="10.22.24.176", port=3000)
