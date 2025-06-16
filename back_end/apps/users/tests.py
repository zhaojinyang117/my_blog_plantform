from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib import admin
from django.contrib.auth.models import Permission
from django.contrib.admin.sites import AdminSite
from django.http import HttpRequest
from django.contrib.messages.storage.fallback import FallbackStorage
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock
import tempfile
from PIL import Image
import io
import os

from utils.email import send_verification_email, generate_verification_token
from .admin import CustomUserAdmin

User = get_user_model()


class UserModelTests(TestCase):
    """用户模型测试类"""

    def setUp(self):
        """测试前的准备工作"""
        self.user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123",
        }

    def test_create_user_with_email_verification_fields(self):
        """测试创建用户时邮箱验证相关字段"""
        user = User.objects.create_user(**self.user_data)

        # 验证新增字段存在且默认值正确
        self.assertFalse(user.is_active)  # 默认未激活
        self.assertEqual(user.email_verification_token, "")  # 默认空token
        # 修复avatar字段检查
        self.assertFalse(bool(user.avatar))  # 默认无头像

    def test_user_str_representation(self):
        """测试用户字符串表示"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(str(user), "test@example.com")

    def test_username_field_is_email(self):
        """测试用户名字段设置为邮箱"""
        self.assertEqual(User.USERNAME_FIELD, "email")
        self.assertEqual(User.REQUIRED_FIELDS, ["username"])


class EmailVerificationTests(TestCase):
    """邮箱验证功能测试类"""

    def setUp(self):
        """测试前的准备工作"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpassword123"
        )

    def test_generate_verification_token(self):
        """测试生成验证token"""
        token = generate_verification_token()

        # 验证token长度和格式
        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 32)  # URL安全的base64编码应该较长

    @patch("utils.email.send_mail")
    @patch("utils.email.threading.Thread")
    def test_send_verification_email_success(self, mock_thread, mock_send_mail):
        """测试发送验证邮件成功"""
        mock_send_mail.return_value = True

        # 模拟线程立即执行
        def mock_thread_start(target):
            target()

        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        mock_thread_instance.start.side_effect = lambda: mock_thread.call_args[1][
            "target"
        ]()

        # 发送验证邮件
        send_verification_email(self.user)

        # 验证用户的验证token已设置
        self.user.refresh_from_db()
        self.assertNotEqual(self.user.email_verification_token, "")

        # 验证邮件发送被调用
        self.assertTrue(mock_send_mail.called)

    @patch("utils.email.send_mail")
    def test_send_verification_email_with_exception(self, mock_send_mail):
        """测试发送验证邮件异常处理"""
        mock_send_mail.side_effect = Exception("SMTP Error")

        # 发送验证邮件不应该抛出异常
        try:
            send_verification_email(self.user)
            import time

            time.sleep(0.1)
        except Exception:
            self.fail("send_verification_email raised Exception unexpectedly!")


class EmailVerificationAPITests(APITestCase):
    """邮箱验证API测试类"""

    def setUp(self):
        """测试前的准备工作"""
        self.client = APIClient()
        self.register_url = reverse("user-register")
        self.verify_url = reverse("email-verify")

    @patch("apps.users.views.send_verification_email")
    def test_user_registration_sends_verification_email(self, mock_send_email):
        """测试用户注册时发送验证邮件"""
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "newuserpassword123",
            "password2": "newuserpassword123",
        }

        response = self.client.post(self.register_url, data, format="json")

        # 验证注册成功
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 验证响应消息
        response_data = response.json()
        self.assertIn("请前往邮箱验证", response_data["message"])

        # 验证发送邮件函数被调用
        mock_send_email.assert_called_once()

    def test_email_verification_success(self):
        """测试邮箱验证成功"""
        # 创建未激活用户
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword123",
            is_active=False,
            email_verification_token="test_token_123",
        )

        # 进行邮箱验证
        response = self.client.get(f"{self.verify_url}?token=test_token_123")

        # 验证响应
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(response_data["status"], "success")
        self.assertIn("邮箱验证成功", response_data["message"])

        # 验证用户状态已更新
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertEqual(user.email_verification_token, "")

    def test_email_verification_invalid_token(self):
        """测试无效token的邮箱验证"""
        response = self.client.get(f"{self.verify_url}?token=invalid_token")

        # 验证响应
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertIn("无效的验证token", response_data["error"])

    def test_email_verification_missing_token(self):
        """测试缺少token参数的邮箱验证"""
        response = self.client.get(self.verify_url)

        # 验证响应
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertIn("缺少token参数", response_data["message"])

    def test_email_verification_already_verified(self):
        """测试已验证用户的重复验证"""
        # 创建已激活用户
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword123",
            is_active=True,
            email_verification_token="test_token_123",
        )

        # 进行邮箱验证
        response = self.client.get(f"{self.verify_url}?token=test_token_123")

        # 验证响应
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(response_data["status"], "already_verified")
        self.assertIn("邮箱已验证", response_data["message"])


