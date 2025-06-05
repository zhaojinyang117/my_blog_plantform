"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"

export default function TestApiPage() {
  const [results, setResults] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [email, setEmail] = useState("test@example.com")
  const [password, setPassword] = useState("testpassword123")

  const addResult = (message: string) => {
    setResults(prev => [...prev, message])
  }

  const clearResults = () => {
    setResults([])
  }

  const testLogin = async () => {
    setIsLoading(true)
    addResult("🔄 开始测试登录...")
    
    try {
      const response = await fetch('/api/users/token/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email,
          password: password,
        }),
      })

      if (response.ok) {
        const data = await response.json()
        addResult(`✅ 登录成功! Token: ${data.access.substring(0, 50)}...`)
        
        // 测试获取用户信息
        const userResponse = await fetch('/api/users/me/', {
          headers: {
            'Authorization': `Bearer ${data.access}`,
          },
        })
        
        if (userResponse.ok) {
          const userData = await userResponse.json()
          addResult(`✅ 获取用户信息成功: ${userData.username} (${userData.email})`)
        } else {
          addResult(`❌ 获取用户信息失败: ${userResponse.status}`)
        }
      } else {
        const errorData = await response.json()
        addResult(`❌ 登录失败: ${JSON.stringify(errorData)}`)
      }
    } catch (error) {
      addResult(`❌ 请求失败: ${error}`)
    }
    
    setIsLoading(false)
  }

  const testArticles = async () => {
    setIsLoading(true)
    addResult("🔄 开始测试文章API...")
    
    try {
      const response = await fetch('/api/articles/')
      
      if (response.ok) {
        const data = await response.json()
        const articles = Array.isArray(data) ? data : data.results || []
        addResult(`✅ 获取文章列表成功! 共 ${articles.length} 篇文章`)
        
        if (articles.length > 0) {
          const firstArticle = articles[0]
          addResult(`📄 第一篇文章: "${firstArticle.title}" by ${firstArticle.author.username}`)
        }
      } else {
        addResult(`❌ 获取文章列表失败: ${response.status}`)
      }
    } catch (error) {
      addResult(`❌ 请求失败: ${error}`)
    }
    
    setIsLoading(false)
  }

  const testDirectAPI = async () => {
    setIsLoading(true)
    addResult("🔄 开始测试直接API调用...")
    
    try {
      // 直接调用后端API
      const response = await fetch('http://localhost:8000/api/articles/')
      
      if (response.ok) {
        const data = await response.json()
        const articles = Array.isArray(data) ? data : data.results || []
        addResult(`✅ 直接API调用成功! 共 ${articles.length} 篇文章`)
      } else {
        addResult(`❌ 直接API调用失败: ${response.status}`)
      }
    } catch (error) {
      addResult(`❌ 直接API调用失败: ${error}`)
    }
    
    setIsLoading(false)
  }

  return (
    <div className="container mx-auto py-8 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>API 集成测试</CardTitle>
          <CardDescription>测试前后端API集成是否正常工作</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="email">邮箱</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="test@example.com"
              />
            </div>
            <div>
              <Label htmlFor="password">密码</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="密码"
              />
            </div>
          </div>
          
          <div className="flex gap-2 flex-wrap">
            <Button onClick={testLogin} disabled={isLoading}>
              测试登录
            </Button>
            <Button onClick={testArticles} disabled={isLoading} variant="outline">
              测试文章API
            </Button>
            <Button onClick={testDirectAPI} disabled={isLoading} variant="outline">
              测试直接API
            </Button>
            <Button onClick={clearResults} variant="destructive" size="sm">
              清空结果
            </Button>
          </div>
        </CardContent>
      </Card>

      {results.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>测试结果</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {results.map((result, index) => (
                <Alert key={index} className="text-sm">
                  <AlertDescription className="font-mono">{result}</AlertDescription>
                </Alert>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
