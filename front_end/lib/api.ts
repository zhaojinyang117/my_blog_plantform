import type {
  User,
  Article,
  Comment,
  LoginCredentials,
  RegisterData,
  ArticleFormData,
  CommentFormData,
  EmailVerificationResponse,
  AvatarUploadResponse,
  SearchParams,
  SearchResponse
} from './types'

const API_BASE_URL = '/api'

class ApiService {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`

    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    }

    // 添加认证头（除非已经在options.headers中指定）
    const token = typeof window !== 'undefined' ? localStorage.getItem('authToken') : null
    if (token && !options.headers?.hasOwnProperty('Authorization')) {
      config.headers = {
        ...config.headers,
        'Authorization': `Bearer ${token}`,
      }
    }

    console.log(`API Request: ${config.method || 'GET'} ${url}`)

    const response = await fetch(url, config)

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      console.error(`API Error: ${response.status}`, errorData)

      // 如果是401错误且不是token相关的请求，尝试刷新token
      if (response.status === 401 && !endpoint.includes('token') && typeof window !== 'undefined') {
        const refreshToken = localStorage.getItem('refreshToken')
        if (refreshToken) {
          try {
            const { access } = await this.refreshToken(refreshToken)
            localStorage.setItem('authToken', access)
            // 重试原请求
            const retryConfig = {
              ...config,
              headers: {
                ...config.headers,
                'Authorization': `Bearer ${access}`,
              },
            }
            const retryResponse = await fetch(url, retryConfig)
            if (retryResponse.ok) {
              return retryResponse.json()
            }
          } catch (refreshError) {
            console.error('Token refresh failed:', refreshError)
            // 清除无效的tokens
            localStorage.removeItem('authToken')
            localStorage.removeItem('refreshToken')
          }
        }
      }

      throw new Error(errorData.error || errorData.detail || `HTTP error! status: ${response.status}`)
    }

    return response.json()
  }

  // 用户认证相关
  async login(credentials: LoginCredentials): Promise<{ access: string; refresh: string; user: User }> {
    try {
      // 1. 获取JWT token
      console.log('Attempting login with:', { email: credentials.username })
      const tokenResponse = await this.request('/users/token/', {
        method: 'POST',
        body: JSON.stringify({
          email: credentials.username, // 后端使用email作为用户名
          password: credentials.password,
        }),
      })
      console.log('Token response received:', { hasAccess: !!tokenResponse.access })

      // 2. 使用token获取用户信息
      const userResponse = await this.request('/users/me/', {
        headers: {
          'Authorization': `Bearer ${tokenResponse.access}`,
        },
      })
      console.log('User response received:', { username: userResponse.username })

      return {
        access: tokenResponse.access,
        refresh: tokenResponse.refresh,
        user: userResponse,
      }
    } catch (error) {
      console.error('Login error:', error)
      throw error
    }
  }

  async register(userData: RegisterData): Promise<{ message: string; user_id: number; email: string }> {
    // 后端需要password2字段来确认密码
    const requestData = {
      ...userData,
      password2: userData.password
    }

    return this.request('/users/register/', {
      method: 'POST',
      body: JSON.stringify(requestData),
    })
  }

  async getCurrentUser(token?: string): Promise<User> {
    const headers: Record<string, string> = {}
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    
    return this.request('/users/me/', {
      headers,
    })
  }

  async updateUser(userData: Partial<User>): Promise<User> {
    return this.request('/users/me/update/', {
      method: 'PATCH',
      body: JSON.stringify(userData),
    })
  }

  async uploadAvatar(file: File): Promise<AvatarUploadResponse> {
    const formData = new FormData()
    formData.append('avatar', file)

    return this.request('/users/me/avatar/', {
      method: 'PATCH',
      headers: {}, // 让浏览器自动设置Content-Type
      body: formData,
    })
  }

  async verifyEmail(token: string): Promise<EmailVerificationResponse> {
    return this.request(`/users/verify-email?token=${token}`)
  }

  async refreshToken(refreshToken: string): Promise<{ access: string }> {
    return this.request('/users/token/refresh/', {
      method: 'POST',
      body: JSON.stringify({
        refresh: refreshToken,
      }),
    })
  }

  // 文章相关
  async getArticles(): Promise<Article[]> {
    const response = await this.request<any>('/articles/')

    // 处理分页响应格式
    if (response && typeof response === 'object') {
      // 如果是分页响应，返回results数组
      if (response.results && Array.isArray(response.results)) {
        return response.results
      }
      // 如果直接是数组，返回数组
      if (Array.isArray(response)) {
        return response
      }
    }

    // 如果都不是，返回空数组
    return []
  }

  async getMyArticles(userId?: number): Promise<Article[]> {
    // 根据后端API文档，认证用户调用 /articles/ 会返回自己的所有文章（包括草稿）和其他人的已发布文章
    // 这里我们直接调用 getArticles，然后在前端过滤出当前用户的文章
    const allArticles = await this.getArticles()

    // 如果提供了userId，过滤出该用户的文章；否则返回所有文章
    if (userId) {
      return allArticles.filter(article => article.author.id === userId)
    }

    return allArticles
  }

  async getArticle(id: string): Promise<Article> {
    return this.request(`/articles/${id}/`)
  }

  async getArticleWithSignal(id: string, signal: AbortSignal): Promise<Article> {
    return this.request(`/articles/${id}/`, { signal })
  }

  async trackArticleView(id: string): Promise<{ view_count: number; message: string }> {
    try {
      return await this.request(`/articles/${id}/track-view/`, {
        method: 'POST',
      })
    } catch (error) {
      console.error('Failed to track article view:', error)
      // 不抛出错误，避免影响文章显示
      return { view_count: 0, message: 'Failed to track view' }
    }
  }

  async createArticle(articleData: ArticleFormData): Promise<Article> {
    return this.request('/articles/', {
      method: 'POST',
      body: JSON.stringify(articleData),
    })
  }

  async updateArticle(id: string, articleData: Partial<ArticleFormData>): Promise<Article> {
    return this.request(`/articles/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(articleData),
    })
  }

  async deleteArticle(id: string): Promise<void> {
    return this.request(`/articles/${id}/`, {
      method: 'DELETE',
    })
  }

  // 搜索相关
  async searchArticles(params: SearchParams): Promise<SearchResponse> {
    const searchParams = new URLSearchParams()

    // 添加搜索参数
    searchParams.append('q', params.q)
    if (params.type) searchParams.append('type', params.type)
    if (params.ordering) searchParams.append('ordering', params.ordering)
    if (params.page) searchParams.append('page', params.page.toString())

    return this.request(`/articles/search/?${searchParams.toString()}`)
  }

  // 评论相关
  async getComments(articleId: string): Promise<Comment[]> {
    return this.request(`/articles/${articleId}/comments/`)
  }

  async createComment(articleId: string, commentData: CommentFormData): Promise<Comment> {
    return this.request(`/articles/${articleId}/comments/`, {
      method: 'POST',
      body: JSON.stringify(commentData),
    })
  }

  async deleteComment(articleId: string, commentId: number): Promise<void> {
    return this.request(`/articles/${articleId}/comments/${commentId}/`, {
      method: 'DELETE',
    })
  }
}

const api = new ApiService()
export default api