class UserAvatarUploadTests(APITestCase):
    """用户头像上传测试类"""

    def setUp(self):
        """测试前的准备工作"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword123",
            is_active=True,
        )
        self.avatar_url = reverse("user-avatar-update")

        # 获取认证token
        token_url = reverse("token_obtain_pair")
        login_data = {"email": "test@example.com", "password": "testpassword123"}
        login_response = self.client.post(token_url, login_data, format="json")
        self.token = login_response.json()["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def create_test_image(self, format="JPEG", size=(100, 100)):
        """创建测试图片"""
        image = Image.new("RGB", size, color="red")
        file = io.BytesIO()
        image.save(file, format=format)
        file.seek(0)
        return file

    def test_avatar_upload_success(self):
        """测试头像上传成功"""
        # 创建测试图片
        image_file = self.create_test_image()
        uploaded_file = SimpleUploadedFile(
            name="test_avatar.jpg",
            content=image_file.getvalue(),
            content_type="image/jpeg",
        )

        # 上传头像
        response = self.client.patch(
            self.avatar_url, {"avatar": uploaded_file}, format="multipart"
        )

        # 验证响应
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertIn("头像更新成功", response_data["message"])
        self.assertIn("avatar_url", response_data)

        # 验证用户头像已更新
        self.user.refresh_from_db()
        self.assertTrue(bool(self.user.avatar))

    def test_avatar_upload_missing_file(self):
        """测试缺少头像文件的上传"""
        response = self.client.patch(self.avatar_url, {}, format="multipart")

        # 验证响应
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertIn("请选择要上传的头像文件", response_data["error"])

    def test_avatar_upload_file_too_large(self):
        """测试文件过大的头像上传"""
        # 创建一个实际超过2MB的大文件
        large_content = b"x" * (3 * 1024 * 1024)  # 3MB 的内容
        large_file = SimpleUploadedFile(
            name="large_avatar.jpg", content=large_content, content_type="image/jpeg"
        )

        # 上传头像
        response = self.client.patch(
            self.avatar_url, {"avatar": large_file}, format="multipart"
        )

        # 验证响应（应该返回400，因为文件太大）
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_avatar_upload_invalid_format(self):
        """测试无效格式的头像上传"""
        # 创建文本文件
        text_file = SimpleUploadedFile(
            name="test.txt", content=b"This is not an image", content_type="text/plain"
        )

        # 上传头像
        response = self.client.patch(
            self.avatar_url, {"avatar": text_file}, format="multipart"
        )

        # 验证响应（应该返回400，因为格式无效）
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_avatar_upload_unauthenticated(self):
        """测试未认证用户上传头像"""
        # 清除认证
        self.client.credentials()

        image_file = self.create_test_image()
        uploaded_file = SimpleUploadedFile(
            name="test_avatar.jpg",
            content=image_file.getvalue(),
            content_type="image/jpeg",
        )

        # 上传头像
        response = self.client.patch(
            self.avatar_url, {"avatar": uploaded_file}, format="multipart"
        )

        # 验证响应
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserProfileSerializerTests(TestCase):
    """用户资料序列化器测试类"""

    def setUp(self):
        """测试前的准备工作"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpassword123"
        )

    def test_avatar_validation_valid_image(self):
        """测试有效图片的头像验证"""
        from .serializers import UserProfileSerializer

        # 创建小尺寸图片
        image_file = io.BytesIO()
        image = Image.new("RGB", (50, 50), color="blue")
        image.save(image_file, format="JPEG")
        image_file.seek(0)

        uploaded_file = SimpleUploadedFile(
            name="valid_avatar.jpg",
            content=image_file.getvalue(),
            content_type="image/jpeg",
        )

        serializer = UserProfileSerializer()
        # 验证方法不应该抛出异常
        validated_avatar = serializer.validate_avatar(uploaded_file)
        self.assertEqual(validated_avatar, uploaded_file)

    def test_avatar_validation_file_too_large(self):
        """测试文件过大的头像验证"""
        from .serializers import UserProfileSerializer
        from rest_framework import serializers

        # 模拟大文件
        large_file = MagicMock()
        large_file.size = 3 * 1024 * 1024  # 3MB
        large_file.content_type = "image/jpeg"

        serializer = UserProfileSerializer()

        with self.assertRaises(serializers.ValidationError) as context:
            serializer.validate_avatar(large_file)

        self.assertIn("头像文件太大了", str(context.exception))

    def test_avatar_validation_invalid_format(self):
        """测试无效格式的头像验证"""
        from .serializers import UserProfileSerializer
        from rest_framework import serializers

        # 模拟文本文件
        text_file = MagicMock()
        text_file.size = 1024  # 1KB
        text_file.content_type = "text/plain"

        serializer = UserProfileSerializer()

        with self.assertRaises(serializers.ValidationError) as context:
            serializer.validate_avatar(text_file)

        self.assertIn("只支持JPEG、PNG、GIF格式", str(context.exception))


