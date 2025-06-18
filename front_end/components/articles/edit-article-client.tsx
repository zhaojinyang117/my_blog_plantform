"use client"

import { useEffect, useState } from "react"
import { useAuth } from "@/hooks/use-auth"
import { useRouter } from "next/navigation"
import api from "@/lib/api"
import { Article } from "@/types/article"
import ArticleForm from "./article-form"
import ProtectedRouteClient from "@/components/auth/protected-route-client"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Lock, AlertCircle } from "lucide-react"
import { Button } from "@/components/ui/button"

interface EditArticleClientProps {
  articleId: string
}

export default function EditArticleClient({ articleId }: EditArticleClientProps) {
  const { user, isAuthenticated } = useAuth()
  const router = useRouter()
  const [article, setArticle] = useState<Article | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchArticle() {
      try {
        setLoading(true)
        setError(null)
        
        console.log("Fetching article for edit:", articleId, "User authenticated:", isAuthenticated)
        
        const fetchedArticle = await api.getArticle(articleId)
        
        if (!fetchedArticle) {
          setError("文章未找到")
          return
        }
        
        // 检查用户是否有权限编辑此文章
        if (!user || fetchedArticle.author.id !== user.id) {
          setError("您没有权限编辑此文章")
          return
        }
        
        setArticle(fetchedArticle)
      } catch (err: any) {
        console.error("Failed to fetch article for editing:", err)
        
        if (err.message?.includes('401') || err.message?.includes('认证')) {
          setError("请登录后编辑文章")
        } else if (err.message?.includes('403') || err.message?.includes('权限')) {
          setError("您没有权限编辑此文章")
        } else if (err.message?.includes('404') || err.message?.includes('not found')) {
          setError("文章未找到")
        } else {
          setError("加载文章时出现错误")
        }
      } finally {
        setLoading(false)
      }
    }

    // 只有在用户认证状态确定后才获取文章
    if (isAuthenticated !== undefined) {
      fetchArticle()
    }
  }, [articleId, user, isAuthenticated])

  if (loading) {
    return (
      <ProtectedRouteClient>
        <div className="max-w-4xl mx-auto py-8">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded mb-6"></div>
            <div className="space-y-4">
              <div className="h-4 bg-gray-200 rounded"></div>
              <div className="h-4 bg-gray-200 rounded"></div>
              <div className="h-32 bg-gray-200 rounded"></div>
            </div>
          </div>
        </div>
      </ProtectedRouteClient>
    )
  }

  if (error) {
    return (
      <ProtectedRouteClient>
        <div className="max-w-4xl mx-auto py-8">
          <Alert className="mb-6">
            {error.includes("权限") ? (
              <Lock className="h-4 w-4" />
            ) : (
              <AlertCircle className="h-4 w-4" />
            )}
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
      </ProtectedRouteClient>
    )
  }

  if (!article) {
    return (
      <ProtectedRouteClient>
        <div className="max-w-4xl mx-auto py-8 text-center">
          <p className="text-muted-foreground">文章未找到</p>
          <Button 
            variant="outline" 
            className="mt-4"
            onClick={() => router.back()}
          >
            返回上一页
          </Button>
        </div>
      </ProtectedRouteClient>
    )
  }

  return (
    <ProtectedRouteClient>
      <div className="max-w-4xl mx-auto py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-center">编辑文章</h1>
          {article.status === "draft" && (
            <Alert className="mt-4">
              <Lock className="h-4 w-4" />
              <AlertDescription>
                您正在编辑一篇草稿文章
              </AlertDescription>
            </Alert>
          )}
        </div>
        
        <ArticleForm article={article} formType="edit" />
      </div>
    </ProtectedRouteClient>
  )
}
