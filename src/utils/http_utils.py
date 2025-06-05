"""HTTP请求工具类"""
import json
import urllib.request
import urllib.parse
import urllib.error
from typing import Dict, Any, Optional, Union
from src.logger import logger


class HTTPUtils:
    """HTTP请求工具类"""
    
    @staticmethod
    def make_request(
        url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Union[Dict[str, Any], str]] = None,
        timeout: int = 30
    ) -> tuple[bool, str]:
        """发送HTTP请求
        
        Args:
            url: 请求URL
            method: HTTP方法 (GET, POST, PUT, DELETE等)
            headers: 请求头字典
            data: 请求数据，可以是字典或字符串
            timeout: 超时时间（秒）
            
        Returns:
            tuple[bool, str]: (是否成功, 响应内容或错误信息)
        """
        try:
            # 验证URL
            if not url or not url.strip():
                return False, "URL不能为空"
            
            # 准备请求数据
            request_data = None
            if data:
                if isinstance(data, dict):
                    # 如果是字典，转换为JSON字符串
                    request_data = json.dumps(data).encode('utf-8')
                    # 确保Content-Type设置为application/json
                    if headers is None:
                        headers = {}
                    if 'Content-Type' not in headers:
                        headers['Content-Type'] = 'application/json'
                elif isinstance(data, str):
                    request_data = data.encode('utf-8')
                else:
                    return False, f"不支持的数据类型: {type(data)}"
            
            # 创建请求对象
            req = urllib.request.Request(
                url=url.strip(),
                data=request_data,
                method=method.upper()
            )
            
            # 添加请求头
            if headers:
                for key, value in headers.items():
                    req.add_header(key, value)
            
            # 发送请求
            logger.debug(f"HTTP工具: 发送{method}请求到 {url}")
            with urllib.request.urlopen(req, timeout=timeout) as response:
                response_data = response.read().decode('utf-8')
                status_code = response.status
                
                logger.debug(f"HTTP工具: 请求成功，状态码: {status_code}")
                
                if 200 <= status_code < 300:
                    return True, response_data
                else:
                    return False, f"HTTP错误 {status_code}: {response_data}"
                    
        except urllib.error.HTTPError as e:
            error_msg = f"HTTP错误 {e.code}: {e.reason}"
            if hasattr(e, 'read'):
                try:
                    error_detail = e.read().decode('utf-8')
                    if error_detail:
                        error_msg += f" - {error_detail}"
                except:
                    pass
            logger.error(f"HTTP工具: {error_msg}")
            return False, error_msg
            
        except urllib.error.URLError as e:
            error_msg = f"URL错误: {e.reason}"
            logger.error(f"HTTP工具: {error_msg}")
            return False, error_msg
            
        except Exception as e:
            error_msg = f"请求失败: {str(e)}"
            logger.error(f"HTTP工具: {error_msg}")
            return False, error_msg 