#!/usr/bin/env python3
from telegram.ext import ApplicationBuilder, Application
from typing import Dict, Any

from src.auth import UserManager
from src.logger import logger
from src.utils import UserStatsManager
from src.bot.plugins.loader import PluginLoader
from src.push.manager import PushManager

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
        self.plugin_loader = PluginLoader(self.user_manager, config)
        self.push_manager = PushManager(self.user_manager, config)
        self.app = None
        
    def setup(self) -> None:
        """设置机器人，加载插件"""
        logger.info("机器人开始初始化...")
        
        # 创建应用实例
        self.app = ApplicationBuilder().token(self.config["telegram_bot_token"]).build()
        
        # 添加管理器到应用数据
        self.app.bot_data['stats_manager'] = self.stats_manager
        self.app.bot_data['push_manager'] = self.push_manager
        
        # 加载并设置插件
        self.plugin_loader.setup_plugins(self.app)
        
        logger.info("机器人初始化完成")
    
    def run(self) -> None:
        """运行机器人"""
        if self.app is None:
            self.setup()
            
        logger.info("机器人开始运行...")
        
        # 设置启动后的处理
        async def post_init(application: Application):
            logger.info("应用启动后设置...")
            
            # 设置命令菜单
            await self.plugin_loader.setup_bot_commands(application)
            
            # 启动推送管理器
            await self.push_manager.start_all_plugins(application)
        
        # 设置停止时的处理
        async def post_shutdown(application: Application):
            logger.info("应用停止时清理...")
            
            # 停止推送管理器
            await self.push_manager.stop_all_plugins()
        
        # 注册应用处理器
        self.app.post_init = post_init
        self.app.post_shutdown = post_shutdown
        
        # 开始轮询
        self.app.run_polling()
        
    def get_application(self) -> Application:
        """获取telegram应用实例"""
        if self.app is None:
            self.setup()
        return self.app 