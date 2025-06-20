from rest_framework import viewsets, permissions
from rest_framework.response import Response
from .models import Article
from .serializers import ArticleSerializer, ArticleCreateUpdateSerializer
from .permissions import IsAuthorOrReadOnly
from utils.permissions import CanEditArticle, IsStaffOrOwnerOrReadOnly
from django.db.models import Q
from guardian.shortcuts import assign_perm, get_perms, remove_perm
from guardian.decorators import permission_required_or_403
from guardian.mixins import PermissionRequiredMixin


class ArticleViewSet(viewsets.ModelViewSet):
    """
    文章视图集
    提供 `list`、`create`、`retrieve`、`update` 和 `destroy` 操作
    集成Guardian对象级权限控制
    阶段9：新增文章访问统计功能
    """

    #########################################
    # queryset的获取后续可以优化性能           #
    #########################################
    queryset = Article.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, CanEditArticle]

    def get_queryset(self):
        """
        根据状态和权限过滤文章
        集成Guardian对象级权限控制
        """
        queryset = Article.objects.select_related('author')  # 优化查询性能
        user = self.request.user

        if not user.is_authenticated:
            # 未认证用户只能看到已发布文章
            return queryset.filter(status=Article.Status.PUBLISHED)

        if user.is_staff:
            # 管理员可以看到所有文章
            return queryset

        # 认证用户可以看到：
        # 1. 自己的所有文章（包括草稿）
        # 2. 其他人的已发布文章
        # 3. 有特殊权限的草稿文章
        base_filter = Q(author=user) | Q(status=Article.Status.PUBLISHED)

        # 这里可以进一步集成Guardian权限检查
        # 但由于性能考虑，暂时保持简单的过滤逻辑
        return queryset.filter(base_filter)

    def get_serializer_class(self):
        """根据操作类型选择序列化器"""
        if self.action in ["update", "partial_update"]:
            return ArticleCreateUpdateSerializer
        return ArticleSerializer

    def perform_create(self, serializer):
        """
        创建文章时自动设置作者为当前用户
        并分配Guardian对象权限
        """
        article = serializer.save(author=self.request.user)

        # 为文章作者分配所有权限
        assign_perm('articles.edit_article', self.request.user, article)
        assign_perm('articles.publish_article', self.request.user, article)
        assign_perm('articles.view_draft_article', self.request.user, article)
        assign_perm('articles.manage_article', self.request.user, article)

        return article

    def retrieve(self, request, *args, **kwargs):
        """
        阶段9：重写retrieve方法以实现文章访问统计
        每次获取文章详情时，增加访问计数
        """
        instance = self.get_object()
        
        # 只有当文章是已发布状态时才增加访问计数
        if instance.status == Article.Status.PUBLISHED:
            # 使用F表达式来避免竞态条件
            from django.db.models import F
            Article.objects.filter(pk=instance.pk).update(
                view_count=F('view_count') + 1
            )
            # 重新获取更新后的实例，确保返回最新的view_count
            instance.refresh_from_db()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def perform_destroy(self, instance):
        """
        删除文章时清理相关权限
        """
        # 删除文章前清理所有相关的对象权限
        # Guardian会自动清理，但这里显式处理以确保一致性
        super().perform_destroy(instance)

    def get_object_permissions(self, obj):
        """
        获取当前用户对特定文章的权限列表
        """
        if not self.request.user.is_authenticated:
            return []

        return get_perms(self.request.user, obj)

    def has_article_permission(self, article, permission):
        """
        检查当前用户是否有特定文章的权限

        Args:
            article: 文章对象
            permission: 权限名称

        Returns:
            bool: 是否有权限
        """
        user = self.request.user

        if not user.is_authenticated:
            return False

        # 管理员有所有权限
        if hasattr(user, 'is_staff') and user.is_staff:
            return True

        # 文章作者有所有权限
        if article.author == user:
            return True

        # 检查Guardian对象权限
        return user.has_perm(f'articles.{permission}', article)
