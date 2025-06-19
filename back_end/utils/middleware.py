"""
权限控制中间件模块

提供路由级权限控制功能，包括管理后台访问限制等
"""

from django.http import HttpResponseForbidden
from django.contrib.auth.models import AnonymousUser
from django.utils.deprecation import MiddlewareMixin
import logging

logger = logging.getLogger(__name__)


class AdminOnlyMiddleware(MiddlewareMixin):
    """
    管理后台访问限制中间件
    
    确保只有管理员用户可以访问Django Admin界面
    非管理员用户访问admin路由时返回403禁止访问
    """
    
    def process_request(self, request):
        """
        处理请求，检查admin路由的访问权限
        
        Args:
            request: HTTP请求对象
            
        Returns:
            HttpResponseForbidden: 如果非管理员访问admin路由
            None: 允许继续处理请求
        """
        # 检查是否访问admin路由
        if request.path.startswith('/admin/'):
            # 检查用户是否已认证且为管理员
            if isinstance(request.user, AnonymousUser) or not request.user.is_authenticated:
                logger.warning(f"未认证用户尝试访问admin界面: {request.META.get('REMOTE_ADDR', 'unknown')}")
                return HttpResponseForbidden("访问被拒绝：需要管理员权限")
            
            if not request.user.is_staff:
                logger.warning(f"非管理员用户 {request.user.email} 尝试访问admin界面")
                return HttpResponseForbidden("访问被拒绝：需要管理员权限")
        
        # 允许继续处理请求
        return None


class UserActivityMiddleware(MiddlewareMixin):
    """
    用户活动记录中间件
    
    记录用户的登录活动，包括登录次数和IP地址
    为后续的数据统计功能做准备
    """
    
    def process_request(self, request):
        """
        处理请求，记录用户活动信息
        
        Args:
            request: HTTP请求对象
        """
        # 只记录已认证用户的活动
        if request.user.is_authenticated and hasattr(request.user, 'login_count'):
            # 获取客户端IP地址
            client_ip = self.get_client_ip(request)
            
            # 更新用户活动信息（这里先预留，等后续阶段实现）
            # request.user.last_login_ip = client_ip
            # request.user.login_count += 1
            # request.user.save(update_fields=['last_login_ip', 'login_count'])
            
            logger.debug(f"用户 {request.user.email} 活动记录: IP={client_ip}")
        
        return None
    
    def get_client_ip(self, request):
        """
        获取客户端真实IP地址
        
        Args:
            request: HTTP请求对象
            
        Returns:
            str: 客户端IP地址
        """
        # 尝试从代理头获取真实IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        
        return ip
