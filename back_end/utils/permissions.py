"""
自定义权限类模块

提供各种自定义的DRF权限类，用于增强API接口的权限控制能力
"""

from rest_framework import permissions
from guardian.shortcuts import get_perms


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    管理员或只读权限
    
    允许管理员用户进行所有操作，普通用户只能进行读取操作
    """
    
    def has_permission(self, request, view):
        """
        检查用户是否有权限访问视图
        
        Args:
            request: HTTP请求对象
            view: 视图对象
            
        Returns:
            bool: 是否有权限
        """
        # 读取权限对所有用户开放
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # 写操作需要用户已认证且为管理员
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_staff
        )


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    所有者或只读权限
    
    允许对象的所有者进行所有操作，其他用户只能进行读取操作
    """
    
    def has_object_permission(self, request, view, obj):
        """
        检查用户是否有权限操作特定对象
        
        Args:
            request: HTTP请求对象
            view: 视图对象
            obj: 要操作的对象
            
        Returns:
            bool: 是否有权限
        """
        # 读取权限对所有用户开放
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # 写操作需要用户为对象的所有者
        # 这里假设对象有owner或author字段
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        elif hasattr(obj, 'author'):
            return obj.author == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False


class IsStaffOrOwnerOrReadOnly(permissions.BasePermission):
    """
    管理员、所有者或只读权限
    
    允许管理员和对象所有者进行所有操作，其他用户只能进行读取操作
    """
    
    def has_permission(self, request, view):
        """
        检查用户是否有权限访问视图
        """
        # 读取权限对所有用户开放
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # 写操作需要用户已认证
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """
        检查用户是否有权限操作特定对象
        """
        # 读取权限对所有用户开放
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # 管理员有所有权限
        if request.user.is_staff:
            return True
        
        # 对象所有者有权限
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        elif hasattr(obj, 'author'):
            return obj.author == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False


class IsActiveUser(permissions.BasePermission):
    """
    激活用户权限
    
    只允许已激活的用户访问
    """
    
    def has_permission(self, request, view):
        """
        检查用户是否为已激活用户
        """
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_active
        )


class HasObjectPermission(permissions.BasePermission):
    """
    基于Guardian的对象级权限检查
    
    使用Django Guardian检查用户是否有特定对象的权限
    """
    
    # 子类需要定义所需的权限
    required_perms = []
    
    def has_object_permission(self, request, view, obj):
        """
        检查用户是否有对象的特定权限
        """
        if not request.user.is_authenticated:
            return False
        
        # 管理员有所有权限
        if request.user.is_staff:
            return True
        
        # 检查用户是否有所需的对象权限
        user_perms = get_perms(request.user, obj)
        
        # 根据请求方法确定所需权限
        if request.method in permissions.SAFE_METHODS:
            # 读取操作，检查view权限
            return any(perm in user_perms for perm in ['view', 'view_' + obj._meta.model_name])
        else:
            # 写操作，检查change权限
            return any(perm in user_perms for perm in ['change', 'change_' + obj._meta.model_name])


class CanEditArticle(HasObjectPermission):
    """
    文章编辑权限
    
    检查用户是否有编辑特定文章的权限
    """
    
    def has_object_permission(self, request, view, obj):
        """
        检查用户是否有编辑文章的权限
        """
        # 读取权限对所有用户开放（包括匿名用户）
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # 写操作需要用户已认证
        if not request.user.is_authenticated:
            return False
        
        # 管理员有所有权限
        if request.user.is_staff:
            return True
        
        # 文章作者有编辑权限
        if hasattr(obj, 'author') and obj.author == request.user:
            return True
        
        # 检查Guardian对象权限
        user_perms = get_perms(request.user, obj)
        return 'edit_article' in user_perms


#######################################
#             评论暂时不可编辑           #
#######################################
# class CanEditComment(HasObjectPermission):
#     """
#     评论编辑权限
    
#     检查用户是否有编辑特定评论的权限
#     """
    
#     def has_object_permission(self, request, view, obj):
#         """
#         检查用户是否有编辑评论的权限
#         """
#         if not request.user.is_authenticated:
#             return False
        
#         # 读取权限对所有用户开放
#         if request.method in permissions.SAFE_METHODS:
#             return True
        
#         # 管理员有所有权限
#         if request.user.is_staff:
#             return True
        
#         # 评论作者有编辑权限
#         if hasattr(obj, 'user') and obj.user == request.user:
#             return True
        
#         # 检查Guardian对象权限
#         user_perms = get_perms(request.user, obj)
#         return 'edit_comment' in user_perms