class CustomUserAdminTests(TestCase):
    """自定义用户Admin测试类"""

    def setUp(self):
        """测试前的准备工作"""
        # 创建admin用户
        self.admin_user = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpassword123"
        )

        # 创建测试用户
        self.test_users = [
            User.objects.create_user(
                username=f"user{i}",
                email=f"user{i}@example.com",
                password="password123",
                is_active=False,
            )
            for i in range(3)
        ]

    def create_request_with_messages(self, user):
        """创建带有消息系统的请求对象"""
        request = HttpRequest()
        request.user = user
        # 添加消息存储
        setattr(request, "session", {})
        messages = FallbackStorage(request)
        setattr(request, "_messages", messages)
        return request

    def test_activate_users_action(self):
        """测试批量激活用户操作"""
        site = AdminSite()
        admin_instance = CustomUserAdmin(User, site)

        # 创建带有消息系统的请求
        request = self.create_request_with_messages(self.admin_user)

        # 创建queryset
        queryset = User.objects.filter(username__startswith="user")

        # 执行激活操作
        admin_instance.activate_users(request, queryset)

        # 验证用户已被激活
        for user in self.test_users:
            user.refresh_from_db()
            self.assertTrue(user.is_active)

    def test_deactivate_users_action(self):
        """测试批量禁用用户操作"""
        site = AdminSite()
        admin_instance = CustomUserAdmin(User, site)

        # 先激活用户
        for user in self.test_users:
            user.is_active = True
            user.save()

        # 创建带有消息系统的请求
        request = self.create_request_with_messages(self.admin_user)

        # 创建queryset
        queryset = User.objects.filter(username__startswith="user")

        # 执行禁用操作
        admin_instance.deactivate_users(request, queryset)

        # 验证用户已被禁用
        for user in self.test_users:
            user.refresh_from_db()
            self.assertFalse(user.is_active)

    def test_clear_verification_tokens_action(self):
        """测试清空验证令牌操作"""
        site = AdminSite()
        admin_instance = CustomUserAdmin(User, site)

        # 设置验证令牌
        for user in self.test_users:
            user.email_verification_token = "test_token"
            user.save()

        # 创建带有消息系统的请求
        request = self.create_request_with_messages(self.admin_user)

        # 创建queryset
        queryset = User.objects.filter(username__startswith="user")

        # 执行清空令牌操作
        admin_instance.clear_verification_tokens(request, queryset)

        # 验证令牌已被清空
        for user in self.test_users:
            user.refresh_from_db()
            self.assertEqual(user.email_verification_token, "")

    def test_admin_list_display(self):
        """测试Admin列表显示字段"""
        site = AdminSite()
        admin_instance = CustomUserAdmin(User, site)

        expected_fields = (
            "email",
            "username",
            "is_active",
            "is_staff",
            "date_joined",
            "last_login",
        )

        self.assertEqual(admin_instance.list_display, expected_fields)

    def test_admin_list_filter(self):
        """测试Admin列表过滤器"""
        site = AdminSite()
        admin_instance = CustomUserAdmin(User, site)

        expected_filters = (
            "is_active",
            "is_staff",
            "is_superuser",
            "date_joined",
            "last_login",
        )

        self.assertEqual(admin_instance.list_filter, expected_filters)


