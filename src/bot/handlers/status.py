from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
import time
import os
from datetime import datetime

from src.auth import UserManager
from src.logger import logger
from src.utils import get_system_info, format_time_delta

# 记录机器人启动时间
BOT_START_TIME = time.time()

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE, user_manager: UserManager):
    """处理/status命令，查看机器人状态
    
    Args:
        update: Telegram更新对象
        context: 上下文对象
        user_manager: 用户管理器实例
    """
    # 验证管理员权限
    if not await user_manager.check_admin_permission(update):
        return
    
    # 获取系统信息
    system_info = get_system_info()
    
    # 计算运行时间
    uptime_seconds = time.time() - BOT_START_TIME
    uptime_str = format_time_delta(int(uptime_seconds))
    
    # 构造状态消息
    status_message = (
        f"🤖 机器人状态报告\n\n"
        f"📊 系统信息:\n"
        f"➢ 平台: {system_info['platform']}\n"
        f"➢ Python: {system_info['python_version']}\n"
        f"➢ 主机名: {system_info['hostname']}\n"
        f"➢ CPU使用率: {system_info['cpu_usage']}%\n"
        f"➢ 内存使用率: {system_info['memory_usage']}%\n"
        f"➢ 磁盘使用率: {system_info['disk_usage']}%\n\n"
        f"⏱ 运行时间: {uptime_str}\n"
        f"🕒 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    )
    
    logger.info(f"用户 {update.effective_user.id} 请求了状态信息")
    await update.message.reply_text(status_message)

def register_status_handler(application, user_manager: UserManager):
    """注册status命令处理器"""
    application.add_handler(
        CommandHandler(
            "status", 
            lambda update, context: status_command(update, context, user_manager)
        )
    ) 