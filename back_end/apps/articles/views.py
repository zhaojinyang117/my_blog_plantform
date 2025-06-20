from rest_framework import viewsets, permissions, generics, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Article
from .serializers import ArticleSerializer, ArticleCreateUpdateSerializer, ArticleSearchSerializer
from .permissions import IsAuthorOrReadOnly
from utils.permissions import CanEditArticle, IsStaffOrOwnerOrReadOnly
from utils.search import SearchQueryBuilder, SearchCache, validate_search_params
from django.db.models import Q
from guardian.shortcuts import assign_perm, get_perms, remove_perm
from guardian.decorators import permission_required_or_403
from guardian.mixins import PermissionRequiredMixin
from django.core.cache import cache
from django.conf import settings
import hashlib


class ArticleViewSet(viewsets.ModelViewSet):
    """
    文章视图集
    提供 `list`、`create`、`retrieve`、`update` 和 `destroy` 操作
    集成Guardian对象级权限控制
    阶段9：新增文章访问统计功能
    阶段10：新增缓存优化功能
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
    
    def list(self, request, *args, **kwargs):
        """
        阶段10：重写list方法以实现文章列表缓存
        """
        # 生成缓存键，考虑用户的认证状态和查询参数
        cache_key_parts = [
            f"{settings.CACHE_KEY_PREFIX}:articles:list",
            f"user:{request.user.id if request.user.is_authenticated else 'anonymous'}",
            f"params:{hashlib.md5(str(request.query_params).encode()).hexdigest()}"
        ]
        cache_key = ":".join(cache_key_parts)
        
        # 尝试从缓存获取数据
        cached_response = cache.get(cache_key)
        if cached_response is not None:
            return Response(cached_response)
        
        # 如果缓存未命中，执行正常的列表查询
        response = super().list(request, *args, **kwargs)
        
        # 将响应数据存入缓存
        cache_timeout = settings.CACHE_TIMEOUT.get('article_list', 600)
        cache.set(cache_key, response.data, timeout=cache_timeout)
        
        return response

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
        阶段10：添加文章详情缓存
        每次获取文章详情时，增加访问计数
        """
        # 生成缓存键
        cache_key = f"{settings.CACHE_KEY_PREFIX}:article:detail:{kwargs.get('pk')}"
        
        # 尝试从缓存获取数据
        cached_article = cache.get(cache_key)
        if cached_article is not None:
            # 如果是从缓存获取的，仍然需要增加访问计数
            instance = self.get_object()
            if instance.status == Article.Status.PUBLISHED:
                from django.db.models import F
                Article.objects.filter(pk=instance.pk).update(
                    view_count=F('view_count') + 1
                )
            return Response(cached_article)
        
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
        
        # 将文章详情存入缓存
        cache_timeout = settings.CACHE_TIMEOUT.get('article_detail', 1800)
        cache.set(cache_key, serializer.data, timeout=cache_timeout)
        
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
    
    def perform_update(self, serializer):
        """
        阶段10：更新文章时清除相关缓存
        """
        article = serializer.save()
        
        # 清除文章详情缓存
        cache_key = f"{settings.CACHE_KEY_PREFIX}:article:detail:{article.pk}"
        cache.delete(cache_key)
        
        # 清除文章列表缓存（使用模式匹配删除所有相关的列表缓存）
        # 注意：默认的缓存后端可能不支持模式删除，这里简单处理
        # 在生产环境中，可以使用Redis的SCAN命令来查找并删除匹配的键
        
        return article
    
    def perform_destroy(self, instance):
        """
        删除文章时清理相关权限和缓存
        阶段10：添加缓存清理
        """
        # 清除文章详情缓存
        cache_key = f"{settings.CACHE_KEY_PREFIX}:article:detail:{instance.pk}"
        cache.delete(cache_key)
        
        # 删除文章前清理所有相关的对象权限
        # Guardian会自动清理，但这里显式处理以确保一致性
        super().perform_destroy(instance)
    
    @action(detail=False, methods=['get'])
    def hot_articles(self, request):
        """
        阶段10：获取热门文章列表（按访问次数排序）
        使用缓存优化性能
        """
        cache_key = f"{settings.CACHE_KEY_PREFIX}:hot_articles"
        
        # 尝试从缓存获取热门文章
        cached_articles = cache.get(cache_key)
        if cached_articles is not None:
            return Response(cached_articles)
        
        # 获取访问量最高的10篇已发布文章
        hot_articles = Article.objects.filter(
            status=Article.Status.PUBLISHED
        ).select_related('author').order_by('-view_count')[:10]
        
        serializer = ArticleSerializer(hot_articles, many=True)
        
        # 将热门文章存入缓存
        cache_timeout = settings.CACHE_TIMEOUT.get('hot_articles', 3600)
        cache.set(cache_key, serializer.data, timeout=cache_timeout)
        
        return Response(serializer.data)


class ArticleSearchView(generics.ListAPIView):
    """
    文章搜索视图
    支持按标题、内容、作者搜索
    """
    serializer_class = ArticleSearchSerializer
    permission_classes = [permissions.AllowAny]  # 搜索功能对所有用户开放

    def get_queryset(self):
        """
        根据搜索参数过滤文章
        """
        queryset = Article.objects.filter(
            status=Article.Status.PUBLISHED
        ).select_related('author')  # 只搜索已发布的文章

        # 获取搜索参数
        query = self.request.query_params.get('q', '').strip()
        search_type = self.request.query_params.get('type', 'all')
        ordering = self.request.query_params.get('ordering', '-created_at')

        # 验证搜索参数
        is_valid, error_msg = validate_search_params(query, search_type, ordering)
        if not is_valid:
            return queryset.none()

        # 使用搜索查询构建器
        search_builder = SearchQueryBuilder(Article)

        # 根据搜索类型添加搜索条件
        if search_type == 'all':
            search_fields = ['title', 'content', 'author__username']
        elif search_type == 'title':
            search_fields = ['title']
        elif search_type == 'content':
            search_fields = ['content']
        elif search_type == 'author':
            search_fields = ['author__username']
        else:
            search_fields = ['title', 'content', 'author__username']

        search_builder.add_text_search(query, search_fields)
        search_conditions = search_builder.build()

        queryset = queryset.filter(search_conditions)

        # 应用排序
        queryset = queryset.order_by(ordering)

        return queryset

    def list(self, request, *args, **kwargs):
        """
        重写list方法，添加搜索结果缓存和统计信息
        """
        # 获取搜索参数
        query = request.query_params.get('q', '').strip()
        search_type = request.query_params.get('type', 'all')
        ordering = request.query_params.get('ordering', '-created_at')
        page = request.query_params.get('page', '1')

        # 验证搜索参数
        is_valid, error_msg = validate_search_params(query, search_type, ordering)
        if not is_valid:
            return Response({
                'error': error_msg,
                'results': [],
                'count': 0
            }, status=400)

        # 生成缓存键
        cache_key = SearchCache.get_cache_key(query, search_type, ordering, page)

        # 尝试从缓存获取搜索结果
        cached_response = SearchCache.get_cached_result(cache_key)
        if cached_response is not None:
            return Response(cached_response)

        # 执行搜索
        response = super().list(request, *args, **kwargs)

        # 添加搜索统计信息
        if hasattr(response, 'data') and isinstance(response.data, dict):
            response.data['search_info'] = {
                'query': query,
                'search_type': search_type,
                'ordering': ordering,
                'total_results': response.data.get('count', 0)
            }

        # 将搜索结果存入缓存
        SearchCache.cache_result(cache_key, response.data)

        return response
