from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from src.auth import UserManager
from src.logger import logger

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE, user_manager: UserManager):
    """处理/help命令
    
    Args:
        update: Telegram更新对象
        context: 上下文对象
        user_manager: 用户管理器实例
    """
    # 验证用户权限
    if not await user_manager.check_user_permission(update):
        return
    
    # 获取用户角色
    user_id = update.effective_user.id
    role = user_manager.get_user_role(user_id)
    
    # 准备通用命令列表
    help_text = "可用命令列表：\n\n" \
                "/start - 启动机器人\n" \
                "/help - 显示此帮助信息\n"
    
    # 如果是管理员，添加管理员命令
    if role and role.name == "ADMIN":
        help_text += "\n管理员命令：\n" \
                    "/admin - 管理员控制面板\n"
    
    logger.info(f"用户 {user_id} 请求了帮助信息")
    await update.message.reply_text(help_text)

def register_help_handler(application, user_manager: UserManager):
    """注册help命令处理器"""
    application.add_handler(
        CommandHandler(
            "help", 
            lambda update, context: help_command(update, context, user_manager)
        )
    ) 