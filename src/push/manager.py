"""推送管理器"""
import asyncio
import importlib
import inspect
import os
from typing import Dict, List, Type, Any

from telegram.ext import Application

from src.auth import UserManager, UserRole
from src.push.interface import PushPluginInterface, PushConfig, PushFrequency
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
        self.all_plugin_classes: Dict[str, Type[PushPluginInterface]] = {}
        self._app: Application = None
        
        # 从配置中获取推送插件配置
        self.push_config = self.config.get('push', {}) or {}
        
    def discover_plugins(self) -> None:
        """发现所有推送插件"""
        logger.info("开始发现推送插件...")
        
        # 发现内置推送插件
        self._discover_internal_plugins()
        
        logger.info(f"推送插件发现完成，共找到 {len(self.all_plugin_classes)} 个推送插件")
    
    def _discover_internal_plugins(self) -> None:
        """发现内置推送插件"""
        try:
            logger.info("加载内置推送插件...")
            
            # 扫描推送插件目录
            plugins_dir = os.path.join(os.path.dirname(__file__), 'plugins')
            if os.path.exists(plugins_dir):
                for filename in os.listdir(plugins_dir):
                    if filename.endswith('.py') and filename != '__init__.py':
                        module_name = filename[:-3]
                        try:
                            module = importlib.import_module(f'src.push.plugins.{module_name}')
                            self._register_plugins_from_module(module, "内置推送")
                        except ImportError as e:
                            logger.warning(f"导入推送插件模块失败: {module_name}, 错误: {str(e)}")
        
        except Exception as e:
            logger.error(f"发现内部推送插件时出错: {str(e)}", exc_info=True)
    
    def _register_plugins_from_module(self, module: Any, source: str) -> None:
        """从模块中注册推送插件
        
        Args:
            module: 模块对象
            source: 插件来源描述
        """
        # 查找模块中继承自PushPluginInterface的所有类
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and 
                issubclass(obj, PushPluginInterface) and 
                obj is not PushPluginInterface):
                
                plugin_name = obj.name
                
                # 检查是否已存在同名插件
                if plugin_name in self.all_plugin_classes:
                    logger.warning(f"发现重复的推送插件名称: {plugin_name}，将忽略{source}插件")
                    continue
                
                self.all_plugin_classes[plugin_name] = obj
                logger.info(f"发现{source}插件: {plugin_name} ({obj.description})")
    
    def load_plugins(self) -> None:
        """根据配置加载推送插件"""
        if not self.all_plugin_classes:
            self.discover_plugins()
            
        logger.info("开始加载推送插件...")
        
        # 获取推送插件配置
        enabled_plugins = self.push_config.get('enabled', [])
        disabled_plugins = self.push_config.get('disabled', [])
        plugins_config = self.push_config.get('plugins', {})
        
        # 决定要加载哪些插件
        plugins_to_load = set()
        
        # 如果没有配置，加载所有插件
        if not enabled_plugins and not disabled_plugins:
            plugins_to_load = set(self.all_plugin_classes.keys())
            logger.info("没有推送插件配置，将加载所有发现的推送插件")
        
        # 如果配置了启用列表，只加载启用的插件
        elif enabled_plugins:
            plugins_to_load = set(enabled_plugins)
            logger.info(f"根据启用配置，将加载 {len(plugins_to_load)} 个推送插件")
        
        # 如果只配置了禁用列表，加载除禁用外的所有插件
        else:
            plugins_to_load = set(self.all_plugin_classes.keys()) - set(disabled_plugins)
            logger.info(f"根据禁用配置，将加载 {len(plugins_to_load)} 个推送插件")
        
        # 应用禁用列表
        if disabled_plugins:
            plugins_to_load -= set(disabled_plugins)
            logger.info(f"应用禁用配置后，将加载 {len(plugins_to_load)} 个推送插件")
        
        # 实例化和加载插件
        for plugin_name in plugins_to_load:
            if plugin_name not in self.all_plugin_classes:
                logger.warning(f"要加载的推送插件 {plugin_name} 不存在，将被忽略")
                continue
                
            try:
                plugin_class = self.all_plugin_classes[plugin_name]
                
                # 获取插件特定配置
                plugin_config_data = plugins_config.get(plugin_name, {})
                
                # 创建推送配置对象
                push_config = self._create_push_config(plugin_config_data)
                
                # 实例化插件
                plugin = plugin_class(self.user_manager, push_config)
                self.plugins[plugin_name] = plugin
                logger.info(f"成功加载推送插件: {plugin_name} ({plugin.description})")
            except Exception as e:
                logger.error(f"实例化推送插件 {plugin_name} 时出错: {str(e)}", exc_info=True)
        
        logger.info(f"推送插件加载完成，共加载 {len(self.plugins)} 个推送插件")
    
    def _create_push_config(self, config_data: Dict[str, Any]) -> PushConfig:
        """创建推送配置对象
        
        Args:
            config_data: 配置数据字典
            
        Returns:
            PushConfig: 推送配置对象
        """
        push_config = PushConfig()
        
        # 应用配置
        push_config.enabled = config_data.get('enabled', True)
        
        # 解析频率
        frequency_str = config_data.get('frequency', 'event')
        try:
            push_config.frequency = PushFrequency(frequency_str)
        except ValueError:
            logger.warning(f"无效的推送频率: {frequency_str}，使用默认值 event")
            push_config.frequency = PushFrequency.EVENT
        
        push_config.interval_seconds = config_data.get('interval_seconds', 300)
        push_config.cron_expression = config_data.get('cron_expression', '')
        
        # 解析目标角色
        target_role = UserRole.ADMIN  # 默认仅管理员
        
        # 新的配置方式：target_role
        if 'target_role' in config_data:
            role_name = config_data['target_role'].lower()
            if role_name == 'admin':
                target_role = UserRole.ADMIN  # 仅管理员
            elif role_name == 'user':
                target_role = UserRole.USER   # 所有用户（管理员+普通用户）
            else:
                logger.warning(f"未知的用户角色: {role_name}，使用默认值 admin")
        
        push_config.target_role = target_role
        push_config.custom_targets = config_data.get('custom_targets', [])
        
        return push_config
    
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
        
        # 停止所有插件
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
            PushPluginInterface: 推送插件实例
        """
        return self.plugins.get(name)
    
    def get_all_plugins(self) -> Dict[str, PushPluginInterface]:
        """获取所有推送插件
        
        Returns:
            Dict[str, PushPluginInterface]: 所有推送插件字典
        """
        return self.plugins.copy()
    
    async def trigger_plugin(self, plugin_name: str) -> bool:
        """手动触发指定推送插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 是否触发成功
        """
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            logger.error(f"推送插件 {plugin_name} 不存在")
            return False
        
        try:
            await plugin.trigger_check()
            return True
        except Exception as e:
            logger.error(f"触发推送插件 {plugin_name} 时出错: {str(e)}", exc_info=True)
            return False
    
    async def trigger_all_plugins(self) -> int:
        """手动触发所有推送插件
        
        Returns:
            int: 成功触发的插件数量
        """
        success_count = 0
        
        for plugin_name in self.plugins:
            if await self.trigger_plugin(plugin_name):
                success_count += 1
        
        return success_count 