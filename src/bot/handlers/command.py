from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Callable, Dict, Any
import yaml
import os

from telegram import Update, BotCommand
from telegram.ext import ContextTypes, CommandHandler, Application
from telegram.constants import BotCommandScopeType

from src.auth import UserManager, UserRole
from src.logger import logger

class CommandCategory(Enum):
    """命令分类枚举"""
    MAIN = "主菜单"
    MENU = "菜单管理"
    USER = "用户管理"
    SYSTEM = "系统管理"
    TOOLS = "实用工具"

@dataclass
class CommandPlugin:
    """命令插件定义"""
    command: str                        # 命令名称（不含/）
    description: str                    # 命令描述
    handler: Callable                   # 命令处理函数
    category: CommandCategory = CommandCategory.MAIN  # 命令分类
    required_role: UserRole = UserRole.USER  # 所需权限
    is_visible: bool = True             # 是否在菜单中可见
    
    # 运行时数据，不在配置中加载
    handler_instance: Optional[CommandHandler] = field(default=None, repr=False)

class CommandRegistry:
    """命令注册表"""
    def __init__(self, user_manager: UserManager):
        self.user_manager = user_manager
        self.commands: Dict[str, CommandPlugin] = {}
        self.application: Optional[Application] = None
    
    def register_command(self, command_plugin: CommandPlugin) -> None:
        """注册命令"""
        self.commands[command_plugin.command] = command_plugin
        
    def load_commands_from_config(self, config_path: str) -> None:
        """从配置文件加载命令配置"""
        if not os.path.exists(config_path):
            logger.warning(f"命令配置文件 {config_path} 不存在，使用默认配置")
            return
            
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
                
            if not config_data or not isinstance(config_data, dict):
                logger.warning("命令配置文件格式不正确，使用默认配置")
                return
                
            commands_config = config_data.get('commands', {})
            
            # 更新已注册命令的配置
            for cmd_name, cmd_config in commands_config.items():
                if cmd_name in self.commands:
                    cmd = self.commands[cmd_name]
                    
                    # 更新描述
                    if 'description' in cmd_config:
                        cmd.description = cmd_config['description']
                        
                    # 更新分类
                    if 'category' in cmd_config:
                        try:
                            cmd.category = CommandCategory[cmd_config['category'].upper()]
                        except (KeyError, AttributeError):
                            logger.warning(f"命令 {cmd_name} 的分类配置不正确: {cmd_config['category']}")
                    
                    # 更新所需角色
                    if 'required_role' in cmd_config:
                        try:
                            cmd.required_role = UserRole[cmd_config['required_role'].upper()]
                        except (KeyError, AttributeError):
                            logger.warning(f"命令 {cmd_name} 的角色配置不正确: {cmd_config['required_role']}")
                    
                    # 更新可见性
                    if 'is_visible' in cmd_config:
                        cmd.is_visible = bool(cmd_config['is_visible'])
                        
                else:
                    logger.warning(f"配置文件中的命令 {cmd_name} 未在代码中注册")
                    
        except Exception as e:
            logger.error(f"加载命令配置文件出错: {str(e)}", exc_info=True)
    
    def setup_command_handlers(self, application: Application) -> None:
        """设置所有命令处理器"""
        self.application = application
        
        # 注册所有命令处理器
        for cmd_name, cmd in self.commands.items():
            handler = CommandHandler(
                cmd_name,
                lambda update, context, cmd=cmd: self._handle_command(update, context, cmd)
            )
            cmd.handler_instance = handler
            application.add_handler(handler)
            
        logger.info(f"已注册 {len(self.commands)} 个命令处理器")
    
    async def _handle_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, cmd: CommandPlugin) -> None:
        """通用命令处理函数"""
        # 检查用户权限
        user_role = self.user_manager.get_user_role(update.effective_user.id)
        
        # 记录命令请求
        logger.info(f"用户 {update.effective_user.id} ({update.effective_user.username}) 请求执行命令 /{cmd.command}")
        
        # 如果用户无权限，拒绝访问
        if user_role is None:
            logger.warning(f"未授权用户 {update.effective_user.id} 尝试执行命令 /{cmd.command}")
            await update.message.reply_text("未授权的用户")
            return
        
        # 检查用户是否有执行此命令的权限
        if cmd.required_role == UserRole.ADMIN and user_role != UserRole.ADMIN:
            logger.warning(f"普通用户 {update.effective_user.id} 尝试执行管理员命令 /{cmd.command}")
            await update.message.reply_text("此命令需要管理员权限")
            return
            
        # 执行命令处理函数
        await cmd.handler(update, context, self.user_manager)
    
    async def setup_bot_commands(self) -> None:
        """设置机器人命令列表，使其显示在左下角菜单中"""
        if not self.application or not self.application.bot:
            logger.error("尝试设置机器人命令列表，但应用程序或机器人尚未初始化")
            return
            
        # 收集所有可见命令
        visible_commands = []
        for cmd in self.commands.values():
            if cmd.is_visible:
                visible_commands.append(BotCommand(cmd.command, cmd.description))
        
        if not visible_commands:
            logger.warning("没有可见命令可设置")
            return
            
        # 设置命令菜单 - 将所有命令设置为全局命令
        try:
            scope = None  # 全局范围
            language_code = "zh"  # 中文
            
            await self.application.bot.set_my_commands(
                commands=visible_commands,
                scope=scope,
                language_code=language_code
            )
                
            logger.info(f"成功设置机器人命令菜单，共 {len(visible_commands)} 个命令")
        except Exception as e:
            logger.error(f"设置机器人命令菜单失败: {str(e)}", exc_info=True)
    
    def get_available_commands(self, user_role: UserRole) -> Dict[CommandCategory, List[CommandPlugin]]:
        """获取用户可用的命令列表"""
        result: Dict[CommandCategory, List[CommandPlugin]] = {}
        
        for cmd in self.commands.values():
            # 检查用户权限和命令可见性
            if not cmd.is_visible:
                continue
                
            if cmd.required_role == UserRole.ADMIN and user_role != UserRole.ADMIN:
                continue
                
            if cmd.category not in result:
                result[cmd.category] = []
                
            result[cmd.category].append(cmd)
            
        return result 