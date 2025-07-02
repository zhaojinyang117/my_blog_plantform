from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from .serializers import UserSerializer, UserRegisterSerializer, UserProfileSerializer
from utils.email import send_verification_email
from drf_spectacular.utils import extend_schema, extend_schema_view
from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes


User = get_user_model()


@extend_schema(
    tags=["用户管理"],
    summary="用户注册",
    description="创建新用户账户，注册成功后会发送邮箱验证邮件",
    responses={
        201: {
            "description": "注册成功",
            "example": {
                "message": "用户注册成功，请前往邮箱验证",
                "user_id": 1,
                "email": "user@example.com"
            }
        },
        400: {
            "description": "请求数据无效",
            "example": {
                "username": ["该字段是必需的。"],
                "email": ["请输入一个有效的邮箱地址。"],
                "password": ["两次密码不一致"]
            }
        }
    }
)
class UserRegisterView(generics.CreateAPIView):
    """
    用户注册视图
    """

    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    # 权限类设置为允许任何人访问（包括未认证用户）
    # 这意味着任何人都可以调用这个注册接口，无需登录或特殊权限
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        """
        重写perform_create方法，在用户注册时发送验证邮件
        """
        user = serializer.save()
        send_verification_email(user)
        return user

    def create(self, request, *args, **kwargs):
        """
        重写create方法，返回自定义状态
        """
        # 1. 获取序列化器实例，传入请求数据
        serializer = self.get_serializer(data=request.data)

        # 2. 验证数据是否有效，如果无效会抛出异常
        serializer.is_valid(raise_exception=True)

        # 3. 调用perform_create方法创建用户并发送验证邮件
        user = self.perform_create(serializer)

        return Response(
            {
                "message": "用户注册成功，请前往邮箱验证",
                "user_id": user.id,
                "email": user.email,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    tags=["用户管理"],
    summary="邮箱验证",
    description="通过验证token激活用户账户",
    parameters=[
        OpenApiParameter(
            name="token",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            required=True,
            description="邮箱验证token"
        )
    ],
    responses={
        200: {
            "description": "验证成功或已验证",
            "example": {
                "message": "邮箱验证成功！您的账户已激活",
                "status": "success"
            }
        },
        400: {
            "description": "验证失败",
            "example": {
                "error": "无效的验证token"
            }
        }
    }
)
class EmailVerifyView(APIView):
    """
    邮箱验证视图
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        """
        处理邮箱验证请求
        """
        token = request.GET.get("token")

        if not token:
            return Response(
                {
                    "message": "缺少token参数",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email_verification_token=token)
            if user.is_active:
                return Response(
                    {
                        "message": "邮箱已验证",
                        "status": "already_verified",
                    },
                )
            user.is_active = True
            user.email_verification_token = ""  # type: ignore
            user.save(update_fields=["is_active", "email_verification_token"])

            return Response(
                {
                    "message": "邮箱验证成功！您的账户已激活",
                    "status": "success",
                },
                status=status.HTTP_200_OK,
            )

        except User.DoesNotExist:
            return Response(
                {
                    "error": "无效的验证token",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


################################
# 可以在这里写一个重新发送验证邮件视图#
################################


@extend_schema(
    tags=["用户管理"],
    summary="获取当前用户信息",
    description="获取当前登录用户的详细信息",
    responses={
        200: UserSerializer,
        401: {
            "description": "未认证",
            "example": {
                "detail": "身份认证信息未提供。"
            }
        }
    }
)
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


@extend_schema(
    tags=["用户管理"],
    summary="更新用户信息",
    description="更新当前登录用户的基本信息（用户名、个人简介等）",
    responses={
        200: UserSerializer,
        400: {
            "description": "请求数据无效",
            "example": {
                "username": ["该字段是必需的。"]
            }
        },
        401: {
            "description": "未认证",
            "example": {
                "detail": "身份认证信息未提供。"
            }
        }
    }
)
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


@extend_schema(
    tags=["用户管理"],
    summary="更新用户头像",
    description="上传并更新当前用户的头像图片",
    request={
        "multipart/form-data": {
            "type": "object",
            "properties": {
                "avatar": {
                    "type": "string",
                    "format": "binary",
                    "description": "头像图片文件"
                }
            },
            "required": ["avatar"]
        }
    },
    responses={
        200: {
            "description": "头像更新成功",
            "example": {
                "message": "头像更新成功",
                "avatar_url": "/media/avatars/user_1/avatar.jpg"
            }
        },
        400: {
            "description": "请求数据无效",
            "example": {
                "error": "请选择要上传的头像文件"
            }
        },
        401: {
            "description": "未认证",
            "example": {
                "detail": "身份认证信息未提供。"
            }
        }
    }
)
class UserAvatarUpdateView(generics.UpdateAPIView):
    """
    更新用户头像
    """

    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """
        获取要更新头像的用户对象信息
        """
        return self.request.user

    def patch(self, request, *args, **kwargs):
        """
        重写patch方法，更新用户头像
        处理头像上传
        """
        if "avatar" not in request.data:
            return Response(
                {
                    "error": "请选择要上传的头像文件",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        # 调用父类的update方法
        response = self.partial_update(request, *args, **kwargs)

        if response.status_code == 200:
            avatar_url = response.data.get("avatar") if response.data else None
            return Response(
                {
                    "message": "头像更新成功",
                    "avatar_url": avatar_url,
                },
                status=status.HTTP_200_OK,
            )
        return response
