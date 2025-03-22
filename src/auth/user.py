from telegram import Update
from typing import List, Dict, Any
import os
import yaml

from src.auth.permissions import UserRole
from src.logger import logger

class UserManager:
    """用户管理类"""
    def __init__(self, config: Dict[str, Any]):
        """初始化用户管理类"""
        self.config = config
        self.config_file = config.get('config_file', 'config.yaml')
        self.admin_ids = self._parse_admin_ids(config.get('telegram_admin_id', ''))
        self.allowed_user_ids = self._parse_user_ids(config.get('telegram_user_id', ''))
        
    def _parse_admin_ids(self, admin_id_str: str) -> List[str]:
        """解析管理员ID列表"""
        if not admin_id_str:
            return []
        return [id.strip() for id in admin_id_str.split(',') if id.strip()]
    
    def _parse_user_ids(self, user_id_str: str) -> List[str]:
        """解析普通用户ID列表"""
        if not user_id_str:
            return []
        return [id.strip() for id in user_id_str.split(',') if id.strip()]
    
    def get_user_role(self, user_id: int) -> UserRole:
        """获取用户角色"""
        user_id_str = str(user_id)
        if user_id_str in self.admin_ids:
            return UserRole.ADMIN
        elif user_id_str in self.allowed_user_ids:
            return UserRole.USER
        return None
    
    async def check_user_permission(self, update: Update) -> bool:
        """检查用户权限，判断用户是否有权限使用机器人"""
        user_id = update.effective_user.id
        user_name = update.effective_user.username
        full_name = update.effective_user.full_name
        
        user_role = self.get_user_role(user_id)
        
        if user_role is None:
            logger.warning(f"未授权的用户尝试访问，用户ID: {user_id}，用户名: {user_name}，全名: {full_name}")
            await update.message.reply_text("未授权的用户")
            return False
            
        logger.info(f"授权用户访问，用户ID: {user_id}，用户名: {user_name}，角色: {user_role.name}")
        return True
        
    async def check_admin_permission(self, update: Update) -> bool:
        """检查管理员权限，判断用户是否为管理员"""
        user_id = update.effective_user.id
        user_name = update.effective_user.username
        full_name = update.effective_user.full_name
        
        user_role = self.get_user_role(user_id)
        
        if user_role != UserRole.ADMIN:
            logger.warning(f"非管理员用户尝试执行管理操作，用户ID: {user_id}，用户名: {user_name}，全名: {full_name}")
            await update.message.reply_text("此操作需要管理员权限")
            return False
            
        logger.info(f"管理员执行操作，用户ID: {user_id}，用户名: {user_name}")
        return True
        
    def add_user(self, user_id: str) -> bool:
        """添加普通用户
        
        Args:
            user_id: 用户ID（字符串形式）
            
        Returns:
            bool: 是否添加成功
        """
        # 清理输入
        user_id = user_id.strip()
        
        if not user_id:
            return False
            
        # 检查是否已经是用户
        if user_id in self.allowed_user_ids:
            return False
            
        # 检查是否已经是管理员
        if user_id in self.admin_ids:
            return False
            
        # 添加到用户列表
        self.allowed_user_ids.append(user_id)
        
        # 更新配置
        return self._save_config()
    
    def remove_user(self, user_id: str) -> bool:
        """删除普通用户
        
        Args:
            user_id: 用户ID（字符串形式）
            
        Returns:
            bool: 是否删除成功
        """
        # 清理输入
        user_id = user_id.strip()
        
        if not user_id:
            return False
            
        # 检查是否是用户
        if user_id not in self.allowed_user_ids:
            return False
            
        # 从用户列表中移除
        self.allowed_user_ids.remove(user_id)
        
        # 更新配置
        return self._save_config()
        
    def get_all_users(self) -> Dict[str, List[str]]:
        """获取所有用户列表
        
        Returns:
            Dict: 包含管理员和普通用户的字典
        """
        return {
            'admins': self.admin_ids.copy(),
            'users': self.allowed_user_ids.copy()
        }
        
    def _save_config(self) -> bool:
        """保存配置到文件
        
        Returns:
            bool: 是否保存成功
        """
        try:
            # 读取当前配置文件
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
            else:
                config_data = {}
            
            # 更新用户配置
            config_data['telegram_admin_id'] = ','.join(self.admin_ids)
            config_data['telegram_user_id'] = ','.join(self.allowed_user_ids)
            
            # 写入配置文件
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
                
            # 更新内存中的配置
            self.config['telegram_admin_id'] = ','.join(self.admin_ids)
            self.config['telegram_user_id'] = ','.join(self.allowed_user_ids)
            
            logger.info(f"用户配置已更新并保存到 {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"保存用户配置失败: {str(e)}", exc_info=True)
            return False 