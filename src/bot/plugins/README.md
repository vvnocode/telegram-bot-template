# 插件系统

这个目录包含了机器人的插件系统核心代码和内置插件。

## 插件加载机制

插件系统支持两种方式加载插件：

1. **内置插件**：存放在`src/bot/plugins`目录中的插件，与代码一起打包
2. **外部插件**：存放在以下位置的`plugins`目录中的插件
   - 项目根目录下的`plugins`目录
   - 可执行文件所在目录下的`plugins`目录
   - 当前工作目录下的`plugins`目录

系统会先加载内置插件，然后尝试加载外部插件。如果发现同名插件，将优先使用内置插件。

插件的加载受到配置文件中`plugins`部分的控制：

```yaml
plugins:
  # 启用的插件列表，如果为空，则加载所有未被禁用的插件
  enabled: []
  
  # 禁用的插件列表，这些插件将不会被加载
  disabled: ["ip"]  # 禁用示例
```

加载优先级规则：
1. 禁用列表（disabled）优先级最高，在此列表中的插件不会被加载
2. 启用列表（enabled）优先级次之，仅加载此列表中的插件
3. 若未配置上述两个列表，则加载所有可用插件

## 创建新插件

### 内置插件

要创建一个内置插件，在`src/bot/plugins`目录下创建一个新的Python文件，并实现插件类。

### 外部插件

要创建一个外部插件，在`plugins`目录（可以是项目根目录、可执行文件目录或当前工作目录下的`plugins`子目录）下创建一个新的Python文件。

外部插件的优势是可以在不修改核心代码的情况下扩展机器人功能，甚至可以在机器人运行时添加或移除。

### 插件类模板

无论是内置插件还是外部插件，插件类的结构都是相同的：

```python
from telegram import Update
from telegram.ext import ContextTypes

from src.auth import UserManager, UserRole
from src.bot.plugins.interface import PluginInterface, CommandInfo, CommandCategory
from src.logger import logger


class ExamplePlugin(PluginInterface):
    """示例插件"""
    # 插件元数据
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
        """示例命令处理函数
        
        Args:
            update: Telegram更新对象
            context: 上下文对象
            user_manager: 用户管理器实例
        """
        await update.message.reply_text("这是一个示例命令")
```

### 注意事项

1. `name`属性必须是唯一的，它用于标识插件。如果内置插件和外部插件使用相同的名称，内置插件将被优先使用。
2. `register_commands`方法必须被实现，用于注册插件的命令。
3. 所有命令处理函数都应该接受三个参数：`update`、`context`和`user_manager`。
4. 插件可以定义任意多的命令，只需在`register_commands`方法中注册即可。

## 禁用插件

若要禁用某个插件，可以在配置文件的`plugins.disabled`列表中添加插件的名称（即插件类的`name`属性值）。例如：

```yaml
plugins:
  disabled: ["ip", "example"]  # 禁用IP插件和示例插件
```

## 只启用特定插件

若要只启用特定插件，可以在配置文件的`plugins.enabled`列表中添加要启用的插件名称。例如：

```yaml
plugins:
  enabled: ["menu", "start"]  # 只启用菜单插件和开始插件
```

## 命令分类

命令可以按以下分类组织：

- `CommandCategory.MAIN`: 主菜单
- `CommandCategory.MENU`: 菜单管理
- `CommandCategory.USER`: 用户管理
- `CommandCategory.SYSTEM`: 系统管理
- `CommandCategory.TOOLS`: 实用工具
- `CommandCategory.STATS`: 统计分析

这些分类会在`/menu`命令中显示，帮助用户了解各个命令的用途。 