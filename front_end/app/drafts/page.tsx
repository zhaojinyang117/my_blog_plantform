"use client"

import { useEffect, useState } from "react"
import ArticleItem from "@/components/articles/article-item"
import ProtectedRouteClient from "@/components/auth/protected-route-client"
import api from "@/lib/api"
import type { Article } from "@/lib/types"
import { useAuth } from "@/hooks/use-auth"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import { Loader2, PenLine } from "lucide-react"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"

export default function DraftsPage() {
  return (
    <ProtectedRouteClient>
      <DraftsContent />
    </ProtectedRouteClient>
  )
}

function DraftsContent() {
  const { user } = useAuth()
  const [drafts, setDrafts] = useState<Article[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchDrafts() {
      if (!user) {
        console.log("No user found, skipping draft fetch")
        return
      }

      console.log("Fetching drafts for user:", user.id)
      setIsLoading(true)
      setError(null)

      try {
        const articles = await api.getMyArticles(user.id)
        console.log("Fetched articles:", articles)

        // 只过滤出草稿状态的文章 (后端返回的状态是英文)
        const draftArticles = articles.filter((article) => article.status === "draft")
        console.log("Draft articles:", draftArticles)

        setDrafts(draftArticles)
      } catch (err: any) {
        console.error("Failed to fetch drafts:", err)
        const errorMessage = err.message || "获取草稿失败，请稍后再试。"
        setError(errorMessage)
      } finally {
        setIsLoading(false)
      }
    }

    fetchDrafts()
  }, [user])

  if (isLoading) {
    return (
      <div className="flex justify-center items-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-primary mr-2" />
        <p>加载草稿中...</p>
      </div>
    )
  }

  if (error) {
    return (
      <Alert variant="destructive" className="my-8">
        <AlertTitle>出错了</AlertTitle>
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    )
  }

  return (
    <div className="space-y-8 py-8">
      <div className="flex justify-between items-center">
        <h1 className="text-4xl font-bold tracking-tight">我的草稿箱</h1>
        <Button asChild>
          <Link href="/create-article">
            <PenLine className="mr-2 h-4 w-4" /> 写新文章
          </Link>
        </Button>
      </div>

      {drafts.length === 0 ? (
        <div className="text-center py-16 bg-muted/30 rounded-lg">
          <h2 className="text-xl font-medium mb-2">暂无草稿</h2>
          <p className="text-muted-foreground mb-6">您还没有保存任何草稿文章</p>
          <Button asChild>
            <Link href="/create-article">开始写作</Link>
          </Button>
        </div>
      ) : (
        <div className="grid gap-6">
          {drafts.map((draft) => (
            <ArticleItem key={draft.id} article={draft} />
          ))}
        </div>
      )}
    </div>
  )
}
