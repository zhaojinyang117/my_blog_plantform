"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { formatDistanceToNow } from "date-fns"
import { zhCN } from "date-fns/locale"
import { Eye, User, Calendar, Search } from "lucide-react"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Alert, AlertDescription } from "@/components/ui/alert"
import api from "@/lib/api"
import type { Article, SearchParams, SearchResponse } from "@/lib/types"

interface SearchResultsProps {
  initialQuery: string
  initialType?: string
  initialOrdering?: string
}

export default function SearchResults({ 
  initialQuery, 
  initialType = "all", 
  initialOrdering = "-created_at" 
}: SearchResultsProps) {
  const [results, setResults] = useState<Article[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchInfo, setSearchInfo] = useState<any>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [searchType, setSearchType] = useState(initialType)
  const [ordering, setOrdering] = useState(initialOrdering)

  const searchParams: SearchParams = {
    q: initialQuery,
    type: searchType as any,
    ordering: ordering as any,
    page: currentPage
  }

  useEffect(() => {
    if (initialQuery.trim()) {
      performSearch()
    }
  }, [initialQuery, searchType, ordering, currentPage])

  const performSearch = async () => {
    try {
      setLoading(true)
      setError(null)

      const response: SearchResponse = await api.searchArticles(searchParams)

      // 确保response和results存在
      if (response && Array.isArray(response.results)) {
        setResults(response.results)
      } else {
        setResults([])
      }

      setSearchInfo(response?.search_info || null)

      // 计算总页数
      const totalCount = response?.count || 0
      const pageSize = 10 // 假设每页10条
      setTotalPages(Math.ceil(totalCount / pageSize))

    } catch (err) {
      console.error('搜索失败:', err)
      setError(err instanceof Error ? err.message : '搜索失败，请稍后重试')
      setResults([])
      setSearchInfo(null)
    } finally {
      setLoading(false)
    }
  }

  const handleTypeChange = (newType: string) => {
    setSearchType(newType)
    setCurrentPage(1) // 重置到第一页
  }

  const handleOrderingChange = (newOrdering: string) => {
    setOrdering(newOrdering)
    setCurrentPage(1) // 重置到第一页
  }

  const highlightText = (text: string, query: string) => {
    if (!query.trim()) return text
    
    const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi')
    const parts = text.split(regex)
    
    return parts.map((part, index) => 
      regex.test(part) ? (
        <mark key={index} className="bg-yellow-200 dark:bg-yellow-800 px-1 rounded">
          {part}
        </mark>
      ) : part
    )
  }

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="h-8 bg-muted rounded w-48 animate-pulse" />
          <div className="flex gap-2">
            <div className="h-10 bg-muted rounded w-32 animate-pulse" />
            <div className="h-10 bg-muted rounded w-32 animate-pulse" />
          </div>
        </div>
        {[...Array(5)].map((_, i) => (
          <Card key={i} className="animate-pulse">
            <CardHeader>
              <div className="h-6 bg-muted rounded w-3/4" />
              <div className="h-4 bg-muted rounded w-1/2" />
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="h-4 bg-muted rounded w-full" />
                <div className="h-4 bg-muted rounded w-5/6" />
                <div className="h-4 bg-muted rounded w-4/6" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <Search className="h-4 w-4" />
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    )
  }

  return (
    <div className="space-y-6">
      {/* 搜索信息和过滤器 */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="space-y-1">
          <h2 className="text-2xl font-bold">搜索结果</h2>
          {searchInfo && (
            <p className="text-muted-foreground">
              找到 {searchInfo.total_results} 个关于 "{searchInfo.query}" 的结果
            </p>
          )}
        </div>
        
        <div className="flex gap-2">
          <Select value={searchType} onValueChange={handleTypeChange}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部</SelectItem>
              <SelectItem value="title">标题</SelectItem>
              <SelectItem value="content">内容</SelectItem>
              <SelectItem value="author">作者</SelectItem>
            </SelectContent>
          </Select>
          
          <Select value={ordering} onValueChange={handleOrderingChange}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="-created_at">最新</SelectItem>
              <SelectItem value="created_at">最早</SelectItem>
              <SelectItem value="-view_count">最热门</SelectItem>
              <SelectItem value="view_count">最冷门</SelectItem>
              <SelectItem value="title">标题A-Z</SelectItem>
              <SelectItem value="-title">标题Z-A</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* 搜索结果列表 */}
      {results.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Search className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">没有找到相关结果</h3>
            <p className="text-muted-foreground text-center">
              尝试使用不同的关键词或调整搜索条件
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {results.map((article) => (
            <Card key={article.id} className="hover:shadow-md transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="space-y-2 flex-1">
                    <Link 
                      href={`/articles/${article.id}`}
                      className="text-xl font-semibold hover:text-primary transition-colors"
                    >
                      {highlightText(article.title, initialQuery)}
                    </Link>
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <div className="flex items-center gap-1">
                        <User className="h-3 w-3" />
                        {highlightText(article.author?.username || "", initialQuery)}
                      </div>
                      <div className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        {formatDistanceToNow(new Date(article.created_at), { 
                          addSuffix: true, 
                          locale: zhCN 
                        })}
                      </div>
                      <div className="flex items-center gap-1">
                        <Eye className="h-3 w-3" />
                        {article.view_count || 0}
                      </div>
                    </div>
                  </div>
                  <Badge variant="secondary">
                    {article.status === 'published' ? '已发布' : '草稿'}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground line-clamp-3">
                  {highlightText(
                    article.content && article.content.length > 200
                      ? article.content.substring(0, 200) + "..."
                      : article.content || "",
                    initialQuery
                  )}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* 分页 */}
      {totalPages > 1 && (
        <div className="flex justify-center gap-2">
          <Button
            variant="outline"
            disabled={currentPage === 1}
            onClick={() => setCurrentPage(currentPage - 1)}
          >
            上一页
          </Button>
          <span className="flex items-center px-4">
            第 {currentPage} 页，共 {totalPages} 页
          </span>
          <Button
            variant="outline"
            disabled={currentPage === totalPages}
            onClick={() => setCurrentPage(currentPage + 1)}
          >
            下一页
          </Button>
        </div>
      )}
    </div>
  )
}
