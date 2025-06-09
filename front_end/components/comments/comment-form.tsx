"use client"

import { useState } from "react"
import { useAuth } from "@/hooks/use-auth"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Card, CardContent } from "@/components/ui/card"
import { useToast } from "@/components/ui/use-toast"
import api from "@/lib/api"
import type { CommentFormData } from "@/lib/types"

interface CommentFormProps {
  articleId: string
  parentId?: string | null
  onCommentAdded: () => void
  onCancel?: () => void
  placeholder?: string
  buttonText?: string
}

export default function CommentForm({
  articleId,
  parentId = null,
  onCommentAdded,
  onCancel,
  placeholder = "写下您的评论...",
  buttonText = "发表评论"
}: CommentFormProps) {
  const { isAuthenticated } = useAuth()
  const { toast } = useToast()
  const [content, setContent] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!isAuthenticated) {
      toast({
        title: "请先登录",
        description: "您需要登录后才能发表评论",
        variant: "destructive",
      })
      return
    }

    if (!content.trim()) {
      toast({
        title: "评论内容不能为空",
        variant: "destructive",
      })
      return
    }

    setIsSubmitting(true)
    try {
      const commentData: CommentFormData = {
        content: content.trim(),
        parent: parentId,
      }

      await api.createComment(articleId, commentData)
      
      toast({
        title: "评论发表成功",
        description: "您的评论已成功发表",
      })

      setContent("")
      onCommentAdded()
    } catch (error) {
      console.error("发表评论失败:", error)
      toast({
        title: "发表评论失败",
        description: error instanceof Error ? error.message : "请稍后再试",
        variant: "destructive",
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  if (!isAuthenticated) {
    return (
      <Card className="mb-6">
        <CardContent className="pt-6">
          <p className="text-muted-foreground text-center">
            请 <a href="/login" className="text-primary hover:underline">登录</a> 后发表评论
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="mb-6">
      <CardContent className="pt-6">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="comment-content" className="sr-only">
              评论内容
            </Label>
            <Textarea
              id="comment-content"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder={placeholder}
              rows={4}
              disabled={isSubmitting}
              className="resize-none"
            />
          </div>
          <div className="flex justify-end space-x-2">
            {onCancel && (
              <Button
                type="button"
                variant="outline"
                onClick={onCancel}
                disabled={isSubmitting}
              >
                取消
              </Button>
            )}
            <Button
              type="submit"
              disabled={isSubmitting || !content.trim()}
            >
              {isSubmitting ? "发表中..." : buttonText}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}
