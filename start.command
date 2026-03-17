#!/bin/bash
cd "$(dirname "$0")"

# 检查 python3 是否可用
if ! command -v python3 &> /dev/null; then
    echo "❌ python3 not found. Please install Python from:"
    echo "   https://www.python.org/downloads/"
    echo ""
    echo "Press any key to close..."
    read -n 1
    exit 1
fi

# 检查 tkinter 是否可用（brew Python 不自带）
if ! python3 -c "import tkinter" &> /dev/null; then
    echo "❌ tkinter not found. Your Python is missing tkinter (common with brew Python)."
    echo ""
    echo "   Please install the official Python from:"
    echo "   https://www.python.org/downloads/"
    echo ""
    echo "   Then delete the venv folder and re-run this script."
    echo ""
    echo "Press any key to close..."
    read -n 1
    exit 1
fi

# 检查 ffmpeg 是否可用
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ ffmpeg not found. Please install ffmpeg first:"
    echo "   brew install ffmpeg"
    echo ""
    echo "Press any key to close..."
    read -n 1
    exit 1
fi

# 检查 SSL 证书（python.org 安装的 Python 需要手动装证书）
PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
CERT_CMD="/Applications/Python ${PY_VER}/Install Certificates.command"
SSL_DIR="/Library/Frameworks/Python.framework/Versions/${PY_VER}/etc/openssl"
if [ -f "$CERT_CMD" ] && [ ! -f "$SSL_DIR/cert.pem" ]; then
    echo "🔐 Installing SSL certificates for Python ${PY_VER}..."
    "$CERT_CMD"
fi

# 没有 venv 就自动创建 + 装依赖
if [ ! -d "venv" ]; then
    echo "📦 First run — setting up virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

echo "🚀 Starting pureWhisper..."
python3 whisper_app.py
