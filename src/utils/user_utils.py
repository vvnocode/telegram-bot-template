"""用户工具类"""

from typing import Optional
from telegram.ext import ContextTypes
from src.logger import logger
from .user_cache import user_cache


class UserUtils:
    """用户相关工具类"""
    
    @staticmethod
    async def get_user_display_name(user_id: any, context: ContextTypes.DEFAULT_TYPE = None) -> str:
        """获取用户显示名称（昵称或ID）
        
        Args:
            user_id: 用户ID
            context: Telegram上下文对象（可选）
            
        Returns:
            str: 用户显示名称，格式为 "昵称 (`用户ID`)" 或 "`用户ID`"
        """
        if not isinstance(user_id, int):
            try:
                user_id = int(user_id)
            except ValueError:
                return f"`{user_id}`"
        
        # 优先从缓存获取
        cached_name = user_cache.get_user_display_name(user_id)
        if cached_name != f"`{user_id}`":  # 如果缓存中有昵称信息
            return cached_name
        
        # 如果缓存中没有且提供了context，尝试从API获取
        if context:
            try:
                chat = await context.bot.get_chat(user_id)
                
                # 更新缓存
                user_cache.update_user_info(
                    user_id=user_id,
                    username=chat.username,
                    full_name=chat.full_name,
                    first_name=chat.first_name,
                    last_name=chat.last_name
                )
                
                # 优先使用全名，其次使用用户名，最后使用ID
                if chat.full_name:
                    return f"{chat.full_name} (`{user_id}`)"
                elif chat.username:
                    return f"@{chat.username} (`{user_id}`)"
                else:
                    return f"`{user_id}`"
            except Exception as e:
                logger.debug(f"无法通过API获取用户 {user_id} 信息: {str(e)}")
        
        # 如果都失败了，返回用户ID
        return f"`{user_id}`"
    
    @staticmethod
    async def get_user_simple_name(user_id: any, context: ContextTypes.DEFAULT_TYPE = None) -> str:
        """获取用户简单显示名称（仅昵称，不包含ID）
        
        Args:
            user_id: 用户ID
            context: Telegram上下文对象（可选）
            
        Returns:
            str: 用户简单显示名称，如果获取失败则返回用户ID字符串
        """
        if not isinstance(user_id, int):
            try:
                user_id = int(user_id)
            except ValueError:
                return f"`{user_id}`"
        
        # 优先从缓存获取
        cached_name = user_cache.get_user_simple_name(user_id)
        if cached_name != str(user_id):  # 如果缓存中有昵称信息
            return cached_name
        
        # 如果缓存中没有且提供了context，尝试从API获取
        if context:
            try:
                chat = await context.bot.get_chat(user_id)
                
                # 更新缓存
                user_cache.update_user_info(
                    user_id=user_id,
                    username=chat.username,
                    full_name=chat.full_name,
                    first_name=chat.first_name,
                    last_name=chat.last_name
                )
                
                # 优先使用全名，其次使用用户名，最后使用ID
                if chat.full_name:
                    return chat.full_name
                elif chat.username:
                    return f"@{chat.username}"
                else:
                    return str(user_id)
            except Exception as e:
                logger.debug(f"无法通过API获取用户 {user_id} 信息: {str(e)}")
        
        # 如果都失败了，返回用户ID
        return str(user_id)
    
    @staticmethod
    async def get_user_info(user_id: any, context: ContextTypes.DEFAULT_TYPE = None) -> Optional[dict]:
        """获取用户完整信息
        
        Args:
            user_id: 用户ID
            context: Telegram上下文对象（可选）
            
        Returns:
            Optional[dict]: 用户信息字典，获取失败时返回None
        """
        if not isinstance(user_id, int):
            try:
                user_id = int(user_id)
            except ValueError:
                return None
        
        # 先尝试从缓存获取
        cached_info = user_cache.get_user_info(user_id)
        if cached_info:
            return cached_info
        
        # 如果缓存中没有且提供了context，尝试从API获取
        if context:
            try:
                chat = await context.bot.get_chat(user_id)
                
                user_info = {
                    'id': chat.id,
                    'username': chat.username,
                    'full_name': chat.full_name,
                    'first_name': chat.first_name,
                    'last_name': chat.last_name,
                    'type': chat.type
                }
                
                # 更新缓存
                user_cache.update_user_info(
                    user_id=user_id,
                    username=chat.username,
                    full_name=chat.full_name,
                    first_name=chat.first_name,
                    last_name=chat.last_name
                )
                
                return user_info
            except Exception as e:
                logger.debug(f"无法通过API获取用户 {user_id} 完整信息: {str(e)}")
        
        return None
    
    @staticmethod
    def update_user_cache_from_update(update):
        """从Update对象更新用户缓存
        
        Args:
            update: Telegram Update对象
        """
        if update.effective_user:
            user = update.effective_user
            user_cache.update_user_info(
                user_id=user.id,
                username=user.username,
                full_name=user.full_name,
                first_name=user.first_name,
                last_name=user.last_name
            ) 