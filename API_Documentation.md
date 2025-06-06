# 博客平台后端 API 文档

## 概述

这是一个基于 Django REST Framework 的博客平台后端 API 文档。该平台支持用户注册、登录、文章管理和评论功能。

**基础URL**: `http://localhost:8000/api`

## 认证方式

使用 JWT (JSON Web Token) 进行身份认证。

### 认证头格式

```
Authorization: Bearer <access_token>
```

---

## 1. 用户管理 API

### 1.1 用户注册

- **URL**: `POST /api/users/register/`
- **权限**: 无需认证
- **描述**: 注册新用户

**请求体**:

```json
{
    "username": "string",
    "email": "string",
    "password": "string",
    "password2": "string"
}
```

**响应示例**:

```json
{
    "id": 1,
    "username": "testuser",
    "email": "test@example.com"
}
```

### 1.2 用户登录

- **URL**: `POST /api/users/token/`
- **权限**: 无需认证
- **描述**: 获取访问令牌

**请求体**:

```json
{
    "email": "string",
    "password": "string"
}
```

**响应示例**:

```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### 1.3 刷新令牌

- **URL**: `POST /api/users/token/refresh/`
- **权限**: 无需认证
- **描述**: 使用刷新令牌获取新的访问令牌

**请求体**:

```json
{
    "refresh": "string"
}
```

### 1.4 获取当前用户信息

- **URL**: `GET /api/users/me/`
- **权限**: 需要认证
- **描述**: 获取当前登录用户的详细信息

**响应示例**:

```json
{
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "bio": "个人简介",
    "avatar": "avatar/2024/01/image.jpg"
}
```

### 1.5 更新当前用户信息

- **URL**: `PUT/PATCH /api/users/me/update/`
- **权限**: 需要认证
- **描述**: 更新当前用户信息

**请求体**:

```json
{
    "username": "newusername",
    "bio": "新的个人简介",
    "avatar": "文件上传"
}
```

---

## 2. 文章管理 API

### 2.1 获取文章列表

- **URL**: `GET /api/articles/`
- **权限**: 无需认证（只能看到已发布文章）/ 认证用户（可看到自己的所有文章+他人已发布文章）
- **描述**: 获取文章列表，支持分页

**查询参数**:

- `page`: 页码
- `page_size`: 每页数量

**响应示例**:

```json
{
    "count": 10,
    "next": "http://localhost:8000/api/articles/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "title": "文章标题",
            "content": "文章内容",
            "author": {
                "id": 1,
                "username": "author",
                "email": "author@example.com"
            },
            "created_at": "2024-01-01T12:00:00Z",
            "updated_at": "2024-01-01T12:00:00Z",
            "status": "published"
        }
    ]
}
```

### 2.2 获取文章详情

- **URL**: `GET /api/articles/{id}/`
- **权限**: 无需认证（仅已发布文章）/ 认证用户（自己的文章或他人已发布文章）
- **描述**: 获取指定文章的详细信息

### 2.3 创建文章

- **URL**: `POST /api/articles/`
- **权限**: 需要认证
- **描述**: 创建新文章

**请求体**:

```json
{
    "title": "文章标题",
    "content": "文章内容",
    "status": "draft"  // 可选: "draft" 或 "published"
}
```

### 2.4 更新文章

- **URL**: `PUT/PATCH /api/articles/{id}/`
- **权限**: 需要认证且为文章作者
- **描述**: 更新指定文章

### 2.5 删除文章

- **URL**: `DELETE /api/articles/{id}/`
- **权限**: 需要认证且为文章作者
- **描述**: 删除指定文章

---

## 3. 评论管理 API

### 3.1 获取文章评论列表

- **URL**: `GET /api/articles/{article_id}/comments/`
- **权限**: 无需认证
- **描述**: 获取指定文章的所有顶级评论（包含回复）

**响应示例**:

```json
[
    {
        "id": 1,
        "user": {
            "id": 1,
            "username": "commenter",
            "email": "commenter@example.com"
        },
        "article": 1,
        "content": "这是一条评论",
        "created_at": "2024-01-01T12:00:00Z",
        "parent": null,
        "replies": [
            {
                "id": 2,
                "user": {
                    "id": 2,
                    "username": "replier",
                    "email": "replier@example.com"
                },
                "article": 1,
                "content": "这是一条回复",
                "created_at": "2024-01-01T12:30:00Z",
                "parent": 1
            }
        ]
    }
]
```

### 3.2 创建评论

- **URL**: `POST /api/articles/{article_id}/comments/`
- **权限**: 需要认证
- **描述**: 为指定文章创建评论或回复

**请求体**:

```json
{
    "content": "评论内容",
    "parent": null  // 可选: 父评论ID，用于回复
}
```

### 3.3 获取评论详情

- **URL**: `GET /api/articles/{article_id}/comments/{comment_id}/`
- **权限**: 无需认证
- **描述**: 获取指定评论的详细信息

### 3.4 删除评论

- **URL**: `DELETE /api/articles/{article_id}/comments/{comment_id}/`
- **权限**: 需要认证且为评论作者
- **描述**: 删除指定评论（级联删除所有回复）

---

## 4. 数据模型

### 4.1 用户模型 (User)

```json
{
    "id": "integer",
    "username": "string",
    "email": "string (unique)",
    "bio": "string (可选)",
    "avatar": "string (图片路径, 可选)",
    "is_active": "boolean",
    "date_joined": "datetime"
}
```

### 4.2 文章模型 (Article)

```json
{
    "id": "integer",
    "title": "string (最大255字符)",
    "content": "text",
    "author": "User对象",
    "created_at": "datetime",
    "updated_at": "datetime",
    "status": "string (draft/published)"
}
```

### 4.3 评论模型 (Comment)

```json
{
    "id": "integer",
    "article": "Article对象",
    "user": "User对象",
    "content": "text",
    "created_at": "datetime",
    "parent": "Comment对象 (可选, 用于回复)"
}
```

---

## 5. 错误响应

### 5.1 认证错误

```json
{
    "detail": "Authentication credentials were not provided."
}
```

**状态码**: 401

### 5.2 权限错误

```json
{
    "detail": "You do not have permission to perform this action."
}
```

**状态码**: 403

### 5.3 资源不存在

```json
{
    "detail": "Not found."
}
```

**状态码**: 404

### 5.4 验证错误

```json
{
    "field_name": ["错误信息"]
}
```

**状态码**: 400

---

## 6. 状态码说明

- `200 OK`: 请求成功
- `201 Created`: 资源创建成功
- `204 No Content`: 删除成功
- `400 Bad Request`: 请求参数错误
- `401 Unauthorized`: 未认证
- `403 Forbidden`: 权限不足
- `404 Not Found`: 资源不存在
- `500 Internal Server Error`: 服务器内部错误

---

## 7. 使用示例

### 7.1 完整的用户注册和登录流程

1. **注册用户**:

```bash
curl -X POST http://localhost:8000/api/users/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "newuser@example.com",
    "password": "securepassword123",
    "password2": "securepassword123"
  }'
