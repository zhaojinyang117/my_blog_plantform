// 用户类型定义
export interface User {
  id: number
  username: string
  email: string
  bio?: string
  avatar?: string
  is_active: boolean
  is_staff: boolean
  date_joined?: string
}

// 文章类型定义
export interface Article {
  id: number
  title: string
  content: string
  author: User
  created_at: string
  updated_at: string
  status: "draft" | "published" // 后端返回的是英文状态
  view_count: number // 文章访问次数
}

// 评论类型定义
export interface Comment {
  id: number
  article: number
  user: User
  content: string
  created_at: string
  parent?: Comment | null
  replies?: Comment[]
}

// 表单数据类型
export interface LoginCredentials {
  username: string // 前端表单字段名，实际为邮箱地址
  password: string
}

export interface RegisterData {
  username: string
  email: string
  password: string
}

export interface ArticleFormData {
  title: string
  content: string
  status: "draft" | "published" // 与后端保持一致
}

export interface CommentFormData {
  content: string
  parent?: string | null
}

// 认证上下文类型
export interface AuthContextType {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (credentials: LoginCredentials) => Promise<void>
  register: (userData: RegisterData) => Promise<void>
  logout: () => void
  checkAuth: () => Promise<void>
  getAuthHeaders: () => { Authorization?: string }
}

// API 响应类型
export interface ApiResponse<T = any> {
  data?: T
  error?: string
  message?: string
}

// 分页响应类型
export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

// 邮箱验证响应类型
export interface EmailVerificationResponse {
  status: 'success' | 'already_verified' | 'error'
  message: string
}

// 头像上传响应类型
export interface AvatarUploadResponse {
  message: string
  avatar_url: string
}

// 搜索相关类型
export interface SearchParams {
  q: string // 搜索关键词
  type?: 'all' | 'title' | 'content' | 'author' // 搜索类型
  ordering?: '-created_at' | 'created_at' | '-view_count' | 'view_count' | 'title' | '-title' // 排序方式
  page?: number // 页码
}

export interface SearchInfo {
  query: string
  search_type: string
  ordering: string
  total_results: number
}

export interface SearchResponse {
  count: number
  next: string | null
  previous: string | null
  results: Article[]
  search_info: SearchInfo
}

// 搜索建议类型
export interface SearchSuggestion {
  text: string
  type: 'recent' | 'popular' | 'suggestion'
}
