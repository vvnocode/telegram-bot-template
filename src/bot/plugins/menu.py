"""菜单插件"""
from typing import Dict, List

from telegram import Update
from telegram.ext import ContextTypes

from src.auth import UserManager, UserRole
from src.bot.plugins.interface import PluginInterface, CommandInfo, CommandCategory
from src.logger import logger


class MenuPlugin(PluginInterface):
    """菜单插件，提供命令菜单功能"""
    name = "menu"
    description = "命令菜单插件"
    version = "1.0.0"
    
    def register_commands(self) -> None:
        """注册菜单命令"""
        self.register_command(
            CommandInfo(
                command="menu",
                description="查看所有可用命令及权限",
                handler=self.menu_command,
                category=CommandCategory.MENU,
                required_role=UserRole.USER
            )
        )
        
        self.register_command(
            CommandInfo(
                command="help",
                description="获取帮助信息",
                handler=self.help_command,
                category=CommandCategory.MENU,
                required_role=UserRole.USER
            )
        )
    
    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_manager: UserManager):
        """处理/menu命令，显示所有可用命令及其权限
        
        Args:
            update: Telegram更新对象
            context: 上下文对象
            user_manager: 用户管理器实例
        """
        # 获取用户信息
        user_id = update.effective_user.id
        user_role = user_manager.get_user_role(user_id)
        
        # 如果用户无权限，拒绝访问
        if user_role is None:
            logger.warning(f"未授权的用户 {user_id} 尝试查看菜单")
            await update.message.reply_text("未授权的用户")
            return
        
        logger.info(f"用户 {user_id} 请求查看菜单，角色: {user_role.name}")
        
        # 获取插件加载器
        plugin_loader = context.bot_data.get('plugin_loader')
        
        if not plugin_loader:
            await update.message.reply_text("系统尚未完全初始化，请稍后再试")
            return
        
        # 构建菜单消息
        menu_message = "📋 *所有可用命令*\n\n"
        
        # 收集所有命令并按分类组织
        commands_by_category: Dict[CommandCategory, List[CommandInfo]] = {}
        
        # 从所有插件中收集命令
        for plugin in plugin_loader.get_all_plugins().values():
            for cmd_name, cmd in plugin.commands.items():
                if cmd.category not in commands_by_category:
                    commands_by_category[cmd.category] = []
                
                # 只添加用户有权限的命令
                if (cmd.required_role == UserRole.ADMIN and user_role == UserRole.ADMIN) or \
                   (cmd.required_role == UserRole.USER):
                    commands_by_category[cmd.category].append(cmd)
        
        # 按分类添加到消息中
        for category, commands in commands_by_category.items():
            if commands:
                menu_message += f"*{category.value}*\n"
                
                for cmd in sorted(commands, key=lambda x: x.command):
                    # 确定权限标记
                    if cmd.required_role == UserRole.ADMIN:
                        permission_mark = "👑" 
                    else:
                        permission_mark = "👤"
                        
                    # 添加命令信息，并且转义下划线
                    escaped_cmd = cmd.command.replace('_', '\\_')
                    menu_message += f"{permission_mark} /{escaped_cmd} - {cmd.description}\n"
                
                menu_message += "\n"
        
        # 添加图例
        menu_message += "*图例:*\n"
        menu_message += "👑 - 需要管理员权限\n"
        menu_message += "👤 - 普通用户可用\n"
        
        # 发送菜单消息
        await update.message.reply_text(menu_message, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_manager: UserManager):
        """处理/help命令，显示帮助信息
        
        Args:
            update: Telegram更新对象
            context: 上下文对象
            user_manager: 用户管理器实例
        """
        # 获取用户信息
        user_id = update.effective_user.id
        user_role = user_manager.get_user_role(user_id)
        
        # 如果用户无权限，拒绝访问
        if user_role is None:
            logger.warning(f"未授权的用户 {user_id} 尝试获取帮助")
            await update.message.reply_text("未授权的用户")
            return
        
        logger.info(f"用户 {user_id} 请求帮助，角色: {user_role.name}")
        
        # 获取插件加载器
        plugin_loader = context.bot_data.get('plugin_loader')
        
        if not plugin_loader:
            await update.message.reply_text("系统尚未完全初始化，请稍后再试")
            return
        
        # 生成帮助消息
        help_message = "🤖 *机器人帮助*\n\n"
        help_message += "这是一个多功能Telegram机器人，提供以下插件功能：\n\n"
        
        # 添加已加载的插件信息
        for plugin_name, plugin in plugin_loader.get_all_plugins().items():
            help_message += f"• *{plugin.description}* (v{plugin.version})\n"
        
        help_message += "\n使用 /menu 命令查看所有可用的命令及其详细信息。\n"
        
        # 发送帮助消息
        await update.message.reply_text(help_message, parse_mode='Markdown') 