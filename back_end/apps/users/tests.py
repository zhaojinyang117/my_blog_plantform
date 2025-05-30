from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


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
            username="testuser", email="test@example.com", password="testpassword123"
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

        # 验证数据库中的邮箱确实没有被更改
        user = User.objects.get(pk=self.test_user.pk)
        self.assertEqual(user.email, "test@example.com")  # 邮箱应该保持不变
