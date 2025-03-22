from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from src.auth import UserManager
from src.logger import logger
from src.bot.handlers.command import CommandPlugin, CommandCategory, CommandRegistry
from src.auth.permissions import UserRole

async def user_list_command(update: Update, context: ContextTypes.DEFAULT_TYPE, user_manager: UserManager):
    """处理/users命令，显示用户列表
    
    Args:
        update: Telegram更新对象
        context: 上下文对象
        user_manager: 用户管理器实例
    """
    
    # 获取所有用户列表
    users = user_manager.get_all_users()
    
    # 构建回复消息
    message = "📋 *用户列表*\n\n"
    
    # 显示管理员
    message += "*👑 管理员:*\n"
    if not users['admins']:
        message += "  _无管理员用户_\n"
    else:
        for i, admin_id in enumerate(users['admins'], 1):
            message += f"  {i}. `{admin_id}`\n"
    
    message += "\n*👤 普通用户:*\n"
    if not users['users']:
        message += "  _无普通用户_\n"
    else:
        for i, user_id in enumerate(users['users'], 1):
            message += f"  {i}. `{user_id}`\n"
    
    # 显示管理命令帮助
    message += "\n*🔧 用户管理命令:*\n"
    message += "  `/adduser <用户ID>` - 添加普通用户\n"
    message += "  `/deluser <用户ID>` - 删除普通用户\n"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def add_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE, user_manager: UserManager):
    """处理/adduser命令，添加普通用户
    
    Args:
        update: Telegram更新对象
        context: 上下文对象
        user_manager: 用户管理器实例
    """
    
    # 检查命令参数
    if not context.args or len(context.args) != 1:
        await update.message.reply_text("❌ 请提供用户ID\n用法: `/adduser <用户ID>`", parse_mode='Markdown')
        return
    
    user_id = context.args[0]
    
    # 添加用户
    if user_manager.add_user(user_id):
        logger.info(f"管理员 {update.effective_user.id} 添加了用户 {user_id}")
        await update.message.reply_text(f"✅ 已成功添加用户: `{user_id}`", parse_mode='Markdown')
    else:
        await update.message.reply_text(f"❌ 添加用户失败，可能该ID已存在或为管理员", parse_mode='Markdown')

async def remove_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE, user_manager: UserManager):
    """处理/deluser命令，删除普通用户
    
    Args:
        update: Telegram更新对象
        context: 上下文对象
        user_manager: 用户管理器实例
    """
    
    # 检查命令参数
    if not context.args or len(context.args) != 1:
        await update.message.reply_text("❌ 请提供用户ID\n用法: `/deluser <用户ID>`", parse_mode='Markdown')
        return
    
    user_id = context.args[0]
    
    # 删除用户
    if user_manager.remove_user(user_id):
        logger.info(f"管理员 {update.effective_user.id} 删除了用户 {user_id}")
        await update.message.reply_text(f"✅ 已成功删除用户: `{user_id}`", parse_mode='Markdown')
    else:
        await update.message.reply_text(f"❌ 删除用户失败，该ID可能不存在或不是普通用户", parse_mode='Markdown')

def register_user_commands(command_registry: CommandRegistry):
    """注册用户管理相关命令
    
    Args:
        command_registry: 命令注册器实例
    """
    # 用户列表命令
    command_registry.register_command(
        CommandPlugin(
            command="users",
            description="显示所有用户列表",
            handler=user_list_command,
            category=CommandCategory.USER,
            required_role=UserRole.ADMIN
        )
    )
    
    # 添加用户命令
    command_registry.register_command(
        CommandPlugin(
            command="adduser",
            description="添加普通用户",
            handler=add_user_command,
            category=CommandCategory.USER,
            required_role=UserRole.ADMIN
        )
    )
    
    # 删除用户命令
    command_registry.register_command(
        CommandPlugin(
            command="deluser",
            description="删除普通用户",
            handler=remove_user_command,
            category=CommandCategory.USER,
            required_role=UserRole.ADMIN
        )
    )
    