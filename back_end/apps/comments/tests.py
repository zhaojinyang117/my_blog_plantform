from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from apps.articles.models import Article  # 假设文章模型在此
from .models import Comment
from rest_framework_simplejwt.tokens import AccessToken
from utils.text_filter import SensitiveWordFilter, CommentContentFilter, filter_comment_content
import threading

User = get_user_model()

# 测试常量
TEST_CONTENT_EMPTY = ""
TEST_CONTENT_WHITESPACE = "   \n\t   "
TEST_CONTENT_LONG = "A" * 10000
TEST_CONTENT_SPECIAL = "测试中文 & <script>alert('xss')</script> 特殊字符 @#$%^&*()"
TEST_CONTENT_UNICODE = "🎉 Emoji test 🚀 中文测试 العربية"
TEST_CONTENT_MULTILINE = "Line 1\nLine 2\nLine 3"
TEST_CONTENT_NUMERIC = "123456789"


class CommentAPITests(APITestCase):
    def setUp(self):
        # 创建用户
        self.user1 = User.objects.create_user(
            username="user1", email="user1@example.com", password="password123", is_active=True
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@example.com", password="password123", is_active=True
        )

        # 创建文章
        self.article1 = Article.objects.create(
            title="Test Article 1", content="Content for article 1", author=self.user1
        )
        self.article2 = Article.objects.create(
            title="Test Article 2", content="Content for article 2", author=self.user1
        )

        # URL 名称假设 (需要与你的 urls.py 配置一致)
        # 例如: articles_router.register(r'comments', CommentViewSet, basename='article-comments')
        self.list_create_url_article1 = reverse(
            "article-comments-list", kwargs={"article_pk": self.article1.pk}
        )
        self.list_create_url_article2 = reverse(
            "article-comments-list", kwargs={"article_pk": self.article2.pk}
        )

        # 顶级评论
        self.comment1_article1 = Comment.objects.create(
            article=self.article1,
            user=self.user1,
            content="This is the first comment on article 1.",
        )
        # 回复评论
        self.reply1_to_comment1 = Comment.objects.create(
            article=self.article1,
            user=self.user2,
            content="This is a reply to the first comment.",
            parent=self.comment1_article1,
        )

        # Generate JWT tokens for users
        self.access_token_user1 = str(AccessToken.for_user(self.user1))
        self.access_token_user2 = str(AccessToken.for_user(self.user2))

    def authenticate_user(self, user_token):
        """辅助方法：为用户设置认证"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {user_token}")

    def clear_authentication(self):
        """辅助方法：清除认证"""
        self.client.credentials()

    def create_comment(self, article_url, content, parent=None, user_token=None):
        """辅助方法：创建评论"""
        if user_token:
            self.authenticate_user(user_token)

        data = {"content": content}
        if parent:
            data["parent"] = parent

        response = self.client.post(article_url, data)

        if user_token:
            self.clear_authentication()

        return response

    def get_comment_detail_url(self, article_pk, comment_pk):
        """辅助方法：获取评论详情URL"""
        return reverse(
            "article-comments-detail",
            kwargs={"article_pk": article_pk, "pk": comment_pk},
        )

    def assert_comment_response_structure(
        self, response_data, expected_replies_count=None
    ):
        """辅助方法：验证评论响应结构"""
        required_fields = ["id", "user", "article", "content", "created_at", "replies"]
        for field in required_fields:
            self.assertIn(field, response_data)

        if expected_replies_count is not None:
            self.assertEqual(len(response_data["replies"]), expected_replies_count)

    def test_list_comments_for_article(self):
        """测试获取文章的评论列表，应只包含顶级评论，并嵌套回复"""
        response = self.client.get(self.list_create_url_article1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 检查分页响应结构和顶级评论数量
        self.assertIn("count", response.data)
        self.assertIn("results", response.data)
        self.assertEqual(response.data["count"], 1)  # article1 只有一个顶级评论
        self.assertEqual(len(response.data["results"]), 1)

        # 检查顶级评论的内容
        top_comment_data = response.data["results"][0]
        self.assertEqual(top_comment_data["id"], self.comment1_article1.id)
        self.assertEqual(top_comment_data["content"], self.comment1_article1.content)

        # 检查回复
        self.assertIn("replies", top_comment_data)
        self.assertEqual(len(top_comment_data["replies"]), 1)
        reply_data = top_comment_data["replies"][0]
        self.assertEqual(reply_data["id"], self.reply1_to_comment1.id)
        self.assertEqual(reply_data["content"], self.reply1_to_comment1.content)
        self.assertEqual(reply_data["parent"], self.comment1_article1.id)

    def test_list_comments_for_non_existent_article(self):
        """测试获取不存在文章的评论列表应返回404"""
        non_existent_article_pk = 999
        url = reverse(
            "article-comments-list", kwargs={"article_pk": non_existent_article_pk}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_top_level_comment_authenticated(self):
        """测试认证用户创建顶级评论"""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access_token_user1)
        data = {"content": "A new top-level comment"}
        response = self.client.post(self.list_create_url_article1, data)
        self.client.credentials()  # Clear credentials
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            Comment.objects.filter(
                article=self.article1, content=data["content"], parent__isnull=True
            ).count(),
            1,
        )  # Should find 1 comment with this specific new content
        new_comment = Comment.objects.get(
            article=self.article1, content=data["content"], parent__isnull=True
        )  # Be more specific with get
        self.assertEqual(new_comment.user, self.user1)
        self.assertIsNone(new_comment.parent)

    def test_create_reply_comment_authenticated(self):
        """测试认证用户创建回复评论"""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access_token_user2)
        data = {"content": "A reply from user2", "parent": self.comment1_article1.pk}
        response = self.client.post(self.list_create_url_article1, data)
        self.client.credentials()  # Clear credentials
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            Comment.objects.filter(
                article=self.article1,
                content=data["content"],
                parent=self.comment1_article1,
            ).count(),
            1,
        )
        new_reply = Comment.objects.get(
            article=self.article1,
            content=data["content"],
            parent=self.comment1_article1,
        )
        self.assertEqual(new_reply.user, self.user2)
        self.assertEqual(new_reply.parent, self.comment1_article1)

    def test_create_comment_unauthenticated(self):
        """测试未认证用户创建评论应失败"""
        data = {"content": "Attempt to comment unauthenticated"}
        response = self.client.post(self.list_create_url_article1, data)
        # IsAuthenticatedOrReadOnly: GET is allowed, POST requires authentication
        self.assertEqual(
            response.status_code, status.HTTP_401_UNAUTHORIZED
        )  # or 403 if using IsAuthenticated

    def test_create_reply_to_comment_in_different_article_fail(self):
        """测试回复一个不属于当前文章的评论应失败"""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access_token_user1)
        # comment1_article1 属于 article1, 但我们尝试在 article2 的URL下创建回复
        data = {
            "content": "Reply to comment in wrong article",
            "parent": self.comment1_article1.pk,
        }
        response = self.client.post(self.list_create_url_article2, data)
        self.client.credentials()  # Clear credentials
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("parent", response.data)  # 应该有关于 parent 字段的错误信息

    def test_create_comment_with_non_existent_parent_fail(self):
        """测试回复一个不存在的父评论ID应失败"""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access_token_user1)
        data = {"content": "Reply to non-existent parent", "parent": 9999}
        response = self.client.post(self.list_create_url_article1, data)
        self.client.credentials()  # Clear credentials
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("parent", response.data)

    def test_delete_own_comment_authenticated(self):
        """测试认证用户删除自己的评论"""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access_token_user1)
        comment_to_delete = Comment.objects.create(
            article=self.article1, user=self.user1, content="Comment to be deleted"
        )
        # 假设删除URL为 /api/articles/<article_pk>/comments/<comment_pk>/
        delete_url = reverse(
            "article-comments-detail",
            kwargs={"article_pk": self.article1.pk, "pk": comment_to_delete.pk},
        )
        response = self.client.delete(delete_url)
        self.client.credentials()  # Clear credentials
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Comment.objects.filter(pk=comment_to_delete.pk).exists())

    def test_delete_others_comment_authenticated_fail(self):
        """测试认证用户删除他人评论应失败"""
        # comment1_article1 由 user1 创建
        self.client.credentials(
            HTTP_AUTHORIZATION="Bearer " + self.access_token_user2
        )  # user2 尝试删除 user1 的评论
        delete_url = reverse(
            "article-comments-detail",
            kwargs={"article_pk": self.article1.pk, "pk": self.comment1_article1.pk},
        )
        response = self.client.delete(delete_url)
        self.client.credentials()  # Clear credentials
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Comment.objects.filter(pk=self.comment1_article1.pk).exists())

    def test_delete_comment_unauthenticated_fail(self):
        """测试未认证用户删除评论应失败"""
        delete_url = reverse(
            "article-comments-detail",
            kwargs={"article_pk": self.article1.pk, "pk": self.comment1_article1.pk},
        )
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)  # or 403
        self.assertTrue(Comment.objects.filter(pk=self.comment1_article1.pk).exists())

    def test_delete_parent_comment_cascades_to_replies(self):
        """测试删除父评论时，其子评论（回复）也被级联删除"""
        self.client.credentials(
            HTTP_AUTHORIZATION="Bearer " + self.access_token_user1
        )  # user1 是 comment1_article1 的作者
        parent_comment_pk = self.comment1_article1.pk
        reply_pk = self.reply1_to_comment1.pk

        self.assertTrue(Comment.objects.filter(pk=parent_comment_pk).exists())
        self.assertTrue(Comment.objects.filter(pk=reply_pk).exists())

        delete_url = reverse(
            "article-comments-detail",
            kwargs={"article_pk": self.article1.pk, "pk": parent_comment_pk},
        )
        response = self.client.delete(delete_url)
        self.client.credentials()  # Clear credentials
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertFalse(Comment.objects.filter(pk=parent_comment_pk).exists())
        self.assertFalse(
            Comment.objects.filter(pk=reply_pk).exists(),
            "Reply should be cascade deleted",
        )

    def test_retrieve_comment_detail(self):
        """测试获取单个评论的详情"""
        url = reverse(
            "article-comments-detail",
            kwargs={"article_pk": self.article1.pk, "pk": self.comment1_article1.pk},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.comment1_article1.id)
        self.assertEqual(response.data["content"], self.comment1_article1.content)
        self.assertEqual(len(response.data["replies"]), 1)
        self.assertEqual(response.data["replies"][0]["id"], self.reply1_to_comment1.id)

    def test_create_comment_with_empty_content_fail(self):
        """测试创建空内容评论应失败"""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access_token_user1)
        data = {"content": ""}
        response = self.client.post(self.list_create_url_article1, data)
        self.client.credentials()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("content", response.data)

    def test_create_comment_with_whitespace_only_content_fail(self):
        """测试创建仅包含空白字符的评论应失败"""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access_token_user1)
        data = {"content": "   \n\t   "}
        response = self.client.post(self.list_create_url_article1, data)
        self.client.credentials()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("content", response.data)

    def test_create_comment_with_very_long_content(self):
        """测试创建超长内容评论（边界测试）"""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access_token_user1)
        # 创建一个很长的内容（假设系统允许，这里测试系统的处理能力）
        long_content = "A" * 10000  # 10000个字符
        data = {"content": long_content}
        response = self.client.post(self.list_create_url_article1, data)
        self.client.credentials()
        # 根据实际业务需求，这里可能是201（允许）或400（拒绝）
        self.assertIn(
            response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST]
        )

    def test_create_comment_with_special_characters(self):
        """测试创建包含特殊字符的评论"""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access_token_user1)
        special_content = "测试中文 & <script>alert('xss')</script> 特殊字符 @#$%^&*()"
        data = {"content": special_content}
        response = self.client.post(self.list_create_url_article1, data)
        self.client.credentials()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # 验证内容被正确保存（应该原样保存，XSS防护在前端处理）
        new_comment = Comment.objects.get(id=response.data["id"])
        self.assertEqual(new_comment.content, special_content)

    def test_retrieve_non_existent_comment_detail(self):
        """测试获取不存在评论的详情应返回404"""
        non_existent_comment_pk = 9999
        url = reverse(
            "article-comments-detail",
            kwargs={"article_pk": self.article1.pk, "pk": non_existent_comment_pk},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_non_existent_comment_fail(self):
        """测试删除不存在的评论应返回404"""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access_token_user1)
        non_existent_comment_pk = 9999
        url = reverse(
            "article-comments-detail",
            kwargs={"article_pk": self.article1.pk, "pk": non_existent_comment_pk},
        )
        response = self.client.delete(url)
        self.client.credentials()
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_comment_ordering_by_creation_time(self):
        """测试评论按创建时间排序"""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access_token_user1)

        # 创建多个评论
        comment_data = [
            {"content": "First comment"},
            {"content": "Second comment"},
            {"content": "Third comment"},
        ]

        created_comments = []
        for data in comment_data:
            response = self.client.post(self.list_create_url_article1, data)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            created_comments.append(response.data["id"])

        self.client.credentials()

        # 获取评论列表，验证排序
        response = self.client.get(self.list_create_url_article1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 验证评论按创建时间排序（包括原有的comment1_article1）
        comments = response.data["results"]
        self.assertEqual(len(comments), 4)  # 1个原有 + 3个新创建

        # 验证时间排序（created_at应该是递增的）
        for i in range(len(comments) - 1):
            current_time = comments[i]["created_at"]
            next_time = comments[i + 1]["created_at"]
            self.assertLessEqual(current_time, next_time)

    def test_pagination_functionality(self):
        """测试评论列表的分页功能"""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access_token_user1)

        # 创建足够多的评论来测试分页（假设每页10条）
        for i in range(15):
            data = {"content": f"Test comment {i}"}
            response = self.client.post(self.list_create_url_article1, data)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.client.credentials()

        # 测试第一页
        response = self.client.get(self.list_create_url_article1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("count", response.data)
        self.assertIn("next", response.data)
        self.assertIn("previous", response.data)
        self.assertIn("results", response.data)

        # 验证总数（15个新创建 + 1个原有的）
        self.assertEqual(response.data["count"], 16)

        # 验证第一页结果数量（应该是10条，根据settings中的PAGE_SIZE）
        self.assertEqual(len(response.data["results"]), 10)

        # 测试第二页
        if response.data["next"]:
            next_page_response = self.client.get(response.data["next"])
            self.assertEqual(next_page_response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(next_page_response.data["results"]), 6)  # 剩余6条

    def test_nested_replies_structure(self):
        """测试嵌套回复的数据结构"""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access_token_user2)

        # 创建多层回复
        reply_to_reply_data = {
            "content": "This is a reply to a reply",
            "parent": self.reply1_to_comment1.pk,
        }
        response = self.client.post(self.list_create_url_article1, reply_to_reply_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.client.credentials()

        # 获取评论列表，验证嵌套结构
        response = self.client.get(self.list_create_url_article1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 找到顶级评论
        top_comment = None
        for comment in response.data["results"]:
            if comment["id"] == self.comment1_article1.id:
                top_comment = comment
                break

        self.assertIsNotNone(top_comment)
        self.assertEqual(len(top_comment["replies"]), 2)  # 应该有2个回复

        # 验证回复的结构
        reply_ids = [reply["id"] for reply in top_comment["replies"]]
        self.assertIn(self.reply1_to_comment1.id, reply_ids)

    def test_comment_content_validation_edge_cases(self):
        """测试评论内容验证的边界情况"""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access_token_user1)

        # 测试只包含数字的内容
        data = {"content": "123456789"}
        response = self.client.post(self.list_create_url_article1, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 测试包含换行符的内容
        data = {"content": "Line 1\nLine 2\nLine 3"}
        response = self.client.post(self.list_create_url_article1, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 测试包含特殊Unicode字符的内容
        data = {"content": "🎉 Emoji test 🚀 中文测试 العربية"}
        response = self.client.post(self.list_create_url_article1, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.client.credentials()

    def test_concurrent_comment_creation(self):
        """测试并发创建评论的情况"""
        import threading
        import time

        results = []
        errors = []

        def create_comment(user_token, content):
            try:
                client = self.client_class()
                client.credentials(HTTP_AUTHORIZATION=f"Bearer {user_token}")
                data = {"content": content}
                response = client.post(self.list_create_url_article1, data)
                results.append(response.status_code)
                client.credentials()
            except Exception as e:
                errors.append(str(e))

        # 创建多个线程同时创建评论
        threads = []
        for i in range(5):
            thread = threading.Thread(
                target=create_comment,
                args=(self.access_token_user1, f"Concurrent comment {i}"),
            )
            threads.append(thread)

        # 启动所有线程
        for thread in threads:
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证结果
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 5)
        for status_code in results:
            self.assertEqual(status_code, status.HTTP_201_CREATED)


class CommentPermissionManagerTests(TestCase):
    """评论权限管理器测试类"""

    def setUp(self):
        """设置测试数据"""
        from utils.permission_manager import PermissionManager, CommentPermissionManager
        
        # 将权限管理器类设置为类属性，以便在测试方法中使用
        self.__class__.PermissionManager = PermissionManager
        self.__class__.CommentPermissionManager = CommentPermissionManager
        
        # 创建测试用户
        self.user1 = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="testpass123",
            is_active=True
        )
        self.user2 = User.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="testpass123",
            is_active=True
        )
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="testpass123",
            is_active=True,
            is_staff=True
        )
        
        # 创建测试文章和评论
        self.article1 = Article.objects.create(
            title="测试文章1",
            content="测试内容1",
            author=self.user1
        )
        
        self.comment1 = Comment.objects.create(
            article=self.article1,
            user=self.user1,
            content="测试评论1"
        )
        
        self.comment2 = Comment.objects.create(
            article=self.article1,
            user=self.user2,
            content="测试评论2"
        )
        
        # 权限管理器实例
        self.permission_manager = PermissionManager()
        self.comment_permission_manager = CommentPermissionManager()

    def test_assign_user_permission_success(self):
        """测试成功分配用户权限"""
        # 分配审核权限
        result = self.permission_manager.assign_user_permission(
            self.user2,
            self.CommentPermissionManager.MODERATE_PERMISSION,
            self.comment1
        )
        
        self.assertTrue(result)
        
        # 验证权限是否正确分配
        has_permission = self.permission_manager.check_user_permission(
            self.user2,
            self.CommentPermissionManager.MODERATE_PERMISSION,
            self.comment1
        )
        self.assertTrue(has_permission)

    def test_assign_user_permission_invalid_user(self):
        """测试分配权限给无效用户"""
        # 使用None作为用户应该返回False
        result = self.permission_manager.assign_user_permission(
            None,
            self.CommentPermissionManager.MODERATE_PERMISSION,
            self.comment1
        )
        self.assertFalse(result)

    def test_check_user_permission_unauthenticated(self):
        """测试未认证用户权限检查"""
        from django.contrib.auth.models import AnonymousUser
        
        anonymous_user = AnonymousUser()
        
        # 未认证用户不应该有权限
        has_permission = self.permission_manager.check_user_permission(
            anonymous_user,
            self.CommentPermissionManager.MODERATE_PERMISSION,
            self.comment1
        )
        self.assertFalse(has_permission)

    def test_check_user_permission_admin(self):
        """测试管理员权限检查"""
        # 管理员应该有所有权限
        has_permission = self.permission_manager.check_user_permission(
            self.admin_user,
            self.CommentPermissionManager.MODERATE_PERMISSION,
            self.comment1
        )
        self.assertTrue(has_permission)

    def test_revoke_user_permission_success(self):
        """测试成功撤销用户权限"""
        # 先分配权限
        self.permission_manager.assign_user_permission(
            self.user2,
            self.CommentPermissionManager.MODERATE_PERMISSION,
            self.comment1
        )
        
        # 验证权限存在
        self.assertTrue(
            self.permission_manager.check_user_permission(
                self.user2,
                self.CommentPermissionManager.MODERATE_PERMISSION,
                self.comment1
            )
        )
        
        # 撤销权限
        result = self.permission_manager.remove_user_permission(
            self.user2,
            self.CommentPermissionManager.MODERATE_PERMISSION,
            self.comment1
        )
        
        self.assertTrue(result)
        
        # 验证权限已被撤销
        self.assertFalse(
            self.permission_manager.check_user_permission(
                self.user2,
                self.CommentPermissionManager.MODERATE_PERMISSION,
                self.comment1
            )
        )

    def test_bulk_assign_permissions_success(self):
        """测试批量分配权限成功"""
        permissions = [
            self.CommentPermissionManager.MODERATE_PERMISSION,
            self.CommentPermissionManager.REPLY_PERMISSION
        ]
        
        result = self.permission_manager.bulk_assign_permissions(
            self.user2,
            permissions,
            self.comment1
        )
        
        self.assertTrue(result)
        
        # 验证所有权限都已分配
        for permission in permissions:
            self.assertTrue(
                self.permission_manager.check_user_permission(
                    self.user2,
                    permission,
                    self.comment1
                )
            )

    def test_bulk_remove_permissions_success(self):
        """测试批量撤销权限成功"""
        permissions = [
            self.CommentPermissionManager.MODERATE_PERMISSION,
            self.CommentPermissionManager.REPLY_PERMISSION
        ]
        
        # 先分配权限
        self.permission_manager.bulk_assign_permissions(
            self.user2,
            permissions,
            self.comment1
        )
        
        # 验证权限存在
        for permission in permissions:
            self.assertTrue(
                self.permission_manager.check_user_permission(
                    self.user2,
                    permission,
                    self.comment1
                )
            )
        
        # 批量撤销权限
        result = self.permission_manager.bulk_remove_permissions(
            self.user2,
            permissions,
            self.comment1
        )
        
        self.assertTrue(result)
        
        # 验证权限已被撤销
        for permission in permissions:
            self.assertFalse(
                self.permission_manager.check_user_permission(
                    self.user2,
                    permission,
                    self.comment1
                )
            )

    def test_transfer_ownership_success(self):
        """测试成功转移所有权"""
        # 为原所有者分配权限
        self.comment_permission_manager.assign_author_permissions(
            self.user1,
            self.comment1
        )
        
        # 验证原所有者有权限
        self.assertTrue(
            self.permission_manager.check_user_permission(
                self.user1,
                self.CommentPermissionManager.MANAGE_PERMISSION,
                self.comment1
            )
        )
        
        # 转移所有权
        result = self.permission_manager.transfer_ownership(
            self.user1,
            self.user2,
            self.comment1
        )
        
        self.assertTrue(result)
        
        # 验证新所有者有权限
        self.assertTrue(
            self.permission_manager.check_user_permission(
                self.user2,
                self.CommentPermissionManager.MANAGE_PERMISSION,
                self.comment1
            )
        )
        
        # 验证原所有者权限已被撤销
        self.assertFalse(
            self.permission_manager.check_user_permission(
                self.user1,
                self.CommentPermissionManager.MANAGE_PERMISSION,
                self.comment1
            )
        )

    def test_cleanup_object_permissions_success(self):
        """测试成功清理对象权限"""
        # 为多个用户分配权限
        self.permission_manager.assign_user_permission(
            self.user1,
            self.CommentPermissionManager.MODERATE_PERMISSION,
            self.comment1
        )
        self.permission_manager.assign_user_permission(
            self.user2,
            self.CommentPermissionManager.REPLY_PERMISSION,
            self.comment1
        )
        
        # 验证权限存在
        self.assertTrue(
            self.permission_manager.check_user_permission(
                self.user1,
                self.CommentPermissionManager.MODERATE_PERMISSION,
                self.comment1
            )
        )
        
        # 清理所有权限
        result = self.permission_manager.cleanup_object_permissions(self.comment1)
        
        self.assertTrue(result)
        
        # 验证权限已被清理（除了管理员）
        self.assertFalse(
            self.permission_manager.check_user_permission(
                self.user1,
                self.CommentPermissionManager.MODERATE_PERMISSION,
                self.comment1
            )
        )
        self.assertFalse(
            self.permission_manager.check_user_permission(
                self.user2,
                self.CommentPermissionManager.REPLY_PERMISSION,
                self.comment1
            )
        )

    def test_assign_author_permissions(self):
        """测试分配作者权限"""
        result = self.comment_permission_manager.assign_author_permissions(
            self.user2,
            self.comment1
        )
        
        self.assertTrue(result)
        
        # 验证作者拥有回复和管理权限
        expected_permissions = [
            self.CommentPermissionManager.REPLY_PERMISSION,
            self.CommentPermissionManager.MANAGE_PERMISSION
        ]
        
        for permission in expected_permissions:
            self.assertTrue(
                self.permission_manager.check_user_permission(
                    self.user2,
                    permission,
                    self.comment1
                )
            )

    def test_assign_moderator_permissions(self):
        """测试分配审核员权限"""
        result = self.comment_permission_manager.assign_moderator_permissions(
            self.user2,
            self.comment1
        )
        
        self.assertTrue(result)
        
        # 验证审核员拥有所有权限
        for permission in self.CommentPermissionManager.ALL_PERMISSIONS:
            self.assertTrue(
                self.permission_manager.check_user_permission(
                    self.user2,
                    permission,
                    self.comment1
                )
            )

    def test_can_moderate_comment(self):
        """测试检查是否可以审核评论"""
        # 未分配权限时不能审核
        self.assertFalse(
            self.comment_permission_manager.can_moderate_comment(
                self.user2,
                self.comment1
            )
        )
        
        # 分配审核权限后可以审核
        self.permission_manager.assign_user_permission(
            self.user2,
            self.CommentPermissionManager.MODERATE_PERMISSION,
            self.comment1
        )
        
        self.assertTrue(
            self.comment_permission_manager.can_moderate_comment(
                self.user2,
                self.comment1
            )
        )

    def test_can_reply_comment(self):
        """测试检查是否可以回复评论"""
        # 未分配权限时不能回复
        self.assertFalse(
            self.comment_permission_manager.can_reply_comment(
                self.user2,
                self.comment1
            )
        )
        
        # 分配回复权限后可以回复
        self.permission_manager.assign_user_permission(
            self.user2,
            self.CommentPermissionManager.REPLY_PERMISSION,
            self.comment1
        )
        
        self.assertTrue(
            self.comment_permission_manager.can_reply_comment(
                self.user2,
                self.comment1
            )
        )

    def test_can_manage_comment(self):
        """测试检查是否可以管理评论"""
        # 未分配权限时不能管理
        self.assertFalse(
            self.comment_permission_manager.can_manage_comment(
                self.user2,
                self.comment1
            )
        )
        
        # 分配管理权限后可以管理
        self.permission_manager.assign_user_permission(
            self.user2,
            self.CommentPermissionManager.MANAGE_PERMISSION,
            self.comment1
        )
        
        self.assertTrue(
            self.comment_permission_manager.can_manage_comment(
                self.user2,
                self.comment1
            )
        )

    def test_get_users_with_permission(self):
        """测试获取拥有特定权限的用户"""
        # 为不同用户分配相同权限
        self.permission_manager.assign_user_permission(
            self.user1,
            self.CommentPermissionManager.MODERATE_PERMISSION,
            self.comment1
        )
        self.permission_manager.assign_user_permission(
            self.user2,
            self.CommentPermissionManager.MODERATE_PERMISSION,
            self.comment1
        )
        
        # 获取拥有审核权限的用户（Guardian需要简化格式权限名）
        users_with_moderate_permission = self.permission_manager.get_users_with_permission(
            'moderate_comment',  # 使用简化格式而不是完整格式
            self.comment1
        )
        
        # 验证返回的用户列表
        user_ids = [user.id for user in users_with_moderate_permission]
        self.assertIn(self.user1.id, user_ids)
        self.assertIn(self.user2.id, user_ids)

    def test_get_user_permissions(self):
        """测试获取用户对对象的所有权限"""
        # 分配多个权限
        permissions = [
            self.CommentPermissionManager.MODERATE_PERMISSION,
            self.CommentPermissionManager.REPLY_PERMISSION
        ]
        
        for permission in permissions:
            self.permission_manager.assign_user_permission(
                self.user1,
                permission,
                self.comment1
            )
        
        # 获取用户权限
        user_permissions = self.permission_manager.get_user_permissions(
            self.user1,
            self.comment1
        )
        
        # 验证权限列表（Guardian返回简化格式，不包含app前缀）
        expected_short_permissions = [
            'moderate_comment',  # 而不是 'comments.moderate_comment'
            'reply_comment'      # 而不是 'comments.reply_comment'
        ]
        for permission in expected_short_permissions:
            self.assertIn(permission, user_permissions)

    def test_comment_permission_edge_cases(self):
        """测试评论权限边界情况"""
        # 测试对不存在的对象分配权限
        fake_comment = Comment(
            id=99999,
            content="不存在的评论",
            user=self.user1,
            article=self.article1
        )
        
        result = self.permission_manager.assign_user_permission(
            self.user1,
            self.CommentPermissionManager.MODERATE_PERMISSION,
            fake_comment
        )
        
        # 应该返回False，因为对象不存在于数据库中
        self.assertFalse(result)

    def test_comment_permission_consistency(self):
        """测试评论权限一致性"""
        # 分配权限
        self.permission_manager.assign_user_permission(
            self.user1,
            self.CommentPermissionManager.MODERATE_PERMISSION,
            self.comment1
        )
        
        # 多次检查权限应该返回一致结果
        for _ in range(5):
            self.assertTrue(
                self.permission_manager.check_user_permission(
                    self.user1,
                    self.CommentPermissionManager.MODERATE_PERMISSION,
                    self.comment1
                )
            )
        
        # 撤销权限
        self.permission_manager.remove_user_permission(
            self.user1,
            self.CommentPermissionManager.MODERATE_PERMISSION,
            self.comment1
        )
        
        # 多次检查应该返回一致的False结果
        for _ in range(5):
            self.assertFalse(
                self.permission_manager.check_user_permission(
                    self.user1,
                    self.CommentPermissionManager.MODERATE_PERMISSION,
                    self.comment1
                )
            )

    def test_comment_specific_scenarios(self):
        """测试评论特定场景"""
        # 测试评论作者默认权限
        original_author = self.comment1.user
        
        # 为原作者分配权限
        self.comment_permission_manager.assign_author_permissions(
            original_author,
            self.comment1
        )
        
        # 验证原作者有管理权限
        self.assertTrue(
            self.comment_permission_manager.can_manage_comment(
                original_author,
                self.comment1
            )
        )
        
        # 验证原作者有回复权限
        self.assertTrue(
            self.comment_permission_manager.can_reply_comment(
                original_author,
                self.comment1
            )
        )
        
        # 验证其他用户没有管理权限
        self.assertFalse(
            self.comment_permission_manager.can_manage_comment(
                self.user2,
                self.comment1
            )
        )

    def test_moderator_vs_author_permissions(self):
        """测试审核员与作者权限差异"""
        # 为用户分配作者权限
        self.comment_permission_manager.assign_author_permissions(
            self.user1,
            self.comment1
        )
        
        # 为另一个用户分配审核员权限
        self.comment_permission_manager.assign_moderator_permissions(
            self.user2,
            self.comment1
        )
        
        # 审核员应该有审核权限，作者没有
        self.assertTrue(
            self.comment_permission_manager.can_moderate_comment(
                self.user2,
                self.comment1
            )
        )
        self.assertFalse(
            self.comment_permission_manager.can_moderate_comment(
                self.user1,
                self.comment1
            )
        )
        
        # 两者都应该有回复权限
        self.assertTrue(
            self.comment_permission_manager.can_reply_comment(
                self.user1,
                self.comment1
            )
        )
        self.assertTrue(
            self.comment_permission_manager.can_reply_comment(
                self.user2,
                self.comment1
            )
        )
        
        # 两者都应该有管理权限
        self.assertTrue(
            self.comment_permission_manager.can_manage_comment(
                self.user1,
                self.comment1
            )
        )
        self.assertTrue(
            self.comment_permission_manager.can_manage_comment(
                self.user2,
                self.comment1
            )
        )

    def test_bulk_operations_performance(self):
        """测试批量操作性能和正确性"""
        # 创建多个评论
        comments = []
        for i in range(10):
            comment = Comment.objects.create(
                article=self.article1,
                user=self.user1,
                content=f"测试评论 {i}"
            )
            comments.append(comment)
        
        # 为每个评论分配权限
        for comment in comments:
            result = self.permission_manager.assign_user_permission(
                self.user2,
                self.CommentPermissionManager.MODERATE_PERMISSION,
                comment
            )
            self.assertTrue(result)
        
        # 验证所有权限都已分配
        for comment in comments:
            self.assertTrue(
                self.permission_manager.check_user_permission(
                    self.user2,
                    self.CommentPermissionManager.MODERATE_PERMISSION,
                    comment
                )
            )
        
        # 清理所有权限
        for comment in comments:
            result = self.permission_manager.cleanup_object_permissions(comment)
            self.assertTrue(result)
        
        # 验证权限已被清理
        for comment in comments:
            self.assertFalse(
                self.permission_manager.check_user_permission(
                    self.user2,
                    self.CommentPermissionManager.MODERATE_PERMISSION,
                    comment
                )
            )


class SensitiveWordFilterTests(TestCase):
    """敏感词过滤器测试类"""
    
    def setUp(self):
        """设置测试数据"""
        self.filter = SensitiveWordFilter()
    
    def test_contains_sensitive_words_true(self):
        """测试检测包含敏感词的文本"""
        test_text = "这里有垃圾内容需要过滤"
        result = self.filter.contains_sensitive_words(test_text)
        self.assertTrue(result)
    
    def test_contains_sensitive_words_false(self):
        """测试检测不包含敏感词的文本"""
        test_text = "这是一条正常的评论内容"
        result = self.filter.contains_sensitive_words(test_text)
        self.assertFalse(result)
    
    def test_find_sensitive_words(self):
        """测试查找敏感词"""
        test_text = "这里有垃圾内容和广告信息"
        words = self.filter.find_sensitive_words(test_text)
        self.assertIn('垃圾内容', words)
        self.assertIn('广告', words)
    
    def test_filter_text(self):
        """测试过滤文本"""
        test_text = "这里有垃圾内容需要过滤"
        filtered = self.filter.filter_text(test_text)
        self.assertIn('***', filtered)
        self.assertNotIn('垃圾内容', filtered)
    
    def test_add_custom_words(self):
        """测试添加自定义敏感词"""
        custom_word = "自定义敏感词"
        self.filter.add_words([custom_word])
        
        test_text = f"这里有{custom_word}需要过滤"
        result = self.filter.contains_sensitive_words(test_text)
        self.assertTrue(result)
    
    def test_empty_text(self):
        """测试空文本"""
        result = self.filter.contains_sensitive_words("")
        self.assertFalse(result)
        
        result = self.filter.filter_text("")
        self.assertEqual(result, "")


class CommentContentFilterTests(TestCase):
    """评论内容过滤器测试类"""
    
    def setUp(self):
        """设置测试数据"""
        self.filter = CommentContentFilter()
    
    def test_normal_content(self):
        """测试正常内容"""
        test_content = "这是一条正常的评论内容"
        result = filter_comment_content(test_content)
        
        self.assertTrue(result['is_valid'])
        self.assertTrue(result['should_auto_approve'])
        self.assertEqual(len(result['issues']), 0)
        self.assertEqual(result['filtered_content'], test_content)
    
    def test_sensitive_content(self):
        """测试包含敏感词的内容"""
        test_content = "这里有垃圾内容需要审核"
        result = filter_comment_content(test_content)
        
        self.assertTrue(result['is_valid'])
        self.assertFalse(result['should_auto_approve'])
        self.assertIn('包含敏感词，需要人工审核', result['issues'])
        self.assertNotEqual(result['filtered_content'], result['original_content'])
    
    def test_empty_content(self):
        """测试空内容"""
        result = filter_comment_content("")
        
        self.assertFalse(result['is_valid'])
        self.assertIn('评论内容不能为空', result['issues'])
    
    def test_whitespace_content(self):
        """测试只包含空白字符的内容"""
        result = filter_comment_content("   \n\t   ")
        
        self.assertFalse(result['is_valid'])
        self.assertIn('评论内容不能为空', result['issues'])
    
    def test_too_long_content(self):
        """测试超长内容"""
        long_content = "a" * 1001  # 假设最大长度为1000
        result = filter_comment_content(long_content)
        
        self.assertFalse(result['is_valid'])
        self.assertTrue(any('不能超过' in issue for issue in result['issues']))
    
    def test_spam_content(self):
        """测试垃圾内容（连续字符）"""
        spam_content = "aaaaa这是垃圾内容"
        result = filter_comment_content(spam_content)
        
        self.assertTrue(result['is_valid'])
        self.assertFalse(result['should_auto_approve'])
        self.assertIn('可能包含垃圾内容，需要人工审核', result['issues'])


class CommentApprovalTests(APITestCase):
    """评论审核测试类"""
    
    def setUp(self):
        """设置测试数据"""
        # 创建用户
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            is_active=True
        )
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
            is_active=True,
            is_staff=True,
            is_superuser=True
        )
        
        # 创建文章
        self.article = Article.objects.create(
            title="测试文章",
            content="测试内容",
            author=self.user
        )
        
        # 生成JWT token
        self.user_token = str(AccessToken.for_user(self.user))
        self.admin_token = str(AccessToken.for_user(self.admin_user))
        
        # API URL
        self.comments_url = reverse(
            "article-comments-list",
            kwargs={"article_pk": self.article.pk}
        )
    
    def test_create_normal_comment_auto_approved(self):
        """测试创建正常评论会自动审核通过"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.user_token}")
        
        data = {"content": "这是一条正常的评论"}
        response = self.client.post(self.comments_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'approved')
        self.assertEqual(response.data['status_display'], '已通过')
        
        # 验证数据库中的状态
        comment = Comment.objects.get(id=response.data['id'])
        self.assertEqual(comment.status, 'approved')
    
    def test_create_sensitive_comment_pending_approval(self):
        """测试创建包含敏感词的评论需要审核"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.user_token}")
        
        data = {"content": "这里有垃圾内容需要审核"}
        response = self.client.post(self.comments_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'pending')
        self.assertEqual(response.data['status_display'], '待审核')
        
        # 验证敏感词被过滤
        self.assertIn('***', response.data['content'])
        
        # 验证数据库中的状态
        comment = Comment.objects.get(id=response.data['id'])
        self.assertEqual(comment.status, 'pending')
    
    def test_comment_visibility_for_different_users(self):
        """测试不同用户的评论可见性"""
        # 创建一个待审核的评论
        pending_comment = Comment.objects.create(
            article=self.article,
            user=self.user,
            content="待审核的评论",
            status='pending'
        )
        
        # 创建一个已通过的评论
        approved_comment = Comment.objects.create(
            article=self.article,
            user=self.user,
            content="已通过的评论",
            status='approved'
        )
        
        # 测试匿名用户只能看到已通过的评论
        response = self.client.get(self.comments_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        comment_ids = [c['id'] for c in response.data['results']]
        self.assertIn(approved_comment.id, comment_ids)
        self.assertNotIn(pending_comment.id, comment_ids)
        
        # 测试评论作者可以看到自己的所有评论
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.user_token}")
        response = self.client.get(self.comments_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        comment_ids = [c['id'] for c in response.data['results']]
        self.assertIn(approved_comment.id, comment_ids)
        self.assertIn(pending_comment.id, comment_ids)
        
        # 测试管理员可以看到所有评论
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
        response = self.client.get(self.comments_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        comment_ids = [c['id'] for c in response.data['results']]
        self.assertIn(approved_comment.id, comment_ids)
        self.assertIn(pending_comment.id, comment_ids)
    
    def test_comment_status_field_in_response(self):
        """测试API响应中包含状态字段"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.user_token}")
        
        data = {"content": "测试评论"}
        response = self.client.post(self.comments_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('status', response.data)
        self.assertIn('status_display', response.data)
        
        # 验证状态字段的值
        self.assertIn(response.data['status'], ['pending', 'approved', 'rejected'])
        self.assertIsInstance(response.data['status_display'], str)
    
    def test_content_validation_error_messages(self):
        """测试内容验证错误消息"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.user_token}")
        
        # 测试空内容
        data = {"content": ""}
        response = self.client.post(self.comments_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('content', response.data)
        
        # 测试超长内容
        data = {"content": "a" * 1001}
        response = self.client.post(self.comments_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('content', response.data)


class CommentModelStatusTests(TestCase):
    """评论模型状态字段测试类"""
    
    def setUp(self):
        """设置测试数据"""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.article = Article.objects.create(
            title="测试文章",
            content="测试内容",
            author=self.user
        )
    
    def test_comment_status_choices(self):
        """测试评论状态选择"""
        choices = Comment.APPROVAL_STATUS_CHOICES
        expected_choices = [
            ('pending', '待审核'),
            ('approved', '已通过'),
            ('rejected', '已拒绝')
        ]
        self.assertEqual(choices, expected_choices)
    
    def test_comment_default_status(self):
        """测试评论默认状态"""
        comment = Comment.objects.create(
            article=self.article,
            user=self.user,
            content="测试评论"
        )
        self.assertEqual(comment.status, 'pending')
    
    def test_comment_status_update(self):
        """测试评论状态更新"""
        comment = Comment.objects.create(
            article=self.article,
            user=self.user,
            content="测试评论",
            status='pending'
        )
        
        # 更新为已通过
        comment.status = 'approved'
        comment.save()
        
        comment.refresh_from_db()
        self.assertEqual(comment.status, 'approved')
    
    def test_get_status_display(self):
        """测试状态显示方法"""
        comment = Comment.objects.create(
            article=self.article,
            user=self.user,
            content="测试评论",
            status='pending'
        )
        
        self.assertEqual(comment.get_status_display(), '待审核')
        
        comment.status = 'approved'
        comment.save()
        self.assertEqual(comment.get_status_display(), '已通过')
        
        comment.status = 'rejected'
        comment.save()
        self.assertEqual(comment.get_status_display(), '已拒绝')
    
    def test_comment_with_all_statuses(self):
        """测试所有状态的评论创建"""
        statuses = ['pending', 'approved', 'rejected']
        
        for status_value in statuses:
            comment = Comment.objects.create(
                article=self.article,
                user=self.user,
                content=f"测试评论 - {status_value}",
                status=status_value
            )
            self.assertEqual(comment.status, status_value)
