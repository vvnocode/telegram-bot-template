"""IP工具插件"""
import os
import json
from datetime import datetime, date
from typing import Dict, Any, Optional

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
    
    def __init__(self, user_manager: UserManager):
        """初始化IP插件"""
        super().__init__(user_manager)
        self.data_file = os.path.join('data', 'records', 'ip_change_limits.json')
        # 确保数据目录存在
        data_dir = os.path.dirname(self.data_file)
        os.makedirs(data_dir, exist_ok=True)
    
    def register_commands(self) -> None:
        """注册IP相关命令"""
        self.register_command(
            CommandInfo(
                command="get_ip",
                description="查看当前IP地址",
                handler=self.check_ip_command,
                category=CommandCategory.TOOLS,
                required_role=UserRole.USER,
                sort=1
            )
        )
        
        self.register_command(
            CommandInfo(
                command="change_ip",
                description="更换IP地址",
                handler=self.change_ip_command,
                category=CommandCategory.TOOLS,
                required_role=UserRole.USER,
                sort=2
            )
        )
        
        self.register_command(
            CommandInfo(
                command="ip_stats",
                description="查看IP更换统计",
                handler=self.ip_stats_command,
                category=CommandCategory.TOOLS,
                required_role=UserRole.USER,
                sort=3
            )
        )
    
    def _load_limit_data(self) -> Dict[str, Any]:
        """加载IP更换次数数据
        
        Returns:
            Dict: 包含用户每日更换次数的数据
        """
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # 清理过期数据（只保留当天的数据）
                today = str(date.today())
                cleaned_data = {}
                
                if 'users' in data:
                    cleaned_data['users'] = {}
                    for user_id, user_data in data['users'].items():
                        if isinstance(user_data, dict) and user_data.get('date') == today:
                            cleaned_data['users'][user_id] = user_data
                
                if 'total' in data and isinstance(data['total'], dict) and data['total'].get('date') == today:
                    cleaned_data['total'] = data['total']
                else:
                    cleaned_data['total'] = {'date': today, 'count': 0}
                
                # 如果清理后数据有变化，保存
                if cleaned_data != data:
                    self._save_limit_data(cleaned_data)
                
                return cleaned_data
            else:
                today = str(date.today())
                return {
                    'users': {},
                    'total': {'date': today, 'count': 0}
                }
        except Exception as e:
            logger.error(f"加载IP更换次数数据失败: {str(e)}")
            today = str(date.today())
            return {
                'users': {},
                'total': {'date': today, 'count': 0}
            }
    
    def _save_limit_data(self, data: Dict[str, Any]) -> bool:
        """保存IP更换次数数据
        
        Args:
            data: 要保存的数据
            
        Returns:
            bool: 是否保存成功
        """
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"保存IP更换次数数据失败: {str(e)}")
            return False
    
    def _get_user_daily_count(self, user_id: int) -> int:
        """获取用户今日IP更换次数
        
        Args:
            user_id: 用户ID
            
        Returns:
            int: 今日更换次数
        """
        data = self._load_limit_data()
        today = str(date.today())
        user_id_str = str(user_id)
        
        user_data = data['users'].get(user_id_str, {})
        if user_data.get('date') == today:
            return user_data.get('count', 0)
        return 0
    
    def _get_total_daily_count(self) -> int:
        """获取今日总IP更换次数
        
        Returns:
            int: 今日总更换次数
        """
        data = self._load_limit_data()
        today = str(date.today())
        total_data = data.get('total', {})
        
        if total_data.get('date') == today:
            return total_data.get('count', 0)
        return 0
    
    def _can_change_ip(self, user_id: int, user_role: UserRole, user_limit: int, total_limit: int) -> tuple[bool, str]:
        """检查用户是否可以更换IP
        
        Args:
            user_id: 用户ID
            user_role: 用户角色
            user_limit: 普通用户每日限制次数
            total_limit: 每日总限制次数（0表示不限制）
            
        Returns:
            tuple[bool, str]: (是否可以更换, 限制原因)
        """
        # 管理员不受个人限制
        if user_role != UserRole.ADMIN:
            user_count = self._get_user_daily_count(user_id)
            if user_count >= user_limit:
                return False, f"您今日已达到个人更换IP次数限制（{user_limit}次）"
        
        # 检查总次数限制
        if total_limit > 0:
            total_count = self._get_total_daily_count()
            if total_count >= total_limit:
                return False, f"今日总更换IP次数已达到限制（{total_limit}次）"
        
        return True, ""
    
    def _record_ip_change(self, user_id: int) -> bool:
        """记录一次IP更换
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 是否记录成功
        """
        try:
            data = self._load_limit_data()
            today = str(date.today())
            user_id_str = str(user_id)
            
            # 更新用户计数
            if user_id_str not in data['users']:
                data['users'][user_id_str] = {'date': today, 'count': 0}
            elif data['users'][user_id_str].get('date') != today:
                data['users'][user_id_str] = {'date': today, 'count': 0}
            
            data['users'][user_id_str]['count'] += 1
            
            # 更新总计数
            if data['total'].get('date') != today:
                data['total'] = {'date': today, 'count': 0}
            
            data['total']['count'] += 1
            
            # 保存数据
            return self._save_limit_data(data)
        except Exception as e:
            logger.error(f"记录IP更换失败: {str(e)}")
            return False
    
    def _get_user_remaining_count(self, user_id: int, user_role: UserRole, user_limit: int) -> Optional[int]:
        """获取用户剩余可更换次数
        
        Args:
            user_id: 用户ID
            user_role: 用户角色
            user_limit: 普通用户每日限制次数
            
        Returns:
            Optional[int]: 剩余次数，管理员返回None表示无限制
        """
        if user_role == UserRole.ADMIN:
            return None  # 管理员无限制
        
        used_count = self._get_user_daily_count(user_id)
        remaining = max(0, user_limit - used_count)
        return remaining
    
    def _get_all_users_stats(self) -> Dict[str, int]:
        """获取所有用户的今日IP更换次数
        
        Returns:
            Dict[str, int]: 用户ID -> 今日更换次数的映射
        """
        data = self._load_limit_data()
        today = str(date.today())
        
        users_stats = {}
        for user_id_str, user_data in data.get('users', {}).items():
            if isinstance(user_data, dict) and user_data.get('date') == today:
                users_stats[user_id_str] = user_data.get('count', 0)
        
        return users_stats

    def _get_stats_message(self, user_id: int, user_role: UserRole, user_limit: int, total_limit: int) -> str:
        """获取统计信息消息
        
        Args:
            user_id: 用户ID
            user_role: 用户角色
            user_limit: 普通用户每日限制次数
            total_limit: 每日总限制次数
            
        Returns:
            str: 统计信息消息
        """
        today = str(date.today())
        user_count = self._get_user_daily_count(user_id)
        total_count = self._get_total_daily_count()
        
        message_parts = []
        message_parts.append(f"📊 **IP更换统计 ({today})**\n")
        
        # 个人统计
        if user_role == UserRole.ADMIN:
            message_parts.append(f"👤 **您的统计**: {user_count}次 (管理员无限制)")
        else:
            remaining = self._get_user_remaining_count(user_id, user_role, user_limit)
            message_parts.append(f"👤 **您的统计**: {user_count}/{user_limit}次 (剩余: {remaining}次)")
        
        # 总体统计
        if total_limit > 0:
            message_parts.append(f"🌐 **总体统计**: {total_count}/{total_limit}次")
        else:
            message_parts.append(f"🌐 **总体统计**: {total_count}次 (无限制)")
        
        # 管理员可以看到所有用户的详细统计
        if user_role == UserRole.ADMIN:
            all_users_stats = self._get_all_users_stats()
            if all_users_stats:
                message_parts.append(f"\n📋 **所有用户详细统计**:")
                
                # 获取管理员和普通用户列表
                admin_ids = set(self.user_manager.admin_ids)
                user_ids = set(self.user_manager.allowed_user_ids)
                
                # 按角色分组显示
                admin_stats = []
                user_stats = []
                
                for user_id_str, count in sorted(all_users_stats.items(), key=lambda x: int(x[1]), reverse=True):
                    if user_id_str in admin_ids:
                        admin_stats.append(f"🔑 `{user_id_str}`: {count}次 (管理员)")
                    elif user_id_str in user_ids:
                        remaining = max(0, user_limit - count)
                        admin_stats.append(f"👤 `{user_id_str}`: {count}/{user_limit}次 (剩余: {remaining})")
                    else:
                        # 未知用户（可能已被移除）
                        user_stats.append(f"❓ `{user_id_str}`: {count}次 (未知用户)")
                
                # 显示管理员统计
                if admin_stats:
                    for stat in admin_stats:
                        message_parts.append(stat)
                
                # 显示普通用户统计
                if user_stats:
                    for stat in user_stats:
                        message_parts.append(stat)
                        
                if not admin_stats and not user_stats:
                    message_parts.append("📭 暂无用户使用记录")
            else:
                message_parts.append(f"\n📋 **所有用户详细统计**: 📭 暂无用户使用记录")
        
        return "\n".join(message_parts)

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
        
        # 获取用户角色和限制配置
        user_role = user_manager.get_user_role(user_id)
        user_limit = change_ip_config.get('user_daily_limit', 2)
        total_limit = change_ip_config.get('total_daily_limit', 5)
        
        # 检查次数限制
        can_change, limit_reason = self._can_change_ip(user_id, user_role, user_limit, total_limit)
        if not can_change:
            await update.message.reply_text(
                f"🚫 **更换IP被限制**\n\n"
                f"❌ {limit_reason}",
                parse_mode='Markdown'
            )
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
            
            # 记录IP更换次数
            if not self._record_ip_change(user_id):
                logger.warning(f"记录用户 {user_id} IP更换次数失败")

            # 下发更新IP成功
            await processing_msg.edit_text(f"✅ **IP更换命令下发成功**\n\n请等待执行结果。如果长时间没有返回执行结果，请再次尝试或者联系管理员！", parse_mode='Markdown')

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
    
    async def ip_stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_manager: UserManager):
        """查看IP更换统计命令处理器
        
        Args:
            update: Telegram更新对象
            context: 上下文对象
            user_manager: 用户管理器实例
        """
        user_id = update.effective_user.id
        logger.info(f"用户 {user_id} 请求查看IP更换统计")
        
        # 获取配置
        change_ip_config = config.get('change_ip', {})
        user_limit = change_ip_config.get('user_daily_limit', 2)
        total_limit = change_ip_config.get('total_daily_limit', 0)
        
        # 获取用户角色
        user_role = user_manager.get_user_role(user_id)
        
        # 生成统计消息
        stats_msg = self._get_stats_message(user_id, user_role, user_limit, total_limit)
        
        await update.message.reply_text(stats_msg, parse_mode='Markdown') 