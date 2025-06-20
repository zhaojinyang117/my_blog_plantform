"use client"

import { useEffect, useState } from "react"
import { Article, User } from "@/lib/types"
import api from "@/lib/api"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { FileText, Eye, Users, TrendingUp, BarChart, Activity } from "lucide-react"
import { Skeleton } from "@/components/ui/skeleton"

interface SiteStats {
  totalArticles: number
  publishedArticles: number
  totalViews: number
  totalAuthors: number
  averageViewsPerArticle: number
  topArticles: Article[]
  articlesByMonth: { month: string; count: number }[]
}

export default function SiteStats() {
  const [stats, setStats] = useState<SiteStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchStats() {
      try {
        setLoading(true)
        setError(null)
        
        // 获取所有文章
        const articles = await api.getArticles()
        
        if (articles && articles.length > 0) {
          // 过滤已发布的文章
          const publishedArticles = articles.filter(a => a.status === "published")
          
          // 计算总阅读量
          const totalViews = publishedArticles.reduce((sum, article) => sum + (article.view_count || 0), 0)
          
          // 计算平均阅读量
          const averageViewsPerArticle = publishedArticles.length > 0 
            ? Math.round(totalViews / publishedArticles.length) 
            : 0
          
          // 获取前5篇最受欢迎的文章
          const topArticles = [...publishedArticles]
            .sort((a, b) => (b.view_count || 0) - (a.view_count || 0))
            .slice(0, 5)
          
          // 计算不同作者数量
          const uniqueAuthors = new Set(articles.map(a => a.author.id))
          const totalAuthors = uniqueAuthors.size
          
          // 按月统计文章数量（最近6个月）
          const articlesByMonth = calculateArticlesByMonth(publishedArticles)
          
          setStats({
            totalArticles: articles.length,
            publishedArticles: publishedArticles.length,
            totalViews,
            totalAuthors,
            averageViewsPerArticle,
            topArticles,
            articlesByMonth
          })
        } else {
          setStats({
            totalArticles: 0,
            publishedArticles: 0,
            totalViews: 0,
            totalAuthors: 0,
            averageViewsPerArticle: 0,
            topArticles: [],
            articlesByMonth: []
          })
        }
      } catch (err) {
        console.error("Failed to fetch site stats:", err)
        setError("加载统计数据失败")
      } finally {
        setLoading(false)
      }
    }

    fetchStats()
  }, [])

  function calculateArticlesByMonth(articles: Article[]) {
    const months = ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '十二月']
    const now = new Date()
    const sixMonthsAgo = new Date(now.getFullYear(), now.getMonth() - 5, 1)
    
    const monthCounts: { [key: string]: number } = {}
    
    // 初始化最近6个月
    for (let i = 0; i < 6; i++) {
      const date = new Date(sixMonthsAgo.getFullYear(), sixMonthsAgo.getMonth() + i, 1)
      const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
      monthCounts[monthKey] = 0
    }
    
    // 统计每月文章数
    articles.forEach(article => {
      const date = new Date(article.created_at)
      const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
      if (monthCounts.hasOwnProperty(monthKey)) {
        monthCounts[monthKey]++
      }
    })
    
    // 转换为数组格式
    return Object.entries(monthCounts).map(([key, count]) => {
      const [year, month] = key.split('-')
      return {
        month: `${months[parseInt(month) - 1]}`,
        count
      }
    })
  }

  if (loading) {
    return (
      <div className="space-y-6">
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
      </div>
    )
  }

  if (error || !stats) {
    return (
      <div className="text-center text-red-500">
        {error || "加载统计数据失败"}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* 概览卡片 */}
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
              {stats.publishedArticles} 已发布
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
              平均每篇 {stats.averageViewsPerArticle} 次
            </p>
          </CardContent>
        </Card>

        {/* 作者数量 */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">活跃作者</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalAuthors}</div>
            <p className="text-xs text-muted-foreground">
              位内容创作者
            </p>
          </CardContent>
        </Card>

        {/* 平台活跃度 */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">平台活跃度</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.publishedArticles > 0 ? Math.round((stats.publishedArticles / stats.totalArticles) * 100) : 0}%
            </div>
            <p className="text-xs text-muted-foreground">
              文章发布率
            </p>
          </CardContent>
        </Card>
      </div>

      {/* 热门文章排行榜 */}
      {stats.topArticles.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              热门文章排行榜
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {stats.topArticles.map((article, index) => (
                <div key={article.id} className="flex items-start space-x-3">
                  <div 
                    className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                      index === 0 ? 'bg-yellow-500 text-white' :
                      index === 1 ? 'bg-gray-400 text-white' :
                      index === 2 ? 'bg-orange-600 text-white' :
                      'bg-gray-200 text-gray-600'
                    }`}
                  >
                    {index + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h4 className="text-sm font-medium truncate">{article.title}</h4>
                    <div className="flex items-center gap-3 text-xs text-muted-foreground mt-1">
                      <span>{article.author.username || article.author.email}</span>
                      <span>•</span>
                      <span className="flex items-center gap-1">
                        <Eye className="h-3 w-3" />
                        {article.view_count} 次阅读
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 文章发布趋势 */}
      {stats.articlesByMonth.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart className="h-5 w-5" />
              最近6个月发布趋势
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {stats.articlesByMonth.map((item, index) => (
                <div key={index} className="flex items-center gap-3">
                  <div className="w-16 text-sm text-muted-foreground">{item.month}</div>
                  <div className="flex-1">
                    <div className="h-4 bg-gray-100 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-blue-500 transition-all duration-500"
                        style={{ 
                          width: `${item.count > 0 ? Math.max((item.count / Math.max(...stats.articlesByMonth.map(m => m.count))) * 100, 10) : 0}%` 
                        }}
                      />
                    </div>
                  </div>
                  <div className="w-12 text-sm text-right font-medium">{item.count}</div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}