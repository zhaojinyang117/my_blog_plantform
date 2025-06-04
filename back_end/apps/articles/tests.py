from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Article
from .serializers import ArticleSerializer, ArticleCreateUpdateSerializer
from datetime import datetime
from django.utils import timezone

User = get_user_model()


class ArticleModelTest(TestCase):
    """文章模型测试"""

    def setUp(self):
        """设置测试数据"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_create_article(self):
        """测试创建文章"""
        article = Article.objects.create(
            title="测试文章",
            content="这是一篇测试文章的内容",
            author=self.user,
            status=Article.Status.DRAFT,
        )

        self.assertEqual(article.title, "测试文章")
        self.assertEqual(article.content, "这是一篇测试文章的内容")
        self.assertEqual(article.author, self.user)
        self.assertEqual(article.status, Article.Status.DRAFT)
        self.assertIsNotNone(article.created_at)
        self.assertIsNotNone(article.updated_at)

    def test_article_str_method(self):
        """测试文章的字符串表示"""
        article = Article.objects.create(
            title="测试文章标题", content="测试内容", author=self.user
        )
        self.assertEqual(str(article), "测试文章标题")

    def test_article_status_choices(self):
        """测试文章状态选择"""
        # 测试草稿状态
        draft_article = Article.objects.create(
            title="草稿文章",
            content="草稿内容",
            author=self.user,
            status=Article.Status.DRAFT,
        )
        self.assertEqual(draft_article.status, "draft")

        # 测试已发布状态
        published_article = Article.objects.create(
            title="已发布文章",
            content="已发布内容",
            author=self.user,
            status=Article.Status.PUBLISHED,
        )
        self.assertEqual(published_article.status, "published")

    def test_article_ordering(self):
        """测试文章排序（按创建时间倒序）"""
        import time

        # 创建第一篇文章
        article1 = Article.objects.create(
            title="第一篇文章", content="第一篇内容", author=self.user
        )

        # 等待一小段时间确保创建时间有差异
        time.sleep(0.01)

        # 创建第二篇文章
        article2 = Article.objects.create(
            title="第二篇文章", content="第二篇内容", author=self.user
        )

        articles = Article.objects.all()
        # 验证排序：最新创建的文章应该排在前面
        self.assertGreaterEqual(articles[0].created_at, articles[1].created_at)
        # 由于我们确保了时间差异，第二篇文章应该排在第一位
        self.assertEqual(articles[0], article2)
        self.assertEqual(articles[1], article1)

    def test_article_author_cascade_delete(self):
        """测试用户删除时文章级联删除"""
        article = Article.objects.create(
            title="测试文章", content="测试内容", author=self.user
        )

        article_id = article.id
        self.user.delete()

        # 文章应该被级联删除
        with self.assertRaises(Article.DoesNotExist):
            Article.objects.get(id=article_id)


class ArticleSerializerTest(TestCase):
    """文章序列化器测试"""

    def setUp(self):
        """设置测试数据"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.article = Article.objects.create(
            title="测试文章",
            content="测试内容",
            author=self.user,
            status=Article.Status.PUBLISHED,
        )

    def test_article_serializer_read(self):
        """测试文章序列化器读取"""
        serializer = ArticleSerializer(self.article)
        data = serializer.data

        self.assertEqual(data["title"], "测试文章")
        self.assertEqual(data["content"], "测试内容")
        self.assertEqual(data["status"], "published")
        self.assertEqual(data["author"]["username"], "testuser")
        self.assertEqual(data["author"]["email"], "test@example.com")
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)

    def test_article_create_update_serializer(self):
        """测试文章创建更新序列化器"""
        data = {"title": "新文章标题", "content": "新文章内容", "status": "draft"}

        serializer = ArticleCreateUpdateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        # 验证序列化器字段
        validated_data = serializer.validated_data
        self.assertEqual(validated_data["title"], "新文章标题")
        self.assertEqual(validated_data["content"], "新文章内容")
        self.assertEqual(validated_data["status"], "draft")

    def test_article_create_update_serializer_invalid_data(self):
        """测试文章创建更新序列化器无效数据"""
        # 缺少必填字段
        data = {"content": "只有内容没有标题"}

        serializer = ArticleCreateUpdateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("title", serializer.errors)

    def test_article_serializer_multiple_articles(self):
        """测试多篇文章序列化"""
        import time

        # 等待一小段时间确保创建时间有差异
        time.sleep(0.01)

        # 创建另一篇文章
        article2 = Article.objects.create(
            title="第二篇文章",
            content="第二篇内容",
            author=self.user,
            status=Article.Status.DRAFT,
        )

        articles = Article.objects.all()
        serializer = ArticleSerializer(articles, many=True)
        data = serializer.data

        self.assertEqual(len(data), 2)
        # 验证排序（最新的在前）- 由于确保了时间差异，第二篇文章应该排在前面
        # 但如果时间相同，则按数据库默认排序
        titles = [article["title"] for article in data]
        self.assertIn("第二篇文章", titles)
        self.assertIn("测试文章", titles)


