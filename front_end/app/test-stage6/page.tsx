"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { CheckCircle, XCircle, Loader2, Mail, Upload } from "lucide-react"
import { useToast } from "@/hooks/use-toast"

export default function TestStage6Page() {
  // 仅在开发环境中显示此页面
  if (process.env.NODE_ENV === 'production') {
    return (
      <div className="container mx-auto py-8 px-4">
        <div className="text-center">
          <h1 className="text-3xl font-bold">页面不可用</h1>
          <p className="text-muted-foreground mt-2">此测试页面仅在开发环境中可用</p>
        </div>
      </div>
    )
  }
  const [results, setResults] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [testEmail, setTestEmail] = useState("test@example.com")
  const [testToken, setTestToken] = useState("")
  const { toast } = useToast()

  const addResult = (message: string) => {
    setResults(prev => [...prev, `${new Date().toLocaleTimeString()}: ${message}`])
  }

  const clearResults = () => {
    setResults([])
  }

  // 测试用户注册
  const testUserRegistration = async () => {
    setIsLoading(true)
    try {
      const response = await fetch('/api/users/register/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: 'testuser' + Date.now(),
          email: testEmail,
          password: 'testpassword123',
        }),
      })

      if (response.ok) {
        const data = await response.json()
        addResult(`✅ 用户注册成功: ${data.message}`)
        addResult(`📧 注册邮箱: ${data.email}`)
      } else {
        const errorData = await response.json()
        addResult(`❌ 用户注册失败: ${JSON.stringify(errorData)}`)
      }
    } catch (error) {
      addResult(`❌ 注册请求失败: ${error}`)
    } finally {
      setIsLoading(false)
    }
  }

  // 测试邮箱验证
  const testEmailVerification = async () => {
    if (!testToken) {
      addResult(`❌ 请输入验证令牌`)
      return
    }

    setIsLoading(true)
    try {
      const response = await fetch(`/api/users/verify-email?token=${testToken}`)
      
      if (response.ok) {
        const data = await response.json()
        addResult(`✅ 邮箱验证成功: ${data.message}`)
        addResult(`📊 验证状态: ${data.status}`)
      } else {
        const errorData = await response.json()
        addResult(`❌ 邮箱验证失败: ${errorData.error}`)
      }
    } catch (error) {
      addResult(`❌ 验证请求失败: ${error}`)
    } finally {
      setIsLoading(false)
    }
  }

  // 测试头像上传
  const testAvatarUpload = async () => {
    // 创建一个测试图片文件
    const canvas = document.createElement('canvas')
    canvas.width = 100
    canvas.height = 100
    const ctx = canvas.getContext('2d')
    if (ctx) {
      ctx.fillStyle = '#007bff'
      ctx.fillRect(0, 0, 100, 100)
      ctx.fillStyle = '#ffffff'
      ctx.font = '20px Arial'
      ctx.fillText('TEST', 25, 55)
    }

    canvas.toBlob(async (blob) => {
      if (!blob) {
        addResult(`❌ 无法创建测试图片`)
        return
      }

      const formData = new FormData()
      formData.append('avatar', blob, 'test-avatar.png')

      setIsLoading(true)
      try {
        const token = localStorage.getItem('authToken')
        if (!token) {
          addResult(`❌ 未登录，无法测试头像上传`)
          return
        }

        const response = await fetch('/api/users/me/avatar/', {
          method: 'PATCH',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
          body: formData,
        })

        if (response.ok) {
          const data = await response.json()
          addResult(`✅ 头像上传成功: ${data.message}`)
          addResult(`🖼️ 头像URL: ${data.avatar_url}`)
        } else {
          const errorData = await response.json()
          addResult(`❌ 头像上传失败: ${errorData.error}`)
        }
      } catch (error) {
        addResult(`❌ 上传请求失败: ${error}`)
      } finally {
        setIsLoading(false)
      }
    }, 'image/png')
  }

  // 测试用户信息获取
  const testGetUserInfo = async () => {
    setIsLoading(true)
    try {
      const token = localStorage.getItem('authToken')
      if (!token) {
        addResult(`❌ 未登录，无法获取用户信息`)
        return
      }

      const response = await fetch('/api/users/me/', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (response.ok) {
        const userData = await response.json()
        addResult(`✅ 获取用户信息成功`)
        addResult(`👤 用户名: ${userData.username}`)
        addResult(`📧 邮箱: ${userData.email}`)
        addResult(`🔓 激活状态: ${userData.is_active ? '已激活' : '未激活'}`)
        addResult(`🖼️ 头像: ${userData.avatar || '无'}`)
      } else {
        const errorData = await response.json()
        addResult(`❌ 获取用户信息失败: ${errorData.error}`)
      }
    } catch (error) {
      addResult(`❌ 请求失败: ${error}`)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="text-center">
          <h1 className="text-3xl font-bold">第六阶段功能测试</h1>
          <p className="text-muted-foreground mt-2">测试邮箱验证、头像上传、用户状态管理等功能</p>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          {/* 测试控制面板 */}
          <Card>
            <CardHeader>
              <CardTitle>测试控制面板</CardTitle>
              <CardDescription>
                点击下方按钮测试各项功能
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="testEmail">测试邮箱</Label>
                <Input
                  id="testEmail"
                  type="email"
                  value={testEmail}
                  onChange={(e) => setTestEmail(e.target.value)}
                  placeholder="输入测试邮箱"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="testToken">验证令牌</Label>
                <Input
                  id="testToken"
                  type="text"
                  value={testToken}
                  onChange={(e) => setTestToken(e.target.value)}
                  placeholder="输入邮箱验证令牌"
                />
              </div>

              <div className="space-y-2">
                <Button 
                  onClick={testUserRegistration} 
                  disabled={isLoading}
                  className="w-full"
                >
                  <Mail className="mr-2 h-4 w-4" />
                  测试用户注册
                </Button>

                <Button 
                  onClick={testEmailVerification} 
                  disabled={isLoading}
                  variant="outline"
                  className="w-full"
                >
                  <CheckCircle className="mr-2 h-4 w-4" />
                  测试邮箱验证
                </Button>

                <Button 
                  onClick={testAvatarUpload} 
                  disabled={isLoading}
                  variant="outline"
                  className="w-full"
                >
                  <Upload className="mr-2 h-4 w-4" />
                  测试头像上传
                </Button>

                <Button 
                  onClick={testGetUserInfo} 
                  disabled={isLoading}
                  variant="outline"
                  className="w-full"
                >
                  获取用户信息
                </Button>

                <Button 
                  onClick={clearResults} 
                  variant="destructive"
                  className="w-full"
                >
                  清空结果
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* 测试结果 */}
          <Card>
            <CardHeader>
              <CardTitle>测试结果</CardTitle>
              <CardDescription>
                查看测试执行结果和响应信息
              </CardDescription>
            </CardHeader>
            <CardContent>
              {isLoading && (
                <div className="flex items-center justify-center py-4">
                  <Loader2 className="h-6 w-6 animate-spin mr-2" />
                  <span>测试执行中...</span>
                </div>
              )}
              
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {results.length === 0 ? (
                  <p className="text-muted-foreground text-center py-4">
                    暂无测试结果
                  </p>
                ) : (
                  results.map((result, index) => (
                    <div 
                      key={index} 
                      className="text-sm p-2 bg-muted rounded font-mono"
                    >
                      {result}
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        <Alert>
          <CheckCircle className="h-4 w-4" />
          <AlertDescription>
            <strong>测试说明：</strong>
            <ul className="mt-2 space-y-1 text-sm">
              <li>• 用户注册测试会创建新用户并发送验证邮件</li>
              <li>• 邮箱验证需要从后端控制台获取验证令牌</li>
              <li>• 头像上传和用户信息获取需要先登录</li>
              <li>• 所有测试都会显示详细的响应信息</li>
            </ul>
          </AlertDescription>
        </Alert>
      </div>
    </div>
  )
}
