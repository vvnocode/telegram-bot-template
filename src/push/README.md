# 推送模块 (Push Module)

## 概述

推送模块采用插件式架构设计，支持多种推送插件，可以灵活配置和扩展。本模块参考了bot插件的设计模式，采用了工厂模式和策略模式，使代码更加清晰和易于维护。

**新特性**: 插件可以定义自己的默认配置，config.yaml中的配置会覆盖这些默认值，实现了更灵活的配置机制。

## 架构设计

### 核心组件

1. **PushPluginInterface** - 推送插件接口
2. **PushManager** - 推送管理器
3. **PushPluginFactory** - 推送插件工厂
4. **PushConfig** - 推送配置类

### 设计模式

- **插件模式**: 支持动态加载和配置推送插件
- **工厂模式**: 统一管理插件的创建和配置
- **策略模式**: 支持不同的推送策略和频率
- **观察者模式**: 事件驱动的推送机制
- **默认配置模式**: 插件提供默认配置，外部配置覆盖默认值

## 配置说明

### 基本配置

```yaml
push:
  # 启用的插件列表 (如果为空则加载所有插件)
  enabled:
    - ip_monitor
    - system_monitor
  
  # 禁用的插件列表
  disabled: []
  
  # 插件具体配置 (可选，覆盖插件默认配置)
  plugins:
    ip_monitor:
      # 只需要配置想要修改的值，其他使用插件默认值
      interval_seconds: 180  # 覆盖默认的300秒
      target_role: user      # 覆盖默认的admin
    
    system_monitor:
      interval_seconds: 300   # 覆盖默认的600秒
      cpu_threshold: 85.0     # 覆盖默认的80.0%
      memory_threshold: 90.0  # 覆盖默认的80.0%
      # disk_threshold 使用插件默认值90.0%
```

### 配置覆盖机制

1. **插件默认配置**: 每个插件在初始化时定义自己的默认配置
2. **外部配置覆盖**: config.yaml中的配置会覆盖对应的默认值
3. **选择性覆盖**: 只需要配置想要修改的参数，其他保持默认

### 配置参数说明

- **enabled**: 插件是否启用
- **frequency**: 推送频率
  - `once`: 一次性推送
  - `interval`: 间隔推送
  - `cron`: 定时推送（暂未实现）
  - `event`: 事件触发推送
- **interval_seconds**: 间隔秒数（frequency为interval时有效）
- **target_role**: 目标用户角色
  - `admin`: 仅管理员
  - `user`: 所有用户
- **custom_targets**: 自定义推送目标用户ID列表

## 内置插件

### 1. IP监控插件 (ip_monitor)

监控服务器IP地址变化，当IP发生变化时推送通知。

**默认配置**:
- enabled: True
- frequency: interval
- interval_seconds: 300 (5分钟)
- target_role: admin
- custom_targets: []

**特性**:
- 首次启动时推送当前IP
- IP变化时推送变化通知
- 支持多种IP获取命令
- 状态持久化存储

### 2. 系统监控插件 (system_monitor)

监控系统资源使用情况，当超过阈值时推送告警。

**默认配置**:
- enabled: True
- frequency: interval
- interval_seconds: 600 (10分钟)
- target_role: admin
- custom_targets: []
- cpu_threshold: 80.0%
- memory_threshold: 80.0%
- disk_threshold: 90.0%

**特性**:
- CPU使用率监控
- 内存使用率监控
- 磁盘使用率监控
- 负载平均值监控（Linux）
- 可配置告警阈值

## 开发新插件

### 1. 创建插件类

