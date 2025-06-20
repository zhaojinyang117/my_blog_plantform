# my_blog_plantform

blog平台

好的，很乐意为您规划一个 Django + React 前后端分离的博客平台（基础版）开发计划。

根据您的要求“只打算开发基础的简单功能, 高阶要求暂不考虑”，并参考您提供的 `博客平台开发 (2).pdf` 文件，我会从中提取最核心、最基础的部分来构建这个计划。

**核心目标：** 快速搭建一个可用的、包含核心发布和阅读功能的博客系统。

**技术选型确认：**

* **后端：** Django + Django REST Framework (DRF)
* **前端：** React
* **数据库：** MySQL (根据PDF，您也可以先用 SQLite 快速开始，后续迁移)
* **认证：** JWT (JSON Web Tokens)

---

**开发计划（分阶段进行）：**

**✅阶段一：后端基础搭建与用户认证 (约 1-2 周)**

1. ✅**环境搭建与项目初始化：**
    * 安装 Python, Django, DRF, `djangorestframework-simplejwt`, `mysqlclient` (或对应数据库驱动)。
    * 创建 Django 项目 (`blog_project`) 和核心应用 (`users`, `articles`)。
    * 配置数据库连接 (MySQL)。
    * 配置 `settings.py`：注册应用，配置 DRF，配置 Simple JWT。
    * 遵循 PDF 中的项目结构建议 (`apps/`, `utils/`, `config/`)。

2. ✅**用户模块 (后端 - `users` app):**
    * **模型 (Models)：**
        * 自定义用户模型 (继承 `AbstractUser`)，至少包含：`username`, `email`, `password`。暂时不考虑头像、复杂权限分级。
    * **序列化器 (Serializers)：**
        * 用户注册序列化器 (`UserRegistrationSerializer`)。
        * 用户登录序列化器 (Simple JWT 默认提供，可按需定制)。
        * 用户基本信息序列化器 (`UserSerializer`)。
    * **视图 (Views)：**
        * 用户注册 API (`/api/users/register/`)。
        * 用户登录 API (`/api/token/` - Simple JWT 默认)。
        * 获取当前用户信息 API (`/api/users/me/` - 需要认证)。
    * **路由 (URLs)：** 配置上述 API 的路由。
    * **初步测试：** 使用 Postman 或类似工具测试用户注册、登录、获取用户信息接口。

**✅阶段二：文章模块核心功能 (后端 - `articles` app) (约 1-2 周)**

1. ✅**文章模块 (后端 - `articles` app):**
    * **模型 (Models)：**
        * 文章模型 (`Article`)：`title`, `content` (TextField, 考虑支持 Markdown 文本), `author` (ForeignKey 到 User), `created_at`, `updated_at`, `status` (简单选择：草稿/发布)。
        * 暂时不实现复杂的分类与标签、文章访问权限、点赞收藏。
    * **序列化器 (Serializers)：**
        * 文章列表/详情序列化器 (`ArticleSerializer`)。
        * 文章创建/更新序列化器 (`ArticleCreateUpdateSerializer`)。
    * **视图 (Views)：**
        * 文章列表 API (`GET /api/articles/`) - 显示已发布的文章。
        * 文章详情 API (`GET /api/articles/<id>/`) - 显示单篇已发布的文章。
        * 创建文章 API (`POST /api/articles/`) - 需要认证。
        * 更新文章 API (`PUT /api/articles/<id>/`) - 需要认证，且用户只能修改自己的文章（基础权限）。
        * 删除文章 API (`DELETE /api/articles/<id>/`) - 需要认证，且用户只能删除自己的文章（基础权限）。
    * **权限 (Permissions)：**
        * 使用 DRF 内置的 `IsAuthenticatedOrReadOnly` (列表和详情允许匿名查看，创建/修改/删除需要登录)。
        * 自定义权限：确保用户只能修改/删除自己的文章。
    * **路由 (URLs)：** 配置上述 API 的路由。
    * **初步测试：** 使用 Postman 测试文章的 CRUD 操作。

**✅阶段三：前端基础搭建与页面框架 (约 1 周)**

1. **环境搭建与项目初始化：**
    * 安装 Node.js, npm/yarn。
    * 使用 `create-react-app` (或其他脚手架) 创建 React 项目 (`blog_frontend`)。
    * 安装核心依赖：`axios` (HTTP 请求), `react-router-dom` (路由)。

2. **基本布局与路由：**
    * 设计基本页面布局 (如：导航栏、内容区、页脚)。
    * 配置前端路由：
        * `/` (首页 - 文章列表)
        * `/articles/:id` (文章详情页)
        * `/login` (登录页)
        * `/register` (注册页)
        * `/create-article` (创建文章页 - 需要登录)
        * `/edit-article/:id` (编辑文章页 - 需要登录)

