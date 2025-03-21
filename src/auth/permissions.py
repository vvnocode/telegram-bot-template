from enum import Enum, auto

class UserRole(Enum):
    """用户角色枚举"""
    USER = auto()      # 普通用户
    ADMIN = auto()     # 管理员
    
class Permission:
    """权限检查工具类"""
    @staticmethod
    def is_admin(role: UserRole) -> bool:
        """检查是否为管理员"""
        return role == UserRole.ADMIN
    
    @staticmethod
    def is_user(role: UserRole) -> bool:
        """检查是否为普通用户"""
        return role == UserRole.USER 