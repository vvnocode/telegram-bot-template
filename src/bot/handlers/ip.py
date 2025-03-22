import subprocess
import time
import json
import requests
import os
from datetime import datetime, timedelta, date
from typing import Dict, Any, Optional

from telegram import Update
from telegram.ext import ContextTypes

from src.auth import UserManager, UserRole
from src.logger import logger
from src.bot.handlers.command import CommandPlugin, CommandCategory, CommandRegistry
from src.config import config


class IPManager:
    """IP管理器，处理IP查询和更换"""
    
    def __init__(self):
        """初始化IP管理器"""
        self.ip_config = config.get('get_ip_cmd', ['curl -s api-ipv4.ip.sb/ip'])
        self.change_ip_config = config.get('change_ip', {})
        
        # IP更换配置参数
        self.change_interval = self.change_ip_config.get('change_interval', 5)  # 更换间隔(分钟)
        self.change_day_limit = self.change_ip_config.get('change_day_limit', 3)  # 每日总限制
        self.change_day_limit_every_user = self.change_ip_config.get('change_day_limit_every_user', 2)  # 每用户限制
        self.change_day_begin = self.change_ip_config.get('change_day_begin', '00:00:00')  # 每日开始时间
        self.change_ip_check_wait = self.change_ip_config.get('change_ip_check_wait', 1)  # 更换后验证等待时间(秒)
        
        # 数据存储目录
        self.data_dir = "data"
        self.ip_data_dir = os.path.join(self.data_dir, "ip_change")
        self.ip_data_file = os.path.join(self.ip_data_dir, "ip_change_records.json")
        
        # 确保目录存在
        self._ensure_dirs()
        
        # 加载IP更换记录
        self.ip_change_data = self._load_ip_change_data()
        
        # 获取今日开始时间
        self._update_day_begin()
    
    def _ensure_dirs(self) -> None:
        """确保所需的目录结构存在"""
        os.makedirs(self.ip_data_dir, exist_ok=True)
    
    def _load_ip_change_data(self) -> Dict:
        """加载IP更换记录数据
        
        Returns:
            Dict: IP更换记录数据
        """
        if os.path.exists(self.ip_data_file):
            try:
                with open(self.ip_data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载IP更换记录数据失败: {str(e)}")
                
        # 如果文件不存在或加载失败，返回空记录
        return {
            'last_ip_change': {},  # 用户上次更换IP时间: {user_id: timestamp}
            'daily_ip_change_count': {},  # 今日IP更换总次数
            'user_daily_ip_change_count': {},  # 每用户今日更换次数: {user_id: count}
            'day_begin': datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 当日开始时间
        }
    
    def _save_ip_change_data(self) -> bool:
        """保存IP更换记录数据
        
        Returns:
            bool: 是否保存成功
        """
        try:
            with open(self.ip_data_file, 'w', encoding='utf-8') as f:
                json.dump(self.ip_change_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"保存IP更换记录数据失败: {str(e)}")
            return False
    
    def _update_day_begin(self):
        """更新每日开始时间"""
        now = datetime.now()
        time_parts = self.change_day_begin.split(':')
        hour, minute, second = int(time_parts[0]), int(time_parts[1]), int(time_parts[2])
        
        day_begin = now.replace(hour=hour, minute=minute, second=second, microsecond=0)
        if day_begin > now:
            day_begin -= timedelta(days=1)
            
        # 存储当日开始时间
        self.ip_change_data['day_begin'] = day_begin.strftime('%Y-%m-%d %H:%M:%S')
            
        # 如果是新的一天，重置计数
        stored_day_begin = datetime.strptime(self.ip_change_data['day_begin'], '%Y-%m-%d %H:%M:%S')
        if now.date() > stored_day_begin.date():
            self.ip_change_data['daily_ip_change_count'] = {}
            self.ip_change_data['user_daily_ip_change_count'] = {}
            self._save_ip_change_data()
    
    def check_current_ip(self) -> str:
        """检查当前IP
        
        Returns:
            str: 当前IP地址
        """
        for cmd in self.ip_config:
            try:
                result = subprocess.check_output(cmd, shell=True, text=True).strip()
                if result:
                    return result
            except Exception as e:
                logger.error(f"IP检查命令失败: {cmd}, 错误: {str(e)}")
        
        return "无法获取IP"
    
    def can_change_ip(self, user_id: int) -> tuple[bool, str]:
        """检查是否可以更换IP
        
        Args:
            user_id: 用户ID
            
        Returns:
            tuple: (是否可以更换, 原因)
        """
        # 更新当天开始时间
        self._update_day_begin()
        
        # 获取用户ID的字符串表示(JSON键必须是字符串)
        user_id_str = str(user_id)
        
        # 检查总次数限制
        daily_count = self.ip_change_data['daily_ip_change_count'].get('total', 0)
        if daily_count >= self.change_day_limit:
            return False, f"今日更换IP总次数已达到限制({daily_count}/{self.change_day_limit})"
        
        # 检查用户次数限制
        user_daily_count = self.ip_change_data['user_daily_ip_change_count'].get(user_id_str, 0)
        if user_daily_count >= self.change_day_limit_every_user:
            return False, f"您今日更换IP次数已达到限制({user_daily_count}/{self.change_day_limit_every_user})"
        
        # 检查时间间隔
        last_change_time = self.ip_change_data['last_ip_change'].get(user_id_str, 0)
        if last_change_time:
            elapsed_minutes = (time.time() - last_change_time) / 60
            if elapsed_minutes < self.change_interval:
                remaining_minutes = self.change_interval - elapsed_minutes
                return False, f"更换IP太频繁，请等待 {int(remaining_minutes)} 分钟后再试"
        
        return True, "可以更换IP"
    
    def change_ip(self) -> tuple[bool, str]:
        """更换IP
        
        Returns:
            tuple: (是否成功, 消息)
        """
        old_ip = self.check_current_ip()
        
        # 根据配置类型执行更换
        change_type = self.change_ip_config.get('type', 'cmd')
        
        try:
            if change_type == 'cmd':
                cmd = self.change_ip_config.get('cmd')
                if not cmd:
                    return False, "更换IP命令未配置"
                
                subprocess.run(cmd, shell=True, check=True)
                
            elif change_type == 'api':
                api_url = self.change_ip_config.get('api')
                if not api_url:
                    return False, "更换IP的API未配置"
                
                # 准备API请求
                headers = {}
                data = {}
                method = self.change_ip_config.get('api_method', 'POST').upper()
                
                # 处理header
                api_header = self.change_ip_config.get('api_header', '')
                if api_header:
                    for header_line in api_header.split('\n'):
                        if ':' in header_line:
                            key, value = header_line.split(':', 1)
                            headers[key.strip()] = value.strip()
                
                # 处理data
                api_data = self.change_ip_config.get('api_data', '')
                if api_data:
                    try:
                        data = json.loads(api_data)
                    except:
                        data = api_data
                
                # 发送请求
                if method == 'GET':
                    response = requests.get(api_url, headers=headers)
                else:  # POST
                    response = requests.post(api_url, headers=headers, json=data if isinstance(data, dict) else None, data=None if isinstance(data, dict) else data)
                
                response.raise_for_status()
            else:
                return False, f"不支持的更换IP类型: {change_type}"
            
            # 等待指定时间
            time.sleep(self.change_ip_check_wait * 60)
            
            # 检查IP是否变化
            new_ip = self.check_current_ip()
            if new_ip != old_ip:
                return True, f"IP已更换: {old_ip} -> {new_ip}"
            else:
                return False, f"IP未变化: {old_ip}"
                
        except Exception as e:
            logger.error(f"更换IP失败: {str(e)}", exc_info=True)
            return False, f"更换IP出错: {str(e)}"
    
    def record_ip_change(self, user_id: int, success: bool) -> None:
        """记录IP更换
        
        Args:
            user_id: 用户ID
            success: 是否成功
        """
        if success:
            # 获取用户ID的字符串表示(JSON键必须是字符串)
            user_id_str = str(user_id)
            
            # 记录用户上次更换时间
            self.ip_change_data['last_ip_change'][user_id_str] = time.time()
            
            # 更新计数
            self.ip_change_data['daily_ip_change_count']['total'] = self.ip_change_data['daily_ip_change_count'].get('total', 0) + 1
            self.ip_change_data['user_daily_ip_change_count'][user_id_str] = self.ip_change_data['user_daily_ip_change_count'].get(user_id_str, 0) + 1
            
            # 保存数据到文件
            self._save_ip_change_data()


# 全局IP管理器实例
ip_manager = IPManager()


async def check_ip_command(update: Update, context: ContextTypes.DEFAULT_TYPE, user_manager: UserManager):
    """查看当前IP命令处理器
    
    Args:
        update: Telegram更新对象
        context: 上下文对象
        user_manager: 用户管理器实例
    """
    user_id = update.effective_user.id
    logger.info(f"用户 {user_id} 请求查看当前IP")
    
    current_ip = ip_manager.check_current_ip()
    
    await update.message.reply_text(f"当前IP地址: {current_ip}")


async def change_ip_command(update: Update, context: ContextTypes.DEFAULT_TYPE, user_manager: UserManager):
    """更换IP命令处理器
    
    Args:
        update: Telegram更新对象
        context: 上下文对象
        user_manager: 用户管理器实例
    """
    user_id = update.effective_user.id
    logger.info(f"用户 {user_id} 请求更换IP")
    
    # 检查是否可以更换IP
    can_change, reason = ip_manager.can_change_ip(user_id)
    if not can_change:
        await update.message.reply_text(f"⚠️ {reason}")
        return
    
    # 发送正在更换的消息
    message = await update.message.reply_text("正在更换IP，请稍候...")
    
    # 更换IP
    success, result_message = ip_manager.change_ip()
    
    # 记录更换结果
    ip_manager.record_ip_change(user_id, success)
    
    # 更新消息
    if success:
        await message.edit_text(f"✅ {result_message}")
    else:
        await message.edit_text(f"❌ {result_message}")


def register_ip_commands(command_registry: CommandRegistry):
    """注册IP相关命令
    
    Args:
        command_registry: 命令注册器实例
    """
    # 查看当前IP命令
    command_registry.register_command(
        CommandPlugin(
            command="get_ip",
            description="查看当前IP地址",
            handler=check_ip_command,
            category=CommandCategory.TOOLS,
            required_role=UserRole.USER
        )
    )
    
    # 更换IP命令
    command_registry.register_command(
        CommandPlugin(
            command="change_ip",
            description="更换当前IP地址",
            handler=change_ip_command,
            category=CommandCategory.TOOLS,
            required_role=UserRole.USER
        )
    ) 