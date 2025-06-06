from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from apps.articles.models import Article  # 假设文章模型在此
from .models import Comment
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()

class CommentAPITests(APITestCase):
    def setUp(self):
        # 创建用户
        self.user1 = User.objects.create_user(username='user1', email='user1@example.com', password='password123')
        self.user2 = User.objects.create_user(username='user2', email='user2@example.com', password='password123')

        # 创建文章
        self.article1 = Article.objects.create(
            title='Test Article 1',
            content='Content for article 1',
            author=self.user1
        )
        self.article2 = Article.objects.create(
            title='Test Article 2',
            content='Content for article 2',
            author=self.user1
        )

        # URL 名称假设 (需要与你的 urls.py 配置一致)
        # 例如: articles_router.register(r'comments', CommentViewSet, basename='article-comments')
        self.list_create_url_article1 = reverse('article-comments-list', kwargs={'article_pk': self.article1.pk})
        self.list_create_url_article2 = reverse('article-comments-list', kwargs={'article_pk': self.article2.pk})
        
        # 顶级评论
        self.comment1_article1 = Comment.objects.create(
            article=self.article1, 
            user=self.user1, 
            content='This is the first comment on article 1.'
        )
        # 回复评论
        self.reply1_to_comment1 = Comment.objects.create(
            article=self.article1,
            user=self.user2,
            content='This is a reply to the first comment.',
            parent=self.comment1_article1
        )

        # Generate JWT tokens for users
        self.access_token_user1 = str(AccessToken.for_user(self.user1))
        self.access_token_user2 = str(AccessToken.for_user(self.user2))

    def test_list_comments_for_article(self):
        """测试获取文章的评论列表，应只包含顶级评论，并嵌套回复"""
        response = self.client.get(self.list_create_url_article1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 检查分页响应结构和顶级评论数量
        self.assertIn('count', response.data)
        self.assertIn('results', response.data)
        self.assertEqual(response.data['count'], 1) # article1 只有一个顶级评论
        self.assertEqual(len(response.data['results']), 1) 
        
        # 检查顶级评论的内容
        top_comment_data = response.data['results'][0]
        self.assertEqual(top_comment_data['id'], self.comment1_article1.id)
        self.assertEqual(top_comment_data['content'], self.comment1_article1.content)
        
        # 检查回复
        self.assertIn('replies', top_comment_data)
        self.assertEqual(len(top_comment_data['replies']), 1)
        reply_data = top_comment_data['replies'][0]
        self.assertEqual(reply_data['id'], self.reply1_to_comment1.id)
        self.assertEqual(reply_data['content'], self.reply1_to_comment1.content)
        self.assertEqual(reply_data['parent'], self.comment1_article1.id)

    def test_list_comments_for_non_existent_article(self):
        """测试获取不存在文章的评论列表应返回404"""
        non_existent_article_pk = 999
        url = reverse('article-comments-list', kwargs={'article_pk': non_existent_article_pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_top_level_comment_authenticated(self):
        """测试认证用户创建顶级评论"""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token_user1)
        data = {'content': 'A new top-level comment'}
        response = self.client.post(self.list_create_url_article1, data)
        self.client.credentials() # Clear credentials
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.filter(article=self.article1, content=data['content'], parent__isnull=True).count(), 1) # Should find 1 comment with this specific new content
        new_comment = Comment.objects.get(article=self.article1, content=data['content'], parent__isnull=True) # Be more specific with get
        self.assertEqual(new_comment.user, self.user1)
        self.assertIsNone(new_comment.parent)

    def test_create_reply_comment_authenticated(self):
        """测试认证用户创建回复评论"""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token_user2)
        data = {'content': 'A reply from user2', 'parent': self.comment1_article1.pk}
        response = self.client.post(self.list_create_url_article1, data)
        self.client.credentials() # Clear credentials
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.filter(article=self.article1, content=data['content'], parent=self.comment1_article1).count(), 1)
        new_reply = Comment.objects.get(article=self.article1, content=data['content'], parent=self.comment1_article1)
        self.assertEqual(new_reply.user, self.user2)
        self.assertEqual(new_reply.parent, self.comment1_article1)

    def test_create_comment_unauthenticated(self):
        """测试未认证用户创建评论应失败"""
        data = {'content': 'Attempt to comment unauthenticated'}
        response = self.client.post(self.list_create_url_article1, data)
        # IsAuthenticatedOrReadOnly: GET is allowed, POST requires authentication
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED) # or 403 if using IsAuthenticated

    def test_create_reply_to_comment_in_different_article_fail(self):
        """测试回复一个不属于当前文章的评论应失败"""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token_user1)
        # comment1_article1 属于 article1, 但我们尝试在 article2 的URL下创建回复
        data = {'content': 'Reply to comment in wrong article', 'parent': self.comment1_article1.pk}
        response = self.client.post(self.list_create_url_article2, data)
        self.client.credentials() # Clear credentials
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('parent', response.data) # 应该有关于 parent 字段的错误信息

    def test_create_comment_with_non_existent_parent_fail(self):
        """测试回复一个不存在的父评论ID应失败"""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token_user1)
        data = {'content': 'Reply to non-existent parent', 'parent': 9999}
        response = self.client.post(self.list_create_url_article1, data)
        self.client.credentials() # Clear credentials
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('parent', response.data)

    def test_delete_own_comment_authenticated(self):
        """测试认证用户删除自己的评论"""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token_user1)
        comment_to_delete = Comment.objects.create(article=self.article1, user=self.user1, content='Comment to be deleted')
        # 假设删除URL为 /api/articles/<article_pk>/comments/<comment_pk>/
        delete_url = reverse('article-comments-detail', kwargs={'article_pk': self.article1.pk, 'pk': comment_to_delete.pk})
        response = self.client.delete(delete_url)
        self.client.credentials() # Clear credentials
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Comment.objects.filter(pk=comment_to_delete.pk).exists())

    def test_delete_others_comment_authenticated_fail(self):
        """测试认证用户删除他人评论应失败"""
        # comment1_article1 由 user1 创建
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token_user2) # user2 尝试删除 user1 的评论
        delete_url = reverse('article-comments-detail', kwargs={'article_pk': self.article1.pk, 'pk': self.comment1_article1.pk})
        response = self.client.delete(delete_url)
        self.client.credentials() # Clear credentials
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Comment.objects.filter(pk=self.comment1_article1.pk).exists())

    def test_delete_comment_unauthenticated_fail(self):
        """测试未认证用户删除评论应失败"""
        delete_url = reverse('article-comments-detail', kwargs={'article_pk': self.article1.pk, 'pk': self.comment1_article1.pk})
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED) # or 403
        self.assertTrue(Comment.objects.filter(pk=self.comment1_article1.pk).exists())

    def test_delete_parent_comment_cascades_to_replies(self):
        """测试删除父评论时，其子评论（回复）也被级联删除"""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token_user1) # user1 是 comment1_article1 的作者
        parent_comment_pk = self.comment1_article1.pk
        reply_pk = self.reply1_to_comment1.pk
        
        self.assertTrue(Comment.objects.filter(pk=parent_comment_pk).exists())
        self.assertTrue(Comment.objects.filter(pk=reply_pk).exists())

        delete_url = reverse('article-comments-detail', kwargs={'article_pk': self.article1.pk, 'pk': parent_comment_pk})
        response = self.client.delete(delete_url)
        self.client.credentials() # Clear credentials
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        self.assertFalse(Comment.objects.filter(pk=parent_comment_pk).exists())
        self.assertFalse(Comment.objects.filter(pk=reply_pk).exists(), "Reply should be cascade deleted")

    def test_retrieve_comment_detail(self):
        """测试获取单个评论的详情"""
        url = reverse('article-comments-detail', kwargs={'article_pk': self.article1.pk, 'pk': self.comment1_article1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.comment1_article1.id)
        self.assertEqual(response.data['content'], self.comment1_article1.content)
        self.assertEqual(len(response.data['replies']), 1)
        self.assertEqual(response.data['replies'][0]['id'], self.reply1_to_comment1.id)
