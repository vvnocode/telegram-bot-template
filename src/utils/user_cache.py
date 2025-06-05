"""用户信息缓存系统"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from src.logger import logger


class UserInfoCache:
    """用户信息缓存类"""
    
    def __init__(self, cache_file: str = "data/cache/user_cache.json"):
        """初始化用户信息缓存
        
        Args:
            cache_file: 缓存文件路径
        """
        self.cache_file = cache_file
        self.cache_data = {}
        self._ensure_cache_dir()
        self._load_cache()
    
    def _ensure_cache_dir(self):
        """确保缓存目录存在"""
        cache_dir = os.path.dirname(self.cache_file)
        if cache_dir:
            os.makedirs(cache_dir, exist_ok=True)
    
    def _load_cache(self):
        """从文件加载缓存数据"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache_data = json.load(f)
                logger.info(f"已加载用户缓存，包含 {len(self.cache_data)} 个用户")
            else:
                self.cache_data = {}
                logger.info("用户缓存文件不存在，创建新缓存")
        except Exception as e:
            logger.error(f"加载用户缓存失败: {str(e)}")
            self.cache_data = {}
    
    def _save_cache(self):
        """保存缓存数据到文件"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"保存用户缓存失败: {str(e)}")
            return False
    
    def update_user_info(self, user_id: int, username: str = None, full_name: str = None, 
                        first_name: str = None, last_name: str = None):
        """更新用户信息
        
        Args:
            user_id: 用户ID
            username: 用户名
            full_name: 全名
            first_name: 名字
            last_name: 姓氏
        """
        user_id_str = str(user_id)
        current_time = datetime.now().isoformat()
        
        # 如果用户不存在，创建新记录
        if user_id_str not in self.cache_data:
            self.cache_data[user_id_str] = {
                'created_at': current_time,
                'updated_at': current_time,
                'interaction_count': 0
            }
        
        # 更新用户信息
        user_data = self.cache_data[user_id_str]
        user_data['updated_at'] = current_time
        user_data['interaction_count'] = user_data.get('interaction_count', 0) + 1
        
        # 只更新非空的字段
        if username is not None:
            user_data['username'] = username
        if full_name is not None:
            user_data['full_name'] = full_name
        if first_name is not None:
            user_data['first_name'] = first_name
        if last_name is not None:
            user_data['last_name'] = last_name
        
        self._save_cache()
        logger.debug(f"已更新用户 {user_id} 的缓存信息")
    
    def get_user_display_name(self, user_id: int) -> str:
        """获取用户显示名称
        
        Args:
            user_id: 用户ID
            
        Returns:
            str: 用户显示名称
        """
        user_id_str = str(user_id)
        
        if user_id_str not in self.cache_data:
            return f"`{user_id}`"
        
        user_data = self.cache_data[user_id_str]
        
        # 优先使用全名，其次使用用户名，最后使用ID
        if user_data.get('full_name'):
            return f"{user_data['full_name']} (`{user_id}`)"
        elif user_data.get('username'):
            return f"@{user_data['username']} (`{user_id}`)"
        elif user_data.get('first_name'):
            last_name = user_data.get('last_name', '')
            full_name = f"{user_data['first_name']} {last_name}".strip()
            return f"{full_name} (`{user_id}`)"
        else:
            return f"`{user_id}`"
    
    def get_user_simple_name(self, user_id: int) -> str:
        """获取用户简单显示名称（仅昵称，不包含ID）
        
        Args:
            user_id: 用户ID
            
        Returns:
            str: 用户简单显示名称
        """
        user_id_str = str(user_id)
        
        if user_id_str not in self.cache_data:
            return str(user_id)
        
        user_data = self.cache_data[user_id_str]
        
        # 优先使用全名，其次使用用户名，最后使用ID
        if user_data.get('full_name'):
            return user_data['full_name']
        elif user_data.get('username'):
            return f"@{user_data['username']}"
        elif user_data.get('first_name'):
            last_name = user_data.get('last_name', '')
            return f"{user_data['first_name']} {last_name}".strip()
        else:
            return str(user_id)
    
    def get_user_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """获取用户完整缓存信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            Optional[Dict]: 用户信息字典，如果不存在则返回None
        """
        user_id_str = str(user_id)
        return self.cache_data.get(user_id_str)
    
    def cleanup_old_entries(self, days: int = 30):
        """清理旧的缓存条目
        
        Args:
            days: 删除多少天前的条目
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff_date.isoformat()
        
        old_count = len(self.cache_data)
        self.cache_data = {
            user_id: data for user_id, data in self.cache_data.items()
            if data.get('updated_at', '') > cutoff_str
        }
        new_count = len(self.cache_data)
        
        if old_count != new_count:
            self._save_cache()
            logger.info(f"清理了 {old_count - new_count} 个旧的用户缓存条目")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            Dict: 缓存统计信息
        """
        return {
            'total_users': len(self.cache_data),
            'cache_file': self.cache_file,
            'cache_size_kb': round(os.path.getsize(self.cache_file) / 1024, 2) if os.path.exists(self.cache_file) else 0
        }


# 全局用户缓存实例
user_cache = UserInfoCache() 