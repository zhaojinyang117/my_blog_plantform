"use client"

import { useState, type FormEvent, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { useToast } from "@/components/ui/use-toast"
import type { Article, ArticleFormData } from "@/lib/types"
import api from "@/lib/api"
import { useAuth } from "@/hooks/use-auth"

interface ArticleFormProps {
  article?: Article // For editing
  formType: "create" | "edit"
}

export default function ArticleForm({ article, formType }: ArticleFormProps) {
  const { user } = useAuth()
  const [title, setTitle] = useState(article?.title || "")
  const [content, setContent] = useState(article?.content || "")
  const [status, setStatus] = useState<"草稿" | "发布">(article?.status || "草稿")
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const router = useRouter()
  const { toast } = useToast()

  useEffect(() => {
    if (article) {
      setTitle(article.title)
      setContent(article.content)
      setStatus(article.status)
    }
  }, [article])

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!user) {
      setError("用户未登录，无法提交。") // Should not happen if route is protected
      return
    }
    setError(null)
    setIsLoading(true)

    const articleData: ArticleFormData = { title, content, status }

    try {
      let savedArticle: Article | null = null
      if (formType === "create") {
        savedArticle = await api.createArticle(articleData, user)
        toast({ title: "文章创建成功！", description: `"${savedArticle.title}" 已保存。` })
      } else if (article) {
        savedArticle = await api.updateArticle(article.id, articleData, user.id)
        toast({ title: "文章更新成功！", description: `"${savedArticle?.title}" 已更新。` })
      }

      if (savedArticle) {
        router.push(`/articles/${savedArticle.id}`)
        router.refresh() // Important to refresh server components
      }
    } catch (err: any) {
      setError(err.message || (formType === "create" ? "创建文章失败。" : "更新文章失败。"))
      toast({
        title: formType === "create" ? "创建失败" : "更新失败",
        description: err.message || "操作失败，请稍后再试。",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-2xl mx-auto">
      {error && <p className="text-red-500">{error}</p>}
      <div>
        <Label htmlFor="title" className="text-lg font-medium">
          标题
        </Label>
        <Input
          id="title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="请输入文章标题"
          required
          className="mt-1 text-base"
          disabled={isLoading}
        />
      </div>
      <div>
        <Label htmlFor="content" className="text-lg font-medium">
          内容 (支持 Markdown)
        </Label>
        <Textarea
          id="content"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="开始写作您的精彩内容..."
          required
          rows={15}
          className="mt-1 text-base"
          disabled={isLoading}
        />
        <p className="text-sm text-muted-foreground mt-1">您可以使用 Markdown 语法来格式化文本。</p>
      </div>
      <div>
        <Label className="text-lg font-medium">状态</Label>
        <RadioGroup
          defaultValue={status}
          onValueChange={(value: "草稿" | "发布") => setStatus(value)}
          className="mt-1 flex space-x-4"
          disabled={isLoading}
        >
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="草稿" id="status-draft" />
            <Label htmlFor="status-draft">草稿</Label>
          </div>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="发布" id="status-publish" />
            <Label htmlFor="status-publish">发布</Label>
          </div>
        </RadioGroup>
      </div>
      <Button type="submit" className="w-full sm:w-auto" disabled={isLoading}>
        {isLoading
          ? formType === "create"
            ? "发布中..."
            : "更新中..."
          : formType === "create"
            ? "发布文章"
            : "保存更改"}
      </Button>
    </form>
  )
}
