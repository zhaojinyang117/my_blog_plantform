"use client"

import { useEffect, useState, useRef } from "react"
import { useAuth } from "@/hooks/use-auth"
import api from "@/lib/api"
import { Article } from "@/lib/types"
import { getCachedArticle, setCachedArticle } from "@/lib/article-cache"
import ReactMarkdown from "react-markdown"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { CalendarDays, Lock, Eye } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { useRouter } from "next/navigation"
import ArticleActions from "./article-actions"
import CommentList from "@/components/comments/comment-list"

interface ArticleDetailClientProps {
  articleId: string
}

export default function ArticleDetailClient({ articleId }: ArticleDetailClientProps) {
  const { user, isAuthenticated } = useAuth()
  const router = useRouter()
  const [article, setArticle] = useState<Article | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)
  const fetchInProgressRef = useRef<boolean>(false)

  useEffect(() => {
    let isMounted = true

    async function fetchArticle() {
      // 如果已经有请求在进行，直接返回
      if (fetchInProgressRef.current) {
        console.log("Request already in progress, skipping duplicate request")
        return
      }

      // 取消之前的请求
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }

      // 创建新的 AbortController
      abortControllerRef.current = new AbortController()
      const signal = abortControllerRef.current.signal

      try {
        setError(null)
        fetchInProgressRef.current = true

        // 先检查缓存
        const cachedArticle = getCachedArticle(articleId)
        if (cachedArticle) {
          console.log("Using cached article:", articleId)
          setArticle(cachedArticle)
          setLoading(false)
          fetchInProgressRef.current = false
          return
        }

        setLoading(true)
        console.log("Fetching article:", articleId, "at", new Date().toISOString())

        const fetchedArticle = await api.getArticleWithSignal(articleId, signal)

        if (!isMounted || signal.aborted) return

        if (!fetchedArticle) {
          setError("文章未找到")
          return
        }

        // 检查是否是草稿文章且用户是否有权限访问
        if (fetchedArticle.status === "draft" && (!user || fetchedArticle.author.id !== user.id)) {
          setError("您没有权限访问此草稿文章")
          return
        }

        // 缓存文章数据
        setCachedArticle(articleId, fetchedArticle)
        setArticle(fetchedArticle)
      } catch (err: any) {
        if (!isMounted || signal.aborted) return
        
        // 忽略中止错误
        if (err.name === 'AbortError') {
          console.log("Request was aborted")
          return
        }

        console.error("Failed to fetch article:", err)

        if (err.message?.includes('401') || err.message?.includes('认证')) {
          setError("请登录后访问此文章")
        } else if (err.message?.includes('403') || err.message?.includes('权限')) {
          setError("您没有权限访问此文章")
        } else if (err.message?.includes('404') || err.message?.includes('not found')) {
          setError("文章未找到")
        } else {
          setError("加载文章时出现错误")
        }
      } finally {
        if (isMounted && !signal.aborted) {
          setLoading(false)
          fetchInProgressRef.current = false
        }
      }
    }

    fetchArticle()

    return () => {
      isMounted = false
      // 组件卸载时取消请求（只在请求进行中时取消）
      if (abortControllerRef.current && fetchInProgressRef.current) {
        abortControllerRef.current.abort()
        fetchInProgressRef.current = false
      }
    }
  }, [articleId, user])

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto py-8">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded mb-4"></div>
          <div className="h-4 bg-gray-200 rounded mb-2"></div>
          <div className="h-4 bg-gray-200 rounded mb-8"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-3xl mx-auto py-8">
        <Alert className="mb-6">
          <Lock className="h-4 w-4" />
          <AlertDescription className="flex items-center justify-between">
            <span>{error}</span>
            {error.includes("登录") && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => router.push("/login")}
              >
                去登录
              </Button>
            )}
          </AlertDescription>
        </Alert>

        <div className="text-center">
          <Button
            variant="outline"
            onClick={() => router.back()}
          >
            返回上一页
          </Button>
        </div>
      </div>
    )
  }

  if (!article) {
    return (
      <div className="max-w-3xl mx-auto py-8 text-center">
        <p className="text-muted-foreground">文章未找到</p>
        <Button
          variant="outline"
          className="mt-4"
          onClick={() => router.back()}
        >
          返回上一页
        </Button>
      </div>
    )
  }

  return (
    <article className="max-w-3xl mx-auto py-8 prose dark:prose-invert lg:prose-xl">
      {/* 草稿标识 */}
      {article.status === "draft" && (
        <Alert className="mb-6">
          <Lock className="h-4 w-4" />
          <AlertDescription>
            这是一篇草稿文章，只有作者可以查看
          </AlertDescription>
        </Alert>
      )}

      <div className="mb-8 text-center">
        <h1 className="text-4xl font-extrabold tracking-tight lg:text-5xl">{article.title}</h1>
        <div className="mt-4 flex items-center justify-center space-x-4 text-muted-foreground">
          <div className="flex items-center">
            <Avatar className="h-8 w-8 mr-2">
              <AvatarImage
                src={article.author.avatar || "/placeholder-user.jpg"}
                alt={article.author.username}
              />
              <AvatarFallback>{article.author.username.charAt(0).toUpperCase()}</AvatarFallback>
            </Avatar>
            <span>{article.author.username}</span>
          </div>
          <span>•</span>
          <div className="flex items-center">
            <CalendarDays className="h-5 w-5 mr-1.5" />
            <time dateTime={article.created_at}>
              {new Date(article.created_at).toLocaleDateString("zh-CN", {
                year: "numeric",
                month: "long",
                day: "numeric",
              })}
            </time>
          </div>
          <span>•</span>
          <div className="flex items-center">
            <Eye className="h-5 w-5 mr-1.5" />
            <span>{article.view_count || 0} 次阅读</span>
          </div>
          {article.status === "draft" && (
            <>
              <span>•</span>
              <span className="text-orange-600 font-medium">草稿</span>
            </>
          )}
        </div>
      </div>

      <ArticleActions articleId={article.id.toString()} authorId={article.author.id.toString()} />

      <ReactMarkdown
        components={{
          h1: ({ ...props }) => <h1 className="text-3xl font-bold mt-8 mb-4" {...props} />,
          h2: ({ ...props }) => <h2 className="text-2xl font-semibold mt-6 mb-3" {...props} />,
          p: ({ ...props }) => <p className="leading-relaxed mb-4" {...props} />,
          a: ({ ...props }) => <a className="text-primary hover:underline" {...props} />,
          blockquote: ({ ...props }) => (
            <blockquote className="border-l-4 border-primary pl-4 italic my-4 text-muted-foreground" {...props} />
          ),
          code: ({ className, children, ...props }: any) => {
            const inline = props.inline;
            const match = /language-(\w+)/.exec(className ?? "")
            return !inline && match ? (
              <pre className="bg-muted p-4 rounded-md overflow-x-auto my-4">
                <code className={`language-${match[1]}`} {...props}>
                  {children}
                </code>
              </pre>
            ) : (
              <code className="bg-muted px-1 py-0.5 rounded-sm font-mono text-sm" {...props}>
                {children}
              </code>
            )
          },
        }}
      >
        {article.content}
      </ReactMarkdown>

      {/* 评论区域 */}
      <div className="mt-12 border-t pt-8">
        <CommentList articleId={article.id.toString()} />
      </div>
    </article>
  )
}
