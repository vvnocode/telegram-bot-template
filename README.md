# telegram-bot-template
一个功能完善的Telegram机器人模板。集成actions自动构建，一键安装脚本，插件式命令系统，用户权限管理。

## 功能特点

- 📦 **插件式命令系统** - 轻松添加新命令，无需修改核心代码
- 👤 **用户权限管理** - 管理员和普通用户权限分离
- 🔄 **自动注册命令** - 符合命名规范的命令自动被发现和注册
- 📋 **命令菜单管理** - 可查看所有可用命令及其权限
- 👑 **用户管理功能** - 管理员可添加/删除普通用户和其他管理员
- 🔌 **动态插件加载** - 支持从内部和外部目录加载插件
- ⚙️ **配置文件支持** - 通过YAML配置文件控制插件的启用与禁用
- 🖥️ **系统状态监控** - 查看机器人运行状态、系统资源使用情况
- 🔧 **简单易用的API** - 清晰的接口设计，便于扩展

## 使用

### 使用install.sh安装(推荐)

1. 运行一键安装脚本
```bash
bash <(curl -L -s https://raw.githubusercontent.com/vvnocode/telegram-bot-template/main/install.sh)
```
2. 根据提示输入Telegram Bot Token和Chat ID

### 手动修改配置文件

安装完成后可以手动修改配置文件，修改完成后需要重启服务：`systemctl restart telegram-bot-template`

配置文件位于 `/opt/telegram-bot-template/config.yaml`，示例：
```yaml
# Telegram配置
telegram_bot_token: ""               # 你的Telegram Bot Token
telegram_admin_id: ""  # 管理员用户ID, 多个用户ID用逗号分隔
telegram_user_id: ""     # 授权的普通用户ID, 多个用户ID用逗号分隔

# 插件配置
plugins:
  # 启用的插件列表，如果为空，则加载所有未被禁用的插件
  enabled: []
  
  # 禁用的插件列表，这些插件将不会被加载
  disabled: ["ip"]  # 禁用示例
```

### Telegram Bot 命令

- `/start` - 机器人使用入口
- `/help` - 显示帮助信息
- `/menu` - 查看所有可用命令及权限
- `/users` - 查看所有用户列表(需管理员权限)
- `/adduser` - 添加普通用户(需管理员权限)
- `/deluser` - 删除普通用户(需管理员权限)
- `/status` - 查看系统状态(需管理员权限)
- `/get_ip` - 查看当前IP地址
- `/stats_total` - 显示所有命令的总体使用统计(需管理员权限)
- `/stats_today` - 显示所有命令的今日使用统计(需管理员权限)
- `/stats_users_total` - 显示所有用户的各菜单使用详情统计(需管理员权限)
- `/stats_users_today` - 显示所有用户的今日各菜单使用详情(需管理员权限)
- `/stats_user` - 显示指定用户的统计信息(需管理员权限)

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

## 项目结构

```
telegram-bot-template/
├── config/                   # 配置目录
│   ├── config.yaml           # 主配置文件
│   └── commands.yaml         # 命令配置文件
├── src/                      # 源代码目录
│   ├── __init__.py           # 初始化文件
│   ├── main.py               # 程序入口点
│   ├── config.py             # 配置加载
│   ├── logger.py             # 日志配置
│   ├── bot/                  # 机器人核心功能
│   │   ├── __init__.py
│   │   ├── core.py           # Bot核心类
│   │   ├── plugins/          # 插件系统
│   │   │   ├── __init__.py
│   │   │   ├── interface.py  # 插件接口定义
│   │   │   ├── loader.py     # 插件加载器
│   │   │   ├── menu.py       # 菜单插件
│   │   │   ├── start.py      # 启动插件
│   │   │   ├── user.py       # 用户管理插件
│   │   │   ├── stats.py      # 统计插件
│   │   │   ├── ip.py         # IP工具插件
│   │   │   └── README.md     # 插件开发文档
│   │   └── utils/            # 机器人工具函数
│   │       ├── __init__.py
│   │       └── message_helper.py # 消息处理助手
│   ├── auth/                 # 用户认证模块
│   │   ├── __init__.py
│   │   ├── permissions.py    # 权限定义
│   │   └── user.py           # 用户管理
│   └── utils/                # 工具函数
│       ├── __init__.py
│       └── stats.py          # 统计管理
└── requirements.txt          # 依赖列表
```

## 用户权限管理

本机器人实现了完善的用户权限管理机制，分为两种角色：

