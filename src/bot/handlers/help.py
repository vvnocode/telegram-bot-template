from telegram import Update
from telegram.ext import ContextTypes

from src.auth import UserManager, UserRole
from src.logger import logger
from src.bot.handlers.command import CommandPlugin, CommandCategory, CommandRegistry

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE, user_manager: UserManager):
    """处理/help命令
    
    Args:
        update: Telegram更新对象
        context: 上下文对象
        user_manager: 用户管理器实例
    """
    # 获取用户信息
    user_id = update.effective_user.id
    user_name = update.effective_user.username
    
    # 获取用户角色
    user_role = user_manager.get_user_role(user_id)
    
    # 如果用户无权限，拒绝访问
    if user_role is None:
        logger.warning(f"未授权的用户尝试访问帮助，用户ID: {user_id}，用户名: {user_name}")
        await update.message.reply_text("未授权的用户")
        return
    
    logger.info(f"用户请求帮助，用户ID: {user_id}，用户名: {user_name}，角色: {user_role.name}")
    
    # 获取命令注册表
    command_registry = context.bot_data.get('command_registry')
    
    if not command_registry:
        # 如果命令注册表不可用，显示基础帮助
        await update.message.reply_text(
            text="系统尚未完全初始化，请稍后再试。\n"
                 "基本命令：\n"
                 "/start - 开始使用机器人\n"
                 "/help - 显示帮助信息"
        )
        return
    
    # 获取用户可用的命令
    available_commands = command_registry.get_available_commands(user_role)
    
    # 构建帮助消息
    help_message = "📋 *可用命令列表*\n\n"
    
    # 按分类显示命令
    for category, commands in available_commands.items():
        if commands:
            help_message += f"*{category.value}*\n"
            
            for cmd in commands:
                help_message += f"/{cmd.command} - {cmd.description}\n"
            
            help_message += "\n"
    
    # 添加提示信息
    help_message += "_提示: 使用 /start 命令可以显示菜单按钮_"
    
    # 发送帮助消息
    await update.message.reply_text(help_message, parse_mode='Markdown')

def register_help_command(command_registry: CommandRegistry):
    """注册help命令
    
    Args:
        command_registry: 命令注册器实例
    """
    command_registry.register_command(
        CommandPlugin(
            command="help",
            description="显示帮助信息",
            handler=help_command,
            category=CommandCategory.MAIN,
            required_role=UserRole.USER
        )
    ) 