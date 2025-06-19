# 博客平台 API 文档

## 目录

1. [认证机制](#认证机制)
2. [用户管理 API](#用户管理-api)
3. [文章管理 API](#文章管理-api)
4. [评论系统 API](#评论系统-api)
5. [权限矩阵](#权限矩阵)
6. [错误处理](#错误处理)
7. [数据模型](#数据模型)
8. [性能指标](#性能指标)
9. [完整示例](#完整示例)

---

## 认证机制

### JWT 认证流程

本平台使用 JWT (JSON Web Token) 进行身份认证，提供 `access` 和 `refresh` 双令牌机制。

#### 认证头格式

```http
Authorization: Bearer <access_token>
```

#### 令牌生命周期

- **Access Token**: 60 分钟
- **Refresh Token**: 7 天

#### 认证状态说明

| 状态         | 说明             | 可访问内容           |
| ------------ | ---------------- | -------------------- |
| 未认证       | 访客用户         | 已发布文章、公开评论 |
| 已认证未激活 | 注册但未验证邮箱 | 无法获取访问令牌     |
| 已认证已激活 | 正常用户         | 所有内容 + 个人操作  |
| 管理员       | 超级用户         | 所有内容 + 管理操作  |

---

## 用户管理 API

### 1.1 用户注册

注册新用户并发送邮箱验证邮件。

**端点**: `POST /api/users/register/`  
**权限**: 无需认证  
**内容类型**: `application/json`

#### 请求参数

| 参数      | 类型   | 必需 | 验证规则         | 说明     |
| --------- | ------ | ---- | ---------------- | -------- |
| username  | string | ✓    | 3-150 字符，唯一 | 用户名   |
| email     | string | ✓    | 有效邮箱，唯一   | 邮箱地址 |
| password  | string | ✓    | Django 密码验证  | 密码     |
| password2 | string | ✓    | 与 password 一致 | 确认密码 |

#### 请求示例

```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "SecurePass123!",
  "password2": "SecurePass123!"
}
```

#### 成功响应 (201 Created)

```json
{
  "message": "用户注册成功，请前往邮箱验证",
  "user_id": 1,
  "email": "newuser@example.com"
}
```

#### 错误响应 (400 Bad Request)

```json
{
  "username": ["该用户名已存在"],
  "email": ["该邮箱已被注册"],
  "password": ["密码过于简单，请包含大小写字母、数字和特殊字符"],
  "password2": ["两次密码不一致"]
}
```

#### cURL 示例

```bash
curl -X POST http://localhost:8000/api/users/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "newuser@example.com",
    "password": "SecurePass123!",
    "password2": "SecurePass123!"
  }'
```

#### JavaScript 示例

```javascript
const registerUser = async (userData) => {
  try {
    const response = await fetch("http://localhost:8000/api/users/register/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(userData),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(JSON.stringify(errorData));
    }

    return await response.json();
  } catch (error) {
    console.error("注册失败:", error);
    throw error;
  }
};
```

### 1.2 邮箱验证

验证用户邮箱并激活账户。

**端点**: `GET /api/users/verify-email/`  
**权限**: 无需认证

#### 查询参数

| 参数  | 类型   | 必需 | 说明         |
| ----- | ------ | ---- | ------------ |
| token | string | ✓    | 邮箱验证令牌 |

#### 请求示例

```http
GET /api/users/verify-email/?token=abc123def456ghi789
```

#### 成功响应 (200 OK)

```json
{
  "message": "邮箱验证成功！您的账户已激活",
  "status": "success"
}
```

#### 错误响应

**无效令牌 (400 Bad Request)**:

```json
{
  "error": "无效的验证token"
}
```

**缺少令牌 (400 Bad Request)**:

```json
{
  "message": "缺少token参数"
}
```

**重复验证 (200 OK)**:

```json
{
  "message": "邮箱已验证",
  "status": "already_verified"
}
```

### 1.3 用户登录

获取访问令牌（仅限已激活账户）。

**端点**: `POST /api/users/token/`  
**权限**: 无需认证

#### 请求参数

| 参数     | 类型   | 必需 | 说明     |
| -------- | ------ | ---- | -------- |
| email    | string | ✓    | 邮箱地址 |
| password | string | ✓    | 密码     |

#### 请求示例

```json
{
  "email": "newuser@example.com",
  "password": "SecurePass123!"
}
```

#### 成功响应 (200 OK)

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjMxNTUwMzYwLCJqdGkiOiI4YzQ5ZGE5ZjU4NjQ0YWU4YjZkZjU5ZjcyZTJjMzA2NCIsInVzZXJfaWQiOjF9.Qo_fVJJq-LKKhwBVRz3QExgdxOdg5RCJt-qTqH8WVQA",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTYzMjE1NTE2MCwianRpIjoiNGY2ZWRmYWE2N2Y2NDkwNWE4ZGZkNzU5MjE2ZDZhNzYiLCJ1c2VyX2lkIjoxfQ.wQJI0KjNBYg8K6JQ_s-FBZ7ZyTW5x1q6wY6qVnGnUPQ"
}
```

#### 错误响应

**账户未激活 (401 Unauthorized)**:

```json
{
  "detail": "账户未激活，请先验证邮箱"
}
```

**凭据错误 (401 Unauthorized)**:

```json
{
  "detail": "邮箱或密码错误"
}
```

### 1.4 刷新令牌

使用刷新令牌获取新的访问令牌。

**端点**: `POST /api/users/token/refresh/`  
**权限**: 无需认证

#### 请求参数

| 参数    | 类型   | 必需 | 说明     |
| ------- | ------ | ---- | -------- |
| refresh | string | ✓    | 刷新令牌 |

#### 成功响应 (200 OK)

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### 1.5 获取当前用户信息

获取当前登录用户的详细信息。

**端点**: `GET /api/users/me/`  
**权限**: 需要认证

#### 成功响应 (200 OK)

```json
{
  "id": 1,
  "username": "newuser",
  "email": "newuser@example.com",
  "bio": "个人简介",
  "avatar": "http://localhost:8000/media/avatars/1/user_1_avatar_12345678.jpg",
  "is_active": true
}
```

### 1.6 更新用户信息

更新当前用户的基本信息（不包括头像）。

**端点**: `PUT/PATCH /api/users/me/update/`  
**权限**: 需要认证

#### 请求参数

| 参数     | 类型   | 必需 | 说明     |
| -------- | ------ | ---- | -------- |
| username | string | ×    | 用户名   |
| bio      | string | ×    | 个人简介 |

#### 请求示例

```json
{
  "username": "updateduser",
  "bio": "这是我的新个人简介"
}
```

#### 成功响应 (200 OK)

```json
{
  "id": 1,
  "username": "updateduser",
  "email": "newuser@example.com",
  "bio": "这是我的新个人简介",
  "avatar": "http://localhost:8000/media/avatars/1/user_1_avatar_12345678.jpg",
  "is_active": true
}
```

### 1.7 用户头像上传

上传或更新用户头像。

**端点**: `PATCH /api/users/me/avatar/`  
**权限**: 需要认证  
**内容类型**: `multipart/form-data`

#### 请求参数

| 参数   | 类型 | 必需 | 限制              | 说明     |
| ------ | ---- | ---- | ----------------- | -------- |
| avatar | File | ✓    | 2MB, JPEG/PNG/GIF | 头像文件 |

#### 文件限制

- **支持格式**: JPEG, PNG, GIF
- **文件大小**: 最大 2MB
- **建议尺寸**: 200x200 像素
- **自动处理**: 中文文件名转换、唯一命名

#### cURL 示例

```bash
curl -X PATCH http://localhost:8000/api/users/me/avatar/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "avatar=@/path/to/avatar.jpg"
```

#### JavaScript 示例 (FormData)

```javascript
const uploadAvatar = async (file, token) => {
  const formData = new FormData();
  formData.append("avatar", file);

  try {
    const response = await fetch("http://localhost:8000/api/users/me/avatar/", {
      method: "PATCH",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: formData,
    });

    if (!response.ok) throw new Error("上传失败");
    return await response.json();
  } catch (error) {
    console.error("头像上传失败:", error);
    throw error;
  }
};
```

#### 成功响应 (200 OK)

```json
{
  "message": "头像更新成功",
  "avatar_url": "http://localhost:8000/media/avatars/1/user_1_avatar_12345678.jpg"
}
```

#### 错误响应

**文件过大 (400 Bad Request)**:

```json
{
  "avatar": ["头像文件太大了，不能超过2MB"]
}
```

**格式不支持 (400 Bad Request)**:

```json
{
  "avatar": ["只支持JPEG、PNG、GIF格式"]
}
```

**缺少文件 (400 Bad Request)**:

```json
{
  "error": "请选择要上传的头像文件"
}
```

---

## 文章管理 API

### 2.1 获取文章列表

获取文章列表，支持分页和权限过滤。

**端点**: `GET /api/articles/`  
**权限**: 无需认证（仅已发布）/ 认证用户（包含自己的草稿）

#### 查询参数

| 参数      | 类型    | 必需 | 默认值 | 说明     |
| --------- | ------- | ---- | ------ | -------- |
| page      | integer | ×    | 1      | 页码     |
| page_size | integer | ×    | 20     | 每页数量 |

#### 权限逻辑

- **未认证用户**: 仅能看到已发布文章
- **认证用户**: 自己的所有文章 + 他人已发布文章
- **管理员**: 所有文章

#### 成功响应 (200 OK)

```json
{
  "count": 25,
  "next": "http://localhost:8000/api/articles/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "我的第一篇博客",
      "content": "这是文章的完整内容...",
      "author": {
        "id": 1,
        "username": "author",
        "email": "author@example.com",
        "avatar": "http://localhost:8000/media/avatars/1/user_1_avatar.jpg"
      },
      "created_at": "2025-06-19T14:30:00Z",
      "updated_at": "2025-06-19T14:30:00Z",
      "status": "published"
    }
  ]
}
```

#### cURL 示例

```bash
# 获取第一页
curl -X GET http://localhost:8000/api/articles/

# 获取特定页码
curl -X GET "http://localhost:8000/api/articles/?page=2&page_size=10"

# 认证用户访问
curl -X GET http://localhost:8000/api/articles/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 2.2 获取文章详情

获取指定文章的详细信息。

**端点**: `GET /api/articles/{id}/`  
**权限**: 无需认证（仅已发布）/ 认证用户（自己的文章或他人已发布）

#### 路径参数

| 参数 | 类型    | 必需 | 说明    |
| ---- | ------- | ---- | ------- |
| id   | integer | ✓    | 文章 ID |

#### 成功响应 (200 OK)

```json
{
  "id": 1,
  "title": "我的第一篇博客",
  "content": "这是文章的完整内容...",
  "author": {
    "id": 1,
    "username": "author",
    "email": "author@example.com",
    "avatar": "http://localhost:8000/media/avatars/1/user_1_avatar.jpg"
  },
  "created_at": "2025-06-19T14:30:00Z",
  "updated_at": "2025-06-19T14:30:00Z",
  "status": "published"
}
```

#### 错误响应

**文章不存在 (404 Not Found)**:

```json
{
  "detail": "Not found."
}
```

**权限不足 (403 Forbidden)** (访问他人草稿):

```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 2.3 创建文章

创建新文章，自动分配作者权限。

**端点**: `POST /api/articles/`  
**权限**: 需要认证

#### 请求参数

| 参数    | 类型   | 必需 | 默认值 | 说明                      |
| ------- | ------ | ---- | ------ | ------------------------- |
| title   | string | ✓    | -      | 文章标题 (最大 255 字符)  |
| content | string | ✓    | -      | 文章内容                  |
| status  | string | ×    | draft  | 文章状态: draft/published |

#### 请求示例

```json
{
  "title": "我的新文章",
  "content": "这是文章的详细内容...",
  "status": "published"
}
```

#### 成功响应 (201 Created)

```json
{
  "id": 2,
  "title": "我的新文章",
  "content": "这是文章的详细内容...",
  "status": "published",
  "author": {
    "id": 1,
    "username": "author",
    "email": "author@example.com",
    "avatar": "http://localhost:8000/media/avatars/1/user_1_avatar.jpg"
  },
  "created_at": "2025-06-19T15:00:00Z",
  "updated_at": "2025-06-19T15:00:00Z"
}
```

#### Guardian 权限分配

创建文章时，系统自动为作者分配以下权限：

- `articles.edit_article`: 编辑文章
- `articles.publish_article`: 发布文章
- `articles.view_draft_article`: 查看草稿
- `articles.manage_article`: 管理文章

#### JavaScript 示例

```javascript
const createArticle = async (articleData, token) => {
  try {
    const response = await fetch("http://localhost:8000/api/articles/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(articleData),
    });

    if (!response.ok) throw new Error("创建失败");
    return await response.json();
  } catch (error) {
    console.error("文章创建失败:", error);
    throw error;
  }
};
```

### 2.4 更新文章

更新指定文章（仅作者或有权限的用户）。

**端点**: `PUT/PATCH /api/articles/{id}/`  
**权限**: 需要认证且为文章作者或有编辑权限

#### 路径参数

| 参数 | 类型    | 必需 | 说明    |
| ---- | ------- | ---- | ------- |
| id   | integer | ✓    | 文章 ID |

#### 请求参数 (同创建文章)

| 参数    | 类型   | 必需 | 说明     |
| ------- | ------ | ---- | -------- |
| title   | string | ×    | 文章标题 |
| content | string | ×    | 文章内容 |
| status  | string | ×    | 文章状态 |

#### 权限检查逻辑

1. 文章作者: 完全控制权限
2. 管理员: 完全控制权限
3. 有 `edit_article` 权限的用户: 可以编辑
4. 其他用户: 禁止访问

#### 成功响应 (200 OK)

```json
{
  "id": 1,
  "title": "更新后的文章标题",
  "content": "更新后的文章内容...",
  "status": "published",
  "author": {
    "id": 1,
    "username": "author",
    "email": "author@example.com",
    "avatar": "http://localhost:8000/media/avatars/1/user_1_avatar.jpg"
  },
  "created_at": "2025-06-19T14:30:00Z",
  "updated_at": "2025-06-19T15:30:00Z"
}
```

### 2.5 删除文章

删除指定文章（仅作者或管理员）。

**端点**: `DELETE /api/articles/{id}/`  
**权限**: 需要认证且为文章作者或管理员

#### 成功响应 (204 No Content)

无响应体，状态码为 204。

#### 级联删除

删除文章时会自动删除：

- 所有相关评论
- 所有相关的 Guardian 对象权限

---

## 评论系统 API

### 3.1 获取文章评论列表

获取指定文章的所有顶级评论（包含回复的嵌套结构）。

**端点**: `GET /api/articles/{article_id}/comments/`  
**权限**: 无需认证

#### 路径参数

| 参数       | 类型    | 必需 | 说明    |
| ---------- | ------- | ---- | ------- |
| article_id | integer | ✓    | 文章 ID |

#### 嵌套结构说明

- 接口返回顶级评论列表
- 每个顶级评论包含 `replies` 字段，包含所有回复
- 回复的 `parent` 字段指向父评论 ID

#### 成功响应 (200 OK)

```json
[
  {
    "id": 1,
    "user": {
      "id": 2,
      "username": "commenter",
      "email": "commenter@example.com",
      "avatar": "http://localhost:8000/media/avatars/2/user_2_avatar.jpg"
    },
    "article": 1,
    "content": "这是一条很有深度的评论！",
    "created_at": "2025-06-19T16:00:00Z",
    "parent": null,
    "replies": [
      {
        "id": 3,
        "user": {
          "id": 1,
          "username": "author",
          "email": "author@example.com",
          "avatar": "http://localhost:8000/media/avatars/1/user_1_avatar.jpg"
        },
        "article": 1,
        "content": "谢谢你的评论！",
        "created_at": "2025-06-19T16:15:00Z",
        "parent": 1
      }
    ]
  },
  {
    "id": 2,
    "user": {
      "id": 3,
      "username": "reader",
      "email": "reader@example.com",
      "avatar": null
    },
    "article": 1,
    "content": "文章写得很好！",
    "created_at": "2025-06-19T16:30:00Z",
    "parent": null,
    "replies": []
  }
]
```

### 3.2 创建评论

为指定文章创建评论或回复。

**端点**: `POST /api/articles/{article_id}/comments/`  
**权限**: 需要认证

#### 路径参数

| 参数       | 类型    | 必需 | 说明    |
| ---------- | ------- | ---- | ------- |
| article_id | integer | ✓    | 文章 ID |

#### 请求参数

| 参数    | 类型    | 必需 | 说明                   |
| ------- | ------- | ---- | ---------------------- |
| content | string  | ✓    | 评论内容               |
| parent  | integer | ×    | 父评论 ID (回复时使用) |

#### 创建顶级评论示例

```json
{
  "content": "这是一条新评论！"
}
```

#### 创建回复示例

```json
{
  "content": "这是一条回复！",
  "parent": 1
}
```

#### 成功响应 (201 Created)

```json
{
  "id": 4,
  "user": {
    "id": 1,
    "username": "current_user",
    "email": "user@example.com",
    "avatar": "http://localhost:8000/media/avatars/1/user_1_avatar.jpg"
  },
  "article": 1,
  "content": "这是一条新评论！",
  "created_at": "2025-06-19T17:00:00Z",
  "parent": null
}
```

#### 验证错误

**父评论不属于当前文章 (400 Bad Request)**:

```json
{
  "parent": ["父评论不属于当前文章。"]
}
```

**文章不存在 (404 Not Found)**:

```json
{
  "detail": "Not found."
}
```

#### Guardian 权限分配

创建评论时，系统自动为作者分配以下权限：

- `comments.reply_comment`: 回复评论
- `comments.manage_comment`: 管理评论

#### JavaScript 示例

```javascript
const createComment = async (articleId, commentData, token) => {
  try {
    const response = await fetch(
      `http://localhost:8000/api/articles/${articleId}/comments/`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(commentData),
      }
    );

    if (!response.ok) throw new Error("评论失败");
    return await response.json();
  } catch (error) {
    console.error("评论创建失败:", error);
    throw error;
  }
};

// 创建顶级评论
await createComment(1, { content: "很棒的文章！" }, token);

// 创建回复
await createComment(1, { content: "我也这么认为", parent: 1 }, token);
```

### 3.3 获取单个评论详情

获取指定评论的详细信息。

**端点**: `GET /api/articles/{article_id}/comments/{comment_id}/`  
**权限**: 无需认证

#### 路径参数

| 参数       | 类型    | 必需 | 说明    |
| ---------- | ------- | ---- | ------- |
| article_id | integer | ✓    | 文章 ID |
| comment_id | integer | ✓    | 评论 ID |

#### 成功响应 (200 OK)

```json
{
  "id": 1,
  "user": {
    "id": 2,
    "username": "commenter",
    "email": "commenter@example.com",
    "avatar": "http://localhost:8000/media/avatars/2/user_2_avatar.jpg"
  },
  "article": 1,
  "content": "这是一条很有深度的评论！",
  "created_at": "2025-06-19T16:00:00Z",
  "parent": null
}
```

### 3.4 删除评论

删除指定评论（仅评论作者或管理员）。

**端点**: `DELETE /api/articles/{article_id}/comments/{comment_id}/`  
**权限**: 需要认证且为评论作者或管理员

#### 路径参数

| 参数       | 类型    | 必需 | 说明    |
| ---------- | ------- | ---- | ------- |
| article_id | integer | ✓    | 文章 ID |
| comment_id | integer | ✓    | 评论 ID |

#### 成功响应 (204 No Content)

无响应体，状态码为 204。

#### 级联删除

删除评论时会：

- 级联删除所有子回复
- 清理相关的 Guardian 对象权限

#### 重要说明

> **注意**: 评论系统不支持编辑功能。如需修改评论内容，请删除后重新创建。

---

## 权限矩阵

### 用户角色与权限对应关系

| 操作           | 未认证用户 | 认证用户 | 文章作者 | 评论作者 | 管理员 |
| -------------- | ---------- | -------- | -------- | -------- | ------ |
| **用户操作**   |
| 注册用户       | ✓          | ✓        | ✓        | ✓        | ✓      |
| 登录           | ✓          | ✓        | ✓        | ✓        | ✓      |
| 查看个人信息   | ✗          | ✓        | ✓        | ✓        | ✓      |
| 更新个人信息   | ✗          | ✓        | ✓        | ✓        | ✓      |
| 上传头像       | ✗          | ✓        | ✓        | ✓        | ✓      |
| **文章操作**   |
| 查看已发布文章 | ✓          | ✓        | ✓        | ✓        | ✓      |
| 查看草稿文章   | ✗          | ✗        | ✓        | ✗        | ✓      |
| 创建文章       | ✗          | ✓        | ✓        | ✓        | ✓      |
| 编辑自己文章   | ✗          | ✗        | ✓        | ✗        | ✓      |
| 编辑他人文章   | ✗          | ✗        | ✗        | ✗        | ✓      |
| 删除自己文章   | ✗          | ✗        | ✓        | ✗        | ✓      |
| 删除他人文章   | ✗          | ✗        | ✗        | ✗        | ✓      |
| **评论操作**   |
| 查看评论       | ✓          | ✓        | ✓        | ✓        | ✓      |
| 创建评论       | ✗          | ✓        | ✓        | ✓        | ✓      |
| 删除自己评论   | ✗          | ✗        | ✗        | ✓        | ✓      |
| 删除他人评论   | ✗          | ✗        | ✗        | ✗        | ✓      |

### Guardian 对象级权限详解

#### 文章权限

| 权限代码                      | 权限名称 | 说明                     | 默认分配 |
| ----------------------------- | -------- | ------------------------ | -------- |
| `articles.edit_article`       | 编辑文章 | 可以修改文章内容和状态   | 文章作者 |
| `articles.publish_article`    | 发布文章 | 可以将草稿发布为正式文章 | 文章作者 |
| `articles.view_draft_article` | 查看草稿 | 可以查看未发布的草稿文章 | 文章作者 |
| `articles.manage_article`     | 管理文章 | 完整的文章管理权限       | 文章作者 |

#### 评论权限

| 权限代码                    | 权限名称 | 说明               | 默认分配 |
| --------------------------- | -------- | ------------------ | -------- |
| `comments.reply_comment`    | 回复评论 | 可以回复特定评论   | 评论作者 |
| `comments.manage_comment`   | 管理评论 | 完整的评论管理权限 | 评论作者 |
| `comments.moderate_comment` | 审核评论 | 可以审核和管理评论 | 管理员   |

### 权限检查优先级

1. **超级管理员**: 拥有所有权限，跳过其他检查
2. **对象所有者**: 文章作者对文章、评论作者对评论拥有完整权限
3. **Guardian 对象权限**: 检查用户是否被明确授权特定权限
4. **默认权限**: 基于用户认证状态的基础权限

---

## 错误处理

### 标准错误响应格式

所有 API 错误响应都遵循统一的格式，包含错误信息和相应的 HTTP 状态码。

#### 基本错误格式

```json
{
  "detail": "错误描述信息"
}
```

#### 字段验证错误格式

```json
{
  "字段名": ["错误信息1", "错误信息2"],
  "另一个字段": ["错误信息"]
}
```

### 常见错误码及解决方案

#### 400 Bad Request - 请求参数错误

**原因**: 请求数据格式错误、字段验证失败

**示例响应**:

```json
{
  "title": ["文章标题不能为空"],
  "email": ["请输入有效的邮箱地址"]
}
```

**解决方案**:

- 检查请求参数是否符合 API 文档要求
- 验证必需字段是否都已提供
- 确认数据类型和格式正确

#### 401 Unauthorized - 认证失败

**原因**: 缺少认证信息或认证信息无效

**示例响应**:

```json
{
  "detail": "Authentication credentials were not provided."
}
```

**解决方案**:

- 确保请求头包含有效的 Authorization
- 检查访问令牌是否过期
- 验证令牌格式是否正确

#### 403 Forbidden - 权限不足

**原因**: 用户已认证但没有执行该操作的权限

**示例响应**:

```json
{
  "detail": "You do not have permission to perform this action."
}
```

**解决方案**:

- 确认当前用户角色是否有相应权限
- 检查是否尝试操作他人的资源
- 联系管理员获取必要权限

#### 404 Not Found - 资源不存在

**原因**: 请求的资源不存在或已被删除

**示例响应**:

```json
{
  "detail": "Not found."
}
```

**解决方案**:

- 验证资源 ID 是否正确
- 确认资源是否已被删除
- 检查 URL 路径是否正确

#### 429 Too Many Requests - 请求频率限制

**原因**: 请求频率超过限制（如果启用了频率限制）

**示例响应**:

```json
{
  "detail": "Request was throttled. Expected available in 60 seconds."
}
```

**解决方案**:

- 减缓请求频率
- 等待指定时间后重试
- 实现客户端重试机制

#### 500 Internal Server Error - 服务器内部错误

**原因**: 服务器内部错误

**示例响应**:

```json
{
  "detail": "A server error occurred."
}
```

**解决方案**:

- 稍后重试请求
- 检查服务器日志
- 联系技术支持

### 错误处理最佳实践

#### 客户端错误处理示例

```javascript
const handleApiRequest = async (url, options) => {
  try {
    const response = await fetch(url, options);

    if (!response.ok) {
      const errorData = await response.json();

      switch (response.status) {
        case 400:
          // 处理验证错误
          console.error("请求参数错误:", errorData);
          break;
        case 401:
          // 处理认证错误
          console.error("认证失败，请重新登录");
          // 重定向到登录页面
          break;
        case 403:
          // 处理权限错误
          console.error("权限不足:", errorData.detail);
          break;
        case 404:
          // 处理资源不存在
          console.error("资源不存在:", errorData.detail);
          break;
        case 429:
          // 处理频率限制
          console.error("请求过于频繁，请稍后重试");
          break;
        default:
          console.error("未知错误:", errorData);
      }

      throw new Error(errorData.detail || "请求失败");
    }

    return await response.json();
  } catch (error) {
    console.error("API请求失败:", error);
    throw error;
  }
};
```

#### 表单验证错误处理

```javascript
const handleFormErrors = (errors) => {
  // 清除之前的错误信息
  clearFormErrors();

  // 显示字段级错误
  Object.keys(errors).forEach((field) => {
    const fieldElement = document.querySelector(`[name="${field}"]`);
    if (fieldElement) {
      const errorMessages = Array.isArray(errors[field])
        ? errors[field]
        : [errors[field]];

      showFieldError(fieldElement, errorMessages.join(", "));
    }
  });
};
```

---

## 数据模型

### 用户模型 (User)

**表名**: `auth_user` (扩展)

```json
{
  "id": "integer (主键)",
  "username": "string (用户名，3-150字符，唯一)",
  "email": "string (邮箱地址，唯一，用于登录)",
  "bio": "string (个人简介，最大500字符，可选)",
  "avatar": "string (头像URL，可选)",
  "is_active": "boolean (账户激活状态，默认false)",
  "is_staff": "boolean (管理员状态)",
  "is_superuser": "boolean (超级用户状态)",
  "email_verification_token": "string (邮箱验证令牌，内部字段)",
  "date_joined": "datetime (注册时间)",
  "last_login": "datetime (最后登录时间)"
}
```

#### 字段说明

- **id**: 自增主键，用户唯一标识符
- **username**: 用户显示名称，允许中文和特殊字符
- **email**: 邮箱地址，作为登录凭据 (USERNAME_FIELD)
- **bio**: 用户个人简介，支持多行文本
- **avatar**: 头像图片完整 URL，使用自定义上传路径
- **is_active**: 账户激活状态，新用户注册时为 `false`
- **email_verification_token**: 邮箱验证用的 UUID 令牌
- **date_joined**: 用户首次注册时间

#### 头像存储路径

```
media/avatars/{user_id}/user_{user_id}_avatar_{random_hash}.{ext}
```

示例: `media/avatars/1/user_1_avatar_12345678.jpg`

### 文章模型 (Article)

**表名**: `articles_article`

```json
{
  "id": "integer (主键)",
  "title": "string (标题，最大255字符)",
  "content": "text (内容，无长度限制)",
  "author": "ForeignKey (关联User，级联删除)",
  "status": "string (状态：draft/published)",
  "created_at": "datetime (创建时间，自动)",
  "updated_at": "datetime (更新时间，自动)"
}
```

#### 状态选择

| 状态值      | 中文名称 | 说明                 |
| ----------- | -------- | -------------------- |
| `draft`     | 草稿     | 未发布，仅作者可见   |
| `published` | 已发布   | 公开发布，所有人可见 |

#### 数据库约束

- **title**: NOT NULL, VARCHAR(255)
- **content**: NOT NULL, TEXT
- **author_id**: NOT NULL, 外键约束
- **status**: NOT NULL, DEFAULT 'draft'
- **索引**: created_at(降序), author_id, status

### 评论模型 (Comment)

**表名**: `comments_comment`

```json
{
  "id": "integer (主键)",
  "article": "ForeignKey (关联Article，级联删除)",
  "user": "ForeignKey (关联User，级联删除)",
  "content": "text (评论内容)",
  "parent": "ForeignKey (父评论，自关联，可选)",
  "created_at": "datetime (创建时间，自动)"
}
```

#### 嵌套评论结构

- **顶级评论**: `parent` 为 `null`
- **回复评论**: `parent` 指向父评论 ID
- **层级限制**: 目前支持二级评论（评论 + 回复）

#### 数据库约束

- **content**: NOT NULL, TEXT
- **article_id**: NOT NULL, 外键约束
- **user_id**: NOT NULL, 外键约束
- **parent_id**: 可选, 外键约束 (自关联)
- **索引**: article_id, parent_id, created_at

### 权限模型 (Guardian 扩展)

#### 文章权限表

**表名**: `articles_articleuserobjectpermission`

```json
{
  "id": "integer (主键)",
  "permission": "ForeignKey (权限类型)",
  "user": "ForeignKey (用户)",
  "content_object": "ForeignKey (文章对象)"
}
```

#### 评论权限表

**表名**: `comments_commentuserobjectpermission`

```json
{
  "id": "integer (主键)",
  "permission": "ForeignKey (权限类型)",
  "user": "ForeignKey (用户)",
  "content_object": "ForeignKey (评论对象)"
}
```

### 数据关系图

```
User (用户)
├── articles (一对多) → Article (文章)
│   └── comments (一对多) → Comment (评论)
│       └── replies (一对多) → Comment (回复)
├── comments (一对多) → Comment (评论)
├── user_permissions (多对多) → 对象权限
└── avatar_file → 头像文件
```

---

## 性能指标

### API 响应时间参考

#### 基准性能指标 (开发环境)

| 操作类型     | 平均响应时间 | 95th 百分位 | 说明         |
| ------------ | ------------ | ----------- | ------------ |
| 用户注册     | 150ms        | 300ms       | 包含邮件发送 |
| 用户登录     | 80ms         | 150ms       | JWT 令牌生成 |
| 获取文章列表 | 100ms        | 200ms       | 20 条记录/页 |
| 获取文章详情 | 50ms         | 100ms       | 单条记录     |
| 创建文章     | 120ms        | 250ms       | 包含权限分配 |
| 创建评论     | 90ms         | 180ms       | 包含权限分配 |
| 头像上传     | 500ms        | 1000ms      | 依赖文件大小 |

#### 性能优化建议

##### 数据库查询优化

1. **使用 select_related 优化外键查询**:

```python
# 文章列表查询优化
Article.objects.select_related('author').filter(status='published')

# 评论查询优化
Comment.objects.select_related('user', 'parent').filter(article=article)
```

2. **使用 prefetch_related 优化反向关系**:

```python
# 获取文章及其所有评论
Article.objects.prefetch_related('comments__user').get(id=1)
```

3. **添加数据库索引**:

```python
class Meta:
    indexes = [
        models.Index(fields=['status', '-created_at']),
        models.Index(fields=['author', 'status']),
    ]
```

##### 缓存策略

1. **Redis 缓存热点数据**:

```python
# 缓存文章详情
cache.set(f'article:{article_id}', article_data, timeout=3600)

# 缓存用户信息
cache.set(f'user:{user_id}', user_data, timeout=1800)
```

2. **使用 Django Cache Framework**:

```python
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)  # 缓存15分钟
def article_list(request):
    # 文章列表视图
    pass
```

### 分页策略

#### 默认分页设置

```python
# settings.py
REST_FRAMEWORK = {
    'PAGE_SIZE': 20,
    'PAGE_SIZE_QUERY_PARAM': 'page_size',
    'MAX_PAGE_SIZE': 100,
}
```

#### 分页最佳实践

1. **文章列表分页**:

   - 默认每页 20 条
   - 最大每页 100 条
   - 使用 `page` 和 `page_size` 参数

2. **评论分页**:

   - 顶级评论分页加载
   - 回复按需加载（点击展开）

3. **性能考虑**:

```javascript
// 前端无限滚动加载
const loadMoreArticles = async (page) => {
  const response = await fetch(`/api/articles/?page=${page}&page_size=10`);
  const data = await response.json();

  // 追加到现有列表
  appendArticles(data.results);

  // 检查是否还有更多
  if (data.next) {
    hasMore = true;
  }
};
```

### 文件上传优化

#### 头像上传限制

- **文件大小**: 最大 2MB
- **支持格式**: JPEG, PNG, GIF
- **处理策略**: 异步处理 + 进度反馈

#### 优化建议

1. **前端预处理**:

```javascript
const compressImage = (file, maxWidth = 800, quality = 0.8) => {
  return new Promise((resolve) => {
    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");
    const img = new Image();

    img.onload = () => {
      const ratio = Math.min(maxWidth / img.width, maxWidth / img.height);
      canvas.width = img.width * ratio;
      canvas.height = img.height * ratio;

      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      canvas.toBlob(resolve, "image/jpeg", quality);
    };

    img.src = URL.createObjectURL(file);
  });
};
```

2. **后端处理**:

```python
# 异步处理头像
from celery import shared_task

@shared_task
def process_avatar(user_id, image_path):
    # 图片压缩、格式转换等
    pass
```

### 监控和告警

#### 关键指标监控

1. **API 响应时间**
2. **错误率**
3. **并发用户数**
4. **数据库连接数**
5. **内存使用率**

#### 日志记录

```python
import logging

logger = logging.getLogger(__name__)

def create_article(request):
    start_time = time.time()
    try:
        # 业务逻辑
        result = process_article_creation(request.data)

        # 记录成功日志
        logger.info(f'Article created successfully. User: {request.user.id}, Time: {time.time() - start_time:.2f}s')
        return result
    except Exception as e:
        # 记录错误日志
        logger.error(f'Article creation failed. User: {request.user.id}, Error: {str(e)}, Time: {time.time() - start_time:.2f}s')
        raise
```

---

## 完整示例

### 用户完整操作流程

#### 1. 注册 → 验证 → 登录

```javascript
// 1. 用户注册
const registerUser = async () => {
  const userData = {
    username: "testuser",
    email: "test@example.com",
    password: "SecurePass123!",
    password2: "SecurePass123!",
  };

  try {
    const response = await fetch("http://localhost:8000/api/users/register/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(userData),
    });

    const result = await response.json();
    console.log("注册成功:", result);

    // 提示用户检查邮箱
    alert("注册成功！请检查邮箱完成验证。");
  } catch (error) {
    console.error("注册失败:", error);
  }
};

// 2. 邮箱验证 (通常通过邮件链接自动完成)
const verifyEmail = async (token) => {
  try {
    const response = await fetch(
      `http://localhost:8000/api/users/verify-email/?token=${token}`
    );
    const result = await response.json();

    if (response.ok) {
      alert("邮箱验证成功！可以登录了。");
    }
  } catch (error) {
    console.error("验证失败:", error);
  }
};

// 3. 用户登录
const loginUser = async () => {
  const loginData = {
    email: "test@example.com",
    password: "SecurePass123!",
  };

  try {
    const response = await fetch("http://localhost:8000/api/users/token/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(loginData),
    });

    const tokens = await response.json();

    // 存储令牌
    localStorage.setItem("access_token", tokens.access);
    localStorage.setItem("refresh_token", tokens.refresh);

    console.log("登录成功！");
    return tokens;
  } catch (error) {
    console.error("登录失败:", error);
  }
};
```

#### 2. 令牌刷新机制

```javascript
class TokenManager {
  constructor() {
    this.accessToken = localStorage.getItem("access_token");
    this.refreshToken = localStorage.getItem("refresh_token");
  }

  // 刷新访问令牌
  async refreshAccessToken() {
    try {
      const response = await fetch(
        "http://localhost:8000/api/users/token/refresh/",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh: this.refreshToken }),
        }
      );

      if (response.ok) {
        const data = await response.json();
        this.accessToken = data.access;
        localStorage.setItem("access_token", data.access);
        return data.access;
      } else {
        // 刷新令牌也失效，需要重新登录
        this.logout();
        throw new Error("登录已过期，请重新登录");
      }
    } catch (error) {
      console.error("令牌刷新失败:", error);
      throw error;
    }
  }

  // 发送认证请求
  async authenticatedFetch(url, options = {}) {
    const headers = {
      Authorization: `Bearer ${this.accessToken}`,
      "Content-Type": "application/json",
      ...options.headers,
    };

    try {
      let response = await fetch(url, { ...options, headers });

      // 如果访问令牌过期，尝试刷新
      if (response.status === 401) {
        await this.refreshAccessToken();
        headers["Authorization"] = `Bearer ${this.accessToken}`;
        response = await fetch(url, { ...options, headers });
      }

      return response;
    } catch (error) {
      console.error("认证请求失败:", error);
      throw error;
    }
  }

  // 登出
  logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    this.accessToken = null;
    this.refreshToken = null;
    // 重定向到登录页面
    window.location.href = "/login";
  }
}

