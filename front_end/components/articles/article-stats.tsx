"use client"

import { useEffect, useState } from "react"
import { Article } from "@/lib/types"
import api from "@/lib/api"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { FileText, Eye, TrendingUp, Clock } from "lucide-react"
import { Skeleton } from "@/components/ui/skeleton"

interface ArticleStatsProps {
  userId?: number
}

interface Stats {
  totalArticles: number
  publishedArticles: number
  draftArticles: number
  totalViews: number
  averageViews: number
  mostPopularArticle: Article | null
}

export default function ArticleStats({ userId }: ArticleStatsProps) {
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchStats() {
      if (!userId) return
      
      try {
        setLoading(true)
        setError(null)
        
        // 获取用户的所有文章
        const articles = await api.getMyArticles(userId)
        
        if (articles && articles.length > 0) {
          const publishedArticles = articles.filter(a => a.status === "published")
          const draftArticles = articles.filter(a => a.status === "draft")
          const totalViews = publishedArticles.reduce((sum, article) => sum + (article.view_count || 0), 0)
          const averageViews = publishedArticles.length > 0 ? Math.round(totalViews / publishedArticles.length) : 0
          
          // 找出最受欢迎的文章
          const mostPopularArticle = publishedArticles.length > 0
            ? publishedArticles.reduce((prev, current) => 
                (current.view_count || 0) > (prev.view_count || 0) ? current : prev
              )
            : null
          
          setStats({
            totalArticles: articles.length,
            publishedArticles: publishedArticles.length,
            draftArticles: draftArticles.length,
            totalViews,
            averageViews,
            mostPopularArticle
          })
        } else {
          setStats({
            totalArticles: 0,
            publishedArticles: 0,
            draftArticles: 0,
            totalViews: 0,
            averageViews: 0,
            mostPopularArticle: null
          })
        }
      } catch (err) {
        console.error("Failed to fetch article stats:", err)
        setError("加载统计数据失败")
      } finally {
        setLoading(false)
      }
    }

    fetchStats()
  }, [userId])

  if (!userId) return null

  if (loading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-4 w-4" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-16 mb-1" />
              <Skeleton className="h-3 w-24" />
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  if (error || !stats) {
    return null
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {/* 总文章数 */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">总文章数</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalArticles}</div>
            <p className="text-xs text-muted-foreground">
              {stats.publishedArticles} 已发布, {stats.draftArticles} 草稿
            </p>
          </CardContent>
        </Card>

        {/* 总阅读量 */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">总阅读量</CardTitle>
            <Eye className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalViews.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              来自 {stats.publishedArticles} 篇文章
            </p>
          </CardContent>
        </Card>

        {/* 平均阅读量 */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">平均阅读量</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.averageViews}</div>
            <p className="text-xs text-muted-foreground">
              每篇文章平均
            </p>
          </CardContent>
        </Card>

        {/* 最受欢迎的文章 */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">最受欢迎</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {stats.mostPopularArticle ? (
              <>
                <div className="text-sm font-medium line-clamp-1">
                  {stats.mostPopularArticle.title}
                </div>
                <p className="text-xs text-muted-foreground">
                  {stats.mostPopularArticle.view_count} 次阅读
                </p>
              </>
            ) : (
              <p className="text-sm text-muted-foreground">暂无数据</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* 最受欢迎文章详情 */}
      {stats.mostPopularArticle && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">最受欢迎的文章</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <h3 className="font-medium">{stats.mostPopularArticle.title}</h3>
              <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                <div className="flex items-center">
                  <Eye className="h-4 w-4 mr-1" />
                  <span>{stats.mostPopularArticle.view_count} 次阅读</span>
                </div>
                <span>•</span>
                <span>
                  发布于 {new Date(stats.mostPopularArticle.created_at).toLocaleDateString("zh-CN")}
                </span>
              </div>
              <p className="text-sm text-muted-foreground line-clamp-2">
                {stats.mostPopularArticle.content.substring(0, 100)}...
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}