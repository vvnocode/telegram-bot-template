#!/bin/bash

# 安装依赖
pip install -r requirements.txt
pip install pyinstaller

# 使用PyInstaller打包
pyinstaller --onefile \
    --name telegram-bot-template \
    --add-data "config.yaml.example:." \
    --hidden-import telegram \
    --hidden-import yaml \
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