```python
from src.auth import UserManager, UserRole
from src.push.interface import PushPluginInterface, PushConfig, PushFrequency
from typing import Optional, Any

class MyPushPlugin(PushPluginInterface):
    """我的推送插件"""
    name = "my_plugin"
    description = "我的自定义推送插件"
    version = "1.0.0"
    
    def __init__(self, user_manager: UserManager, default_config: PushConfig = None):
        # 定义插件的默认配置
        if default_config is None:
            default_config = PushConfig(
                enabled=True,
                frequency=PushFrequency.INTERVAL,
                interval_seconds=600,  # 默认10分钟
                target_role=UserRole.ADMIN,
                custom_targets=[]
            )
        
        super().__init__(user_manager, default_config)
        
        # 插件特有的配置
        self.my_threshold = 50.0
    
    def configure(self, config_data: Dict[str, Any]) -> None:
        """配置插件，处理外部配置覆盖"""
        # 先处理基础配置
        super().configure(config_data)
        
        # 处理插件特有配置
        if 'my_threshold' in config_data:
            self.my_threshold = config_data['my_threshold']
    
    async def check_condition(self) -> tuple[bool, Optional[str]]:
        """检查推送条件"""
        # 实现你的检查逻辑
        should_push = True  # 你的条件判断
        if should_push:
            message = self.get_message({"status": "alert"})
            return True, message
        return False, None
    
    def get_message(self, data: Any = None) -> str:
        """获取推送消息内容"""
        return f"📢 我的插件推送消息: {data}"
```

### 2. 插件放置

将插件文件放置在 `src/push/plugins/` 目录下，文件名为 `my_plugin.py`。

### 3. 配置插件（可选）

在配置文件中添加插件配置来覆盖默认值:

```yaml
push:
  enabled:
    - my_plugin
  plugins:
    my_plugin:
      # 只配置需要修改的参数
      interval_seconds: 300  # 覆盖默认的600秒
      my_threshold: 75.0     # 覆盖默认的50.0
      # 其他参数使用插件默认值
```

## 配置示例

### 最小配置（使用所有默认值）

```yaml
push:
  enabled:
    - ip_monitor
    - system_monitor
  # 不需要plugins配置，使用插件默认值
```

### 部分覆盖配置

```yaml
push:
  enabled:
    - ip_monitor
    - system_monitor
  plugins:
    ip_monitor:
      interval_seconds: 120  # 只修改检查间隔
    system_monitor:
      cpu_threshold: 90.0    # 只修改CPU阈值
```

### 完整自定义配置

```yaml
push:
  enabled:
    - ip_monitor
    - system_monitor
  plugins:
    ip_monitor:
      enabled: true
      frequency: interval
      interval_seconds: 300
      target_role: admin
      custom_targets: []
    
    system_monitor:
      enabled: true
      frequency: interval
      interval_seconds: 300
      target_role: user
      cpu_threshold: 85.0
      memory_threshold: 85.0
      disk_threshold: 95.0
```

## 使用方法

### 在机器人中使用

```python
from src.push import PushManager

# 创建推送管理器
push_manager = PushManager(user_manager, config)

# 启动推送插件
await push_manager.start_all_plugins(app)

# 手动触发插件
await push_manager.trigger_plugin("ip_monitor")

# 停止推送插件
await push_manager.stop_all_plugins()
```

### 获取插件信息

```python
# 获取所有可用插件信息
plugins_info = push_manager.get_available_plugins_info()

# 获取已加载的插件
loaded_plugins = push_manager.get_all_plugins()
```

## 优势特性

1. **默认配置机制**: 插件提供合理的默认配置，减少必需的配置项
2. **选择性覆盖**: 只需配置想要修改的参数，提高配置效率
3. **插件自主性**: 每个插件可以定义自己的最佳默认配置
4. **配置简化**: 大多数情况下只需要启用插件，无需详细配置
5. **向后兼容**: 支持完整的配置覆盖，保持灵活性
6. **错误处理**: 完善的异常处理和日志记录
7. **并发支持**: 支持插件并发执行
8. **扩展性好**: 易于添加新的推送插件

## 注意事项

1. 插件名称必须唯一
2. 推送消息支持Markdown格式
3. 建议使用异步操作避免阻塞
4. 注意处理网络异常和超时
5. 合理设置推送频率避免骚扰用户
6. 插件默认配置应该是合理和安全的
7. 配置覆盖只影响明确指定的参数 