// 使用示例
const tokenManager = new TokenManager();
```

### 文章管理完整示例

#### 3. 文章 CRUD 操作

```javascript
class ArticleManager {
  constructor(tokenManager) {
    this.tokenManager = tokenManager;
    this.baseUrl = "http://localhost:8000/api/articles";
  }

  // 获取文章列表
  async getArticles(page = 1, pageSize = 20) {
    try {
      const url = `${this.baseUrl}/?page=${page}&page_size=${pageSize}`;
      const response = await this.tokenManager.authenticatedFetch(url);

      if (!response.ok) throw new Error("获取文章列表失败");
      return await response.json();
    } catch (error) {
      console.error("文章列表获取失败:", error);
      throw error;
    }
  }

  // 获取文章详情
  async getArticle(articleId) {
    try {
      const response = await this.tokenManager.authenticatedFetch(
        `${this.baseUrl}/${articleId}/`
      );

      if (!response.ok) throw new Error("文章不存在或无权限访问");
      return await response.json();
    } catch (error) {
      console.error("文章详情获取失败:", error);
      throw error;
    }
  }

  // 创建文章
  async createArticle(articleData) {
    try {
      const response = await this.tokenManager.authenticatedFetch(
        this.baseUrl + "/",
        {
          method: "POST",
          body: JSON.stringify(articleData),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(JSON.stringify(errorData));
      }

      return await response.json();
    } catch (error) {
      console.error("文章创建失败:", error);
      throw error;
    }
  }

  // 更新文章
  async updateArticle(articleId, updateData) {
    try {
      const response = await this.tokenManager.authenticatedFetch(
        `${this.baseUrl}/${articleId}/`,
        {
          method: "PATCH",
          body: JSON.stringify(updateData),
        }
      );

      if (!response.ok) throw new Error("文章更新失败");
      return await response.json();
    } catch (error) {
      console.error("文章更新失败:", error);
      throw error;
    }
  }

  // 删除文章
  async deleteArticle(articleId) {
    try {
      const response = await this.tokenManager.authenticatedFetch(
        `${this.baseUrl}/${articleId}/`,
        {
          method: "DELETE",
        }
      );

      if (!response.ok) throw new Error("文章删除失败");
      return true;
    } catch (error) {
      console.error("文章删除失败:", error);
      throw error;
    }
  }
}

// 使用示例
const articleManager = new ArticleManager(tokenManager);

// 创建文章
const newArticle = await articleManager.createArticle({
  title: "我的新文章",
  content: "这是文章内容...",
  status: "published",
});

// 获取文章列表
const articles = await articleManager.getArticles(1, 10);
console.log("文章列表:", articles);
```

### 评论系统完整示例

#### 4. 评论管理

```javascript
class CommentManager {
  constructor(tokenManager) {
    this.tokenManager = tokenManager;
  }