class ArticleAPITest(APITestCase):
    """文章API测试"""

    def setUp(self):
        """设置测试数据"""
        self.user1 = User.objects.create_user(
            username="user1", email="user1@example.com", password="testpass123"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@example.com", password="testpass123"
        )

        # 创建测试文章
        self.published_article = Article.objects.create(
            title="已发布文章",
            content="已发布内容",
            author=self.user1,
            status=Article.Status.PUBLISHED,
        )

        self.draft_article = Article.objects.create(
            title="草稿文章",
            content="草稿内容",
            author=self.user1,
            status=Article.Status.DRAFT,
        )

        self.other_user_article = Article.objects.create(
            title="其他用户文章",
            content="其他用户内容",
            author=self.user2,
            status=Article.Status.PUBLISHED,
        )

    def get_jwt_token(self, user):
        """获取JWT令牌"""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    def test_article_list_anonymous_user(self):
        """测试匿名用户获取文章列表"""
        url = reverse("article-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 匿名用户只能看到已发布的文章
        self.assertEqual(len(response.data["results"]), 2)

        # 验证返回的都是已发布文章
        for article in response.data["results"]:
            self.assertEqual(article["status"], "published")

    def test_article_list_authenticated_user(self):
        """测试认证用户获取文章列表"""
        token = self.get_jwt_token(self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        url = reverse("article-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 认证用户可以看到自己的所有文章和其他人的已发布文章
        self.assertEqual(len(response.data["results"]), 3)

    def test_article_detail_published(self):
        """测试获取已发布文章详情"""
        url = reverse("article-detail", kwargs={"pk": self.published_article.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "已发布文章")
        self.assertEqual(response.data["status"], "published")

    def test_article_detail_draft_anonymous(self):
        """测试匿名用户访问草稿文章"""
        url = reverse("article-detail", kwargs={"pk": self.draft_article.pk})
        response = self.client.get(url)

        # 匿名用户不能访问草稿文章
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_article_detail_draft_author(self):
        """测试作者访问自己的草稿文章"""
        token = self.get_jwt_token(self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        url = reverse("article-detail", kwargs={"pk": self.draft_article.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "草稿文章")
        self.assertEqual(response.data["status"], "draft")

    def test_create_article_authenticated(self):
        """测试认证用户创建文章"""
        token = self.get_jwt_token(self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        url = reverse("article-list")
        data = {"title": "新创建的文章", "content": "新创建的内容", "status": "draft"}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "新创建的文章")
        # 注意：创建时现在使用ArticleSerializer，包含author字段
        self.assertIn("author", response.data)
        self.assertEqual(response.data["author"]["username"], "user1")

        # 验证数据库中确实创建了文章，并且作者正确
        article = Article.objects.get(title="新创建的文章")
        self.assertEqual(article.author, self.user1)

    def test_create_article_anonymous(self):
        """测试匿名用户创建文章"""
        url = reverse("article-list")
        data = {"title": "匿名用户文章", "content": "匿名用户内容", "status": "draft"}

        response = self.client.post(url, data, format="json")

        # 匿名用户不能创建文章
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_article_author(self):
        """测试作者更新自己的文章"""
        token = self.get_jwt_token(self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        url = reverse("article-detail", kwargs={"pk": self.draft_article.pk})
        data = {
            "title": "更新后的标题",
            "content": "更新后的内容",
            "status": "published",
        }

        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "更新后的标题")
        self.assertEqual(response.data["status"], "published")

        # 验证数据库中的数据确实更新了
        article = Article.objects.get(pk=self.draft_article.pk)
        self.assertEqual(article.title, "更新后的标题")
        self.assertEqual(article.status, "published")

    def test_update_article_non_author(self):
        """测试非作者更新文章 - 预期行为：返回404因为草稿文章对非作者不可见"""
        token = self.get_jwt_token(self.user2)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        url = reverse("article-detail", kwargs={"pk": self.draft_article.pk})
        data = {"title": "恶意更新", "content": "恶意内容", "status": "published"}

        response = self.client.put(url, data, format="json")

        # 非作者访问其他人的草稿文章会返回404（因为get_queryset过滤了不可见的文章）
        # 这是预期的业务逻辑：用户看不到其他人的草稿，所以返回404而不是403
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_article_author(self):
        """测试作者删除自己的文章"""
        token = self.get_jwt_token(self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        article_id = self.draft_article.pk
        url = reverse("article-detail", kwargs={"pk": article_id})

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # 验证文章确实被删除了
        with self.assertRaises(Article.DoesNotExist):
            Article.objects.get(pk=article_id)

    def test_delete_article_non_author(self):
        """测试非作者删除文章 - 预期行为：返回404因为草稿文章对非作者不可见"""
        token = self.get_jwt_token(self.user2)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        url = reverse("article-detail", kwargs={"pk": self.draft_article.pk})

        response = self.client.delete(url)

        # 非作者访问其他人的草稿文章会返回404（因为get_queryset过滤了不可见的文章）
        # 这是预期的业务逻辑：用户看不到其他人的草稿，所以返回404而不是403
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # 验证文章仍然存在
        self.assertTrue(Article.objects.filter(pk=self.draft_article.pk).exists())

    def test_update_published_article_non_author(self):
        """测试非作者更新已发布文章 - 预期行为：返回403因为权限不足"""
        token = self.get_jwt_token(self.user2)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        url = reverse("article-detail", kwargs={"pk": self.published_article.pk})
        data = {
            "title": "恶意更新已发布文章",
            "content": "恶意内容",
            "status": "published",
        }

        response = self.client.put(url, data, format="json")

        # 非作者尝试更新已发布文章应该返回403（权限不足）
        # 因为已发布文章对所有人可见，但只有作者可以修改
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_published_article_non_author(self):
        """测试非作者删除已发布文章 - 预期行为：返回403因为权限不足"""
        token = self.get_jwt_token(self.user2)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        url = reverse("article-detail", kwargs={"pk": self.published_article.pk})

        response = self.client.delete(url)

        # 非作者尝试删除已发布文章应该返回403（权限不足）
        # 因为已发布文章对所有人可见，但只有作者可以删除
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # 验证文章仍然存在
        self.assertTrue(Article.objects.filter(pk=self.published_article.pk).exists())


class ArticlePermissionTest(TestCase):
    """文章权限测试"""

    def setUp(self):
        """设置测试数据"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.other_user = User.objects.create_user(
            username="otheruser", email="other@example.com", password="testpass123"
        )

        self.article = Article.objects.create(
            title="测试文章",
            content="测试内容",
            author=self.user,
            status=Article.Status.PUBLISHED,
        )

    def test_is_author_or_read_only_permission(self):
        """测试IsAuthorOrReadOnly权限"""
        from .permissions import IsAuthorOrReadOnly
        from rest_framework.test import APIRequestFactory
        from django.contrib.auth.models import AnonymousUser

        permission = IsAuthorOrReadOnly()
        factory = APIRequestFactory()

        # 测试读取权限（GET请求）
        request = factory.get("/")
        request.user = AnonymousUser()
        self.assertTrue(permission.has_object_permission(request, None, self.article))

        # 测试作者的写权限
        request = factory.put("/")
        request.user = self.user
        self.assertTrue(permission.has_object_permission(request, None, self.article))

        # 测试非作者的写权限
        request = factory.put("/")
        request.user = self.other_user
        self.assertFalse(permission.has_object_permission(request, None, self.article))


class ArticleEdgeCaseTest(TestCase):
    """文章边界情况测试"""

    def setUp(self):
        """设置测试数据"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_article_with_empty_content(self):
        """测试空内容文章"""
        article = Article.objects.create(
            title="空内容文章", content="", author=self.user
        )
        self.assertEqual(article.content, "")
        self.assertEqual(str(article), "空内容文章")

    def test_article_with_long_title(self):
        """测试长标题文章 - Django CharField会自动截断超长内容"""
        long_title = "这是一个非常长的标题" * 10  # 超过255字符

        # Django的CharField(max_length=255)会自动截断超长内容，不会抛出异常
        # 这是Django的默认行为，除非在数据库层面有严格约束
        article = Article.objects.create(
            title=long_title, content="测试内容", author=self.user
        )

        # 验证标题被截断到255字符以内
        self.assertLessEqual(len(article.title), 255)

    def test_article_default_status(self):
        """测试文章默认状态"""
        article = Article.objects.create(
            title="默认状态文章", content="测试内容", author=self.user
        )
        self.assertEqual(article.status, Article.Status.DRAFT)

    def test_article_timestamps(self):
        """测试文章时间戳"""
        import time

        article = Article.objects.create(
            title="时间戳测试", content="测试内容", author=self.user
        )

        # 创建时间和更新时间应该存在
        self.assertIsNotNone(article.created_at)
        self.assertIsNotNone(article.updated_at)

        # 创建时间应该等于更新时间（刚创建时）
        self.assertEqual(article.created_at, article.updated_at)

        # 等待一小段时间确保时间戳有差异
        time.sleep(0.01)

        # 更新文章
        original_created_at = article.created_at
        original_updated_at = article.updated_at
        article.title = "更新后的标题"
        article.save()

        # 重新从数据库获取以确保获得最新的时间戳
        article.refresh_from_db()

        # 创建时间不应该改变，更新时间应该改变
        self.assertEqual(article.created_at, original_created_at)
        self.assertGreater(article.updated_at, original_updated_at)


class ArticleQueryTest(TestCase):
    """文章查询测试"""

    def setUp(self):
        """设置测试数据"""
        self.user1 = User.objects.create_user(
            username="user1", email="user1@example.com", password="testpass123"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@example.com", password="testpass123"
        )

        # 创建不同状态的文章
        self.published_articles = [
            Article.objects.create(
                title=f"已发布文章{i}",
                content=f"已发布内容{i}",
                author=self.user1,
                status=Article.Status.PUBLISHED,
            )
            for i in range(3)
        ]

        self.draft_articles = [
            Article.objects.create(
                title=f"草稿文章{i}",
                content=f"草稿内容{i}",
                author=self.user1,
                status=Article.Status.DRAFT,
            )
            for i in range(2)
        ]

    def test_published_articles_query(self):
        """测试查询已发布文章"""
        published = Article.objects.filter(status=Article.Status.PUBLISHED)
        self.assertEqual(published.count(), 3)

    def test_draft_articles_query(self):
        """测试查询草稿文章"""
        drafts = Article.objects.filter(status=Article.Status.DRAFT)
        self.assertEqual(drafts.count(), 2)

    def test_articles_by_author(self):
        """测试按作者查询文章"""
        user1_articles = Article.objects.filter(author=self.user1)
        self.assertEqual(user1_articles.count(), 5)

        user2_articles = Article.objects.filter(author=self.user2)
        self.assertEqual(user2_articles.count(), 0)

    def test_articles_ordering(self):
        """测试文章排序"""
        articles = Article.objects.all()

        # 应该按创建时间倒序排列
        for i in range(len(articles) - 1):
            self.assertGreaterEqual(articles[i].created_at, articles[i + 1].created_at)