3. **API 服务封装：**
    * 创建 `services/api.js` 或类似文件，封装与后端 API 的交互逻辑 (使用 `axios`)。
    * 处理 JWT token 的存储 (localStorage/sessionStorage) 和请求头携带。

**✅阶段四：前端核心功能实现 (约 2-3 周)**

1. **用户认证页面：**
    * **注册页面：** 表单、调用注册 API、处理响应和错误。
    * **登录页面：** 表单、调用登录 API、成功后存储 token 并跳转、处理响应和错误。
    * **导航栏：** 根据用户登录状态显示不同内容 (如：登录/注册按钮 vs 用户名/退出按钮)。
    * **登出功能：** 清除 token，跳转到首页或登录页。

2. **文章展示页面：**
    * **首页 (文章列表)：**
        * 调用文章列表 API。
        * 展示文章标题、摘要 (后端可提供或前端截取)、作者、发布时间。
        * 点击标题跳转到文章详情页。
    * **文章详情页：**
        * 根据路由参数获取文章 ID，调用文章详情 API。
        * 展示文章完整内容 (需要支持 Markdown 渲染，如使用 `react-markdown`)。
        * 显示作者、发布时间。

3. **文章管理页面 (需要登录)：**
    * **创建文章页面：**
        * 表单 (标题、内容 - Markdown 编辑器如 `react-mde` 或简单的 textarea)。
        * 调用创建文章 API，成功后跳转到文章列表或详情页。
    * **编辑文章页面：**
        * 加载现有文章数据到表单。
        * 调用更新文章 API。
    * **删除文章功能：**
        * 在文章列表或详情页为作者提供删除按钮。
        * 调用删除文章 API。
    * **路由守卫/组件：** 实现 `ProtectedRoute`，未登录用户访问需登录的页面时跳转到登录页。

**✅阶段五：评论模块 (基础版) (约 1-2 周)**

1. ✅**后端 (articles 或新建 `comments` app):**
    * **模型 (Models)：**
        * 评论模型 (`Comment`)：`article` (ForeignKey 到 Article), `author` (ForeignKey 到 User), `content` (TextField), `created_at`.
        * 暂时不实现审核、敏感词过滤。
    * **序列化器 (Serializers)：**
        * 评论序列化器 (`CommentSerializer`)。
    * **视图 (Views)：**
        * 获取某篇文章的评论列表 API (`GET /api/articles/<article_id>/comments/`)。
        * 为某篇文章创建评论 API (`POST /api/articles/<article_id>/comments/`) - 需要认证。
        * 删除评论 API (`DELETE /api/comments/<comment_id>/`) - 用户只能删除自己的评论。
    * **路由 (URLs)：** 配置评论相关 API 路由。

2. ✅**前端：**
    * **文章详情页：**
        * 调用 API 获取并展示评论列表。
        * 提供评论表单 (如果用户已登录)。
        * 提交评论后刷新评论列表。
        * 用户可以删除自己的评论。

**Django + React 博客平台开发计划（进阶基础功能补充）**  
**当前进度：已完成阶段一至阶段五基础功能开发**  

---

### ✅**阶段六：完善用户管理模块 (约3-5天)**  

#### **1. 邮箱验证功能（后端 - `users` app）**  

* ✅**模型增强**  
  * 添加 `is_active` 字段（默认False），标记账户激活状态[1]  
  * 添加 `email_verification_token` 字段存储验证令牌  

  ```python
  # users/models.py
  class CustomUser(AbstractUser):
      is_active = models.BooleanField(default=False)
      email_verification_token = models.CharField(max_length=64, blank=True)
  ```

* ✅**邮件服务**  
  * 配置 Django 邮件设置（SMTP 参数）  
  * 实现邮件发送工具类（使用 `django.core.mail`）  

  ```python
  # utils/email.py
  from django.core.mail import send_mail
  
  def send_verification_email(user):
      token = generate_token()  # 使用secrets模块生成安全令牌
      verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
      send_mail(
          '邮箱验证',
          f'请点击链接完成验证: {verification_url}',
          settings.DEFAULT_FROM_EMAIL,
          [user.email]
      )
      user.email_verification_token = token
      user.save()
  ```