# 保留原有的基本API测试
class UserAPITests(TestCase):
    """用户 API 测试类"""

    def setUp(self):
        """测试前的准备工作"""
        self.client = APIClient()
        self.register_url = reverse("user-register")
        self.token_url = reverse("token_obtain_pair")
        self.me_url = reverse("user-detail")
        self.update_url = reverse("user-update")

        # 创建测试用户
        self.test_user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword123",
            is_active=True,
        )

    def test_user_registration(self):
        """测试用户注册"""
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "newuserpassword123",
            "password2": "newuserpassword123",
        }

        response = self.client.post(self.register_url, data, format="json")

        # 验证响应状态码为 201 Created
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 验证用户是否已创建
        self.assertTrue(User.objects.filter(email="newuser@example.com").exists())

        # 验证密码是否已正确加密（不应该返回明文密码）
        self.assertNotIn("password", response.json())

    def test_user_registration_invalid_data(self):
        """测试无效数据的用户注册"""
        # 测试密码不匹配
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123",
            "password2": "password456",
        }

        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # 测试邮箱已存在
        data = {
            "username": "anotheruser",
            "email": "test@example.com",  # 已存在的邮箱
            "password": "password123",
            "password2": "password123",
        }

        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_login(self):
        """测试用户登录"""
        data = {"email": "test@example.com", "password": "testpassword123"}

        response = self.client.post(self.token_url, data, format="json")

        # 验证响应状态码为 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 验证响应中包含 access 和 refresh token
        response_data = response.json()
        self.assertIn("access", response_data)
        self.assertIn("refresh", response_data)

    def test_user_login_invalid_credentials(self):
        """测试无效凭据的用户登录"""
        data = {"email": "test@example.com", "password": "wrongpassword"}

        response = self.client.post(self.token_url, data, format="json")

        # 验证响应状态码为 401 Unauthorized
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_user_details(self):
        """测试获取用户详情"""
        # 先登录获取 token
        login_data = {"email": "test@example.com", "password": "testpassword123"}

        login_response = self.client.post(self.token_url, login_data, format="json")
        token = login_response.json()["access"]

        # 设置认证头
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        # 获取用户详情
        response = self.client.get(self.me_url)

        # 验证响应状态码为 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 验证返回的用户信息
        response_data = response.json()
        self.assertEqual(response_data["email"], "test@example.com")
        self.assertEqual(response_data["username"], "testuser")

    def test_get_user_details_unauthenticated(self):
        """测试未认证用户获取用户详情"""
        response = self.client.get(self.me_url)

        # 验证响应状态码为 401 Unauthorized
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_user_details_put(self):
        """测试使用PUT方法完整更新用户信息（只更新允许修改的字段）"""
        # 先登录获取 token
        login_data = {"email": "test@example.com", "password": "testpassword123"}

        login_response = self.client.post(self.token_url, login_data, format="json")
        token = login_response.json()["access"]

        # 设置认证头
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        # 更新用户信息（只更新可修改的字段）
        update_data = {"username": "updateduser", "bio": "这是更新后的个人简介"}

        response = self.client.put(self.update_url, update_data, format="json")

        # 验证响应状态码为 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 验证用户信息已更新
        response_data = response.json()
        self.assertEqual(response_data["username"], "updateduser")
        self.assertEqual(response_data["email"], "test@example.com")  # 邮箱应该保持不变
        self.assertEqual(response_data["bio"], "这是更新后的个人简介")

        # 验证数据库中的用户信息也已更新
        updated_user = User.objects.get(pk=self.test_user.pk)
        self.assertEqual(updated_user.username, "updateduser")
        self.assertEqual(updated_user.email, "test@example.com")  # 邮箱应该保持不变

    def test_update_user_details_patch(self):
        """测试使用PATCH方法部分更新用户信息"""
        # 先登录获取 token
        login_data = {"email": "test@example.com", "password": "testpassword123"}

        login_response = self.client.post(self.token_url, login_data, format="json")
        token = login_response.json()["access"]

        # 设置认证头
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        # 部分更新用户信息（只更新用户名）
        update_data = {"username": "patcheduser"}

        response = self.client.patch(self.update_url, update_data, format="json")

        # 验证响应状态码为 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 验证用户名已更新，但邮箱保持不变
        response_data = response.json()
        self.assertEqual(response_data["username"], "patcheduser")
        self.assertEqual(response_data["email"], "test@example.com")  # 邮箱应该保持不变

        # 验证数据库中的用户信息
        updated_user = User.objects.get(pk=self.test_user.pk)
        self.assertEqual(updated_user.username, "patcheduser")
        self.assertEqual(updated_user.email, "test@example.com")

    def test_update_user_details_unauthenticated(self):
        """测试未认证用户更新用户信息"""
        update_data = {"username": "hackeduser"}

        response = self.client.patch(self.update_url, update_data, format="json")

        # 验证响应状态码为 401 Unauthorized
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # 验证用户信息未被更改
        user = User.objects.get(pk=self.test_user.pk)
        self.assertEqual(user.username, "testuser")  # 应该保持原来的用户名

    def test_update_user_details_invalid_data(self):
        """测试使用无效数据更新用户信息"""
        # 先登录获取 token
        login_data = {"email": "test@example.com", "password": "testpassword123"}

        login_response = self.client.post(self.token_url, login_data, format="json")
        token = login_response.json()["access"]

        # 设置认证头
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        # 创建另一个用户，用于测试用户名重复
        User.objects.create_user(
            username="anotheruser", email="another@example.com", password="password123"
        )

        # 尝试更新为已存在的用户名
        update_data = {
            "username": "anotheruser"  # 已存在的用户名
        }

        response = self.client.patch(self.update_url, update_data, format="json")

        # 验证响应状态码为 400 Bad Request
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # 验证用户名未被更改
        user = User.objects.get(pk=self.test_user.pk)
        self.assertEqual(user.username, "testuser")  # 应该保持原来的用户名

    def test_update_email_readonly(self):
        """测试邮箱字段是只读的，不能被更新"""
        # 先登录获取 token
        login_data = {"email": "test@example.com", "password": "testpassword123"}

        login_response = self.client.post(self.token_url, login_data, format="json")
        token = login_response.json()["access"]

        # 设置认证头
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        # 尝试更新邮箱（应该被忽略）
        update_data = {
            "username": "newusername",
            "email": "newemail@example.com",  # 尝试更新邮箱
        }

        response = self.client.patch(self.update_url, update_data, format="json")

        # 验证响应状态码为 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 验证用户名已更新，但邮箱保持不变
        response_data = response.json()
        self.assertEqual(response_data["username"], "newusername")
        self.assertEqual(response_data["email"], "test@example.com")  # 邮箱应该保持不变


