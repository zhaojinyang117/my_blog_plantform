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

**阶段五：评论模块 (基础版) (约 1-2 周)**

1. **后端 (articles 或新建 `comments` app):**
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

2. **前端：**
    * **文章详情页：**
        * 调用 API 获取并展示评论列表。
        * 提供评论表单 (如果用户已登录)。
        * 提交评论后刷新评论列表。
        * 用户可以删除自己的评论。

**阶段六：联调、测试与基础部署准备 (约 1 周)**

1. **前后端联调：** 确保所有功能按预期工作。
2. **CORS 配置：** 在 Django 后端配置 `django-cors-headers` 以允许前端访问。
3. **错误处理：** 完善前端和后端的错误提示和处理。
4. **基础样式：** 使用简单的 CSS 或 UI 框架 (如 Bootstrap, Material UI 基础组件) 进行基本美化，确保可用性。
5. **文档：** 编写基础的 API 文档 (如使用 DRF 自带的 Browsable API，或简单的 Postman Collection)。
6. **准备部署：**
    * **后端：** Gunicorn + Nginx (或类似方案)。
    * **前端：** `npm run build` 生成静态文件，可由 Nginx 托管，或使用 Vercel/Netlify 等平台。

---

**总计时间预估：** 约 7 - 11 周 (这是一个相对宽松的估计，具体取决于您的熟练程度和投入时间)。

**关键简化点 (对比 PDF)：**

* **用户管理：** 移除了邮箱验证、头像上传、复杂权限分级、用户激活状态管理。
* **文章管理：** 移除了分类与标签系统 (可后续添加为简单文本字段或完整 M2M)、文章访问权限 (默认公开)、点赞/收藏。
* **评论系统：** 移除了评论审核、敏感词过滤、管理员删除权限。
* **权限管理：** 简化为基于用户角色的基本操作权限 (如文章作者才能编辑/删除)，暂不引入复杂的路由级、对象级权限 (如 Django Guardian)。
* **技术要求：** 暂不强制 Django Filter, Django Guardian, Redis 缓存, 访问日志中间件, 数据库事务 (DRF 会处理一些基本情况)。Swagger 可后续添加。
* **后台管理：** 初期可依赖 Django Admin 进行管理，不开发独立的前端后台。

**开发建议：**

1. **版本控制：** 从一开始就使用 Git 进行版本控制。
2. **先后端后前端：** 通常建议先完成一部分后端 API，再进行对应的前端开发，这样前端有明确的接口可以对接。
3. **小步快跑，持续集成：** 完成一个小功能模块后，就进行测试和集成。
4. **DRF 文档：** Django REST framework 的官方文档是你最好的朋友。
5. **React 文档与社区：** React 也有丰富的学习资源。

这个计划为您勾勒了一个基础版博客平台的轮廓。您可以根据实际开发进度和需求灵活调整。祝您开发顺利！
