"use client"

import ArticleForm from "@/components/articles/article-form"
import ProtectedRouteClient from "@/components/auth/protected-route-client"
import api from "@/lib/api"
import type { Article } from "@/lib/types"
import { notFound } from "next/navigation"
import { useAuth } from "@/hooks/use-auth" // For checking author, will need client component

// This part will fetch data on the server
async function getArticleForEdit(id: string) {
  try {
    const article = await api.getArticle(id)
    if (!article) {
      notFound()
    }
    return article
  } catch (error) {
    console.error("Failed to fetch article for editing:", error)
    notFound()
  }
}

// The page itself is a Server Component.
// The ProtectedRouteClient and ArticleForm are Client Components.
export default async function EditArticlePage({ params }: { params: { id: string } }) {
  const article = await getArticleForEdit(params.id)

  // Additional check: Ensure only the author can edit.
  // This needs to be done in a client component part, or the API should enforce it.
  // For now, we pass the article to the form, and the form/API can handle auth.
  // If the API's updateArticle enforces authorship, that's good.
  // We can add a client-side check in ArticleForm or ProtectedRouteClient if needed.

  return (
    <ProtectedRouteClient>
      {" "}
      {/* This handles general authentication */}
      <EditArticleClientWrapper article={article} />
    </ProtectedRouteClient>
  )
}

// A new client component to handle author check more gracefully
function EditArticleClientWrapper({ article }: { article: Article }) {
  const { user, isLoading } = useAuth()

  if (isLoading) {
    return <div className="text-center py-10">加载用户信息...</div>
  }

  if (user?.id !== article.author.id) {
    // This should ideally redirect or show a proper unauthorized page.
    // For simplicity, showing a message. A redirect with `useRouter` would be better.
    return <div className="text-center py-10 text-red-500">您无权编辑此文章。</div>
  }

  return (
    <div className="py-8">
      <h1 className="text-3xl font-bold mb-8 text-center">编辑文章</h1>
      <ArticleForm article={article} formType="edit" />
    </div>
  )
}
