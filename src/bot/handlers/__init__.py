from telegram.ext import Application
from src.auth import UserManager
from src.logger import logger
from src.bot.handlers.command import CommandRegistry
from src.utils import UserStatsManager
import os
# import asyncio
# import importlib
import inspect
# import pkgutil
from typing import List, Callable, Any, Dict

# 导入所有处理器模块
from . import start, help, status, user, menu, stats, ip

def register_handlers(app: Application, user_manager: UserManager, stats_manager: UserStatsManager) -> None:
    """注册所有命令处理器
    
    Args:
        app: Telegram应用实例
        user_manager: 用户管理器实例
        stats_manager: 统计管理器实例
    """
    logger.info("注册命令处理器...")
    
    # 创建命令注册表
    command_registry = CommandRegistry(user_manager)
    
    # 自动发现和注册命令
    auto_register_commands(command_registry)
    
    # 尝试从配置文件加载命令配置
    commands_config_path = "config/commands.yaml"
    if os.path.exists(commands_config_path):
        try:
            command_registry.load_commands_from_config(commands_config_path)
            logger.info(f"从 {commands_config_path} 加载了命令配置")
        except Exception as e:
            logger.warning(f"加载命令配置文件失败: {str(e)}")
    else:
        logger.info(f"命令配置文件 {commands_config_path} 不存在，使用默认配置")
    
    # 设置命令处理器
    command_registry.setup_command_handlers(app)
    
    # 将命令注册表和统计管理器添加到bot_data中，以便其他处理器访问
    app.bot_data['command_registry'] = command_registry
    app.bot_data['stats_manager'] = stats_manager
    
    logger.info("命令处理器注册完成")
    
    # 异步设置机器人命令列表
    async def setup_bot_commands():
        await command_registry.setup_bot_commands()
    
    # 尝试使用job_queue，如果不可用则直接运行
    if hasattr(app, 'job_queue') and app.job_queue is not None:
        app.job_queue.run_once(lambda _: setup_bot_commands(), 1)
        logger.info("已将命令菜单设置任务添加到队列")
    else:
        # 如果job_queue不可用，创建一个任务来执行setup_bot_commands
        logger.warning("JobQueue不可用，将在应用启动后直接设置命令菜单")
        
        # 注册应用启动处理器
        async def post_init(application: Application):
            logger.info("应用启动后设置命令菜单")
            await setup_bot_commands()
        
        app.post_init = post_init

def auto_register_commands(command_registry: CommandRegistry) -> None:
    """自动发现和注册所有命令
    
    Args:
        command_registry: 命令注册表实例
    """
    modules = [start, help, status, user, menu, stats, ip]
    registered_count = 0
    
    for module in modules:
        # 查找模块中的所有函数
        for name, func in inspect.getmembers(module, inspect.isfunction):
            # 查找命令注册函数
            if name.startswith('register_') and name.endswith(('_command', '_commands')):
                try:
                    # 调用注册函数
                    func(command_registry)
                    registered_count += 1
                    logger.debug(f"通过函数 {name} 注册了命令")
                except Exception as e:
                    logger.error(f"调用注册函数 {name} 时出错: {str(e)}")
    
    logger.info(f"自动注册了 {registered_count} 个模块的命令")
