from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from apps.articles.models import Article  # 假设文章模型在此
from .models import Comment
from rest_framework_simplejwt.tokens import AccessToken
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
            username="user1", email="user1@example.com", password="password123"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@example.com", password="password123"
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
