from django.urls import path, include
from rest_framework.routers import SimpleRouter
from rest_framework_nested.routers import NestedSimpleRouter
from .views import ArticleViewSet, ArticleSearchView
from apps.comments.views import CommentViewSet

# 主路由，用于文章 CRUD 操作
# 生成的URL: /api/articles/
router = SimpleRouter()
router.register(r"", ArticleViewSet, basename="article")

# 嵌套路由，用于文章下的评论管理
# 生成的URL: /api/articles/{article_pk}/comments/
articles_router = NestedSimpleRouter(
    router,  # 父路由
    r"",  # 父路由前缀（对应ArticleViewSet）
    lookup="article",  # 父资源查找字段，生成 article_pk 参数
)

# 注册评论视图集到嵌套路由
# basename='article-comments' 用于URL反向解析
articles_router.register(r"comments", CommentViewSet, basename="article-comments")

urlpatterns = [
    # 搜索路由: /api/articles/search/
    path("search/", ArticleSearchView.as_view(), name="article-search"),
    # 文章相关路由: /api/articles/
    path("", include(router.urls)),
    # 评论相关路由: /api/articles/{article_pk}/comments/
    path("", include(articles_router.urls)),
]
