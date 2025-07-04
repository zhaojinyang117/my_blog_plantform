from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    UserRegisterView,
    UserDetailView,
    UserUpdateView,
    UserAvatarUpdateView,
    EmailVerifyView,
)

urlpatterns = [
    # 用户注册
    path("register/", UserRegisterView.as_view(), name="user-register"),
    path("verify-email/", EmailVerifyView.as_view(), name="email-verify"),
    # 获取当前用户信息
    path("me/", UserDetailView.as_view(), name="user-detail"),
    # 更新当前用户信息
    path("me/update/", UserUpdateView.as_view(), name="user-update"),
    path("me/avatar/", UserAvatarUpdateView.as_view(), name="user-avatar-update"),
    # JWT 认证
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
