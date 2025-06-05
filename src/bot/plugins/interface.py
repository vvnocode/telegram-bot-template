"""插件接口定义"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional, Callable, Type, ClassVar, Set

from telegram import Update, BotCommand
from telegram.ext import ContextTypes, CommandHandler, Application

from src.auth import UserManager, UserRole
from src.utils.user_utils import UserUtils


class CommandCategory(Enum):
    """命令分类枚举"""
    MAIN = "主菜单"
    MENU = "菜单管理" 
    USER = "用户管理"
    SYSTEM = "系统管理"
    STATS = "统计分析"
    PUSH = "推送管理"
    TOOLS = "实用工具"

@dataclass
class CommandInfo:
    """命令信息定义"""
    command: str                        # 命令名称（不含/）
    description: str                    # 命令描述
    handler: Callable                   # 命令处理函数
    category: CommandCategory = CommandCategory.MAIN  # 命令分类
    required_role: UserRole = UserRole.USER  # 所需权限
    is_visible: bool = True             # 是否在菜单中可见
    sort: int = 999                     # 排序权重，数字越小越靠前
    
    # 运行时数据，不在配置中加载
    handler_instance: Optional[CommandHandler] = field(default=None, repr=False)


class PluginInterface(ABC):
    """插件接口"""
    # 插件元数据，子类应该覆盖这些属性
    name: ClassVar[str] = "base_plugin"  # 插件名称（唯一标识符）
    description: ClassVar[str] = "基础插件"  # 插件描述
    version: ClassVar[str] = "1.0.0"  # 插件版本
    
    def __init__(self, user_manager: UserManager):
        """初始化插件
        
        Args:
            user_manager: 用户管理器
        """
        self.user_manager = user_manager
        self.commands: Dict[str, CommandInfo] = {}
        self._is_enabled = True
    
    @property
    def is_enabled(self) -> bool:
        """获取插件是否启用"""
        return self._is_enabled
    
    @is_enabled.setter 
    def set_enabled(self, value: bool) -> None:
        """设置插件是否启用"""
        self._is_enabled = value
    
    @abstractmethod
    def register_commands(self) -> None:
        """注册命令到插件"""
        pass
    
    def register_command(self, command_info: CommandInfo) -> None:
        """注册命令到插件
        
        Args:
            command_info: 命令信息
        """
        self.commands[command_info.command] = command_info
    
    def setup(self, app: Application) -> None:
        """设置插件
        
        Args:
            app: Telegram应用实例
        """
        if not self.is_enabled:
            return
        
        # 注册命令
        self.register_commands()
        
        # 创建并注册命令处理器
        for command_name, command_info in self.commands.items():
            # 创建命令处理器
            handler = CommandHandler(
                command_name, 
                self._create_command_handler(command_info)
            )
            command_info.handler_instance = handler
            
            # 注册到应用
            app.add_handler(handler)
    
    def _create_command_handler(self, command_info: CommandInfo) -> Callable:
        """创建命令处理函数的包装器
        
        Args:
            command_info: 命令信息
        
        Returns:
            包装后的命令处理函数
        """
        async def handler_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """命令处理函数包装器"""
            # 更新用户缓存信息
            UserUtils.update_user_cache_from_update(update)
            
            # 检查用户权限
            if not await self.user_manager.check_permission(update, command_info.required_role):
                role_name = command_info.required_role.name.lower()
                await update.message.reply_text(
                    f"⚠️ 权限不足。",
                    parse_mode='Markdown'
                )
                return
                
            # 获取统计管理器（如果存在）
            stats_manager = context.bot_data.get('stats_manager')
            
            # 记录命令使用情况
            if stats_manager:
                user_id = str(update.effective_user.id)
                stats_manager.record_command_usage(user_id, command_info.command)
                
            # 调用实际处理函数
            await command_info.handler(update, context, self.user_manager)
            
        return handler_wrapper
    
    def get_bot_commands(self) -> List[BotCommand]:
        """获取插件的机器人命令列表
        
        Returns:
            命令列表
        """
        return [
            BotCommand(cmd.command, cmd.description)
            for cmd in self.commands.values()
            if cmd.is_visible
        ] 