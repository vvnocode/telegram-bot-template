from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from src.auth import UserManager
from src.logger import logger

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE, user_manager: UserManager):
    """处理/start命令
    
    Args:
        update: Telegram更新对象
        context: 上下文对象
        user_manager: 用户管理器实例
    """
    # 验证用户权限
    if not await user_manager.check_user_permission(update):
        return
    
    # 获取用户信息
    user_id = update.effective_user.id
    user_name = update.effective_user.username
    full_name = update.effective_user.full_name
    
    logger.info(f"收到 start 命令，用户ID: {user_id}，用户名: {user_name}，全名: {full_name}")
        
    # 回复用户
    await update.message.reply_text(
        text=f"欢迎使用，{full_name}！\n"
             f"您的用户ID: {user_id}，用户名: {user_name}\n"
             f"输入 /help 查看可用命令"
    )

def register_start_handler(application, user_manager: UserManager):
    """注册start命令处理器"""
    application.add_handler(
        CommandHandler(
            "start", 
            lambda update, context: start_command(update, context, user_manager)
        )
    ) 