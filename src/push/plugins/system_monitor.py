"""系统监控推送插件"""
import psutil
import shutil
from datetime import datetime
from typing import Optional, Dict, Any

from src.auth import UserManager, UserRole
from src.push.interface import PushPluginInterface, PushConfig, PushFrequency
from src.logger import logger


class SystemMonitorPushPlugin(PushPluginInterface):
    """系统监控推送插件，监控CPU、内存、磁盘使用率"""
    name = "system_monitor"
    description = "系统资源监控推送"
    version = "1.0.0"
    
    def __init__(self, user_manager: UserManager, default_config: PushConfig = None):
        """初始化系统监控推送插件
        
        Args:
            user_manager: 用户管理器
            default_config: 默认配置，如果为None则使用插件自定义默认配置
        """
        # 如果没有传入默认配置，创建插件的自定义默认配置
        if default_config is None:
            default_config = PushConfig(
                enabled=True,
                frequency=PushFrequency.INTERVAL,
                interval_seconds=600,  # 10分钟检查一次
                target_role=UserRole.ADMIN,  # 默认只推送给管理员
                custom_targets=[]
            )
        
        super().__init__(user_manager, default_config)
        
        # 默认阈值配置
        self.cpu_threshold = 80.0      # CPU使用率阈值(%)
        self.memory_threshold = 80.0   # 内存使用率阈值(%)
        self.disk_threshold = 90.0     # 磁盘使用率阈值(%)
    
    def configure(self, config_data: Dict[str, Any]) -> None:
        """配置插件
        
        Args:
            config_data: 配置数据字典
        """
        # 先调用父类的配置方法处理基础配置
        super().configure(config_data)
        
        # 然后处理插件特有的配置
        if 'cpu_threshold' in config_data:
            self.cpu_threshold = config_data['cpu_threshold']
        if 'memory_threshold' in config_data:
            self.memory_threshold = config_data['memory_threshold']
        if 'disk_threshold' in config_data:
            self.disk_threshold = config_data['disk_threshold']
        
        logger.info(f"系统监控: 配置阈值 - CPU: {self.cpu_threshold}%, 内存: {self.memory_threshold}%, 磁盘: {self.disk_threshold}%")
    
    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息
        
        Returns:
            Dict[str, Any]: 系统统计信息
        """
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # 磁盘使用率
            disk = shutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # 负载平均值（如果可用）
            load_avg = None
            try:
                load_avg = psutil.getloadavg()
            except AttributeError:
                # Windows系统不支持getloadavg
                pass
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'memory_total': memory.total,
                'memory_used': memory.used,
                'disk_percent': disk_percent,
                'disk_total': disk.total,
                'disk_used': disk.used,
                'load_avg': load_avg,
                'check_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            logger.error(f"系统监控: 获取系统统计信息失败: {str(e)}")
            return {}
    
    async def check_condition(self) -> tuple[bool, Optional[str]]:
        """检查系统资源使用情况
        
        Returns:
            tuple[bool, Optional[str]]: (是否需要推送, 推送消息)
        """
        try:
            stats = self.get_system_stats()
            if not stats:
                return False, None
            
            alerts = []
            
            # 检查CPU使用率
            cpu_percent = stats.get('cpu_percent', 0)
            if cpu_percent > self.cpu_threshold:
                alerts.append(f"🔥 CPU使用率过高: {cpu_percent:.1f}%")
            
            # 检查内存使用率
            memory_percent = stats.get('memory_percent', 0)
            if memory_percent > self.memory_threshold:
                alerts.append(f"🧠 内存使用率过高: {memory_percent:.1f}%")
            
            # 检查磁盘使用率
            disk_percent = stats.get('disk_percent', 0)
            if disk_percent > self.disk_threshold:
                alerts.append(f"💾 磁盘使用率过高: {disk_percent:.1f}%")
            
            # 如果有告警，生成推送消息
            if alerts:
                message = self.get_message({'stats': stats, 'alerts': alerts})
                return True, message
            
            return False, None
            
        except Exception as e:
            logger.error(f"系统监控: 检查条件时出错: {str(e)}", exc_info=True)
            return False, None
    
    def get_message(self, data: Any = None) -> str:
        """获取推送消息内容
        
        Args:
            data: 系统统计信息和告警
            
        Returns:
            str: 推送消息
        """
        if not data or not isinstance(data, dict):
            return "⚠️ 系统监控: 无数据"
        
        stats = data.get('stats', {})
        alerts = data.get('alerts', [])
        
        if not stats:
            return "⚠️ 系统监控: 获取系统信息失败"
        
        # 格式化内存和磁盘大小
        def format_bytes(bytes_value):
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if bytes_value < 1024.0:
                    return f"{bytes_value:.1f} {unit}"
                bytes_value /= 1024.0
            return f"{bytes_value:.1f} PB"
        
        message = f"""⚠️ **系统资源告警**

🚨 **告警信息**:
{chr(10).join(f"• {alert}" for alert in alerts)}

📊 **当前系统状态**:
🔥 **CPU使用率**: {stats.get('cpu_percent', 0):.1f}%
🧠 **内存使用率**: {stats.get('memory_percent', 0):.1f}% ({format_bytes(stats.get('memory_used', 0))}/{format_bytes(stats.get('memory_total', 0))})
💾 **磁盘使用率**: {stats.get('disk_percent', 0):.1f}% ({format_bytes(stats.get('disk_used', 0))}/{format_bytes(stats.get('disk_total', 0))})"""
        
        # 添加负载平均值（如果可用）
        load_avg = stats.get('load_avg')
        if load_avg:
            message += f"\n⚖️ **负载平均值**: {load_avg[0]:.2f}, {load_avg[1]:.2f}, {load_avg[2]:.2f}"
        
        message += f"\n\n⏰ **检查时间**: {stats.get('check_time', '未知')}\n🤖 *来自系统监控的自动推送*"
        
        return message 