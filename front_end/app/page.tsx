"use client"

import { useState, useEffect } from "react"
import ArticleItem from "@/components/articles/article-item"
import api from "@/lib/api"
import type { Article } from "@/lib/types"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import { useAuth } from "@/hooks/use-auth"
import { FileText } from "lucide-react"

function DraftsButton() {
  const { isAuthenticated } = useAuth()

  if (!isAuthenticated) return null

  return (
    <Button variant="outline" asChild>
      <Link href="/drafts">
        <FileText className="mr-2 h-4 w-4" /> 我的草稿箱
      </Link>
    </Button>
  )
}

export default function HomePage() {
  const [articles, setArticles] = useState<Article[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchArticles() {
      try {
        setLoading(true)
        const fetchedArticles = await api.getArticles()
        setArticles(fetchedArticles)
        setError(null)
      } catch (error) {
        console.error("Failed to fetch articles:", error)
        setError("获取文章失败")
        setArticles([])
      } finally {
        setLoading(false)
      }
    }

    fetchArticles()
  }, [])

  if (loading) {
    return (
      <div className="text-center py-10">
        <h1 className="text-3xl font-bold mb-4">加载中...</h1>
        <p className="text-muted-foreground">正在获取最新文章...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-10">
        <h1 className="text-3xl font-bold mb-4">加载失败</h1>
        <p className="text-muted-foreground mb-6">{error}</p>
        <Button onClick={() => window.location.reload()}>重试</Button>
      </div>
    )
  }

  if (!articles || articles.length === 0) {
    return (
      <div className="text-center py-10">
        <h1 className="text-3xl font-bold mb-4">暂无文章</h1>
        <p className="text-muted-foreground mb-6">看起来这里还没有任何内容。为什么不写一篇呢？</p>
        <Button asChild>
          <Link href="/create-article">开始写作</Link>
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-4xl font-bold tracking-tight">最新文章</h1>
        <DraftsButton />
      </div>
      <div className="grid gap-6 md:grid-cols-1 lg:grid-cols-1">
        {articles.map((article) => (
          <ArticleItem key={article.id} article={article} />
        ))}
      </div>
    </div>
  )
}
