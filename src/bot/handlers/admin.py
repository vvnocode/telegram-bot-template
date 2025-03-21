from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from src.auth import UserManager
from src.logger import logger

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE, user_manager: UserManager):
    """处理/admin命令，仅管理员可用
    
    Args:
        update: Telegram更新对象
        context: 上下文对象
        user_manager: 用户管理器实例
    """
    # 验证管理员权限
    if not await user_manager.check_admin_permission(update):
        return
    
    # 获取管理员信息
    admin_id = update.effective_user.id
    admin_name = update.effective_user.username
    
    logger.info(f"管理员 {admin_id} ({admin_name}) 访问了管理面板")
    
    # 回复管理员
    await update.message.reply_text(
        text=f"管理员控制面板\n"
             f"管理员ID: {admin_id}\n"
             f"管理员名称: {admin_name}\n\n"
             f"可用管理命令：\n"
             f"/status - 查看机器人状态\n"
    )

def register_admin_handler(application, user_manager: UserManager):
    """注册admin命令处理器"""
    application.add_handler(
        CommandHandler(
            "admin", 
            lambda update, context: admin_command(update, context, user_manager)
        )
    ) 