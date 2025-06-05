"""用户使用统计插件"""
from telegram import Update
from telegram.ext import ContextTypes
from datetime import date, timedelta
from collections import defaultdict

from src.auth import UserManager, UserRole
from src.logger import logger
from src.bot.plugins.interface import PluginInterface, CommandInfo, CommandCategory
from src.utils import UserStatsManager
from src.utils.user_utils import UserUtils


class StatsPlugin(PluginInterface):
    """统计分析插件，提供命令使用情况统计功能"""
    name = "stats"
    description = "用户使用统计插件"
    version = "1.0.0"
    
    def register_commands(self) -> None:
        """注册统计相关命令"""
        # 注册总体统计命令
        self.register_command(
            CommandInfo(
                command="stats_total",
                description="显示所有命令的总体使用统计",
                handler=self.stats_total_command,
                category=CommandCategory.STATS,
                required_role=UserRole.ADMIN,
                is_visible=True,
                sort=1
            )
        )
        
        # 注册今日统计命令
        self.register_command(
            CommandInfo(
                command="stats_today",
                description="显示所有命令的今日使用统计",
                handler=self.stats_today_command,
                category=CommandCategory.STATS,
                required_role=UserRole.ADMIN,
                is_visible=True,
                sort=2
            )
        )
        
        # 注册用户总体统计命令
        self.register_command(
            CommandInfo(
                command="stats_users_total",
                description="显示所有用户的各菜单使用详情统计",
                handler=self.stats_users_total_command,
                category=CommandCategory.STATS,
                required_role=UserRole.ADMIN,
                is_visible=True,
                sort=3
            )
        )
        
        # 注册用户今日统计命令
        self.register_command(
            CommandInfo(
                command="stats_users_today",
                description="显示所有用户的今日各菜单使用详情",
                handler=self.stats_users_today_command,
                category=CommandCategory.STATS,
                required_role=UserRole.ADMIN,
                is_visible=True,
                sort=4
            )
        )
        
        # 注册指定用户统计命令
        self.register_command(
            CommandInfo(
                command="stats_user",
                description="显示指定用户的统计信息，格式: /stats_user [user_id]",
                handler=self.stats_user_command,
                category=CommandCategory.STATS,
                required_role=UserRole.ADMIN,
                is_visible=True,
                sort=5
            )
        )
    
    async def stats_total_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_manager: UserManager):
        """处理/stats_total命令，显示总体命令使用统计，仅管理员可用"""
        
        # 获取统计管理器
        stats_manager: UserStatsManager = context.bot_data.get('stats_manager')
        if not stats_manager:
            await update.message.reply_text("❌ 统计功能未启用")
            return
        
        try:
            await self.show_total_stats(update, stats_manager)
        except Exception as e:
            logger.error(f"显示总体统计时出错: {str(e)}")
            await update.message.reply_text(f"显示统计数据时出错: {str(e)}")
    
    async def stats_today_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_manager: UserManager):
        """处理/stats_today命令，显示今日命令使用统计，仅管理员可用"""
        
        # 获取统计管理器
        stats_manager: UserStatsManager = context.bot_data.get('stats_manager')
        if not stats_manager:
            await update.message.reply_text("❌ 统计功能未启用")
            return
        
        try:
            await self.show_daily_stats(update, stats_manager, date.today())
        except Exception as e:
            logger.error(f"显示今日统计时出错: {str(e)}")
            await update.message.reply_text(f"显示统计数据时出错: {str(e)}")
    
    async def stats_users_total_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_manager: UserManager):
        """处理/stats_users_total命令，显示所有用户的总体菜单使用详情，仅管理员可用"""
        
        # 获取统计管理器
        stats_manager: UserStatsManager = context.bot_data.get('stats_manager')
        if not stats_manager:
            await update.message.reply_text("❌ 统计功能未启用")
            return
        
        try:
            await self.show_users_menu_stats(update, stats_manager, user_manager, context)
        except Exception as e:
            logger.error(f"显示用户总体统计时出错: {str(e)}")
            await update.message.reply_text(f"显示统计数据时出错: {str(e)}")
    
    async def stats_users_today_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_manager: UserManager):
        """处理/stats_users_today命令，显示所有用户今日菜单使用详情，仅管理员可用"""
        
        # 获取统计管理器
        stats_manager: UserStatsManager = context.bot_data.get('stats_manager')
        if not stats_manager:
            await update.message.reply_text("❌ 统计功能未启用")
            return
        
        try:
            await self.show_users_menu_daily_stats(update, stats_manager, user_manager, date.today(), context)
        except Exception as e:
            logger.error(f"显示用户今日统计时出错: {str(e)}")
            await update.message.reply_text(f"显示统计数据时出错: {str(e)}")
    
    async def stats_user_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_manager: UserManager):
        """处理/stats_user命令，显示指定用户的统计信息，仅管理员可用"""
        
        # 获取统计管理器
        stats_manager: UserStatsManager = context.bot_data.get('stats_manager')
        if not stats_manager:
            await update.message.reply_text("❌ 统计功能未启用")
            return
        
        # 获取命令参数
        args = context.args
        if not args:
            await update.message.reply_text("❌ 请指定用户ID，格式: /stats_user [user_id]")
            return
            
        user_id = args[0]
        try:
            await self.show_user_stats(update, stats_manager, user_id, context)
        except Exception as e:
            logger.error(f"显示指定用户统计时出错: {str(e)}")
            await update.message.reply_text(f"显示统计数据时出错: {str(e)}")
    
    async def show_total_stats(self, update: Update, stats_manager: UserStatsManager):
        """显示总体统计信息
        
        Args:
            update: Telegram更新对象
            stats_manager: 统计管理器实例
        """
        # 获取命令总体摘要
        command_summary = stats_manager.get_command_summary()
        
        if not command_summary:
            await update.message.reply_text("📊 目前还没有统计数据")
            return
        
        # 构建消息
        message = "📊 *命令使用总体统计*\n\n"
        
        # 按使用次数降序排序
        sorted_commands = sorted(command_summary.items(), key=lambda x: x[1], reverse=True)
        
        for command, count in sorted_commands:
            # 转义命令名称中的下划线
            escaped_command = command.replace('_', '\\_')
            message += f"/{escaped_command}: {count}次\n"
        
        # 计算总使用次数
        total_usage = sum(command_summary.values())
        message += f"\n总计: {total_usage}次"
        
        # 发送消息
        try:
            await update.message.reply_text(message, parse_mode='Markdown')
        except Exception as e:
            # 如果Markdown格式失败，尝试无格式发送
            logger.error(f"使用Markdown格式发送消息失败: {str(e)}")
            await update.message.reply_text(message.replace('*', ''), parse_mode=None)
    
    async def show_daily_stats(self, update: Update, stats_manager: UserStatsManager, day: date):
        """显示每日统计信息
        
        Args:
            update: Telegram更新对象
            stats_manager: 统计管理器实例
            day: 日期对象
        """
        # 获取指定日期的命令摘要
        command_summary = stats_manager.get_command_summary(day)
        
        if not command_summary:
            await update.message.reply_text(f"📊 {day.isoformat()} 没有统计数据")
            return
        
        # 构建消息
        message = f"📊 *{day.isoformat()} 命令使用统计*\n\n"
        
        # 按使用次数降序排序
        sorted_commands = sorted(command_summary.items(), key=lambda x: x[1], reverse=True)
        
        for command, count in sorted_commands:
            # 转义命令名称中的下划线
            escaped_command = command.replace('_', '\\_')
            message += f"/{escaped_command}: {count}次\n"
        
        # 计算总使用次数
        total_usage = sum(command_summary.values())
        message += f"\n总计: {total_usage}次"
        
        # 发送消息
        try:
            await update.message.reply_text(message, parse_mode='Markdown')
        except Exception as e:
            # 如果Markdown格式失败，尝试无格式发送
            logger.error(f"使用Markdown格式发送每日统计失败: {str(e)}")
            await update.message.reply_text(message.replace('*', ''), parse_mode=None)
    
    async def show_user_stats(self, update: Update, stats_manager: UserStatsManager, user_id: str, context: ContextTypes.DEFAULT_TYPE = None):
        """显示用户统计信息
        
        Args:
            update: Telegram更新对象
            stats_manager: 统计管理器实例
            user_id: 用户ID
            context: Telegram上下文对象（用于获取用户昵称）
        """
        # 获取用户总体统计
        user_total_stats = stats_manager.get_user_total_stats(user_id)
        
        # 获取用户今日统计
        user_today_stats = stats_manager.get_user_daily_stats(user_id)
        
        if not user_total_stats and not user_today_stats:
            user_display_name = await UserUtils.get_user_display_name(user_id, context)
            await update.message.reply_text(f"📊 {user_display_name} 没有统计数据")
            return
        
        # 构建消息
        user_display_name = await UserUtils.get_user_display_name(user_id, context)
        message = f"📊 *{user_display_name} 的使用统计*\n\n"
        
        # 今日统计
        if user_today_stats:
            message += "*今日使用:*\n"
            sorted_today = sorted(user_today_stats.items(), key=lambda x: x[1], reverse=True)
            for command, count in sorted_today:
                escaped_cmd = command.replace('_', '\\_')
                message += f"/{escaped_cmd}: {count}次\n"
            message += f"今日总计: {sum(user_today_stats.values())}次\n\n"
        
        # 总体统计
        if user_total_stats:
            message += "*总体使用:*\n"
            sorted_total = sorted(user_total_stats.items(), key=lambda x: x[1], reverse=True)
            for command, count in sorted_total:
                escaped_cmd = command.replace('_', '\\_')
                message += f"/{escaped_cmd}: {count}次\n"
            message += f"总计: {sum(user_total_stats.values())}次"
        
        # 发送消息
        try:
            await update.message.reply_text(message, parse_mode='Markdown')
        except Exception as e:
            # 如果Markdown格式失败，尝试无格式发送
            logger.error(f"使用Markdown格式发送用户统计失败: {str(e)}")
            await update.message.reply_text(message.replace('*', ''), parse_mode=None)
    
    async def show_users_menu_stats(self, update: Update, stats_manager: UserStatsManager, user_manager: UserManager, context: ContextTypes.DEFAULT_TYPE = None):
        """显示所有用户的菜单使用详情（总体统计）
        
        Args:
            update: Telegram更新对象
            stats_manager: 统计管理器实例
            user_manager: 用户管理器实例
            context: Telegram上下文对象（用于获取用户昵称）
        """
        # 获取所有用户的总体统计
        all_stats = stats_manager.get_all_total_stats()
        
        if not all_stats:
            await update.message.reply_text("📊 目前还没有统计数据")
            return
        
        # 构建按用户分组的菜单使用情况 (而不是按菜单分组)
        user_menu_stats = {}
        
        for user_id, commands in all_stats.items():
            user_menu_stats[user_id] = commands
        
        # 获取用户角色信息
        all_users = user_manager.get_all_users()
        admin_ids = all_users['admins']
        normal_user_ids = all_users['users']
        
        # 构建消息
        message = "📊 *各用户菜单使用详情统计*\n\n"
        
        # 先显示管理员
        for user_id in admin_ids:
            if user_id in user_menu_stats:
                user_display_name = await UserUtils.get_user_display_name(user_id, context)
                message += f"*👑 {user_display_name}:*\n"
                
                # 按使用次数对命令排序
                sorted_commands = sorted(user_menu_stats[user_id].items(), key=lambda x: x[1], reverse=True)
                
                for cmd, count in sorted_commands:
                    # 转义命令名称中的下划线
                    escaped_cmd = cmd.replace('_', '\\_')
                    message += f"  /{escaped_cmd}: {count}次\n"
                
                message += "\n"
        
        # 再显示普通用户
        for user_id in normal_user_ids:
            if user_id in user_menu_stats:
                user_display_name = await UserUtils.get_user_display_name(user_id, context)
                message += f"*👤 {user_display_name}:*\n"
                
                # 按使用次数对命令排序
                sorted_commands = sorted(user_menu_stats[user_id].items(), key=lambda x: x[1], reverse=True)
                
                for cmd, count in sorted_commands:
                    escaped_cmd = cmd.replace('_', '\\_')
                    message += f"  /{escaped_cmd}: {count}次\n"
                
                message += "\n"
        
        # 发送消息
        try:
            await update.message.reply_text(message, parse_mode='Markdown')
        except Exception as e:
            # 如果Markdown格式失败，尝试无格式发送
            logger.error(f"使用Markdown格式发送菜单统计失败: {str(e)}")
            await update.message.reply_text(message.replace('*', ''), parse_mode=None)
    
    async def show_users_menu_daily_stats(self, update: Update, stats_manager: UserStatsManager, user_manager: UserManager, day: date, context: ContextTypes.DEFAULT_TYPE = None):
        """显示所有用户的菜单使用详情（每日统计）
        
        Args:
            update: Telegram更新对象
            stats_manager: 统计管理器实例
            user_manager: 用户管理器实例
            day: 日期对象
            context: Telegram上下文对象（用于获取用户昵称）
        """
        # 获取指定日期的统计数据
        all_stats = stats_manager.get_all_daily_stats(day)
        
        if not all_stats:
            await update.message.reply_text(f"📊 {day.isoformat()} 没有统计数据")
            return
        
        # 构建按用户分组的菜单使用情况
        user_menu_stats = {}
        
        for user_id, commands in all_stats.items():
            user_menu_stats[user_id] = commands
        
        # 获取用户角色信息
        all_users = user_manager.get_all_users()
        admin_ids = all_users['admins']
        normal_user_ids = all_users['users']
        
        # 构建消息
        message = f"📊 *{day.isoformat()} 各用户菜单使用详情*\n\n"
        
        # 先显示管理员
        for user_id in admin_ids:
            if user_id in user_menu_stats:
                user_display_name = await UserUtils.get_user_display_name(user_id, context)
                message += f"*👑 {user_display_name}:*\n"
                
                # 按使用次数对命令排序
                sorted_commands = sorted(user_menu_stats[user_id].items(), key=lambda x: x[1], reverse=True)
                
                for cmd, count in sorted_commands:
                    # 转义命令名称中的下划线
                    escaped_cmd = cmd.replace('_', '\\_')
                    message += f"  /{escaped_cmd}: {count}次\n"
                
                message += "\n"
        
        # 再显示普通用户
        for user_id in normal_user_ids:
            if user_id in user_menu_stats:
                user_display_name = await UserUtils.get_user_display_name(user_id, context)
                message += f"*👤 {user_display_name}:*\n"
                
                # 按使用次数对命令排序
                sorted_commands = sorted(user_menu_stats[user_id].items(), key=lambda x: x[1], reverse=True)
                
                for cmd, count in sorted_commands:
                    escaped_cmd = cmd.replace('_', '\\_')
                    message += f"  /{escaped_cmd}: {count}次\n"
                
                message += "\n"
        
        # 发送消息
        try:
            await update.message.reply_text(message, parse_mode='Markdown')
        except Exception as e:
            # 如果Markdown格式失败，尝试无格式发送
            logger.error(f"使用Markdown格式发送每日菜单统计失败: {str(e)}")
            await update.message.reply_text(message.replace('*', ''), parse_mode=None) 