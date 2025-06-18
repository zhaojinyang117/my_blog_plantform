"use client"

import { useState, useRef } from "react"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Upload, Camera, Loader2, AlertCircle } from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import { useAuth } from "@/hooks/use-auth"

interface AvatarUploadProps {
  currentAvatar?: string
  onAvatarUpdated?: (avatarUrl: string) => void
}

export default function AvatarUpload({ currentAvatar, onAvatarUpdated }: AvatarUploadProps) {
  const [isUploading, setIsUploading] = useState(false)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { toast } = useToast()
  const { user } = useAuth()

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    // 验证文件类型
    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif']
    if (!allowedTypes.includes(file.type)) {
      setError('只支持 JPEG、PNG、GIF 格式的图片')
      return
    }

    // 验证文件大小 (2MB)
    const maxSize = 2 * 1024 * 1024
    if (file.size > maxSize) {
      setError('图片文件不能超过 2MB')
      return
    }

    setError(null)

    // 创建预览
    const reader = new FileReader()
    reader.onload = (e) => {
      setPreviewUrl(e.target?.result as string)
    }
    reader.readAsDataURL(file)

    // 自动上传
    uploadAvatar(file)
  }

  const uploadAvatar = async (file: File) => {
    setIsUploading(true)
    setError(null)

    try {
      const formData = new FormData()
      formData.append('avatar', file)

      const token = localStorage.getItem('authToken')
      if (!token) {
        throw new Error('未登录')
      }

      const response = await fetch('/api/users/me/avatar/', {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || '上传失败')
      }

      const data = await response.json()
      
      toast({
        title: "头像上传成功",
        description: "您的头像已更新",
      })

      // 通知父组件头像已更新
      if (onAvatarUpdated && data.avatar_url) {
        onAvatarUpdated(data.avatar_url)
      }

      setPreviewUrl(null)
    } catch (error) {
      console.error('头像上传失败:', error)
      setError(error instanceof Error ? error.message : '上传失败，请稍后再试')
      setPreviewUrl(null)
      
      toast({
        title: "头像上传失败",
        description: error instanceof Error ? error.message : '请稍后再试',
        variant: "destructive",
      })
    } finally {
      setIsUploading(false)
      // 清空文件输入
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const handleUploadClick = () => {
    fileInputRef.current?.click()
  }

  const getAvatarUrl = () => {
    if (previewUrl) return previewUrl
    if (currentAvatar) return currentAvatar
    return undefined
  }

  const getUserInitials = () => {
    if (!user?.username) return 'U'
    return user.username.charAt(0).toUpperCase()
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Camera className="h-5 w-5" />
          头像设置
        </CardTitle>
        <CardDescription>
          上传您的个人头像，支持 JPEG、PNG、GIF 格式，文件大小不超过 2MB
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center space-x-4">
          <div className="relative">
            <Avatar className="h-20 w-20">
              <AvatarImage src={getAvatarUrl()} alt="用户头像" />
              <AvatarFallback className="text-lg">
                {getUserInitials()}
              </AvatarFallback>
            </Avatar>
            {isUploading && (
              <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50 rounded-full">
                <Loader2 className="h-6 w-6 animate-spin text-white" />
              </div>
            )}
          </div>
          
          <div className="flex-1 space-y-2">
            <Button 
              onClick={handleUploadClick} 
              disabled={isUploading}
              className="w-full sm:w-auto"
            >
              <Upload className="h-4 w-4 mr-2" />
              {isUploading ? '上传中...' : '选择头像'}
            </Button>
            
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png,image/gif"
              onChange={handleFileSelect}
              className="hidden"
            />
          </div>
        </div>

        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <div className="text-sm text-muted-foreground">
          <p>• 建议尺寸：200x200 像素</p>
          <p>• 支持格式：JPEG、PNG、GIF</p>
          <p>• 文件大小：最大 2MB</p>
        </div>
      </CardContent>
    </Card>
  )
}
