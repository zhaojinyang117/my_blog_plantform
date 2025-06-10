"use client"

import { useState } from "react"
import { useAuth } from "@/hooks/use-auth"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { useToast } from "@/components/ui/use-toast"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import { MessageCircle, Trash2, Calendar } from "lucide-react"
import api from "@/lib/api"
import type { Comment } from "@/lib/types"
import CommentForm from "./comment-form"

interface CommentItemProps {
  comment: Comment
  articleId: string
  onCommentUpdated: () => void
  level?: number
}

export default function CommentItem({
  comment,
  articleId,
  onCommentUpdated,
  level = 0
}: CommentItemProps) {
  const { user } = useAuth()
  const { toast } = useToast()
  const [showReplyForm, setShowReplyForm] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)

  const isAuthor = user?.id === comment.user.id
  const maxLevel = 2 // 最大嵌套层级

  const handleDelete = async () => {
    setIsDeleting(true)
    try {
      await api.deleteComment(articleId, comment.id)
      toast({
        title: "评论删除成功",
        description: "评论已成功删除",
      })
      onCommentUpdated()
    } catch (error) {
      console.error("删除评论失败:", error)
      toast({
        title: "删除评论失败",
        description: error instanceof Error ? error.message : "请稍后再试",
        variant: "destructive",
      })
    } finally {
      setIsDeleting(false)
    }
  }

  const handleReplyAdded = () => {
    setShowReplyForm(false)
    onCommentUpdated()
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60))

    if (diffInMinutes < 1) {
      return "刚刚"
    } else if (diffInMinutes < 60) {
      return `${diffInMinutes}分钟前`
    } else if (diffInMinutes < 60 * 24) {
      return `${Math.floor(diffInMinutes / 60)}小时前`
    } else if (diffInMinutes < 60 * 24 * 7) {
      return `${Math.floor(diffInMinutes / (60 * 24))}天前`
    } else {
      return date.toLocaleDateString("zh-CN", {
        year: "numeric",
        month: "short",
        day: "numeric",
      })
    }
  }

  return (
    <div className={`${level > 0 ? 'ml-8 mt-4' : 'mb-6'}`}>
      <Card>
        <CardContent className="pt-4">
          {/* 评论头部 */}
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center space-x-3">
              <Avatar className="h-8 w-8">
                <AvatarImage
                  src={`/placeholder-0y3ry.png?width=32&height=32&query=user+${comment.user.username}`}
                  alt={comment.user.username}
                />
                <AvatarFallback>
                  {comment.user.username.charAt(0).toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <div>
                <p className="font-medium text-sm">{comment.user.username}</p>
                <div className="flex items-center text-xs text-muted-foreground">
                  <Calendar className="h-3 w-3 mr-1" />
                  <time dateTime={comment.created_at}>
                    {formatDate(comment.created_at)}
                  </time>
                </div>
              </div>
            </div>

            {/* 操作按钮 */}
            {isAuthor && (
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    disabled={isDeleting}
                    className="text-muted-foreground hover:text-destructive"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>确认删除评论</AlertDialogTitle>
                    <AlertDialogDescription>
                      此操作无法撤销。删除评论后，所有回复也将被删除。
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>取消</AlertDialogCancel>
                    <AlertDialogAction
                      onClick={handleDelete}
                      className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                    >
                      删除
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            )}
          </div>

          {/* 评论内容 */}
          <div className="mb-3">
            <p className="text-sm leading-relaxed whitespace-pre-wrap">
              {comment.content}
            </p>
          </div>

          {/* 回复按钮 */}
          {level === 0 && user && (
            <div className="flex items-center space-x-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowReplyForm(!showReplyForm)}
                className="text-muted-foreground hover:text-primary"
              >
                <MessageCircle className="h-4 w-4 mr-1" />
                回复
              </Button>
            </div>
          )}

          {/* 回复表单 */}
          {showReplyForm && (
            <div className="mt-4">
              <CommentForm
                articleId={articleId}
                parentId={comment.id}
                onCommentAdded={handleReplyAdded}
                onCancel={() => setShowReplyForm(false)}
                placeholder={`回复 @${comment.user.username}...`}
                buttonText="发表回复"
              />
            </div>
          )}
        </CardContent>
      </Card>

      {/* 回复列表 */}
      {comment.replies && comment.replies.length > 0 && (
        <div className="mt-4">
          {comment.replies.map((reply) => (
            <CommentItem
              key={reply.id}
              comment={reply}
              articleId={articleId}
              onCommentUpdated={onCommentUpdated}
              level={level + 1}
            />
          ))}
        </div>
      )}
    </div>
  )
}
