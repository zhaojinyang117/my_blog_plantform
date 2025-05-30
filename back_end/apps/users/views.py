from rest_framework import generics, permissions
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .serializers import UserSerializer, UserRegisterSerializer


User = get_user_model()


class UserRegisterView(generics.CreateAPIView):
    """
    用户注册视图
    """

    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    # 权限类设置为允许任何人访问（包括未认证用户）
    # 这意味着任何人都可以调用这个注册接口，无需登录或特殊权限
    permission_classes = [permissions.AllowAny]


class UserDetailView(generics.RetrieveAPIView):
    """
    获取当前用户信息
    登录后行为
    """

    serializer_class = UserSerializer
    # 权限类设置为只有已认证用户才能访问
    # 这意味着用户必须先登录才能获取和更新自己的用户信息
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """
        获取当前用户信息
        这个方法重写了父类的get_object方法，用于指定要检索的对象
        在RetrieveAPIView中，get_object方法用于确定要返回的具体对象实例
        这里返回当前请求的用户对象，即已登录的用户
        """
        return self.request.user


class UserUpdateView(generics.UpdateAPIView):
    """
    更新当前用户信息
    支持PUT和PATCH方法
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """
        获取要更新的用户对象
        """
        return self.request.user