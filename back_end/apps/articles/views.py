from rest_framework import viewsets, permissions
from .models import Article
from .serializers import ArticleSerializer, ArticleCreateUpdateSerializer
from .permissions import IsAuthorOrReadOnly
from django.db.models import Q


class ArticleViewSet(viewsets.ModelViewSet):
    """
    文章视图集
    提供 `list`、`create`、`retrieve`、`update` 和 `destroy` 操作
    """

    #########################################
    # queryset的获取后续可以优化性能           #
    #########################################
    queryset = Article.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    def get_queryset(self):
        """根据状态过滤文章"""
        # 局部的queryset
        queryset = Article.objects.all()
        user = self.request.user
        if not user.is_authenticated:
            return self.queryset.filter(status=Article.Status.PUBLISHED)
        # 认证用户可以看到自己的所有文章（包括草稿）和其他人的已发布文章
        return queryset.filter(Q(author=user) | Q(status=Article.Status.PUBLISHED))

    def get_serializer_class(self):
        """根据操作类型选择序列化器"""
        if self.action in ["create", "update", "partial_update"]:
            return ArticleCreateUpdateSerializer
        return ArticleSerializer

    def perform_create(self, serializer):
        """创建文章时自动设置作者为当前用户"""
        serializer.save(author=self.request.user)
