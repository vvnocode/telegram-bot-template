# telegram-bot-template
A Telegram Bot template. 一个Telegram机器人模板。集成actions自动构建，一键安装脚本。

## 使用

### 使用install.sh安装(推荐)

1. 运行一键安装脚本
```bash
bash <(curl -L -s https://raw.githubusercontent.com/vvnocode/telegram-bot-template/main/install.sh)
```
2. 根据提示输入Telegram Bot Token和Chat ID

### 手动修改配置文件

安装完成后可以手动修改配置文件，修改完成后需要重启服务：`systemctl restart telegram-bot-template`

配置文件位于 `/etc/telegram-bot-template/config.yaml`，示例：
```yaml
# Telegram配置
telegram_bot_token: ""  # 你的Telegram Bot Token
telegram_user_id: ""    # 授权的Telegram用户ID, 多个用户ID用逗号分隔
```

### Telegram Bot 命令

- `/start` - 显示帮助信息

### 服务管理

```bash
# 启动服务
systemctl start telegram-bot-template
# 停止服务
systemctl stop telegram-bot-template
# 重启服务
systemctl restart telegram-bot-template
# 查看服务状态
systemctl status telegram-bot-template
```

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
python src/main.py
```

## 自动构建

1. 支持打tag后，使用actions自动构建。
2. 未使用全局Token，需要自己创建 [tokens](https://github.com/settings/tokens)。
3. 需要配置MY_GITHUB_TOKEN
    路径：Project - Settins -> Security -> Secrets and variables -> Repository secrets
    参数：MY_GITHUB_TOKEN
    值为步骤2的token

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

## 项目结构

```
telegram-bot-template/
├── src/                      # 源代码目录
│   ├── __init__.py           # 初始化文件
│   ├── main.py               # 程序入口点
│   ├── config.py             # 配置加载
│   ├── logger.py             # 日志配置
│   ├── bot/                  # 机器人核心功能
│   │   ├── __init__.py
│   │   ├── core.py           # Bot核心类
│   │   └── handlers/         # 命令处理器
│   │       ├── __init__.py
│   │       ├── start.py      # /start命令处理
│   │       ├── help.py       # /help命令处理
│   │       ├── admin.py      # /admin命令处理
│   │       └── status.py     # /status命令处理
│   ├── auth/                 # 用户认证模块
│   │   ├── __init__.py
│   │   ├── permissions.py    # 权限定义
│   │   └── user.py           # 用户管理
│   └── utils/                # 工具函数
│       ├── __init__.py
│       └── helpers.py
├── config.yaml               # 配置文件
├── config.yaml.example       # 配置示例
└── requirements.txt          # 依赖列表
```

## 用户权限管理

本模板实现了简单的用户权限管理机制，分为两种角色：

1. **普通用户**：可以访问基本命令，如`/start`和`/help`
2. **管理员**：除了普通用户的权限外，还可以访问管理命令，如`/admin`和`/status`

### 效果展示

#### 普通用户界面
![普通用户界面](img/user.png)

#### 管理员界面
![管理员界面](img/admin.png)

### 配置权限

在配置文件`config.yaml`中设置用户ID：

```yaml
# 普通用户ID列表，用逗号分隔
telegram_user_id: "USER_ID_1,USER_ID_2"

# 管理员ID列表，用逗号分隔
telegram_admin_id: "ADMIN_ID_1,ADMIN_ID_2"
```

### 扩展命令

如果您想添加新的命令处理器，请遵循以下步骤：

1. 在`src/bot/handlers/`目录下创建新的处理器文件
2. 参考现有处理器实现命令逻辑
3. 在`src/bot/handlers/__init__.py`中注册新的处理器

示例：
```python
# 在新的命令处理文件中
def register_new_command_handler(application, user_manager: UserManager):
    application.add_handler(
        CommandHandler(
            "command_name", 
            lambda update, context: command_function(update, context, user_manager)
        )
    )

# 在__init__.py中添加
from .new_command import register_new_command_handler
# ...
register_new_command_handler(app, user_manager)
```