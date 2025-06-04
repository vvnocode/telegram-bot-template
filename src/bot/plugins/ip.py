"""IP工具插件"""
from typing import Dict, Any

from telegram import Update
from telegram.ext import ContextTypes

from src.auth import UserManager, UserRole
from src.bot.plugins.interface import PluginInterface, CommandInfo, CommandCategory
from src.logger import logger
from src.utils.ip_utils import IPUtils


class IPPlugin(PluginInterface):
    """IP工具插件，提供IP地址查询功能"""
    name = "ip"
    description = "IP地址工具"
    version = "1.0.0"
    
    def register_commands(self) -> None:
        """注册IP相关命令"""
        self.register_command(
            CommandInfo(
                command="get_ip",
                description="查看当前IP地址",
                handler=self.check_ip_command,
                category=CommandCategory.TOOLS,
                required_role=UserRole.USER
            )
        )
    
    def check_current_ip(self) -> str:
        """检查当前IP
        
        Returns:
            str: 当前IP地址
        """
        return IPUtils.get_current_ip_with_fallback()
    
    async def check_ip_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_manager: UserManager):
        """查看当前IP命令处理器
        
        Args:
            update: Telegram更新对象
            context: 上下文对象
            user_manager: 用户管理器实例
        """
        user_id = update.effective_user.id
        logger.info(f"用户 {user_id} 请求查看当前IP")
        
        current_ip = self.check_current_ip()
        
        await update.message.reply_text(f"当前IP地址: {current_ip}") 