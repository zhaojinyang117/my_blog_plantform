// This page itself is a Server Component.
// The actual form and logic are in ArticleForm, which is a Client Component.
// We wrap the client component part with ProtectedRouteClient for auth check.
import ArticleForm from "@/components/articles/article-form"
import ProtectedRouteClient from "@/components/auth/protected-route-client"

export default function CreateArticlePage() {
  return (
    <ProtectedRouteClient>
      <div className="py-8">
        <h1 className="text-3xl font-bold mb-8 text-center">撰写新文章</h1>
        <ArticleForm formType="create" />
      </div>
    </ProtectedRouteClient>
  )
}
