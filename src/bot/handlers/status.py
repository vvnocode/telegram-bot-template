from telegram import Update
from telegram.ext import ContextTypes

import os
import platform
import time
import psutil

from src.auth import UserManager, UserRole
from src.logger import logger
from src.bot.handlers.command import CommandPlugin, CommandCategory, CommandRegistry

# 启动时间
START_TIME = time.time()

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE, user_manager: UserManager):
    """处理/status命令，显示机器人状态，仅管理员可用
    
    Args:
        update: Telegram更新对象
        context: 上下文对象
        user_manager: 用户管理器实例
    """
    
    # 获取管理员信息
    admin_id = update.effective_user.id
    admin_name = update.effective_user.username
    
    logger.info(f"管理员 {admin_id} ({admin_name}) 查看了系统状态")
    
    # 计算运行时间
    uptime_seconds = int(time.time() - START_TIME)
    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    uptime_str = ""
    if days > 0:
        uptime_str += f"{days}天 "
    if hours > 0 or days > 0:
        uptime_str += f"{hours}小时 "
    if minutes > 0 or hours > 0 or days > 0:
        uptime_str += f"{minutes}分钟 "
    uptime_str += f"{seconds}秒"
    
    # 获取系统信息
    cpu_percent = psutil.cpu_percent()
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # 构建状态消息
    status_message = "🖥️ *系统状态*\n\n"
    
    # 机器人信息
    status_message += "*🤖 机器人信息:*\n"
    status_message += f"⏱️ 运行时间: {uptime_str}\n"
    status_message += f"👥 已授权用户: {len(user_manager.allowed_user_ids)}\n"
    status_message += f"👑 管理员: {len(user_manager.admin_ids)}\n\n"
    
    # 系统信息
    status_message += "*💻 系统信息:*\n"
    status_message += f"🐧 系统: {platform.system()} {platform.release()}\n"
    status_message += f"🔄 CPU使用率: {cpu_percent}%\n"
    status_message += f"💾 内存: {mem.percent}% ({round(mem.used/1024/1024/1024, 1)}/{round(mem.total/1024/1024/1024, 1)} GB)\n"
    status_message += f"💿 硬盘: {disk.percent}% ({round(disk.used/1024/1024/1024, 1)}/{round(disk.total/1024/1024/1024, 1)} GB)\n"
    
    # 发送状态消息
    await update.message.reply_text(status_message, parse_mode='Markdown')

def register_status_command(command_registry: CommandRegistry):
    """注册status命令
    
    Args:
        command_registry: 命令注册器实例
    """
    command_registry.register_command(
        CommandPlugin(
            command="status",
            description="查看系统状态",
            handler=status_command,
            category=CommandCategory.SYSTEM,
            required_role=UserRole.ADMIN
        )
    ) 