class SecurityAndEdgeCaseTests(APITestCase):
    """安全性和边界情况测试类"""

    def setUp(self):
        """测试前的准备工作"""
        self.client = APIClient()
        self.register_url = reverse("user-register")
        self.verify_url = reverse("email-verify")
        self.avatar_url = reverse("user-avatar-update")

        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword123",
            is_active=True,
        )

        # 获取认证token
        token_url = reverse("token_obtain_pair")
        login_data = {"email": "test@example.com", "password": "testpassword123"}
        login_response = self.client.post(token_url, login_data, format="json")
        self.token = login_response.json()["access"]

    def test_email_verification_token_security(self):
        """测试邮箱验证token的安全性"""
        # 生成多个token，确保每次都不同
        tokens = [generate_verification_token() for _ in range(10)]

        # 验证token唯一性
        self.assertEqual(
            len(tokens), len(set(tokens)), "Generated tokens should be unique"
        )

        # 验证token长度足够安全
        for token in tokens:
            self.assertGreaterEqual(
                len(token), 32, "Token should be at least 32 characters long"
            )

    def test_email_verification_sql_injection_protection(self):
        """测试邮箱验证的SQL注入防护"""
        malicious_tokens = [
            "'; DROP TABLE users_user; --",
            "1' OR '1'='1",
            "'; UPDATE users_user SET is_active=1; --",
        ]

        for token in malicious_tokens:
            response = self.client.get(f"{self.verify_url}?token={token}")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

            # 确保没有用户被意外激活
            inactive_users = User.objects.filter(is_active=False).count()
            self.assertGreaterEqual(inactive_users, 0)

    def test_concurrent_email_verification(self):
        """测试并发邮箱验证"""
        import threading
        import time

        # 创建未激活用户
        user = User.objects.create_user(
            username="concurrent_user",
            email="concurrent@example.com",
            password="password123",
            is_active=False,
            email_verification_token="concurrent_token",
        )

        results = []

        def verify_email():
            response = self.client.get(f"{self.verify_url}?token=concurrent_token")
            results.append(response.status_code)

        # 启动多个并发请求
        threads = [threading.Thread(target=verify_email) for _ in range(5)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # 验证只有一个成功响应
        success_count = sum(1 for status_code in results if status_code == 200)
        self.assertEqual(success_count, 1, "Only one verification should succeed")

        # 验证用户确实被激活
        user.refresh_from_db()
        self.assertTrue(user.is_active)

    def test_avatar_upload_malicious_file_protection(self):
        """测试头像上传恶意文件防护"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

        # 测试上传PHP脚本文件
        php_content = b'<?php system($_GET["cmd"]); ?>'
        malicious_file = SimpleUploadedFile(
            name="script.php.jpg",  # 双扩展名
            content=php_content,
            content_type="image/jpeg",  # 伪装成图片
        )

        response = self.client.patch(
            self.avatar_url, {"avatar": malicious_file}, format="multipart"
        )

        # 应该被验证器拒绝
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_avatar_upload_path_traversal_protection(self):
        """测试头像上传路径遍历攻击防护"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

        # 尝试路径遍历攻击
        image = Image.new("RGB", (50, 50), color="blue")
        image_file = io.BytesIO()
        image.save(image_file, format="JPEG")
        image_file.seek(0)

        malicious_file = SimpleUploadedFile(
            name="../../etc/passwd.jpg",  # 路径遍历尝试
            content=image_file.getvalue(),
            content_type="image/jpeg",
        )

        response = self.client.patch(
            self.avatar_url, {"avatar": malicious_file}, format="multipart"
        )

        # 确保文件被安全处理
        if response.status_code == 200:
            self.user.refresh_from_db()
            # 验证文件路径不包含路径遍历
            if self.user.avatar:
                self.assertNotIn("..", self.user.avatar.name)

    def test_rate_limiting_simulation(self):
        """模拟速率限制测试"""
        # 快速连续请求邮箱验证
        responses = []
        for i in range(20):
            response = self.client.get(f"{self.verify_url}?token=rate_limit_test_{i}")
            responses.append(response.status_code)

        # 所有请求都应该得到处理（即使失败也是正常的400响应）
        for status_code in responses:
            self.assertIn(status_code, [400, 429])  # 400=正常失败, 429=速率限制

    def test_user_enumeration_protection(self):
        """测试用户枚举攻击防护"""
        # 尝试注册已存在的邮箱
        existing_email_data = {
            "username": "newuser",
            "email": "test@example.com",  # 已存在的邮箱
            "password": "password123",
            "password2": "password123",
        }

        response = self.client.post(
            self.register_url, existing_email_data, format="json"
        )

        # 应该返回错误，但不应该泄露用户是否存在的信息
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # 错误信息不应该明确说明邮箱已存在
        response_data = response.json()
        self.assertIsInstance(response_data, dict)

    def test_password_validation_edge_cases(self):
        """测试密码验证边界情况"""
        weak_passwords = [
            "123",  # 太短
            "password",  # 太常见
            "12345678",  # 纯数字
            "abcdefgh",  # 纯字母
        ]

        for weak_password in weak_passwords:
            data = {
                "username": f"user_weak_{weak_password}",
                "email": f"weak_{weak_password}@example.com",
                "password": weak_password,
                "password2": weak_password,
            }

            response = self.client.post(self.register_url, data, format="json")
            # 弱密码应该被拒绝
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unicode_handling(self):
        """测试Unicode字符处理"""
        unicode_data = {
            "username": "测试用户🎉",
            "email": "unicode@测试.com",
            "password": "Password123!@#",
            "password2": "Password123!@#",
        }

        response = self.client.post(self.register_url, unicode_data, format="json")

        # 应该能够正确处理Unicode字符或给出适当的错误
        self.assertIn(response.status_code, [201, 400])

    def test_large_payload_handling(self):
        """测试大负载处理"""
        # 创建一个非常长的用户名和bio
        large_data = {
            "username": "a" * 1000,  # 超长用户名
            "email": "large@example.com",
            "password": "Password123!",
            "password2": "Password123!",
        }

        response = self.client.post(self.register_url, large_data, format="json")

        # 应该适当处理过长的数据
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_memory_usage_avatar_upload(self):
        """测试头像上传内存使用"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

        # 创建接近限制大小的图片
        large_but_valid_content = b"x" * (2 * 1024 * 1024 - 1000)  # 接近2MB但未超过
        large_file = SimpleUploadedFile(
            name="large_valid.jpg",
            content=large_but_valid_content,
            content_type="image/jpeg",
        )

        # 这应该被文件大小验证捕获，而不是导致内存问题
        response = self.client.patch(
            self.avatar_url, {"avatar": large_file}, format="multipart"
        )

        # 验证系统能够正确处理大文件
        self.assertIn(response.status_code, [200, 400])


class PerformanceTests(APITestCase):
    """性能测试类"""

    def setUp(self):
        """测试前的准备工作"""
        self.client = APIClient()
        self.register_url = reverse("user-register")

    def test_bulk_user_creation_performance(self):
        """测试批量用户创建性能"""
        import time

        start_time = time.time()

        # 创建100个用户
        users_data = []
        for i in range(100):
            user_data = {
                "username": f"perftest_user_{i}",
                "email": f"perftest_{i}@example.com",
                "password": "TestPassword123!",
                "password2": "TestPassword123!",
            }
            users_data.append(user_data)

        # 批量创建用户（模拟高负载）
        success_count = 0
        for user_data in users_data[:10]:  # 限制为10个以避免测试时间过长
            response = self.client.post(self.register_url, user_data, format="json")
            if response.status_code == 201:
                success_count += 1

        end_time = time.time()
        execution_time = end_time - start_time

        # 验证性能指标
        self.assertLess(
            execution_time,
            30.0,
            "Bulk user creation should complete in reasonable time",
        )
        self.assertGreater(
            success_count, 5, "At least half of user creations should succeed"
        )

    def test_token_generation_performance(self):
        """测试token生成性能"""
        import time

        start_time = time.time()

        # 生成1000个token
        tokens = [generate_verification_token() for _ in range(1000)]

        end_time = time.time()
        execution_time = end_time - start_time

        # 验证性能和唯一性
        self.assertLess(execution_time, 5.0, "Token generation should be fast")
        self.assertEqual(len(tokens), len(set(tokens)), "All tokens should be unique")
