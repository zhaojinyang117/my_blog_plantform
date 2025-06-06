from rest_framework import viewsets, permissions
from rest_framework import serializers
from .models import Comment, Article
from .serializers import CommentSerializer
from .permissions import IsCommentUserOrReadOnly
from django.shortcuts import get_object_or_404

class CommentViewSet(viewsets.ModelViewSet):
    """
     评论视图集
    - list: 获取某篇文章下的所有评论
    - create: 为某篇文章创建新评论
    - retrieve: 获取单个评论详情
    - destroy: 删除单个评论
    """
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsCommentUserOrReadOnly]
    
    def get_queryset(self):
        """返回某篇文章下的所有顶级评论"""
        article_pk = self.kwargs.get('article_pk')
        article = get_object_or_404(Article, pk=article_pk)
        return Comment.objects.filter(article=article, parent__isnull=True).order_by('created_at')

    def perform_create(self, serializer):
        """
        创建评论时，关联当前文章和当前用户
        父评论由客户端在请求数据中提供
        """
        article_pk = self.kwargs.get('article_pk')
        article = get_object_or_404(Article, pk=article_pk)

        # 从 serializer.validated_data 获取 'parent' 字段。
        # 如果 'parent' 是 PrimaryKeyRelatedField (DRF 默认行为)，它会是一个 Comment 实例或 None。
        # 无效的 ID 会在 serializer.is_valid() 阶段被捕获。
        parent_obj_from_serializer = serializer.validated_data.get('parent')

        # 初始化将要保存到数据库的父评论变量
        parent_to_save = None

        if parent_obj_from_serializer:
            if parent_obj_from_serializer.article != article:
                raise serializers.ValidationError({
                    "parent": "父评论不属于当前文章。"
                })
            parent_to_save = parent_obj_from_serializer

        serializer.save(article=article, user=self.request.user, parent=parent_to_save)



