"""推送插件工厂"""
from typing import Dict, Type, Any, Optional

from src.auth import UserManager
from src.push.interface import PushPluginInterface, PushConfig
from src.logger import logger


class PushPluginFactory:
    """推送插件工厂类，负责创建和配置推送插件实例"""
    
    def __init__(self):
        """初始化工厂"""
        self._plugin_classes: Dict[str, Type[PushPluginInterface]] = {}
    
    def register_plugin(self, plugin_class: Type[PushPluginInterface]) -> None:
        """注册插件类
        
        Args:
            plugin_class: 插件类
        """
        plugin_name = plugin_class.name
        
        if plugin_name in self._plugin_classes:
            logger.warning(f"推送插件工厂: 插件 {plugin_name} 已存在，将被覆盖")
        
        self._plugin_classes[plugin_name] = plugin_class
        logger.info(f"推送插件工厂: 注册插件 {plugin_name} ({plugin_class.description})")
    
    def get_available_plugins(self) -> Dict[str, Type[PushPluginInterface]]:
        """获取所有可用的插件类
        
        Returns:
            Dict[str, Type[PushPluginInterface]]: 插件名称到插件类的映射
        """
        return self._plugin_classes.copy()
    
    def create_plugin(self, plugin_name: str, user_manager: UserManager, 
                     config: Optional[Dict[str, Any]] = None,
                     default_config: Optional[PushConfig] = None) -> Optional[PushPluginInterface]:
        """创建插件实例
        
        Args:
            plugin_name: 插件名称
            user_manager: 用户管理器
            config: 插件配置，可选
            default_config: 默认配置，可选
            
        Returns:
            Optional[PushPluginInterface]: 插件实例，如果创建失败返回None
        """
        if plugin_name not in self._plugin_classes:
            logger.error(f"推送插件工厂: 未知的插件名称 {plugin_name}")
            return None
        
        try:
            plugin_class = self._plugin_classes[plugin_name]
            # 传入默认配置创建插件实例
            plugin = plugin_class(user_manager, default_config)
            
            # 如果提供了配置，应用配置覆盖默认值
            if config:
                plugin.configure(config)
            
            logger.info(f"推送插件工厂: 成功创建插件 {plugin_name}")
            return plugin
            
        except Exception as e:
            logger.error(f"推送插件工厂: 创建插件 {plugin_name} 失败: {str(e)}", exc_info=True)
            return None
    
    def create_plugins_batch(self, plugin_configs: Dict[str, Dict[str, Any]], 
                           user_manager: UserManager,
                           default_configs: Optional[Dict[str, PushConfig]] = None) -> Dict[str, PushPluginInterface]:
        """批量创建插件实例
        
        Args:
            plugin_configs: 插件配置字典，格式为 {plugin_name: config}
            user_manager: 用户管理器
            default_configs: 默认配置字典，格式为 {plugin_name: default_config}，可选
            
        Returns:
            Dict[str, PushPluginInterface]: 成功创建的插件实例字典
        """
        plugins = {}
        default_configs = default_configs or {}
        
        for plugin_name, config in plugin_configs.items():
            default_config = default_configs.get(plugin_name)
            plugin = self.create_plugin(plugin_name, user_manager, config, default_config)
            if plugin:
                plugins[plugin_name] = plugin
        
        logger.info(f"推送插件工厂: 批量创建完成，成功创建 {len(plugins)}/{len(plugin_configs)} 个插件")
        return plugins
    
    def is_plugin_available(self, plugin_name: str) -> bool:
        """检查插件是否可用
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 插件是否可用
        """
        return plugin_name in self._plugin_classes
    
    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, str]]:
        """获取插件信息
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            Optional[Dict[str, str]]: 插件信息，包含name、description、version
        """
        if plugin_name not in self._plugin_classes:
            return None
        
        plugin_class = self._plugin_classes[plugin_name]
        return {
            'name': plugin_class.name,
            'description': plugin_class.description,
            'version': plugin_class.version
        }
    
    def list_all_plugins_info(self) -> Dict[str, Dict[str, str]]:
        """列出所有插件的信息
        
        Returns:
            Dict[str, Dict[str, str]]: 插件信息字典
        """
        result = {}
        for plugin_name in self._plugin_classes:
            result[plugin_name] = self.get_plugin_info(plugin_name)
        return result


# 全局插件工厂实例
plugin_factory = PushPluginFactory() 