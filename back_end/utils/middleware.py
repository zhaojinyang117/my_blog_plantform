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


class UserActivityMiddleware:
    """
    用户活动记录中间件
    
    记录用户的登录活动，包括登录次数和IP地址
    使用现代Django中间件风格，可以在请求前后处理数据
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 在处理请求前，如果是登录请求则捕获邮箱信息
        login_email = self.capture_login_email(request)
        
        # 处理请求
        response = self.get_response(request)
        
        # 处理响应 - 检查是否为成功登录
        if (login_email and 
            request.path == '/api/users/token/' and 
            request.method == 'POST' and 
            response.status_code == 200):
            
            self.record_user_activity(login_email, request)
        
        return response
    
    def capture_login_email(self, request):
        """
        在请求处理前捕获登录邮箱信息
        
        Args:
            request: HTTP请求对象
            
        Returns:
            str: 用户邮箱或None
        """
        if (request.path == '/api/users/token/' and 
            request.method == 'POST'):
            
            try:
                import json
                
                # 尝试从不同来源获取邮箱
                email = None
                
                # 首先尝试从POST数据获取（表单提交）
                if hasattr(request, 'POST') and request.POST:
                    email = request.POST.get('email')
                    logger.debug(f"从POST获取登录邮箱: {email}")
                
                # 如果POST中没有，尝试从body获取（JSON提交）
                if not email and hasattr(request, 'body') and request.body:
                    try:
                        # 读取原始body数据
                        body_data = request.body.decode('utf-8')
                        data = json.loads(body_data)
                        email = data.get('email')
                        logger.debug(f"从body获取登录邮箱: {email}")
                    except (json.JSONDecodeError, UnicodeDecodeError) as e:
                        logger.debug(f"解析body数据失败: {e}")
                
                if email:
                    logger.debug(f"成功捕获登录邮箱: {email}")
                    return email
                else:
                    logger.debug("未能捕获登录邮箱")
                    
            except Exception as e:
                logger.error(f"捕获登录邮箱时出错: {e}")
        
        return None
    
    def record_user_activity(self, email, request):
        """
        记录用户活动信息
        
        Args:
            email: 用户邮箱
            request: HTTP请求对象
        """
        try:
            from django.contrib.auth import get_user_model
            
            User = get_user_model()
            
            # 获取客户端IP地址
            client_ip = self.get_client_ip(request)
            logger.debug(f"获取到客户端IP: {client_ip}")
            
            # 查找用户并更新活动信息
            user = User.objects.get(email=email, is_active=True)
            
            # 更新用户活动信息
            user.last_login_ip = client_ip
            user.login_count += 1
            user.save(update_fields=['last_login_ip', 'login_count'])
            
            logger.info(f"用户 {user.email} 活动更新: IP={client_ip}, 登录次数={user.login_count}")
            
        except User.DoesNotExist:
            logger.warning(f"用户不存在: {email}")
        except Exception as e:
            logger.error(f"更新用户活动信息失败: {e}")
    
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
