"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { useAuth } from "@/hooks/use-auth"
import api from "@/lib/api"

export default function TestDraftsPage() {
  const { user, isAuthenticated } = useAuth()
  const [results, setResults] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(false)

  const addResult = (message: string) => {
    setResults(prev => [...prev, `${new Date().toLocaleTimeString()}: ${message}`])
  }

  const clearResults = () => {
    setResults([])
  }

  const testGetMyArticles = async () => {
    if (!user) {
      addResult("❌ 用户未登录")
      return
    }

    setIsLoading(true)
    addResult("🔄 开始测试获取个人文章...")
    
    try {
      addResult(`📝 当前用户: ${user.username} (ID: ${user.id})`)
      
      const articles = await api.getMyArticles(user.id)
      addResult(`✅ 获取个人文章成功! 共 ${articles.length} 篇文章`)
      
      articles.forEach((article, index) => {
        addResult(`📄 文章 ${index + 1}: "${article.title}" - 状态: ${article.status} - 作者: ${article.author.username}`)
      })

      const drafts = articles.filter(article => article.status === "草稿")
      addResult(`📝 其中草稿文章: ${drafts.length} 篇`)
      
    } catch (error: any) {
      addResult(`❌ 获取个人文章失败: ${error.message}`)
    } finally {
      setIsLoading(false)
    }
  }

  const testDirectAPICall = async () => {
    if (!user) {
      addResult("❌ 用户未登录")
      return
    }

    setIsLoading(true)
    addResult("🔄 开始测试直接API调用...")
    
    try {
      // 获取token
      const token = localStorage.getItem('authToken')
      if (!token) {
        addResult("❌ 未找到认证token")
        return
      }

      addResult(`🔑 使用token: ${token.substring(0, 20)}...`)

      // 直接调用前端API代理
      const response = await fetch('/api/articles/', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      })

      if (response.ok) {
        const data = await response.json()
        const articles = Array.isArray(data) ? data : data.results || []
        addResult(`✅ 直接API调用成功! 共 ${articles.length} 篇文章`)
        
        articles.forEach((article: any, index: number) => {
          addResult(`📄 文章 ${index + 1}: "${article.title}" - 状态: ${article.status} - 作者: ${article.author.username}`)
        })
      } else {
        const errorData = await response.json().catch(() => ({}))
        addResult(`❌ 直接API调用失败: ${response.status} - ${JSON.stringify(errorData)}`)
      }
    } catch (error: any) {
      addResult(`❌ 直接API调用失败: ${error.message}`)
    } finally {
      setIsLoading(false)
    }
  }

  const testBackendDirectCall = async () => {
    if (!user) {
      addResult("❌ 用户未登录")
      return
    }

    setIsLoading(true)
    addResult("🔄 开始测试后端直接调用...")
    
    try {
      const token = localStorage.getItem('authToken')
      if (!token) {
        addResult("❌ 未找到认证token")
        return
      }

      // 直接调用后端API
      const response = await fetch('http://localhost:8000/api/articles/', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      })

      if (response.ok) {
        const data = await response.json()
        const articles = Array.isArray(data) ? data : data.results || []
        addResult(`✅ 后端直接调用成功! 共 ${articles.length} 篇文章`)
        
        articles.forEach((article: any, index: number) => {
          addResult(`📄 文章 ${index + 1}: "${article.title}" - 状态: ${article.status} - 作者: ${article.author.username}`)
        })
      } else {
        const errorData = await response.json().catch(() => ({}))
        addResult(`❌ 后端直接调用失败: ${response.status} - ${JSON.stringify(errorData)}`)
      }
    } catch (error: any) {
      addResult(`❌ 后端直接调用失败: ${error.message}`)
    } finally {
      setIsLoading(false)
    }
  }

  if (!isAuthenticated) {
    return (
      <div className="container mx-auto py-8">
        <Card>
          <CardHeader>
            <CardTitle>草稿功能测试</CardTitle>
            <CardDescription>请先登录以测试草稿功能</CardDescription>
          </CardHeader>
          <CardContent>
            <Alert>
              <AlertDescription>您需要先登录才能测试草稿功能</AlertDescription>
            </Alert>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="container mx-auto py-8 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>草稿功能测试</CardTitle>
          <CardDescription>测试获取个人草稿文章的功能</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="text-sm text-muted-foreground">
            当前用户: {user?.username} ({user?.email})
          </div>
          
          <div className="flex gap-2 flex-wrap">
            <Button onClick={testGetMyArticles} disabled={isLoading}>
              测试 getMyArticles
            </Button>
            <Button onClick={testDirectAPICall} disabled={isLoading} variant="outline">
              测试前端API代理
            </Button>
            <Button onClick={testBackendDirectCall} disabled={isLoading} variant="outline">
              测试后端直接调用
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
