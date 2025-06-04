"""推送插件接口定义"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, List, Optional, ClassVar
import asyncio
from datetime import datetime

from telegram.ext import Application

from src.auth import UserManager, UserRole
from src.logger import logger


class PushFrequency(Enum):
    """推送频率枚举"""
    ONCE = "once"           # 一次性推送
    INTERVAL = "interval"   # 间隔推送
    CRON = "cron"          # 定时推送
    EVENT = "event"        # 事件触发推送


@dataclass
class PushConfig:
    """推送配置"""
    enabled: bool = True                    # 是否启用
    frequency: PushFrequency = PushFrequency.EVENT  # 推送频率
    interval_seconds: int = 300             # 间隔秒数（当频率为INTERVAL时）
    cron_expression: str = ""               # Cron表达式（当频率为CRON时）
    target_role: UserRole = UserRole.ADMIN  # 目标用户角色：ADMIN=仅管理员，USER=所有用户
    custom_targets: List[int] = None        # 自定义推送目标用户ID列表
    
    def __post_init__(self):
        if self.custom_targets is None:
            self.custom_targets = []


class PushPluginInterface(ABC):
    """推送插件接口"""
    # 插件元数据，子类应该覆盖这些属性
    name: ClassVar[str] = "base_push_plugin"
    description: ClassVar[str] = "基础推送插件"
    version: ClassVar[str] = "1.0.0"
    
    # 默认推送配置，子类应该覆盖这些属性
    default_enabled: ClassVar[bool] = True
    default_frequency: ClassVar[PushFrequency] = PushFrequency.EVENT
    default_interval_seconds: ClassVar[int] = 300
    default_target_role: ClassVar[UserRole] = UserRole.ADMIN
    
    def __init__(self, user_manager: UserManager, config: PushConfig):
        """初始化推送插件
        
        Args:
            user_manager: 用户管理器
            config: 推送配置对象
        """
        self.user_manager = user_manager
        self.config = config
        self._task: Optional[asyncio.Task] = None
        self._app: Optional[Application] = None
        self._is_running = False
        
    @property
    def is_enabled(self) -> bool:
        """获取插件是否启用"""
        return self.config.enabled
    
    @property
    def is_running(self) -> bool:
        """获取插件是否正在运行"""
        return self._is_running
    
    @abstractmethod
    async def check_condition(self) -> tuple[bool, Optional[str]]:
        """检查推送条件
        
        Returns:
            tuple[bool, Optional[str]]: (是否需要推送, 推送消息)
        """
        pass
    
    @abstractmethod
    def get_message(self, data: Any = None) -> str:
        """获取推送消息内容
        
        Args:
            data: 额外数据
            
        Returns:
            str: 推送消息
        """
        pass
    
    async def get_target_users(self) -> List[int]:
        """获取推送目标用户列表
        
        Returns:
            List[int]: 用户ID列表
        """
        # 如果有自定义目标，直接返回
        if self.config.custom_targets:
            return self.config.custom_targets
        
        # 根据角色获取用户
        if self.config.target_role == UserRole.ADMIN:
            # 仅管理员
            return await self.user_manager.get_admin_user_ids()
        elif self.config.target_role == UserRole.USER:
            # 所有用户（管理员+普通用户）
            return await self.user_manager.get_all_user_ids()
        else:
            # 默认情况
            logger.warning(f"推送插件 {self.name}: 未知的目标角色 {self.config.target_role}，默认推送给管理员")
            return await self.user_manager.get_admin_user_ids()
    
    async def send_push_message(self, message: str, targets: List[int] = None) -> bool:
        """发送推送消息
        
        Args:
            message: 消息内容
            targets: 目标用户列表，为空则使用默认配置
            
        Returns:
            bool: 是否发送成功
        """
        if not self._app or not self._app.bot:
            logger.error(f"推送插件 {self.name}: Bot应用未初始化")
            return False
        
        if targets is None:
            targets = await self.get_target_users()
        
        if not targets:
            logger.warning(f"推送插件 {self.name}: 没有找到目标用户，跳过推送")
            return False
        
        success_count = 0
        
        for user_id in targets:
            try:
                await self._app.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode='Markdown'
                )
                success_count += 1
                logger.info(f"推送插件 {self.name}: 成功向用户 {user_id} 发送消息")
            except Exception as e:
                logger.error(f"推送插件 {self.name}: 向用户 {user_id} 发送消息失败: {str(e)}")
        
        logger.info(f"推送插件 {self.name}: 推送完成，成功发送 {success_count}/{len(targets)} 条消息")
        return success_count > 0
    
    async def start(self, app: Application) -> None:
        """启动推送插件
        
        Args:
            app: Telegram应用实例
        """
        if not self.is_enabled:
            logger.info(f"推送插件 {self.name} 未启用，跳过启动")
            return
        
        if self._is_running:
            logger.warning(f"推送插件 {self.name} 已在运行中")
            return
        
        self._app = app
        self._is_running = True
        
        # 根据频率类型启动不同的任务
        if self.config.frequency == PushFrequency.INTERVAL:
            self._task = asyncio.create_task(self._interval_task())
        elif self.config.frequency == PushFrequency.EVENT:
            # 事件驱动模式，由外部调用trigger_check
            pass
        elif self.config.frequency == PushFrequency.ONCE:
            self._task = asyncio.create_task(self._once_task())
        
        logger.info(f"推送插件 {self.name} 已启动，频率: {self.config.frequency.value}")
    
    async def stop(self) -> None:
        """停止推送插件"""
        if not self._is_running:
            return
        
        self._is_running = False
        
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info(f"推送插件 {self.name} 已停止")
    
    async def trigger_check(self) -> None:
        """手动触发条件检查（用于事件驱动模式）"""
        if not self.is_enabled or not self._is_running:
            return
        
        try:
            should_push, message = await self.check_condition()
            if should_push and message:
                await self.send_push_message(message)
        except Exception as e:
            logger.error(f"推送插件 {self.name} 触发检查时出错: {str(e)}", exc_info=True)
    
    async def _interval_task(self) -> None:
        """间隔任务循环"""
        logger.info(f"推送插件 {self.name} 开始间隔任务，间隔: {self.config.interval_seconds}秒")
        
        while self._is_running:
            try:
                await self.trigger_check()
                await asyncio.sleep(self.config.interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"推送插件 {self.name} 间隔任务出错: {str(e)}", exc_info=True)
                await asyncio.sleep(self.config.interval_seconds)
    
    async def _once_task(self) -> None:
        """一次性任务"""
        logger.info(f"推送插件 {self.name} 执行一次性推送")
        try:
            await self.trigger_check()
        except Exception as e:
            logger.error(f"推送插件 {self.name} 一次性任务出错: {str(e)}", exc_info=True) 