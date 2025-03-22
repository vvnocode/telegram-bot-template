from telegram import Update
from telegram.ext import ContextTypes

from src.auth import UserManager, UserRole
from src.logger import logger
from src.bot.handlers.command import CommandPlugin, CommandCategory, CommandRegistry

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE, user_manager: UserManager):
    """处理/start命令
    
    Args:
        update: Telegram更新对象
        context: 上下文对象
        user_manager: 用户管理器实例
    """
    # 获取用户信息
    user_id = update.effective_user.id
    user_name = update.effective_user.username
    full_name = update.effective_user.full_name
    
    # 获取用户角色
    user_role = user_manager.get_user_role(user_id)
    
    # 如果用户无权限，拒绝访问
    if user_role is None:
        logger.warning(f"未授权的用户尝试访问，用户ID: {user_id}，用户名: {user_name}，全名: {full_name}")
        await update.message.reply_text("未授权的用户")
        return
    
    logger.info(f"收到 start 命令，用户ID: {user_id}，用户名: {user_name}，全名: {full_name}，角色: {user_role.name}")
    
    # 创建欢迎消息
    welcome_message = f"👋 *欢迎使用，{full_name}！*\n\n"
    
    if user_role == UserRole.ADMIN:
        welcome_message += "🔑 您现在以 *管理员* 身份登录。\n\n"
    else:
        welcome_message += "👤 您现在以 *普通用户* 身份登录。\n\n"
    
    welcome_message += "🔍 输入 /help 查看可用命令。"
    
    # 回复用户，不带命令键盘
    await update.message.reply_text(
        text=welcome_message,
        parse_mode='Markdown'
    )

def register_start_command(command_registry: CommandRegistry):
    """注册start命令
    
    Args:
        command_registry: 命令注册器实例
    """
    command_registry.register_command(
        CommandPlugin(
            command="start",
            description="开始使用机器人",
            handler=start_command,
            category=CommandCategory.MAIN,
            required_role=UserRole.USER
        )
    ) 