"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Skeleton } from "@/components/ui/skeleton"
import { MessageCircle, AlertCircle } from "lucide-react"
import api from "@/lib/api"
import type { Comment } from "@/lib/types"
import CommentForm from "./comment-form"
import CommentItem from "./comment-item"

interface CommentListProps {
  articleId: string
}

export default function CommentList({ articleId }: CommentListProps) {
  const [comments, setComments] = useState<Comment[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchComments = async () => {
    try {
      setError(null)
      console.log(`正在获取文章${articleId}的评论...`)
      const fetchedComments = await api.getComments(articleId)
      console.log("获取到的评论数据:", fetchedComments)
      console.log("评论数据类型:", typeof fetchedComments)
      console.log("是否为数组:", Array.isArray(fetchedComments))
      // 确保返回的是数组
      if (Array.isArray(fetchedComments)) {
        console.log(`成功获取${fetchedComments.length}条评论`)
        setComments(fetchedComments)
      } else {
        console.warn("评论数据不是数组格式:", fetchedComments)
        console.warn("尝试从results字段获取数据...")
        if (fetchedComments && fetchedComments.results && Array.isArray(fetchedComments.results)) {
          console.log(`从results字段获取到${fetchedComments.results.length}条评论`)
          setComments(fetchedComments.results)
        } else {
          setComments([])
        }
      }
    } catch (error) {
      console.error("获取评论失败:", error)
      setError(error instanceof Error ? error.message : "获取评论失败")
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchComments()
  }, [articleId])

  const handleCommentUpdated = () => {
    console.log("handleCommentUpdated被调用，重新获取评论列表...")
    fetchComments()
  }

  // 计算总评论数（包括回复）
  const getTotalCommentCount = (comments: Comment[]): number => {
    if (!Array.isArray(comments)) {
      return 0
    }
    return comments.reduce((total, comment) => {
      return total + 1 + getTotalCommentCount(comment.replies || [])
    }, 0)
  }

  const totalComments = getTotalCommentCount(comments)

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <MessageCircle className="h-5 w-5 mr-2" />
              评论
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <Skeleton className="h-32 w-full" />
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="space-y-2">
                    <div className="flex items-center space-x-3">
                      <Skeleton className="h-8 w-8 rounded-full" />
                      <div className="space-y-1">
                        <Skeleton className="h-4 w-20" />
                        <Skeleton className="h-3 w-16" />
                      </div>
                    </div>
                    <Skeleton className="h-16 w-full" />
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <MessageCircle className="h-5 w-5 mr-2" />
            评论 ({totalComments})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {/* 评论表单 */}
          <CommentForm
            articleId={articleId}
            onCommentAdded={handleCommentUpdated}
          />

          {/* 错误提示 */}
          {error && (
            <Alert variant="destructive" className="mb-6">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* 评论列表 */}
          {comments.length === 0 ? (
            <div className="text-center py-8">
              <MessageCircle className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground">
                还没有评论，来发表第一条评论吧！
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {comments.map((comment) => (
                <CommentItem
                  key={comment.id}
                  comment={comment}
                  articleId={articleId}
                  onCommentUpdated={handleCommentUpdated}
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
