"""插件加载器"""
import importlib
import inspect
import os
import sys
from typing import Dict, List, Type, Set, Any

from telegram import BotCommand
from telegram.ext import Application

from src.auth import UserManager
from src.bot.plugins.interface import PluginInterface
from src.logger import logger


class PluginLoader:
    """插件加载器"""
    def __init__(self, user_manager: UserManager, config: Dict[str, Any]):
        """初始化插件加载器
        
        Args:
            user_manager: 用户管理器
            config: 配置字典
        """
        self.user_manager = user_manager
        self.config = config
        self.plugins: Dict[str, PluginInterface] = {}
        self.all_plugin_classes: Dict[str, Type[PluginInterface]] = {}
        
        # 从配置中获取插件启用和禁用列表
        plugin_config = config.get('plugins', {})
        self.enabled_plugins: List[str] = plugin_config.get('enabled', [])
        self.disabled_plugins: List[str] = plugin_config.get('disabled', [])
    
    def discover_plugins(self) -> None:
        """发现所有可用插件"""
        logger.info("开始发现插件...")
        
        # 获取插件目录路径
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 遍历插件目录中的所有文件
        for filename in os.listdir(plugin_dir):
            # 忽略非Python文件和特殊文件
            if not filename.endswith('.py') or filename.startswith('__') or filename in ['interface.py', 'loader.py']:
                continue
                
            module_name = filename[:-3]  # 去掉.py扩展名
            full_module_path = f"src.bot.plugins.{module_name}"
            
            try:
                # 动态导入模块
                module = importlib.import_module(full_module_path)
                
                # 查找模块中继承自PluginInterface的所有类
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, PluginInterface) and 
                        obj is not PluginInterface):
                        
                        plugin_name = obj.name
                        self.all_plugin_classes[plugin_name] = obj
                        logger.info(f"发现插件: {plugin_name} ({obj.description})")
            
            except Exception as e:
                logger.error(f"加载插件模块 {full_module_path} 时出错: {str(e)}", exc_info=True)
        
        logger.info(f"插件发现完成，共找到 {len(self.all_plugin_classes)} 个插件")
    
    def load_plugins(self) -> None:
        """根据配置加载插件"""
        if not self.all_plugin_classes:
            self.discover_plugins()
            
        logger.info("开始加载插件...")
        
        # 决定要加载哪些插件
        plugins_to_load: Set[str] = set()
        
        # 如果没有配置，加载所有插件
        if not self.enabled_plugins and not self.disabled_plugins:
            plugins_to_load = set(self.all_plugin_classes.keys())
            logger.info("没有插件配置，将加载所有发现的插件")
        
        # 如果配置了启用列表，只加载启用的插件
        elif self.enabled_plugins:
            plugins_to_load = set(self.enabled_plugins)
            logger.info(f"根据启用配置，将加载 {len(plugins_to_load)} 个插件")
            
            # 验证所有启用的插件是否存在
            for plugin_name in self.enabled_plugins:
                if plugin_name not in self.all_plugin_classes:
                    logger.warning(f"启用的插件 {plugin_name} 不存在，将被忽略")
        
        # 如果只配置了禁用列表，加载除禁用外的所有插件
        else:
            plugins_to_load = set(self.all_plugin_classes.keys()) - set(self.disabled_plugins)
            logger.info(f"根据禁用配置，将加载 {len(plugins_to_load)} 个插件")
        
        # 应用禁用列表（如果同时配置了启用和禁用列表）
        if self.disabled_plugins:
            plugins_to_load -= set(self.disabled_plugins)
            logger.info(f"应用禁用配置后，将加载 {len(plugins_to_load)} 个插件")
        
        # 实例化和加载插件
        for plugin_name in plugins_to_load:
            if plugin_name not in self.all_plugin_classes:
                logger.warning(f"要加载的插件 {plugin_name} 不存在，将被忽略")
                continue
                
            try:
                plugin_class = self.all_plugin_classes[plugin_name]
                plugin = plugin_class(self.user_manager)
                self.plugins[plugin_name] = plugin
                logger.info(f"成功加载插件: {plugin_name} ({plugin.description})")
            except Exception as e:
                logger.error(f"实例化插件 {plugin_name} 时出错: {str(e)}", exc_info=True)
        
        logger.info(f"插件加载完成，共加载 {len(self.plugins)} 个插件")
    
    def setup_plugins(self, app: Application) -> None:
        """设置所有已加载的插件
        
        Args:
            app: Telegram应用实例
        """
        if not self.plugins:
            self.load_plugins()
            
        logger.info("开始设置插件...")
        
        # 存储插件管理器到应用数据中
        app.bot_data['plugin_loader'] = self
        
        # 为每个插件调用setup方法
        for plugin_name, plugin in self.plugins.items():
            try:
                plugin.setup(app)
                logger.info(f"成功设置插件: {plugin_name}")
            except Exception as e:
                logger.error(f"设置插件 {plugin_name} 时出错: {str(e)}", exc_info=True)
        
        logger.info("所有插件设置完成")
    
    async def setup_bot_commands(self, app: Application) -> None:
        """设置机器人命令列表
        
        Args:
            app: Telegram应用实例
        """
        if not app.bot:
            logger.error("尝试设置机器人命令列表，但机器人尚未初始化")
            return
            
        # 收集所有插件的命令
        commands: List[BotCommand] = []
        
        for plugin in self.plugins.values():
            try:
                plugin_commands = plugin.get_bot_commands()
                commands.extend(plugin_commands)
            except Exception as e:
                logger.error(f"获取插件 {plugin.name} 的命令时出错: {str(e)}", exc_info=True)
        
        if not commands:
            logger.warning("没有命令可以设置")
            return
            
        # 设置机器人命令
        try:
            await app.bot.set_my_commands(
                commands=commands,
                language_code="zh"  # 中文
            )
            logger.info(f"成功设置机器人命令，共 {len(commands)} 个命令")
        except Exception as e:
            logger.error(f"设置机器人命令时出错: {str(e)}", exc_info=True)
    
    def get_plugin(self, name: str) -> PluginInterface:
        """获取指定名称的插件
        
        Args:
            name: 插件名称
            
        Returns:
            插件实例
        
        Raises:
            KeyError: 如果插件不存在
        """
        if name not in self.plugins:
            raise KeyError(f"插件 {name} 不存在或未加载")
        return self.plugins[name]
    
    def get_all_plugins(self) -> Dict[str, PluginInterface]:
        """获取所有已加载的插件
        
        Returns:
            插件字典，键为插件名称，值为插件实例
        """
        return self.plugins 