"""IP工具插件"""
import subprocess
from typing import Dict, Any

from telegram import Update
from telegram.ext import ContextTypes

from src.auth import UserManager, UserRole
from src.bot.plugins.interface import PluginInterface, CommandInfo, CommandCategory
from src.logger import logger
from src.config import config


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
                required_role=UserRole.ADMIN
            )
        )
    
    def check_current_ip(self) -> str:
        """检查当前IP
        
        Returns:
            str: 当前IP地址
        """
        ip_config = config.get('get_ip_cmd', ['curl -s api-ipv4.ip.sb/ip'])
        
        for cmd in ip_config:
            try:
                result = subprocess.check_output(cmd, shell=True, text=True).strip()
                if result:
                    return result
            except Exception as e:
                logger.error(f"IP检查命令失败: {cmd}, 错误: {str(e)}")
        
        return "无法获取IP"
    
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