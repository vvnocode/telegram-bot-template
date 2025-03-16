# telegram-bot-template
A Telegram Bot template. 一个Telegram机器人模板。

## 开发

1. 克隆项目:
```shell
git clone https://github.com/vvnocode/telegram-bot-template.git
cd telegram-bot-template
```

2. 创建并激活虚拟环境:
```shell
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows
```

3. 安装依赖:
```shell
pip install -r requirements.txt
```

4. 本地开发运行:
```shell
python src/bot.py
```

## 自动构建

支持打tag后，使用actions自动构建。
需要配置项目secrets
路径：Project - Settins -> Security -> Secrets and variables -> Repository secrets
参数：MY_GITHUB_TOKEN

## 常见问题

### 1. 如何获取 Telegram Bot Token？
1. 在 Telegram 中找到 @BotFather
2. 发送 `/newbot` 命令
3. 按照提示设置 bot 名称
4. 获取 bot token

### 2. 如何获取 Chat ID？
1. 在 Telegram 中找到 @userinfobot
2. 发送任意消息
3. 机器人会返回你的 Chat ID

## 贡献指南
欢迎提交 Pull Request 或 Issue 来帮助改进项目。

## 许可证
MIT License