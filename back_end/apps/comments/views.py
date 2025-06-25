from rest_framework import viewsets, permissions
from rest_framework import serializers
from django.db import models
from .models import Comment, Article
from .serializers import CommentSerializer
from .permissions import IsCommentUserOrReadOnly
# 评论不允许编辑，只允许创建和删除
from django.shortcuts import get_object_or_404
from guardian.shortcuts import assign_perm, get_perms

class CommentViewSet(viewsets.ModelViewSet):
    """
    评论视图集
    - list: 获取某篇文章下的所有评论
    - create: 为某篇文章创建新评论
    - retrieve: 获取单个评论详情
    - destroy: 删除单个评论
    注意：评论不允许编辑，只能删除后重新创建
    """
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsCommentUserOrReadOnly]

    # 禁用编辑相关的HTTP方法
    http_method_names = ['get', 'post', 'delete', 'head', 'options']
    
    def get_queryset(self):
        """
        返回某篇文章下的所有评论
        集成权限检查和审核状态过滤
        """
        article_pk = self.kwargs.get('article_pk')
        article = get_object_or_404(Article, pk=article_pk)

        # 基础查询集
        base_queryset = Comment.objects.filter(article=article).select_related('user', 'parent')
        
        # 审核状态过滤逻辑
        user = self.request.user
        if user.is_authenticated and (user.is_staff or user.is_superuser):
            # 管理员可以看到所有状态的评论
            pass
        elif user.is_authenticated:
            # 登录用户可以看到已通过的评论和自己的评论
            base_queryset = base_queryset.filter(
                models.Q(status='approved') | models.Q(user=user)
            )
        else:
            # 匿名用户只能看到已通过的评论
            base_queryset = base_queryset.filter(status='approved')

        # 对于list操作，只返回顶级评论
        if self.action == 'list':
            queryset = base_queryset.filter(parent__isnull=True)
        else:
            # 对于其他操作（retrieve, update, destroy），返回所有评论
            queryset = base_queryset

        return queryset.order_by('created_at')

    def perform_create(self, serializer):
        """
        创建评论时，关联当前文章和当前用户
        父评论由客户端在请求数据中提供
        并分配Guardian对象权限
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

        comment = serializer.save(article=article, user=self.request.user, parent=parent_to_save)

        # 为评论作者分配权限（评论不允许编辑，只分配回复和管理权限）
        assign_perm('comments.reply_comment', self.request.user, comment)
        assign_perm('comments.manage_comment', self.request.user, comment)

        return comment

    def perform_destroy(self, instance):
        """
        删除评论时清理相关权限
        """
        # 删除评论前清理所有相关的对象权限
        # Guardian会自动清理，但这里显式处理以确保一致性
        super().perform_destroy(instance)

    def get_comment_permissions(self, comment):
        """
        获取当前用户对特定评论的权限列表
        """
        if not self.request.user.is_authenticated:
            return []

        return get_perms(self.request.user, comment)

    def has_comment_permission(self, comment, permission):
        """
        检查当前用户是否有特定评论的权限

        Args:
            comment: 评论对象
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

        # 评论作者有所有权限
        if comment.user == user:
            return True

        # 检查Guardian对象权限
        return user.has_perm(f'comments.{permission}', comment)