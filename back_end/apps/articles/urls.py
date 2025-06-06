from django.urls import path, include
from rest_framework_nested import routers # 导入 rest_framework_nested
from .views import ArticleViewSet
from apps.comments.views import CommentViewSet # 导入 CommentViewSet

# 主路由，用于文章
router = routers.SimpleRouter()
router.register(r'', ArticleViewSet, basename='article') # 明确指定 basename='article'

# 嵌套路由，用于文章下的评论
# 第一个参数是父路由 (router)
# 第二个参数是父路由中用于查找的前缀 (r'')，这里对应 ArticleViewSet
# 第三个参数是父资源的主键查找字段 (lookup='article')，这会生成如 /articles/<article_pk>/... 的URL
articles_router = routers.NestedSimpleRouter(router, r'', lookup='article')

# 在嵌套路由下注册 CommentViewSet
# basename='article-comments' 与测试用例中的 reverse 调用匹配
articles_router.register(r'comments', CommentViewSet, basename='article-comments')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(articles_router.urls)), # 包含嵌套路由的 URL
]