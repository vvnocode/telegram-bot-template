#!/usr/bin/env python3
from telegram.ext import ApplicationBuilder, Application
from typing import Dict, Any

from src.auth import UserManager
from src.logger import logger
from src.utils import UserStatsManager

class TelegramBot:
    """Telegram机器人核心类"""
    def __init__(self, config: Dict[str, Any]):
        """初始化机器人实例
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.user_manager = UserManager(config)
        self.stats_manager = UserStatsManager()
        self.app = None
        
    def setup(self) -> None:
        """设置机器人，注册处理器"""
        logger.info("机器人开始初始化...")
        
        # 创建应用实例
        self.app = ApplicationBuilder().token(self.config["telegram_bot_token"]).build()
        
        # 注册命令处理器（由各个handlers模块处理）
        from src.bot.handlers import register_handlers
        register_handlers(self.app, self.user_manager, self.stats_manager)
        
        logger.info("机器人初始化完成")
    
    def run(self) -> None:
        """运行机器人"""
        if self.app is None:
            self.setup()
            
        logger.info("机器人开始运行...")
        self.app.run_polling()
        
    def get_application(self) -> Application:
        """获取telegram应用实例"""
        if self.app is None:
            self.setup()
        return self.app 