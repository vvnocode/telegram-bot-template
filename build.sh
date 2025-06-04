#!/bin/bash

# 确保在虚拟环境中运行
if [ -z "$VIRTUAL_ENV" ]; then
    echo "警告: 不在虚拟环境中，尝试激活venv..."
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        echo "错误: 未找到虚拟环境"
        exit 1
    fi
fi

# 安装依赖
pip install -r requirements.txt
pip install pyinstaller

# 使用PyInstaller打包
pyinstaller --onefile \
    --name telegram-bot-template \
    --add-data "config/config.yaml.example:." \
    --add-data "config/commands.yaml.example:." \
    --hidden-import telegram \
    --hidden-import yaml \
    --hidden-import src.push.plugins \
    --paths src \
    src/main.py

# 检查构建是否成功
if [ ! -f "dist/telegram-bot-template" ]; then
    echo "构建失败!"
    exit 1
fi

# 移动生成的文件
mv dist/telegram-bot-template .
chmod +x telegram-bot-template

echo "构建完成! 使用环境: $(python --version) on $(lsb_release -d 2>/dev/null || echo 'Unknown Linux')"