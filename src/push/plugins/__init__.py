"""推送插件包"""

# 导入所有推送插件
try:
    from .ip_monitor import IPMonitorPushPlugin
except ImportError as e:
    print(f"Warning: Failed to import IPMonitorPushPlugin: {e}")

try:
    from .system_monitor import SystemMonitorPushPlugin
except ImportError as e:
    print(f"Warning: Failed to import SystemMonitorPushPlugin: {e}")

__all__ = [
    'IPMonitorPushPlugin',
    'SystemMonitorPushPlugin'
] 