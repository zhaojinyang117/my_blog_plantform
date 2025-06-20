"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { Article } from "@/lib/types"
import api from "@/lib/api"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { TrendingUp, Eye } from "lucide-react"
import { Skeleton } from "@/components/ui/skeleton"

interface PopularArticlesProps {
  limit?: number
}

export default function PopularArticles({ limit = 5 }: PopularArticlesProps) {
  const [articles, setArticles] = useState<Article[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchPopularArticles() {
      try {
        setLoading(true)
        setError(null)
        
        // 获取文章列表
        const articles = await api.getArticles()
        
        if (articles && articles.length > 0) {
          // 过滤已发布的文章并按访问量排序
          const publishedArticles = articles
            .filter((article: Article) => article.status === "published")
            .sort((a: Article, b: Article) => (b.view_count || 0) - (a.view_count || 0))
            .slice(0, limit)
          
          setArticles(publishedArticles)
        }
      } catch (err) {
        console.error("Failed to fetch popular articles:", err)
        setError("加载热门文章失败")
      } finally {
        setLoading(false)
      }
    }

    fetchPopularArticles()
  }, [limit])

  if (loading) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <TrendingUp className="h-5 w-5" />
            <span>热门文章</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[...Array(limit)].map((_, i) => (
              <div key={i} className="space-y-2">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-3 w-2/3" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error || articles.length === 0) {
    return null
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <TrendingUp className="h-5 w-5 text-orange-500" />
          <span>热门文章</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ol className="space-y-4">
          {articles.map((article, index) => (
            <li key={article.id} className="flex items-start space-x-3">
              <Badge 
                variant={index < 3 ? "default" : "secondary"} 
                className={`mt-1 min-w-[24px] h-6 px-2 ${
                  index === 0 ? "bg-red-500 hover:bg-red-600" : 
                  index === 1 ? "bg-orange-500 hover:bg-orange-600" : 
                  index === 2 ? "bg-yellow-500 hover:bg-yellow-600" : ""
                }`}
              >
                {index + 1}
              </Badge>
              <div className="flex-1 min-w-0">
                <Link 
                  href={`/articles/${article.id}`}
                  className="text-sm font-medium hover:text-primary transition-colors line-clamp-2"
                >
                  {article.title}
                </Link>
                <div className="flex items-center space-x-3 mt-1 text-xs text-muted-foreground">
                  <span>{article.author.username}</span>
                  <span>•</span>
                  <div className="flex items-center">
                    <Eye className="h-3 w-3 mr-1" />
                    <span>{article.view_count || 0}</span>
                  </div>
                </div>
              </div>
            </li>
          ))}
        </ol>
      </CardContent>
    </Card>
  )
}