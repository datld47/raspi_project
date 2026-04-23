#!/bin/bash

# ==========================================
# CẤU HÌNH ĐƯỜNG DẪN TỔNG
# ==========================================
# (Khai báo đường dẫn tuyệt đối giúp script chạy ổn định dù gọi từ thư mục nào)
PROJECT_DIR="/home/dat/hoang_project/raspi_project"
VENV_PATH="/home/dat/hoang_project/raspi_project/hoangenv/bin/activate"

# Thư mục chứa các module/thư viện của bạn (nếu có)
AD7606_DIR="/home/dat/hoang_project/raspi_project/project_ad7606"

# File python chính cần chạy
MAIN_SCRIPT="/home/dat/hoang_project/raspi_project/project_ad7606/main_app.py"

# ==========================================
# THỰC THI
# ==========================================

echo "======================================"
echo "[1] Đang kích hoạt môi trường ảo (myenv)..."
source "$VENV_PATH"

echo "[2] Chuyển đến thư mục gốc của dự án..."
cd "$PROJECT_DIR"
# (Nếu code của bạn bắt buộc phải đứng ở thư mục project_ad7606 để chạy thì đổi thành: cd "$AD7606_DIR")

echo "[3] Đang khởi động chương trình thu thập dữ liệu..."
echo "======================================"

# Chạy file Python
python3 "$MAIN_SCRIPT"

# Lệnh này sẽ chạy sau khi bạn tắt file Python (Ctrl+C)
echo "[4] Đã thoát chương trình. Tắt môi trường ảo..."
deactivate