"use client"

import { useAuth } from "@/hooks/use-auth"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import { Edit, Trash2 } from "lucide-react"
import { useRouter } from "next/navigation"
import api from "@/lib/api"
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

interface ArticleActionsProps {
  articleId: string
  authorId: string
}

export default function ArticleActions({ articleId, authorId }: ArticleActionsProps) {
  const { user, isAuthenticated } = useAuth()
  const router = useRouter()
  const { toast } = useToast()

  if (!isAuthenticated || user?.id !== authorId) {
    return null // Only show actions if authenticated and is the author
  }

  const handleDelete = async () => {
    if (!user) return
    try {
      await api.deleteArticle(articleId)
      toast({
        title: "删除成功",
        description: "文章已成功删除。",
      })
      router.push("/")
      router.refresh() // Refresh server components
    } catch (error: any) {
      toast({
        title: "删除失败",
        description: error.message || "无法删除文章，请稍后再试。",
        variant: "destructive",
      })
    }
  }

  return (
    <div className="mb-6 flex justify-end space-x-2">
      <Button variant="outline" size="sm" asChild>
        <Link href={`/edit-article/${articleId}`}>
          <Edit className="mr-2 h-4 w-4" /> 编辑
        </Link>
      </Button>
      <AlertDialog>
        <AlertDialogTrigger asChild>
          <Button variant="destructive" size="sm">
            <Trash2 className="mr-2 h-4 w-4" /> 删除
          </Button>
        </AlertDialogTrigger>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>确定要删除这篇文章吗？</AlertDialogTitle>
            <AlertDialogDescription>此操作无法撤销。文章将被永久删除。</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-destructive hover:bg-destructive/90">
              确定删除
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
