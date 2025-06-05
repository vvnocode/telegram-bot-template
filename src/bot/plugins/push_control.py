"""推送控制插件"""
from telegram import Update
from telegram.ext import ContextTypes

from src.auth import UserManager, UserRole
from src.bot.plugins.interface import PluginInterface, CommandInfo, CommandCategory
from src.logger import logger


class PushControlPlugin(PluginInterface):
    """推送控制插件，提供推送系统管理功能"""
    name = "push_control"
    description = "推送系统控制"
    version = "1.0.0"
    
    def register_commands(self) -> None:
        """注册推送控制相关命令"""
        self.register_command(
            CommandInfo(
                command="push_status",
                description="查看推送系统状态",
                handler=self.push_status_command,
                category=CommandCategory.PUSH,
                required_role=UserRole.ADMIN,
                sort=1
            )
        )
        
        self.register_command(
            CommandInfo(
                command="push_list",
                description="列出所有推送插件",
                handler=self.push_list_command,
                category=CommandCategory.PUSH,
                required_role=UserRole.ADMIN,
                sort=2
            )
        )
        
        self.register_command(
            CommandInfo(
                command="push_trigger",
                description="手动触发推送插件",
                handler=self.push_trigger_command,
                category=CommandCategory.PUSH,
                required_role=UserRole.ADMIN,
                sort=3
            )
        )
        
        self.register_command(
            CommandInfo(
                command="push_trigger_all",
                description="手动触发所有推送插件",
                handler=self.push_trigger_all_command,
                category=CommandCategory.PUSH,
                required_role=UserRole.ADMIN,
                sort=4
            )
        )
    
    async def push_status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_manager: UserManager):
        """查看推送系统状态命令处理器"""
        user_id = update.effective_user.id
        logger.info(f"管理员 {user_id} 请求查看推送系统状态")
        
        push_manager = context.bot_data.get('push_manager')
        if not push_manager:
            await update.message.reply_text("❌ 推送管理器未初始化")
            return
        
        plugins = push_manager.get_all_plugins()
        if not plugins:
            await update.message.reply_text("📋 没有加载任何推送插件")
            return
        
        status_lines = ["📊 **推送系统状态**\n"]
        
        for plugin_name, plugin in plugins.items():
            status_icon = "🟢" if plugin.is_enabled else "🔴"
            running_icon = "▶️" if plugin.is_running else "⏸️"
            
            frequency = plugin.config.frequency.value
            
            # 根据目标角色显示信息
            if plugin.config.custom_targets:
                custom_count = len(plugin.config.custom_targets)
                target_info = f"自定义({custom_count}个用户)"
            elif plugin.config.target_role == UserRole.ADMIN:
                target_info = "仅管理员"
            elif plugin.config.target_role == UserRole.USER:
                target_info = "所有用户"
            else:
                target_info = "未配置"
            
            status_lines.append(
                f"{status_icon} **{plugin_name}** {running_icon}\n"
                f"   📝 {plugin.description}\n"
                f"   ⏱️ 频率: {frequency}\n"
                f"   👥 目标: {target_info}\n"
            )
        
        message = "\n".join(status_lines)
        await update.message.reply_text(message, parse_mode='Markdown')
    
    async def push_list_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_manager: UserManager):
        """列出所有推送插件命令处理器"""
        user_id = update.effective_user.id
        logger.info(f"管理员 {user_id} 请求列出推送插件")
        
        push_manager = context.bot_data.get('push_manager')
        if not push_manager:
            await update.message.reply_text("❌ 推送管理器未初始化")
            return
        
        plugins = push_manager.get_all_plugins()
        if not plugins:
            await update.message.reply_text("📋 没有加载任何推送插件")
            return
        
        plugin_lines = ["📋 **可用推送插件列表**\n"]
        
        for plugin_name, plugin in plugins.items():
            status = "启用" if plugin.is_enabled else "禁用"
            plugin_lines.append(
                f"• **{plugin_name}** ({status})\n"
                f"  📝 {plugin.description}\n"
                f"  🏷️ 版本: {plugin.version}\n"
            )
        
        message = "\n".join(plugin_lines)
        await update.message.reply_text(message, parse_mode='Markdown')
    
    async def push_trigger_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_manager: UserManager):
        """手动触发推送插件命令处理器"""
        user_id = update.effective_user.id
        
        # 获取参数
        if not context.args:
            await update.message.reply_text(
                "❌ 请指定要触发的推送插件名称\n\n"
                "用法: `/push_trigger <插件名称>`\n"
                "示例: `/push_trigger ip_monitor`",
                parse_mode='Markdown'
            )
            return
        
        plugin_name = context.args[0]
        logger.info(f"管理员 {user_id} 请求手动触发推送插件: {plugin_name}")
        
        push_manager = context.bot_data.get('push_manager')
        if not push_manager:
            await update.message.reply_text("❌ 推送管理器未初始化")
            return
        
        # 检查插件是否存在
        if not push_manager.get_plugin(plugin_name):
            await update.message.reply_text(f"❌ 推送插件 `{plugin_name}` 不存在")
            return
        
        # 触发插件
        success = await push_manager.trigger_plugin(plugin_name)
        
        if success:
            await update.message.reply_text(
                f"✅ 成功触发推送插件 `{plugin_name}`",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                f"❌ 触发推送插件 `{plugin_name}` 失败",
                parse_mode='Markdown'
            )
    
    async def push_trigger_all_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_manager: UserManager):
        """手动触发所有推送插件命令处理器"""
        user_id = update.effective_user.id
        logger.info(f"管理员 {user_id} 请求手动触发所有推送插件")
        
        push_manager = context.bot_data.get('push_manager')
        if not push_manager:
            await update.message.reply_text("❌ 推送管理器未初始化")
            return
        
        plugins = push_manager.get_all_plugins()
        if not plugins:
            await update.message.reply_text("📋 没有可触发的推送插件")
            return
        
        await update.message.reply_text("🔄 开始触发所有推送插件...")
        
        success_count = await push_manager.trigger_all_plugins()
        total_count = len(plugins)
        
        if success_count == total_count:
            await update.message.reply_text(
                f"✅ 成功触发所有 {total_count} 个推送插件"
            )
        elif success_count > 0:
            await update.message.reply_text(
                f"⚠️ 成功触发 {success_count}/{total_count} 个推送插件"
            )
        else:
            await update.message.reply_text(
                f"❌ 触发推送插件失败，共 {total_count} 个插件"
            ) 