"""IP工具插件"""
from typing import Dict, Any

from telegram import Update
from telegram.ext import ContextTypes

from src.auth import UserManager, UserRole
from src.bot.plugins.interface import PluginInterface, CommandInfo, CommandCategory
from src.logger import logger
from src.utils.ip_utils import IPUtils
from src.utils.http_utils import HTTPUtils
from src.config import config


class IPPlugin(PluginInterface):
    """IP工具插件"""
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
        
        self.register_command(
            CommandInfo(
                command="change_ip",
                description="更换IP地址",
                handler=self.change_ip_command,
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
        
        await update.message.reply_text(f"📍 当前IP地址: `{current_ip}`", parse_mode='Markdown')
    
    async def change_ip_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_manager: UserManager):
        """更换IP命令处理器
        
        Args:
            update: Telegram更新对象
            context: 上下文对象
            user_manager: 用户管理器实例
        """
        user_id = update.effective_user.id
        logger.info(f"用户 {user_id} 请求更换IP")
        
        # 检查配置
        change_ip_config = config.get('change_ip')
        if not change_ip_config:
            await update.message.reply_text("❌ **配置错误**\n\n⚠️ 更换IP功能未配置，请联系管理员在配置文件中添加 `change_ip` 配置项。", parse_mode='Markdown')
            return
        
        url = change_ip_config.get('url', '').strip()
        if not url:
            await update.message.reply_text("❌ **配置错误**\n\n⚠️ 更换IP的URL未配置，请联系管理员在配置文件的 `change_ip.url` 中设置接口地址。", parse_mode='Markdown')
            return
        
        # 获取更换前的IP
        old_ip = self.check_current_ip()
        
        # 发送处理中消息
        processing_msg = await update.message.reply_text("🔄 **正在更换IP...**\n\n⏳ 请稍候，正在调用更换IP接口...", parse_mode='Markdown')
        
        try:
            # 调用更换IP接口
            method = change_ip_config.get('method', 'GET').upper()
            headers = change_ip_config.get('headers', {})
            data = change_ip_config.get('data', {})
            timeout = change_ip_config.get('timeout', 30)
            
            success, response = HTTPUtils.make_request(
                url=url,
                method=method,
                headers=headers,
                data=data if data else None,
                timeout=timeout
            )

            if not success:
                logger.error(f"更换IP失败: {response}")
                await processing_msg.edit_text(
                    f"❌ **更换IP失败**\n\n🚫 接口调用失败：\n`{response}`\n\n📋 请联系管理员。",
                    parse_mode='Markdown'
                )
                return
            
            logger.info(f"更换IP接口调用成功: {response}")

            # 下发更新IP成功
            await processing_msg.edit_text(f"✅ **IP更换命令下发成功**\n\n请等待执行结果", parse_mode='Markdown')

            # 是否通知用户。因为同的接口，不同的返回值，所以用户决定是否通知用户结果。默认不通知。
            notify_user = change_ip_config.get('notify_user', False)
            if notify_user:
                # 等待一段时间后检查新IP
                import asyncio
                await asyncio.sleep(5)
                
                # 获取新的IP
                new_ip = self.check_current_ip()
                
                if old_ip == new_ip:
                    await processing_msg.edit_text(
                        f"⚠️ **IP未发生变化**\n\n"
                        f"📍 **当前IP**: `{new_ip}`\n"
                        f"📡 **接口响应**: `{response[:200]}`\n\n"
                        f"ℹ️ 接口调用成功，但IP地址未变化。可能需要更长时间生效，或者接口配置需要调整。",
                        parse_mode='Markdown'
                    )
                else:
                    await processing_msg.edit_text(
                        f"✅ **IP更换成功**\n\n"
                        f"📍 **旧IP**: `{old_ip}`\n"
                        f"📍 **新IP**: `{new_ip}`\n"
                        f"📡 **接口响应**: `{response[:200]}`\n\n"
                        f"🎉 IP地址已成功更换！",
                        parse_mode='Markdown'
                    )
            
        except Exception as e:
            logger.error(f"更换IP过程中出错: {str(e)}")
            await processing_msg.edit_text(
                f"❌ **更换IP过程中出错**\n\n"
                f"🚫 错误信息：`{str(e)}`\n\n"
                f"📋 请联系管理员。",
                parse_mode='Markdown'
            ) 