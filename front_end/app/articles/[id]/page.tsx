import ArticleDetailClient from "@/components/articles/article-detail-client"

export default async function ArticleDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params

  return <ArticleDetailClient articleId={id} />
}