```

2. **登录获取令牌**:

```bash
curl -X POST http://localhost:8000/api/users/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "securepassword123"
  }'
```

3. **使用令牌访问受保护资源**:

```bash
curl -X GET http://localhost:8000/api/users/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 7.2 文章操作示例

1. **创建文章**:

```bash
curl -X POST http://localhost:8000/api/articles/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "我的第一篇文章",
    "content": "这是文章内容...",
    "status": "published"
  }'
```

2. **获取文章列表**:

```bash
curl -X GET http://localhost:8000/api/articles/
```

### 7.3 评论操作示例

1. **为文章添加评论**:

```bash
curl -X POST http://localhost:8000/api/articles/1/comments/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "这是一条很棒的评论！"
  }'
```

2. **回复评论**:

```bash
curl -X POST http://localhost:8000/api/articles/1/comments/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "我同意你的观点！",
    "parent": 1
  }'
```

---

## 8. 注意事项

1. **认证令牌有效期**: Access token 有效期较短，需要定期使用 refresh token 刷新
2. **文件上传**: 头像上传需要使用 multipart/form-data 格式
3. **分页**: 列表接口默认支持分页，可通过 page 和 page_size 参数控制
4. **权限控制**:
   - 未认证用户只能查看已发布的文章和评论
   - 认证用户可以查看自己的所有文章（包括草稿）
   - 只有作者可以修改/删除自己的文章和评论
5. **评论嵌套**: 支持一级回复，删除父评论会级联删除所有回复
6. **路由配置**: 评论路由通过嵌套方式实现，确保数据一致性和API语义清晰

---

## 9. 路由设计说明

### 9.1 评论路由设计原理

评论功能采用嵌套路由设计，这是RESTful API的最佳实践：

**为什么不使用独立的 `/api/comments/` 路由？**

1. **语义清晰**: `/api/articles/{id}/comments/` 明确表达评论与文章的从属关系
2. **数据安全**: 自动确保评论操作在正确的文章上下文中进行
3. **权限控制**: 更容易实现基于文章的权限控制
4. **RESTful原则**: 符合资源嵌套的设计原则

### 9.2 技术实现细节

- 使用 `drf-nested-routers` 包实现嵌套路由
- 在 `apps/articles/urls.py` 中统一管理文章和评论路由
- 不需要为 `comments` 应用创建独立的 `urls.py` 文件
- URL名称模式: `article-comments-list`, `article-comments-detail`

### 9.3 路由配置文件结构

```python
# apps/articles/urls.py
from rest_framework.routers import SimpleRouter
from rest_framework_nested.routers import NestedSimpleRouter

# 主路由: /api/articles/
router = SimpleRouter()
router.register(r'', ArticleViewSet, basename='article')

# 嵌套路由: /api/articles/{article_pk}/comments/
articles_router = NestedSimpleRouter(router, r'', lookup='article')
articles_router.register(r'comments', CommentViewSet, basename='article-comments')
```

---

## 10. 开发环境配置

### 9.1 启动后端服务

```bash
cd back_end
python manage.py runserver
```

### 9.2 数据库迁移

```bash
python manage.py makemigrations
python manage.py migrate
```

### 9.3 创建超级用户

```bash
python manage.py createsuperuser
```

---

*文档版本: v1.0*  
*最后更新: 2024年1月*
