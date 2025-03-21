from telegram import Update
from typing import List, Dict, Any
from src.auth.permissions import UserRole
from src.logger import logger

class UserManager:
    """用户管理类"""
    def __init__(self, config: Dict[str, Any]):
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