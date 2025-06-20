import Link from "next/link"
import type { Article } from "@/lib/types"
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { CalendarDays, Eye } from "lucide-react"

interface ArticleItemProps {
  article: Article
}

export default function ArticleItem({ article }: ArticleItemProps) {
  const summary = article.content.split("\n\n")[0].substring(0, 150) + "..." // Simple summary

  return (
    <Card className="w-full hover:shadow-lg transition-shadow duration-200">
      <CardHeader>
        <Link href={`/articles/${article.id}`} className="hover:underline">
          <CardTitle className="text-2xl font-semibold">{article.title}</CardTitle>
        </Link>
        <div className="flex items-center space-x-2 text-sm text-muted-foreground pt-1">
          <div className="flex items-center">
            <Avatar className="h-6 w-6 mr-1.5">
              <AvatarImage
                src={article.author.avatar || "/placeholder-user.jpg"}
                alt={article.author.username}
              />
              <AvatarFallback>{article.author.username.charAt(0).toUpperCase()}</AvatarFallback>
            </Avatar>
            <span>{article.author.username}</span>
          </div>
          <span>•</span>
          <div className="flex items-center">
            <CalendarDays className="h-4 w-4 mr-1.5" />
            <time dateTime={article.created_at}>{new Date(article.created_at).toLocaleDateString("zh-CN")}</time>
          </div>
          <span>•</span>
          <div className="flex items-center">
            <Eye className="h-4 w-4 mr-1.5" />
            <span>{article.view_count || 0} 次阅读</span>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-muted-foreground">{summary}</p>
      </CardContent>
      <CardFooter className="flex justify-between">
        <Link href={`/articles/${article.id}`} className="text-sm text-primary hover:underline">
          阅读全文 &rarr;
        </Link>
        {article.status === "draft" && (
          <Badge variant="secondary" className="bg-amber-100 text-amber-800 hover:bg-amber-200">
            草稿
          </Badge>
        )}
      </CardFooter>
    </Card>
  )
}