* ✅**API 增强**  
  * 修改注册接口：注册后发送验证邮件（异步任务可用 `threading` 简单实现）  
  * 新增验证接口：`GET /api/users/verify-email/?token=`  

  ```python
  # users/views.py
  class EmailVerificationView(APIView):
      def get(self, request):
          token = request.GET.get('token')
          user = CustomUser.objects.filter(email_verification_token=token).first()
          if user:
              user.is_active = True
              user.email_verification_token = ''
              user.save()
              return Response({'status': 'success'})
          return Response({'error': '无效令牌'}, status=400)
  ```

* ✅**前端适配**  
  * 注册页面：成功注册后提示检查邮箱  
  * 新增验证页面：`/verify-email` 处理验证逻辑  

#### **2. 用户头像上传（前后端）**  

* ✅**后端实现**  
  * 安装 `Pillow` 处理图片  
  * 修改用户模型添加 `avatar` 字段  

  ```python
  # users/models.py
  class CustomUser(AbstractUser):
      avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
  ```

  * 创建 `UserProfileSerializer` 处理头像上传  

  ```python
  # users/serializers.py
  class UserProfileSerializer(serializers.ModelSerializer):
      class Meta:
          model = CustomUser
          fields = ['username', 'email', 'avatar']
  ```

  * 新增头像上传接口：`PATCH /api/users/me/avatar/`  
* ✅**前端实现**  
  * 用户中心页面添加头像上传组件（使用 ``）  
  * 使用 `FormData` 处理文件上传  

  ```javascript
  // 前端示例代码
  const handleUpload = async (file) => {
    const formData = new FormData();
    formData.append('avatar', file);
    await api.patch('/users/me/avatar/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  };
  ```

#### **3. 用户状态管理（后台）**  

* ✅**Django Admin 增强**  
  * 在管理员界面添加用户状态过滤  
  * 增加批量操作：激活/禁用用户  

  ```python
  # users/admin.py
  @admin.register(CustomUser)
  class CustomUserAdmin(UserAdmin):
      list_filter = ('is_active',)
      actions = ['activate_users', 'deactivate_users']
  
      def activate_users(self, request, queryset):
          queryset.update(is_active=True)
      activate_users.short_description = "激活选定用户"
  ```

---

### ✅**阶段七：增强权限管理系统 (约5-7天)**  

#### ✅**1. 路由级权限控制**  

- **后端中间件**  
  * 创建 `AdminOnlyMiddleware` 限制管理后台路由  

  ```python
  # utils/middleware.py
  class AdminOnlyMiddleware:
      def __init__(self, get_response):
          self.get_response = get_response
  
      def __call__(self, request):
          if request.path.startswith('/admin/') and not request.user.is_staff:
              return HttpResponseForbidden()
          return self.get_response(request)
  ```

- **DRF 权限类**  
  * 创建 `IsAdminOrReadOnly` 权限类  

  ```python
  # utils/permissions.py
  class IsAdminOrReadOnly(permissions.BasePermission):
      def has_permission(self, request, view):
          return (
              request.method in permissions.SAFE_METHODS or
              request.user and 
              request.user.is_staff
          )
  ```

#### ✅**2. 对象级权限控制**  

- **集成 Django Guardian**  
  * 安装 `django-guardian`  
  * 配置文章模型权限  

  ```python
  # articles/models.py
  from guardian.models import UserObjectPermissionAbstract
  
  class Article(models.Model):
      ...
      class Meta:
          permissions = [
              ('edit_article', "Can edit article"),
          ]
  
  class ArticleUserObjectPermission(UserObjectPermissionAbstract):
      content_object = models.ForeignKey(Article, on_delete=models.CASCADE)
  ```

- **视图权限控制**  

  ```python
  # articles/views.py
  from guardian.shortcuts import assign_perm
  
  class ArticleCreateView(APIView):
      def post(self, request):
          serializer = ArticleSerializer(data=request.data)
          if serializer.is_valid():
              article = serializer.save(author=request.user)
              assign_perm('articles.edit_article', request.user, article)
              return Response(serializer.data)
  ```

---

### ✅**阶段八：评论系统进阶功能 (约5-7天)**  

#### ✅**1. 评论审核机制**  

- **模型增强**  

  ```python
  # comments/models.py
  class Comment(models.Model):
      APPROVAL_STATUS = [
          ('pending', '待审核'),
          ('approved', '已通过'),
          ('rejected', '已拒绝')
      ]
      status = models.CharField(max_length=10, choices=APPROVAL_STATUS, default='pending')
  ```

- **管理界面**  
  * 在 Django Admin 添加状态过滤器和批量审核操作  
  * 默认通过, 如果有敏感词需要审核
* **API 修改**  

  ```python
  # comments/views.py
  class CommentCreateView(APIView):
      permission_classes = [IsAuthenticated]
      
      def post(self, request, article_id):
          serializer = CommentSerializer(data=request.data)
          if serializer.is_valid():
              serializer.save(article_id=article_id, author=request.user, status='pending')
              return Response(serializer.data)
  ```

