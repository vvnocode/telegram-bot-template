"""推送管理器"""
import asyncio
import importlib
import inspect
import os
from typing import Dict, List, Any

from telegram.ext import Application

from src.auth import UserManager
from src.push.interface import PushPluginInterface
from src.push.factory import plugin_factory
from src.logger import logger


class PushManager:
    """推送管理器，负责管理所有推送插件"""
    
    def __init__(self, user_manager: UserManager, config: Dict[str, Any] = None):
        """初始化推送管理器
        
        Args:
            user_manager: 用户管理器
            config: 配置字典
        """
        self.user_manager = user_manager
        self.config = config or {}
        self.plugins: Dict[str, PushPluginInterface] = {}
        self._app: Application = None
        
        # 从配置中获取推送插件配置
        push_config = self.config.get('push', {}) or {}
        self.enabled_plugins: List[str] = push_config.get('enabled', [])
        self.disabled_plugins: List[str] = push_config.get('disabled', [])
        self.plugins_config: Dict[str, Dict[str, Any]] = push_config.get('plugins', {})
        
    def discover_plugins(self) -> None:
        """发现所有推送插件"""
        logger.info("开始发现推送插件...")
        self._discover_internal_plugins()
        logger.info(f"推送插件发现完成，共找到 {len(plugin_factory.get_available_plugins())} 个推送插件")
    
    def _discover_internal_plugins(self) -> None:
        """发现内置推送插件"""
        try:
            logger.info("加载内置推送插件...")
            
            # 方法1：尝试直接导入已知的内置推送插件模块
            try:
                # 直接导入内置推送插件
                from src.push.plugins import ip_monitor, system_monitor
                
                internal_modules = [ip_monitor, system_monitor]
                for module in internal_modules:
                    self._register_plugins_from_module(module)
            except ImportError as e:
                logger.warning(f"导入内置推送插件模块失败: {str(e)}")
        
        except Exception as e:
            logger.error(f"发现内部推送插件时出错: {str(e)}", exc_info=True)
    
    def _register_plugins_from_module(self, module: Any) -> None:
        """从模块中注册推送插件到工厂
        
        Args:
            module: 模块对象
        """
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and 
                issubclass(obj, PushPluginInterface) and 
                obj is not PushPluginInterface):
                
                plugin_factory.register_plugin(obj)
    
    def load_plugins(self) -> None:
        """根据配置加载推送插件"""
        # 确保已经发现插件
        available_plugins = plugin_factory.get_available_plugins()
        if not available_plugins:
            self.discover_plugins()
            available_plugins = plugin_factory.get_available_plugins()
            
        logger.info("开始加载推送插件...")
        
        # 决定要加载哪些插件
        plugins_to_load = self._determine_plugins_to_load(list(available_plugins.keys()))
        
        # 准备插件配置
        plugin_configs = {}
        for plugin_name in plugins_to_load:
            plugin_configs[plugin_name] = self.plugins_config.get(plugin_name, {})
        
        # 使用工厂批量创建插件
        self.plugins = plugin_factory.create_plugins_batch(plugin_configs, self.user_manager)
        
        logger.info(f"推送插件加载完成，共加载 {len(self.plugins)} 个推送插件")
    
    def _determine_plugins_to_load(self, available_plugin_names: List[str]) -> set:
        """确定要加载的插件列表
        
        Args:
            available_plugin_names: 可用的插件名称列表
            
        Returns:
            set: 要加载的插件名称集合
        """
        # 如果没有配置，加载所有插件
        if not self.enabled_plugins and not self.disabled_plugins:
            logger.info("没有推送插件配置，将加载所有发现的推送插件")
            return set(available_plugin_names)
        
        # 如果配置了启用列表，只加载启用的插件
        if self.enabled_plugins:
            plugins_to_load = set(self.enabled_plugins)
            logger.info(f"根据启用配置，将加载 {len(plugins_to_load)} 个推送插件")
            
            # 验证插件是否存在
            for plugin_name in self.enabled_plugins:
                if plugin_name not in available_plugin_names:
                    logger.warning(f"启用的推送插件 {plugin_name} 不存在，将被忽略")
        else:
            # 如果只配置了禁用列表，加载除禁用外的所有插件
            plugins_to_load = set(available_plugin_names) - set(self.disabled_plugins)
            logger.info(f"根据禁用配置，将加载 {len(plugins_to_load)} 个推送插件")
        
        # 应用禁用列表
        if self.disabled_plugins:
            plugins_to_load -= set(self.disabled_plugins)
            logger.info(f"应用禁用配置后，将加载 {len(plugins_to_load)} 个推送插件")
        
        return plugins_to_load
    
    async def start_all_plugins(self, app: Application) -> None:
        """启动所有推送插件
        
        Args:
            app: Telegram应用实例
        """
        if not self.plugins:
            self.load_plugins()
        
        self._app = app
        logger.info("开始启动所有推送插件...")
        
        # 启动所有插件
        for plugin_name, plugin in self.plugins.items():
            try:
                await plugin.start(app)
                logger.info(f"成功启动推送插件: {plugin_name}")
            except Exception as e:
                logger.error(f"启动推送插件 {plugin_name} 时出错: {str(e)}", exc_info=True)
        
        logger.info("所有推送插件启动完成")
    
    async def stop_all_plugins(self) -> None:
        """停止所有推送插件"""
        logger.info("开始停止所有推送插件...")
        
        # 并发停止所有插件
        tasks = []
        for plugin_name, plugin in self.plugins.items():
            try:
                task = asyncio.create_task(plugin.stop())
                tasks.append(task)
            except Exception as e:
                logger.error(f"停止推送插件 {plugin_name} 时出错: {str(e)}", exc_info=True)
        
        # 等待所有停止任务完成
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info("所有推送插件已停止")
    
    def get_plugin(self, name: str) -> PushPluginInterface:
        """获取指定名称的推送插件
        
        Args:
            name: 插件名称
            
        Returns:
            推送插件实例
        
        Raises:
            KeyError: 如果插件不存在
        """
        if name not in self.plugins:
            raise KeyError(f"推送插件 {name} 不存在或未加载")
        return self.plugins[name]
    
    def get_all_plugins(self) -> Dict[str, PushPluginInterface]:
        """获取所有已加载的推送插件
        
        Returns:
            推送插件字典，键为插件名称，值为插件实例
        """
        return self.plugins
    
    def get_available_plugins_info(self) -> Dict[str, Dict[str, str]]:
        """获取所有可用插件的信息
        
        Returns:
            Dict[str, Dict[str, str]]: 插件信息字典
        """
        if not plugin_factory.get_available_plugins():
            self.discover_plugins()
        return plugin_factory.list_all_plugins_info()
    
    async def trigger_plugin(self, plugin_name: str) -> bool:
        """手动触发指定推送插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 是否触发成功
        """
        try:
            plugin = self.get_plugin(plugin_name)
            await plugin.trigger_check()
            logger.info(f"成功触发推送插件: {plugin_name}")
            return True
        except KeyError:
            logger.error(f"推送插件 {plugin_name} 不存在或未加载")
            return False
        except Exception as e:
            logger.error(f"触发推送插件 {plugin_name} 时出错: {str(e)}", exc_info=True)
            return False
    
    async def trigger_all_plugins(self) -> int:
        """手动触发所有推送插件
        
        Returns:
            int: 成功触发的插件数量
        """
        success_count = 0
        
        for plugin_name in self.plugins.keys():
            if await self.trigger_plugin(plugin_name):
                success_count += 1
        
        logger.info(f"批量触发推送插件完成，成功触发 {success_count}/{len(self.plugins)} 个插件")
        return success_count 