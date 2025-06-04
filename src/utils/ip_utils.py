"""IP工具类"""
import urllib.request
import urllib.error
from typing import Optional
from src.config import config
from src.logger import logger


class IPUtils:
    """IP地址相关工具类"""
    
    @staticmethod
    def get_current_ip() -> Optional[str]:
        """获取当前IP地址
        
        Returns:
            Optional[str]: 当前IP地址，获取失败时返回None
        """
        # 使用Python内置urllib（避免curl兼容性问题）
        try:
            api_urls = config.get('get_ip_urls', [
                'https://api.ipify.org'
            ])
            
            for url in api_urls:
                try:
                    with urllib.request.urlopen(url, timeout=5) as response:
                        if response.status == 200:
                            ip = response.read().decode('utf-8').strip()
                            if ip and IPUtils._is_valid_ip(ip):
                                logger.debug(f"IP工具: 成功获取IP {ip} (来源: {url})")
                                return ip
                except Exception as e:
                    logger.debug(f"IP工具: 请求失败 {url}, 错误: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"IP工具: 获取IP地址失败: {str(e)}")
        
        return None
    
    @staticmethod
    def _is_valid_ip(ip: str) -> bool:
        """验证IP地址格式
        
        Args:
            ip: IP地址字符串
            
        Returns:
            bool: 是否为有效IP地址
        """
        try:
            import ipaddress
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def get_current_ip_with_fallback() -> str:
        """获取当前IP地址，带默认值
        
        Returns:
            str: 当前IP地址，获取失败时返回"无法获取IP"
        """
        ip = IPUtils.get_current_ip()
        return ip if ip else "无法获取IP" 