1. **普通用户**：可以访问基本命令，如`/start`、`/help`和`/menu`
2. **管理员**：除了普通用户的权限外，还可以访问管理命令，如`/status`和用户管理命令

### 添加或删除用户

管理员可以使用以下命令管理用户：

- `/users` - 查看所有用户和管理员列表
- `/adduser <用户ID>` - 添加普通用户（也可转发用户消息后回复此命令）
- `/deluser <用户ID>` - 删除普通用户

### 配置权限

在配置文件`config.yaml`中设置用户ID：

```yaml
# 普通用户ID列表，用逗号分隔
telegram_user_id: "USER_ID_1,USER_ID_2"

# 管理员ID列表，用逗号分隔
telegram_admin_id: "ADMIN_ID_1,ADMIN_ID_2"
```

## 插件系统

本机器人采用全新的插件系统，支持动态加载内部和外部插件：

### 插件加载机制

插件系统支持两种方式加载插件：

1. **内置插件**：存放在`src/bot/plugins`目录中的插件，与代码一起打包
2. **外部插件**：存放在以下位置的`plugins`目录中的插件
   - 项目根目录下的`plugins`目录
   - 可执行文件所在目录下的`plugins`目录 (`/opt/telegram-bot-template/plugins`)
   - 当前工作目录下的`plugins`目录

系统会先加载内置插件，然后尝试加载外部插件。如果发现同名插件，将优先使用内置插件。

### 插件配置

在`config.yaml`中可以控制插件的加载：

```yaml
plugins:
  # 启用的插件列表，如果为空，则加载所有未被禁用的插件
  enabled: ["menu", "start"]  # 只启用这些插件
  
  # 禁用的插件列表，这些插件将不会被加载
  disabled: ["ip"]  # 禁用IP插件
```

加载优先级规则：
1. 禁用列表（disabled）优先级最高，在此列表中的插件不会被加载
2. 启用列表（enabled）优先级次之，仅加载此列表中的插件
3. 若未配置上述两个列表，则加载所有可用插件

### 添加新插件

#### 内置插件

1. 在`src/bot/plugins`目录下创建新的Python文件
2. 创建一个继承自`PluginInterface`的插件类
3. 实现必要的方法，特别是`register_commands`

#### 外部插件

1. 在`/opt/telegram-bot-template/plugins`目录下创建新的Python文件
2. 创建一个继承自`PluginInterface`的插件类
3. 实现必要的方法，特别是`register_commands`

#### 插件类模板

```python
from telegram import Update
from telegram.ext import ContextTypes

from src.auth import UserManager, UserRole
from src.bot.plugins.interface import PluginInterface, CommandInfo, CommandCategory
from src.logger import logger

class ExamplePlugin(PluginInterface):
    """示例插件"""
    name = "example"  # 插件名称（唯一标识符）
    description = "示例插件"  # 插件描述
    version = "1.0.0"  # 插件版本
    
    def register_commands(self) -> None:
        """注册命令到插件"""
        self.register_command(
            CommandInfo(
                command="example",  # 命令名称（不含/）
                description="示例命令",  # 命令描述
                handler=self.example_command,  # 命令处理函数
                category=CommandCategory.TOOLS,  # 命令分类
                required_role=UserRole.USER  # 所需权限级别
            )
        )
    
    async def example_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_manager: UserManager):
        """示例命令处理函数"""
        await update.message.reply_text("这是一个示例命令")
```

### 命令分类

命令可以按以下分类组织：

- `CommandCategory.MAIN`: 主菜单
- `CommandCategory.MENU`: 菜单管理
- `CommandCategory.USER`: 用户管理
- `CommandCategory.SYSTEM`: 系统管理
- `CommandCategory.TOOLS`: 实用工具
- `CommandCategory.STATS`: 统计分析

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

### 3. 如何添加用户？
有两种方式：
1. 通过用户ID添加: `/adduser <用户ID>`

### 4. 如何开发新的插件？
1. 在`/opt/telegram-bot-template/plugins`目录下创建新的Python文件
2. 参考插件类模板创建自己的插件
3. 实现`register_commands`方法注册命令
4. 重启机器人：`systemctl restart telegram-bot-template`

## 效果展示

### 普通用户界面
![普通用户界面](img/user.png)

### 管理员界面
![管理员界面](img/admin.png)

### 菜单管理
![](img/menu.jpg)

## 贡献指南
欢迎提交 Pull Request 或 Issue 来帮助改进项目。

## 许可证
MIT License