  // 获取文章评论列表
  async getComments(articleId) {
    try {
      const url = `http://localhost:8000/api/articles/${articleId}/comments/`;
      const response = await this.tokenManager.authenticatedFetch(url);

      if (!response.ok) throw new Error("获取评论失败");
      return await response.json();
    } catch (error) {
      console.error("评论列表获取失败:", error);
      throw error;
    }
  }

  // 创建评论
  async createComment(articleId, commentData) {
    try {
      const url = `http://localhost:8000/api/articles/${articleId}/comments/`;
      const response = await this.tokenManager.authenticatedFetch(url, {
        method: "POST",
        body: JSON.stringify(commentData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(JSON.stringify(errorData));
      }

      return await response.json();
    } catch (error) {
      console.error("评论创建失败:", error);
      throw error;
    }
  }

  // 删除评论
  async deleteComment(articleId, commentId) {
    try {
      const url = `http://localhost:8000/api/articles/${articleId}/comments/${commentId}/`;
      const response = await this.tokenManager.authenticatedFetch(url, {
        method: "DELETE",
      });

      if (!response.ok) throw new Error("评论删除失败");
      return true;
    } catch (error) {
      console.error("评论删除失败:", error);
      throw error;
    }
  }
}

// 使用示例
const commentManager = new CommentManager(tokenManager);

// 创建顶级评论
await commentManager.createComment(1, {
  content: "这篇文章写得很好！",
});

// 创建回复
await commentManager.createComment(1, {
  content: "我也这么认为！",
  parent: 1,
});

// 获取评论列表
const comments = await commentManager.getComments(1);
console.log("评论列表:", comments);
```

#### 5. 用户资料管理

```javascript
class UserManager {
  constructor(tokenManager) {
    this.tokenManager = tokenManager;
    this.baseUrl = "http://localhost:8000/api/users";
  }

  // 获取当前用户信息
  async getCurrentUser() {
    try {
      const response = await this.tokenManager.authenticatedFetch(
        `${this.baseUrl}/me/`
      );

      if (!response.ok) throw new Error("获取用户信息失败");
      return await response.json();
    } catch (error) {
      console.error("用户信息获取失败:", error);
      throw error;
    }
  }

  // 更新用户信息
  async updateUser(userData) {
    try {
      const response = await this.tokenManager.authenticatedFetch(
        `${this.baseUrl}/me/update/`,
        {
          method: "PATCH",
          body: JSON.stringify(userData),
        }
      );

      if (!response.ok) throw new Error("用户信息更新失败");
      return await response.json();
    } catch (error) {
      console.error("用户信息更新失败:", error);
      throw error;
    }
  }

  // 上传头像
  async uploadAvatar(file) {
    try {
      const formData = new FormData();
      formData.append("avatar", file);

      const response = await this.tokenManager.authenticatedFetch(
        `${this.baseUrl}/me/avatar/`,
        {
          method: "PATCH",
          headers: {
            // 移除 Content-Type，让浏览器自动设置
          },
          body: formData,
        }
      );

      if (!response.ok) throw new Error("头像上传失败");
      return await response.json();
    } catch (error) {
      console.error("头像上传失败:", error);
      throw error;
    }
  }
}

// 使用示例
const userManager = new UserManager(tokenManager);

// 更新用户信息
await userManager.updateUser({
  username: "新用户名",
  bio: "新的个人简介",
});

// 头像上传示例
const handleAvatarUpload = async (event) => {
  const file = event.target.files[0];
  if (!file) return;

  // 文件大小检查
  if (file.size > 2 * 1024 * 1024) {
    alert("文件大小不能超过2MB");
    return;
  }

  // 文件类型检查
  const allowedTypes = ["image/jpeg", "image/png", "image/gif"];
  if (!allowedTypes.includes(file.type)) {
    alert("只支持JPEG、PNG、GIF格式");
    return;
  }

  try {
    const result = await userManager.uploadAvatar(file);
    console.log("头像上传成功:", result);
    alert("头像更新成功！");
  } catch (error) {
    alert("头像上传失败：" + error.message);
  }
};
```

### 综合应用示例

#### 6. 完整的博客应用

```javascript
class BlogApp {
  constructor() {
    this.tokenManager = new TokenManager();
    this.articleManager = new ArticleManager(this.tokenManager);
    this.commentManager = new CommentManager(this.tokenManager);
    this.userManager = new UserManager(this.tokenManager);
    this.currentUser = null;

    this.init();
  }

  async init() {
    // 检查登录状态
    if (this.tokenManager.accessToken) {
      await this.loadUserProfile();
      await this.loadArticles();
    } else {
      this.showLoginForm();
    }
  }

  // 加载用户资料
  async loadUserProfile() {
    try {
      this.currentUser = await this.userManager.getCurrentUser();
      this.displayUserInfo(this.currentUser);
    } catch (error) {
      console.error("加载用户资料失败:", error);
      this.tokenManager.logout();
    }
  }

  // 加载文章列表
  async loadArticles(page = 1) {
    try {
      const response = await this.articleManager.getArticles(page, 10);
      this.displayArticles(response.results);
      this.setupPagination(response);
    } catch (error) {
      console.error("加载文章失败:", error);
    }
  }

  // 显示用户信息
  displayUserInfo(user) {
    const userInfoContainer = document.getElementById("user-info");
    if (userInfoContainer) {
      userInfoContainer.innerHTML = `
        <div class="user-profile">
          <img src="${
            user.avatar || "/default-avatar.png"
          }" alt="头像" class="avatar">
          <div class="user-details">
            <h3>${user.username}</h3>
            <p>${user.bio || "暂无个人简介"}</p>
            <button onclick="app.showProfileEditForm()">编辑资料</button>
          </div>
        </div>
      `;
    }
  }

  // 显示文章列表
  displayArticles(articles) {
    const container = document.getElementById("articles-container");
    if (!container) return;

    container.innerHTML = articles
      .map(
        (article) => `
      <div class="article-card" data-id="${article.id}">
        <header class="article-header">
          <h3 class="article-title">${article.title}</h3>
          <div class="article-meta">
            <img src="${
              article.author.avatar || "/default-avatar.png"
            }" alt="作者头像" class="author-avatar">
            <span class="author-name">${article.author.username}</span>
            <span class="publish-date">${new Date(
              article.created_at
            ).toLocaleDateString()}</span>
            <span class="article-status status-${article.status}">${
          article.status === "published" ? "已发布" : "草稿"
        }</span>
          </div>
        </header>
        
        <div class="article-content">
          ${
            article.content.length > 200
              ? article.content.substring(0, 200) + "..."
              : article.content
          }
        </div>
        
        <div class="article-actions">
          <button onclick="app.viewArticle(${
            article.id
          })" class="btn-primary">查看详情</button>
          ${
            this.isCurrentUserAuthor(article)
              ? `
            <button onclick="app.editArticle(${article.id})" class="btn-secondary">编辑</button>
            <button onclick="app.deleteArticle(${article.id})" class="btn-danger">删除</button>
          `
              : ""
          }
        </div>
      </div>
    `
      )
      .join("");
  }

  // 查看文章详情
  async viewArticle(articleId) {
    try {
      this.showLoading();
      const [article, comments] = await Promise.all([
        this.articleManager.getArticle(articleId),
        this.commentManager.getComments(articleId),
      ]);

      this.displayArticleDetail(article, comments);
    } catch (error) {
      console.error("加载文章详情失败:", error);
      alert("文章加载失败: " + error.message);
    } finally {
      this.hideLoading();
    }
  }

  // 显示文章详情
  displayArticleDetail(article, comments) {
    const container = document.getElementById("article-detail");
    if (!container) return;

    container.innerHTML = `
      <article class="article-detail">
        <header class="article-header">
          <h1 class="article-title">${article.title}</h1>
          <div class="article-meta">
            <img src="${
              article.author.avatar || "/default-avatar.png"
            }" alt="作者头像" class="author-avatar">
            <div class="author-info">
              <span class="author-name">${article.author.username}</span>
              <span class="publish-date">${new Date(
                article.created_at
              ).toLocaleString()}</span>
              ${
                article.created_at !== article.updated_at
                  ? `
                <span class="update-date">更新于 ${new Date(
                  article.updated_at
                ).toLocaleString()}</span>
              `
                  : ""
              }
            </div>
          </div>
        </header>
        
        <div class="article-content">${article.content.replace(
          /\n/g,
          "<br>"
        )}</div>
        
        ${
          this.isCurrentUserAuthor(article)
            ? `
          <div class="article-admin-actions">
            <button onclick="app.editArticle(${article.id})" class="btn-secondary">编辑文章</button>
            <button onclick="app.deleteArticle(${article.id})" class="btn-danger">删除文章</button>
          </div>
        `
            : ""
        }
      </article>
      
      <section class="comments-section">
        <h3>评论 (${this.countAllComments(comments)})</h3>
        
        ${
          this.currentUser
            ? `
          <form id="comment-form" class="comment-form" onsubmit="app.submitComment(event, ${article.id})">
            <div class="form-group">
              <textarea name="content" placeholder="写下您的评论..." required rows="3"></textarea>
            </div>
            <button type="submit" class="btn-primary">发表评论</button>
          </form>
        `
            : `
          <div class="login-prompt">
            <p>请 <a href="#" onclick="app.showLoginForm()">登录</a> 后发表评论</p>
          </div>
        `
        }
        
        <div class="comments-list">
          ${this.renderComments(comments, article.id)}
        </div>
      </section>
    `;

    // 滚动到页面顶部
    window.scrollTo(0, 0);
  }

  // 渲染评论列表
  renderComments(comments, articleId) {
    if (comments.length === 0) {
      return '<p class="no-comments">还没有评论，快来发表第一条评论吧！</p>';
    }

    return comments
      .map(
        (comment) => `
      <div class="comment" data-id="${comment.id}">
        <div class="comment-header">
          <img src="${
            comment.user.avatar || "/default-avatar.png"
          }" alt="用户头像" class="user-avatar">
          <div class="comment-meta">
            <span class="username">${comment.user.username}</span>
            <span class="time">${new Date(
              comment.created_at
            ).toLocaleString()}</span>
          </div>
          <div class="comment-actions">
            ${
              this.currentUser
                ? `
              <button onclick="app.showReplyForm(${comment.id})" class="btn-reply">回复</button>
            `
                : ""
            }
            ${
              this.isCurrentUserCommentAuthor(comment)
                ? `
              <button onclick="app.deleteComment(${articleId}, ${comment.id})" class="btn-delete">删除</button>
            `
                : ""
            }
          </div>
        </div>
        
        <div class="comment-content">${comment.content.replace(
          /\n/g,
          "<br>"
        )}</div>
        
        <div id="reply-form-${
          comment.id
        }" class="reply-form" style="display: none;">
          <form onsubmit="app.submitReply(event, ${articleId}, ${comment.id})">
            <div class="form-group">
              <textarea name="content" placeholder="回复 ${
                comment.user.username
              }..." required rows="2"></textarea>
            </div>
            <div class="form-actions">
              <button type="submit" class="btn-primary">回复</button>
              <button type="button" onclick="app.hideReplyForm(${
                comment.id
              })" class="btn-secondary">取消</button>
            </div>
          </form>
        </div>
        
        <div class="replies">
          ${comment.replies
            .map(
              (reply) => `
            <div class="reply" data-id="${reply.id}">
              <div class="comment-header">
                <img src="${
                  reply.user.avatar || "/default-avatar.png"
                }" alt="用户头像" class="user-avatar">
                <div class="comment-meta">
                  <span class="username">${reply.user.username}</span>
                  <span class="time">${new Date(
                    reply.created_at
                  ).toLocaleString()}</span>
                </div>
                ${
                  this.isCurrentUserCommentAuthor(reply)
                    ? `
                  <div class="comment-actions">
                    <button onclick="app.deleteComment(${articleId}, ${reply.id})" class="btn-delete">删除</button>
                  </div>
                `
                    : ""
                }
              </div>
              <div class="comment-content">${reply.content.replace(
                /\n/g,
                "<br>"
              )}</div>
            </div>
          `
            )
            .join("")}
        </div>
      </div>
    `
      )
      .join("");
  }

  // 统计评论总数
  countAllComments(comments) {
    return comments.reduce((total, comment) => {
      return total + 1 + comment.replies.length;
    }, 0);
  }

  // 提交评论
  async submitComment(event, articleId) {
    event.preventDefault();
    const form = event.target;
    const content = form.content.value.trim();

    if (!content) return;

    try {
      this.showLoading();
      await this.commentManager.createComment(articleId, { content });
      form.reset();
      await this.viewArticle(articleId); // 重新加载文章
    } catch (error) {
      alert("评论发表失败: " + error.message);
    } finally {
      this.hideLoading();
    }
  }

  // 提交回复
  async submitReply(event, articleId, parentId) {
    event.preventDefault();
    const form = event.target;
    const content = form.content.value.trim();

    if (!content) return;

    try {
      this.showLoading();
      await this.commentManager.createComment(articleId, {
        content,
        parent: parentId,
      });
      form.reset();
      this.hideReplyForm(parentId);
      await this.viewArticle(articleId); // 重新加载文章
    } catch (error) {
      alert("回复发表失败: " + error.message);
    } finally {
      this.hideLoading();
    }
  }

  // 显示回复表单
  showReplyForm(commentId) {
    // 隐藏其他回复表单
    document.querySelectorAll(".reply-form").forEach((form) => {
      form.style.display = "none";
    });

    // 显示目标回复表单
    const replyForm = document.getElementById(`reply-form-${commentId}`);
    if (replyForm) {
      replyForm.style.display = "block";
      replyForm.querySelector("textarea").focus();
    }
  }

  // 隐藏回复表单
  hideReplyForm(commentId) {
    const replyForm = document.getElementById(`reply-form-${commentId}`);
    if (replyForm) {
      replyForm.style.display = "none";
      replyForm.querySelector("form").reset();
    }
  }

  // 删除评论
  async deleteComment(articleId, commentId) {
    if (!confirm("确定要删除这条评论吗？此操作无法撤销。")) return;

    try {
      this.showLoading();
      await this.commentManager.deleteComment(articleId, commentId);
      await this.viewArticle(articleId); // 重新加载文章
    } catch (error) {
      alert("删除失败: " + error.message);
    } finally {
      this.hideLoading();
    }
  }

  // 创建文章
  async createArticle(articleData) {
    try {
      this.showLoading();
      const newArticle = await this.articleManager.createArticle(articleData);
      await this.loadArticles(); // 重新加载文章列表
      this.viewArticle(newArticle.id); // 查看新创建的文章
    } catch (error) {
      alert("文章创建失败: " + error.message);
    } finally {
      this.hideLoading();
    }
  }

  // 删除文章
  async deleteArticle(articleId) {
    if (!confirm("确定要删除这篇文章吗？此操作无法撤销。")) return;

    try {
      this.showLoading();
      await this.articleManager.deleteArticle(articleId);
      await this.loadArticles(); // 重新加载文章列表
      this.showArticleList(); // 返回文章列表页面
    } catch (error) {
      alert("删除失败: " + error.message);
    } finally {
      this.hideLoading();
    }
  }

  // 检查是否是当前用户的文章
  isCurrentUserAuthor(article) {
    return this.currentUser && this.currentUser.id === article.author.id;
  }

  // 检查是否是当前用户的评论
  isCurrentUserCommentAuthor(comment) {
    return this.currentUser && this.currentUser.id === comment.user.id;
  }

  // 显示加载状态
  showLoading() {
    const loader = document.getElementById("loading");
    if (loader) loader.style.display = "block";
  }

  // 隐藏加载状态
  hideLoading() {
    const loader = document.getElementById("loading");
    if (loader) loader.style.display = "none";
  }

  // 显示登录表单
  showLoginForm() {
    // 实现登录表单显示逻辑
    console.log("显示登录表单");
  }

  // 显示文章列表
  showArticleList() {
    // 实现文章列表显示逻辑
    console.log("显示文章列表");
  }
}

// 初始化应用
const app = new BlogApp();
```

### 错误处理最佳实践

#### 7. 统一错误处理

```javascript
class ErrorHandler {
  static handle(error, context = "") {
    console.error(`${context} 错误:`, error);

    // 根据错误类型进行不同处理
    if (error.message.includes("401")) {
      this.handleAuthError();
    } else if (error.message.includes("403")) {
      this.handlePermissionError();
    } else if (error.message.includes("404")) {
      this.handleNotFoundError();
    } else if (error.message.includes("400")) {
      this.handleValidationError(error);
    } else {
      this.handleGenericError(error);
    }
  }

  static handleAuthError() {
    alert("登录已过期，请重新登录");
    window.location.href = "/login";
  }

  static handlePermissionError() {
    alert("您没有权限执行此操作");
  }

  static handleNotFoundError() {
    alert("请求的资源不存在");
  }

  static handleValidationError(error) {
    try {
      const errorData = JSON.parse(error.message);
      const errorMessages = Object.values(errorData).flat().join("\n");
      alert("数据验证失败:\n" + errorMessages);
    } catch {
      alert("请求参数错误");
    }
  }

  static handleGenericError(error) {
    alert("操作失败: " + error.message);
  }
}

// 在API调用中使用
try {
  await articleManager.createArticle(articleData);
} catch (error) {
  ErrorHandler.handle(error, "创建文章");
}
```
