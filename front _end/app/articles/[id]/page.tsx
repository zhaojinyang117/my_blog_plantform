import api from "@/lib/api"
import { notFound } from "next/navigation"
import ReactMarkdown from "react-markdown"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { CalendarDays } from "lucide-react"
import ArticleActions from "@/components/articles/article-actions" // We'll create this next

async function getArticle(id: string) {
  try {
    const article = await api.getArticle(id)
    if (!article) {
      notFound()
    }
    return article
  } catch (error) {
    console.error("Failed to fetch article:", error)
    notFound()
  }
}

export default async function ArticleDetailPage({ params }: { params: { id: string } }) {
  const article = await getArticle(params.id)

  if (!article) {
    // This should be handled by getArticle calling notFound(), but as a fallback:
    return <div className="text-center py-10">文章未找到或无法访问。</div>
  }

  return (
    <article className="max-w-3xl mx-auto py-8 prose dark:prose-invert lg:prose-xl">
      <div className="mb-8 text-center">
        <h1 className="text-4xl font-extrabold tracking-tight lg:text-5xl">{article.title}</h1>
        <div className="mt-4 flex items-center justify-center space-x-4 text-muted-foreground">
          <div className="flex items-center">
            <Avatar className="h-8 w-8 mr-2">
              <AvatarImage
                src={`/placeholder-0y3ry.png?width=32&height=32&query=user+${article.author.username}`}
                alt={article.author.username}
              />
              <AvatarFallback>{article.author.username.charAt(0).toUpperCase()}</AvatarFallback>
            </Avatar>
            <span>{article.author.username}</span>
          </div>
          <span>•</span>
          <div className="flex items-center">
            <CalendarDays className="h-5 w-5 mr-1.5" />
            <time dateTime={article.created_at}>
              {new Date(article.created_at).toLocaleDateString("zh-CN", {
                year: "numeric",
                month: "long",
                day: "numeric",
              })}
            </time>
          </div>
        </div>
      </div>

      <ArticleActions articleId={article.id} authorId={article.author.id} />

      <ReactMarkdown
        components={{
          // Customize rendering of HTML elements if needed
          // For example, to style images or links
          h1: ({ node, ...props }) => <h1 className="text-3xl font-bold mt-8 mb-4" {...props} />,
          h2: ({ node, ...props }) => <h2 className="text-2xl font-semibold mt-6 mb-3" {...props} />,
          p: ({ node, ...props }) => <p className="leading-relaxed mb-4" {...props} />,
          a: ({ node, ...props }) => <a className="text-primary hover:underline" {...props} />,
          blockquote: ({ node, ...props }) => (
            <blockquote className="border-l-4 border-primary pl-4 italic my-4 text-muted-foreground" {...props} />
          ),
          code: ({ node, inline, className, children, ...props }) => {
            const match = /language-(\w+)/.exec(className || "")
            return !inline && match ? (
              <pre className="bg-muted p-4 rounded-md overflow-x-auto my-4">
                <code className={`language-${match[1]}`} {...props}>
                  {children}
                </code>
              </pre>
            ) : (
              <code className="bg-muted px-1 py-0.5 rounded-sm font-mono text-sm" {...props}>
                {children}
              </code>
            )
          },
        }}
      >
        {article.content}
      </ReactMarkdown>
    </article>
  )
}
