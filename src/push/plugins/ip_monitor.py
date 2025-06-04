"""IP地址监控推送插件"""
import subprocess
import json
import os
import ipaddress
from datetime import datetime
from typing import Optional, Dict, Any

from src.auth import UserManager, UserRole
from src.push.interface import PushPluginInterface, PushConfig, PushFrequency
from src.logger import logger
from src.utils.ip_utils import IPUtils

class IPMonitorPushPlugin(PushPluginInterface):
    """IP地址监控推送插件，当IP地址发生变化时推送通知"""
    name = "ip_monitor"
    description = "IP地址变化监控推送"
    version = "1.0.0"
    
    def __init__(self, user_manager: UserManager, default_config: PushConfig = None):
        """初始化IP监控推送插件
        
        Args:
            user_manager: 用户管理器
            default_config: 默认配置，如果为None则使用插件自定义默认配置
        """
        # 如果没有传入默认配置，创建插件的自定义默认配置
        if default_config is None:
            default_config = PushConfig(
                enabled=True,
                frequency=PushFrequency.INTERVAL,
                interval_seconds=300,  # 5分钟检查一次
                target_role=UserRole.USER,
                custom_targets=[]
            )
        
        super().__init__(user_manager, default_config)
        
        # IP状态文件路径
        self.ip_state_file = os.path.join('data', 'records', 'ip_monitor_state.json')
        
        # 确保数据目录存在
        data_dir = os.path.dirname(self.ip_state_file)
        os.makedirs(data_dir, exist_ok=True)
        
        # 上次记录的IP信息
        self.last_ip_info: Optional[Dict[str, Any]] = None
        
        # 加载上次保存的IP状态
        self._load_last_ip_state()
    
    def _load_last_ip_state(self) -> None:
        """加载上次保存的IP状态"""
        try:
            if os.path.exists(self.ip_state_file):
                with open(self.ip_state_file, 'r', encoding='utf-8') as f:
                    self.last_ip_info = json.load(f)
                    logger.info(f"IP监控: 加载上次IP状态 - {self.last_ip_info}")
        except Exception as e:
            logger.error(f"IP监控: 加载IP状态文件失败: {str(e)}")
            self.last_ip_info = None
    
    def _save_ip_state(self, ip_info: Dict[str, Any]) -> None:
        """保存当前IP状态
        
        Args:
            ip_info: IP信息字典
        """
        try:
            # 确保目录存在
            data_dir = os.path.dirname(self.ip_state_file)
            os.makedirs(data_dir, exist_ok=True)
            
            with open(self.ip_state_file, 'w', encoding='utf-8') as f:
                json.dump(ip_info, f, ensure_ascii=False, indent=2)
            logger.info(f"IP监控: 保存IP状态 - {ip_info}")
        except Exception as e:
            logger.error(f"IP监控: 保存IP状态文件失败: {str(e)}")
    
    def get_current_ip(self) -> Optional[str]:
        """获取当前IP地址
        
        Returns:
            Optional[str]: 当前IP地址，获取失败时返回None
        """
        try:
            return IPUtils.get_current_ip()
        except Exception as e:
            logger.error(f"IP监控: 调用IP工具失败: {str(e)}")
            return None
    
    def _is_valid_ip(self, ip: str) -> bool:
        """验证IP地址格式
        
        Args:
            ip: IP地址字符串
            
        Returns:
            bool: 是否为有效IP地址
        """
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    async def check_condition(self) -> tuple[bool, Optional[str]]:
        """检查IP变化条件
        
        Returns:
            tuple[bool, Optional[str]]: (是否需要推送, 推送消息)
        """
        try:
            current_ip = self.get_current_ip()
            if not current_ip:
                logger.warning("IP监控: 无法获取当前IP地址")
                return False, None
            
            current_time = datetime.now()
            current_ip_info = {
                'ip': current_ip,
                'check_time': current_time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 如果没有上次记录的IP信息，这是第一次运行
            if not self.last_ip_info:
                logger.info(f"IP监控: 首次运行，记录当前IP: {current_ip}")
                self._save_ip_state(current_ip_info)
                self.last_ip_info = current_ip_info
                
                # 首次运行时发送当前IP信息
                message = self.get_message(current_ip_info)
                message = f"🔍 **IP监控首次启动**\n\n{message}"
                return True, message
            
            # 检查IP是否发生变化
            last_ip = self.last_ip_info.get('ip')
            if current_ip != last_ip:
                logger.info(f"IP监控: 检测到IP变化 {last_ip} -> {current_ip}")
                
                # 保存新的IP状态
                self._save_ip_state(current_ip_info)
                
                # 准备变化信息
                change_info = {
                    'old_ip': last_ip,
                    'new_ip': current_ip,
                    'old_time': self.last_ip_info.get('check_time', '未知'),
                    'new_time': current_ip_info['check_time']
                }
                
                self.last_ip_info = current_ip_info
                
                # 生成变化消息
                message = self.get_message(change_info)
                return True, message
            
            # IP没有变化，更新时间戳
            self.last_ip_info['check_time'] = current_time.strftime('%Y-%m-%d %H:%M:%S')
            self._save_ip_state(self.last_ip_info)
            
            logger.debug(f"IP监控: IP未变化，当前IP: {current_ip}")
            return False, None
            
        except Exception as e:
            logger.error(f"IP监控: 检查IP条件时出错: {str(e)}", exc_info=True)
            return False, None
    
    def get_message(self, data: Any = None) -> str:
        """获取推送消息内容
        
        Args:
            data: IP变化信息或当前IP信息
            
        Returns:
            str: 推送消息
        """
        if not data:
            return "📡 IP监控: 无数据"
        
        # 如果是IP变化信息
        if isinstance(data, dict) and 'old_ip' in data:
            return f"""🔄 **IP地址发生变化**

📍 **旧IP地址**: `{data['old_ip']}`
📍 **新IP地址**: `{data['new_ip']}`

⏰ **变化时间**: {data['new_time']}
⏰ **上次记录**: {data['old_time']}

🤖 *来自IP监控系统的自动推送*"""
            
        # 如果是当前IP信息  
        elif isinstance(data, dict) and 'ip' in data:
            return f"""📡 **当前IP地址信息**

📍 **IP地址**: `{data['ip']}`
⏰ **检查时间**: {data['check_time']}

🤖 *来自IP监控系统的自动推送*"""
            
        else:
            return f"📡 IP监控: {str(data)}"