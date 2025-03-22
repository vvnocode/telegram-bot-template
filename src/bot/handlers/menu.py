from telegram import Update
from telegram.ext import ContextTypes

from src.auth import UserManager, UserRole
from src.logger import logger
from src.bot.handlers.command import CommandPlugin, CommandCategory, CommandRegistry

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE, user_manager: UserManager):
    """处理/menu命令，显示所有可用命令及其权限
    
    Args:
        update: Telegram更新对象
        context: 上下文对象
        user_manager: 用户管理器实例
    """
    # 获取用户信息
    user_id = update.effective_user.id
    user_role = user_manager.get_user_role(user_id)
    
    # 如果用户无权限，拒绝访问
    if user_role is None:
        logger.warning(f"未授权的用户 {user_id} 尝试查看菜单")
        await update.message.reply_text("未授权的用户")
        return
    
    logger.info(f"用户 {user_id} 请求查看菜单，角色: {user_role.name}")
    
    # 获取命令注册表
    command_registry = context.bot_data.get('command_registry')
    
    if not command_registry:
        await update.message.reply_text("系统尚未完全初始化，请稍后再试")
        return
    
    # 获取所有命令
    all_commands = command_registry.commands
    
    # 构建菜单消息
    menu_message = "📋 *所有可用命令*\n\n"
    
    # 按分类组织命令
    commands_by_category = {}
    for cmd_name, cmd in all_commands.items():
        if cmd.category not in commands_by_category:
            commands_by_category[cmd.category] = []
        commands_by_category[cmd.category].append(cmd)
    
    # 按分类添加到消息中
    for category, commands in commands_by_category.items():
        if commands:
            menu_message += f"*{category.value}*\n"
            
            for cmd in sorted(commands, key=lambda x: x.command):
                # 确定权限标记
                if cmd.required_role == UserRole.ADMIN:
                    permission_mark = "👑" 
                else:
                    permission_mark = "👤"
                    
                # 添加命令信息，并且转义下划线
                escaped_cmd = cmd.command.replace('_', '\\_')
                menu_message += f"{permission_mark} /{escaped_cmd} - {cmd.description}\n"
            
            menu_message += "\n"
    
    # 添加图例
    menu_message += "*图例:*\n"
    menu_message += "👑 - 需要管理员权限\n"
    menu_message += "👤 - 普通用户可用\n"
    
    # 发送菜单消息
    await update.message.reply_text(menu_message, parse_mode='Markdown')

def register_menu_command(command_registry: CommandRegistry):
    """注册menu命令
    
    Args:
        command_registry: 命令注册器实例
    """
    command_registry.register_command(
        CommandPlugin(
            command="menu",
            description="查看所有可用命令及权限",
            handler=menu_command,
            category=CommandCategory.MENU,
            required_role=UserRole.ADMIN
        )
    ) 