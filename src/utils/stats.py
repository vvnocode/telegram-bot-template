import os
import json
from datetime import datetime, date
from typing import Dict, List, Any, Optional
import yaml

from src.logger import logger

class UserStatsManager:
    """用户统计管理类，用于记录和查询用户的功能请求次数"""
    
    def __init__(self, data_dir: str = "data"):
        """初始化统计管理器
        
        Args:
            data_dir: 数据存储目录
        """
        self.data_dir = data_dir
        self.stats_dir = os.path.join(data_dir, "stats")
        self.daily_stats_dir = os.path.join(self.stats_dir, "daily")
        self.total_stats_file = os.path.join(self.stats_dir, "total_stats.json")
        
        # 确保目录存在
        self._ensure_dirs()
        
        # 加载总体统计数据
        self.total_stats = self._load_total_stats()
        
    def _ensure_dirs(self) -> None:
        """确保所需的目录结构存在"""
        os.makedirs(self.stats_dir, exist_ok=True)
        os.makedirs(self.daily_stats_dir, exist_ok=True)
        
    def _get_daily_stats_file(self, day: date = None) -> str:
        """获取指定日期的统计文件路径
        
        Args:
            day: 日期对象，默认为今天
            
        Returns:
            str: 文件路径
        """
        if day is None:
            day = date.today()
            
        return os.path.join(self.daily_stats_dir, f"{day.isoformat()}.json")
        
    def _load_total_stats(self) -> Dict[str, Dict[str, int]]:
        """加载总体统计数据
        
        Returns:
            Dict: 用户请求总次数统计
        """
        if os.path.exists(self.total_stats_file):
            try:
                with open(self.total_stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载总体统计数据失败: {str(e)}")
                
        # 如果文件不存在或加载失败，返回空统计
        return {}
        
    def _load_daily_stats(self, day: date = None) -> Dict[str, Dict[str, int]]:
        """加载指定日期的统计数据
        
        Args:
            day: 日期对象，默认为今天
            
        Returns:
            Dict: 当日用户请求次数统计
        """
        if day is None:
            day = date.today()
            
        stats_file = self._get_daily_stats_file(day)
        
        if os.path.exists(stats_file):
            try:
                with open(stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载{day.isoformat()}统计数据失败: {str(e)}")
                
        # 如果文件不存在或加载失败，返回空统计
        return {}
        
    def _save_total_stats(self) -> bool:
        """保存总体统计数据
        
        Returns:
            bool: 是否保存成功
        """
        try:
            with open(self.total_stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.total_stats, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"保存总体统计数据失败: {str(e)}")
            return False
            
    def _save_daily_stats(self, stats: Dict[str, Dict[str, int]], day: date = None) -> bool:
        """保存指定日期的统计数据
        
        Args:
            stats: 统计数据
            day: 日期对象，默认为今天
            
        Returns:
            bool: 是否保存成功
        """
        if day is None:
            day = date.today()
            
        stats_file = self._get_daily_stats_file(day)
        
        try:
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"保存{day.isoformat()}统计数据失败: {str(e)}")
            return False
    
    def record_command_usage(self, user_id: str, command: str) -> bool:
        """记录用户使用命令
        
        Args:
            user_id: 用户ID
            command: 命令名称
            
        Returns:
            bool: 是否记录成功
        """
        today = date.today()
        
        # 加载今日统计
        daily_stats = self._load_daily_stats(today)
        
        # 更新今日统计
        if user_id not in daily_stats:
            daily_stats[user_id] = {}
            
        if command not in daily_stats[user_id]:
            daily_stats[user_id][command] = 0
            
        daily_stats[user_id][command] += 1
        
        # 更新总体统计
        if user_id not in self.total_stats:
            self.total_stats[user_id] = {}
            
        if command not in self.total_stats[user_id]:
            self.total_stats[user_id][command] = 0
            
        self.total_stats[user_id][command] += 1
        
        # 保存统计数据
        daily_saved = self._save_daily_stats(daily_stats, today)
        total_saved = self._save_total_stats()
        
        return daily_saved and total_saved
        
    def get_user_daily_stats(self, user_id: str, day: date = None) -> Dict[str, int]:
        """获取用户指定日期的使用统计
        
        Args:
            user_id: 用户ID
            day: 日期对象，默认为今天
            
        Returns:
            Dict: 命令使用次数统计
        """
        if day is None:
            day = date.today()
            
        daily_stats = self._load_daily_stats(day)
        return daily_stats.get(user_id, {})
        
    def get_user_total_stats(self, user_id: str) -> Dict[str, int]:
        """获取用户总体使用统计
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict: 命令使用总次数统计
        """
        return self.total_stats.get(user_id, {})
        
    def get_all_daily_stats(self, day: date = None) -> Dict[str, Dict[str, int]]:
        """获取所有用户指定日期的使用统计
        
        Args:
            day: 日期对象，默认为今天
            
        Returns:
            Dict: 所有用户的命令使用次数统计
        """
        if day is None:
            day = date.today()
            
        return self._load_daily_stats(day)
        
    def get_all_total_stats(self) -> Dict[str, Dict[str, int]]:
        """获取所有用户的总体使用统计
        
        Returns:
            Dict: 所有用户的命令使用总次数统计
        """
        return self.total_stats
        
    def get_command_summary(self, day: date = None) -> Dict[str, int]:
        """获取所有命令的使用摘要（按命令汇总）
        
        Args:
            day: 日期对象，默认为None表示获取总体统计
            
        Returns:
            Dict: 命令使用次数汇总
        """
        summary = {}
        
        if day is None:
            # 总体统计
            for user_id, commands in self.total_stats.items():
                for cmd, count in commands.items():
                    if cmd not in summary:
                        summary[cmd] = 0
                    summary[cmd] += count
        else:
            # 指定日期统计
            daily_stats = self._load_daily_stats(day)
            for user_id, commands in daily_stats.items():
                for cmd, count in commands.items():
                    if cmd not in summary:
                        summary[cmd] = 0
                    summary[cmd] += count
                    
        return summary 