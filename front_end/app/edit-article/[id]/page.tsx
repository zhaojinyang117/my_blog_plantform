import EditArticleClient from "@/components/articles/edit-article-client"

export default async function EditArticlePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params

  return <EditArticleClient articleId={id} />
}