#### ✅**2. 敏感词过滤**  

- **实现基础过滤**  

  ```python
  # utils/text_filter.py
  sensitive_words = ['违规词1', '违规词2']  # 扩展为数据库存储
  
  def filter_content(text):
      for word in sensitive_words:
          text = text.replace(word, '***')
      return text
  ```

- **集成到序列化器**  

  ```python
  # comments/serializers.py
  class CommentSerializer(serializers.ModelSerializer):
      def validate_content(self, value):
          return filter_content(value)
  ```

---

### ✅**阶段九：数据统计基础实现 (约3-5天)**  

#### ✅**1. 用户活跃度统计**  

- **模型添加字段**  

  ```python
  # users/models.py
  class CustomUser(AbstractUser):
      last_login_ip = models.GenericIPAddressField(null=True)
      login_count = models.IntegerField(default=0)
  ```

- **中间件记录**  

  ```python
  # utils/middleware.py
  class UserActivityMiddleware:
      def __init__(self, get_response):
          self.get_response = get_response
  
      def __call__(self, request):
          if request.user.is_authenticated:
              request.user.login_count += 1
              request.user.last_login_ip = request.META.get('REMOTE_ADDR')
              request.user.save()
          return self.get_response(request)
  ```

#### ✅**2. 文章访问统计**  

- **模型增强**  

  ```python
  # articles/models.py
  class Article(models.Model):
      view_count = models.PositiveIntegerField(default=0)
  ```

- **视图计数器**  

  ```python
  # articles/views.py
  class ArticleDetailView(RetrieveAPIView):
      def retrieve(self, request, *args, **kwargs):
          instance = self.get_object()
          instance.view_count += 1
          instance.save(update_fields=['view_count'])
          return super().retrieve(request, *args, **kwargs)
  ```

---

### ✅**阶段十：缓存优化 (约2-3天)**  

#### ✅**1. Redis 配置**  

- 安装 `django-redis`  
* 配置缓存后端  

  ```python
  # settings.py
  CACHES = {
      "default": {
          "BACKEND": "django_redis.cache.RedisCache",
          "LOCATION": "redis://127.0.0.1:6379/1",
      }
  }
  ```

#### ✅**2. 热门文章缓存**  

```python
# articles/views.py
from django.core.cache import cache

class ArticleListView(ListAPIView):
    def get_queryset(self):
        cache_key = 'hot_articles'
        queryset = cache.get(cache_key)
        if not queryset:
            queryset = Article.objects.filter(status='published').order_by('-view_count')[:10]
            cache.set(cache_key, queryset, timeout=3600)  # 缓存1小时
        return queryset
```

---

### **阶段十一：测试与优化 (约5-7天)**  

#### ✅**1. 单元测试**  

- 使用 Django 测试框架  
* 覆盖核心功能：  

  ```python
  # articles/tests.py
  class ArticleTests(APITestCase):
      def test_create_article(self):
          self.client.force_authenticate(user=self.user)
          response = self.client.post('/api/articles/', {'title': 'Test', 'content': '...'})
          self.assertEqual(response.status_code, 201)
  ```

#### **2. 性能优化**  

- 使用 `select_related` 优化查询  

  ```python
  # articles/views.py
  queryset = Article.objects.select_related('author')
  ```

- 添加数据库索引  

  ```python
  class Article(models.Model):
      class Meta:
          indexes = [
              models.Index(fields=['-created_at']),
          ]
  ```

---

### **阶段十二：部署与文档 (约3-5天)**  

#### **1. Docker 部署**  

```dockerfile
# Dockerfile 示例
FROM python:3.9
RUN pip install gunicorn
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

#### **2. 文档生成**  

- 使用 `drf-spectacular` 生成 OpenAPI 文档  

  ```python
  # settings.py
  INSTALLED_APPS += ['drf_spectacular']
  
  REST_FRAMEWORK = {
      'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
  }
  ```

- 编写部署手册：  

  ```
  ## 部署步骤
  1. 安装 Docker 和 docker-compose
  2. 构建镜像: docker-compose build
  3. 启动服务: docker-compose up -d
  ```

---

**总新增开发时间预估：** 约 25-35 天  
**关键实现要点：**  

1. 权限系统采用组合策略：DRF权限类 + Django Guardian对象权限  
2. 敏感词过滤采用内存缓存 + 定期更新机制  
3. 统计功能使用中间件 + 模型字段组合实现  
4. 缓存策略遵循"先读缓存-后更新"模式[1]  
