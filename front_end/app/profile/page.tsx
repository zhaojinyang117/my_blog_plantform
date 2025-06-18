"use client"

import { useState, useEffect } from "react"
import { useAuth } from "@/hooks/use-auth"
import { useRouter } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Separator } from "@/components/ui/separator"
import { User, Mail, Edit3, Save, X, AlertCircle, CheckCircle } from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import AvatarUpload from "@/components/user/avatar-upload"
import api from "@/lib/api"

export default function ProfilePage() {
  const { user, isAuthenticated, isLoading } = useAuth()
  const router = useRouter()
  const { toast } = useToast()
  
  const [isEditing, setIsEditing] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [formData, setFormData] = useState({
    username: '',
    bio: '',
  })
  const [currentAvatar, setCurrentAvatar] = useState<string>('')

  // 重定向未认证用户
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login?redirect=/profile')
    }
  }, [isAuthenticated, isLoading, router])

  // 初始化表单数据
  useEffect(() => {
    if (user) {
      setFormData({
        username: user.username || '',
        bio: user.bio || '',
      })
      setCurrentAvatar(user.avatar || '')
    }
  }, [user])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleSave = async () => {
    setIsSaving(true)
    setError(null)

    try {
      const token = localStorage.getItem('authToken')
      if (!token) {
        throw new Error('未登录')
      }

      const response = await fetch('/api/users/me/update/', {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || '更新失败')
      }

      toast({
        title: "个人信息更新成功",
        description: "您的个人信息已保存",
      })

      setIsEditing(false)
    } catch (error) {
      console.error('更新个人信息失败:', error)
      setError(error instanceof Error ? error.message : '更新失败，请稍后再试')
      
      toast({
        title: "更新失败",
        description: error instanceof Error ? error.message : '请稍后再试',
        variant: "destructive",
      })
    } finally {
      setIsSaving(false)
    }
  }

  const handleCancel = () => {
    if (user) {
      setFormData({
        username: user.username || '',
        bio: user.bio || '',
      })
    }
    setIsEditing(false)
    setError(null)
  }

  const handleAvatarUpdated = (avatarUrl: string) => {
    setCurrentAvatar(avatarUrl)
  }

  // 加载中状态
  if (isLoading) {
    return (
      <div className="container mx-auto py-8">
        <div className="text-center">
          <p>加载中...</p>
        </div>
      </div>
    )
  }

  // 未认证状态
  if (!isAuthenticated || !user) {
    return null
  }

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="max-w-2xl mx-auto space-y-6">
        {/* 页面标题 */}
        <div className="text-center">
          <h1 className="text-3xl font-bold">个人中心</h1>
          <p className="text-muted-foreground mt-2">管理您的个人信息和设置</p>
        </div>

        {/* 头像上传 */}
        <AvatarUpload 
          currentAvatar={currentAvatar} 
          onAvatarUpdated={handleAvatarUpdated}
        />

        {/* 基本信息 */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <User className="h-5 w-5" />
                  基本信息
                </CardTitle>
                <CardDescription>
                  管理您的个人基本信息
                </CardDescription>
              </div>
              {!isEditing && (
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => setIsEditing(true)}
                >
                  <Edit3 className="h-4 w-4 mr-2" />
                  编辑
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <div className="space-y-4">
              {/* 邮箱 (只读) */}
              <div className="space-y-2">
                <Label htmlFor="email" className="flex items-center gap-2">
                  <Mail className="h-4 w-4" />
                  邮箱地址
                </Label>
                <Input
                  id="email"
                  type="email"
                  value={user.email}
                  disabled
                  className="bg-muted"
                />
                <p className="text-sm text-muted-foreground">
                  邮箱地址不可修改
                </p>
              </div>

              {/* 用户名 */}
              <div className="space-y-2">
                <Label htmlFor="username">用户名</Label>
                <Input
                  id="username"
                  name="username"
                  type="text"
                  value={formData.username}
                  onChange={handleInputChange}
                  disabled={!isEditing}
                  placeholder="请输入用户名"
                />
              </div>

              {/* 个人简介 */}
              <div className="space-y-2">
                <Label htmlFor="bio">个人简介</Label>
                <Textarea
                  id="bio"
                  name="bio"
                  value={formData.bio}
                  onChange={handleInputChange}
                  disabled={!isEditing}
                  placeholder="介绍一下自己吧..."
                  rows={4}
                  maxLength={500}
                />
                <p className="text-sm text-muted-foreground">
                  {formData.bio.length}/500 字符
                </p>
              </div>
            </div>

            {/* 编辑模式下的操作按钮 */}
            {isEditing && (
              <>
                <Separator />
                <div className="flex gap-2 justify-end">
                  <Button 
                    variant="outline" 
                    onClick={handleCancel}
                    disabled={isSaving}
                  >
                    <X className="h-4 w-4 mr-2" />
                    取消
                  </Button>
                  <Button 
                    onClick={handleSave}
                    disabled={isSaving}
                  >
                    {isSaving ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        保存中...
                      </>
                    ) : (
                      <>
                        <Save className="h-4 w-4 mr-2" />
                        保存
                      </>
                    )}
                  </Button>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* 账户状态 */}
        <Card>
          <CardHeader>
            <CardTitle>账户状态</CardTitle>
            <CardDescription>
              您的账户激活状态和相关信息
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              {user.is_active ? (
                <>
                  <CheckCircle className="h-5 w-5 text-green-600" />
                  <span className="text-green-600 font-medium">账户已激活</span>
                </>
              ) : (
                <>
                  <AlertCircle className="h-5 w-5 text-orange-600" />
                  <span className="text-orange-600 font-medium">账户未激活</span>
                  <span className="text-sm text-muted-foreground ml-2">
                    请检查邮箱完成验证
                  </span>
                </>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
