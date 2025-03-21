from telegram.ext import Application
from src.auth import UserManager
from src.logger import logger

# 导入所有处理器模块
from .start import register_start_handler
from .help import register_help_handler
from .admin import register_admin_handler
from .status import register_status_handler

def register_handlers(app: Application, user_manager: UserManager) -> None:
    """注册所有命令处理器
    
    Args:
        app: Telegram应用实例
        user_manager: 用户管理器实例
    """
    logger.info("注册命令处理器...")
    
    # 注册基础命令
    register_start_handler(app, user_manager)
    register_help_handler(app, user_manager)
    
    # 注册管理员命令
    register_admin_handler(app, user_manager)
    register_status_handler(app, user_manager)
    
    logger.info("命令处理器注册完成")
